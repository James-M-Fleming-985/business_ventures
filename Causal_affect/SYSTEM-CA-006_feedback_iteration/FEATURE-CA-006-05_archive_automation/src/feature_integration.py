"""
Feature Integration Module for Archive & Cleanup Automation
FEATURE ID: FEATURE-CA-006-05

This module orchestrates the complete archive workflow by integrating:
- Archive Workflow Orchestrator (LAYER-CA-006-05-01)
- Infrastructure Cleanup Service (LAYER-CA-006-05-02)
- Data Preservation Service (LAYER-CA-006-05-03)
- Notification Service (LAYER-CA-006-05-04)
"""

from pathlib import Path
import sys
from dataclasses import dataclass, field
from typing import Dict, Any, Optional, List
from datetime import datetime
from enum import Enum
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Layer imports
try:
    from LAYER_CA_006_05_01_Archive_Workflow_Orchestrator.src.implementation import (
        ArchiveWorkflowOrchestrator,
        WorkflowStage,
        WorkflowStatus,
        ApprovalMode,
        WorkflowExecution
    )
except ImportError:
    from layer_ca_006_05_01.src.implementation import (
        ArchiveWorkflowOrchestrator,
        WorkflowStage,
        WorkflowStatus,
        ApprovalMode,
        WorkflowExecution
    )

try:
    from LAYER_CA_006_05_02_Infrastructure_Cleanup_Service.src.implementation import (
        InfrastructureCleanupService,
        ResourceType,
        CleanupStatus,
        Resource
    )
except ImportError:
    from layer_ca_006_05_02.src.implementation import (
        InfrastructureCleanupService,
        ResourceType,
        CleanupStatus,
        Resource
    )

try:
    from LAYER_CA_006_05_03_Data_Preservation_Service.src.implementation import (
        DataPreservationService
    )
except ImportError:
    from layer_ca_006_05_03.src.implementation import (
        DataPreservationService
    )

try:
    from LAYER_CA_006_05_04_Notification_Service.src.implementation import (
        NotificationService,
        NotificationChannel,
        WorkflowEventType,
        WorkflowEvent
    )
except ImportError:
    from layer_ca_006_05_04.src.implementation import (
        NotificationService,
        NotificationChannel,
        WorkflowEventType,
        WorkflowEvent
    )


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureStatus(Enum):
    """Status of feature operations"""
    SUCCESS = "success"
    FAILURE = "failure"
    PARTIAL = "partial"
    IN_PROGRESS = "in_progress"
    PENDING_APPROVAL = "pending_approval"


@dataclass
class FeatureConfig:
    """Configuration for Archive & Cleanup Automation feature"""
    
    # Workflow configuration
    mvp_id: str
    mvp_name: str
    approval_mode: ApprovalMode = ApprovalMode.MANUAL
    auto_approve_stages: List[WorkflowStage] = field(default_factory=list)
    
    # Infrastructure configuration
    railway_api_key: Optional[str] = None
    railway_project_id: Optional[str] = None
    
    # Data preservation configuration
    aws_access_key: Optional[str] = None
    aws_secret_key: Optional[str] = None
    s3_bucket: Optional[str] = None
    database_connection: Optional[Dict[str, str]] = None
    
    # Notification configuration
    email_enabled: bool = True
    slack_enabled: bool = True
    smtp_config: Optional[Dict[str, Any]] = None
    slack_webhook_url: Optional[str] = None
    notification_recipients: List[str] = field(default_factory=list)
    
    # General settings
    dry_run: bool = False
    max_retries: int = 3
    timeout_seconds: int = 3600
    
    def validate(self) -> tuple[bool, List[str]]:
        """
        Validate configuration completeness
        
        Returns:
            Tuple of (is_valid, error_messages)
        """
        errors = []
        
        if not self.mvp_id:
            errors.append("mvp_id is required")
        if not self.mvp_name:
            errors.append("mvp_name is required")
            
        if self.railway_project_id and not self.railway_api_key:
            errors.append("railway_api_key required when railway_project_id is set")
            
        if any([self.aws_access_key, self.aws_secret_key, self.s3_bucket]):
            if not all([self.aws_access_key, self.aws_secret_key, self.s3_bucket]):
                errors.append("All AWS credentials required for data preservation")
                
        if self.email_enabled and not self.smtp_config:
            errors.append("smtp_config required when email notifications enabled")
            
        if self.slack_enabled and not self.slack_webhook_url:
            errors.append("slack_webhook_url required when slack notifications enabled")
            
        return len(errors) == 0, errors


@dataclass
class FeatureResponse:
    """Unified response structure for feature operations"""
    
    status: FeatureStatus
    message: str
    execution_id: Optional[str] = None
    workflow_status: Optional[WorkflowStatus] = None
    current_stage: Optional[WorkflowStage] = None
    data: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        return {
            "status": self.status.value,
            "message": self.message,
            "execution_id": self.execution_id,
            "workflow_status": self.workflow_status.value if self.workflow_status else None,
            "current_stage": self.current_stage.value if self.current_stage else None,
            "data": self.data,
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": self.timestamp.isoformat()
        }


class FeatureOrchestrator:
    """
    Main orchestrator for Archive & Cleanup Automation feature.
    
    Coordinates all layers to execute the complete archive workflow:
    1. Initialize workflow through Archive Workflow Orchestrator
    2. Execute data preservation via Data Preservation Service
    3. Cleanup infrastructure via Infrastructure Cleanup Service
    4. Send notifications via Notification Service
    """
    
    def __init__(self, config: FeatureConfig):
        """
        Initialize feature orchestrator with configuration
        
        Args:
            config: Feature configuration
            
        Raises:
            ValueError: If configuration is invalid
        """
        self.config = config
        
        # Validate configuration
        is_valid, errors = config.validate()
        if not is_valid:
            raise ValueError(f"Invalid configuration: {', '.join(errors)}")
        
        # Initialize layers
        self._init_layers()
        
        # Track current execution
        self.current_execution: Optional[WorkflowExecution] = None
        
        logger.info(f"Feature orchestrator initialized for MVP: {config.mvp_name}")
    
    def _init_layers(self) -> None:
        """Initialize all layer services"""
        try:
            # Initialize Workflow Orchestrator
            self.workflow_orchestrator = ArchiveWorkflowOrchestrator(
                approval_mode=self.config.approval_mode
            )
            logger.info("Archive Workflow Orchestrator initialized")
            
            # Initialize Infrastructure Cleanup Service
            if self.config.railway_api_key:
                self.infrastructure_service = InfrastructureCleanupService(
                    api_key=self.config.railway_api_key
                )
                logger.info("Infrastructure Cleanup Service initialized")
            else:
                self.infrastructure_service = None
                logger.warning("Infrastructure Cleanup Service not initialized (no API key)")
            
            # Initialize Data Preservation Service
            if all([self.config.aws_access_key, self.config.aws_secret_key, self.config.s3_bucket]):
                self.data_preservation_service = DataPreservationService(
                    aws_access_key_id=self.config.aws_access_key,
                    aws_secret_access_key=self.config.aws_secret_key,
                    s3_bucket=self.config.s3_bucket,
                    db_config=self.config.database_connection
                )
                logger.info("Data Preservation Service initialized")
            else:
                self.data_preservation_service = None
                logger.warning("Data Preservation Service not initialized (no AWS credentials)")
            
            # Initialize Notification Service
            channels = []
            if self.config.email_enabled:
                channels.append(NotificationChannel.EMAIL)
            if self.config.slack_enabled:
                channels.append(NotificationChannel.SLACK)
            
            self.notification_service = NotificationService(
                enabled_channels=channels,
                smtp_config=self.config.smtp_config,
                slack_webhook_url=self.config.slack_webhook_url
            )
            logger.info(f"Notification Service initialized with channels: {channels}")
            
        except Exception as e:
            logger.error(f"Failed to initialize layers: {str(e)}")
            raise
    
    def start_archive_workflow(self) -> FeatureResponse:
        """
        Start the complete archive workflow
        
        Returns:
            FeatureResponse with workflow execution details
        """
        try:
            logger.info(f"Starting archive workflow for MVP: {self.config.mvp_id}")
            
            # Start workflow execution
            execution = self.workflow_orchestrator.start_workflow(
                mvp_id=self.config.mvp_id,
                mvp_name=self.config.mvp_name,
                metadata={
                    "initiated_by": "feature_orchestrator",
                    "config": {
                        "dry_run": self.config.dry_run,
                        "approval_mode": self.config.approval_mode.value
                    }
                }
            )
            
            self.current_execution = execution
            
            # Send workflow started notification
            self._send_notification(
                event_type=WorkflowEventType.WORKFLOW_STARTED,
                message=f"Archive workflow started for {self.config.mvp_name}",
                execution=execution
            )
            
            # Auto-advance through initial stages if configured
            if self.config.approval_mode == ApprovalMode.AUTO:
                self._auto_advance_stages()
            
            return FeatureResponse(
                status=FeatureStatus.IN_PROGRESS,
                message="Archive workflow started successfully",
                execution_id=execution.execution_id,
                workflow_status=execution.status,
                current_stage=execution.current_stage,
                data={
                    "execution": execution.to_dict(),
                    "next_action": self._get_next_action(execution)
                }
            )
            
        except Exception as e:
            logger.error(f"Failed to start archive workflow: {str(e)}")
            return FeatureResponse(
                status=FeatureStatus.FAILURE,
                message="Failed to start archive workflow",
                errors=[str(e)]
            )
    
    def _auto_advance_stages(self) -> None:
        """Automatically advance through stages based on configuration"""
        if not self.current_execution:
            return
        
        while (self.current_execution.status == WorkflowStatus.IN_PROGRESS and
               self.current_execution.current_stage in self.config.auto_approve_stages):
            
            # Execute stage based on type
            if self.current_execution.current_stage == WorkflowStage.DATA_PRESERVATION:
                self._execute_data_preservation()
            elif self.current_execution.current_stage == WorkflowStage.INFRASTRUCTURE_CLEANUP:
                self._execute_infrastructure_cleanup()
            elif self.current_execution.current_stage == WorkflowStage.VERIFICATION:
                self._execute_verification()
            
            # Advance to next stage
            if self.current_execution.status == WorkflowStatus.IN_PROGRESS:
                self.advance_stage(auto_approve=True)
    
    def advance_stage(self, auto_approve: bool = False, notes: Optional[str] = None) -> FeatureResponse:
        """
        Advance workflow to next stage
        
        Args:
            auto_approve: Whether to auto-approve checkpoints
            notes: Optional notes for stage advancement
            
        Returns:
            FeatureResponse with updated workflow status
        """
        if not self.current_execution:
            return FeatureResponse(
                status=FeatureStatus.FAILURE,
                message="No active workflow execution",
                errors=["Workflow must be started first"]
            )
        
        try:
            current_stage = self.current_execution.current_stage
            
            # Execute stage-specific logic
            if current_stage == WorkflowStage.DATA_PRESERVATION:
                result = self._execute_data_preservation()
            elif current_stage == WorkflowStage.INFRASTRUCTURE_CLEANUP:
                result = self._execute_infrastructure_cleanup()
            elif current_stage == WorkflowStage.VERIFICATION:
                result = self._execute_verification()
            else:
                result = {"success": True, "message": f"Stage {current_stage.value} completed"}
            
            # Complete current stage
            success = result.get("success", True)
            stage_notes = result.get("message", notes or "Stage completed")
            
            self.workflow_orchestrator.complete_stage(
                execution_id=self.current_execution.execution_id,
                success=success,
                notes=stage_notes
            )
            
            # Check if workflow needs approval
            if (self.current_execution.requires_approval and 
                not auto_approve and
                current_stage not in self.config.auto_approve_stages):
                
                return FeatureResponse(
                    status=FeatureStatus.PENDING_APPROVAL,
                    message=f"Stage {current_stage.value} completed, awaiting approval",
                    execution_id=self.current_execution.execution_id,
                    workflow_status=self.current_execution.status,
                    current_stage=self.current_execution.current_stage,
                    data={"result": result}
                )
            
            # Advance to next stage
            self.workflow_orchestrator.advance_stage(
                execution_id=self.current_execution.execution_id
            )
            
            # Send stage completion notification
            self._send_notification(
                event_type=WorkflowEventType.STAGE_COMPLETED,
                message=f"Stage {current_stage.value} completed",
                execution=self.current_execution
            )
            
            # Check if workflow is complete
            if self.current_execution.status == WorkflowStatus.COMPLETED:
                self._handle_workflow_completion()
            
            return FeatureResponse(
                status=FeatureStatus.SUCCESS if success else FeatureStatus.PARTIAL,
                message=f"Advanced from {current_stage.value}",
                execution_id=self.current_execution.execution_id,
                workflow_status=self.current_execution.status,
                current_stage=self.current_execution.current_stage,
                data={"stage_result": result}
            )
            
        except Exception as e:
            logger.error(f"Failed to advance stage: {str(e)}")
            return FeatureResponse(
                status=FeatureStatus.FAILURE,
                message="Failed to advance stage",
                errors=[str(e)]
            )
    
    def _execute_data_preservation(self) -> Dict[str, Any]:
        """Execute data preservation stage"""
        if not self.data_preservation_service:
            logger.warning("Data Preservation Service not available, skipping")
            return {"success": True, "message": "Data preservation skipped (service not configured)"}
        
        try:
            logger.info("Executing data preservation stage")
            
            if self.config.dry_run:
                return {
                    "success": True,
                    "message": "Data preservation completed (dry run)",
                    "backed_up_count": 0
                }
            
            # Export data to S3
            export_result = self.data_preservation_service.export_to_s3(
                mvp_id=self.config.mvp_id
            )
            
            # Verify backup integrity
            verification_result = self.data_preservation_service.verify_backup(
                backup_key=export_result.get("backup_key")
            )
            
            return {
                "success": verification_result.get("verified", False),
                "message": "Data preservation completed successfully",
                "backup_location": export_result.get("s3_location"),
                "backed_up_count": export_result.get("record_count", 0),
                "verification": verification_result
            }
            
        except Exception as e:
            logger.error(f"Data preservation failed: {str(e)}")
            return {
                "success": False,
                "message": f"Data preservation failed: {str(e)}"
            }
    
    def _execute_infrastructure_cleanup(self) -> Dict[str, Any]:
        """Execute infrastructure cleanup stage"""
        if not self.infrastructure_service:
            logger.warning("Infrastructure Cleanup Service not available, skipping")
            return {"success": True, "message": "Infrastructure cleanup skipped (service not configured)"}
        
        try:
            logger.info("Executing infrastructure cleanup stage")
            
            if self.config.dry_run:
                return {
                    "success": True,
                    "message": "Infrastructure cleanup completed (dry run)",
                    "resources_cleaned": 0
                }
            
            # Cleanup Railway project
            cleanup_result = self.infrastructure_service.cleanup_project(
                project_id=self.config.railway_project_id
            )
            
            return {
                "success": cleanup_result.overall_status == CleanupStatus.SUCCESS,
                "message": "Infrastructure cleanup completed",
                "resources_cleaned": len(cleanup_result.resources),
                "cleanup_details": [r.to_dict() for r in cleanup_result.resources]
            }
            
        except Exception as e:
            logger.error(f"Infrastructure cleanup failed: {str(e)}")
            return {
                "success": False,
                "message": f"Infrastructure cleanup failed: {str(e)}"
            }
    
    def _execute_verification(self) -> Dict[str, Any]:
        """Execute verification stage"""
        try:
            logger.info("Executing verification stage")
            
            checks = []
            
            # Verify data preservation
            if self.data_preservation_service:
                data_check = self._verify_data_preservation()
                checks.append(data_check)
            
            # Verify infrastructure cleanup
            if self.infrastructure_service:
                infra_check = self._verify_infrastructure_cleanup()
                checks.append(infra_check)
            
            all_passed = all(check.get("passed", False) for check in checks)
            
            return {
                "success": all_passed,
                "message": "Verification completed" if all_passed else "Verification found issues",
                "checks": checks,
                "passed_count": sum(1 for c in checks if c.get("passed")),
                "total_count": len(checks)
            }
            
        except Exception as e:
            logger.error(f"Verification failed: {str(e)}")
            return {
                "success": False,
                "message": f"Verification failed: {str(e)}"
            }
    
    def _verify_data_preservation(self) -> Dict[str, Any]:
        """Verify data preservation was successful"""
        try:
            # Check if backup exists and is valid
            backup_exists = self.data_preservation_service.check_backup_exists(
                mvp_id=self.config.mvp_id
            )
            
            return {
                "check": "data_preservation",
                "passed": backup_exists,
                "message": "Data backup verified" if backup_exists else "Data backup not found"
            }
        except Exception as e:
            return {
                "check": "data_preservation",
                "passed": False,
                "message": f"Data verification failed: {str(e)}"
            }
    
    def _verify_infrastructure_cleanup(self) -> Dict[str, Any]:
        """Verify infrastructure cleanup was successful"""
        try:
            # Check if resources are properly cleaned up
            resources = self.infrastructure_service.list_project_resources(
                project_id=self.config.railway_project_id
            )
            
            active_resources = [r for r in resources if r.status != CleanupStatus.SUCCESS]
            
            return {
                "check": "infrastructure_cleanup",
                "passed": len(active_resources) == 0,
                "message": "All resources cleaned" if len(active_resources) == 0 
                          else f"{len(active_resources)} resources still active"
            }
        except Exception as e:
            return {
                "check": "infrastructure_cleanup",
                "passed": False,
                "message": f"Infrastructure verification failed: {str(e)}"
            }
    
    def _handle_workflow_completion(self) -> None:
        """Handle workflow completion"""
        logger.info("Workflow completed successfully")
        
        # Send completion notification
        self._send_notification(
            event_type=WorkflowEventType.WORKFLOW_COMPLETED,
            message=f"Archive workflow completed for {self.config.mvp_name}",
            execution=self.current_execution
        )
    
    def _send_notification(
        self,
        event_type: WorkflowEventType,
        message: str,
        execution: Optional[WorkflowExecution] = None
    ) -> None:
        """Send notification for workflow event"""
        try:
            event = WorkflowEvent(
                event_type=event_type,
                mvp_name=self.config.mvp_name,
                execution_id=execution.execution_id if execution else None,
                current_stage=execution.current_stage if execution else None,
                message=message,
                timestamp=datetime.utcnow()
            )
            
            self.notification_service.send_workflow_notification(
                event=event,
                recipients=self.config.notification_recipients
            )
            
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
    
    def _get_next_action(self, execution: WorkflowExecution) -> str:
        """Determine next action required for workflow"""
        if execution.status == WorkflowStatus.COMPLETED:
            return "Workflow completed"
        elif execution.status == WorkflowStatus.FAILED:
            return "Workflow failed - review errors"
        elif execution.requires_approval:
            return f"Approve {execution.current_stage.value} to continue"
        else:
            return f"Execute {execution.current_stage.value} stage"
    
    def get_workflow_status(self) -> FeatureResponse:
        """
        Get current workflow status
        
        Returns:
            FeatureResponse with current workflow state
        """
        if not self.current_execution:
            return FeatureResponse(
                status=FeatureStatus.FAILURE,
                message="No active workflow execution"
            )
        
        return FeatureResponse(
            status=FeatureStatus.I