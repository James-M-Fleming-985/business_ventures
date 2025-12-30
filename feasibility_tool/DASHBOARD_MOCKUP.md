# Hose Feasibility Tool - Dashboard Mockup

**Date:** December 29, 2025  
**Purpose:** Visual representation of the interactive dashboard layout

---

## Dashboard Layout Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│  HOSE OPTIMIZATION FEASIBILITY TOOL                          [Export] [Help] │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  ┌─────────────────────────────────┐  ┌─────────────────────────────────┐  │
│  │                                 │  │                                 │  │
│  │                                 │  │    PERFORMANCE METRICS          │  │
│  │         3D HOSE MODEL           │  │                                 │  │
│  │                                 │  │  ⚡ Pressure Drop: 0.8 bar     │  │
│  │    (Rotatable, Zoomable)        │  │  📊 Efficiency: 87%            │  │
│  │                                 │  │  💧 Flow Velocity: 2.3 m/s     │  │
│  │  Color gradient shows pressure  │  │  🔄 Reynolds Number: 45,200    │  │
│  │  High ━━━━━━━━━━━━━━ Low       │  │                                 │  │
│  │  🔴 ━━━━━━━━━━━━━━ 🔵         │  │  Grade: ⭐⭐⭐⭐ GOOD          │  │
│  │                                 │  │                                 │  │
│  │                                 │  ├─────────────────────────────────┤
│  │                                 │  │    ECONOMIC METRICS             │  │
│  │                                 │  │                                 │  │
│  │                                 │  │  💰 Hose Cost: $127            │  │
│  │                                 │  │  ⚡ Energy Cost/yr: $23        │  │
│  │                                 │  │  📈 Total TCO (5yr): $242      │  │
│  │                                 │  │  💎 ROI vs Baseline: +215%     │  │
│  │                                 │  │  ⏱️  Payback: 1.2 years        │  │
│  │                                 │  │                                 │  │
│  └─────────────────────────────────┘  └─────────────────────────────────┘  │
│                                                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  DESIGN PARAMETERS                                                            │
│                                                                               │
│  Geometry                          Material & Environment                    │
│  ┌──────────────────────────────┐  ┌──────────────────────────────────┐    │
│  │ Inner Diameter: 15 mm        │  │ Material: [Polyurethane ▼]       │    │
│  │ ━━━━━━●━━━━━━━━━ [6-50]     │  │                                  │    │
│  │                              │  │ Climate: [Temperate ▼]           │    │
│  │ Length: 25 m                 │  │                                  │    │
│  │ ━━━━━━●━━━━━━━━━ [1-100]    │  │ Ambient Temp: 20°C               │    │
│  │                              │  │ ━━━━●━━━━━━━━━ [-40 to 50]      │    │
│  │ Roughness: 0.005 mm          │  │                                  │    │
│  │ ━━━●━━━━━━━━━━━ [0.002-0.1] │  │ Electricity Rate: $0.15/kWh      │    │
│  │                              │  │ ━━━━━━●━━━━━━━ [$0.03-0.35]     │    │
│  │ Bends: 2                     │  │                                  │    │
│  │ ━●━━━━━━━━━━━━━ [0-10]      │  └──────────────────────────────────┘    │
│  └──────────────────────────────┘                                            │
│                                                                               │
│  Operating Conditions                                                         │
│  ┌──────────────────────────────┐                                            │
│  │ Inlet Pressure: 3.5 bar      │                                            │
│  │ ━━━━━━━●━━━━━━ [0.5-20]     │                                            │
│  │                              │                                            │
│  │ Flow Rate: 15 L/min          │                                            │
│  │ ━━━━━●━━━━━━━━ [1-200]      │                                            │
│  │                              │                                            │
│  │ Usage: 2000 hrs/year         │                                            │
│  │ ━━━━━━━●━━━━━━ [0-8760]     │                                            │
│  └──────────────────────────────┘                                            │
│                                                                               │
├─────────────────────────────────────────────────────────────────────────────┤
│  COMPARATIVE ANALYSIS                                                         │
│                                                                               │
│  ┌────────────────────────────────────────┐  ┌──────────────────────────┐  │
│  │  COST vs PERFORMANCE COMPARISON        │  │  MATERIAL COMPARISON     │  │
│  │                                        │  │                          │  │
│  │   Performance (η_P %)                 │  │  Material    ROI   Cost  │  │
│  │   100│                                 │  │  ─────────────────────── │  │
│  │      │      ●Optimal                   │  │  ● PU        215%  $127  │  │
│  │   80 │    ●                             │  │  ○ EPDM      198%  $145  │  │
│  │      │  ●     ● Current                 │  │  ○ Rubber    175%  $98   │  │
│  │   60 │●                                 │  │  ○ PVC       120%  $67   │  │
│  │      └──────────────────── TCO ($)     │  │                          │  │
│  │       100    200    300    400         │  │  [Compare Selected]      │  │
│  └────────────────────────────────────────┘  └──────────────────────────┘  │
│                                                                               │
│  ┌──────────────────────────────────────────────────────────────────────┐  │
│  │  PRESSURE PROFILE ALONG HOSE LENGTH                                  │  │
│  │                                                                        │  │
│  │  Pressure                                                              │  │
│  │  (bar)                                                                 │  │
│  │   3.5 ┌─╲                                                              │  │
│  │       │  ╲                                                             │  │
│  │   3.0 │   ╲___                                                         │  │
│  │       │       ╲____                                                    │  │
│  │   2.5 │            ╲_____                                              │  │
│  │       └──────────────────────────────────────── Length (m)            │  │
│  │        0      5      10     15     20     25                           │  │
│  └──────────────────────────────────────────────────────────────────────┘  │
│                                                                               │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## SIMPLIFIED ARCHITECTURE

### Clear Separation of Concerns

**LEFT PANEL: Control Panel (Inputs Only)**
- All user-adjustable variables
- Dropdowns for categorical choices (Material, Climate)
- Sliders for continuous variables (dimensions, pressure, temperature)
- Clean, organized by category
- Updates trigger calculations

**RIGHT PANEL: 3D Model (Outputs Only)**
- Displays calculated results visually
- Results shown as callouts/annotations around the 3D hose
- Color gradient on hose represents pressure drop
- Interactive (rotate, zoom) but mainly for viewing results
- No input controls here

**BACKEND: Mathematical Engine**
- Receives all inputs from control panel
- Performs physics calculations
- Returns all output variables
- Fast (<100ms) for real-time feel

---

## INPUT VARIABLES (Control Panel)

### Categorical Variables (Dropdowns)

| Variable | Options | Notes |
|----------|---------|-------|
| **Material Type** | PVC, NBR Rubber, EPDM, Polyurethane, Silicone, PTFE | Determines properties (density, roughness, cost, temp limits) |
| **Climate Zone** | Hot-Arid, Hot-Humid, Temperate, Cold, High-Altitude, Marine | Affects material degradation, lifetime |
| **Application** | Garden, Industrial Cooling, Irrigation, Chemical Transfer | Optional - sets recommended ranges |

### Continuous Variables (Sliders)

**Geometry:**
- Inner Diameter (Di): 6-50 mm
- Outer Diameter (Do): 10-60 mm (auto-calculated or manual)
- Length (L): 1-100 m
- Surface Roughness (ε): 0.0015-0.15 mm
- Number of Bends: 0-10

**Environment:**
- Ambient Temperature (T_amb): -40 to 50°C
- UV Index: 0-12 (auto-set by climate or manual)

**Operating Conditions:**
- Inlet Pressure (P_in): 0.5-20 bar
- Flow Rate (Q): 1-200 L/min
- Fluid Temperature (T_fluid): 0-100°C
- Fluid Viscosity (μ): 0.0001-0.1 Pa·s (or select fluid type)

**Economic (Optional for now):**
- Electricity Rate: $0.03-0.35/kWh
- Annual Operating Hours: 0-8760 hours

---

## OUTPUT VARIABLES (Displayed on 3D Model)

### Primary Performance Outputs

**Hydraulic Performance:**
- ✅ **Pressure Drop (ΔP)**: Total pressure loss (bar) - MAIN METRIC
- ✅ **Friction Loss**: Pressure lost to friction (bar)
- ✅ **Local Losses**: Pressure lost at bends/fittings (bar)
- ✅ **Outlet Pressure (P_out)**: Pressure at hose exit (bar)
- ✅ **Flow Velocity (v)**: Average flow speed (m/s)
- ✅ **Reynolds Number (Re)**: Flow regime indicator
- ✅ **Pressure Efficiency (η_P)**: P_out/P_in ratio (%)

**Physical Properties:**
- ✅ **Hose Weight**: Total weight (kg)
- ✅ **Weight per Meter**: (kg/m)
- ✅ **Burst Pressure**: Safety limit (bar)
- ✅ **Safety Factor**: Burst/Operating pressure ratio

**Durability:**
- ✅ **Expected Lifetime**: Years based on material + environment
- ✅ **Degradation Rate**: % per year in specified climate
- ✅ **Replacement Frequency**: Cycles or years

**Economic:**
- ✅ **Material Cost**: Cost of raw materials ($)
- ✅ **Cost per Meter**: ($/m)
- ✅ **Total Hose Cost**: ($ for specified length)
- ✅ **Energy Cost (if usage specified)**: Annual pumping cost ($/year)

### How Outputs are Displayed

**VISUAL APPROACH: Target Profile Optimization**

The 3D display shows:
1. Component variables as callouts/annotations
2. Visual progress towards ideal profile
3. Key derived metrics in summary table

**ON the 3D Model:**
1. **Color Gradient**: Pressure distribution with performance indicator
   - Red (inlet, high pressure) → Blue (outlet, low pressure)
   - Smooth interpolation along length
   - Glow effect when near ideal profile

**AROUND the 3D Model (Component Variables as Callouts):**
2. **Direct Calculation Results:**
   ```
                    P_in: 3.5 bar
                         ↓
        ╔════════════════════════════╗
        ║ ΔP: 0.8 bar               ║ ← Callout
        ║                            ║
        ║ 🔴🟠🟡🟢🟢🔵            ║ ← Pressure gradient
        ║                            ║
        ║ Friction: 0.65 bar        ║ ← Callout
        ║ Local: 0.15 bar           ║ ← Callout
        ╚════════════════════════════╝
                         ↓
                  P_out: 2.7 bar
   
        v: 2.3 m/s  ←  Re: 45,200  ←  f: 0.024
   ```

**OVERLAY: Key Metrics Table (Derived from Components)**
3. **Performance Summary with Target Comparison:**
   ```
   ┌─────────────────────────────────────────────────┐
   │ KEY METRICS        Current    Target    Status  │
   │ ─────────────────────────────────────────────── │
   │ Pressure Efficiency  77%      >75%      ✅ GOOD │
   │ Flow Performance     Good      Good      ✅ GOOD │
   │ Expected Life        7.2 yr    >5 yr     ✅ GOOD │
   │ Cost Feasibility     $127      <$150     ✅ GOOD │
   │ ─────────────────────────────────────────────── │
   │ OVERALL SCORE:       87/100              ⭐⭐⭐⭐│
   │ Optimization Level:  NEAR OPTIMAL        🟢     │
   └─────────────────────────────────────────────────┘
   ```

**VISUAL TARGET INDICATOR: Radar Chart or Progress Bars**
4. **How Close to Ideal Profile:**
   ```
   ┌────────────────────────────────┐
   │  OPTIMIZATION RADAR            │
   │                                │
   │         Performance            │
   │              ╱│╲               │
   │             ╱ │ ╲              │
   │            ╱  │  ╲             │
   │    Life   ────●──── Cost       │  ← Current (●)
   │            ╲  │  ╱             │  ← Target  (○)
   │             ╲ │ ╱              │
   │              ╲│╱               │
   │           Efficiency           │
   │                                │
   │  Legend: ● Current  ○ Target   │
   └────────────────────────────────┘
   
   OR simpler progress bars:
   
   ┌────────────────────────────────┐
   │ Performance:  ████████░░  80%  │ ← Close to target
   │ Cost:         █████████░  90%  │ ← Very close
   │ Lifetime:     ███████░░░  70%  │ ← Acceptable
   │ Efficiency:   ████████░░  85%  │ ← Close to target
   └────────────────────────────────┘
   ```

---

## 3D Hose Visualization Details

### What the 3D Model Shows

```
                    Inlet (High Pressure - Red)
                           ↓
        ╔══════════════════════════════════════╗
        ║ 🔴🔴🔴🔴🔴🟠🟠🟠🟠🟡🟡🟡🟢🟢🔵🔵 ║  ← Cylindrical hose
        ╚══════════════════════════════════════╝
                           ↑
                    Outlet (Low Pressure - Blue)

        └──────────────────┬──────────────────┘
                    Pressure Gradient
                    Color-coded surface
```

### Visual Features (NOT Flow Simulation)

**The 3D model displays:**
1. ✅ **Hose geometry** - cylinder with accurate dimensions from sliders
2. ✅ **Pressure gradient** - smooth color gradient from inlet (red/high) to outlet (blue/low)
3. ✅ **Material appearance** - realistic PBR textures (rubber looks like rubber, PU looks like PU)
4. ✅ **Bends/curves** - if user sets bends, hose shape updates
5. ✅ **Visual indicators**:
   - Glow effect if performance is excellent
   - Warning indicators if pressure drop too high
   - Annotations showing key dimensions
6. ✅ **Interactive camera** - orbit, zoom, pan around the hose
7. ✅ **Lighting** - professional studio lighting with shadows

**The 3D model does NOT show:**
- ❌ Fluid particles flowing through
- ❌ CFD simulation
- ❌ Turbulence visualization
- ❌ Real-time fluid dynamics

### Why This Approach?

The **calculated** pressure gradient is visualized as a **static color map** on the hose surface:
- Physics engine calculates: P_in = 3.5 bar → P_out = 2.7 bar
- Visualization maps this linearly along hose length
- Color shader interpolates: Red (3.5 bar) → Blue (2.7 bar)
- Updates instantly when sliders change (<100ms)

---

## Dashboard Sections Explained

### 1. Top Section (Main Visualization)

**Left Panel: 3D Hose Model**
- Real-time 3D rendering using Three.js + React Three Fiber
- Physically-based materials (looks realistic)
- Color gradient represents calculated pressure drop
- Rotatable with mouse/touch
- Professional lighting and shadows

**Right Panel: Live Metrics**
- Updates in real-time as sliders move
- Two sections:
  - **Performance Metrics**: Physics calculations (ΔP, η, velocity, Re)
  - **Economic Metrics**: Cost calculations (TCO, ROI, payback)
- Visual grade indicator (stars/color-coded rating)

### 2. Middle Section (Parameter Controls)

**Slider Groups:**
- **Geometry**: Di, Do, L, roughness, bends
- **Material & Environment**: Material dropdown, climate zone, temperature, electricity cost
- **Operating Conditions**: Pressure, flow rate, annual usage hours

**Behavior:**
- Drag slider → calculations update instantly → 3D model updates → metrics refresh
- All connected in real-time
- Smooth animations on value changes

### 3. Bottom Section (Analysis Tools)

**Charts and Comparisons:**
- **Cost vs Performance Scatter**: Shows design space, optimal region
- **Material Comparison Table**: Quick ROI/cost comparison across materials
- **Pressure Profile Graph**: 2D line chart showing pressure along hose length
- **Climate Comparison**: How same design performs in different regions (optional)

---

## Technical Flow (With Target Optimization)

```
CONTROL PANEL              BACKEND                      3D DISPLAY + METRICS
─────────────              ───────                      ────────────────────

User sets target      →    Store target profile    →    Display target indicators
Application: "Cooling"     {η_P: >80%, ΔP: <1.0...}    
    ↓
User adjusts slider   →    Receive inputs          →    Update visuals
(Di: 15mm → 18mm)          
    ↓                      Calculate Components:         Component Callouts:
State updates              ├─ v = 4Q/(πDi²)             ├─ ΔP: 0.7 bar
(React/Zustand)            ├─ Re = ρvDi/μ               ├─ v: 1.7 m/s
    ↓                      ├─ f = f(Re, ε/Di)           ├─ Re: 42,000
API call (debounced)       ├─ ΔP = f(L/Di)(ρv²/2)       └─ Cost: $153
    ↓                      ├─ Weight, Cost
Send inputs + targets      └─ Lifetime                  Derived Metrics Table:
    ↓                          ↓                         ┌─────────────────┐
Backend receives           Derive Key Metrics:          │ η_P: 84% ✅     │
{                          ├─ η_P = P_out/P_in          │ ΔP: 0.7 bar ✅  │
  Di: 18,                  ├─ Flow grade                │ Life: 6.5yr ✅  │
  material: "EPDM",        ├─ Cost feasibility          │ Cost: $153 🟡   │
  P_in: 3.5,               └─ Overall score             │ Score: 86/100   │
  target: {...}                ↓                         └─────────────────┘
}                          Compare to Target:               ↓
    ↓                      ├─ η_P: 84% vs >80% ✅       Optimization Radar:
                           ├─ ΔP: 0.7 vs <1.0 ✅        Shows closeness to
                           ├─ Cost: $153 vs <$150 🟡    target on all dims
                           └─ Score: 86/100                 ↓
                               ↓                         3D Model Effects:
                           Return JSON:                  ├─ Glow if near target
                           {                             ├─ Color shift
                             "components": {...},        └─ Update geometry
                             "derived": {...},
                             "comparison": {...}        Render at 60 FPS
                           }                            
                               ↓                         <100ms total time
                           Frontend updates all
```

**Key Points:**
- User sets target profile (optional, preset or custom)
- Backend calculates components AND derived metrics
- Backend compares to targets
- Frontend shows both raw values AND progress to target
- Visual feedback guides user to optimal configuration

---

## Advanced 3D Features (Premium Visual Quality)

### Materials & Rendering

**Physically-Based Rendering (PBR):**
```javascript
// Material properties vary by selection
{
  PVC: {
    color: '#E8E8E8',        // Light gray
    roughness: 0.6,          // Slightly matte
    metalness: 0.0,          // Non-metallic
    clearcoat: 0.2           // Slight sheen
  },
  Polyurethane: {
    color: '#FFD700',        // Golden/amber
    roughness: 0.4,          // Smoother
    metalness: 0.0,
    clearcoat: 0.5           // More glossy
  },
  EPDM: {
    color: '#2C2C2C',        // Dark rubber
    roughness: 0.8,          // Very matte
    metalness: 0.0
  }
}
```

**Lighting Setup:**
- Key light (main directional light)
- Fill lights (ambient softer light)
- Rim light (edge highlighting)
- Environment map (reflections)
- Shadow mapping enabled

**Post-Processing Effects:**
- Anti-aliasing (FXAA or SMAA)
- Ambient occlusion (subtle depth)
- Bloom (glow on high-performance configs)
- Optional: Depth of field for cinematic look

### Pressure Gradient Shader

**Custom vertex/fragment shader for smooth color interpolation:**
```glsl
// Pseudocode for pressure color mapping
uniform float P_in;      // Inlet pressure
uniform float P_out;     // Outlet pressure
varying float vPosition; // Position along hose (0-1)

vec3 getPressureColor() {
  float pressure = mix(P_in, P_out, vPosition);
  
  // Map pressure to color (red → yellow → green → blue)
  if (pressure > P_in * 0.9) return RED;
  else if (pressure > P_in * 0.7) return ORANGE;
  else if (pressure > P_in * 0.5) return YELLOW;
  else if (pressure > P_in * 0.3) return GREEN;
  else return BLUE;
}
```

**Result:** Smooth, continuous color gradient along hose length representing calculated pressure drop

---

## Responsive Behavior

### Desktop Layout (>1200px)
```
┌────────────────────────────┐
│  [3D Model] [Metrics]      │  ← Side by side
│  [Sliders in 3 columns]    │
│  [Charts in grid]          │
└────────────────────────────┘
```

### Tablet Layout (768px - 1200px)
```
┌─────────────────┐
│  [3D Model]     │  ← Full width
│  [Metrics]      │
│  [Sliders 2col] │
│  [Charts stack] │
└─────────────────┘
```

### Mobile (Not primary target, but functional)
```
┌──────────────┐
│  [Metrics]   │  ← Stats first
│  [3D Model]  │  ← Simplified
│  [Sliders]   │  ← Stacked
└──────────────┘
```

---

## Example Use Case Walkthrough (Simplified)

**Scenario:** Engineer sizing a 25m industrial cooling hose

### Step 1: Set Basic Inputs (Control Panel)
```
Material: Polyurethane
Length: 25 m
Inner Diameter: 15 mm (starting point)
Climate: Hot-Arid
Inlet Pressure: 4.0 bar
Flow Rate: 20 L/min
```

### Step 2: Set Target Profile
```
Application: Industrial Cooling (preset)

Target Profile Loaded:
├─ Min η_P: 80%
├─ Max ΔP: 1.0 bar
├─ Min Lifetime: 5 years
├─ Max Cost: $150
└─ Flow Velocity: 1.5-3.0 m/s
```
4: Optimize Diameter (Adjust Slider to Meet Target)
```
Move Di slider: 15mm → 20mm

Component Variables Update:
├─ ΔP_total: 1.2 → 0.5 bar ✅ Now below target!
├─ ΔP_friction: 1.0 → 0.4 bar
├─ v: 1.9 → 1.1 m/s ⚠️ Below optimal range
└─ Cost: $127 → $189 ⚠️ Above budget

Visual Changes:
├─ Hose widens (geometry update)
├─ Color gradient more uniform (less pressure loss)
└─ Glow effect appears (approaching target)

Key Metrics Update:
┌──────────────────────────────────┐
│ Metric           Current  Target │
│ Pressure Effic.  88%     >80%  ✅│
│ Pressure Drop    0.5 bar <1.0  ✅│
│ Lifetime         6.5 yr  >5    ✅│
│ Cost             $189    <$150 ❌│
├──────────────────────────────────┤
│ Overall Score:   78/100      🟡 │
│ Status: ACCEPTABLE (cost high)   │
└──────────────────────────────────┘

Optimization Radar Updates:
  Performance: 90% ✅
  Cost: 50% ❌ (over budget)
  Lifetime: 95% ✅
  Efficiency: 92% ✅
│ Pressure Drop    1.2 bar <1.0  ❌│
│ Lifetime         6.5 yr  >5    ✅│
│ Cost             $127    <$150 ✅│
├──────────────────────────────────┤
│ Overall Score:   65/100      ⚠️ │
│ Status: NEEDS IMPROVEMENT        │
└──────────────────────────────────┘
```5: Fine-tune to Meet All Targets
```
Adjust Di slider: 20mm → 18mm (compromise)

Component Variables:
├─ ΔP_total: 0.5 → 0.7 bar ✅ Still good
├─ v: 1.1 → 1.7 m/s ✅ Now in optimal range
└─ Cost: $189 → $153 🟡 Close to budget

Key Metrics:
┌──────────────────────────────────┐
│ Metric           Current  Target │
│ Pressure Effic.  84%     >80%  ✅│
│ Pressure Drop    0.7 bar <1.0  ✅│
│ Lifetime         6.5 yr  >5    ✅│
│ Cost             $153    <$150 🟡│ ← $3 over
├──────────────────────────────────┤
│ Overall Score:   86/100      🟢 │
│ Status: NEAR OPTIMAL             │
└──────────────────────────────────┘

Optimization Radar:
  All dimensions in green zone!
  Minor cost overrun acceptable
```

### Step 6: Try Alternative Material
```
Change Material: Polyurethane → EPDM

Component Variables Update:
├─ ΔP_total: 0.7 → 0.8 bar (slightly worse, still OK)
├─ Lifetime: 6.5 → 9.2 years ✅ Much longer!
├─ Cost: $153 → $138 ✅ Under budget!
└─ Material texture: Golden → Dark rubber

Key Metrics:
┌──────────────────────────────────┐
│ Metric           Current  Target │
│ Pressur7: Export Optimal Configuration
```
Click [Export]

Generates PDF Report:
├─ Target Profile Definition
├─ Final Configuration (all inputs)
├─ Component Variables (all calculated values)
├─ Key Metrics vs Targets (comparison table)
├─ Optimization Score: 91/100
├─ 3D Model Screenshot
├─ Material Specification Sheet
└─ Recommendation: "OPTIMAL - Deploy this configuration"────┘

Decision: EPDM at 18mm Di = OPTIMAL
  ✅ Meets all targets
  ✅ Longer lifetime bonus
  ✅ Under budget
  ✅ Excellent performance
```
Engineer sees:
- Better performance (lower pressure drop)
- Higher cost ($62 more)
- Decision: Worth it for critical cooling application
```

### Step 5: Check Different Material
```
Change Material dropdown: Polyurethane → EPDM

3D Model Updates:
├─ Pressure Drop: 0.5 → 0.6 bar (slightly worse)
├─ Expected Life: 6.5 → 10 years ✅ LONGER
├─ Cost: $189 → $165 ✅ CHEAPER
└─ Material appearance changes (dark rubber texture)

Decision: EPDM wins (longer life, cheaper, acceptable performance)
```

### Step 6: Export Configuration
```
Click [Export]
Generates:
├─ Configuration summary (all inputs)
├─ Performance metrics (all outputs)
├─ 3D model screenshot
└─ Material specification sheet
```

---

## Color Scheme & Aesthetics

**Overall Theme:** Professional Engineering Tool (Dark mode with accent colors)

```
Background: #1A1A1A (Dark gray)
Panels: #2D2D2D (Medium gray)
Text: #FFFFFF (White)
Accent: #00E5FF (Cyan) for primary actions
Success: #00FF88 (Green) for good performance
Warning: #FFB84D (Orange) for caution
Error: #FF4444 (Red) for poor performance

Pressure Gradient:
  High: #FF3333 (Red)
  Med-High: #FF9933 (Orange)
  Medium: #FFFF33 (Yellow)
  Med-Low: #33FF33 (Green)
  Low: #3333FF (Blue)
```

---

## Performance Targets

- **3D Rendering**: 60 FPS on modern hardware (1080p)
- **Calculation Response**: <100ms from slider change to display update
- **Smooth Animations**: 60 FPS transitions on all UI elements
- **Load Time**: <2 seconds to interactive state

---

## REVISED SCOPE: What's In, What's Out

### ✅ IN SCOPE (This Feasibility Tool)

**INPUT Variables (Control Panel):**
1. Geometry: Di, Do, L, roughness, bends
2. Material: Type (dropdown)
3. Environment: Climate zone, ambient temperature
4. Operating: Inlet pressure, flow rate, fluid properties

**OUTPUT Variables (3D Display):**
1. **Performance**: Pressure drop, friction loss, flow velocity, Reynolds number, efficiency
2. **Durability**: Expected lifetime, degradation rate
3. **Cost**: Material cost, cost/meter, total hose cost

**Visualization:**
1. 3D hose model with realistic materials
2. Pressure gradient color coding
3. Callout labels for key outputs
4. Clean, professional UI

### ❌ OUT OF SCOPE (For Now)

**Not Calculating (too use-case specific):**
- ROI (need specific use case and baseline)
- Payback period (need operating cost data)
- Energy cost comparison (need usage patterns)
- Comparative analysis across scenarios

**Not Visualizing:**
- Fluid particles or flow animation (not CFD)
- Turbulence or eddies
- Time-varying dynamics
- Complex charts and graphs (keep it simple)

### 🔄 SIMPLE, COMPREHENSIVE APPROACH

```
┌─────────────────┐         ┌──────────────────────┐
│ CONTROL PANEL   │    →    │   3D MODEL DISPLAY   │
│                 │         │                      │
│ • Dropdowns     │         │ • Calculated results │
│ • Sliders       │  Math   │ • Visual feedback    │
│ • User inputs   │  Engine │ • Output metrics     │
│                 │         │                      │
└─────────────────┘         └──────────────────────┘

Simple: Two areas, clear purpose
Comprehensive: All relevant variables and outputs
```

---

## OUTPUT VARIABLES ARCHITECTURE

### Component Variables (Direct Calculations - Displayed as Callouts)

**Hydraulic Calculations:**
- ΔP_total: Total pressure drop [bar]
- ΔP_friction: Friction loss [bar]  
- ΔP_local: Local losses at bends [bar]
- P_out: Outlet pressure [bar]
- v: Flow velocity [m/s]
- Re: Reynolds number [-]
- f: Friction factor [-]

**Physical Properties:**
- W_total: Hose weight [kg]
- W_per_m: Weight per meter [kg/m]
- P_burst: Burst pressure [bar]
- SF: Safety factor [-]

**Economic:**
- C_material: Material cost [$]
- C_per_m: Cost per meter [$/m]
- C_total: Total hose cost [$]

**Durability:**
- L_expected: Expected lifetime [years]
- D_rate: Degradation rate [%/year]

---

### Key Derived Metrics (Calculated from Components - Displayed in Table)

**1. Pressure Efficiency (η_P)**
```
η_P = (P_out / P_in) × 100%

Target: >75% (Good), >85% (Excellent)
Interpretation: How much inlet pressure is retained at outlet
```

**2. Flow Performance Grade**
```
Based on:
- ΔP_total (lower is better)
- v (optimal range: 1.5-3.5 m/s)
- Re (turbulent but not excessive: 4000-100,000)

Grades: Poor | Fair | Good | Excellent
Interpretation: Overall hydraulic performance quality
```

**3. Cost Feasibility Score**
```
Comparison to baseline/reference hose:
- C_per_m vs typical market price
- Value = Performance / Cost ratio

Grades: Expensive | Fair | Good Value | Excellent Value
```

**4. Lifetime Score**
```
L_expected vs material baseline in climate:
- PVC in temperate: 5 years baseline
- Adjustment for actual climate/conditions

Target: >5 years (minimum acceptable)
```

**5. Overall Optimization Score (0-100)**
```
Weighted composite:
- Performance (40%): From η_P, flow grade
- Cost (30%): From cost feasibility
- Lifetime (20%): From lifetime score
- Safety (10%): From safety factor

Score:
  90-100: Optimal
  75-89:  Near Optimal
  60-74:  Acceptable
  <60:    Needs Improvement
```

---

### Target Profile (User's Goal)

**User defines application requirements:**

```
┌────────────────────────────────────────┐
│ SET TARGET PROFILE (Optional)          │
│ ────────────────────────────────────── │
│ Application: [Industrial Cooling  ▼]   │
│                                        │
│ Auto-sets targets:                     │
│ • Min Pressure Efficiency: 80%         │
│ • Max Pressure Drop: 1.0 bar           │
│ • Min Lifetime: 5 years                │
│ • Max Cost: $150                       │
│ • Flow Velocity Range: 1.5-3.0 m/s     │
│                                        │
│ OR [Custom Targets] button             │
└────────────────────────────────────────┘
```

**Target profiles preset for common applications:**
- Garden Hose: Low cost, acceptable performance
- Industrial Cooling: High performance, moderate cost
- Chemical Transfer: High safety, long lifetime
- Irrigation: Low cost, acceptable lifetime
- Hydraulic: Very high performance, high cost OK

**Visual feedback:**
- User adjusts sliders → outputs update → comparison to target shows
- Green indicators when meeting/exceeding targets
- Red/yellow when below targets
- Optimization score updates in real-time

---

## Does This Revised Design Match Your Vision?

**Key Changes from Previous Mockup:**
1. ✅ **Simplified to two areas**: Control Panel (left) + 3D Display (right)
2. ✅ **Clear input/output separation**: No mixing of controls and results
3. ✅ **Removed ROI/comparative analysis**: Too complex, not needed for feasibility
4. ✅ **Focus on core outputs**: Performance, durability, cost
5. ✅ **3D model displays results**: Not just eye candy, it's the output display

**The tool is now:**
- Simple: Easy to understand at a glance
- Comprehensive: All relevant variables covered
- Focused: Answers "is this design feasible?" not "which is best?"

Is this aligned with your vision?
