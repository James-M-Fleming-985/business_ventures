from datetime import datetime
from typing import List, Optional
from uuid import UUID

import redis.asyncio as redis
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.dependencies import get_db, get_redis
from app.db.models import Worker, IngestionJob
from app.models.status import (
    WorkerStatus,
    WorkerListResponse,
    IngestionStatus,
    IngestionListResponse,
    SystemMetrics,
)
from app.services.metrics import MetricsService

router = APIRouter()


@router.get("/workers", response_model=WorkerListResponse)
async def list_workers(
    active_only: bool = Query(False, description="Filter active workers only"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> WorkerListResponse:
    """List all registered workers and their status."""
    query = select(Worker)
    
    if active_only:
        query = query.where(Worker.is_active == True)
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    workers = result.scalars().all()
    
    worker_statuses = [
        WorkerStatus(
            id=worker.id,
            name=worker.name,
            status="active" if worker.is_active else "inactive",
            last_heartbeat=worker.last_heartbeat,
            tasks_completed=worker.tasks_completed,
            tasks_failed=worker.tasks_failed,
            current_task=worker.current_task,
            metadata=worker.metadata or {},
        )
        for worker in workers
    ]
    
    return WorkerListResponse(
        workers=worker_statuses,
        total=len(worker_statuses),
        limit=limit,
        offset=offset,
    )


@router.get("/workers/{worker_id}", response_model=WorkerStatus)
async def get_worker_status(
    worker_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> WorkerStatus:
    """Get detailed status of a specific worker."""
    result = await db.execute(
        select(Worker).where(Worker.id == worker_id)
    )
    worker = result.scalar_one_or_none()
    
    if not worker:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Worker {worker_id} not found",
        )
    
    return WorkerStatus(
        id=worker.id,
        name=worker.name,
        status="active" if worker.is_active else "inactive",
        last_heartbeat=worker.last_heartbeat,
        tasks_completed=worker.tasks_completed,
        tasks_failed=worker.tasks_failed,
        current_task=worker.current_task,
        metadata=worker.metadata or {},
    )


@router.get("/ingestions", response_model=IngestionListResponse)
async def list_ingestions(
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db: AsyncSession = Depends(get_db),
) -> IngestionListResponse:
    """List ingestion jobs and their status."""
    query = select(IngestionJob).order_by(IngestionJob.created_at.desc())
    
    if status_filter:
        query = query.where(IngestionJob.status == status_filter)
    
    query = query.offset(offset).limit(limit)
    result = await db.execute(query)
    jobs = result.scalars().all()
    
    ingestion_statuses = [
        IngestionStatus(
            id=job.id,
            source_type=job.source_type,
            source_url=job.source_url,
            status=job.status,
            created_at=job.created_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            items_processed=job.items_processed,
            items_failed=job.items_failed,
            error_message=job.error_message,
            metadata=job.metadata or {},
        )
        for job in jobs
    ]
    
    return IngestionListResponse(
        ingestions=ingestion_statuses,
        total=len(ingestion_statuses),
        limit=limit,
        offset=offset,
    )


@router.get("/ingestions/{job_id}", response_model=IngestionStatus)
async def get_ingestion_status(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
) -> IngestionStatus:
    """Get detailed status of a specific ingestion job."""
    result = await db.execute(
        select(IngestionJob).where(IngestionJob.id == job_id)
    )
    job = result.scalar_one_or_none()
    
    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Ingestion job {job_id} not found",
        )
    
    return IngestionStatus(
        id=job.id,
        source_type=job.source_type,
        source_url=job.source_url,
        status=job.status,
        created_at=job.created_at,
        started_at=job.started_at,
        completed_at=job.completed_at,
        items_processed=job.items_processed,
        items_failed=job.items_failed,
        error_message=job.error_message,
        metadata=job.metadata or {},
    )


@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics(
    redis_client: redis.Redis = Depends(get_redis),
    db: AsyncSession = Depends(get_db),
) -> SystemMetrics:
    """Get system-wide metrics and statistics."""
    metrics_service = MetricsService(redis_client, db)
    return await metrics_service.get_system_metrics()