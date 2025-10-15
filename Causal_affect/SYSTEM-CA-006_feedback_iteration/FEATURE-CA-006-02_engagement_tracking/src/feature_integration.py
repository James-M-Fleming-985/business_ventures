"""
Real-Time Engagement Tracking Feature Integration Module

This module orchestrates the interaction between all layers of the engagement tracking feature,
providing a unified interface for tracking user engagement events in real-time.

Feature ID: FEATURE-CA-006-02
"""

from pathlib import Path
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime, timedelta
import asyncio
import logging
from enum import Enum

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Layer imports
from LAYER_CA_006_02_01_Event_Collector.src.implementation import (
    EventValidationResult,
    EventCollector
)
from LAYER_CA_006_02_02_Session_Tracker.src.implementation import (
    SessionMetrics,
    Session,
    SessionTracker
)
from LAYER_CA_006_02_03_Metrics_Calculator.src.implementation import (
    MetricsCalculator
)
from LAYER_CA_006_02_04_Real_Time_Processor.src.implementation import (
    Event,
    ProcessingResult,
    DashboardCache,
    EventBuffer,
    MetricsAggregator,
    RealTimeProcessor
)
from LAYER_CA_006_02_05_Engagement_Storage_Layer.src.implementation import (
    EngagementEvent,
    EngagementStorage
)
from LAYER_CA_006_02_06_Engagement_Cache_Layer.src.implementation import (
    EngagementCache
)


# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class FeatureStatus(Enum):
    """Status codes for feature operations"""
    SUCCESS = "success"
    PARTIAL_SUCCESS = "partial_success"
    FAILURE = "failure"
    ERROR = "error"


@dataclass
class FeatureConfig:
    """Configuration for the Real-Time Engagement Tracking feature"""
    
    # Redis configuration
    redis_host: str = "localhost"
    redis_port: int = 6379
    redis_db: int = 0
    redis_queue_name: str = "engagement_events"
    
    # PostgreSQL configuration
    db_host: str = "localhost"
    db_port: int = 5432
    db_name: str = "engagement_db"
    db_user: str = "postgres"
    db_password: str = ""
    
    # Processing configuration
    batch_size: int = 100
    processing_interval_seconds: float = 1.0
    max_queue_size: int = 10000
    
    # Session configuration
    session_timeout_minutes: int = 30
    
    # Rate limiting
    rate_limit_per_user: int = 1000
    rate_limit_window_seconds: int = 3600
    
    # Performance targets
    target_latency_seconds: float = 5.0
    
    # Cache configuration
    cache_ttl_seconds: int = 300
    dashboard_cache_ttl_seconds: int = 10
    
    # Retry configuration
    max_retries: int = 3
    retry_delay_seconds: float = 1.0


@dataclass
class FeatureResponse:
    """Unified response structure for feature operations"""
    
    status: FeatureStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    processing_time_ms: Optional[float] = None
    
    def is_success(self) -> bool:
        """Check if operation was successful"""
        return self.status in [FeatureStatus.SUCCESS, FeatureStatus.PARTIAL_SUCCESS]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert response to dictionary"""
        return {
            "status": self.status.value,
            "message": self.message,
            "data": self.data,
            "errors": self.errors,
            "warnings": self.warnings,
            "timestamp": self.timestamp.isoformat(),
            "processing_time_ms": self.processing_time_ms
        }


class FeatureOrchestrator:
    """
    Main orchestrator for the Real-Time Engagement Tracking feature.
    
    Coordinates interaction between all layers to provide end-to-end
    engagement tracking functionality with <5 second latency.
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Initialize the feature orchestrator with all required layers.
        
        Args:
            config: Feature configuration. Uses defaults if not provided.
        """
        self.config = config or FeatureConfig()
        self._initialized = False
        self._processing_task: Optional[asyncio.Task] = None
        
        # Layer instances
        self.event_collector: Optional[EventCollector] = None
        self.session_tracker: Optional[SessionTracker] = None
        self.metrics_calculator: Optional[MetricsCalculator] = None
        self.real_time_processor: Optional[RealTimeProcessor] = None
        self.engagement_storage: Optional[EngagementStorage] = None
        self.engagement_cache: Optional[EngagementCache] = None
        
        logger.info("FeatureOrchestrator instance created")
    
    async def initialize(self) -> FeatureResponse:
        """
        Initialize all feature layers in the correct order.
        
        Returns:
            FeatureResponse indicating success or failure of initialization
        """
        start_time = datetime.utcnow()
        errors = []
        warnings = []
        
        try:
            logger.info("Initializing Real-Time Engagement Tracking feature...")
            
            # Initialize storage layer first (dependencies for other layers)
            try:
                logger.info("Initializing Engagement Storage Layer...")
                self.engagement_storage = EngagementStorage(
                    host=self.config.db_host,
                    port=self.config.db_port,
                    database=self.config.db_name,
                    user=self.config.db_user,
                    password=self.config.db_password
                )
                await self.engagement_storage.initialize()
                logger.info("✓ Engagement Storage Layer initialized")
            except Exception as e:
                errors.append(f"Storage layer initialization failed: {str(e)}")
                logger.error(f"✗ Engagement Storage Layer failed: {e}")
            
            # Initialize cache layer
            try:
                logger.info("Initializing Engagement Cache Layer...")
                self.engagement_cache = EngagementCache(
                    host=self.config.redis_host,
                    port=self.config.redis_port,
                    db=self.config.redis_db,
                    ttl_seconds=self.config.cache_ttl_seconds
                )
                await self.engagement_cache.connect()
                logger.info("✓ Engagement Cache Layer initialized")
            except Exception as e:
                errors.append(f"Cache layer initialization failed: {str(e)}")
                logger.error(f"✗ Engagement Cache Layer failed: {e}")
            
            # Initialize event collector
            try:
                logger.info("Initializing Event Collector...")
                self.event_collector = EventCollector(
                    redis_host=self.config.redis_host,
                    redis_port=self.config.redis_port,
                    queue_name=self.config.redis_queue_name,
                    rate_limit_per_user=self.config.rate_limit_per_user,
                    rate_limit_window=self.config.rate_limit_window_seconds
                )
                await self.event_collector.initialize()
                logger.info("✓ Event Collector initialized")
            except Exception as e:
                errors.append(f"Event collector initialization failed: {str(e)}")
                logger.error(f"✗ Event Collector failed: {e}")
            
            # Initialize session tracker
            try:
                logger.info("Initializing Session Tracker...")
                self.session_tracker = SessionTracker(
                    timeout_minutes=self.config.session_timeout_minutes,
                    storage=self.engagement_storage,
                    cache=self.engagement_cache
                )
                logger.info("✓ Session Tracker initialized")
            except Exception as e:
                errors.append(f"Session tracker initialization failed: {str(e)}")
                logger.error(f"✗ Session Tracker failed: {e}")
            
            # Initialize metrics calculator
            try:
                logger.info("Initializing Metrics Calculator...")
                self.metrics_calculator = MetricsCalculator(
                    storage=self.engagement_storage,
                    cache=self.engagement_cache
                )
                logger.info("✓ Metrics Calculator initialized")
            except Exception as e:
                errors.append(f"Metrics calculator initialization failed: {str(e)}")
                logger.error(f"✗ Metrics Calculator failed: {e}")
            
            # Initialize real-time processor
            try:
                logger.info("Initializing Real-Time Processor...")
                self.real_time_processor = RealTimeProcessor(
                    redis_host=self.config.redis_host,
                    redis_port=self.config.redis_port,
                    queue_name=self.config.redis_queue_name,
                    batch_size=self.config.batch_size,
                    session_tracker=self.session_tracker,
                    metrics_calculator=self.metrics_calculator,
                    storage=self.engagement_storage,
                    cache=self.engagement_cache
                )
                await self.real_time_processor.initialize()
                logger.info("✓ Real-Time Processor initialized")
            except Exception as e:
                errors.append(f"Real-time processor initialization failed: {str(e)}")
                logger.error(f"✗ Real-Time Processor failed: {e}")
            
            # Determine overall status
            if errors:
                if len(errors) >= 3:  # Critical layers failed
                    status = FeatureStatus.FAILURE
                    message = "Feature initialization failed"
                else:
                    status = FeatureStatus.PARTIAL_SUCCESS
                    message = "Feature partially initialized with some errors"
                    warnings.append("Some layers failed to initialize")
            else:
                status = FeatureStatus.SUCCESS
                message = "Feature successfully initialized"
                self._initialized = True
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return FeatureResponse(
                status=status,
                message=message,
                data={
                    "initialized_layers": self._get_initialized_layers(),
                    "config": self._get_config_summary()
                },
                errors=errors,
                warnings=warnings,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Unexpected error during initialization: {e}", exc_info=True)
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message="Unexpected error during feature initialization",
                errors=[str(e)],
                processing_time_ms=processing_time
            )
    
    async def start_processing(self) -> FeatureResponse:
        """
        Start the real-time event processing pipeline.
        
        Returns:
            FeatureResponse indicating success or failure
        """
        if not self._initialized:
            return FeatureResponse(
                status=FeatureStatus.FAILURE,
                message="Cannot start processing: feature not initialized",
                errors=["Feature must be initialized before starting processing"]
            )
        
        try:
            if self._processing_task and not self._processing_task.done():
                return FeatureResponse(
                    status=FeatureStatus.SUCCESS,
                    message="Processing already running",
                    warnings=["Processing task is already active"]
                )
            
            # Start the real-time processor
            self._processing_task = asyncio.create_task(
                self.real_time_processor.start_processing()
            )
            
            logger.info("Real-time processing pipeline started")
            
            return FeatureResponse(
                status=FeatureStatus.SUCCESS,
                message="Real-time processing started successfully"
            )
            
        except Exception as e:
            logger.error(f"Error starting processing: {e}", exc_info=True)
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message="Failed to start processing",
                errors=[str(e)]
            )
    
    async def stop_processing(self) -> FeatureResponse:
        """
        Stop the real-time event processing pipeline.
        
        Returns:
            FeatureResponse indicating success or failure
        """
        try:
            if self._processing_task and not self._processing_task.done():
                await self.real_time_processor.stop_processing()
                self._processing_task.cancel()
                try:
                    await self._processing_task
                except asyncio.CancelledError:
                    pass
                
                logger.info("Real-time processing pipeline stopped")
            
            return FeatureResponse(
                status=FeatureStatus.SUCCESS,
                message="Processing stopped successfully"
            )
            
        except Exception as e:
            logger.error(f"Error stopping processing: {e}", exc_info=True)
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message="Failed to stop processing",
                errors=[str(e)]
            )
    
    async def track_event(
        self,
        mvp_id: str,
        user_id: str,
        event_type: str,
        event_data: Optional[Dict[str, Any]] = None,
        timestamp: Optional[datetime] = None
    ) -> FeatureResponse:
        """
        Track a single engagement event through the entire pipeline.
        
        Args:
            mvp_id: ID of the MVP generating the event
            user_id: ID of the user generating the event
            event_type: Type of event (e.g., 'page_view', 'click', 'form_submit')
            event_data: Additional event metadata
            timestamp: Event timestamp (uses current time if not provided)
        
        Returns:
            FeatureResponse with validation and queuing results
        """
        start_time = datetime.utcnow()
        
        if not self._initialized:
            return FeatureResponse(
                status=FeatureStatus.FAILURE,
                message="Feature not initialized",
                errors=["Feature must be initialized before tracking events"]
            )
        
        try:
            # Validate and queue event through event collector
            event_dict = {
                "mvp_id": mvp_id,
                "user_id": user_id,
                "event_type": event_type,
                "event_data": event_data or {},
                "timestamp": (timestamp or datetime.utcnow()).isoformat()
            }
            
            validation_result = await self.event_collector.validate_and_queue_event(
                event_dict
            )
            
            if not validation_result.is_valid:
                return FeatureResponse(
                    status=FeatureStatus.FAILURE,
                    message="Event validation failed",
                    errors=validation_result.errors,
                    warnings=validation_result.warnings
                )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Check if we're meeting latency targets
            if processing_time > self.config.target_latency_seconds * 1000:
                warnings = [f"Event processing exceeded target latency: {processing_time}ms"]
            else:
                warnings = []
            
            return FeatureResponse(
                status=FeatureStatus.SUCCESS,
                message="Event successfully tracked",
                data={
                    "event_id": validation_result.event_id,
                    "queued": True,
                    "validation_passed": True
                },
                warnings=warnings,
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error tracking event: {e}", exc_info=True)
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message="Failed to track event",
                errors=[str(e)],
                processing_time_ms=processing_time
            )
    
    async def track_events_batch(
        self,
        events: List[Dict[str, Any]]
    ) -> FeatureResponse:
        """
        Track multiple engagement events in batch for improved throughput.
        
        Args:
            events: List of event dictionaries with mvp_id, user_id, event_type, etc.
        
        Returns:
            FeatureResponse with batch processing results
        """
        start_time = datetime.utcnow()
        
        if not self._initialized:
            return FeatureResponse(
                status=FeatureStatus.FAILURE,
                message="Feature not initialized",
                errors=["Feature must be initialized before tracking events"]
            )
        
        try:
            successful = 0
            failed = 0
            errors = []
            
            for event in events:
                try:
                    validation_result = await self.event_collector.validate_and_queue_event(
                        event
                    )
                    if validation_result.is_valid:
                        successful += 1
                    else:
                        failed += 1
                        errors.extend(validation_result.errors)
                except Exception as e:
                    failed += 1
                    errors.append(f"Event processing error: {str(e)}")
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            if failed == 0:
                status = FeatureStatus.SUCCESS
                message = f"All {successful} events tracked successfully"
            elif successful == 0:
                status = FeatureStatus.FAILURE
                message = f"All {failed} events failed"
            else:
                status = FeatureStatus.PARTIAL_SUCCESS
                message = f"{successful} events tracked, {failed} failed"
            
            return FeatureResponse(
                status=status,
                message=message,
                data={
                    "total_events": len(events),
                    "successful": successful,
                    "failed": failed,
                    "throughput_events_per_sec": len(events) / (processing_time / 1000)
                },
                errors=errors[:10] if errors else [],  # Limit error list
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error tracking batch events: {e}", exc_info=True)
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message="Failed to track batch events",
                errors=[str(e)],
                processing_time_ms=processing_time
            )
    
    async def get_current_metrics(
        self,
        mvp_id: str,
        include_realtime: bool = True
    ) -> FeatureResponse:
        """
        Get current engagement metrics for an MVP from cache.
        
        Args:
            mvp_id: ID of the MVP
            include_realtime: Whether to include real-time metrics
        
        Returns:
            FeatureResponse with current metrics
        """
        start_time = datetime.utcnow()
        
        if not self._initialized:
            return FeatureResponse(
                status=FeatureStatus.FAILURE,
                message="Feature not initialized",
                errors=["Feature must be initialized before retrieving metrics"]
            )
        
        try:
            metrics = {}
            
            # Get cached metrics
            cached_metrics = await self.engagement_cache.get_metrics(mvp_id)
            if cached_metrics:
                metrics.update(cached_metrics)
            
            # Get real-time dashboard metrics if requested
            if include_realtime and self.real_time_processor:
                dashboard_metrics = await self.real_time_processor.get_dashboard_metrics(
                    mvp_id
                )
                if dashboard_metrics:
                    metrics["realtime"] = dashboard_metrics
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return FeatureResponse(
                status=FeatureStatus.SUCCESS,
                message="Metrics retrieved successfully",
                data={
                    "mvp_id": mvp_id,
                    "metrics": metrics,
                    "cached": bool(cached_metrics),
                    "timestamp": datetime.utcnow().isoformat()
                },
                processing_time_ms=processing_time
            )
            
        except Exception as e:
            logger.error(f"Error getting metrics: {e}", exc_info=True)
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message="Failed to retrieve metrics",
                errors=[str(e)],
                processing_time_ms=processing_time
            )
    
    async def get_session_metrics(
        self,
        mvp_id: str,
        user_id: Optional[str] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None
    ) -> FeatureResponse:
        """
        Get session metrics for an MVP, optionally filtered by user and time range.
        
        Args:
            mvp_id: ID of the MVP
            user_id: Optional user ID to filter sessions
            start_time: Optional start of time range
            end_time: Optional end of time range
        
        Returns:
            FeatureResponse with session metrics
        """
        query_start_time = datetime.utcnow()
        
        if not self._initialized:
            return FeatureResponse(
                status=FeatureStatus.FAILURE,
                message="Feature not initialized",
                errors=["Feature must be initialized before retrieving session metrics"]
            )
        
        try:
            # Get sessions from tracker
            sessions = await self.session_tracker.get_sessions(
                mvp_id=mvp_id,
                user_id=user_id,
                start_time=start_time,
                end_time=end_time
            )
            
            # Calculate aggregate metrics
            if sessions:
                total_sessions = len(sessions)
                active_sessions = sum(1 for s in sessions if s.is_active)
                total_duration = sum(s.duration_seconds for s in sessions)
                avg_duration = total_duration / total_sessions if total_sessions > 0 else 0
                
                metrics = {
                    "total_sessions": total_sessions,
                    "active_sessions": active_sessions,
                    "completed_sessions": total_sessions - active_sessions,
                    "total_duration_seconds": total_duration,
                    "average_duration_seconds": avg_duration,
                    "sessions": [s.to_dict() for s in sessions[:100]]  # Limit response size
                }
            else:
                metrics = {
                    "total_sessions": 0,
                    "active_sessions": 0,
                    "completed_sessions": 0,
                    "sessions": []
                }
            
            processing_time = (datetime.utcnow() - query_start_time).total