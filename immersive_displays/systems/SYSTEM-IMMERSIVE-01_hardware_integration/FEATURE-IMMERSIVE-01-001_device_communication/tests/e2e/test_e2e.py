"""
End-to-end tests for Device Communication Management Feature
Feature ID: FEATURE-IMMERSIVE-01-001
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock
import websockets
import aiohttp

# Test fixtures and utilities
@pytest.fixture
def device_config():
    """Fixture for device configuration"""
    return {
        "device_id": "DEV-001-IMMERSIVE",
        "device_type": "immersive_controller",
        "firmware_version": "2.1.0",
        "capabilities": ["haptic_feedback", "motion_tracking", "biometric_sensing"],
        "connection_params": {
            "protocol": "websocket",
            "host": "localhost",
            "port": 8765,
            "timeout": 30,
            "retry_attempts": 3
        }
    }

@pytest.fixture
def test_messages():
    """Fixture for test messages"""
    return {
        "handshake": {
            "type": "handshake",
            "device_id": "DEV-001-IMMERSIVE",
            "timestamp": datetime.utcnow().isoformat()
        },
        "telemetry": {
            "type": "telemetry",
            "data": {
                "temperature": 37.2,
                "battery_level": 85,
                "signal_strength": -45,
                "active_sensors": ["accelerometer", "gyroscope", "heart_rate"]
            },
            "timestamp": datetime.utcnow().isoformat()
        },
        "command": {
            "type": "command",
            "action": "enable_haptic_feedback",
            "parameters": {
                "intensity": 0.7,
                "pattern": "pulse",
                "duration_ms": 500
            }
        }
    }

@pytest.fixture
async def mock_device_server():
    """Mock WebSocket server for device simulation"""
    class DeviceServer:
        def __init__(self):
            self.connected = False
            self.received_messages = []
            self.server = None
            
        async def handler(self, websocket, path):
            self.connected = True
            try:
                async for message in websocket:
                    data = json.loads(message)
                    self.received_messages.append(data)
                    
                    # Simulate device responses
                    if data.get("type") == "handshake":
                        response = {
                            "type": "handshake_ack",
                            "status": "connected",
                            "device_info": {
                                "id": "DEV-001-IMMERSIVE",
                                "firmware": "2.1.0"
                            }
                        }
                        await websocket.send(json.dumps(response))
                    
                    elif data.get("type") == "command":
                        response = {
                            "type": "command_ack",
                            "command_id": data.get("id"),
                            "status": "executed",
                            "timestamp": datetime.utcnow().isoformat()
                        }
                        await websocket.send(json.dumps(response))
                        
            except websockets.exceptions.ConnectionClosed:
                self.connected = False
                
        async def start(self):
            self.server = await websockets.serve(self.handler, "localhost", 8765)
            
        async def stop(self):
            if self.server:
                self.server.close()
                await self.server.wait_closed()
    
    server = DeviceServer()
    yield server
    # Cleanup
    await server.stop()

class DeviceCommunicationManager:
    """Main class for managing device communications"""
    
    def __init__(self, config):
        self.config = config
        self.connection = None
        self.is_connected = False
        self.message_queue = asyncio.Queue()
        self.telemetry_data = {}
        self.command_history = []
        
    async def connect(self):
        """Establish connection to device"""
        try:
            uri = f"ws://{self.config['connection_params']['host']}:{self.config['connection_params']['port']}"
            self.connection = await websockets.connect(uri)
            self.is_connected = True
            
            # Send handshake
            handshake = {
                "type": "handshake",
                "device_id": self.config["device_id"],
                "timestamp": datetime.utcnow().isoformat()
            }
            await self.connection.send(json.dumps(handshake))
            
            # Wait for handshake acknowledgment
            response = await self.connection.recv()
            ack = json.loads(response)
            
            if ack.get("status") == "connected":
                asyncio.create_task(self._receive_messages())
                return True
            return False
            
        except Exception as e:
            self.is_connected = False
            raise ConnectionError(f"Failed to connect: {str(e)}")
    
    async def disconnect(self):
        """Disconnect from device"""
        if self.connection:
            await self.connection.close()
            self.is_connected = False
    
    async def _receive_messages(self):
        """Receive messages from device"""
        try:
            async for message in self.connection:
                data = json.loads(message)
                await self.message_queue.put(data)
                
                # Process telemetry data
                if data.get("type") == "telemetry":
                    self.telemetry_data = data.get("data", {})
                    
        except websockets.exceptions.ConnectionClosed:
            self.is_connected = False
    
    async def send_command(self, command):
        """Send command to device"""
        if not self.is_connected:
            raise ConnectionError("Device not connected")
            
        command["id"] = f"CMD-{datetime.utcnow().timestamp()}"
        command["timestamp"] = datetime.utcnow().isoformat()
        
        await self.connection.send(json.dumps(command))
        self.command_history.append(command)
        
        # Wait for acknowledgment
        timeout = self.config["connection_params"]["timeout"]
        try:
            while True:
                message = await asyncio.wait_for(self.message_queue.get(), timeout=timeout)
                if message.get("type") == "command_ack" and message.get("command_id") == command["id"]:
                    return message
        except asyncio.TimeoutError:
            raise TimeoutError(f"Command acknowledgment timeout after {timeout}s")
    
    def get_telemetry(self):
        """Get latest telemetry data"""
        return self.telemetry_data
    
    def get_connection_status(self):
        """Get current connection status"""
        return {
            "connected": self.is_connected,
            "device_id": self.config["device_id"],
            "uptime": len(self.command_history),
            "last_command": self.command_history[-1] if self.command_history else None
        }

# End-to-end test cases
@pytest.mark.asyncio
class TestDeviceCommunicationE2E:
    """End-to-end tests for Device Communication Management"""
    
    async def test_e2e_complete_device_lifecycle(self, device_config, mock_device_server, test_messages):
        """
        E2E Test 1: Complete device lifecycle from connection to disconnection
        
        Scenario:
        1. Start device server
        2. Initialize communication manager
        3. Connect to device
        4. Send multiple commands
        5. Receive telemetry data
        6. Handle connection interruption
        7. Reconnect
        8. Graceful disconnection
        
        Acceptance Criteria:
        - Device connects successfully within timeout
        - All commands are acknowledged
        - Telemetry data is received and processed
        - Connection recovery works properly
        - Disconnection is handled gracefully
        """
        # Start mock device server
        await mock_device_server.start()
        await asyncio.sleep(0.1)  # Allow server to start
        
        # Initialize communication manager
        manager = DeviceCommunicationManager(device_config)
        
        # Test connection establishment
        connected = await manager.connect()
        assert connected is True
        assert manager.is_connected is True
        
        status = manager.get_connection_status()
        assert status["connected"] is True
        assert status["device_id"] == "DEV-001-IMMERSIVE"
        
        # Test sending multiple commands
        commands = [
            {
                "type": "command",
                "action": "enable_haptic_feedback",
                "parameters": {"intensity": 0.7, "pattern": "pulse"}
            },
            {
                "type": "command",
                "action": "calibrate_sensors",
                "parameters": {"sensors": ["accelerometer", "gyroscope"]}
            },
            {
                "type": "command",
                "action": "set_sampling_rate",
                "parameters": {"rate_hz": 100}
            }
        ]
        
        for cmd in commands:
            response = await manager.send_command(cmd)
            assert response["status"] == "executed"
            assert response["command_id"] is not None
        
        # Verify command history
        assert len(manager.command_history) == 3
        
        # Test connection interruption and recovery
        await mock_device_server.stop()
        await asyncio.sleep(0.1)
        
        # Attempt command on disconnected device
        with pytest.raises(ConnectionError):
            await manager.send_command(commands[0])
        
        # Restart server and reconnect
        await mock_device_server.start()
        await asyncio.sleep(0.1)
        
        manager = DeviceCommunicationManager(device_config)
        connected = await manager.connect()
        assert connected is True
        
        # Test graceful disconnection
        await manager.disconnect()
        assert manager.is_connected is False
        
        # Cleanup
        await mock_device_server.stop()
    
    async def test_e2e_real_time_telemetry_streaming(self, device_config, test_messages):
        """
        E2E Test 2: Real-time telemetry data streaming and processing
        
        Scenario:
        1. Connect to device
        2. Enable telemetry streaming
        3. Receive continuous telemetry updates
        4. Process and validate telemetry data
        5. Detect anomalies in telemetry
        6. Adjust device parameters based on telemetry
        
        Acceptance Criteria:
        - Telemetry data is received at expected intervals
        - All telemetry fields are properly parsed
        - Anomaly detection triggers appropriate actions
        - System responds to telemetry-based adjustments
        """
        # Mock telemetry server with streaming capability
        telemetry_stream = []
        anomaly_detected = False
        
        async def telemetry_handler(websocket, path):
            # Send handshake ack
            handshake = await websocket.recv()
            ack = {"type": "handshake_ack", "status": "connected"}
            await websocket.send(json.dumps(ack))
            
            # Start telemetry streaming
            for i in range(10):
                telemetry = {
                    "type": "telemetry",
                    "sequence": i,
                    "data": {
                        "temperature": 36.5 + (i * 0.2),  # Gradually increasing temp
                        "battery_level": 100 - (i * 2),
                        "signal_strength": -40 - i,
                        "heart_rate": 70 + (i * 2),
                        "motion": {
                            "acceleration": {"x": 0.1 * i, "y": 0.2 * i, "z": 9.8},
                            "rotation": {"pitch": i, "roll": i/2, "yaw": i/3}
                        }
                    },
                    "timestamp": datetime.utcnow().isoformat()
                }
                
                telemetry_stream.append(telemetry)
                await websocket.send(json.dumps(telemetry))
                
                # Check for anomaly (high temperature)
                if telemetry["data"]["temperature"] > 38.5:
                    anomaly_detected = True
                
                # Listen for commands
                try:
                    command = await asyncio.wait_for(websocket.recv(), timeout=0.1)
                    cmd_data = json.loads(command)
                    if cmd_data.get("action") == "reduce_power":
                        # Acknowledge power reduction
                        ack = {
                            "type": "command_ack",
                            "command_id": cmd_data["id"],
                            "status": "executed"
                        }
                        await websocket.send(json.dumps(ack))
                except asyncio.TimeoutError:
                    pass
                
                await asyncio.sleep(0.5)  # 2Hz telemetry rate
        
        # Start telemetry server
        server = await websockets.serve(telemetry_handler, "localhost", 8765)
        
        try:
            # Connect and process telemetry
            manager = DeviceCommunicationManager(device_config)
            await manager.connect()
            
            # Collect telemetry for 5 seconds
            collected_telemetry = []
            start_time = datetime.utcnow()
            
            while (datetime.utcnow() - start_time).seconds < 5:
                await asyncio.sleep(0.1)
                telemetry = manager.get_telemetry()
                if telemetry:
                    collected_telemetry.append(telemetry)
                    
                    # Check for anomalies and respond
                    if telemetry.get("temperature", 0) > 38.5:
                        # Send power reduction command
                        cmd = {
                            "type": "command",
                            "action": "reduce_power",
                            "parameters": {"level": 0.7}
                        }
                        await manager.send_command(cmd)
            
            # Validate telemetry collection
            assert len(collected_telemetry) >= 8  # At least 8 samples in 5 seconds at 2Hz
            
            # Verify telemetry data integrity
            for telemetry in collected_telemetry:
                assert "temperature" in telemetry
                assert "battery_level" in telemetry
                assert "signal_strength" in telemetry
                assert "motion" in telemetry
            
            # Verify anomaly was detected and handled
            assert anomaly_detected is True
            assert any(cmd["action"] == "reduce_power" for cmd in manager.command_history)
            
        finally:
            server.close()
            await server.wait_closed()
    
    async def test_e2e_multi_device_coordination(self, device_config):
        """
        E2E Test 3: Multi-device coordination and synchronization
        
        Scenario:
        1. Connect multiple devices
        2. Synchronize device states
        3. Coordinate actions across devices
        4. Handle device failures
        5. Maintain data consistency
        6. Load balance communications
        
        Acceptance Criteria:
        - All devices connect successfully
        - Commands are synchronized across devices
        - Failure of one device doesn't affect others
        - Data remains consistent across all devices
        - Load is distributed evenly
        """
        # Create multiple device configurations
        devices = [
            {
                **device_config,
                "device_id": f"DEV-00{i}-IMMERSIVE",
                "connection_params": {
                    **device_config["connection_params"],
                    "port": 8765 + i
                }
            }
            for i in range(3)
        ]
        
        # Mock device servers
        servers = []
        device_states = {}
        
        async def multi_device_handler(device_id):
            async def handler(websocket, path):
                device_states[device_id] = {
                    "connected": True,
                    "commands_received": 0,
                    "last_sync": None
                }
                
                # Handle handshake
                handshake = await websocket.recv()
                ack = {
                    "type": "handshake_ack",
                    "status": "connected",
                    "device_info": {"id": device_id}
                }
                await websocket.send(json.dumps(ack))
                
                # Handle messages
                try:
                    async for message in websocket:
                        data = json.loads(message)
                        
                        if data.get("type") == "command":
                            device_states[device_id]["commands_received"] += 1
                            
                            if data.get("action") == "sync_state":
                                device_states[device_id]["last_sync"] = datetime.utcnow()
                            
                            # Simulate processing delay for load testing
                            await asyncio.sleep(0.1)
                            
                            # Send acknowledgment
                            ack = {
                                "type": "command_ack",
                                "command_id": data.get("id"),
                                "status": "executed",
                                "device_id": device_id
                            }
                            await websocket.send(json.dumps(ack))
                            
                except websockets.exceptions.ConnectionClosed:
                    device_states[device_id]["connected"] = False
            
            return handler
        
        # Start all device servers
        for i, dev_config in enumerate(devices):
            handler = multi_device_handler(dev_config["device_id"])
            server = await websockets.serve(
                handler(dev_config["device_id"]),
                "localhost",
                dev_config["connection_params"]["port"]
            )
            servers.append(server)
        
        try:
            # Connect all devices
            managers = []
            for dev_config in devices:
                manager = DeviceCommunicationManager(dev_config)
                await manager.connect()
                managers.append(manager)
            
            # Verify all devices connected
            assert all(m.is_connected for m in managers)
            
            # Test synchronized commands
            sync_command = {
                "type": "command",
                "action": "sync_state",
                "parameters": {
                    "timestamp": datetime.utcnow().isoformat(),
                    "mode": "immersive",
                    "profile": "high_precision"
                }
            }
            
            # Send sync command to all devices
            sync_tasks = [m.send_command(sync_command.copy()) for m in managers]
            responses = await asyncio.gather(*sync_tasks)
            
            # Verify all devices acknowledged
            assert all(r["status"] == "executed" for r in responses)
            
            # Test load distribution
            commands_per_device = {dev["device_id"]: [] for dev in devices}
            
            # Send 30 commands distributed across devices
            for i in range(30):
                device_idx = i % len(managers)
                manager = managers[device_idx]
                
                cmd = {
                    "type": "command",
                    "action": "process_data",
                    "parameters": {"data_id": f"DATA-{i:03d}"}
                }
                
                response = await manager.send_command(cmd)
                commands_per_device[devices[device_idx]["device_id"]].append(response)
            
            # Verify load distribution
            for device_id, commands in commands_per_device.items():
                assert len(commands) == 10  # Each device should get 10 commands
                assert device_states[device_id]["commands_received"] >= 10
            
            # Test device failure handling
            # Stop one server
            await servers[1].close()
            await servers[1].wait_closed()
            await asyncio.sleep(0.1)
            
            # Verify other devices still functional
            test_cmd = {
                "type": "command",
                "action": "health_check",
                "parameters": {}
            }
            
            # Device 0 should still work
            response = await managers[0].send_command(test_cmd)
            assert response["status"] == "executed"
            
            # Device 1 should fail
            with pytest.raises(ConnectionError):
                await managers[1].send_command(test_cmd)
            
            # Device 2 should still work
            response = await managers[2].send_command(test_cmd)
            assert response["status"] == "executed"
            
            # Verify data consistency
            assert device_states[devices[0]["device_id"]]["connected"] is True
            assert device_states[devices[2]["device_id"]]["connected"] is True
            
            # All active devices should have received sync
            active_devices = [devices[0]["device_id"], devices[2]["device_id"]]
            for dev_id in active_devices:
                assert device_states[dev_id]["last_sync"] is not None
            
        finally:
            # Cleanup all servers
            for server in servers:
                if hasattr(server, 'close'):
                    server.close()
                    await server.wait_closed()

# Additional helper tests for edge cases
@pytest.mark.asyncio
async def test_e2e_connection_retry_mechanism(device_config):
    """Test automatic retry mechanism for failed connections"""
    manager = DeviceCommunicationManager(device_config)
    
    # No server running - should fail
    with pytest.raises(ConnectionError):
        await manager.connect()
    
    # Start server after initial failure
    async def delayed_server(websocket, path):
        handshake = await websocket.recv()
        ack = {"type": "handshake_ack", "status": "connected"}
        await websocket.send(json.dumps(ack))
        await websocket.wait_closed()
    
    # Wait then start server
    await asyncio.sleep(1)
    server = await websockets.serve(delayed_server, "localhost", 8765)
    
    try:
        # Retry connection
        connected = await manager.connect()
        assert connected is True
    finally:
        server.close()
        await server.wait_closed()

@pytest.mark.asyncio
async def test_e2e_message_queue_overflow(device_config):
    """Test behavior when message queue overflows"""
    async def flooding_server(websocket, path):
        # Send handshake ack
        handshake = await websocket.recv()
        ack = {"type": "handshake_ack", "status": "connected"}
        await websocket.send(json.dumps(ack))
        
        # Flood with messages
        for i in range(1000):
            msg = {
                "type": "telemetry",
                "sequence": i,
                "data": {"value": i},
                "timestamp": datetime.utcnow().isoformat()
            }
            await websocket.send(json.dumps(msg))
            if i % 100 == 0:
                await asyncio.sleep(0.01)  # Small delay every 100 messages
    
    server = await websockets.serve(flooding_server, "localhost", 8765)
    
    try:
        manager = DeviceCommunicationManager(device_config)
        manager.message_queue = asyncio.Queue(maxsize=100)  # Limit queue size
        
        await manager.connect()
        await asyncio.sleep(2)  # Let messages accumulate
        
        # Queue should be at capacity but system should remain stable
        assert manager.is_connected is True
        assert manager.message_queue.qsize() <= 100
        
    finally:
        server.close()
        await server.wait_closed()

if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])