```python
import json
import time
import asyncio
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
from abc import ABC, abstractmethod
import math
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime


@dataclass
class Engine:
    """Represents a calculation engine."""
    id: str
    name: str
    description: str
    version: str
    
    def to_dict(self) -> Dict[str, str]:
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'version': self.version
        }


@dataclass
class SliderConfig:
    """Configuration for a slider control."""
    id: str
    label: str
    min_value: float
    max_value: float
    default_value: float
    step: float
    unit: str
    formula: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'label': self.label,
            'min': self.min_value,
            'max': self.max_value,
            'default': self.default_value,
            'step': self.step,
            'unit': self.unit,
            'formula': self.formula
        }


class VisualizationRenderer(ABC):
    """Abstract base class for 3D visualization rendering."""
    
    @abstractmethod
    def render(self, data: Dict[str, Any]) -> None:
        pass
    
    @abstractmethod
    def get_fps(self) -> float:
        pass


class Default3DRenderer(VisualizationRenderer):
    """Default 3D renderer implementation."""
    
    def __init__(self):
        self._fps = 60.0
        self._last_render_time = time.time()
        self._frame_count = 0
        self._running = True
        self._render_thread = threading.Thread(target=self._render_loop)
        self._render_thread.daemon = True
        self._render_thread.start()
        self._data = {}
    
    def _render_loop(self):
        """Main render loop running at 60 FPS."""
        frame_time = 1.0 / 60.0
        
        while self._running:
            start_time = time.time()
            
            # Simulate rendering
            self._do_render()
            
            # Calculate actual FPS
            self._frame_count += 1
            current_time = time.time()
            if current_time - self._last_render_time >= 1.0:
                self._fps = self._frame_count / (current_time - self._last_render_time)
                self._frame_count = 0
                self._last_render_time = current_time
            
            # Sleep to maintain 60 FPS
            elapsed = time.time() - start_time
            if elapsed < frame_time:
                time.sleep(frame_time - elapsed)
    
    def _do_render(self):
        """Perform actual rendering."""
        # Simulate rendering work
        pass
    
    def render(self, data: Dict[str, Any]) -> None:
        """Update render data."""
        self._data = data
    
    def get_fps(self) -> float:
        """Get current FPS."""
        return self._fps
    
    def stop(self):
        """Stop the render loop."""
        self._running = False
        self._render_thread.join()


class CalculationEngine:
    """Handles calculations based on slider values."""
    
    def __init__(self):
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._last_calculation_time = 0
    
    def calculate(self, engine_id: str, values: Dict[str, float]) -> Dict[str, Any]:
        """Perform calculation based on engine and values."""
        start_time = time.time()
        
        # Simulate calculation
        result = {
            'score': sum(values.values()) / len(values) if values else 0,
            'breakdown': values,
            'timestamp': datetime.now().isoformat()
        }
        
        # Ensure calculation time is tracked
        self._last_calculation_time = (time.time() - start_time) * 1000  # ms
        
        return result
    
    async def calculate_async(self, engine_id: str, values: Dict[str, float]) -> Dict[str, Any]:
        """Async version of calculate."""
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(self._executor, self.calculate, engine_id, values)
    
    def get_last_calculation_time(self) -> float:
        """Get the last calculation time in milliseconds."""
        return self._last_calculation_time


class EngineAPI:
    """API for managing calculation engines."""
    
    def __init__(self):
        self._engines = [
            Engine('engine1', 'Basic Engine', 'Simple calculations', '1.0.0'),
            Engine('engine2', 'Advanced Engine', 'Complex calculations', '2.0.0'),
            Engine('engine3', 'Premium Engine', 'Premium features', '3.0.0')
        ]
    
    def get_engines(self) -> List[Engine]:
        """Get list of available engines."""
        return self._engines
    
    def get_engine(self, engine_id: str) -> Optional[Engine]:
        """Get engine by ID."""
        for engine in self._engines:
            if engine.id == engine_id:
                return engine
        return None


class SchemaProvider:
    """Provides control schemas for engines."""
    
    def __init__(self):
        self._schemas = {
            'engine1': [
                SliderConfig('efficiency', 'Efficiency', 0, 100, 75, 1, '%', 'E = \\frac{Output}{Input} \\times 100'),
                SliderConfig('power', 'Power', 0, 1000, 500, 10, 'W', 'P = V \\times I'),
                SliderConfig('temperature', 'Temperature', 0, 100, 25, 0.5, '°C', 'T = T_0 + \\Delta T')
            ],
            'engine2': [
                SliderConfig('efficiency', 'Efficiency', 0, 100, 80, 1, '%', 'E = \\frac{Output}{Input} \\times 100'),
                SliderConfig('power', 'Power', 0, 2000, 1000, 20, 'W', 'P = V \\times I'),
                SliderConfig('temperature', 'Temperature', -20, 150, 30, 1, '°C', 'T = T_0 + \\Delta T'),
                SliderConfig('pressure', 'Pressure', 0, 10, 5, 0.1, 'bar', 'P = \\frac{F}{A}')
            ],
            'engine3': [
                SliderConfig('efficiency', 'Efficiency', 0, 100, 90, 0.5, '%', 'E = \\frac{Output}{Input} \\times 100'),
                SliderConfig('power', 'Power', 0, 5000, 2500, 50, 'W', 'P = V \\times I'),
                SliderConfig('temperature', 'Temperature', -50, 200, 50, 2, '°C', 'T = T_0 + \\Delta T'),
                SliderConfig('pressure', 'Pressure', 0, 20, 10, 0.5, 'bar', 'P = \\frac{F}{A}'),
                SliderConfig('flow_rate', 'Flow Rate', 0, 100, 50, 1, 'L/min', 'Q = A \\times v')
            ]
        }
    
    def get_schema(self, engine_id: str) -> List[SliderConfig]:
        """Get control schema for engine."""
        return self._schemas.get(engine_id, [])


class Tooltip:
    """Manages tooltip display."""
    
    def __init__(self):
        self._visible = False
        self._content = ''
        self._position = (0, 0)
    
    def show(self, content: str, position: tuple) -> None:
        """Show tooltip with content at position."""
        self._visible = True
        self._content = content
        self._position = position
    
    def hide(self) -> None:
        """Hide tooltip."""
        self._visible = False
    
    def get_content(self) -> str:
        """Get tooltip content."""
        return self._content if self._visible else ''
    
    def is_visible(self) -> bool:
        """Check if tooltip is visible."""
        return self._visible


class ControlPanel:
    """Main control panel for the visualization tool."""
    
    def __init__(self):
        self.api = EngineAPI()
        self.schema_provider = SchemaProvider()
        self.calculator = CalculationEngine()
        self.renderer = Default3DRenderer()
        self.tooltip = Tooltip()
        
        self._selected_engine: Optional[str] = None
        self._slider_values: Dict[str, float] = {}
        self._sliders: List[SliderConfig] = []
        self._score = 0.0
        self._update_callbacks: List[Callable] = []
    
    def get_engines(self) -> List[Dict[str, str]]:
        """Get list of available engines."""
        return [engine.to_dict() for engine in self.api.get_engines()]
    
    def select_engine(self, engine_id: str) -> None:
        """Select an engine and load its schema."""
        self._selected_engine = engine_id
        self._sliders = self.schema_provider.get_schema(engine_id)
        self._slider_values = {
            slider.id: slider.default_value 
            for slider in self._sliders
        }
        self._trigger_calculation()
    
    def get_sliders(self) -> List[Dict[str, Any]]:
        """Get current slider configurations."""
        return [slider.to_dict() for slider in self._sliders]
    
    def update_slider(self, slider_id: str, value: float) -> None:
        """Update slider value and trigger calculation."""
        if slider_id in self._slider_values:
            self._slider_values[slider_id] = value
            self._trigger_calculation()
    
    def _trigger_calculation(self) -> None:
        """Trigger calculation with current values."""
        if self._selected_engine:
            result = self.calculator.calculate(
                self._selected_engine, 
                self._slider_values
            )
            self._score = result['score']
            self.renderer.render(result)
            self._notify_update()
    
    async def update_slider_async(self, slider_id: str, value: float) -> None:
        """Async version of update_slider."""
        if slider_id in self._slider_values:
            self._slider_values[slider_id] = value
            if self._selected_engine:
                result = await self.calculator.calculate_async(
                    self._selected_engine,
                    self._slider_values
                )
                self._score = result['score']
                self.renderer.render(result)
                self._notify_update()
    
    def get_score(self) -> float:
        """Get current overall score."""
        return self._score
    
    def get_calculation_time(self) -> float:
        """Get last calculation time in milliseconds."""
        return self.calculator.get_last_calculation_time()
    
    def show_tooltip(self, slider_id: str, position: tuple) -> None:
        """Show tooltip for slider."""
        for slider in self._sliders:
            if slider.id == slider_id:
                self.tooltip.show(slider.formula, position)
                break
    
    def hide_tooltip(self) -> None:
        """Hide tooltip."""
        self.tooltip.hide()
    
    def get_tooltip_content(self) -> str:
        """Get current tooltip content."""
        return self.tooltip.get_content()
    
    def on_update(self, callback: Callable) -> None:
        """Register update callback."""
        self._update_callbacks.append(callback)
    
    def _notify_update(self) -> None:
        """Notify all update callbacks."""
        for callback in self._update_callbacks:
            callback()
    
    def get_fps(self) -> float:
        """Get current rendering FPS."""
        return self.renderer.get_fps()
    
    def shutdown(self) -> None:
        """Shutdown the control panel."""
        self.renderer.stop()


# Create global instance for easy access
control_panel = ControlPanel()


def create_app() -> ControlPanel:
    """Factory function to create a new control panel instance."""
    return ControlPanel()


if __name__ == "__main__":
    # Example usage
    panel = create_app()
    
    # Get available engines
    engines = panel.get_engines()
    print(f"Available engines: {engines}")
    
    # Select first engine
    if engines:
        panel.select_engine(engines[0]['id'])
        
        # Get sliders
        sliders = panel.get_sliders()
        print(f"Sliders: {sliders}")
        
        # Update a slider
        if sliders:
            panel.update_slider(sliders[0]['id'], 50.0)
            print(f"Score: {panel.get_score()}")
            print(f"Calculation time: {panel.get_calculation_time()}ms")
            print(f"FPS: {panel.get_fps()}")
    
    # Cleanup
    panel.shutdown()
```