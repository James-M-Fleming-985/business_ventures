# PROJECT-001: Energy Efficiency Feasibility Platform

## Overview
Generic feasibility analysis platform with pluggable mathematical engines for evaluating energy efficiency opportunities across multiple domains (hose optimization, solar panels, HVAC systems, etc.).

## Project Structure

```
PROJECT-001 ENERGY EFFICIENCY/
├── PROJECT-001_energy_efficiency.yaml          # Project-level requirements
│
├── SYSTEM-001 FEASIBILITY PLATFORM/
│   ├── SYSTEM-001_feasibility_platform.yaml   # System-level requirements
│   │
│   └── FEATURE-001 Interactive Feasibility Tool/
│       ├── FEATURE-001_interactive_feasibility_tool.yaml  # Feature requirements
│       │
│       ├── LAYER-001 Engine Framework/
│       │   └── REQ-001.yaml                   # Engine interface, registry, hose engine
│       │
│       ├── LAYER-002 Material Database/
│       │   └── REQ-002.yaml                   # Material properties, climate zones, costs
│       │
│       ├── LAYER-003 Optimization Engine/
│       │   └── REQ-003.yaml                   # Normalization, composite scores
│       │
│       ├── LAYER-004 API Backend/
│       │   └── REQ-004.yaml                   # FastAPI REST endpoints
│       │
│       └── LAYER-005 3D Visualization Frontend/
│           └── REQ-005.yaml                   # React + Three.js 3D viz
```

## Key Features

### Pluggable Engine Architecture
- Abstract `FeasibilityEngine` base class
- `EngineRegistry` for dynamic engine discovery
- `HoseOptimizationEngine` as reference implementation
- New engines can be added without modifying API or frontend code

### 3D Response Surface Visualization
- Performance Score (X axis)
- Economic Score (Y axis)  
- Durability Score (Z axis)
- Normalized to 0-100 scale for cross-domain comparison

### Calculation Transparency
- Every output includes formula (LaTeX notation)
- Step-by-step calculation breakdown
- Normalized scores shown alongside raw values

### Dynamic UI Generation
- Control panel generated from engine's input schema
- No hardcoded forms - fully adaptive to engine parameters
- Engine selector dropdown auto-populated from registry

## Technology Stack

### Backend
- **Framework:** FastAPI 0.104.0
- **ORM:** SQLAlchemy 2.0
- **Database:** PostgreSQL 15
- **Computation:** numpy, scipy, pandas
- **Optimization:** pygmo (multi-objective)

### Frontend
- **Framework:** React 18 + TypeScript 5
- **Bundler:** Vite 5
- **3D Library:** React-Three-Fiber + Three.js
- **UI Components:** Material-UI 5
- **State Management:** React Query + Zustand

### Deployment
- **Platform:** Railway
- **Services:** Backend API + Frontend Dashboard
- **Cost:** ~$20/month (Phase 1)

## Getting Started with AI Code Generator

### Prerequisites
1. Control Tower repository with `build_feature.py`
2. OpenAI API key or Anthropic API key

### Generate Code

```bash
# Navigate to control tower
cd /workspaces/control_tower

# Generate complete feature implementation
python build_feature.py /workspaces/business_ventures/projects/PROJECT-001\ ENERGY\ EFFICIENCY/SYSTEM-001\ FEASIBILITY\ PLATFORM/FEATURE-001\ Interactive\ Feasibility\ Tool/FEATURE-001_interactive_feasibility_tool.yaml

# The AI will:
# 1. Read all layer requirements (REQ-001 through REQ-005)
# 2. Generate RED phase tests for each layer
# 3. Generate GREEN phase implementations
# 4. Run tests and verify quality gates
# 5. Generate verification reports
```

### Estimated Generation Time
- **Total:** 3-5 hours (with AI code generator)
- **Manual:** 5-8 days (without AI)
- **Cost:** ~$0.50-$2.00 in API tokens

## Architecture Highlights

### Engine Interface Contract
```python
class FeasibilityEngine(ABC):
    @abstractmethod
    def get_metadata() -> EngineMetadata
    
    @abstractmethod
    def get_input_schema() -> Dict[str, ParameterSchema]
    
    @abstractmethod
    def get_output_schema() -> Dict[str, OutputSchema]
    
    @abstractmethod
    def calculate(inputs: Dict[str, Any]) -> CalculationResult
    
    @abstractmethod
    def get_target_profile(profile_name: str) -> Dict[str, Any]
```

### Calculation Result Structure
```python
{
  "components": {
    "deltaP": {
      "value": 0.7,
      "unit": "bar",
      "formula": "ΔP = f × (L/Di) × (ρv²/2)",
      "calculation_steps": [
        "f = 0.024 (from Colebrook-White)",
        "ρv²/2 = 998 × 1.7² / 2 = 1442 Pa",
        "ΔP = 0.024 × (25/0.015) × 1442 = 57,680 Pa = 0.577 bar"
      ],
      "normalized": 70
    }
  },
  "composites": {
    "performance_score": 75,
    "economic_score": 82,
    "durability_score": 68
  },
  "visualization_point": {"x": 75, "y": 82, "z": 68},
  "overall_score": 75.5
}
```

### API Endpoints
- `GET /api/engines` - List all available engines
- `GET /api/engines/{id}/input-schema` - Get input parameters
- `GET /api/engines/{id}/output-schema` - Get output metrics  
- `POST /api/engines/{id}/calculate` - Perform calculation
- `GET /api/engines/{id}/target-profiles` - Get optimal configurations

## Testing Strategy

### Coverage Targets
- **Unit Tests:** 85%
- **Integration Tests:** 75%
- **E2E Tests:** 70%

### Test Pyramid
```
      /\
     /E2E\      8 tests   (complete workflows)
    /------\
   /  INT   \   20 tests  (API + DB integration)
  /----------\
 /   UNIT     \ 40 tests  (calculations, normalization)
/--------------\
```

## Quality Gates

### Performance
- Calculation latency: <100ms
- 3D rendering: 60 FPS minimum
- API response time: <200ms (p95)

### Reliability  
- Calculation accuracy: ±1% vs manual
- Uptime: 99% (Phase 1)

### Maintainability
- Code coverage: 85% unit, 75% integration
- 100% API documentation
- Engine addition time: <4 hours

## Next Steps

1. **Run AI Code Generator** (3-5 hours)
   - Generates all 5 layers with tests
   - Verifies quality gates
   - Creates traceability reports

2. **Manual Verification** (1-2 hours)
   - Review generated code
   - Test in browser
   - Verify calculations against spreadsheet

3. **Deployment** (1 hour)
   - Deploy backend to Railway
   - Deploy frontend to Railway
   - Configure database
   - Seed material data

4. **User Testing** (ongoing)
   - Gather feedback
   - Iterate on UI/UX
   - Add more engines

## Adding New Engines

To add a new feasibility domain (e.g., solar panels):

1. Create class inheriting from `FeasibilityEngine`
2. Implement required methods (get_metadata, get_input_schema, etc.)
3. Register engine: `EngineRegistry().register(SolarPanelEngine())`
4. **No changes needed to API or frontend!**

## Related Documents

- `/energy_savings/VARIABLE_INVENTORY.md` - Comprehensive variable catalog
- `/energy_savings/PLUGGABLE_ENGINE_ARCHITECTURE.md` - Architecture deep-dive
- `/energy_savings/DASHBOARD_MOCKUP.md` - UI/UX design
- `/energy_savings/IMPLEMENTATION_STRATEGY_EVALUATION.md` - AI vs manual analysis

## Success Metrics

### MVP Success
- ✅ Hose optimization engine working end-to-end
- ✅ 3D visualization rendering at 60 FPS
- ✅ Tooltips displaying formulas
- ✅ Real-time calculation updates

### Production Success  
- 3+ engines available
- 95%+ calculation accuracy
- Sub-100ms latency
- Positive user feedback

### Stretch Goals
- 10+ engines
- Export to Excel/PDF
- Multi-user collaboration
- Historical tracking

---

**Created:** 2025-12-29  
**Status:** Ready for AI Code Generation  
**Estimated Completion:** 3-5 hours with AI generator
