```python
"""MQTT Device Controller implementation for immersive display systems."""

import json
import logging
import threading
import time
from typing import Any, Callable, Dict, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum
from datetime import datetime

import paho.mqtt.client as mqtt


class DeviceState(Enum):
    """Enumeration of device states."""
    UNKNOWN = "unknown"
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"


class CommandType(Enum):
    """Enumeration of command types."""
    POWER_ON = "power_on"
    POWER_OFF = "power_off"
    SET_BRIGHTNESS = "set_brightness"
    SET_COLOR = "set_color"
    RESET = "reset"


@dataclass
class DeviceInfo:
    """Information about a connected device."""
    device_id: str
    device_type: str
    state: DeviceState = DeviceState.UNKNOWN
    last_seen: Optional[datetime] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)


@dataclass
class Command:
    """Command to be sent to a device."""
    command_id: str
    device_id: str
    command_type: CommandType
    parameters: Dict[str, Any] = field(default_factory=dict)
    timestamp: datetime = field(default_factory=datetime.now)
    status: str = "pending"
    result: Optional[Dict[str, Any]] = None


class MQTTDeviceController:
    """Controller for managing devices via MQTT protocol."""
    
    def __init__(self, broker_host: str, broker_port: int = 1883, client_id: Optional[str] = None):
        """
        Initialize the MQTT Device Controller.
        
        Args:
            broker_host: MQTT broker hostname or IP address
            broker_port: MQTT broker port (default: 1883)
            client_id: Optional client ID for MQTT connection
        """
        self.broker_host = broker_host
        self.broker_port = broker_port
        self.client_id = client_id or f"device_controller_{int(time.time())}"
        
        # Internal state
        self._connected = False
        self._devices: Dict[str, DeviceInfo] = {}
        self._commands: Dict[str, Command] = {}
        self._subscriptions: Set[str] = set()
        self._message_handlers: Dict[str, List[Callable]] = {}
        self._lock = threading.RLock()
        
        # MQTT client setup
        self._client = mqtt.Client(client_id=self.client_id)
        self._client.on_connect = self._on_connect
        self._client.on_disconnect = self._on_disconnect
        self._client.on_message = self._on_message
        
        # Configure logging
        self._logger = logging.getLogger(__name__)
        
        # Topic patterns
        self.device_status_topic = "devices/+/status"
        self.device_command_topic_pattern = "devices/{device_id}/command"
        self.device_response_topic_pattern = "devices/{device_id}/response"
        self.discovery_topic = "devices/discovery"
        
    def connect(self, username: Optional[str] = None, password: Optional[str] = None) -> bool:
        """
        Connect to the MQTT broker.
        
        Args:
            username: Optional username for authentication
            password: Optional password for authentication
            
        Returns:
            True if connection successful, False otherwise
        """
        try:
            if username and password:
                self._client.username_pw_set(username, password)
                
            self._client.connect(self.broker_host, self.broker_port, keepalive=60)
            self._client.loop_start()
            
            # Wait for connection to establish
            timeout = 5
            start_time = time.time()
            while not self._connected and (time.time() - start_time) < timeout:
                time.sleep(0.1)
                
            return self._connected
            
        except Exception as e:
            self._logger.error(f"Failed to connect to MQTT broker: {e}")
            return False
    
    def disconnect(self) -> None:
        """Disconnect from the MQTT broker."""
        self._client.loop_stop()
        self._client.disconnect()
        self._connected = False
        
    def subscribe(self, topic: str, handler: Optional[Callable] = None) -> bool:
        """
        Subscribe to an MQTT topic.
        
        Args:
            topic: MQTT topic to subscribe to
            handler: Optional message handler for this topic
            
        Returns:
            True if subscription successful, False otherwise
        """
        try:
            result = self._client.subscribe(topic)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                with self._lock:
                    self._subscriptions.add(topic)
                    if handler:
                        if topic not in self._message_handlers:
                            self._message_handlers[topic] = []
                        self._message_handlers[topic].append(handler)
                return True
            return False
        except Exception as e:
            self._logger.error(f"Failed to subscribe to topic {topic}: {e}")
            return False
    
    def unsubscribe(self, topic: str) -> bool:
        """
        Unsubscribe from an MQTT topic.
        
        Args:
            topic: MQTT topic to unsubscribe from
            
        Returns:
            True if unsubscription successful, False otherwise
        """
        try:
            result = self._client.unsubscribe(topic)
            if result[0] == mqtt.MQTT_ERR_SUCCESS:
                with self._lock:
                    self._subscriptions.discard(topic)
                    self._message_handlers.pop(topic, None)
                return True
            return False
        except Exception as e:
            self._logger.error(f"Failed to unsubscribe from topic {topic}: {e}")
            return False
    
    def publish(self, topic: str, payload: Any, qos: int = 1, retain: bool = False) -> bool:
        """
        Publish a message to an MQTT topic.
        
        Args:
            topic: MQTT topic to publish to
            payload: Message payload (will be JSON-encoded if dict)
            qos: Quality of Service level (0, 1, or 2)
            retain: Whether to retain the message on the broker
            
        Returns:
            True if publish successful, False otherwise
        """
        try:
            if isinstance(payload, dict):
                payload = json.dumps(payload)
            elif not isinstance(payload, (str, bytes)):
                payload = str(payload)
                
            result = self._client.publish(topic, payload, qos=qos, retain=retain)
            return result.rc == mqtt.MQTT_ERR_SUCCESS
        except Exception as e:
            self._logger.error(f"Failed to publish to topic {topic}: {e}")
            return False
    
    def discover_devices(self, timeout: float = 5.0) -> List[DeviceInfo]:
        """
        Discover devices on the network.
        
        Args:
            timeout: Discovery timeout in seconds
            
        Returns:
            List of discovered devices
        """
        # Subscribe to device status topics
        self.subscribe(self.device_status_topic)
        
        # Send discovery broadcast
        self.publish(self.discovery_topic, {"action": "discover"})
        
        # Wait for responses
        time.sleep(timeout)
        
        with self._lock:
            return list(self._devices.values())
    
    def get_device(self, device_id: str) -> Optional[DeviceInfo]:
        """
        Get information about a specific device.
        
        Args:
            device_id: Device identifier
            
        Returns:
            Device information if found, None otherwise
        """
        with self._lock:
            return self._devices.get(device_id)
    
    def get_all_devices(self) -> List[DeviceInfo]:
        """
        Get information about all known devices.
        
        Returns:
            List of all known devices
        """
        with self._lock:
            return list(self._devices.values())
    
    def send_command(self, device_id: str, command_type: CommandType, 
                    parameters: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Send a command to a device.
        
        Args:
            device_id: Target device identifier
            command_type: Type of command to send
            parameters: Optional command parameters
            
        Returns:
            Command ID if successful, None otherwise
        """
        command = Command(
            command_id=f"cmd_{device_id}_{int(time.time() * 1000)}",
            device_id=device_id,
            command_type=command_type,
            parameters=parameters or {}
        )
        
        with self._lock:
            self._commands[command.command_id] = command
        
        # Subscribe to response topic
        response_topic = self.device_response_topic_pattern.format(device_id=device_id)
        self.subscribe(response_topic)
        
        # Send command
        command_topic = self.device_command_topic_pattern.format(device_id=device_id)
        payload = {
            "command_id": command.command_id,
            "command": command_type.value,
            "parameters": command.parameters,
            "timestamp": command.timestamp.isoformat()
        }
        
        if self.publish(command_topic, payload):
            return command.command_id
        else:
            with self._lock:
                self._commands.pop(command.command_id, None)
            return None
    
    def get_command_status(self, command_id: str) -> Optional[Dict[str, Any]]:
        """
        Get the status of a command.
        
        Args:
            command_id: Command identifier
            
        Returns:
            Command status information if found, None otherwise
        """
        with self._lock:
            command = self._commands.get(command_id)
            if command:
                return {
                    "command_id": command.command_id,
                    "device_id": command.device_id,
                    "command_type": command.command_type.value,
                    "status": command.status,
                    "result": command.result,
                    "timestamp": command.timestamp.isoformat()
                }
        return None
    
    def _on_connect(self, client, userdata, flags, rc):
        """MQTT on_connect callback."""
        if rc == 0:
            self._connected = True
            self._logger.info(f"Connected to MQTT broker at {self.broker_host}:{self.broker_port}")
            
            # Resubscribe to topics
            with self._lock:
                for topic in self._subscriptions.copy():
                    client.subscribe(topic)
        else:
            self._connected = False
            self._logger.error(f"Failed to connect to MQTT broker: {mqtt.connack_string(rc)}")
    
    def _on_disconnect(self, client, userdata, rc):
        """MQTT on_disconnect callback."""
        self._connected = False
        if rc != 0:
            self._logger.warning(f"Unexpected disconnect from MQTT broker: {rc}")
    
    def _on_message(self, client, userdata, msg):
        """MQTT on_message callback."""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            # Try to parse JSON payload
            try:
                data = json.loads(payload)
            except json.JSONDecodeError:
                data = payload
            
            # Handle device status updates
            if topic.startswith("devices/") and topic.endswith("/status"):
                self._handle_device_status(topic, data)
            
            # Handle command responses
            elif topic.startswith("devices/") and topic.endswith("/response"):
                self._handle_command_response(topic, data)
            
            # Call registered handlers
            with self._lock:
                # Exact topic match
                if topic in self._message_handlers:
                    for handler in self._message_handlers[topic]:
                        try:
                            handler(topic, data)
                        except Exception as e:
                            self._logger.error(f"Error in message handler: {e}")
                
                # Pattern matching for wildcard subscriptions
                for pattern, handlers in self._message_handlers.items():
                    if self._match_topic(pattern, topic):
                        for handler in handlers:
                            try:
                                handler(topic, data)
                            except Exception as e:
                                self._logger.error(f"Error in message handler: {e}")
                                
        except Exception as e:
            self._logger.error(f"Error processing message: {e}")
    
    def _handle_device_status(self, topic: str, data: Dict[str, Any]) -> None:
        """Handle device status updates."""
        parts = topic.split('/')
        if len(parts) >= 3:
            device_id = parts[1]
            
            with self._lock:
                if device_id not in self._devices:
                    self._devices[device_id] = DeviceInfo(
                        device_id=device_id,
                        device_type=data.get('device_type', 'unknown')
                    )
                
                device = self._devices[device_id]
                device.last_seen = datetime.now()
                
                # Update state
                state_str = data.get('state', 'unknown')
                try:
                    device.state = DeviceState(state_str)
                except ValueError:
                    device.state = DeviceState.UNKNOWN
                
                # Update properties
                if 'properties' in data:
                    device.properties.update(data['properties'])
                
                # Update capabilities
                if 'capabilities' in data:
                    device.capabilities = data['capabilities']
    
    def _handle_command_response(self, topic: str, data: Dict[str, Any]) -> None:
        """Handle command responses from devices."""
        command_id = data.get('command_id')
        if command_id:
            with self._lock:
                if command_id in self._commands:
                    command = self._commands[command_id]
                    command.status = data.get('status', 'unknown')
                    command.result = data.get('result', {})
    
    def _match_topic(self, pattern: str, topic: str) -> bool:
        """
        Match MQTT topic against pattern with wildcards.
        
        Args:
            pattern: Topic pattern (may contain + and # wildcards)
            topic: Actual topic to match
            
        Returns:
            True if topic matches pattern, False otherwise
        """
        pattern_parts = pattern.split('/')
        topic_parts = topic.split('/')
        
        if '#' in pattern_parts:
            # # must be the last element
            hash_index = pattern_parts.index('#')
            if hash_index != len(pattern_parts) - 1:
                return False
            
            # Check all parts before #
            if len(topic_parts) < hash_index:
                return False
            
            for i in range(hash_index):
                if pattern_parts[i] != '+' and pattern_parts[i] != topic_parts[i]:
                    return False
            return True
        
        # No # wildcard, must have same number of parts
        if len(pattern_parts) != len(topic_parts):
            return False
        
        # Check each part
        for pattern_part, topic_part in zip(pattern_parts, topic_parts):
            if pattern_part != '+' and pattern_part != topic_part:
                return False
        
        return True
    
    @property
    def is_connected(self) -> bool:
        """Check if connected to MQTT broker."""
        return self._connected
    
    @property
    def connected_devices_count(self) -> int:
        """Get the count of connected devices."""
        with self._lock:
            return sum(1 for device in self._devices.values() 
                      if device.state == DeviceState.CONNECTED)
```