"""
Feature Integration Module for Interactive Feasibility Tool
FEATURE-001

This module orchestrates the integration of all layers to provide
a unified interface for the Interactive Feasibility Tool.
"""

from pathlib import Path
import sys
from dataclasses import dataclass
from typing import Dict, List, Any, Optional, Tuple
import logging

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from layer implementations
from LAYER_001_Engine_Framework.src.implementation import (
    FeasibilityEngine, 
    EngineRegistry, 
    HoseOptimizationEngine
)
from LAYER_002_Material_Database.src.implementation import (
    MaterialRepository, 
    FluidRepository
)
from LAYER_003_Optimization_Engine.src.implementation import OptimizationEngine
from LAYER_004_API_Backend.src.implementation import (
    PerformanceTracker, 
    Engine as APIEngine, 
    APIHandler
)
from LAYER_005_3D_Visualization_Frontend.src.implementation import (
    Engine as FrontendEngine,
    SliderConfig,
    VisualizationRenderer,
    Default3DRenderer,
    CalculationEngine,
    EngineAPI,
    SchemaProvider,
    Tooltip,
    ControlPanel
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FeatureConfig:
    """Configuration for the Interactive Feasibility Tool."""
    enable_performance_tracking: bool = True
    default_engine: str = "hose_optimization"
    max_calculation_timeout: float = 30.0
    visualization_fps_target: int = 60


@dataclass
class FeatureResponse:
    """Unified response structure for feature operations."""
    success: bool
    data: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


class FeatureOrchestrator:
    """
    Main orchestrator for the Interactive Feasibility Tool feature.
    
    This class coordinates all layers to provide a unified interface
    for feasibility analysis with interactive 3D visualization.
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Initialize the feature orchestrator.
        
        Args:
            config: Feature configuration object
        """
        self.config = config or FeatureConfig()
        self._initialized = False
        
        # Layer instances
        self.engine_registry: Optional[EngineRegistry] = None
        self.material_repo: Optional[MaterialRepository] = None
        self.fluid_repo: Optional[FluidRepository] = None
        self.optimization_engine: Optional[OptimizationEngine] = None
        self.performance_tracker: Optional[PerformanceTracker] = None
        self.control_panel: Optional[ControlPanel] = None
        self.visualization_renderer: Optional[VisualizationRenderer] = None
        
        # Initialize layers
        self._initialize_layers()
    
    def _initialize_layers(self) -> None:
        """Initialize all layer components with error handling."""
        try:
            # Layer 1: Engine Framework
            self.engine_registry = EngineRegistry()
            hose_engine = HoseOptimizationEngine()
            self.engine_registry.register("hose_optimization", hose_engine)
            
            # Layer 2: Material Database
            self.material_repo = MaterialRepository()
            self.fluid_repo = FluidRepository()
            
            # Layer 3: Optimization Engine
            self.optimization_engine = OptimizationEngine()
            
            # Layer 4: API Backend
            if self.config.enable_performance_tracking:
                self.performance_tracker = PerformanceTracker()
            
            # Layer 5: 3D Visualization Frontend
            self.visualization_renderer = Default3DRenderer()
            self.control_panel = ControlPanel()
            
            self._initialized = True
            logger.info("All layers initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize layers: {str(e)}")
            self._initialized = False
            raise
    
    def get_available_engines(self) -> FeatureResponse:
        """
        Get list of available calculation engines.
        
        Returns:
            FeatureResponse with engine list and metadata
        """
        if not self._initialized:
            return FeatureResponse(
                success=False,
                error="Feature not properly initialized"
            )
        
        try:
            engines = self.engine_registry.list_engines()
            engine_data = []
            
            for engine_name in engines:
                engine = self.engine_registry.get_engine(engine_name)
                if engine:
                    metadata = engine.get_metadata()
                    engine_data.append({
                        "name": engine_name,
                        "metadata": metadata
                    })
            
            return FeatureResponse(
                success=True,
                data={"engines": engine_data},
                metadata={"count": len(engine_data)}
            )
            
        except Exception as e:
            logger.error(f"Error getting available engines: {str(e)}")
            return FeatureResponse(
                success=False,
                error=str(e)
            )
    
    def get_engine_schema(self, engine_name: str) -> FeatureResponse:
        """
        Get input schema for a specific engine.
        
        Args:
            engine_name: Name of the engine
            
        Returns:
            FeatureResponse with engine schema
        """
        if not self._initialized:
            return FeatureResponse(
                success=False,
                error="Feature not properly initialized"
            )
        
        try:
            engine = self.engine_registry.get_engine(engine_name)
            if not engine:
                return FeatureResponse(
                    success=False,
                    error=f"Engine '{engine_name}' not found"
                )
            
            schema = engine.get_input_schema()
            
            return FeatureResponse(
                success=True,
                data={"schema": schema},
                metadata={"engine": engine_name}
            )
            
        except Exception as e:
            logger.error(f"Error getting engine schema: {str(e)}")
            return FeatureResponse(
                success=False,
                error=str(e)
            )
    
    def calculate_feasibility(
        self, 
        engine_name: str, 
        parameters: Dict[str, Any],
        optimize: bool = True
    ) -> FeatureResponse:
        """
        Run feasibility calculation with optional optimization.
        
        Args:
            engine_name: Name of the calculation engine
            parameters: Input parameters for calculation
            optimize: Whether to apply optimization
            
        Returns:
            FeatureResponse with calculation results
        """
        if not self._initialized:
            return FeatureResponse(
                success=False,
                error="Feature not properly initialized"
            )
        
        try:
            # Get engine
            engine = self.engine_registry.get_engine(engine_name)
            if not engine:
                return FeatureResponse(
                    success=False,
                    error=f"Engine '{engine_name}' not found"
                )
            
            # Validate inputs
            validation_result = engine.validate_inputs(parameters)
            if not validation_result.get("valid", False):
                return FeatureResponse(
                    success=False,
                    error="Input validation failed",
                    data={"validation_errors": validation_result.get("errors", [])}
                )
            
            # Perform calculation
            calculation_result = engine.calculate(parameters)
            
            # Apply optimization if requested
            if optimize and self.optimization_engine:
                # Prepare optimization parameters
                opt_params = []
                for key, value in parameters.items():
                    if isinstance(value, (int, float)):
                        opt_params.append({
                            "name": key,
                            "value": value,
                            "min": value * 0.8,  # Default range
                            "max": value * 1.2
                        })
                
                if opt_params:
                    # Run optimization
                    optimization_result = self.optimization_engine.optimize_parameters(
                        opt_params,
                        lambda p: self._objective_function(engine, p)
                    )
                    
                    calculation_result["optimization"] = optimization_result
            
            # Track performance if enabled
            if self.performance_tracker and calculation_result.get("calculation_time"):
                self.performance_tracker.add_response_time(
                    calculation_result["calculation_time"]
                )
            
            return FeatureResponse(
                success=True,
                data=calculation_result,
                metadata={
                    "engine": engine_name,
                    "optimized": optimize,
                    "parameter_count": len(parameters)
                }
            )
            
        except Exception as e:
            logger.error(f"Error in feasibility calculation: {str(e)}")
            return FeatureResponse(
                success=False,
                error=str(e)
            )
    
    def _objective_function(
        self, 
        engine: FeasibilityEngine, 
        parameters: List[Dict[str, Any]]
    ) -> float:
        """
        Objective function for optimization.
        
        Args:
            engine: Feasibility engine instance
            parameters: List of parameter dictionaries
            
        Returns:
            Objective value (lower is better)
        """
        try:
            # Convert parameter list to dict
            param_dict = {p["name"]: p["value"] for p in parameters}
            
            # Calculate with engine
            result = engine.calculate(param_dict)
            
            # Extract objective value (customize based on engine)
            if "total_cost" in result:
                return result["total_cost"]
            elif "efficiency" in result:
                return -result["efficiency"]  # Negative for maximization
            else:
                return 0.0
                
        except Exception:
            return float('inf')  # Return large value on error
    
    def get_materials(self) -> FeatureResponse:
        """
        Get all available materials from the database.
        
        Returns:
            FeatureResponse with material list
        """
        if not self._initialized or not self.material_repo:
            return FeatureResponse(
                success=False,
                error="Material repository not initialized"
            )
        
        try:
            materials = self.material_repo.get_all()
            
            return FeatureResponse(
                success=True,
                data={"materials": materials},
                metadata={"count": len(materials)}
            )
            
        except Exception as e:
            logger.error(f"Error getting materials: {str(e)}")
            return FeatureResponse(
                success=False,
                error=str(e)
            )
    
    def get_fluid_properties(
        self, 
        fluid_name: str, 
        temperature: float
    ) -> FeatureResponse:
        """
        Get fluid properties at specific temperature.
        
        Args:
            fluid_name: Name of the fluid
            temperature: Temperature in Celsius
            
        Returns:
            FeatureResponse with fluid properties
        """
        if not self._initialized or not self.fluid_repo:
            return FeatureResponse(
                success=False,
                error="Fluid repository not initialized"
            )
        
        try:
            fluid = self.fluid_repo.get_by_name_and_temperature(
                fluid_name, 
                temperature
            )
            
            if not fluid:
                return FeatureResponse(
                    success=False,
                    error=f"Fluid '{fluid_name}' not found at {temperature}°C"
                )
            
            return FeatureResponse(
                success=True,
                data={"fluid": fluid},
                metadata={
                    "name": fluid_name,
                    "temperature": temperature
                }
            )
            
        except Exception as e:
            logger.error(f"Error getting fluid properties: {str(e)}")
            return FeatureResponse(
                success=False,
                error=str(e)
            )
    
    def start_visualization(self, engine_name: str) -> FeatureResponse:
        """
        Start 3D visualization for specified engine.
        
        Args:
            engine_name: Name of the engine to visualize
            
        Returns:
            FeatureResponse with visualization status
        """
        if not self._initialized:
            return FeatureResponse(
                success=False,
                error="Feature not properly initialized"
            )
        
        try:
            # Select engine in control panel
            self.control_panel.select_engine(engine_name)
            
            # Start rendering
            render_result = self.visualization_renderer.render()
            
            # Get initial FPS
            fps = self.visualization_renderer.get_fps()
            
            return FeatureResponse(
                success=True,
                data={
                    "rendering": True,
                    "engine": engine_name,
                    "fps": fps
                },
                metadata={
                    "renderer": "Default3DRenderer",
                    "target_fps": self.config.visualization_fps_target
                }
            )
            
        except Exception as e:
            logger.error(f"Error starting visualization: {str(e)}")
            return FeatureResponse(
                success=False,
                error=str(e)
            )
    
    def update_visualization_parameter(
        self, 
        parameter_name: str, 
        value: float
    ) -> FeatureResponse:
        """
        Update a parameter in the visualization.
        
        Args:
            parameter_name: Name of the parameter
            value: New value
            
        Returns:
            FeatureResponse with update status
        """
        if not self._initialized or not self.control_panel:
            return FeatureResponse(
                success=False,
                error="Control panel not initialized"
            )
        
        try:
            # Update slider value
            self.control_panel.update_slider(parameter_name, value)
            
            # Get current score
            score = self.control_panel.get_score()
            
            # Get calculation time
            calc_time = self.control_panel.get_calculation_time()
            
            return FeatureResponse(
                success=True,
                data={
                    "parameter": parameter_name,
                    "value": value,
                    "score": score,
                    "calculation_time": calc_time
                }
            )
            
        except Exception as e:
            logger.error(f"Error updating visualization parameter: {str(e)}")
            return FeatureResponse(
                success=False,
                error=str(e)
            )
    
    def get_performance_metrics(self) -> FeatureResponse:
        """
        Get performance metrics for the system.
        
        Returns:
            FeatureResponse with performance data
        """
        if not self.config.enable_performance_tracking:
            return FeatureResponse(
                success=False,
                error="Performance tracking is disabled"
            )
        
        try:
            metrics = {
                "visualization_fps": self.visualization_renderer.get_fps() if self.visualization_renderer else None,
                "control_panel_fps": self.control_panel.get_fps() if self.control_panel else None
            }
            
            if self.performance_tracker:
                metrics["api_p95_response_time"] = self.performance_tracker.get_p95()
            
            return FeatureResponse(
                success=True,
                data={"metrics": metrics},
                metadata={"tracking_enabled": True}
            )
            
        except Exception as e:
            logger.error(f"Error getting performance metrics: {str(e)}")
            return FeatureResponse(
                success=False,
                error=str(e)
            )
    
    def shutdown(self) -> FeatureResponse:
        """
        Gracefully shutdown all components.
        
        Returns:
            FeatureResponse with shutdown status
        """
        try:
            # Stop visualization if running
            if self.visualization_renderer and hasattr(self.visualization_renderer, 'stop'):
                self.visualization_renderer.stop()
            
            # Shutdown control panel
            if self.control_panel:
                self.control_panel.shutdown()
            
            self._initialized = False
            
            return FeatureResponse(
                success=True,
                data={"status": "shutdown_complete"}
            )
            
        except Exception as e:
            logger.error(f"Error during shutdown: {str(e)}")
            return FeatureResponse(
                success=False,
                error=str(e)
            )


# Example usage
if __name__ == "__main__":
    # Create orchestrator with default config
    orchestrator = FeatureOrchestrator()
    
    # Get available engines
    engines_response = orchestrator.get_available_engines()
    if engines_response.success:
        print(f"Available engines: {engines_response.data}")
    
    # Run a calculation
    calc_response = orchestrator.calculate_feasibility(
        "hose_optimization",
        {
            "flow_rate": 100.0,
            "pressure": 10.0,
            "temperature": 25.0
        },
        optimize=True
    )
    
    if calc_response.success:
        print(f"Calculation result: {calc_response.data}")
    
    # Shutdown
    orchestrator.shutdown()
