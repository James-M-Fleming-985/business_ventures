# test_e2e.py
import pytest
import asyncio
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any
import aiohttp
import json
import time
import random
from dataclasses import dataclass
from enum import Enum


class DataType(Enum):
    """Supported time-series data types"""
    TEMPERATURE = "temperature"
    HUMIDITY = "humidity"
    PRESSURE = "pressure"
    FLOW_RATE = "flow_rate"
    ENERGY_CONSUMPTION = "energy_consumption"


@dataclass
class TimeSeriesDataPoint:
    """Represents a single time-series data point"""
    timestamp: datetime
    value: float
    device_id: str
    sensor_id: str
    data_type: DataType
    metadata: Dict[str, Any] = None


class TimeSeriesStorageE2ETest:
    """Base class for time-series storage E2E tests"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.session = None
        
    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self
        
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()
            
    async def write_data(self, data_points: List[TimeSeriesDataPoint]) -> Dict[str, Any]:
        """Write time-series data points"""
        url = f"{self.base_url}/api/v1/timeseries/write"
        
        payload = {
            "data_points": [
                {
                    "timestamp": dp.timestamp.isoformat(),
                    "value": dp.value,
                    "device_id": dp.device_id,
                    "sensor_id": dp.sensor_id,
                    "data_type": dp.data_type.value,
                    "metadata": dp.metadata or {}
                }
                for dp in data_points
            ]
        }
        
        async with self.session.post(url, json=payload) as response:
            return {
                "status": response.status,
                "body": await response.json() if response.status == 200 else await response.text()
            }
            
    async def query_data(self, 
                        device_id: str,
                        start_time: datetime,
                        end_time: datetime,
                        sensor_id: str = None,
                        data_type: DataType = None,
                        aggregation: str = None,
                        interval: str = None) -> Dict[str, Any]:
        """Query time-series data"""
        url = f"{self.base_url}/api/v1/timeseries/query"
        
        params = {
            "device_id": device_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
        if sensor_id:
            params["sensor_id"] = sensor_id
        if data_type:
            params["data_type"] = data_type.value
        if aggregation:
            params["aggregation"] = aggregation
        if interval:
            params["interval"] = interval
            
        async with self.session.get(url, params=params) as response:
            return {
                "status": response.status,
                "body": await response.json() if response.status == 200 else await response.text()
            }
            
    async def get_data_statistics(self, 
                                 device_id: str,
                                 start_time: datetime,
                                 end_time: datetime) -> Dict[str, Any]:
        """Get statistics for stored data"""
        url = f"{self.base_url}/api/v1/timeseries/statistics"
        
        params = {
            "device_id": device_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
        async with self.session.get(url, params=params) as response:
            return {
                "status": response.status,
                "body": await response.json() if response.status == 200 else await response.text()
            }
            
    async def delete_data(self, 
                         device_id: str,
                         start_time: datetime,
                         end_time: datetime) -> Dict[str, Any]:
        """Delete time-series data"""
        url = f"{self.base_url}/api/v1/timeseries/delete"
        
        payload = {
            "device_id": device_id,
            "start_time": start_time.isoformat(),
            "end_time": end_time.isoformat()
        }
        
        async with self.session.delete(url, json=payload) as response:
            return {
                "status": response.status,
                "body": await response.json() if response.status == 200 else await response.text()
            }


def generate_realistic_sensor_data(device_id: str, 
                                 sensor_id: str,
                                 data_type: DataType,
                                 start_time: datetime,
                                 duration_minutes: int,
                                 interval_seconds: int = 60) -> List[TimeSeriesDataPoint]:
    """Generate realistic sensor data for testing"""
    data_points = []
    current_time = start_time
    end_time = start_time + timedelta(minutes=duration_minutes)
    
    # Base values and variations for different data types
    base_values = {
        DataType.TEMPERATURE: (20.0, 2.0),  # base, variation
        DataType.HUMIDITY: (50.0, 10.0),
        DataType.PRESSURE: (101.325, 2.0),
        DataType.FLOW_RATE: (100.0, 20.0),
        DataType.ENERGY_CONSUMPTION: (1000.0, 200.0)
    }
    
    base_value, variation = base_values.get(data_type, (50.0, 10.0))
    current_value = base_value
    
    while current_time < end_time:
        # Add some realistic variation
        change = random.uniform(-variation, variation)
        current_value += change * 0.1  # Dampen the change
        current_value = max(0, current_value)  # Ensure non-negative
        
        # Add occasional anomalies (5% chance)
        if random.random() < 0.05:
            current_value += random.uniform(-variation * 2, variation * 2)
            
        data_points.append(TimeSeriesDataPoint(
            timestamp=current_time,
            value=round(current_value, 2),
            device_id=device_id,
            sensor_id=sensor_id,
            data_type=data_type,
            metadata={
                "unit": get_unit_for_data_type(data_type),
                "quality": "good" if random.random() > 0.1 else "degraded"
            }
        ))
        
        current_time += timedelta(seconds=interval_seconds)
        
    return data_points


def get_unit_for_data_type(data_type: DataType) -> str:
    """Get measurement unit for data type"""
    units = {
        DataType.TEMPERATURE: "°C",
        DataType.HUMIDITY: "%",
        DataType.PRESSURE: "kPa",
        DataType.FLOW_RATE: "L/min",
        DataType.ENERGY_CONSUMPTION: "kWh"
    }
    return units.get(data_type, "")


@pytest.fixture
def base_url():
    """Base URL for the time-series storage service"""
    return "http://localhost:8080"


@pytest.fixture
def test_devices():
    """Test device configurations"""
    return [
        {
            "device_id": "factory-floor-01",
            "sensors": [
                {"id": "temp-sensor-01", "type": DataType.TEMPERATURE},
                {"id": "humidity-sensor-01", "type": DataType.HUMIDITY},
                {"id": "pressure-sensor-01", "type": DataType.PRESSURE}
            ]
        },
        {
            "device_id": "production-line-02",
            "sensors": [
                {"id": "flow-sensor-01", "type": DataType.FLOW_RATE},
                {"id": "energy-meter-01", "type": DataType.ENERGY_CONSUMPTION}
            ]
        }
    ]


@pytest.mark.asyncio
class TestTimeSeriesStorageE2E:
    """End-to-end tests for time-series data storage feature"""
    
    async def test_complete_data_lifecycle_with_multiple_devices(self, base_url, test_devices):
        """
        Test complete lifecycle: write, query, aggregate, and delete data from multiple devices
        
        This test verifies:
        1. Writing large volumes of time-series data from multiple devices
        2. Querying data with various filters
        3. Performing aggregations on stored data
        4. Retrieving statistics
        5. Deleting old data
        """
        async with TimeSeriesStorageE2ETest(base_url) as client:
            start_time = datetime.now(timezone.utc) - timedelta(hours=24)
            
            # Step 1: Generate and write data for all devices
            all_data_points = []
            for device in test_devices:
                device_id = device["device_id"]
                for sensor in device["sensors"]:
                    # Generate 24 hours of data at 1-minute intervals
                    data_points = generate_realistic_sensor_data(
                        device_id=device_id,
                        sensor_id=sensor["id"],
                        data_type=sensor["type"],
                        start_time=start_time,
                        duration_minutes=1440,  # 24 hours
                        interval_seconds=60
                    )
                    all_data_points.extend(data_points)
            
            # Write data in batches to simulate realistic load
            batch_size = 1000
            write_results = []
            for i in range(0, len(all_data_points), batch_size):
                batch = all_data_points[i:i + batch_size]
                result = await client.write_data(batch)
                write_results.append(result)
                
                # Verify successful write
                assert result["status"] == 200, f"Failed to write batch {i//batch_size}: {result['body']}"
                assert result["body"]["points_written"] == len(batch)
                
            # Allow time for data to be indexed
            await asyncio.sleep(2)
            
            # Step 2: Query raw data for specific device and time range
            query_start = start_time + timedelta(hours=12)
            query_end = start_time + timedelta(hours=13)
            
            raw_data_result = await client.query_data(
                device_id="factory-floor-01",
                start_time=query_start,
                end_time=query_end
            )
            
            assert raw_data_result["status"] == 200
            raw_data = raw_data_result["body"]["data"]
            assert len(raw_data) > 0
            
            # Verify data integrity
            for point in raw_data:
                timestamp = datetime.fromisoformat(point["timestamp"])
                assert query_start <= timestamp <= query_end
                assert point["device_id"] == "factory-floor-01"
                assert "value" in point
                assert "sensor_id" in point
                
            # Step 3: Query with aggregation
            hourly_avg_result = await client.query_data(
                device_id="factory-floor-01",
                start_time=start_time,
                end_time=start_time + timedelta(hours=6),
                data_type=DataType.TEMPERATURE,
                aggregation="avg",
                interval="1h"
            )
            
            assert hourly_avg_result["status"] == 200
            hourly_data = hourly_avg_result["body"]["data"]
            assert len(hourly_data) == 6  # 6 hourly averages
            
            # Verify aggregated data structure
            for hour_data in hourly_data:
                assert "timestamp" in hour_data
                assert "avg_value" in hour_data
                assert "count" in hour_data
                assert hour_data["count"] > 0
                
            # Step 4: Get statistics for the entire period
            stats_result = await client.get_data_statistics(
                device_id="production-line-02",
                start_time=start_time,
                end_time=start_time + timedelta(hours=24)
            )
            
            assert stats_result["status"] == 200
            stats = stats_result["body"]["statistics"]
            
            # Verify statistics contain expected metrics
            assert "total_points" in stats
            assert "sensors" in stats
            assert stats["total_points"] > 0
            
            for sensor_stats in stats["sensors"]:
                assert "sensor_id" in sensor_stats
                assert "data_type" in sensor_stats
                assert "min_value" in sensor_stats
                assert "max_value" in sensor_stats
                assert "avg_value" in sensor_stats
                assert "std_dev" in sensor_stats
                
            # Step 5: Delete old data (first 6 hours)
            delete_end = start_time + timedelta(hours=6)
            delete_result = await client.delete_data(
                device_id="factory-floor-01",
                start_time=start_time,
                end_time=delete_end
            )
            
            assert delete_result["status"] == 200
            assert delete_result["body"]["points_deleted"] > 0
            
            # Verify data was deleted
            deleted_range_result = await client.query_data(
                device_id="factory-floor-01",
                start_time=start_time,
                end_time=delete_end
            )
            
            assert deleted_range_result["status"] == 200
            assert len(deleted_range_result["body"]["data"]) == 0
            
            # Verify remaining data is intact
            remaining_data_result = await client.query_data(
                device_id="factory-floor-01",
                start_time=delete_end,
                end_time=start_time + timedelta(hours=24)
            )
            
            assert remaining_data_result["status"] == 200
            assert len(remaining_data_result["body"]["data"]) > 0
    
    async def test_high_frequency_data_ingestion_and_real_time_query(self, base_url):
        """
        Test high-frequency data ingestion with concurrent real-time queries
        
        This test verifies:
        1. System can handle high-frequency data ingestion (every second)
        2. Real-time queries work correctly during active ingestion
        3. Data consistency under concurrent operations
        4. Performance metrics meet requirements
        """
        async with TimeSeriesStorageE2ETest(base_url) as client:
            device_id = "high-freq-device-01"
            sensor_id = "vibration-sensor-01"
            
            # Start time for the test
            test_start = datetime.now(timezone.utc)
            
            # Metrics collection
            write_latencies = []
            query_latencies = []
            data_consistency_checks = []
            
            async def continuous_writer():
                """Continuously write high-frequency data"""
                nonlocal write_latencies
                
                for i in range(6