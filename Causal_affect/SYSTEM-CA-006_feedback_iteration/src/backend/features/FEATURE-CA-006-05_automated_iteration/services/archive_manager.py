from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from uuid import UUID
import json
import gzip
import asyncio
import logging

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError

from ..models.archive import (
    ArchiveCreate,
    ArchiveUpdate,
    ArchiveResponse,
    ArchiveStatus,
    ArchiveFilter
)
from ..models.iteration import IterationResponse
from ..db.repositories.archive_repository import ArchiveRepository
from ..db.repositories.iteration_repository import IterationRepository
from core.exceptions import (
    ResourceNotFoundError,
    BusinessLogicError,
    StorageError
)
from core.storage import StorageService
from core.events import EventBus, Event
from core.cache import CacheManager

logger = logging.getLogger(__name__)


class ArchiveManager:
    """Manages iteration archive lifecycle and storage."""

    def __init__(
        self,
        archive_repo: ArchiveRepository,
        iteration_repo: IterationRepository,
        storage_service: StorageService,
        event_bus: EventBus,
        cache_manager: CacheManager
    ):
        self.archive_repo = archive_repo
        self.iteration_repo = iteration_repo
        self.storage_service = storage_service
        self.event_bus = event_bus
        self.cache_manager = cache_manager
        self._archive_queue: asyncio.Queue = asyncio.Queue()
        self._worker_task: Optional[asyncio.Task] = None

    async def start(self):
        """Start archive worker."""
        self._worker_task = asyncio.create_task(self._archive_worker())

    async def stop(self):
        """Stop archive worker."""
        if self._worker_task:
            self._worker_task.cancel()
            try:
                await self._worker_task
            except asyncio.CancelledError:
                pass

    async def archive_iteration(
        self,
        db: AsyncSession,
        iteration_id: UUID,
        user_id: UUID
    ) -> UUID:
        """Archive completed iteration data."""
        try:
            # Get iteration data
            iteration = await self.iteration_repo.get(db, iteration_id)
            if not iteration:
                raise ResourceNotFoundError(f"Iteration {iteration_id} not found")

            # Create archive record
            archive_data = ArchiveCreate(
                iteration_id=iteration_id,
                name=f"Archive of {iteration.name}",
                description=f"Archived data from iteration {iteration.name}",
                metadata={
                    "iteration_type": iteration.iteration_type,
                    "parameters": iteration.parameters,
                    "started_at": iteration.created_at.isoformat(),
                    "completed_at": datetime.utcnow().isoformat()
                }
            )

            archive = await self.archive_repo.create(db, archive_data, user_id)

            # Queue for async processing
            await self._archive_queue.put({
                "archive_id": archive.id,
                "iteration_id": iteration_id,
                "user_id": user_id
            })

            # Publish event
            await self.event_bus.publish(
                Event(
                    type="archive.created",
                    data={
                        "archive_id": str(archive.id),
                        "iteration_id": str(iteration_id)
                    }
                )
            )

            return archive.id

        except Exception as e:
            logger.error(f"Failed to create archive: {str(e)}")
            raise BusinessLogicError(f"Failed to create archive: {str(e)}")

    async def get_archive(
        self,
        db: AsyncSession,
        archive_id: UUID,
        user_id: UUID
    ) -> ArchiveResponse:
        """Get archive details."""
        archive = await self.archive_repo.get(db, archive_id)
        if not archive:
            raise ResourceNotFoundError(f"Archive {archive_id} not found")

        # Check ownership
        if archive.created_by != user_id:
            raise BusinessLogicError("Access denied to archive")

        return archive

    async def list_archives(
        self,
        db: AsyncSession,
        user_id: UUID,
        filter_params: Optional[ArchiveFilter] = None,
        skip: int = 0,
        limit: int = 100
    ) -> List[ArchiveResponse]:
        """List user's archives with filtering."""
        return await self.archive_repo.list_by_user(
            db,
            user_id,
            filter_params,
            skip,
            limit
        )

    async def restore_archive(
        self,
        db: AsyncSession,
        archive_id: UUID,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Restore archived iteration data."""
        archive = await self.get_archive(db, archive_id, user_id)
        
        if archive.status != ArchiveStatus.COMPLETED:
            raise BusinessLogicError(f"Cannot restore archive in {archive.status} state")

        try:
            # Download from storage
            data = await self.storage_service.download(
                archive.storage_path
            )

            # Decompress
            decompressed = gzip.decompress(data)
            restored_data = json.loads(decompressed.decode('utf-8'))

            # Update access time
            await self.archive_repo.update(
                db,
                archive_id,
                ArchiveUpdate(last_accessed_at=datetime.utcnow())
            )

            return restored_data

        except Exception as e:
            logger.error(f"Failed to restore archive: {str(e)}")
            raise StorageError(f"Failed to restore archive: {str(e)}")

    async def delete_archive(
        self,
        db: AsyncSession,
        archive_id: UUID,
        user_id: UUID
    ) -> bool:
        """Delete archive and associated data."""
        archive = await self.get_archive(db, archive_id, user_id)

        try:
            # Delete from storage
            if archive.storage_path:
                await self.storage_service.delete(archive.storage_path)

            # Delete record
            await self.archive_repo.delete(db, archive_id)

            # Clear cache
            await self.cache_manager.delete(f"archive:{archive_id}")

            # Publish event
            await self.event_bus.publish(
                Event(
                    type="archive.deleted",
                    data={"archive_id": str(archive_id)}
                )
            )

            return True

        except Exception as e:
            logger.error(f"Failed to delete archive: {str(e)}")
            raise BusinessLogicError(f"Failed to delete archive: {str(e)}")

    async def cleanup_old_archives(
        self,
        db: AsyncSession,
        retention_days: int = 90
    ) -> int:
        """Clean up archives older than retention period."""
        cutoff_date = datetime.utcnow() - timedelta(days=retention_days)
        
        old_archives = await self.archive_repo.find_old_archives(
            db,
            cutoff_date
        )

        deleted_count = 0
        for archive in old_archives:
            try:
                await self.delete_archive(db, archive.id, archive.created_by)
                deleted_count += 1
            except Exception as e:
                logger.error(f"Failed to delete old archive {archive.id}: {str(e)}")

        logger.info(f"Cleaned up {deleted_count} old archives")
        return deleted_count

    async def get_archive_statistics(
        self,
        db: AsyncSession,
        user_id: UUID
    ) -> Dict[str, Any]:
        """Get user's archive statistics."""
        cache_key = f"archive_stats:{user_id}"
        cached = await self.cache_manager.get(cache_key)
        if cached:
            return cached

        stats = await self.archive_repo.get_user_statistics(db, user_id)
        
        # Cache for 5 minutes
        await self.cache_manager.set(cache_key, stats, ttl=300)
        
        return stats

    async def _archive_worker(self):
        """Background worker to process archive queue."""
        while True:
            try:
                # Get item from queue
                item = await self._archive_queue.get()
                
                # Process archive
                await self._process_archive(item)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"Archive worker error: {str(e)}")
                await asyncio.sleep(5)  # Back off on error

    async def _process_archive(
        self,
        archive_item: Dict[str, Any]
    ):
        """Process single archive job."""
        archive_id = archive_item["archive_id"]
        iteration_id = archive_item["iteration_id"]
        
        async with AsyncSession() as db:
            try:
                # Update status
                await self.archive_repo.update(
                    db,
                    archive_id,
                    ArchiveUpdate(status=ArchiveStatus.PROCESSING)
                )

                # Collect iteration data
                data = await self._collect_iteration_data(db, iteration_id)

                # Compress data
                json_data = json.dumps(data).encode('utf-8')
                compressed = gzip.compress(json_data)

                # Upload to storage
                storage_path = f"archives/{archive_id}/data.gz"
                await self.storage_service.upload(
                    storage_path,
                    compressed,
                    content_type="application/gzip"
                )

                # Update archive record
                await self.archive_repo.update(
                    db,
                    archive_id,
                    ArchiveUpdate(
                        status=ArchiveStatus.COMPLETED,
                        storage_path=storage_path,
                        size_bytes=len(compressed),
                        completed_at=datetime.utcnow()
                    )
                )

                # Publish completion event
                await self.event_bus.publish(
                    Event(
                        type="archive.completed",
                        data={"archive_id": str(archive_id)}
                    )
                )

            except Exception as e:
                logger.error(f"Archive processing failed: {str(e)}")
                await self.archive_repo.update(
                    db,
                    archive_id,
                    ArchiveUpdate(
                        status=ArchiveStatus.FAILED,
                        error_message=str(e)
                    )
                )

    async def _collect_iteration_data(
        self,
        db: AsyncSession,
        iteration_id: UUID
    ) -> Dict[str, Any]:
        """Collect all data related to an iteration."""
        iteration = await self.iteration_repo.get(db, iteration_id)
        if not iteration:
            raise ResourceNotFoundError(f"Iteration {iteration_id} not found")

        # Collect iteration data and results
        # This is a simplified example - actual implementation would
        # gather all relevant data from various sources
        return {
            "iteration": {
                "id": str(iteration.id),
                "name": iteration.name,
                "type": iteration.iteration_type,
                "parameters": iteration.parameters,
                "status": iteration.status,
                "created_at": iteration.created_at.isoformat(),
                "updated_at": iteration.updated_at.isoformat()
            },
            "results": {
                # This would include actual iteration results
                "total_executions": 1000,
                "successful_executions": 950,
                "failed_executions": 50,
                "metrics": {
                    "average_duration": 1.5,
                    "max_duration": 5.2,
                    "min_duration": 0.8
                }
            },
            "metadata": {
                "archived_at": datetime.utcnow().isoformat(),
                "version": "1.0"
            }
        }
