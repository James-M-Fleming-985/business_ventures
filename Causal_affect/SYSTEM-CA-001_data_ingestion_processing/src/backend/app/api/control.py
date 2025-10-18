from datetime import datetime
from typing import Dict, Any, Optional
from uuid import UUID, uuid4

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, status, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_redis
from app.core.exceptions import ValidationError, TaskError
from app.models.control import (
    StartIngestionRequest,
    StartIngestionResponse,
    StopTaskRequest,
    ConfigUpdateRequest,
    ConfigUpdateResponse,
    TaskResponse,
)
from app.services.ingestion import IngestionService
from app.services.task_manager import TaskManager
from app.services.config import ConfigService

router = APIRouter()


@router.post("/ingestion/start", response_model=StartIngestionResponse)
async def start_ingestion(
    request: StartIngestionRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    redis_client: redis.Redis = Depends(get_redis),
) -> StartIngestionResponse:
    """Start a new ingestion task."""
    try:
        ingestion_service = IngestionService(db, redis_client)
        task_manager = TaskManager(redis_client)
        
        # Validate request
        await ingestion_service.validate_source(request.source_type, request.source_config)
        
        # Create job ID
        job_id = uuid4()
        
        # Register task
        task_info = {
            "job_id": str(job_id),
            "source_type": request.source_type,
            "source_config": request.source_config,
            "options": request.options or {},
            "created_at": datetime.utcnow().isoformat(),
        }
        
        await task_manager.register_task(str(job_id), "ingestion", task_info)
        
        # Queue task for processing
        background_tasks.add_task(
            ingestion_service.process_ingestion,
            job_id,
            request.source_type,
            request.source_config,
            request.options,
        )
        
        return StartIngestionResponse(
            job_id=job_id,
            status="queued",
            message="Ingestion task queued successfully",
            created_at=datetime.utcnow(),
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to start ingestion: {str(e)}",
        )


@router.post("/task/stop", response_model=TaskResponse)
async def stop_task(
    request: StopTaskRequest,
    redis_client: redis.Redis = Depends(get_redis),
) -> TaskResponse:
    """Stop a running task."""
    try:
        task_manager = TaskManager(redis_client)
        
        # Send stop signal
        success = await task_manager.stop_task(str(request.task_id), request.force)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {request.task_id} not found or already stopped",
            )
        
        return TaskResponse(
            task_id=request.task_id,
            status="stopping" if not request.force else "terminated",
            message="Stop signal sent to task",
            timestamp=datetime.utcnow(),
        )
        
    except TaskError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/task/{task_id}/pause", response_model=TaskResponse)
async def pause_task(
    task_id: UUID,
    redis_client: redis.Redis = Depends(get_redis),
) -> TaskResponse:
    """Pause a running task."""
    try:
        task_manager = TaskManager(redis_client)
        
        success = await task_manager.pause_task(str(task_id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found or not pausable",
            )
        
        return TaskResponse(
            task_id=task_id,
            status="paused",
            message="Task paused successfully",
            timestamp=datetime.utcnow(),
        )
        
    except TaskError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.post("/task/{task_id}/resume", response_model=TaskResponse)
async def resume_task(
    task_id: UUID,
    redis_client: redis.Redis = Depends(get_redis),
) -> TaskResponse:
    """Resume a paused task."""
    try:
        task_manager = TaskManager(redis_client)
        
        success = await task_manager.resume_task(str(task_id))
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Task {task_id} not found or not paused",
            )
        
        return TaskResponse(
            task_id=task_id,
            status="running",
            message="Task resumed successfully",
            timestamp=datetime.utcnow(),
        )
        
    except TaskError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.put("/config", response_model=ConfigUpdateResponse)
async def update_configuration(
    request: ConfigUpdateRequest,
    redis_client: redis.Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
) -> ConfigUpdateResponse:
    """Update system configuration."""
    try:
        config_service = ConfigService(db, redis_client)
        
        # Validate configuration
        await config_service.validate_config(request.section, request.config)
        
        # Update configuration
        updated = await config_service.update_config(
            request.section,
            request.config,
            request.merge,
        )
        
        # Apply immediately if requested
        if request.apply_immediately:
            await config_service.broadcast_config_change(request.section)
        
        return ConfigUpdateResponse(
            section=request.section,
            updated=updated,
            applied=request.apply_immediately,
            timestamp=datetime.utcnow(),
        )
        
    except ValidationError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )


@router.get("/config/{section}")
async def get_configuration(
    section: str,
    redis_client: redis.Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Any]:
    """Get current configuration for a section."""
    config_service = ConfigService(db, redis_client)
    config = await config_service.get_config(section)
    
    if not config:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Configuration section '{section}' not found",
        )
    
    return config