"""
Integration tests for Time-Series Data Storage Feature
Feature ID: FEATURE-CA-001-03
Tests integration between DB_Connection, Partitioner, Indexer, and Compressor layers
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock
import pandas as pd
import numpy as np
from typing import Dict, List, Any

# Import feature components (assuming these exist)
from feature_integration import (
    TimeSeriesStorageFeature,
    DBConnection,
    Partitioner,
    Indexer,
    Compressor,
    PartitionStrategy,
    CompressionType,
    IndexType
)


class TestTimeSeriesStorageIntegration:
    """Integration tests for Time-Series Data Storage feature"""

    @pytest.fixture
    def mock_db_connection(self):
        """Create a mock database connection"""
        mock_conn = Mock(spec=DBConnection)
        mock_conn.is_connected = True
        mock_conn.execute_query = Mock(return_value=True)
        mock_conn.bulk_insert = Mock(return_value=True)
        mock_conn.create_table = Mock(return_value=True)
        return mock_conn

    @pytest.fixture
    def sample_time_series_data(self):
        """Generate sample time-series data for testing"""
        start_date = datetime.now() - timedelta(days=30)
        dates = pd.date_range(start=start_date, periods=1000, freq='H')
        
        data = pd.DataFrame({
            'timestamp': dates,
            'sensor_id': np.random.choice(['sensor_1', 'sensor_2', 'sensor_3'], 1000),
            'temperature': np.random.normal(25, 5, 1000),
            'humidity': np.random.normal(60, 10, 1000),
            'pressure': np.random.normal(1013, 20, 1000)
        })
        return data

    @pytest.fixture
    def time_series_feature(self, mock_db_connection):
        """Create TimeSeriesStorageFeature instance with mocked components"""
        feature = TimeSeriesStorageFeature(
            db_connection=mock_db_connection,
            partition_strategy=PartitionStrategy.MONTHLY,
            compression_type=CompressionType.ZLIB,
            index_columns=['timestamp', 'sensor_id']
        )
        return feature

    def test_end_to_end_data_ingestion_and_retrieval(self, time_series_feature, sample_time_series_data):
        """Test complete data flow from ingestion through all layers to retrieval"""
        # Arrange
        expected_partitions = {
            '2024_01': sample_time_series_data[sample_time_series_data['timestamp'].dt.month == 1],
            '2024_02': sample_time_series_data[sample_time_series_data['timestamp'].dt.month == 2]
        }
        
        # Mock partitioner behavior
        time_series_feature.partitioner.partition_data = Mock(
            return_value=expected_partitions
        )
        
        # Mock compressor behavior
        compressed_data = b'compressed_binary_data'
        time_series_feature.compressor.compress = Mock(return_value=compressed_data)
        time_series_feature.compressor.decompress = Mock(
            return_value=sample_time_series_data.to_dict()
        )
        
        # Mock indexer behavior
        index_metadata = {
            'timestamp_index': {'type': 'btree', 'columns': ['timestamp']},
            'sensor_index': {'type': 'hash', 'columns': ['sensor_id']}
        }
        time_series_feature.indexer.create_indexes = Mock(return_value=index_metadata)
        
        # Act
        result = time_series_feature.store_time_series_data(sample_time_series_data)
        
        # Assert
        assert result['success'] is True
        assert result['partitions_created'] == 2
        assert result['compression_ratio'] > 0
        assert 'indexes' in result
        
        # Verify layer interactions
        time_series_feature.partitioner.partition_data.assert_called_once()
        assert time_series_feature.compressor.compress.call_count == len(expected_partitions)
        time_series_feature.indexer.create_indexes.assert_called()
        assert time_series_feature.db_connection.bulk_insert.call_count == len(expected_partitions)

    def test_query_optimization_across_layers(self, time_series_feature):
        """Test query optimization using indexer and partitioner for efficient data retrieval"""
        # Arrange
        query_params = {
            'start_date': datetime(2024, 1, 1),
            'end_date': datetime(2024, 1, 31),
            'sensor_id': 'sensor_1',
            'metrics': ['temperature', 'humidity']
        }
        
        # Mock partitioner to identify relevant partitions
        relevant_partitions = ['2024_01']
        time_series_feature.partitioner.get_relevant_partitions = Mock(
            return_value=relevant_partitions
        )
        
        # Mock indexer to provide query hints
        query_hints = {
            'use_index': 'timestamp_sensor_composite',
            'estimated_rows': 500,
            'index_type': IndexType.COMPOSITE
        }
        time_series_feature.indexer.get_query_hints = Mock(return_value=query_hints)
        
        # Mock compressed data retrieval
        compressed_data = b'compressed_partition_data'
        time_series_feature.db_connection.execute_query = Mock(
            return_value=[{'partition': '2024_01', 'data': compressed_data}]
        )
        
        # Mock decompression
        decompressed_data = pd.DataFrame({
            'timestamp': pd.date_range(start='2024-01-01', periods=100, freq='H'),
            'sensor_id': 'sensor_1',
            'temperature': np.random.normal(25, 5, 100),
            'humidity': np.random.normal(60, 10, 100)
        })
        time_series_feature.compressor.decompress = Mock(return_value=decompressed_data)
        
        # Act
        result = time_series_feature.query_time_series_data(query_params)
        
        # Assert
        assert result is not None
        assert len(result) == 100
        assert all(col in result.columns for col in ['timestamp', 'sensor_id', 'temperature', 'humidity'])
        
        # Verify optimization flow
        time_series_feature.partitioner.get_relevant_partitions.assert_called_once_with(
            query_params['start_date'], query_params['end_date']
        )
        time_series_feature.indexer.get_query_hints.assert_called_once()
        time_series_feature.db_connection.execute_query.assert_called_once()
        time_series_feature.compressor.decompress.assert_called_once()

    def test_error_handling_cascade_across_layers(self, time_series_feature, sample_time_series_data):
        """Test error handling when failures occur in different layers"""
        # Test 1: Database connection failure
        time_series_feature.db_connection.is_connected = False
        time_series_feature.db_connection.bulk_insert.side_effect = Exception(
            "Database connection lost"
        )
        
        with pytest.raises(Exception) as exc_info:
            time_series_feature.store_time_series_data(sample_time_series_data)
        assert "Database connection lost" in str(exc_info.value)
        
        # Test 2: Partitioner failure
        time_series_feature.db_connection.is_connected = True
        time_series_feature.partitioner.partition_data.side_effect = ValueError(
            "Invalid partition strategy"
        )
        
        with pytest.raises(ValueError) as exc_info:
            time_series_feature.store_time_series_data(sample_time_series_data)
        assert "Invalid partition strategy" in str(exc_info.value)
        
        # Test 3: Compression failure
        time_series_feature.partitioner.partition_data.side_effect = None
        time_series_feature.partitioner.partition_data.return_value = {'2024_01': sample_time_series_data}
        time_series_feature.compressor.compress.side_effect = MemoryError(
            "Insufficient memory for compression"
        )
        
        with pytest.raises(MemoryError) as exc_info:
            time_series_feature.store_time_series_data(sample_time_series_data)
        assert "Insufficient memory for compression" in str(exc_info.value)
        
        # Test 4: Index creation failure
        time_series_feature.compressor.compress.side_effect = None
        time_series_feature.compressor.compress.return_value = b'compressed_data'
        time_series_feature.indexer.create_indexes.side_effect = RuntimeError(
            "Index creation failed"
        )
        
        # Should complete but log index creation failure
        result = time_series_feature.store_time_series_data(sample_time_series_data)
        assert result['success'] is True
        assert result.get('index_warnings') is not None

    def test_performance_optimization_integration(self, time_series_feature):
        """Test performance optimizations across layers for large datasets"""
        # Arrange - Large dataset
        large_dataset = pd.DataFrame({
            'timestamp': pd.date_range(start='2024-01-01', periods=100000, freq='min'),
            'sensor_id': np.random.choice(['sensor_' + str(i) for i in range(100)], 100000),
            'value': np.random.random(100000) * 100
        })
        
        # Mock batch processing in partitioner
        batch_partitions = {}
        for month in range(1, 4):
            month_data = large_dataset[large_dataset['timestamp'].dt.month == month]
            if not month_data.empty:
                batch_partitions[f'2024_{month:02d}'] = month_data
        
        time_series_feature.partitioner.partition_data = Mock(return_value=batch_partitions)
        
        # Mock parallel compression
        compression_results = []
        def mock_compress(data):
            # Simulate compression with metrics
            original_size = data.memory_usage(deep=True).sum()
            compressed_size = original_size * 0.3  # 70% compression
            compression_results.append({
                'original_size': original_size,
                'compressed_size': compressed_size
            })
            return b'compressed_' + str(len(compression_results)).encode()
        
        time_series_feature.compressor.compress = Mock(side_effect=mock_compress)
        
        # Mock bulk index creation
        time_series_feature.indexer.create_bulk_indexes = Mock(
            return_value={'indexes_created': 6, 'time_elapsed': 2.5}
        )
        
        # Act
        result = time_series_feature.store_time_series_data(
            large_dataset, 
            use_bulk_optimization=True
        )
        
        # Assert
        assert result['success'] is True
        assert result['total_records'] == 100000
        assert result['partitions_created'] >= 1
        assert result['compression_ratio'] > 2.0  # Expect good compression
        assert result.get('bulk_optimization_used') is True
        
        # Verify optimized operations
        time_series_feature.partitioner.partition_data.assert_called_once()
        assert time_series_feature.compressor.compress.call_count == len(batch_partitions)
        time_series_feature.indexer.create_bulk_indexes.assert_called_once()

    def test_data_consistency_across_layers(self, time_series_feature, sample_time_series_data):
        """Test data consistency and integrity through all transformation layers"""
        # Arrange
        original_data = sample_time_series_data.copy()
        original_checksum = hash(original_data.to_string())
        
        # Mock layer operations with data tracking
        partition_checksums = {}
        def mock_partition(data):
            partitions = {}
            for month in data['timestamp'].dt.month.unique():
                month_data = data[data['timestamp'].dt.month == month]
                partition_name = f'2024_{month:02d}'
                partitions[partition_name] = month_data
                partition_checksums[partition_name] = hash(month_data.to_string())
            return partitions
        
        time_series_feature.partitioner.partition_data = Mock(side_effect=mock_partition)
        
        # Mock compression with integrity check
        compression_map = {}
        def mock_compress_with_integrity(data):
            checksum = hash(data.to_string())
            compressed = b'compressed_' + str(checksum).encode()
            compression_map[compressed] = data
            return compressed
        
        def mock_decompress_with_integrity(compressed_data):
            return compression_map.get(compressed_data, pd.DataFrame())
        
        time_series_feature.compressor.compress = Mock(side_effect=mock_compress_with_integrity)
        time_series_feature.compressor.decompress = Mock(side_effect=mock_decompress_with_integrity)
        
        # Mock indexer with metadata tracking
        index_metadata = {
            'created_indexes': [],
            'index_statistics': {}
        }
        def mock_create_indexes(partition_name, data):
            indexes = {
                'primary': {'columns': ['timestamp'], 'unique_values': len(data['timestamp'].unique())},
                'secondary': {'columns': ['sensor_id'], 'unique_values': len(data['sensor_id'].unique())}
            }
            index_metadata['created_indexes'].append(partition_name)
            index_metadata['index_statistics'][partition_name] = indexes
            return indexes
        
        time_series_feature.indexer.create_indexes = Mock(side_effect=mock_create_indexes)
        
        # Act - Store data
        store_result = time_series_feature.store_time_series_data(original_data)
        
        # Act - Retrieve data
        time_series_feature.db_connection.execute_query = Mock(
            return_value=[
                {'partition': name, 'data': compressed}
                for name, compressed in compression_map.items()
            ]
        )
        
        retrieved_data = time_series_feature.query_time_series_data({
            'start_date': original_data['timestamp'].min(),
            'end_date': original_data['timestamp'].max()
        })
        
        # Assert - Data integrity
        assert store_result['success'] is True
        assert len(retrieved_data) == len(original_data)
        
        # Verify data consistency after round trip
        retrieved_sorted = retrieved_data.sort_values(['timestamp', 'sensor_id']).reset_index(drop=True)
        original_sorted = original_data.sort_values(['timestamp', 'sensor_id']).reset_index(drop=True)
        
        # Check critical columns maintained integrity
        pd.testing.assert_series_equal(
            retrieved_sorted['timestamp'], 
            original_sorted['timestamp'],
            check_names=False
        )
        pd.testing.assert_series_equal(
            retrieved_sorted['sensor_id'], 
            original_sorted['sensor_id'],
            check_names=False
        )
        
        # Verify index metadata consistency
        assert len(index_metadata['created_indexes']) == len(partition_checksums)
        for partition in index_metadata[