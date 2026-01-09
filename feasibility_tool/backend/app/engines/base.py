# Feasibility Platform Backend

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field
import numpy as np
from datetime import datetime


# ============================================================================
# SCHEMAS & MODELS
# ============================================================================

class ParameterSchema(BaseModel):
    """Schema for input parameter definition"""
    name: str
    type: str  # "float", "integer", "select"
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    default: Any
    unit: str
    description: str
    options: Optional[List[str]] = None  # For dropdown/select inputs


class OutputSchema(BaseModel):
    """Schema for output metric definition"""
    name: str
    type: str
    unit: str
    description: str


class ComponentResult(BaseModel):
    """Individual calculation result with formula tracking"""
    value: float
    unit: str
    formula: str
    calculation_steps: List[str]
    normalized: float


class CalculationResult(BaseModel):
    """Complete calculation result"""
    components: Dict[str, ComponentResult]
    composites: Dict[str, float]
    visualization_point: Dict[str, float]
    overall_score: float
    metadata: Dict[str, Any] = Field(default_factory=dict)


class EngineMetadata(BaseModel):
    """Engine metadata"""
    engine_id: str
    name: str
    description: str
    version: str
    domain: str


# ============================================================================
# ENGINE INTERFACE
# ============================================================================

class FeasibilityEngine(ABC):
    """Abstract base class for feasibility engines"""
    
    @abstractmethod
    def get_metadata(self) -> EngineMetadata:
        """Return engine metadata"""
        pass
    
    @abstractmethod
    def get_input_schema(self) -> Dict[str, ParameterSchema]:
        """Return input parameter schema"""
        pass
    
    @abstractmethod
    def get_output_schema(self) -> Dict[str, OutputSchema]:
        """Return output metric schema"""
        pass
    
    @abstractmethod
    def calculate(self, inputs: Dict[str, Any]) -> CalculationResult:
        """Perform calculations with formula tracking"""
        pass
    
    @abstractmethod
    def get_target_profile(self, profile_name: str) -> Dict[str, Any]:
        """Return predefined optimal configuration"""
        pass


class EngineRegistry:
    """Singleton registry for managing engines"""
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._engines = {}
        return cls._instance
    
    def register(self, engine: FeasibilityEngine) -> None:
        """Register a new engine"""
        metadata = engine.get_metadata()
        self._engines[metadata.engine_id] = engine
    
    def list_engines(self) -> List[EngineMetadata]:
        """List all registered engines"""
        return [engine.get_metadata() for engine in self._engines.values()]
    
    def get_engine(self, engine_id: str) -> Optional[FeasibilityEngine]:
        """Retrieve engine by ID"""
        return self._engines.get(engine_id)


# ============================================================================
# HOSE OPTIMIZATION ENGINE
# ============================================================================

class HoseOptimizationEngine(FeasibilityEngine):
    """Reference implementation for hose/pipe optimization"""
    
    def get_metadata(self) -> EngineMetadata:
        return EngineMetadata(
            engine_id="hose_optimization",
            name="Hose/Pipe Optimization",
            description="Evaluate hydraulic, economic, and durability factors for hose configurations",
            version="1.0.0",
            domain="Energy Efficiency"
        )
    
    def get_input_schema(self) -> Dict[str, ParameterSchema]:
        return {
            # MATERIAL SELECTION (DROPDOWN)
            "material_type": ParameterSchema(
                name="Material Type",
                type="select",
                default="PVC",
                unit="",
                description="Hose material - affects cost, durability, temperature range",
                options=["PVC", "Rubber (NBR)", "Polyurethane (PU)", "EPDM", "Silicone", "PTFE"]
            ),
            "reinforcement_type": ParameterSchema(
                name="Reinforcement",
                type="select",
                default="Textile",
                unit="",
                description="Reinforcement type for pressure rating",
                options=["None", "Wire Braid", "Textile", "Aramid", "Steel Wire"]
            ),
            "climate_zone": ParameterSchema(
                name="Climate Zone",
                type="select",
                default="Temperate",
                unit="",
                description="Operating environment climate",
                options=["Hot/Tropical", "Cold/Arctic", "Temperate", "High UV/Desert", "Indoor/Controlled"]
            ),
            
            # GEOMETRY (SLIDERS)
            "Di": ParameterSchema(
                name="Inner Diameter",
                type="float",
                min_value=0.006,
                max_value=0.050,
                default=0.015,
                unit="m",
                description="Inner diameter of hose"
            ),
            "Do": ParameterSchema(
                name="Outer Diameter",
                type="float",
                min_value=0.010,
                max_value=0.060,
                default=0.021,
                unit="m",
                description="Outer diameter of hose"
            ),
            "L": ParameterSchema(
                name="Length",
                type="float",
                min_value=1.0,
                max_value=100.0,
                default=25.0,
                unit="m",
                description="Total hose length"
            ),
            "roughness": ParameterSchema(
                name="Surface Roughness",
                type="float",
                min_value=0.0015,
                max_value=0.15,
                default=0.007,
                unit="mm",
                description="Internal surface roughness (ε)"
            ),
            
            # FLOW CONDITIONS (SLIDERS)
            "flow_rate": ParameterSchema(
                name="Flow Rate",
                type="float",
                min_value=0.1,
                max_value=10.0,
                default=2.0,
                unit="L/s",
                description="Volumetric flow rate"
            ),
            "operating_pressure": ParameterSchema(
                name="Operating Pressure",
                type="float",
                min_value=1.0,
                max_value=30.0,
                default=10.0,
                unit="bar",
                description="System operating pressure"
            ),
            
            # ENVIRONMENTAL (SLIDERS)
            "ambient_temp": ParameterSchema(
                name="Ambient Temperature",
                type="float",
                min_value=-40.0,
                max_value=60.0,
                default=20.0,
                unit="°C",
                description="Operating environment temperature"
            ),
            "uv_exposure": ParameterSchema(
                name="UV Exposure",
                type="float",
                min_value=0.0,
                max_value=10.0,
                default=5.0,
                unit="hours/day",
                description="Daily UV exposure hours"
            ),
            
            # ECONOMIC (SLIDERS)
            "electricity_rate": ParameterSchema(
                name="Electricity Rate",
                type="float",
                min_value=0.05,
                max_value=0.50,
                default=0.12,
                unit="£/kWh",
                description="Cost of electricity for pumping"
            ),
            "operating_hours_per_year": ParameterSchema(
                name="Operating Hours/Year",
                type="float",
                min_value=500.0,
                max_value=8760.0,
                default=4000.0,
                unit="hours",
                description="Annual operating hours for lifetime cost calculation"
            ),
            "material_cost_per_kg": ParameterSchema(
                name="Material Cost Override",
                type="float",
                min_value=0.5,
                max_value=20.0,
                default=2.5,
                unit="£/kg",
                description="Override material cost per kg (defaults to database values if not provided)"
            ),
            "reinforcement_cost_mult": ParameterSchema(
                name="Reinforcement Cost Multiplier",
                type="float",
                min_value=1.0,
                max_value=3.0,
                default=1.3,
                unit="multiplier",
                description="Override reinforcement cost multiplier (defaults to database values if not provided)"
            ),
            "installation_cost_per_meter": ParameterSchema(
                name="Installation Cost Per Meter",
                type="float",
                min_value=0.0,
                max_value=100.0,
                default=25.0,
                unit="£/m",
                description="Labor and installation cost per meter (removal + fitting + downtime)"
            ),
        }
    
    def get_output_schema(self) -> Dict[str, OutputSchema]:
        return {
            "deltaP": OutputSchema(
                name="Pressure Drop",
                type="float",
                unit="bar",
                description="Total pressure loss through hose"
            ),
            "velocity": OutputSchema(
                name="Flow Velocity",
                type="float",
                unit="m/s",
                description="Average fluid velocity"
            ),
            "reynolds": OutputSchema(
                name="Reynolds Number",
                type="float",
                unit="dimensionless",
                description="Flow regime indicator"
            ),
        }
    
    def calculate(self, inputs: Dict[str, Any]) -> CalculationResult:
        """Perform hydraulic calculations using ALL 13 inputs"""
        from .calculations import comprehensive_calculate
        return comprehensive_calculate(inputs)

    
    def get_target_profile(self, profile_name: str) -> Dict[str, Any]:
        """Return predefined configurations"""
        profiles = {
            "Maximum Performance": {
                "Di": 0.020,
                "Do": 0.028,
                "L": 20.0,
                "flow_rate": 2.5
            },
            "Best ROI": {
                "Di": 0.015,
                "Do": 0.021,
                "L": 25.0,
                "flow_rate": 2.0
            },
            "Balanced": {
                "Di": 0.018,
                "Do": 0.025,
                "L": 22.0,
                "flow_rate": 2.2
            }
        }
        return profiles.get(profile_name, profiles["Balanced"])


# ============================================================================
# INITIALIZE REGISTRY
# ============================================================================

def initialize_engines():
    """Register all available engines"""
    registry = EngineRegistry()
    registry.register(HoseOptimizationEngine())
    return registry
