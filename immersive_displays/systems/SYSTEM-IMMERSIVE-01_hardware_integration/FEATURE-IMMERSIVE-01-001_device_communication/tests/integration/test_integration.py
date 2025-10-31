"""
Integration tests for Device Communication Management Feature
Feature ID: FEATURE-IMMERSIVE-01-001
Tests integration between MQTT Device Controller, Device State Manager, and Health Monitor Service
"""

import pytest
import asyncio
import json
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import paho.mqtt.client as mqtt
from typing import Dict, Any, List

# Assuming these are the actual module paths - adjust as needed
from src.mqtt_device_controller import MQTTDeviceController
from src.device_state_manager import DeviceStateManager
from src.health_monitor_service import HealthMonitorService


class TestDeviceCommunicationIntegration:
    """Integration tests for Device Communication Management feature"""

    @pytest.fixture
    async def mqtt_controller(self):
        """Create MQTT Device Controller instance"""
        controller = MQTTDeviceController(
            broker_address="test.mosquitto.org",
            port=1883,
            client_id="test_client"
        )
        yield controller
        await controller.disconnect()

    @pytest.fixture
    async def state_manager(self):
        """Create Device State Manager instance"""
        manager = DeviceStateManager()
        yield manager
        await manager.cleanup()

    @pytest.fixture
    async def health_monitor(self):
        """Create Health Monitor Service instance"""
        monitor = HealthMonitorService(
            check_interval=5,
            failure_threshold=3
        )
        yield monitor
        await monitor.stop()

    @pytest.fixture
    def mock_mqtt_client(self):
        """Mock MQTT client for testing"""
        client = Mock(spec=mqtt.Client)
        client.is_connected = Mock(return_value=True)
        client.publish = Mock(return_value=(0, 1))  # Success
        client.subscribe = Mock(return_value=(0, 1))  # Success
        return client

    @pytest.mark.asyncio
    async def test_device_registration_flow(self, mqtt_controller, state_manager, health_monitor):
        """
        Test complete device registration flow across all layers:
        1. Device connects via MQTT
        2. State Manager registers device
        3. Health Monitor starts monitoring
        """
        device_id = "device_001"
        device_data = {
            "device_id": device_id,
            "type": "sensor",
            "location": "room_1",
            "capabilities": ["temperature", "humidity"]
        }

        # Mock MQTT client
        with patch.object(mqtt_controller, 'client') as mock_client:
            mock_client.is_connected.return_value = True
            mock_client.publish.return_value = (0, 1)

            # Step 1: Device registration via MQTT
            registration_topic = f"devices/{device_id}/register"
            await mqtt_controller.publish(registration_topic, json.dumps(device_data))

            # Step 2: State Manager processes registration
            await state_manager.register_device(device_id, device_data)
            
            # Verify device is registered
            device_state = await state_manager.get_device_state(device_id)
            assert device_state is not None
            assert device_state["device_id"] == device_id
            assert device_state["status"] == "online"
            assert device_state["type"] == "sensor"

            # Step 3: Health Monitor starts monitoring
            await health_monitor.add_device(device_id)
            
            # Verify device is being monitored
            monitored_devices = await health_monitor.get_monitored_devices()
            assert device_id in monitored_devices
            
            # Simulate health check
            await health_monitor.check_device_health(device_id)
            health_status = await health_monitor.get_device_health(device_id)
            assert health_status["status"] == "healthy"
            assert health_status["last_check"] is not None

    @pytest.mark.asyncio
    async def test_state_update_propagation(self, mqtt_controller, state_manager, health_monitor):
        """
        Test state update propagation across layers:
        1. Device sends state update via MQTT
        2. State Manager updates internal state
        3. Health Monitor reflects updated state
        """
        device_id = "device_002"
        
        # Setup device
        await state_manager.register_device(device_id, {"type": "actuator"})
        await health_monitor.add_device(device_id)

        # Mock MQTT message callback
        state_update = {
            "device_id": device_id,
            "state": "active",
            "power": 85,
            "temperature": 22.5,
            "timestamp": datetime.now().isoformat()
        }

        with patch.object(mqtt_controller, 'client') as mock_client:
            mock_client.is_connected.return_value = True
            
            # Simulate MQTT state update
            update_topic = f"devices/{device_id}/state"
            
            # Mock the callback that would be triggered by MQTT message
            async def simulate_mqtt_callback():
                await state_manager.update_device_state(device_id, state_update)
            
            await simulate_mqtt_callback()

            # Verify state update in State Manager
            current_state = await state_manager.get_device_state(device_id)
            assert current_state["state"] == "active"
            assert current_state["power"] == 85
            assert current_state["temperature"] == 22.5

            # Verify Health Monitor acknowledges the update
            await health_monitor.process_state_update(device_id, state_update)
            health_status = await health_monitor.get_device_health(device_id)
            assert health_status["last_update"] is not None
            assert health_status["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_device_failure_detection_flow(self, mqtt_controller, state_manager, health_monitor):
        """
        Test device failure detection and recovery:
        1. Device stops responding
        2. Health Monitor detects failure
        3. State Manager updates status
        4. MQTT publishes alert
        """
        device_id = "device_003"
        
        # Setup device
        await state_manager.register_device(device_id, {"type": "camera"})
        await health_monitor.add_device(device_id)

        with patch.object(mqtt_controller, 'client') as mock_client:
            mock_client.is_connected.return_value = True
            mock_client.publish.return_value = (0, 1)

            # Simulate device going offline
            # Mock health check failures
            with patch.object(health_monitor, '_perform_health_check', return_value=False):
                
                # Simulate multiple failed health checks
                for _ in range(3):  # Assuming failure_threshold is 3
                    await health_monitor.check_device_health(device_id)
                
                # Verify device marked as unhealthy
                health_status = await health_monitor.get_device_health(device_id)
                assert health_status["status"] == "unhealthy"
                assert health_status["failure_count"] >= 3

                # State Manager should update device status
                await state_manager.update_device_status(device_id, "offline")
                device_state = await state_manager.get_device_state(device_id)
                assert device_state["status"] == "offline"

                # Verify MQTT alert published
                alert_topic = f"alerts/device_failure/{device_id}"
                mock_client.publish.assert_called()
                
                # Check if alert topic was used
                call_args = [call[0][0] for call in mock_client.publish.call_args_list]
                assert any(alert_topic in topic for topic in call_args)

    @pytest.mark.asyncio
    async def test_command_execution_flow(self, mqtt_controller, state_manager, health_monitor):
        """
        Test command execution flow:
        1. Command sent via MQTT
        2. State Manager validates command
        3. Device executes and reports back
        4. Health Monitor logs command execution
        """
        device_id = "device_004"
        
        # Setup device
        device_info = {
            "type": "actuator",
            "capabilities": ["on_off", "dim"],
            "status": "online"
        }
        await state_manager.register_device(device_id, device_info)
        await health_monitor.add_device(device_id)

        command = {
            "command_id": "cmd_001",
            "device_id": device_id,
            "action": "turn_on",
            "parameters": {"brightness": 75},
            "timestamp": datetime.now().isoformat()
        }

        with patch.object(mqtt_controller, 'client') as mock_client:
            mock_client.is_connected.return_value = True
            mock_client.publish.return_value = (0, 1)

            # Step 1: Send command via MQTT
            command_topic = f"devices/{device_id}/command"
            await mqtt_controller.publish(command_topic, json.dumps(command))

            # Step 2: State Manager validates command
            is_valid = await state_manager.validate_command(device_id, command)
            assert is_valid is True

            # Step 3: Simulate device execution and response
            response = {
                "command_id": "cmd_001",
                "status": "success",
                "result": {"state": "on", "brightness": 75},
                "timestamp": datetime.now().isoformat()
            }

            # Update state after command execution
            await state_manager.update_device_state(device_id, {
                "state": "on",
                "brightness": 75,
                "last_command": command["command_id"]
            })

            # Step 4: Health Monitor logs command execution
            await health_monitor.log_command_execution(device_id, command, response)
            
            # Verify command was logged
            command_history = await health_monitor.get_command_history(device_id)
            assert len(command_history) > 0
            assert command_history[-1]["command_id"] == "cmd_001"
            assert command_history[-1]["status"] == "success"

    @pytest.mark.asyncio
    async def test_multi_device_coordination(self, mqtt_controller, state_manager, health_monitor):
        """
        Test coordination between multiple devices:
        1. Register multiple devices
        2. Create device group
        3. Send group command
        4. Monitor group health
        """
        devices = [
            {"id": "device_005", "type": "light", "location": "living_room"},
            {"id": "device_006", "type": "light", "location": "living_room"},
            {"id": "device_007", "type": "sensor", "location": "living_room"}
        ]

        with patch.object(mqtt_controller, 'client') as mock_client:
            mock_client.is_connected.return_value = True
            mock_client.publish.return_value = (0, 1)
            mock_client.subscribe.return_value = (0, 1)

            # Step 1: Register all devices
            for device in devices:
                await state_manager.register_device(device["id"], device)
                await health_monitor.add_device(device["id"])

            # Step 2: Create device group
            group_id = "living_room_devices"
            device_ids = [d["id"] for d in devices]
            await state_manager.create_device_group(group_id, device_ids)

            # Step 3: Send group command (turn on all lights)
            group_command = {
                "group_id": group_id,
                "command": "turn_on",
                "filter": {"type": "light"},
                "timestamp": datetime.now().isoformat()
            }

            # Subscribe to group command responses
            response_topic = f"groups/{group_id}/responses/+"
            await mqtt_controller.subscribe(response_topic)

            # Publish group command
            command_topic = f"groups/{group_id}/command"
            await mqtt_controller.publish(command_topic, json.dumps(group_command))

            # Simulate device responses
            light_devices = [d for d in devices if d["type"] == "light"]
            for device in light_devices:
                await state_manager.update_device_state(device["id"], {"state": "on"})

            # Step 4: Monitor group health
            group_health = await health_monitor.get_group_health(device_ids)
            assert group_health["total_devices"] == 3
            assert group_health["healthy_devices"] >= 2  # At least the lights
            assert group_health["group_status"] == "healthy"

            # Verify all lights are on
            for device in light_devices:
                state = await state_manager.get_device_state(device["id"])
                assert state["state"] == "on"

    @pytest.mark.asyncio
    async def test_error_recovery_cascade(self, mqtt_controller, state_manager, health_monitor):
        """
        Test error handling and recovery across all layers:
        1. MQTT connection failure
        2. State Manager handles disconnection
        3. Health Monitor marks devices as unreachable
        4. Recovery process when connection restored
        """
        device_ids = ["device_008", "device_009"]
        
        # Setup devices
        for device_id in device_ids:
            await state_manager.register_device(device_id, {"type": "sensor"})
            await health_monitor.add_device(device_id)

        with patch.object(mqtt_controller, 'client') as mock_client:
            # Step 1: Simulate MQTT connection failure
            mock_client.is_connected.return_value = False
            mock_client.reconnect.side_effect = Exception("Connection failed")

            # Trigger connection check
            is_connected = await mqtt_controller.check_connection()
            assert is_connected is False

            # Step 2: State Manager handles disconnection
            await state_manager.handle_broker_disconnection()
            
            # All devices should be marked as unknown/unreachable
            for device_id in device_ids:
                state = await state_manager.get_device_state(device_id)
                assert state["status"] in ["unknown", "unreachable"]

            # Step 3: Health Monitor updates
            await health_monitor.handle_connection_loss()
            
            for device_id in device_ids:
                health = await health_monitor.get_device_health(device_id)
                assert health["status"] == "unreachable"

            # Step 4: Simulate connection recovery
            mock_client.is_connected.return_value = True
            mock_client.reconnect.side_effect = None
            mock_client.reconnect.return_value = None

            # Trigger reconnection
            await mqtt_controller.reconnect()
            
            # Recovery process
            await state_manager.handle_broker_reconnection()
            await health_monitor.handle_connection_restored()

            # Devices should be re-evaluated
            for device_id in device_ids:
                # Simulate device coming back online
                await state_manager.update_device_status(device_id, "online")
                await health_monitor.check_device_health(device_id)
                
                state = await state_manager.get_device_state(device_id)
                assert state["status"] == "online"
                
                health = await health_monitor.get_device_health(device_id)
                assert health["status"] in ["healthy", "recovering"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])