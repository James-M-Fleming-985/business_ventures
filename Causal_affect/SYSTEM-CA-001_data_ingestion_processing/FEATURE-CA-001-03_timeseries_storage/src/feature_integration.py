"""
Feature Integration Module for Time-Series Data Storage
Feature ID: FEATURE-CA-001-03

This module orchestrates the interaction between DB_Connection, Partitioner,
Indexer, and Compressor layers to provide comprehensive time-series data storage.
"""

from pathlib import Path
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Tuple, Union
from datetime import datetime, timedelta
from enum import Enum
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import layer implementations
from LAYER_CA_001_03_01_DB_Connection.LAYER_CA_001_03_01_db_connection.src.implementation import (
    DatabaseConnectionError, DatabaseConnection
)
from LAYER_CA_001_03_02_Partitioner.LAYER_CA_001_03_02_partitioner.src.implementation import (
    Partitioner
)
from LAYER_CA_001_03_03_Indexer.LAYER_CA_001_03_03_indexer.src.implementation import (
    IndexEntry, Indexer
)
from LAYER_CA_001_03_04_Compressor.LAYER_CA_001_03_04_compressor.src.implementation import (
    CompressionType, CompressionError, CompressionStats, FileMetadata, Compressor, BatchCompressor
)


class FeatureStatus(Enum):
    """Enumeration for feature operation status."""
    SUCCESS = "success"
    ERROR = "error"
    PARTIAL_SUCCESS = "partial_success"
    WARNING = "warning"


@dataclass
class FeatureConfig:
    """Configuration dataclass for Time-Series Data Storage feature."""
    # Database configuration
    db_connection_string: str
    db_pool_size: int = 10
    db_timeout: int = 30
    
    # Partitioner configuration
    partition_by: str = "time"  # Options: 'time', 'size', 'count'
    partition_interval: timedelta = timedelta(hours=1)
    max_partition_size: int = 1024 * 1024 * 100  # 100MB
    
    # Indexer configuration
    index_fields: List[str] = None
    index_cache_size: int = 1000
    
    # Compressor configuration
    compression_type: CompressionType = CompressionType.GZIP
    compression_level: int = 6
    batch_size: int = 100
    
    # General configuration
    enable_logging: bool = True
    log_level: str = "INFO"
    
    def __post_init__(self):
        """Initialize default values after dataclass creation."""
        if self.index_fields is None:
            self.index_fields = ['timestamp', 'metric_name', 'source']


@dataclass
class FeatureResponse:
    """Unified response dataclass for feature operations."""
    status: FeatureStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        """Initialize timestamp if not provided."""
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class TimeSeriesStorageOrchestrator:
    """
    Main orchestrator class for Time-Series Data Storage feature.
    
    This class coordinates the interaction between DB_Connection, Partitioner,
    Indexer, and Compressor layers to provide efficient time-series data storage
    with automatic partitioning, indexing, and compression.
    """
    
    def __init__(self, config: FeatureConfig):
        """
        Initialize the Time-Series Storage Orchestrator.
        
        Args:
            config: FeatureConfig instance containing all configuration parameters
            
        Raises:
            ValueError: If configuration is invalid
            RuntimeError: If layer initialization fails
        """
        self.config = config
        self._logger = self._setup_logging()
        
        # Initialize layers
        self._db_connection: Optional[DatabaseConnection] = None
        self._partitioner: Optional[Partitioner] = None
        self._indexer: Optional[Indexer] = None
        self._compressor: Optional[Compressor] = None
        self._batch_compressor: Optional[BatchCompressor] = None
        
        # Initialize all layers
        self._initialize_layers()
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger("TimeSeriesStorage")
        if self.config.enable_logging:
            level = getattr(logging, self.config.log_level.upper(), logging.INFO)
            logger.setLevel(level)
            
            # Configure handler if not already configured
            if not logger.handlers:
                handler = logging.StreamHandler()
                formatter = logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
                handler.setFormatter(formatter)
                logger.addHandler(handler)
        else:
            logger.setLevel(logging.CRITICAL)
            
        return logger
        
    def _initialize_layers(self) -> None:
        """
        Initialize all layer instances.
        
        Raises:
            RuntimeError: If any layer fails to initialize
        """
        try:
            # Initialize database connection
            self._logger.info("Initializing database connection...")
            self._db_connection = DatabaseConnection(
                connection_string=self.config.db_connection_string,
                pool_size=self.config.db_pool_size,
                timeout=self.config.db_timeout
            )
            
            # Initialize partitioner
            self._logger.info("Initializing partitioner...")
            self._partitioner = Partitioner()
            
            # Initialize indexer
            self._logger.info("Initializing indexer...")
            self._indexer = Indexer()
            
            # Initialize compressors
            self._logger.info("Initializing compressors...")
            self._compressor = Compressor(compression_type=self.config.compression_type)
            self._batch_compressor = BatchCompressor(
                compression_type=self.config.compression_type,
                batch_size=self.config.batch_size
            )
            
            self._logger.info("All layers initialized successfully")
            
        except Exception as e:
            error_msg = f"Failed to initialize layers: {str(e)}"
            self._logger.error(error_msg)
            raise RuntimeError(error_msg) from e
            
    def store_time_series_data(
        self,
        metric_name: str,
        data_points: List[Dict[str, Any]],
        compress: bool = True
    ) -> FeatureResponse:
        """
        Store time-series data with automatic partitioning, indexing, and optional compression.
        
        Args:
            metric_name: Name of the metric being stored
            data_points: List of data points, each containing 'timestamp' and 'value'
            compress: Whether to compress the data before storage
            
        Returns:
            FeatureResponse containing operation status and details
        """
        try:
            self._logger.info(f"Storing {len(data_points)} data points for metric: {metric_name}")
            
            # Validate input data
            validation_result = self._validate_data_points(data_points)
            if validation_result:
                return FeatureResponse(
                    status=FeatureStatus.ERROR,
                    message="Data validation failed",
                    errors=validation_result
                )
            
            # Step 1: Partition the data
            partitions = self._partition_data(metric_name, data_points)
            
            # Step 2: Process each partition
            stored_partitions = []
            errors = []
            
            for partition_info in partitions:
                try:
                    # Compress data if requested
                    if compress:
                        compressed_data = self._compress_partition(partition_info['data'])
                        partition_info['compressed'] = True
                        partition_info['compression_stats'] = compressed_data['stats']
                        partition_info['data'] = compressed_data['data']
                    
                    # Store in database
                    storage_result = self._store_partition(metric_name, partition_info)
                    
                    # Index the partition
                    index_result = self._index_partition(metric_name, partition_info, storage_result)
                    
                    stored_partitions.append({
                        'partition_id': partition_info['partition_id'],
                        'storage_id': storage_result['id'],
                        'index_id': index_result['id'],
                        'data_points': len(partition_info['original_count'])
                    })
                    
                except Exception as e:
                    error_msg = f"Failed to process partition {partition_info.get('partition_id')}: {str(e)}"
                    self._logger.error(error_msg)
                    errors.append(error_msg)
            
            # Determine overall status
            if errors:
                status = FeatureStatus.PARTIAL_SUCCESS if stored_partitions else FeatureStatus.ERROR
                message = f"Stored {len(stored_partitions)}/{len(partitions)} partitions with errors"
            else:
                status = FeatureStatus.SUCCESS
                message = f"Successfully stored {len(data_points)} data points in {len(partitions)} partitions"
            
            return FeatureResponse(
                status=status,
                message=message,
                data={
                    'metric_name': metric_name,
                    'total_data_points': len(data_points),
                    'partitions_created': len(stored_partitions),
                    'stored_partitions': stored_partitions
                },
                errors=errors if errors else None,
                metadata={
                    'compressed': compress,
                    'compression_type': self.config.compression_type.value if compress else None
                }
            )
            
        except Exception as e:
            error_msg = f"Failed to store time-series data: {str(e)}"
            self._logger.error(error_msg, exc_info=True)
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message=error_msg,
                errors=[str(e)]
            )
            
    def query_time_series_data(
        self,
        metric_name: str,
        start_time: datetime,
        end_time: datetime,
        decompress: bool = True
    ) -> FeatureResponse:
        """
        Query time-series data for a specific time range.
        
        Args:
            metric_name: Name of the metric to query
            start_time: Start of the time range
            end_time: End of the time range
            decompress: Whether to decompress the data if it was compressed
            
        Returns:
            FeatureResponse containing the queried data
        """
        try:
            self._logger.info(f"Querying data for metric: {metric_name} from {start_time} to {end_time}")
            
            # Step 1: Use indexer to find relevant partitions
            index_entries = self._query_index(metric_name, start_time, end_time)
            
            if not index_entries:
                return FeatureResponse(
                    status=FeatureStatus.SUCCESS,
                    message="No data found for the specified time range",
                    data={'metric_name': metric_name, 'data_points': []}
                )
            
            # Step 2: Retrieve data from database
            all_data_points = []
            errors = []
            
            for entry in index_entries:
                try:
                    # Fetch partition data
                    partition_data = self._retrieve_partition(entry)
                    
                    # Decompress if needed and requested
                    if entry.get('compressed') and decompress:
                        partition_data = self._decompress_partition(partition_data)
                    
                    # Filter data points within the time range
                    filtered_points = self._filter_by_time_range(
                        partition_data, start_time, end_time
                    )
                    all_data_points.extend(filtered_points)
                    
                except Exception as e:
                    error_msg = f"Failed to retrieve partition {entry.get('partition_id')}: {str(e)}"
                    self._logger.error(error_msg)
                    errors.append(error_msg)
            
            # Sort data points by timestamp
            all_data_points.sort(key=lambda x: x['timestamp'])
            
            status = FeatureStatus.PARTIAL_SUCCESS if errors else FeatureStatus.SUCCESS
            message = f"Retrieved {len(all_data_points)} data points"
            if errors:
                message += f" with {len(errors)} errors"
            
            return FeatureResponse(
                status=status,
                message=message,
                data={
                    'metric_name': metric_name,
                    'start_time': start_time.isoformat(),
                    'end_time': end_time.isoformat(),
                    'data_points': all_data_points,
                    'partitions_queried': len(index_entries)
                },
                errors=errors if errors else None
            )
            
        except Exception as e:
            error_msg = f"Failed to query time-series data: {str(e)}"
            self._logger.error(error_msg, exc_info=True)
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message=error_msg,
                errors=[str(e)]
            )
            
    def optimize_storage(self, metric_name: Optional[str] = None) -> FeatureResponse:
        """
        Optimize storage by recompressing and reorganizing partitions.
        
        Args:
            metric_name: Optional metric name to optimize. If None, optimizes all metrics.
            
        Returns:
            FeatureResponse containing optimization results
        """
        try:
            self._logger.info(f"Optimizing storage for: {metric_name or 'all metrics'}")
            
            # Get partitions to optimize
            partitions = self._get_partitions_for_optimization(metric_name)
            
            optimized_count = 0
            saved_bytes = 0
            errors = []
            
            for partition in partitions:
                try:
                    # Recompress with optimal settings
                    optimization_result = self._optimize_partition(partition)
                    
                    if optimization_result['saved_bytes'] > 0:
                        optimized_count += 1
                        saved_bytes += optimization_result['saved_bytes']
                        
                        # Update index with new metadata
                        self._update_partition_index(partition['id'], optimization_result)
                        
                except Exception as e:
                    error_msg = f"Failed to optimize partition {partition.get('id')}: {str(e)}"
                    self._logger.error(error_msg)
                    errors.append(error_msg)
            
            status = FeatureStatus.SUCCESS if not errors else FeatureStatus.PARTIAL_SUCCESS
            message = f"Optimized {optimized_count}/{len(partitions)} partitions, saved {saved_bytes} bytes"
            
            return FeatureResponse(
                status=status,
                message=message,
                data={
                    'total_partitions': len(partitions),
                    'optimized_partitions': optimized_count,
                    'saved_bytes': saved_bytes,
                    'saved_mb': round(saved_bytes / (1024 * 1024), 2)
                },
                errors=errors if errors else None
            )
            
        except Exception as e:
            error_msg = f"Failed to optimize storage: {str(e)}"
            self._logger.error(error_msg, exc_info=True)
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message=error_msg,
                errors=[str(e)]
            )
            
    def get_storage_statistics(self, metric_name: Optional[str] = None) -> FeatureResponse:
        """
        Get storage statistics for time-series data.
        
        Args:
            metric_name: Optional metric name to get statistics for. If None, returns overall statistics.
            
        Returns:
            FeatureResponse containing storage statistics
        """
        try:
            self._logger.info(f"Getting storage statistics for: {metric_name or 'all metrics'}")
            
            # Gather statistics from all layers
            db_stats = self._get_database_statistics(metric_name)
            index_stats = self._get_index_statistics(metric_name)
            compression_stats = self._get_compression_statistics(metric_name)
            
            # Combine statistics
            total_size = db_stats.get('total_size_bytes', 0)
            compressed_size = db_stats.get('compressed_size_bytes', 0)
            compression_ratio = (
                1 - (compressed_size / total_size) if total_size > 0 else 0
            )
            
            statistics = {
                'metric_name': metric_name,
                'total_data_points': db_stats.get('total_data_points', 0),
                'total_partitions': db_stats.get('total_partitions', 0),
                'total_size_bytes': total_size,
                'compressed_size_bytes': compressed_size,
                'compression_ratio': round(compression_ratio, 3),
                'average_partition_size_bytes': (
                    total_size // db_stats.get('total_partitions', 1) 
                    if db_stats.get('total_partitions', 0) > 0 else 0
                ),
                'index_entries': index_stats.get('total_entries', 0),
                'index_size_bytes': index_stats.get('index_size_bytes', 0),
                'compression_type': compression_stats.get('primary_type', 'none'),
                'average_compression_time_ms': compression_stats.get('avg_compression_time_ms', 0)
            }
            
            return FeatureResponse(
                status=FeatureStatus.SUCCESS,
                message="Storage statistics retrieved successfully",
                data=statistics,
                metadata={
                    'query_time_ms': db_stats.get('query_time_ms', 0),
                    'cached_results': index_stats.get('cached_results', False)
                }
            )
            
        except Exception as e:
            error_msg = f"Failed to get storage statistics: {str(e)}"
            self._logger.error(error_msg, exc_info=True)
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message=error_msg,
                errors=[str(e)]
            )
            
    def cleanup_old_data(
        self,
        retention_period: timedelta,
        metric_name: Optional[str] = None
    ) -> FeatureResponse:
        """
        Clean up time-series data older than the specified retention period.
        
        Args:
            retention_period: How long to retain data
            metric_name: Optional metric name to clean up. If None, cleans up all metrics.
            
        Returns:
            FeatureResponse containing cleanup results
        """
        try:
            cutoff_date = datetime.utcnow() - retention_period
            self._logger.info(
                f"Cleaning up data older than {cutoff_date} for: {metric_name or 'all metrics'}"
            )
            
            # Find partitions to delete
            old_partitions = self._find_old_partitions(cutoff_date, metric_name)
            
            if not old_partitions:
                return FeatureResponse(
                    status=FeatureStatus.SUCCESS,
                    message="No old data found to clean up",
                    data={'deleted_partitions': 0, 'freed_bytes': 0}
                )
            
            deleted_count = 0
            freed_bytes = 0
            errors = []
            
            for partition in old_partitions:
                try:
                    # Delete from database
                    size = partition.get('size_bytes', 0)
                    self._delete_partition(partition['id'])
                    
                    # Remove from index
                    self._remove_from_index(partition['id'])
                    
                    deleted_count += 1
                    freed_bytes += size
                    
                except Exception as e:
                    error_msg = f"Failed to delete partition {partition.get('id')}: {str(e)}"
                    self._logger.error(error_msg)
                    errors.append(error_msg)
            
            status = FeatureStatus.SUCCESS if not errors else FeatureStatus.PARTIAL_SUCCESS
            message = f"Deleted {deleted_count}/{len(old_partitions)} old partitions, freed {freed_bytes} bytes"
            
            return FeatureResponse(
                status=status,
                message=message,
                data={
                    'retention_period_days': retention_period.days,
                    'cutoff_date': cutoff_date.isoformat(),
                    'total_old_partitions': len(old_partitions),
                    'deleted_partitions': deleted_count,
                    'freed_bytes': freed_bytes,
                    'freed_mb': round(freed_bytes / (1024 * 1024), 2)
                },
                errors=errors if errors else None
            )
            
        except Exception as e:
            error_msg = f"Failed to clean up old data: {str(e)}"
            self._logger.error(error_msg, exc_info=True)
            return FeatureResponse(
                status=FeatureStatus.ERROR,
                message=error_msg,
                errors=[str(e)]
            )
            
    # Helper methods
    
    def _validate_data_points(self, data_points: List[Dict[str, Any]]) -> List[str]:
        """Validate input data points."""
        errors = []
        
        if not data_points:
            errors.append("No data points provided")
            return errors
            
        for i, point in enumerate(data_points):
            if 'timestamp' not in point:
                errors.append(f"Data point {i} missing 'timestamp' field")
            elif not isinstance(point['timestamp'], (datetime, str)):
                errors.append(f"Data point {i} has invalid timestamp type")
                
            if 'value' not in point:
                errors.append(f"Data point {i} missing 'value' field")
                
        return errors
        
    def _partition_data(
        self,
        metric_name: str,
        data_points: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """Partition data points based on configuration."""
        # This is a simplified implementation
        # In reality, the Partitioner layer would handle this logic
        partitions = []
        
        if self.config.partition_by == "time":
            # Group by time intervals
            current_partition = []
            partition_start = None
            
            for point in sorted(data_points, key=lambda x: x['timestamp']):
                timestamp = point['timestamp']
                if isinstance(timestamp, str):
                    timestamp = datetime.fromisoformat(timestamp)
                    
                if partition_start is None:
                    partition_start = timestamp
                    
                if timestamp - partition_start >= self.config.partition_interval:
                    # Create new partition
                    if current_partition:
                        partitions.append({
                            'partition_id': f"{metric_name}_{partition_start.isoformat()}",
                            'start_time': partition_start,
                            'end_time': current_partition[-1]['timestamp'],
                            'data': current_partition,
                            'original_count': len