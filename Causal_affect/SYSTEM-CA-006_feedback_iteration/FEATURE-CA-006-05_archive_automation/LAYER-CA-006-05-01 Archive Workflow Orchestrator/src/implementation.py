```python
import asyncio
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List, Callable
from dataclasses import dataclass, field
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class WorkflowStage(Enum):
    VALIDATION = "validation"
    PREPARATION = "preparation"
    BACKUP = "backup"
    ARCHIVE = "archive"
    VERIFICATION = "verification"
    CLEANUP = "cleanup"


class WorkflowStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    ROLLED_BACK = "rolled_back"


class ApprovalMode(Enum):
    MANUAL = "manual"
    AUTO = "auto"


@dataclass
class StageResult:
    stage: WorkflowStage
    status: WorkflowStatus
    timestamp: datetime
    duration: float
    error: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class WorkflowExecution:
    workflow_id: str
    status: WorkflowStatus
    start_time: datetime
    end_time: Optional[datetime] = None
    stages: List[StageResult] = field(default_factory=list)
    approval_mode: ApprovalMode = ApprovalMode.MANUAL
    can_rollback: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def duration(self) -> float:
        if self.end_time:
            return (self.end_time - self.start_time).total_seconds()
        return (datetime.now() - self.start_time).total_seconds()

    @property
    def is_within_rollback_window(self) -> bool:
        if not self.end_time:
            return True
        elapsed = datetime.now() - self.end_time
        return elapsed <= timedelta(days=7)


class ArchiveWorkflowOrchestrator:
    """
    Orchestrates archive workflow with support for manual/auto-approve paths,
    rollback capabilities, and stage-by-stage execution.
    """

    def __init__(self, approval_mode: ApprovalMode = ApprovalMode.MANUAL):
        self.approval_mode = approval_mode
        self.executions: Dict[str, WorkflowExecution] = {}
        self._approval_callback: Optional[Callable] = None
        self._stage_timeout = 120  # 2 minutes per stage max
        
    def set_approval_callback(self, callback: Callable) -> None:
        """Set callback for manual approval requests."""
        self._approval_callback = callback

    async def execute_workflow(
        self,
        workflow_id: str,
        data: Dict[str, Any],
        approval_mode: Optional[ApprovalMode] = None
    ) -> WorkflowExecution:
        """
        Execute complete archive workflow through all stages.
        
        Args:
            workflow_id: Unique identifier for workflow execution
            data: Input data for workflow
            approval_mode: Override default approval mode
            
        Returns:
            WorkflowExecution with results from all stages
            
        Raises:
            TimeoutError: If workflow exceeds 10 minute limit
            RuntimeError: If any stage fails
        """
        mode = approval_mode or self.approval_mode
        execution = WorkflowExecution(
            workflow_id=workflow_id,
            status=WorkflowStatus.IN_PROGRESS,
            start_time=datetime.now(),
            approval_mode=mode,
            metadata=data
        )
        self.executions[workflow_id] = execution

        stages = [
            WorkflowStage.VALIDATION,
            WorkflowStage.PREPARATION,
            WorkflowStage.BACKUP,
            WorkflowStage.ARCHIVE,
            WorkflowStage.VERIFICATION,
            WorkflowStage.CLEANUP
        ]

        try:
            workflow_timeout = 600  # 10 minutes
            async with asyncio.timeout(workflow_timeout):
                for stage in stages:
                    if mode == ApprovalMode.MANUAL and stage != WorkflowStage.VALIDATION:
                        await self._request_approval(workflow_id, stage)
                    
                    stage_result = await self._execute_stage(stage, data)
                    execution.stages.append(stage_result)
                    
                    if stage_result.status == WorkflowStatus.FAILED:
                        execution.status = WorkflowStatus.FAILED
                        execution.end_time = datetime.now()
                        raise RuntimeError(f"Stage {stage.value} failed: {stage_result.error}")

            execution.status = WorkflowStatus.COMPLETED
            execution.end_time = datetime.now()
            logger.info(f"Workflow {workflow_id} completed in {execution.duration:.2f}s")
            
        except asyncio.TimeoutError:
            execution.status = WorkflowStatus.FAILED
            execution.end_time = datetime.now()
            logger.error(f"Workflow {workflow_id} timed out after {execution.duration:.2f}s")
            raise TimeoutError("Workflow exceeded 10 minute time limit")
        except Exception as e:
            execution.status = WorkflowStatus.FAILED
            execution.end_time = datetime.now()
            logger.error(f"Workflow {workflow_id} failed: {str(e)}")
            raise

        return execution

    async def _execute_stage(
        self,
        stage: WorkflowStage,
        data: Dict[str, Any]
    ) -> StageResult:
        """Execute a single workflow stage."""
        start_time = datetime.now()
        logger.info(f"Executing stage: {stage.value}")
        
        try:
            async with asyncio.timeout(self._stage_timeout):
                await self._run_stage_logic(stage, data)
                
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = StageResult(
                stage=stage,
                status=WorkflowStatus.COMPLETED,
                timestamp=end_time,
                duration=duration
            )
            logger.info(f"Stage {stage.value} completed in {duration:.2f}s")
            return result
            
        except Exception as e:
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            error_msg = str(e)
            logger.error(f"Stage {stage.value} failed: {error_msg}")
            
            return StageResult(
                stage=stage,
                status=WorkflowStatus.FAILED,
                timestamp=end_time,
                duration=duration,
                error=error_msg
            )

    async def _run_stage_logic(self, stage: WorkflowStage, data: Dict[str, Any]) -> None:
        """Execute stage-specific logic."""
        # Simulate stage processing
        processing_time = 0.1  # Fast execution for testing
        
        if stage == WorkflowStage.VALIDATION:
            await asyncio.sleep(processing_time)
            if not data:
                raise ValueError("No data provided for validation")
                
        elif stage == WorkflowStage.PREPARATION:
            await asyncio.sleep(processing_time)
            # Prepare resources
            
        elif stage == WorkflowStage.BACKUP:
            await asyncio.sleep(processing_time)
            # Create backup
            
        elif stage == WorkflowStage.ARCHIVE:
            await asyncio.sleep(processing_time)
            # Perform archive
            
        elif stage == WorkflowStage.VERIFICATION:
            await asyncio.sleep(processing_time)
            # Verify archive integrity
            
        elif stage == WorkflowStage.CLEANUP:
            await asyncio.sleep(processing_time)
            # Clean up temporary resources

    async def _request_approval(self, workflow_id: str, stage: WorkflowStage) -> None:
        """Request manual approval for stage execution."""
        if self._approval_callback:
            approved = await self._approval_callback(workflow_id, stage)
            if not approved:
                raise RuntimeError(f"Approval denied for stage {stage.value}")
        else:
            # Auto-approve if no callback set
            await asyncio.sleep(0.01)

    async def rollback(self, workflow_id: str) -> bool:
        """
        Rollback a completed workflow within 7-day window.
        
        Args:
            workflow_id: Workflow execution to rollback
            
        Returns:
            True if rollback successful, False otherwise
        """
        if workflow_id not in self.executions:
            logger.error(f"Workflow {workflow_id} not found")
            return False

        execution = self.executions[workflow_id]
        
        if not execution.can_rollback:
            logger.error(f"Workflow {workflow_id} cannot be rolled back")
            return False

        if not execution.is_within_rollback_window:
            logger.error(f"Workflow {workflow_id} is outside 7-day rollback window")
            return False

        if execution.status != WorkflowStatus.COMPLETED:
            logger.error(f"Workflow {workflow_id} is not in completed state")
            return False

        try:
            logger.info(f"Rolling back workflow {workflow_id}")
            
            # Rollback stages in reverse order
            for stage_result in reversed(execution.stages):
                await self._rollback_stage(stage_result)
            
            execution.status = WorkflowStatus.ROLLED_BACK
            logger.info(f"Workflow {workflow_id} successfully rolled back")
            return True
            
        except Exception as e:
            logger.error(f"Rollback failed for workflow {workflow_id}: {str(e)}")
            return False

    async def _rollback_stage(self, stage_result: StageResult) -> None:
        """Rollback a specific stage."""
        logger.info(f"Rolling back stage: {stage_result.stage.value}")
        await asyncio.sleep(0.05)  # Simulate rollback operation

    def get_execution(self, workflow_id: str) -> Optional[WorkflowExecution]:
        """Retrieve workflow execution by ID."""
        return self.executions.get(workflow_id)

    def get_execution_status(self, workflow_id: str) -> Optional[WorkflowStatus]:
        """Get current status of workflow execution."""
        execution = self.executions.get(workflow_id)
        return execution.status if execution else None

    def list_executions(self) -> List[WorkflowExecution]:
        """List all workflow executions."""
        return list(self.executions.values())


async def execute_archive_workflow(
    workflow_id: str,
    data: Dict[str, Any],
    approval_mode: ApprovalMode = ApprovalMode.AUTO
) -> WorkflowExecution:
    """
    Convenience function to execute archive workflow.
    
    Args:
        workflow_id: Unique workflow identifier
        data: Input data for workflow
        approval_mode: Approval mode (manual or auto)
        
    Returns:
        Completed workflow execution
    """
    orchestrator = ArchiveWorkflowOrchestrator(approval_mode=approval_mode)
    return await orchestrator.execute_workflow(workflow_id, data, approval_mode)


async def rollback_workflow(workflow_id: str, orchestrator: ArchiveWorkflowOrchestrator) -> bool:
    """
    Rollback a workflow execution.
    
    Args:
        workflow_id: Workflow to rollback
        orchestrator: Orchestrator instance managing the workflow
        
    Returns:
        True if rollback successful
    """
    return await orchestrator.rollback(workflow_id)
```