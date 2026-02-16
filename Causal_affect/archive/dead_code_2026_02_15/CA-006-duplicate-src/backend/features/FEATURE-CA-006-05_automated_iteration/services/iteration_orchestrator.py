from typing import List, Optional, Dict, Any
from datetime import datetime
from uuid import UUID
import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from ..models.iteration import (
    IterationCreate,
    IterationUpdate,
    IterationResponse,
    IterationStatus,
    IterationType,
    IterationMetrics
)
from ..db.repositories.iteration_repository import IterationRepository
from ..db.repositories.archive_repository import ArchiveRepository
from .archive_manager import ArchiveManager
from core.exceptions import (
    ResourceNotFoundError,
    BusinessLogicError,
    ValidationError
)
from core.events import EventBus, Event
from core.cache import CacheManager

logger = logging.getLogger(__name__)


class IterationOrchestrator:
    """Orchestrates automated iteration lifecycle and state management."""

    def __init__(
        self,
        iteration_repo: IterationRepository,
        archive_repo: ArchiveRepository,
        archive_manager: ArchiveManager,
        event_bus: EventBus,
        cache_manager: CacheManager
    ):
        self.iteration_repo = iteration_repo
        self.archive_repo = archive_repo
        self.archive_manager = archive_manager
        self.event_bus = event_bus
        self.cache_manager = cache_manager
        self._active_iterations: Dict[UUID, asyncio.Task] = {}

    async def create_iteration(
        self,
        db: AsyncSession,
        iteration_data: IterationCreate,
        user_id: UUID
    ) -> IterationResponse:
        """Create and start a new iteration."""
        try:
            # Validate iteration parameters
            await self._validate_iteration_params(iteration_data)

            # Create iteration record
            iteration = await self.iteration_repo.create(
                db,
                iteration_data,
                user_id
            )

            # Initialize metrics
            await self._initialize_metrics(db, iteration.id)

            # Start iteration processing
            task = asyncio.create_task(
                self._execute_iteration(db, iteration.id)
            )
            self._active_iterations[iteration.id] = task

            # Publish creation event
            await self.event_bus.publish(
                Event(
                    type="iteration.created",
                    data={"iteration_id": str(iteration.id)}
                )
            )

            return iteration

        except Exception as e:
            logger.error(f"Failed to create iteration: {str(e)}")
            raise BusinessLogicError(f"Failed to create iteration: {str(e)}")

    async def update_iteration(
        self,
        db: AsyncSession,
        iteration_id: UUID,
        update_data: IterationUpdate,
        user_id: UUID
    ) -> IterationResponse:
        """Update iteration configuration."""
        iteration = await self.iteration_repo.get(db, iteration_id)
        if not iteration:
            raise ResourceNotFoundError(f"Iteration {iteration_id} not found")

        # Validate state for updates
        if iteration.status in [IterationStatus.COMPLETED, IterationStatus.FAILED]:
            raise BusinessLogicError(
                f"Cannot update iteration in {iteration.status} state"
            )

        # Apply updates
        updated = await self.iteration_repo.update(
            db,
            iteration_id,
            update_data
        )

        # Invalidate cache
        await self.cache_manager.delete(f"iteration:{iteration_id}")

        return updated

    async def pause_iteration(
        self,
        db: AsyncSession,
        iteration_id: UUID,
        user_id: UUID
    ) -> IterationResponse:
        """Pause an active iteration."""
        iteration = await self.iteration_repo.get(db, iteration_id)
        if not iteration:
            raise ResourceNotFoundError(f"Iteration {iteration_id} not found")

        if iteration.status != IterationStatus.RUNNING:
            raise BusinessLogicError(
                f"Cannot pause iteration in {iteration.status} state"
            )

        # Cancel active task
        if iteration_id in self._active_iterations:
            self._active_iterations[iteration_id].cancel()
            del self._active_iterations[iteration_id]

        # Update status
        update_data = IterationUpdate(status=IterationStatus.PAUSED)
        return await self.iteration_repo.update(db, iteration_id, update_data)

    async def resume_iteration(
        self,
        db: AsyncSession,
        iteration_id: UUID,
        user_id: UUID
    ) -> IterationResponse:
        """Resume a paused iteration."""
        iteration = await self.iteration_repo.get(db, iteration_id)
        if not iteration:
            raise ResourceNotFoundError(f"Iteration {iteration_id} not found")

        if iteration.status != IterationStatus.PAUSED:
            raise BusinessLogicError(
                f"Cannot resume iteration in {iteration.status} state"
            )

        # Update status and restart
        update_data = IterationUpdate(status=IterationStatus.PENDING)
        iteration = await self.iteration_repo.update(db, iteration_id, update_data)

        # Restart processing
        task = asyncio.create_task(
            self._execute_iteration(db, iteration_id)
        )
        self._active_iterations[iteration_id] = task

        return iteration

    async def stop_iteration(
        self,
        db: AsyncSession,
        iteration_id: UUID,
        user_id: UUID
    ) -> IterationResponse:
        """Stop and finalize an iteration."""
        iteration = await self.iteration_repo.get(db, iteration_id)
        if not iteration:
            raise ResourceNotFoundError(f"Iteration {iteration_id} not found")

        # Cancel active task
        if iteration_id in self._active_iterations:
            self._active_iterations[iteration_id].cancel()
            del self._active_iterations[iteration_id]

        # Archive results
        archive_id = await self.archive_manager.archive_iteration(
            db,
            iteration_id,
            user_id
        )

        # Update status
        update_data = IterationUpdate(
            status=IterationStatus.COMPLETED,
            completed_at=datetime.utcnow(),
            archive_id=archive_id
        )
        return await self.iteration_repo.update(db, iteration_id, update_data)

    async def get_iteration_metrics(
        self,
        db: AsyncSession,
        iteration_id: UUID
    ) -> IterationMetrics:
        """Get current iteration metrics."""
        # Check cache first
        cache_key = f"metrics:{iteration_id}"
        cached = await self.cache_manager.get(cache_key)
        if cached:
            return IterationMetrics(**cached)

        iteration = await self.iteration_repo.get(db, iteration_id)
        if not iteration:
            raise ResourceNotFoundError(f"Iteration {iteration_id} not found")

        metrics = await self._calculate_metrics(db, iteration)
        
        # Cache for 30 seconds
        await self.cache_manager.set(
            cache_key,
            metrics.dict(),
            ttl=30
        )

        return metrics

    async def _execute_iteration(self, db: AsyncSession, iteration_id: UUID):
        """Execute iteration processing loop."""
        try:
            # Update status to running
            await self.iteration_repo.update(
                db,
                iteration_id,
                IterationUpdate(status=IterationStatus.RUNNING)
            )

            iteration = await self.iteration_repo.get(db, iteration_id)
            if not iteration:
                return

            # Execute based on iteration type
            if iteration.iteration_type == IterationType.TIME_BASED:
                await self._execute_time_based(db, iteration)
            elif iteration.iteration_type == IterationType.COUNT_BASED:
                await self._execute_count_based(db, iteration)
            elif iteration.iteration_type == IterationType.CONDITION_BASED:
                await self._execute_condition_based(db, iteration)

            # Mark as completed
            await self.iteration_repo.update(
                db,
                iteration_id,
                IterationUpdate(
                    status=IterationStatus.COMPLETED,
                    completed_at=datetime.utcnow()
                )
            )

        except asyncio.CancelledError:
            logger.info(f"Iteration {iteration_id} cancelled")
            raise
        except Exception as e:
            logger.error(f"Iteration {iteration_id} failed: {str(e)}")
            await self.iteration_repo.update(
                db,
                iteration_id,
                IterationUpdate(
                    status=IterationStatus.FAILED,
                    error_message=str(e)
                )
            )

    async def _execute_time_based(
        self,
        db: AsyncSession,
        iteration: IterationResponse
    ):
        """Execute time-based iteration."""
        start_time = datetime.utcnow()
        duration = iteration.parameters.get("duration_seconds", 3600)
        
        while (datetime.utcnow() - start_time).total_seconds() < duration:
            await self._process_iteration_step(db, iteration)
            await asyncio.sleep(iteration.parameters.get("interval_seconds", 60))

    async def _execute_count_based(
        self,
        db: AsyncSession,
        iteration: IterationResponse
    ):
        """Execute count-based iteration."""
        target_count = iteration.parameters.get("target_count", 100)
        current_count = 0
        
        while current_count < target_count:
            await self._process_iteration_step(db, iteration)
            current_count += 1
            await asyncio.sleep(iteration.parameters.get("interval_seconds", 1))

    async def _execute_condition_based(
        self,
        db: AsyncSession,
        iteration: IterationResponse
    ):
        """Execute condition-based iteration."""
        while True:
            result = await self._process_iteration_step(db, iteration)
            
            # Check termination condition
            if await self._check_condition(db, iteration, result):
                break
                
            await asyncio.sleep(iteration.parameters.get("interval_seconds", 60))

    async def _process_iteration_step(
        self,
        db: AsyncSession,
        iteration: IterationResponse
    ) -> Dict[str, Any]:
        """Process a single iteration step."""
        # This would contain the actual iteration logic
        # For now, return mock result
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "iteration_id": str(iteration.id),
            "step_result": "success"
        }

    async def _check_condition(
        self,
        db: AsyncSession,
        iteration: IterationResponse,
        result: Dict[str, Any]
    ) -> bool:
        """Check if termination condition is met."""
        condition = iteration.parameters.get("termination_condition")
        if not condition:
            return False
            
        # Evaluate condition based on result
        # This is a simplified example
        if condition.get("type") == "threshold":
            value = result.get(condition.get("field", "value"), 0)
            threshold = condition.get("threshold", 0)
            return value >= threshold
            
        return False

    async def _validate_iteration_params(self, iteration_data: IterationCreate):
        """Validate iteration parameters."""
        if iteration_data.iteration_type == IterationType.TIME_BASED:
            if "duration_seconds" not in iteration_data.parameters:
                raise ValidationError("duration_seconds required for time-based iteration")
        elif iteration_data.iteration_type == IterationType.COUNT_BASED:
            if "target_count" not in iteration_data.parameters:
                raise ValidationError("target_count required for count-based iteration")
        elif iteration_data.iteration_type == IterationType.CONDITION_BASED:
            if "termination_condition" not in iteration_data.parameters:
                raise ValidationError("termination_condition required for condition-based iteration")

    async def _initialize_metrics(self, db: AsyncSession, iteration_id: UUID):
        """Initialize iteration metrics."""
        # Initialize metrics storage
        metrics = {
            "total_steps": 0,
            "successful_steps": 0,
            "failed_steps": 0,
            "average_step_duration": 0,
            "start_time": datetime.utcnow().isoformat()
        }
        await self.cache_manager.set(
            f"metrics:{iteration_id}",
            metrics,
            ttl=3600
        )

    async def _calculate_metrics(
        self,
        db: AsyncSession,
        iteration: IterationResponse
    ) -> IterationMetrics:
        """Calculate current iteration metrics."""
        # This would aggregate actual metrics from iteration execution
        return IterationMetrics(
            iteration_id=iteration.id,
            total_steps=100,
            successful_steps=95,
            failed_steps=5,
            average_step_duration=1.5,
            current_rate=60.0,
            estimated_completion=datetime.utcnow(),
            resource_usage={
                "cpu_percent": 25.5,
                "memory_mb": 512,
                "api_calls": 1000
            }
        )
