# Feasibility Tool - Pluggable Engine Architecture

**Date:** December 29, 2025  
**Purpose:** Generic feasibility tool with pluggable mathematical engines

---

## CORE CONCEPT

**A universal feasibility analysis platform where:**
1. User selects a mathematical engine (e.g., "Hose Optimization", "Solar Panel Sizing", etc.)
2. Control panel adapts to show relevant input variables for that engine
3. Engine performs calculations and returns normalized outputs
4. 3D visualization displays the response surface (input space → output space)
5. Tooltips show detailed calculations, formulas, and component values

---

## PLUGGABLE ENGINE INTERFACE

### Engine Contract (All Engines Must Implement)

```python
# Abstract Base Class
class FeasibilityEngine(ABC):
    """Base class for all mathematical engines"""
    
    @abstractmethod
    def get_metadata(self) -> EngineMetadata:
        """Return engine information and configuration"""
        return {
            "id": "hose_optimization",
            "name": "Hose Optimization Engine",
            "description": "Optimize hose design for performance, cost, lifetime",
            "version": "1.0.0",
            "author": "Engineering Team"
        }
    
    @abstractmethod
    def get_input_schema(self) -> InputSchema:
        """Define what inputs this engine needs"""
        return {
            "geometry": [
                {"id": "Di", "name": "Inner Diameter", "type": "slider", 
                 "unit": "mm", "range": [6, 50], "default": 15},
                {"id": "L", "name": "Length", "type": "slider",
                 "unit": "m", "range": [1, 100], "default": 25}
            ],
            "material": [
                {"id": "material_type", "name": "Material", "type": "dropdown",
                 "options": ["PVC", "PU", "EPDM", "Rubber"]}
            ],
            # ... etc
        }
    
    @abstractmethod
    def get_output_schema(self) -> OutputSchema:
        """Define what outputs this engine produces"""
        return {
            "component_outputs": [
                {"id": "deltaP", "name": "Pressure Drop", "unit": "bar",
                 "formula": "f × (L/Di) × (ρv²/2)", "category": "performance"},
                {"id": "lifetime", "name": "Expected Life", "unit": "years",
                 "formula": "baseline_life × material_factor × climate_factor",
                 "category": "durability"}
            ],
            "composite_dimensions": [
                {"id": "performance_score", "name": "Performance", 
                 "components": ["deltaP", "efficiency", "velocity"]},
                {"id": "economic_score", "name": "Economics",
                 "components": ["cost_per_m", "total_cost"]},
                {"id": "durability_score", "name": "Durability",
                 "components": ["lifetime", "degradation_rate"]}
            ]
        }
    
    @abstractmethod
    def calculate(self, inputs: Dict) -> EngineResults:
        """Perform calculations and return results"""
        # 1. Validate inputs
        # 2. Perform component calculations
        # 3. Calculate composite scores
        # 4. Normalize to 0-100 scale
        # 5. Return structured results
        return {
            "components": {
                "deltaP": {"value": 0.7, "unit": "bar", "normalized": 70,
                          "formula_used": "f × (L/Di) × (ρv²/2)",
                          "calculation_steps": [
                              "f = 0.024 (from Colebrook-White)",
                              "ρv²/2 = 998 × 1.7² / 2 = 1442 Pa",
                              "ΔP = 0.024 × (25/0.015) × 1442 = 57,680 Pa = 0.58 bar"
                          ]},
                # ... other components
            },
            "composites": {
                "performance_score": 82,
                "economic_score": 71,
                "durability_score": 65
            },
            "overall_score": 76,
            "visualization_point": {"x": 82, "y": 71, "z": 65}
        }
    
    @abstractmethod
    def get_target_profile(self, application: str) -> TargetProfile:
        """Return target/ideal values for given application"""
        return {
            "application": "Industrial Cooling",
            "targets": {
                "performance_score": {"min": 80, "ideal": 90},
                "economic_score": {"min": 70, "ideal": 85},
                "durability_score": {"min": 60, "ideal": 75}
            }
        }
```

---

## ENGINE REGISTRY SYSTEM

### How Engines are Registered and Selected

```python
# backend/engines/registry.py
class EngineRegistry:
    """Central registry for all available engines"""
    
    _engines = {}
    
    @classmethod
    def register(cls, engine_id: str, engine_class: Type[FeasibilityEngine]):
        """Register a new engine"""
        cls._engines[engine_id] = engine_class
    
    @classmethod
    def get_engine(cls, engine_id: str) -> FeasibilityEngine:
        """Get engine instance by ID"""
        if engine_id not in cls._engines:
            raise ValueError(f"Engine '{engine_id}' not found")
        return cls._engines[engine_id]()
    
    @classmethod
    def list_engines(cls) -> List[Dict]:
        """List all available engines"""
        return [
            engine().get_metadata() 
            for engine in cls._engines.values()
        ]

# Register engines
EngineRegistry.register("hose_optimization", HoseOptimizationEngine)
EngineRegistry.register("solar_panel", SolarPanelEngine)  # Future
EngineRegistry.register("hvac_sizing", HVACSizingEngine)   # Future
```

---

## EXAMPLE: Hose Optimization Engine Implementation

```python
# backend/engines/hose_optimization_engine.py
class HoseOptimizationEngine(FeasibilityEngine):
    
    def calculate(self, inputs: Dict) -> EngineResults:
        """Hose-specific calculations"""
        
        # Extract inputs
        Di = inputs["geometry"]["Di"] / 1000  # mm to m
        L = inputs["geometry"]["L"]
        material = inputs["material"]["material_type"]
        P_in = inputs["operating"]["P_in"]
        Q = inputs["operating"]["Q"] / 60000  # L/min to m³/s
        
        # Component calculations with detailed tracking
        results = {"components": {}, "composites": {}}
        
        # 1. Flow velocity
        A = np.pi * (Di/2)**2
        v = Q / A
        results["components"]["velocity"] = {
            "value": v,
            "unit": "m/s",
            "formula": "v = Q / A = Q / (π × (Di/2)²)",
            "calculation_steps": [
                f"Di = {Di*1000} mm = {Di} m",
                f"A = π × ({Di/2})² = {A:.6f} m²",
                f"Q = {Q*60000} L/min = {Q:.6f} m³/s",
                f"v = {Q:.6f} / {A:.6f} = {v:.2f} m/s"
            ],
            "normalized": self._normalize_velocity(v)
        }
        
        # 2. Reynolds number
        rho = 998  # kg/m³ for water
        mu = 0.001  # Pa·s for water at 20°C
        Re = (rho * v * Di) / mu
        results["components"]["reynolds"] = {
            "value": Re,
            "unit": "-",
            "formula": "Re = (ρ × v × Di) / μ",
            "calculation_steps": [
                f"ρ = {rho} kg/m³ (water at 20°C)",
                f"μ = {mu} Pa·s (water at 20°C)",
                f"Re = ({rho} × {v:.2f} × {Di}) / {mu} = {Re:.0f}"
            ],
            "normalized": self._normalize_reynolds(Re)
        }
        
        # 3. Friction factor (Colebrook-White, iterative)
        roughness = inputs["geometry"]["roughness"] / 1000  # mm to m
        epsilon_over_D = roughness / Di
        f = self._calculate_friction_factor(Re, epsilon_over_D)
        results["components"]["friction_factor"] = {
            "value": f,
            "unit": "-",
            "formula": "1/√f = -2 × log₁₀(ε/(3.7D) + 2.51/(Re√f))",
            "calculation_steps": [
                f"ε = {roughness*1000} mm = {roughness} m",
                f"ε/D = {roughness} / {Di} = {epsilon_over_D:.6f}",
                f"Re = {Re:.0f}",
                "Iterative solution of Colebrook-White equation:",
                f"f = {f:.4f}"
            ],
            "normalized": None  # Not normalized individually
        }
        
        # 4. Pressure drop
        deltaP_friction = f * (L/Di) * (rho * v**2 / 2)
        deltaP_friction_bar = deltaP_friction / 100000  # Pa to bar
        results["components"]["deltaP"] = {
            "value": deltaP_friction_bar,
            "unit": "bar",
            "formula": "ΔP = f × (L/Di) × (ρv²/2)",
            "calculation_steps": [
                f"f = {f:.4f}",
                f"L/Di = {L} / {Di} = {L/Di:.1f}",
                f"ρv²/2 = {rho} × {v:.2f}² / 2 = {rho*v**2/2:.0f} Pa",
                f"ΔP = {f:.4f} × {L/Di:.1f} × {rho*v**2/2:.0f}",
                f"ΔP = {deltaP_friction:.0f} Pa = {deltaP_friction_bar:.2f} bar"
            ],
            "normalized": self._normalize_pressure_drop(deltaP_friction_bar)
        }
        
        # 5. Pressure efficiency
        P_out = P_in - deltaP_friction_bar
        eta_P = (P_out / P_in) * 100
        results["components"]["efficiency"] = {
            "value": eta_P,
            "unit": "%",
            "formula": "η_P = (P_out / P_in) × 100%",
            "calculation_steps": [
                f"P_in = {P_in} bar",
                f"ΔP = {deltaP_friction_bar:.2f} bar",
                f"P_out = {P_in} - {deltaP_friction_bar:.2f} = {P_out:.2f} bar",
                f"η_P = ({P_out:.2f} / {P_in}) × 100 = {eta_P:.1f}%"
            ],
            "normalized": eta_P  # Already 0-100
        }
        
        # ... continue with cost, lifetime, etc.
        
        # Calculate composite scores
        results["composites"]["performance_score"] = self._calc_performance_score(
            results["components"]
        )
        results["composites"]["economic_score"] = self._calc_economic_score(
            results["components"]
        )
        results["composites"]["durability_score"] = self._calc_durability_score(
            results["components"]
        )
        
        # Overall score
        results["overall_score"] = (
            results["composites"]["performance_score"] * 0.4 +
            results["composites"]["economic_score"] * 0.3 +
            results["composites"]["durability_score"] * 0.3
        )
        
        # Visualization coordinates
        results["visualization_point"] = {
            "x": results["composites"]["performance_score"],
            "y": results["composites"]["economic_score"],
            "z": results["composites"]["durability_score"],
            "color": self._score_to_color(results["overall_score"]),
            "size": 10  # Could vary based on confidence
        }
        
        return results
```

---

## FRONTEND: DYNAMIC UI BASED ON SELECTED ENGINE

### Engine Selector Component

```typescript
// Frontend: EngineSelector.tsx
const EngineSelector = () => {
  const [engines, setEngines] = useState([]);
  const [selectedEngine, setSelectedEngine] = useState(null);
  
  useEffect(() => {
    // Fetch available engines
    fetch('/api/engines/list')
      .then(res => res.json())
      .then(data => setEngines(data));
  }, []);
  
  const handleEngineChange = (engineId) => {
    // Load engine configuration
    fetch(`/api/engines/${engineId}/schema`)
      .then(res => res.json())
      .then(schema => {
        setSelectedEngine({
          id: engineId,
          inputSchema: schema.inputs,
          outputSchema: schema.outputs
        });
      });
  };
  
  return (
    <Select onChange={handleEngineChange}>
      {engines.map(engine => (
        <MenuItem value={engine.id}>
          {engine.name} - {engine.description}
        </MenuItem>
      ))}
    </Select>
  );
};
```

### Dynamic Control Panel

```typescript
// DynamicControlPanel.tsx
const DynamicControlPanel = ({ inputSchema }) => {
  const [inputs, setInputs] = useState({});
  
  const renderControl = (input) => {
    switch (input.type) {
      case 'slider':
        return (
          <SliderControl
            label={input.name}
            unit={input.unit}
            min={input.range[0]}
            max={input.range[1]}
            value={inputs[input.id] || input.default}
            onChange={(val) => setInputs({...inputs, [input.id]: val})}
          />
        );
      
      case 'dropdown':
        return (
          <DropdownControl
            label={input.name}
            options={input.options}
            value={inputs[input.id] || input.options[0]}
            onChange={(val) => setInputs({...inputs, [input.id]: val})}
          />
        );
      
      // ... other control types
    }
  };
  
  return (
    <Box>
      {Object.entries(inputSchema).map(([category, controls]) => (
        <Section title={category}>
          {controls.map(renderControl)}
        </Section>
      ))}
    </Box>
  );
};
```

---

## 3D VISUALIZATION WITH COMPREHENSIVE TOOLTIPS

### Response Surface with Interactive Points

```typescript
// ResponseSurface3D.tsx
const ResponseSurface3D = ({ results, outputSchema }) => {
  const { x, y, z, color } = results.visualization_point;
  
  return (
    <Canvas>
      {/* Axes */}
      <Axes
        xLabel={outputSchema.composites[0].name}
        yLabel={outputSchema.composites[1].name}
        zLabel={outputSchema.composites[2].name}
      />
      
      {/* Current configuration point */}
      <Sphere
        position={[x, y, z]}
        color={color}
        onPointerOver={() => setTooltipVisible(true)}
        onPointerOut={() => setTooltipVisible(false)}
      >
        {tooltipVisible && (
          <Html>
            <TooltipCard>
              <h3>Current Configuration</h3>
              <ScoreDisplay score={results.overall_score} />
              
              <Divider />
              
              <h4>Component Outputs</h4>
              {Object.entries(results.components).map(([key, data]) => (
                <ComponentDetail
                  name={data.name}
                  value={data.value}
                  unit={data.unit}
                  formula={data.formula}
                  steps={data.calculation_steps}
                />
              ))}
              
              <Divider />
              
              <h4>Composite Scores</h4>
              <BarChart>
                {Object.entries(results.composites).map(([dim, score]) => (
                  <Bar label={dim} value={score} />
                ))}
              </BarChart>
            </TooltipCard>
          </Html>
        )}
      </Sphere>
      
      {/* Target profile indicator */}
      {targetProfile && (
        <Sphere
          position={[
            targetProfile.performance_score.ideal,
            targetProfile.economic_score.ideal,
            targetProfile.durability_score.ideal
          ]}
          color="gold"
          opacity={0.5}
        />
      )}
      
      {/* Optional: Response surface mesh */}
      {showSurface && (
        <ResponseSurfaceMesh
          engine={selectedEngine}
          inputRanges={inputSchema}
        />
      )}
    </Canvas>
  );
};
```

### Tooltip Card Component

```typescript
// ComponentDetail.tsx
const ComponentDetail = ({ name, value, unit, formula, steps }) => {
  const [expanded, setExpanded] = useState(false);
  
  return (
    <Card onClick={() => setExpanded(!expanded)}>
      <CardHeader>
        <strong>{name}:</strong> {value} {unit}
      </CardHeader>
      
      {expanded && (
        <CardContent>
          <Box>
            <strong>Formula:</strong>
            <MathDisplay formula={formula} />
          </Box>
          
          <Box>
            <strong>Calculation:</strong>
            <ol>
              {steps.map(step => (
                <li><code>{step}</code></li>
              ))}
            </ol>
          </Box>
        </CardContent>
      )}
    </Card>
  );
};
```

---

## API ENDPOINTS

### Engine Management

```
GET  /api/engines/list
→ Returns all available engines

GET  /api/engines/{engine_id}/schema
→ Returns input and output schema for engine

POST /api/engines/{engine_id}/calculate
Body: { inputs: {...} }
→ Performs calculation, returns results with formulas
```

---

## ADDING A NEW ENGINE (Future Example)

```python
# backend/engines/solar_panel_engine.py
class SolarPanelEngine(FeasibilityEngine):
    
    def get_metadata(self):
        return {
            "id": "solar_panel",
            "name": "Solar Panel Sizing",
            "description": "Optimize solar panel configuration for energy/cost"
        }
    
    def get_input_schema(self):
        return {
            "location": [
                {"id": "latitude", "type": "slider", "range": [-90, 90]},
                {"id": "avg_sunlight", "type": "slider", "unit": "hours/day"}
            ],
            "panel": [
                {"id": "panel_type", "type": "dropdown",
                 "options": ["Monocrystalline", "Polycrystalline", "Thin-film"]},
                {"id": "panel_area", "type": "slider", "unit": "m²"}
            ],
            "usage": [
                {"id": "daily_consumption", "type": "slider", "unit": "kWh/day"}
            ]
        }
    
    def calculate(self, inputs):
        # Solar-specific calculations
        # Returns same structure as hose engine
        pass

# Register it
EngineRegistry.register("solar_panel", SolarPanelEngine)
```

**That's it!** The frontend automatically:
- Shows new engine in selector
- Adapts control panel to new inputs
- Displays results in 3D visualization
- Shows tooltips with solar-specific formulas

---

## SUMMARY

**Pluggable Architecture:**
- ✅ Abstract engine interface
- ✅ Engine registry system
- ✅ Dynamic UI generation from schema
- ✅ Generic 3D visualization
- ✅ Comprehensive tooltips with formulas

**To Add a New Use Case:**
1. Create new engine class (implement interface)
2. Register in EngineRegistry
3. Done - UI adapts automatically

**User Experience:**
1. Select engine from dropdown
2. Control panel shows relevant inputs
3. Adjust sliders → calculation updates
4. 3D viz shows position in response surface
5. Hover/click for detailed tooltips with formulas
6. Move towards optimal region

Does this pluggable architecture match your vision?
