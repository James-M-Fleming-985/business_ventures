# Feasibility Platform Implementation Plan
**Date:** December 30, 2025  
**Project:** Generic Feasibility Analysis Platform with First-Class 3D Visualizations

---

## Executive Summary

The Feasibility Platform is a **generic, engine-agnostic** system for multi-objective optimization across any domain. It consists of:

1. **Pluggable Mathematical Engines** - Domain-specific calculation engines (hose optimization, solar, HVAC, etc.)
2. **Engine Selection Interface** - UI for selecting and configuring engines
3. **First-Class 3D Visualizations** - 8 engine-agnostic visualization modes for exploring optimization spaces

**Core Principle:** Any engine that produces a `CalculationResult` can leverage ALL 8 visualization modes without modification.

---

## System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 0: ENGINE REGISTRY & SELECTION                           │
│  ─────────────────────────────────────────────────────────────  │
│  • Engine Selection Page/Tab                                    │
│  • List all registered engines dynamically                      │
│  • Architect can add new engines as use cases arise             │
│  • User selects engine → loads dynamic parameter panel          │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 1: SELECTED ENGINE (Domain-Specific)                     │
│  ─────────────────────────────────────────────────────────────  │
│  • Example: HoseOptimizationEngine                              │
│  • get_input_schema() → generates UI controls dynamically       │
│  • calculate(inputs) → produces CalculationResult               │
│  • Standard output interface shared by ALL engines              │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│  STANDARD INTERFACE: CalculationResult                          │
│  ─────────────────────────────────────────────────────────────  │
│  {                                                               │
│    components: {                                                 │
│      "metric1": {value, unit, formula, steps, normalized}       │
│      "metric2": {...}                                            │
│    },                                                            │
│    composites: {                                                 │
│      performance_score: 85.3,    // 0-100                       │
│      economic_score: 72.1,        // 0-100                      │
│      durability_score: 91.4       // 0-100                      │
│    },                                                            │
│    visualization_point: {x: 85.3, y: 72.1, z: 91.4},            │
│    overall_score: 83.2                                           │
│  }                                                               │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 2: VISUALIZATION MODE SELECTOR                           │
│  ─────────────────────────────────────────────────────────────  │
│  • Dropdown/Tab switcher for visualization modes                │
│  • Engine-agnostic - works with ANY CalculationResult           │
│  • Manages state, history tracking, performance monitoring      │
│  • Routes data to selected visualization component              │
└─────────────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────────────┐
│  LAYER 3: FIRST-CLASS 3D VISUALIZATIONS (8 Modes)               │
│  ─────────────────────────────────────────────────────────────  │
│  ALL modes consume CalculationResult interface:                 │
│                                                                  │
│  1. Ternary Diagram - Barycentric coords for 3-score balance    │
│  2. Feasibility Volume - 3D morphing surface with constraints   │
│  3. Parallel Coordinates - All inputs/outputs on vertical axes  │
│  4. Response Surface - 2-variable interaction surface           │
│  5. Sensitivity Analysis - Tornado chart of input impacts       │
│  6. Correlation Matrix - 3D heatmap of relationships            │
│  7. Pareto Frontier - Non-dominated solutions boundary          │
│  8. Radar Chart - Multi-dimensional spider chart                │
└─────────────────────────────────────────────────────────────────┘
```

---

## Current Implementation Status

### ✅ COMPLETED

#### Backend Framework
- **File:** `/backend/app/engines/base.py`
- **Status:** COMPLETE
- **Components:**
  - `FeasibilityEngine` abstract base class
  - `EngineRegistry` singleton for engine management
  - `CalculationResult` standard interface
  - `HoseOptimizationEngine` reference implementation

#### Backend API
- **File:** `/backend/app/main.py`
- **Status:** COMPLETE
- **Endpoints:**
  - `GET /api/engines` - List all registered engines
  - `GET /api/engines/{engine_id}/input-schema` - Get parameter schema
  - `POST /api/engines/{engine_id}/calculate` - Execute calculation
  - `GET /api/engines/{engine_id}/target-profiles` - Get optimal configs

#### Hose Optimization Engine (Reference Implementation)
- **File:** `/backend/app/engines/calculations.py`
- **Status:** COMPLETE
- **Features:**
  - 13 input parameters (material, geometry, flow, environment, economics)
  - Comprehensive hydraulic calculations (Darcy-Weisbach, Reynolds, etc.)
  - Material properties database
  - 3 composite scores (performance, durability, economic)
  - Overall optimization score

#### FEATURE-001: Basic Frontend
- **File:** `/frontend/src/App.tsx`
- **Status:** FUNCTIONAL
- **Features:**
  - Engine parameter controls (sliders, dropdowns)
  - Real-time calculation updates
  - Basic triangle visualization (performance/durability/economic)
  - Tooltip system with formulas

### ⚠️ PARTIAL COMPLETION

#### FEATURE-002: Advanced 3D Visualizations
- **Location:** `/SYSTEM-001 FEASIBILITY PLATFORM/FEATURE-002 Advanced 3D Visualizations/`
- **Status:** LAYERS BUILT, NOT INTEGRATED

**What Exists:**
- 10 layer folders with implementations
- Layer requirement specifications (YAML files)
- Unit tests for each layer
- Build logs and verification reports

**The Problem:**
- Implementations are generic placeholders, NOT connected to CalculationResult
- Layer 10 (Integration) is a transform control demo, NOT a visualization switcher
- No actual integration with backend API
- Visualizations don't consume real engine data

---

## Work Required

### Phase 1: Engine Selection UI (NEW)
**Estimated Time:** 2 days

#### Tasks:
1. **Create Engine Selection Page/Component**
   - Display list of engines from `GET /api/engines`
   - Show engine metadata (name, description, domain)
   - Click to select engine → load its parameter panel

2. **Update App.tsx Navigation**
   - Add tab/page for engine selection
   - Route to selected engine's interface

3. **Dynamic Parameter Panel**
   - Already exists in current App.tsx
   - Ensure it works with ANY engine's input schema

**Deliverable:** Users can select from multiple engines (currently just Hose, but ready for more)

---

### Phase 2: Rewrite Layer 10 (Integration Layer)
**Estimated Time:** 3 days

#### Current Implementation Issues:
- File: `LAYER_001_002_010_Integration_Layer/src/implementation.tsx`
- Implements generic transform controls (position/rotation/scale)
- No connection to CalculationResult
- No visualization mode switching

#### Required Implementation:

```typescript
// New interface for Layer 10
interface VisualizationModeSelectorProps {
  calculationResult: CalculationResult | null;
  inputs: Record<string, any>;
  parameterSchema: ParameterSchema[];
  explorationHistory: CalculationResult[];
}

// Main component
const VisualizationModeSelector: React.FC<VisualizationModeSelectorProps> = ({
  calculationResult,
  inputs,
  parameterSchema,
  explorationHistory
}) => {
  const [mode, setMode] = useState<VisualizationMode>('ternary');
  
  return (
    <>
      {/* Mode selector dropdown */}
      <Select value={mode} onChange={(e) => setMode(e.target.value)}>
        <MenuItem value="ternary">Ternary Diagram</MenuItem>
        <MenuItem value="feasibility">Feasibility Volume</MenuItem>
        <MenuItem value="parallel">Parallel Coordinates</MenuItem>
        <MenuItem value="response">Response Surface</MenuItem>
        <MenuItem value="sensitivity">Sensitivity Analysis</MenuItem>
        <MenuItem value="correlation">Correlation Matrix</MenuItem>
        <MenuItem value="pareto">Pareto Frontier</MenuItem>
        <MenuItem value="radar">Radar Chart</MenuItem>
      </Select>
      
      {/* Render selected visualization */}
      {mode === 'ternary' && <TernaryDiagram {...props} />}
      {mode === 'feasibility' && <FeasibilityVolume {...props} />}
      {/* etc... */}
    </>
  );
};
```

**Key Features:**
- Dropdown for mode selection (<200ms switching)
- State management (Zustand store)
- History tracking (last 100 configurations)
- Performance monitoring (60 FPS target)
- Props validation and routing to correct visualization

---

### Phase 3: Rewrite Layers 2-9 (Visualization Components)
**Estimated Time:** 10-12 days (1.5 days per component)

All 8 visualization components need complete rewrites to:

#### Common Requirements for ALL Components:

1. **Accept Standard Props:**
```typescript
interface VisualizationProps {
  calculationResult: CalculationResult | null;
  inputs: Record<string, any>;
  parameterSchema: ParameterSchema[];
  explorationHistory: CalculationResult[];
  onParameterHighlight?: (paramName: string) => void;
}
```

2. **Use CalculationResult Data:**
   - Extract `composites.performance_score`, `composites.economic_score`, `composites.durability_score`
   - Use `components` for detailed metric visualization
   - Use `visualization_point` for positioning
   - Use `overall_score` for color mapping

3. **Engine-Agnostic Implementation:**
   - No hardcoded parameter names (use `parameterSchema` instead)
   - Dynamic axis labels from schema
   - Work with ANY engine's output

4. **Performance Requirements:**
   - 60 FPS during interactions
   - <5ms update latency
   - React.memo, useMemo, useCallback optimizations

#### Component-Specific Details:

**Layer 2: Ternary Diagram Component**
- Equilateral triangle for 3-score balance
- Current point as glowing sphere
- Trail of last 20 configurations
- Iso-composition grid lines

**Layer 3: Feasibility Volume Component**
- Morphing 3D surface based on constraints
- Gradient vectors showing improvement direction
- Viridis color scale

**Layer 4: Parallel Coordinates Component**
- Vertical axes for ALL inputs + 3 composite outputs
- Polylines connecting parameter values
- Normalization using schema min/max
- Brushing for filtering

**Layer 5: Response Surface Component**
- User selects 2 input parameters
- 3D surface: Z-axis = overall_score
- Contour lines on XY plane
- Current point highlighted

**Layer 6: Sensitivity Analysis Component**
- 3D tornado chart
- Bar length = ∂(overall_score)/∂(input_i)
- Sorted by impact magnitude
- Green/red for positive/negative impact

**Layer 7: Correlation Matrix Component**
- 3D heatmap grid
- Pearson correlation from history (last 100)
- Cube height = |correlation|
- Color intensity = correlation strength

**Layer 8: Pareto Frontier Component**
- Sample N random configurations
- Extract non-dominated solutions
- 3D convex hull
- Current point relative to frontier

**Layer 9: Radar Chart Component**
- Radial axes for all inputs
- Filled polygon showing current config
- Reference config overlay
- Concentric circles at 25/50/75/100%

---

### Phase 4: Integration & Testing
**Estimated Time:** 3-4 days

#### Integration Tests:
- Feature-level integration: `tests/integration/test_integration.py`
- Verify all 8 modes work with CalculationResult
- Test mode switching performance
- History tracking validation

#### E2E Tests:
- End-to-end flow: `tests/e2e/test_e2e.py`
- User selects engine → adjusts parameters → switches viz modes
- Performance benchmarks (60 FPS, <5ms latency)

#### Frontend Integration:
- Import Layer 10 into App.tsx
- Add visualization mode selector to UI
- Connect to existing backend API

---

## Implementation Priority

### Sprint 1 (Week 1): Foundation
1. ✅ Review current implementation status
2. Create Engine Selection UI component
3. Rewrite Layer 10 (Integration/Mode Selector)
4. Update App.tsx to include mode selector

### Sprint 2 (Week 2): Core Visualizations
5. Rewrite Layer 2 (Ternary Diagram)
6. Rewrite Layer 4 (Parallel Coordinates)
7. Rewrite Layer 6 (Sensitivity Analysis)
8. Integration testing for completed modes

### Sprint 3 (Week 3): Advanced Visualizations
9. Rewrite Layer 3 (Feasibility Volume)
10. Rewrite Layer 5 (Response Surface)
11. Rewrite Layer 7 (Correlation Matrix)

### Sprint 4 (Week 4): Optimization Visualizations
12. Rewrite Layer 8 (Pareto Frontier)
13. Rewrite Layer 9 (Radar Chart)
14. Full E2E testing
15. Performance optimization

---

## Technical Specifications

### Standard Interfaces

#### CalculationResult (Backend Output)
```python
class CalculationResult(BaseModel):
    components: Dict[str, ComponentResult]      # Detailed metrics
    composites: Dict[str, float]                # performance_score, economic_score, durability_score
    visualization_point: Dict[str, float]       # {x, y, z} for 3D plotting
    overall_score: float                        # 0-100 optimization score
    metadata: Dict[str, Any]                    # calculation_time_ms, timestamp, etc.
```

#### VisualizationProps (Frontend Input)
```typescript
interface VisualizationProps {
  calculationResult: CalculationResult | null;
  inputs: Record<string, any>;
  parameterSchema: ParameterSchema[];
  explorationHistory: CalculationResult[];
  onParameterHighlight?: (paramName: string) => void;
}
```

### Technology Stack

**Backend:**
- Python 3.11
- FastAPI
- Pydantic (data validation)
- NumPy/SciPy (calculations)

**Frontend:**
- React 18.2.0
- TypeScript 5.0+ (strict mode)
- Three.js + @react-three/fiber
- Material-UI 5.x
- Zustand (state management)

**Performance Targets:**
- 60 FPS during interactions
- <5ms update latency
- <200ms mode switching
- Support 100 history entries

---

## Engine Extension Guide

### How to Add a New Engine

1. **Create Engine Class:**
```python
class MyNewEngine(FeasibilityEngine):
    def get_metadata(self) -> EngineMetadata:
        return EngineMetadata(
            engine_id="my_new_engine",
            name="My New Engine",
            description="...",
            version="1.0.0",
            domain="..."
        )
    
    def get_input_schema(self) -> Dict[str, ParameterSchema]:
        return {
            "param1": ParameterSchema(...),
            # Define all input parameters
        }
    
    def calculate(self, inputs: Dict[str, Any]) -> CalculationResult:
        # Perform domain-specific calculations
        # MUST return CalculationResult with:
        # - components (detailed metrics)
        # - composites (3 scores: performance, economic, durability)
        # - visualization_point
        # - overall_score
        return CalculationResult(...)
```

2. **Register Engine:**
```python
# In backend/app/engines/base.py or separate module
def initialize_engines():
    registry = EngineRegistry()
    registry.register(HoseOptimizationEngine())
    registry.register(MyNewEngine())  # Add new engine
    return registry
```

3. **No Frontend Changes Required:**
   - Parameter panel auto-generates from input_schema
   - All 8 visualizations automatically work
   - CalculationResult is the only contract

---

## Success Metrics

### Functionality
- [ ] User can select from multiple engines
- [ ] User can switch between 8 visualization modes
- [ ] All modes work with ANY engine
- [ ] Real-time updates during parameter adjustments

### Performance
- [ ] Maintain 60 FPS during slider interactions
- [ ] Mode switching completes in <200ms
- [ ] Update latency <5ms from onChange to render

### Extensibility
- [ ] New engine added in <2 hours (no frontend changes)
- [ ] All visualizations work immediately with new engine
- [ ] Zero coupling between engines and visualizations

### Quality
- [ ] TypeScript strict mode compliance
- [ ] 90%+ test coverage
- [ ] No console errors or warnings
- [ ] Accessible (colorblind-friendly palettes)

---

## Risk Mitigation

### Technical Risks

**Risk:** Performance degradation with complex visualizations  
**Mitigation:** 
- Use React.memo, useMemo, useCallback aggressively
- Implement progressive quality reduction
- Monitor FPS in real-time

**Risk:** Tight coupling between engines and visualizations  
**Mitigation:**
- Enforce CalculationResult interface strictly
- Write integration tests that swap engines
- Documentation emphasizes interface contract

**Risk:** Visualization components become engine-specific  
**Mitigation:**
- Code review checklist: "Does this use CalculationResult only?"
- No hardcoded parameter names
- Use parameterSchema for ALL dynamic content

### Project Risks

**Risk:** Scope creep - adding features beyond 8 visualizations  
**Mitigation:**
- Freeze feature set until all 8 modes complete
- Document future enhancements separately

**Risk:** Inconsistent visualization behavior across modes  
**Mitigation:**
- Shared utilities in Layer 1 (Visualization Framework)
- Common testing harness
- Style guide for visual consistency

---

## Future Enhancements (Post-MVP)

1. **Export Capabilities**
   - Export current visualization as PNG/SVG
   - Export history data as CSV/JSON
   - Generate report PDF

2. **Comparison Mode**
   - Side-by-side engine comparison
   - Overlay multiple configurations
   - Diff highlighting

3. **Optimization Wizard**
   - Guided parameter tuning
   - Auto-suggest improvements
   - Multi-objective optimization solver

4. **Collaborative Features**
   - Share configurations via URL
   - Save/load workspaces
   - Team annotations

5. **Additional Engines**
   - Solar panel optimization
   - HVAC system efficiency
   - Chemical process optimization
   - Financial portfolio analysis

---

## Appendix: File Structure

```
feasibility_tool/
├── backend/
│   ├── app/
│   │   ├── engines/
│   │   │   ├── base.py              ✅ Engine framework
│   │   │   └── calculations.py      ✅ Hose engine
│   │   └── main.py                  ✅ API endpoints
│   └── requirements.txt
│
├── frontend/
│   └── src/
│       ├── App.tsx                  ✅ Main app (basic viz)
│       ├── components/              ⚠️ Needs engine selector
│       └── store/                   ⚠️ Needs viz state management
│
└── SYSTEM-001 FEASIBILITY PLATFORM/
    ├── FEATURE-001 Interactive Feasibility Tool/
    │   ├── LAYER_001_Engine_Framework/           ✅ Complete
    │   ├── LAYER_002_Material_Database/          ✅ Complete
    │   └── ... (other layers)                    ✅ Complete
    │
    └── FEATURE-002 Advanced 3D Visualizations/
        ├── LAYER_001_002_001_Visualization_Framework/
        │   └── src/implementation.tsx            ⚠️ Generic placeholder
        ├── LAYER_001_002_002_Ternary_Diagram_Component/
        │   └── src/implementation.tsx            ❌ Needs rewrite
        ├── ... (Layers 3-9)                      ❌ Need rewrite
        └── LAYER_001_002_010_Integration_Layer/
            └── src/implementation.tsx            ❌ Needs complete rewrite
```

**Legend:**
- ✅ Complete and functional
- ⚠️ Partial or needs update
- ❌ Needs complete rewrite

---

## Contact & Ownership

**Project Owner:** [Your Name]  
**Architecture Lead:** [AI Assistant]  
**Start Date:** December 30, 2025  
**Target Completion:** January 27, 2026 (4 weeks)

---

*End of Implementation Plan*
