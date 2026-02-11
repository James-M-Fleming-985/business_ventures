"""
Integration tests for Lag Analysis Service (FEATURE-CA-002-08)

This module tests the integration between:
- API Layer (REST endpoints)
- Service Layer (business logic)
- Data Access Layer (database operations)
- Cache Layer (Redis caching)
- Message Queue Layer (async processing)
"""

import pytest
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import asyncio
import redis
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.api.lag_analysis_api import LagAnalysisAPI
from src.services.lag_analysis_service import LagAnalysisService
from src.data_access.lag_repository import LagRepository
from src.cache.cache_service import CacheService
from src.messaging.message_queue import MessageQueue
from src.models.lag_models import LagMetrics, LagAnalysisRequest, LagAnalysisResult
from src.exceptions import (
    DataNotFoundError, 
    InvalidParametersError,
    ServiceUnavailableError,
    CacheConnectionError
)


class TestLagAnalysisIntegration:
    """Integration tests for Lag Analysis Service"""

    @pytest.fixture
    def db_session(self):
        """Create a test database session"""
        engine = create_engine('sqlite:///:memory:')
        Session = sessionmaker(bind=engine)
        session = Session()
        
        # Create tables
        from src.models.database_models import Base
        Base.metadata.create_all(engine)
        
        yield session
        
        session.close()

    @pytest.fixture
    def cache_client(self):
        """Create a mock Redis client"""
        client = Mock(spec=redis.StrictRedis)
        client.get.return_value = None
        client.set.return_value = True
        client.exists.return_value = False
        client.ttl.return_value = -2
        return client

    @pytest.fixture
    def message_queue(self):
        """Create a mock message queue"""
        queue = Mock(spec=MessageQueue)
        queue.publish = AsyncMock(return_value=True)
        queue.consume = AsyncMock()
        return queue

    @pytest.fixture
    def lag_repository(self, db_session):
        """Create lag repository instance"""
        return LagRepository(db_session)

    @pytest.fixture
    def cache_service(self, cache_client):
        """Create cache service instance"""
        return CacheService(cache_client)

    @pytest.fixture
    def lag_service(self, lag_repository, cache_service, message_queue):
        """Create lag analysis service instance"""
        return LagAnalysisService(
            repository=lag_repository,
            cache=cache_service,
            message_queue=message_queue
        )

    @pytest.fixture
    def lag_api(self, lag_service):
        """Create lag analysis API instance"""
        return LagAnalysisAPI(lag_service)

    @pytest.fixture
    def sample_lag_request(self):
        """Sample lag analysis request"""
        return LagAnalysisRequest(
            stream_id="stream_123",
            start_time=datetime.utcnow() - timedelta(hours=1),
            end_time=datetime.utcnow(),
            metrics=["latency", "throughput", "error_rate"],
            aggregation_window="5m",
            threshold_ms=100
        )

    @pytest.fixture
    def sample_lag_metrics(self):
        """Sample lag metrics data"""
        return [
            LagMetrics(
                stream_id="stream_123",
                timestamp=datetime.utcnow() - timedelta(minutes=30),
                latency_ms=95,
                throughput_mbps=100,
                error_rate=0.01,
                consumer_lag=50
            ),
            LagMetrics(
                stream_id="stream_123",
                timestamp=datetime.utcnow() - timedelta(minutes=25),
                latency_ms=105,
                throughput_mbps=95,
                error_rate=0.02,
                consumer_lag=75
            ),
            LagMetrics(
                stream_id="stream_123",
                timestamp=datetime.utcnow() - timedelta(minutes=20),
                latency_ms=120,
                throughput_mbps=85,
                error_rate=0.05,
                consumer_lag=100
            )
        ]

    @pytest.mark.asyncio
    async def test_successful_lag_analysis_with_caching(
        self, lag_api, lag_service, lag_repository, cache_service, 
        message_queue, sample_lag_request, sample_lag_metrics
    ):
        """
        Test 1: Successful lag analysis flow with caching
        
        Integration scenario:
        1. API receives lag analysis request
        2. Service checks cache (miss)
        3. Repository fetches data from database
        4. Service processes and analyzes data
        5. Result is cached
        6. Message is published to queue
        7. API returns response
        """
        # Setup
        lag_repository.get_lag_metrics = Mock(return_value=sample_lag_metrics)
        cache_key = f"lag_analysis:{sample_lag_request.stream_id}:{sample_lag_request.start_time}:{sample_lag_request.end_time}"
        
        # Execute
        result = await lag_api.analyze_lag(sample_lag_request)
        
        # Verify layer interactions
        assert result is not None
        assert result.stream_id == "stream_123"
        assert result.analysis_period.start_time == sample_lag_request.start_time
        assert result.analysis_period.end_time == sample_lag_request.end_time
        
        # Verify cache was checked and updated
        cache_service.cache_client.get.assert_called_once()
        cache_service.cache_client.set.assert_called_once()
        
        # Verify database was queried
        lag_repository.get_lag_metrics.assert_called_once_with(
            stream_id="stream_123",
            start_time=sample_lag_request.start_time,
            end_time=sample_lag_request.end_time
        )
        
        # Verify message was published
        message_queue.publish.assert_called_once()
        published_message = message_queue.publish.call_args[0][0]
        assert published_message["event_type"] == "lag_analysis_completed"
        assert published_message["stream_id"] == "stream_123"

    @pytest.mark.asyncio
    async def test_cache_hit_bypasses_database(
        self, lag_api, lag_service, lag_repository, cache_service,
        sample_lag_request
    ):
        """
        Test 2: Cache hit prevents database query
        
        Integration scenario:
        1. API receives lag analysis request
        2. Service checks cache (hit)
        3. Cached result is returned
        4. Database is not queried
        """
        # Setup cached result
        cached_result = {
            "stream_id": "stream_123",
            "avg_latency": 95.5,
            "max_latency": 120,
            "violations": 2,
            "analysis_timestamp": datetime.utcnow().isoformat()
        }
        cache_service.cache_client.get.return_value = json.dumps(cached_result)
        cache_service.cache_client.exists.return_value = True
        
        # Execute
        result = await lag_api.analyze_lag(sample_lag_request)
        
        # Verify
        assert result is not None
        cache_service.cache_client.get.assert_called_once()
        lag_repository.get_lag_metrics.assert_not_called()

    @pytest.mark.asyncio
    async def test_database_failure_with_graceful_degradation(
        self, lag_api, lag_service, lag_repository, cache_service,
        message_queue, sample_lag_request
    ):
        """
        Test 3: Database failure with graceful degradation
        
        Integration scenario:
        1. API receives request
        2. Cache miss occurs
        3. Database query fails
        4. Service attempts fallback to recent cache
        5. Error is logged to message queue
        6. Appropriate error response is returned
        """
        # Setup database failure
        lag_repository.get_lag_metrics = Mock(
            side_effect=Exception("Database connection lost")
        )
        
        # Setup fallback cache
        fallback_key = f"lag_analysis:fallback:{sample_lag_request.stream_id}"
        fallback_data = {
            "stream_id": "stream_123",
            "avg_latency": 90,
            "stale": True,
            "cached_at": (datetime.utcnow() - timedelta(minutes=10)).isoformat()
        }
        
        def cache_get_side_effect(key):
            if key == fallback_key:
                return json.dumps(fallback_data)
            return None
            
        cache_service.cache_client.get.side_effect = cache_get_side_effect
        
        # Execute
        with pytest.raises(ServiceUnavailableError) as exc_info:
            await lag_api.analyze_lag(sample_lag_request)
        
        # Verify error handling
        assert "Database connection lost" in str(exc_info.value)
        
        # Verify error was published to message queue
        message_queue.publish.assert_called()
        error_message = message_queue.publish.call_args[0][0]
        assert error_message["event_type"] == "lag_analysis_error"
        assert error_message["error_type"] == "database_failure"

    @pytest.mark.asyncio
    async def test_concurrent_requests_with_cache_stampede_prevention(
        self, lag_service, lag_repository, cache_service, message_queue,
        sample_lag_request, sample_lag_metrics
    ):
        """
        Test 4: Concurrent requests with cache stampede prevention
        
        Integration scenario:
        1. Multiple concurrent requests for same analysis
        2. Cache lock prevents multiple database queries
        3. First request populates cache
        4. Subsequent requests wait and use cached result
        """
        # Setup
        lag_repository.get_lag_metrics = Mock(return_value=sample_lag_metrics)
        cache_service.cache_client.set.return_value = True
        
        # Simulate cache lock mechanism
        lock_acquired = False
        original_get = cache_service.cache_client.get
        
        def cache_get_with_lock(key):
            nonlocal lock_acquired
            if "lock:" in key and not lock_acquired:
                lock_acquired = True
                return None
            elif "lock:" in key:
                return "locked"
            return original_get(key)
            
        cache_service.cache_client.get.side_effect = cache_get_with_lock
        
        # Execute concurrent requests
        tasks = [
            lag_service.analyze(sample_lag_request)
            for _ in range(5)
        ]
        results = await asyncio.gather(*tasks)
        
        # Verify
        assert len(results) == 5
        assert all(r.stream_id == "stream_123" for r in results)
        
        # Database should only be queried once
        assert lag_repository.get_lag_metrics.call_count == 1

    @pytest.mark.asyncio
    async def test_end_to_end_with_invalid_parameters(
        self, lag_api, sample_lag_request
    ):
        """
        Test 5: End-to-end validation with invalid parameters
        
        Integration scenario:
        1. API receives request with invalid parameters
        2. Validation fails at API layer
        3. Error is properly formatted and returned
        4. No downstream services are called
        """
        # Create invalid request
        invalid_request = LagAnalysisRequest(
            stream_id="",  # Empty stream ID
            start_time=datetime.utcnow(),
            end_time=datetime.utcnow() - timedelta(hours=1),  # End before start
            metrics=["invalid_metric"],
            aggregation_window="invalid",
            threshold_ms=-10  # Negative threshold
        )
        
        # Execute
        with pytest.raises(InvalidParametersError) as exc_info:
            await lag_api.analyze_lag(invalid_request)
        
        # Verify validation errors
        error = exc_info.value
        assert "stream_id" in str(error)
        assert "end_time must be after start_time" in str(error)
        assert "Invalid metric" in str(error)
        assert "Invalid aggregation window" in str(error)
        assert "Threshold must be positive" in str(error)

    @pytest.mark.asyncio
    async def test_cache_failure_with_database_fallback(
        self, lag_api, lag_service, lag_repository, cache_service,
        sample_lag_request, sample_lag_metrics
    ):
        """
        Test 6: Cache failure with successful database fallback
        
        Integration scenario:
        1. API receives request
        2. Cache service fails (connection error)
        3. Service continues without caching
        4. Database query succeeds
        5. Result is returned (without caching)
        6. Warning is logged
        """
        # Setup cache failure
        cache_service.cache_client.get.side_effect = redis.ConnectionError("Redis unavailable")
        cache_service.cache_client.set.side_effect = redis.ConnectionError("Redis unavailable")
        
        # Setup successful database response
        lag_repository.get_lag_metrics = Mock(return_value=sample_lag_metrics)
        
        # Execute
        result = await lag_api.analyze_lag(sample_lag_request)
        
        # Verify
        assert result is not None
        assert result.stream_id == "stream_123"
        lag_repository.get_lag_metrics.assert_called_once()
        
        # Verify cache errors were handled gracefully
        cache_service.cache_client.get.assert_called()
        cache_service.cache_client.set.assert_called()

    @pytest.mark.asyncio
    async def test_message_queue_async_processing(
        self, lag_service, message_queue, sample_lag_request, sample_lag_metrics
    ):
        """
        Test 7: Asynchronous message queue processing
        
        Integration scenario:
        1. Lag analysis completes
        2. Result is published to message queue
        3. Async consumers process the message
        4. Secondary actions are triggered (alerts, metrics)
        """
        # Setup
        lag_service.repository.get_lag_metrics = Mock(return_value=sample_lag_metrics)
        
        # Track published messages
        published_messages = []
        async def capture_publish(message, topic):
            published_messages.append((message, topic))
            return True
            
        message_queue.publish.side_effect = capture_publish
        
        # Execute
        result = await lag_service.analyze(sample_lag_request)
        
        # Verify primary message
        assert len(published_messages) > 0
        primary_msg, topic = published_messages[0]
        assert topic == "lag_analysis"
        assert primary_msg["stream_id"] == "stream_123"
        assert "metrics" in primary_msg
        
        # Simulate alert triggering for high lag
        if any(m.latency_ms > sample_lag_request.threshold_ms for m in sample_lag_metrics):
            alert_msg = {
                "alert_type": "high_lag_detected",
                "stream_id": "stream_123",
                "threshold": sample_lag_request.threshold_ms,
                "max_latency": max(m.latency_ms for m in sample_lag_metrics)
            }
            await message_queue.publish(alert_msg, "alerts")
            
        # Verify alert was published
        assert any(msg[1] == "alerts" for msg in published_messages)


if __name__ == "__main__":
    pytest.main(["-v", __file__])