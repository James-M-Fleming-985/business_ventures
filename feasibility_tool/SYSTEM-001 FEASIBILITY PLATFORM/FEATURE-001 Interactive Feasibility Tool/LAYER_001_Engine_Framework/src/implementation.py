```python
from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import json


class FeasibilityEngine(ABC):
    """Abstract base class for feasibility engines."""
    
    @abstractmethod
    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata about the engine."""
        pass
    
    @abstractmethod
    def get_input_schema(self) -> Dict[str, Any]:
        """Return JSON schema for input validation."""
        pass
    
    @abstractmethod
    def calculate(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Perform feasibility calculations."""
        pass
    
    @abstractmethod
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Validate inputs against schema."""
        pass


class EngineRegistry:
    """Registry for managing feasibility engines."""
    
    def __init__(self):
        self._engines: Dict[str, FeasibilityEngine] = {}
    
    def register(self, name: str, engine: FeasibilityEngine) -> None:
        """Register a new engine."""
        if not isinstance(engine, FeasibilityEngine):
            raise ValueError(f"Engine must be an instance of FeasibilityEngine")
        self._engines[name] = engine
    
    def list_engines(self) -> List[str]:
        """List all registered engine names."""
        return list(self._engines.keys())
    
    def get_engine(self, name: str) -> Optional[FeasibilityEngine]:
        """Get engine by name."""
        return self._engines.get(name)


class HoseOptimizationEngine(FeasibilityEngine):
    """Engine for hose optimization calculations."""
    
    def get_metadata(self) -> Dict[str, Any]:
        """Return metadata about the engine."""
        return {
            "name": "Hose Optimization Engine",
            "version": "1.0.0",
            "description": "Optimizes hose selection based on flow requirements"
        }
    
    def get_input_schema(self) -> Dict[str, Any]:
        """Return JSON schema for input validation."""
        return {
            "type": "object",
            "properties": {
                "flow_rate": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Flow rate in gallons per minute"
                },
                "pressure_drop": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Allowable pressure drop in PSI"
                },
                "hose_length": {
                    "type": "number",
                    "minimum": 0,
                    "description": "Hose length in feet"
                }
            },
            "required": ["flow_rate", "pressure_drop", "hose_length"]
        }
    
    def calculate(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Perform hose optimization calculations."""
        if not self.validate_inputs(inputs):
            raise ValueError("Invalid inputs")
        
        flow_rate = inputs["flow_rate"]
        pressure_drop = inputs["pressure_drop"]
        hose_length = inputs["hose_length"]
        
        # Calculate required diameter using Darcy-Weisbach equation approximation
        # This is simplified for demonstration purposes
        friction_factor = 0.02  # Assumed friction factor
        density = 8.34  # Water density in lb/gal
        
        # Calculate velocity for each standard hose size
        hose_sizes = {
            "0.5": 0.5,
            "0.75": 0.75,
            "1.0": 1.0,
            "1.25": 1.25,
            "1.5": 1.5
        }
        
        results = []
        formulas = {}
        
        for size_name, diameter in hose_sizes.items():
            # Calculate area
            area = 3.14159 * (diameter / 2) ** 2
            formula_area = f"A = π × (D/2)² = 3.14159 × ({diameter}/2)² = {area:.4f} in²"
            
            # Calculate velocity
            velocity = (flow_rate * 231) / (area * 12 * 60)  # Convert to ft/s
            formula_velocity = f"V = (Q × 231) / (A × 12 × 60) = ({flow_rate} × 231) / ({area:.4f} × 12 × 60) = {velocity:.2f} ft/s"
            
            # Calculate pressure drop using Darcy-Weisbach equation
            calculated_pressure_drop = (friction_factor * hose_length * density * velocity ** 2) / (2 * 32.2 * diameter / 12 * 144)
            formula_pressure = f"ΔP = (f × L × ρ × V²) / (2 × g × D × 144) = ({friction_factor} × {hose_length} × {density} × {velocity:.2f}²) / (2 × 32.2 × {diameter}/12 × 144) = {calculated_pressure_drop:.2f} PSI"
            
            formulas[size_name] = {
                "area": formula_area,
                "velocity": formula_velocity,
                "pressure_drop": formula_pressure
            }
            
            if calculated_pressure_drop <= pressure_drop:
                results.append({
                    "hose_diameter": diameter,
                    "pressure_drop": calculated_pressure_drop,
                    "velocity": velocity,
                    "suitable": True
                })
        
        # Select the smallest suitable hose
        suitable_hoses = [r for r in results if r["suitable"]]
        if suitable_hoses:
            recommended = min(suitable_hoses, key=lambda x: x["hose_diameter"])
        else:
            # If no suitable hose found, recommend the largest
            recommended = max(results, key=lambda x: x["hose_diameter"])
            recommended["suitable"] = False
        
        return {
            "recommended_diameter": recommended["hose_diameter"],
            "calculated_pressure_drop": round(recommended["pressure_drop"], 2),
            "velocity": round(recommended["velocity"], 2),
            "suitable": recommended["suitable"],
            "formulas": formulas[str(recommended["hose_diameter"])],
            "all_results": results
        }
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> bool:
        """Validate inputs against schema."""
        schema = self.get_input_schema()
        required_fields = schema.get("required", [])
        properties = schema.get("properties", {})
        
        # Check required fields
        for field in required_fields:
            if field not in inputs:
                return False
        
        # Check field types and constraints
        for field, value in inputs.items():
            if field not in properties:
                continue
            
            field_schema = properties[field]
            
            # Check type
            if field_schema.get("type") == "number":
                if not isinstance(value, (int, float)):
                    return False
                
                # Check minimum
                min_val = field_schema.get("minimum")
                if min_val is not None and value < min_val:
                    return False
        
        return True
```