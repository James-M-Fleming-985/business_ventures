"""Celery background tasks for data ingestion.

These tasks run asynchronously to process data ingestion workflows.
"""

from app.celery_app import celery_app
from app.integration.orchestrator import SystemOrchestrator
from typing import Dict, Any
import logging

logger = logging.getLogger(__name__)


@celery_app.task(bind=True, max_retries=3)
def ingest_data_task(
    self,
    source: str,
    data_type: str,
    params: Dict[str, Any] = None
) -> Dict[str, Any]:
    """Background task for data ingestion.
    
    Args:
        source: Data source identifier
        data_type: Type of data
        params: Additional parameters
        
    Returns:
        Task result with processing status
    """
    try:
        import asyncio
        orchestrator = SystemOrchestrator()
        
        # Run async orchestrator in sync context
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        result = loop.run_until_complete(
            orchestrator.ingest_data(source, data_type, params or {})
        )
        loop.close()
        
        logger.info(
            f"Task complete: {result['records_processed']} records from {source}"
        )
        return result
        
    except Exception as exc:
        logger.error(f"Task failed: {exc}")
        self.retry(exc=exc, countdown=60)


@celery_app.task
def health_check_task() -> Dict[str, str]:
    """Periodic health check task.
    
    Returns:
        Health status
    """
    import asyncio
    orchestrator = SystemOrchestrator()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    status = loop.run_until_complete(orchestrator.get_system_status())
    loop.close()
    
    return status


@celery_app.task
def cleanup_old_data_task(days: int = 90) -> Dict[str, Any]:
    """Cleanup data older than specified days.
    
    Args:
        days: Number of days to keep
        
    Returns:
        Cleanup result
    """
    logger.info(f"Cleanup task started: removing data older than {days} days")
    
    # TODO: Implement actual cleanup logic
    return {
        'status': 'success',
        'records_deleted': 0,
        'retention_days': days
    }
