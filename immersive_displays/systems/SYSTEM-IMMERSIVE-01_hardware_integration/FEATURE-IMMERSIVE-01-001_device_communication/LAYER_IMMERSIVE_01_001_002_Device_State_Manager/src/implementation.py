```python
import asyncio
from enum import Enum
from typing import Dict, Optional, Callable, Any
from datetime import datetime


class DeviceType(Enum):
    DISPLAY = "display"
    SENSOR = "sensor"
    CONTROLLER = "controller"


class DeviceState(Enum):
    CONNECTED = "connected"
    DISCONNECTED = "disconnected"
    ERROR = "error"
    INITIALIZING = "initializing"


class Device:
    """Represents a hardware device with state management."""
    
    def __init__(self, device_id: str, device_type: DeviceType):
        """
        Initialize a device.
        
        Args:
            device_id: Unique identifier for the device
            device_type: Type of the device (display, sensor, controller)
        """
        self.device_id = device_id
        self.device_type = device_type
        self.state = DeviceState.DISCONNECTED
        self.last_update = datetime.now()
        self.metadata: Dict[str, Any] = {}
        self._state_change_callbacks: list[Callable] = []
    
    def update_state(self, new_state: DeviceState, metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update the device state and notify callbacks.
        
        Args:
            new_state: New state for the device
            metadata: Optional metadata to associate with the state change
        """
        old_state = self.state
        self.state = new_state
        self.last_update = datetime.now()
        
        if metadata:
            self.metadata.update(metadata)
        
        # Notify all callbacks of state change
        for callback in self._state_change_callbacks:
            try:
                callback(self.device_id, old_state, new_state)
            except Exception:
                # Continue notifying other callbacks even if one fails
                pass
    
    def add_state_change_callback(self, callback: Callable) -> None:
        """Add a callback to be notified of state changes."""
        if callback not in self._state_change_callbacks:
            self._state_change_callbacks.append(callback)
    
    def remove_state_change_callback(self, callback: Callable) -> None:
        """Remove a state change callback."""
        if callback in self._state_change_callbacks:
            self._state_change_callbacks.remove(callback)


class DeviceStateManager:
    """Manages state for multiple hardware devices."""
    
    def __init__(self):
        """Initialize the device state manager."""
        self._devices: Dict[str, Device] = {}
        self._global_callbacks: list[Callable] = []
        self._lock = asyncio.Lock()
    
    async def register_device(self, device_id: str, device_type: DeviceType) -> Device:
        """
        Register a new device with the state manager.
        
        Args:
            device_id: Unique identifier for the device
            device_type: Type of the device
            
        Returns:
            The registered Device instance
            
        Raises:
            ValueError: If device_id already exists
        """
        async with self._lock:
            if device_id in self._devices:
                raise ValueError(f"Device with ID {device_id} already registered")
            
            device = Device(device_id, device_type)
            
            # Add global callback wrapper
            def global_callback_wrapper(dev_id, old_state, new_state):
                for callback in self._global_callbacks:
                    try:
                        callback(dev_id, old_state, new_state)
                    except Exception:
                        pass
            
            device.add_state_change_callback(global_callback_wrapper)
            self._devices[device_id] = device
            return device
    
    async def unregister_device(self, device_id: str) -> None:
        """
        Unregister a device from the state manager.
        
        Args:
            device_id: ID of the device to unregister
            
        Raises:
            KeyError: If device_id doesn't exist
        """
        async with self._lock:
            if device_id not in self._devices:
                raise KeyError(f"Device with ID {device_id} not found")
            
            del self._devices[device_id]
    
    async def get_device(self, device_id: str) -> Optional[Device]:
        """
        Get a device by its ID.
        
        Args:
            device_id: ID of the device to retrieve
            
        Returns:
            Device instance or None if not found
        """
        async with self._lock:
            return self._devices.get(device_id)
    
    async def update_device_state(self, device_id: str, new_state: DeviceState, 
                                  metadata: Optional[Dict[str, Any]] = None) -> None:
        """
        Update the state of a specific device.
        
        Args:
            device_id: ID of the device to update
            new_state: New state for the device
            metadata: Optional metadata for the state change
            
        Raises:
            KeyError: If device_id doesn't exist
        """
        async with self._lock:
            if device_id not in self._devices:
                raise KeyError(f"Device with ID {device_id} not found")
            
            self._devices[device_id].update_state(new_state, metadata)
    
    async def get_all_devices(self) -> Dict[str, Device]:
        """
        Get all registered devices.
        
        Returns:
            Dictionary mapping device IDs to Device instances
        """
        async with self._lock:
            return self._devices.copy()
    
    async def get_devices_by_type(self, device_type: DeviceType) -> Dict[str, Device]:
        """
        Get all devices of a specific type.
        
        Args:
            device_type: Type of devices to retrieve
            
        Returns:
            Dictionary mapping device IDs to Device instances of the specified type
        """
        async with self._lock:
            return {
                device_id: device
                for device_id, device in self._devices.items()
                if device.device_type == device_type
            }
    
    async def get_devices_by_state(self, state: DeviceState) -> Dict[str, Device]:
        """
        Get all devices in a specific state.
        
        Args:
            state: State to filter by
            
        Returns:
            Dictionary mapping device IDs to Device instances in the specified state
        """
        async with self._lock:
            return {
                device_id: device
                for device_id, device in self._devices.items()
                if device.state == state
            }
    
    def add_global_state_change_callback(self, callback: Callable) -> None:
        """
        Add a callback to be notified of all device state changes.
        
        Args:
            callback: Function to call on state changes (device_id, old_state, new_state)
        """
        if callback not in self._global_callbacks:
            self._global_callbacks.append(callback)
    
    def remove_global_state_change_callback(self, callback: Callable) -> None:
        """
        Remove a global state change callback.
        
        Args:
            callback: Callback function to remove
        """
        if callback in self._global_callbacks:
            self._global_callbacks.remove(callback)
    
    async def reset_all_devices(self) -> None:
        """Reset all devices to DISCONNECTED state."""
        async with self._lock:
            for device in self._devices.values():
                device.update_state(DeviceState.DISCONNECTED)
```