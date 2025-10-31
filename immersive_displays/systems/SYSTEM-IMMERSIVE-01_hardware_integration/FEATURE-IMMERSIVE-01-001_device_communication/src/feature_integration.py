"""
Feature Integration Module for Device Communication Management
Feature ID: FEATURE-IMMERSIVE-01-001
"""

from pathlib import Path
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Callable
from enum import Enum
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from standardized layer folders
from LAYER_IMMERSIVE_01_001_001_MQTT_Device_Controller.src.implementation import MQTTDeviceController
from LAYER_IMMERSIVE_01_001_002_Device_State_Manager.src.implementation import Device, DeviceStateManager
from LAYER_IMMERSIVE_01_001_003_Health_Monitor_Service.src.implementation import DeviceHealthMonitor


class ResponseStatus(Enum):
    """Response status enumeration"""
    SUCCESS = "success"
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


@dataclass
class FeatureResponse:
    """Unified response structure for feature operations"""
    status: ResponseStatus
    message: str
    data: Optional[Dict[str, Any]] = None
    errors: Optional[List[str]] = None


@dataclass
class FeatureConfig:
    """Configuration for Device Communication Management feature"""
    mqtt_broker_host: str = "localhost"
    mqtt_broker_port: int = 1883
    mqtt_client_id: str = "immersive_display_controller"
    health_check_interval: float = 30.0
    device_timeout_threshold: float = 60.0
    enable_auto_discovery: bool = True


class DeviceCommunicationOrchestrator:
    """
    Feature orchestrator for Device Communication Management
    
    This class coordinates interactions between:
    - MQTT Device Controller
    - Device State Manager
    - Health Monitor Service
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Initialize the feature orchestrator
        
        Args:
            config: Feature configuration object
        """
        self.config = config or FeatureConfig()
        self.logger = logging.getLogger(__name__)
        
        # Initialize layer instances
        self._mqtt_controller: Optional[MQTTDeviceController] = None
        self._state_manager: Optional[DeviceStateManager] = None
        self._health_monitor: Optional[DeviceHealthMonitor] = None
        
        # Initialize layers
        self._initialize_layers()
    
    def _initialize_layers(self) -> None:
        """Initialize all layer instances"""
        try:
            # Initialize MQTT Device Controller
            self._mqtt_controller = MQTTDeviceController()
            
            # Initialize Device State Manager
            self._state_manager = DeviceStateManager()
            
            # Initialize Health Monitor Service
            self._health_monitor = DeviceHealthMonitor()
            
            # Set up health monitoring configuration
            self._health_monitor.set_health_check_interval(self.config.health_check_interval)
            self._health_monitor.set_threshold('timeout', self.config.device_timeout_threshold)
            
            self.logger.info("All layers initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Error initializing layers: {str(e)}")
            raise
    
    def connect_to_mqtt(self) -> FeatureResponse:
        """
        Establish MQTT connection
        
        Returns:
            FeatureResponse with connection status
        """
        try:
            if not self._mqtt_controller:
                return FeatureResponse(
                    status=ResponseStatus.ERROR,
                    message="MQTT controller not initialized"
                )
            
            # Connect to MQTT broker
            self._mqtt_controller.connect()
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS,
                message="Successfully connected to MQTT broker",
                data={
                    "broker_host": self.config.mqtt_broker_host,
                    "broker_port": self.config.mqtt_broker_port,
                    "connected": self._mqtt_controller.is_connected()
                }
            )
            
        except Exception as e:
            self.logger.error(f"MQTT connection error: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                message="Failed to connect to MQTT broker",
                errors=[str(e)]
            )
    
    def disconnect_from_mqtt(self) -> FeatureResponse:
        """
        Disconnect from MQTT broker
        
        Returns:
            FeatureResponse with disconnection status
        """
        try:
            if not self._mqtt_controller:
                return FeatureResponse(
                    status=ResponseStatus.ERROR,
                    message="MQTT controller not initialized"
                )
            
            self._mqtt_controller.disconnect()
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS,
                message="Successfully disconnected from MQTT broker"
            )
            
        except Exception as e:
            self.logger.error(f"MQTT disconnection error: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                message="Failed to disconnect from MQTT broker",
                errors=[str(e)]
            )
    
    def discover_and_register_devices(self) -> FeatureResponse:
        """
        Discover devices and register them with health monitoring
        
        Returns:
            FeatureResponse with discovered devices information
        """
        try:
            if not all([self._mqtt_controller, self._health_monitor]):
                return FeatureResponse(
                    status=ResponseStatus.ERROR,
                    message="Required layers not initialized"
                )
            
            # Discover devices via MQTT
            devices = self._mqtt_controller.discover_devices()
            
            # Register each discovered device with health monitor
            registered_devices = []
            for device_id in devices:
                device_info = self._mqtt_controller.get_device(device_id)
                if device_info:
                    self._health_monitor.register_device(device_id)
                    registered_devices.append(device_id)
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Discovered and registered {len(registered_devices)} devices",
                data={
                    "discovered_devices": devices,
                    "registered_devices": registered_devices,
                    "total_count": len(registered_devices)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Device discovery error: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                message="Failed to discover and register devices",
                errors=[str(e)]
            )
    
    def send_device_command(self, device_id: str, command: str, parameters: Dict[str, Any]) -> FeatureResponse:
        """
        Send command to a specific device
        
        Args:
            device_id: Target device identifier
            command: Command to send
            parameters: Command parameters
            
        Returns:
            FeatureResponse with command execution result
        """
        try:
            if not self._mqtt_controller:
                return FeatureResponse(
                    status=ResponseStatus.ERROR,
                    message="MQTT controller not initialized"
                )
            
            # Send command via MQTT
            command_id = self._mqtt_controller.send_command(device_id, command, parameters)
            
            # Get command status
            status = self._mqtt_controller.get_command_status(command_id)
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Command sent to device {device_id}",
                data={
                    "device_id": device_id,
                    "command": command,
                    "command_id": command_id,
                    "status": status
                }
            )
            
        except Exception as e:
            self.logger.error(f"Command sending error: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                message=f"Failed to send command to device {device_id}",
                errors=[str(e)]
            )
    
    def get_device_health_status(self, device_id: Optional[str] = None) -> FeatureResponse:
        """
        Get health status for a specific device or all devices
        
        Args:
            device_id: Optional device identifier (None for all devices)
            
        Returns:
            FeatureResponse with health status information
        """
        try:
            if not self._health_monitor:
                return FeatureResponse(
                    status=ResponseStatus.ERROR,
                    message="Health monitor not initialized"
                )
            
            if device_id:
                # Get status for specific device
                status = self._health_monitor.get_device_status(device_id)
                alerts = self._health_monitor.get_device_alerts(device_id)
                
                return FeatureResponse(
                    status=ResponseStatus.SUCCESS,
                    message=f"Health status retrieved for device {device_id}",
                    data={
                        "device_id": device_id,
                        "status": status,
                        "alerts": alerts
                    }
                )
            else:
                # Get status for all devices
                statuses = self._health_monitor.get_all_device_statuses()
                all_alerts = self._health_monitor.get_all_alerts()
                
                return FeatureResponse(
                    status=ResponseStatus.SUCCESS,
                    message="Health status retrieved for all devices",
                    data={
                        "device_statuses": statuses,
                        "total_devices": len(statuses),
                        "alerts": all_alerts
                    }
                )
                
        except Exception as e:
            self.logger.error(f"Health status retrieval error: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                message="Failed to retrieve health status",
                errors=[str(e)]
            )
    
    def setup_state_monitoring(self, state_change_callback: Callable) -> FeatureResponse:
        """
        Set up global state change monitoring
        
        Args:
            state_change_callback: Callback function for state changes
            
        Returns:
            FeatureResponse with setup status
        """
        try:
            if not self._state_manager:
                return FeatureResponse(
                    status=ResponseStatus.ERROR,
                    message="State manager not initialized"
                )
            
            # Add global state change callback
            self._state_manager.add_global_state_change_callback(state_change_callback)
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS,
                message="State monitoring configured successfully",
                data={
                    "callback_registered": True
                }
            )
            
        except Exception as e:
            self.logger.error(f"State monitoring setup error: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                message="Failed to set up state monitoring",
                errors=[str(e)]
            )
    
    def subscribe_to_topic(self, topic: str) -> FeatureResponse:
        """
        Subscribe to MQTT topic
        
        Args:
            topic: MQTT topic to subscribe to
            
        Returns:
            FeatureResponse with subscription status
        """
        try:
            if not self._mqtt_controller:
                return FeatureResponse(
                    status=ResponseStatus.ERROR,
                    message="MQTT controller not initialized"
                )
            
            self._mqtt_controller.subscribe(topic)
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Successfully subscribed to topic: {topic}",
                data={"topic": topic}
            )
            
        except Exception as e:
            self.logger.error(f"Topic subscription error: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                message=f"Failed to subscribe to topic: {topic}",
                errors=[str(e)]
            )
    
    def publish_message(self, topic: str, payload: Dict[str, Any]) -> FeatureResponse:
        """
        Publish message to MQTT topic
        
        Args:
            topic: MQTT topic to publish to
            payload: Message payload
            
        Returns:
            FeatureResponse with publish status
        """
        try:
            if not self._mqtt_controller:
                return FeatureResponse(
                    status=ResponseStatus.ERROR,
                    message="MQTT controller not initialized"
                )
            
            self._mqtt_controller.publish(topic, payload)
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Message published to topic: {topic}",
                data={
                    "topic": topic,
                    "payload_size": len(str(payload))
                }
            )
            
        except Exception as e:
            self.logger.error(f"Message publish error: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                message=f"Failed to publish message to topic: {topic}",
                errors=[str(e)]
            )
    
    def get_connected_devices_info(self) -> FeatureResponse:
        """
        Get information about all connected devices
        
        Returns:
            FeatureResponse with connected devices information
        """
        try:
            if not self._mqtt_controller:
                return FeatureResponse(
                    status=ResponseStatus.ERROR,
                    message="MQTT controller not initialized"
                )
            
            # Get all devices and connection count
            all_devices = self._mqtt_controller.get_all_devices()
            connected_count = self._mqtt_controller.connected_devices_count()
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Retrieved information for {connected_count} connected devices",
                data={
                    "devices": all_devices,
                    "connected_count": connected_count,
                    "mqtt_connected": self._mqtt_controller.is_connected()
                }
            )
            
        except Exception as e:
            self.logger.error(f"Device info retrieval error: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                message="Failed to retrieve connected devices information",
                errors=[str(e)]
            )
    
    def register_health_check_function(self, device_id: str, check_function: Callable) -> FeatureResponse:
        """
        Register a custom health check function for a device
        
        Args:
            device_id: Device identifier
            check_function: Health check function
            
        Returns:
            FeatureResponse with registration status
        """
        try:
            if not self._health_monitor:
                return FeatureResponse(
                    status=ResponseStatus.ERROR,
                    message="Health monitor not initialized"
                )
            
            self._health_monitor.register_device_check_function(device_id, check_function)
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Health check function registered for device {device_id}",
                data={"device_id": device_id}
            )
            
        except Exception as e:
            self.logger.error(f"Health check registration error: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                message=f"Failed to register health check for device {device_id}",
                errors=[str(e)]
            )
    
    def get_metrics_history(self, device_id: str, metric_name: str, limit: int = 100) -> FeatureResponse:
        """
        Get historical metrics for a device
        
        Args:
            device_id: Device identifier
            metric_name: Name of the metric
            limit: Maximum number of records to retrieve
            
        Returns:
            FeatureResponse with metrics history
        """
        try:
            if not self._health_monitor:
                return FeatureResponse(
                    status=ResponseStatus.ERROR,
                    message="Health monitor not initialized"
                )
            
            history = self._health_monitor.get_metrics_history(device_id, metric_name, limit)
            
            return FeatureResponse(
                status=ResponseStatus.SUCCESS,
                message=f"Retrieved {len(history)} metrics records for device {device_id}",
                data={
                    "device_id": device_id,
                    "metric_name": metric_name,
                    "history": history,
                    "record_count": len(history)
                }
            )
            
        except Exception as e:
            self.logger.error(f"Metrics history retrieval error: {str(e)}")
            return FeatureResponse(
                status=ResponseStatus.ERROR,
                message=f"Failed to retrieve metrics history for device {device_id}",
                errors=[str(e)]
            )
