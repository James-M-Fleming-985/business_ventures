```python
import asyncio
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResourceType(Enum):
    SERVICE = "service"
    DATABASE = "database"
    VOLUME = "volume"
    NETWORK = "network"
    DEPLOYMENT = "deployment"


class CleanupStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class Resource:
    """Represents a Railway resource to be cleaned up."""
    id: str
    type: ResourceType
    name: str
    dependencies: List[str] = field(default_factory=list)
    status: CleanupStatus = CleanupStatus.PENDING
    metadata: Dict = field(default_factory=dict)


@dataclass
class CleanupResult:
    """Result of a cleanup operation."""
    success: bool
    total_resources: int
    deallocated_resources: int
    orphaned_resources: int
    duration_seconds: float
    errors: List[str] = field(default_factory=list)

    @property
    def deallocation_percentage(self) -> float:
        """Calculate the percentage of successfully deallocated resources."""
        if self.total_resources == 0:
            return 100.0
        return (self.deallocated_resources / self.total_resources) * 100.0


class RailwayClient:
    """Mock Railway API client for service management."""

    def __init__(self):
        self._services: Dict[str, Resource] = {}
        self._shutdown_services: Set[str] = set()

    async def list_services(self) -> List[Resource]:
        """List all Railway services."""
        return list(self._services.values())

    async def shutdown_service(self, service_id: str, graceful: bool = True) -> bool:
        """Shutdown a Railway service gracefully."""
        if service_id not in self._services:
            raise ValueError(f"Service {service_id} not found")
        
        if graceful:
            await asyncio.sleep(0.1)  # Simulate graceful shutdown
        
        self._shutdown_services.add(service_id)
        return True

    async def delete_service(self, service_id: str) -> bool:
        """Delete a Railway service."""
        if service_id not in self._services:
            raise ValueError(f"Service {service_id} not found")
        
        if service_id in self._services:
            del self._services[service_id]
        return True

    async def backup_service_data(self, service_id: str) -> str:
        """Backup service data before deletion."""
        if service_id not in self._services:
            raise ValueError(f"Service {service_id} not found")
        
        await asyncio.sleep(0.05)  # Simulate backup operation
        backup_id = f"backup_{service_id}_{datetime.now().timestamp()}"
        return backup_id

    async def verify_resource_deallocation(self, resource_id: str) -> bool:
        """Verify that a resource has been completely deallocated."""
        return resource_id not in self._services

    def add_service(self, resource: Resource):
        """Add a service for testing purposes."""
        self._services[resource.id] = resource


class InfrastructureCleanupService:
    """Service for cleaning up Railway infrastructure resources."""

    def __init__(self, railway_client: Optional[RailwayClient] = None):
        self.railway_client = railway_client or RailwayClient()
        self._cleanup_timeout = timedelta(minutes=5)
        self._resources: Dict[str, Resource] = {}

    async def shutdown_services(
        self,
        service_ids: List[str],
        backup_data: bool = True,
        graceful: bool = True
    ) -> CleanupResult:
        """
        Shutdown Railway services without data loss.
        
        Args:
            service_ids: List of service IDs to shutdown
            backup_data: Whether to backup data before shutdown
            graceful: Whether to perform graceful shutdown
            
        Returns:
            CleanupResult with operation details
        """
        start_time = datetime.now()
        errors = []
        deallocated = 0
        
        try:
            # Validate timeout
            if (datetime.now() - start_time) > self._cleanup_timeout:
                raise TimeoutError("Cleanup operation exceeded 5 minute limit")
            
            for service_id in service_ids:
                try:
                    # Backup data if requested
                    if backup_data:
                        await self.railway_client.backup_service_data(service_id)
                    
                    # Graceful shutdown
                    await self.railway_client.shutdown_service(service_id, graceful)
                    deallocated += 1
                    
                except Exception as e:
                    logger.error(f"Error shutting down service {service_id}: {e}")
                    errors.append(f"Service {service_id}: {str(e)}")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            return CleanupResult(
                success=len(errors) == 0,
                total_resources=len(service_ids),
                deallocated_resources=deallocated,
                orphaned_resources=len(service_ids) - deallocated,
                duration_seconds=duration,
                errors=errors
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Cleanup operation failed: {e}")
            return CleanupResult(
                success=False,
                total_resources=len(service_ids),
                deallocated_resources=deallocated,
                orphaned_resources=len(service_ids) - deallocated,
                duration_seconds=duration,
                errors=[str(e)]
            )

    async def cleanup_resources(
        self,
        resources: List[Resource],
        verify_deallocation: bool = True
    ) -> CleanupResult:
        """
        Clean up infrastructure resources with verification.
        
        Args:
            resources: List of resources to clean up
            verify_deallocation: Whether to verify complete deallocation
            
        Returns:
            CleanupResult with operation details
        """
        start_time = datetime.now()
        errors = []
        deallocated = 0
        orphaned = 0
        
        try:
            # Check timeout constraint
            if (datetime.now() - start_time) > self._cleanup_timeout:
                raise TimeoutError("Cleanup operation exceeded 5 minute limit")
            
            # Sort resources by dependency order (reverse topological sort)
            sorted_resources = self._sort_by_dependencies(resources)
            
            for resource in sorted_resources:
                try:
                    # Backup if service type
                    if resource.type == ResourceType.SERVICE:
                        await self.railway_client.backup_service_data(resource.id)
                    
                    # Delete the resource
                    await self._delete_resource(resource)
                    
                    # Verify deallocation if requested
                    if verify_deallocation:
                        is_deallocated = await self.railway_client.verify_resource_deallocation(
                            resource.id
                        )
                        if is_deallocated:
                            deallocated += 1
                        else:
                            orphaned += 1
                            errors.append(f"Resource {resource.id} not fully deallocated")
                    else:
                        deallocated += 1
                        
                except Exception as e:
                    logger.error(f"Error cleaning up resource {resource.id}: {e}")
                    orphaned += 1
                    errors.append(f"Resource {resource.id}: {str(e)}")
            
            duration = (datetime.now() - start_time).total_seconds()
            
            # Verify 100% deallocation requirement
            deallocation_pct = (deallocated / len(resources)) * 100.0 if resources else 100.0
            
            return CleanupResult(
                success=deallocation_pct == 100.0 and len(errors) == 0,
                total_resources=len(resources),
                deallocated_resources=deallocated,
                orphaned_resources=orphaned,
                duration_seconds=duration,
                errors=errors
            )
            
        except Exception as e:
            duration = (datetime.now() - start_time).total_seconds()
            logger.error(f"Cleanup operation failed: {e}")
            return CleanupResult(
                success=False,
                total_resources=len(resources),
                deallocated_resources=deallocated,
                orphaned_resources=len(resources) - deallocated,
                duration_seconds=duration,
                errors=[str(e)]
            )

    async def _delete_resource(self, resource: Resource):
        """Delete a single resource."""
        if resource.type == ResourceType.SERVICE:
            await self.railway_client.delete_service(resource.id)
        else:
            # Simulate deletion for other resource types
            await asyncio.sleep(0.05)

    def _sort_by_dependencies(self, resources: List[Resource]) -> List[Resource]:
        """Sort resources by dependency order (children before parents)."""
        resource_map = {r.id: r for r in resources}
        visited = set()
        result = []
        
        def visit(resource_id: str):
            if resource_id in visited or resource_id not in resource_map:
                return
            visited.add(resource_id)
            
            resource = resource_map[resource_id]
            for dep_id in resource.dependencies:
                visit(dep_id)
            
            result.append(resource_map[resource_id])
        
        for resource in resources:
            visit(resource.id)
        
        return result

    async def verify_complete_deallocation(
        self,
        resource_ids: List[str]
    ) -> Dict[str, bool]:
        """
        Verify that all resources have been completely deallocated.
        
        Args:
            resource_ids: List of resource IDs to verify
            
        Returns:
            Dictionary mapping resource IDs to deallocation status
        """
        results = {}
        
        for resource_id in resource_ids:
            try:
                is_deallocated = await self.railway_client.verify_resource_deallocation(
                    resource_id
                )
                results[resource_id] = is_deallocated
            except Exception as e:
                logger.error(f"Error verifying resource {resource_id}: {e}")
                results[resource_id] = False
        
        return results

    async def cleanup_with_timeout(
        self,
        resources: List[Resource],
        timeout_minutes: int = 5
    ) -> CleanupResult:
        """
        Clean up resources with a timeout constraint.
        
        Args:
            resources: List of resources to clean up
            timeout_minutes: Maximum time allowed for cleanup
            
        Returns:
            CleanupResult with operation details
        """
        try:
            result = await asyncio.wait_for(
                self.cleanup_resources(resources, verify_deallocation=True),
                timeout=timeout_minutes * 60
            )
            return result
        except asyncio.TimeoutError:
            return CleanupResult(
                success=False,
                total_resources=len(resources),
                deallocated_resources=0,
                orphaned_resources=len(resources),
                duration_seconds=timeout_minutes * 60,
                errors=[f"Cleanup exceeded {timeout_minutes} minute timeout"]
            )


async def main():
    """Example usage of the Infrastructure Cleanup Service."""
    client = RailwayClient()
    service = InfrastructureCleanupService(client)
    
    # Create test resources
    resources = [
        Resource(
            id="svc-1",
            type=ResourceType.SERVICE,
            name="web-service",
            dependencies=[]
        ),
        Resource(
            id="db-1",
            type=ResourceType.DATABASE,
            name="postgres-db",
            dependencies=["svc-1"]
        )
    ]
    
    # Add to client
    for resource in resources:
        if resource.type == ResourceType.SERVICE:
            client.add_service(resource)
    
    # Perform cleanup
    result = await service.cleanup_resources(resources)
    
    logger.info(f"Cleanup completed: {result.success}")
    logger.info(f"Deallocation: {result.deallocation_percentage}%")
    logger.info(f"Duration: {result.duration_seconds}s")


if __name__ == "__main__":
    asyncio.run(main())
```