# Hose Performance Variable Inventory
**Purpose:** Complete catalog of variables impacting hose performance for feasibility modeling  
**Date:** December 29, 2025

---

## OPTIMIZATION OBJECTIVES (PRIMARY TARGETS)

### Triple Optimization Goal
The feasibility model targets three simultaneous objectives:

1. **MAXIMIZE Performance** (η_P, ΔP_min, flow delivery)
2. **MAXIMIZE ROI** (energy savings / total cost over lifetime)
3. **MINIMIZE Cost** (material + manufacturing + lifetime operating)

These are **competing objectives** - the model must identify Pareto-optimal profiles where trade-offs are balanced for specific applications and environments.

### Key Performance Indicators (KPIs)
| KPI | Formula | Target | Priority |
|-----|---------|--------|----------|
| Pressure Maintenance | η_P = P_out/P_in × 100% | Maximize | High |
| ROI | (Energy Savings - Extra Cost) / Extra Cost | >200% in 2-5 years | **Critical** |
| Cost per Meter | C_hose / L | Minimize | **Critical** |
| Total Cost of Ownership | C_purchase + C_energy × lifetime | Minimize | **Critical** |
| Energy Efficiency | 1 - (P_loss/P_in) | Maximize | High |
| Performance/Cost Ratio | η_P / c_pm | Maximize | High |

---

## 1. GEOMETRIC VARIABLES

### 1.1 Core Dimensions
| Variable | Symbol | Unit | Typical Range | Impact on Performance |
|----------|--------|------|---------------|----------------------|
| Inner Diameter | D_i | mm | 6-50 | ↑ D_i → ↓ velocity → ↓ friction loss (major impact) |
| Outer Diameter | D_o | mm | 10-60 | Structural only, affects material volume |
| Wall Thickness | t | mm | 2-10 | t = (D_o - D_i)/2, affects strength & weight |
| Total Length | L | m | 1-100 | ↑ L → ↑ friction loss (linear relationship) |

### 1.2 Internal Geometry
| Variable | Symbol | Unit | Typical Range | Impact on Performance |
|----------|--------|------|---------------|----------------------|
| Surface Roughness | ε | mm | 0.0015-0.15 | ↑ ε → ↑ friction factor (critical) |
| Internal Corrugation Depth | h_corr | mm | 0-3 | ↑ h_corr → ↑↑ friction loss (severe penalty) |
| Corrugation Pitch | p_corr | mm | 5-20 | Affects turbulence intensity |
| Taper Angle (if any) | α | degrees | 0-5 | Venturi effect, local velocity changes |

### 1.3 Bend & Coil Characteristics
| Variable | Symbol | Unit | Typical Range | Impact on Performance |
|----------|--------|------|---------------|----------------------|
| Bend Radius | R_bend | mm | 50-500 | ↓ R_bend → ↑ local losses (secondary flow) |
| Number of Bends | n_bend | - | 0-10 | Each bend adds loss coefficient |
| Coil Diameter | D_coil | mm | 200-600 | Coiled hose has higher friction than straight |
| Coil Pitch | p_coil | mm | 10-100 | Affects degree of helical flow distortion |

---

## 2. MATERIAL PROPERTIES

### 2.1 Mechanical Properties
| Variable | Symbol | Unit | Material Examples | Notes |
|----------|--------|------|-------------------|-------|
| Density | ρ_m | kg/m³ | PVC: 1300-1400<br>Rubber: 1100-1200<br>PU: 1200-1300<br>Steel: 7850 | Weight calculation |
| Tensile Strength | σ_t | MPa | PVC: 10-25<br>Rubber: 15-30<br>PU: 40-60<br>Aramid: 3000+ | Burst pressure capability |
| Elastic Modulus | E | MPa | PVC: 2500-3000<br>Rubber: 5-50<br>PU: 500-2000 | Flexibility, kink resistance |
| Allowable Stress | σ_allow | MPa | Typically σ_t / SF (SF=3-10) | Design constraint for pressure |
| Shore Hardness | - | Shore A/D | Soft rubber: 40A<br>Hard PVC: 75D | Flexibility, wear resistance |

### 2.2 Surface & Flow Properties
| Variable | Symbol | Unit | Material Examples | Notes |
|----------|--------|------|-------------------|-------|
| Surface Smoothness | ε | mm | Smooth polymer: 0.0015-0.007<br>Wire imprint: 0.015-0.05<br>Corrugated: 0.05-0.15 | Critical for friction |
| Coefficient of Friction (internal) | μ_i | - | 0.3-0.8 | Affects drag |
| Wettability | θ | degrees | Hydrophilic: <90°<br>Hydrophobic: >90° | Minor effect on boundary layer |

### 2.3 Environmental Resistance & Temperature Performance (CRITICAL)
| Variable | Unit | Material Examples | Notes |
|----------|------|-------------------|-------|
| Operating Temp Range | °C | PVC: -10 to 60<br>Rubber (NBR): -40 to 100<br>EPDM: -50 to 150<br>PU: -40 to 90<br>Silicone: -60 to 200<br>PTFE: -200 to 260 | Hard limits for material integrity |
| Optimal Performance Temp | °C | PVC: 15-40<br>Rubber: 10-60<br>PU: 0-50 | Best flexibility & durability |
| Temp Performance Degradation | %/10°C | Material-specific | Strength, flexibility loss outside optimal range |
| UV Resistance | rating (1-5) | PVC: 1-2 (Poor)<br>Rubber+carbon: 4 (Good)<br>PU: 5 (Excellent)<br>EPDM: 4 | Outdoor durability, UV stabilizers help |
| UV Degradation Rate | %/year | PVC unstabilized: 10-20%<br>PVC stabilized: 2-5%<br>PU: <2% | Affects replacement frequency |
| Chemical Compatibility | - | Material-dependent | Limits applications, swelling, dissolution |
| Ozone Resistance | rating (1-5) | Natural rubber: 1<br>EPDM: 5<br>Nitrile: 3 | Cracking, aging in outdoor/industrial |
| Hydrolysis Resistance | rating (1-5) | Polyester: 2<br>Polyether PU: 4<br>PTFE: 5 | Hot water, steam applications |
| Abrasion Resistance | cycles to failure | PVC: 10k-50k<br>Rubber: 50k-100k<br>PU: 100k-500k | External wear |

### 2.3.1 Temperature Effects on Material Properties (Geographic Optimization)
| Material | Property | Cold (<0°C) | Moderate (15-25°C) | Hot (>40°C) | Notes |
|----------|----------|-------------|-------------------|-------------|-------|
| PVC | Flexibility | Stiff, brittle | Optimal | Softens | Poor for cold climates |
| PVC | Kink Resistance | Poor | Good | Excellent | |
| Rubber (NBR) | Flexibility | Reduced but OK | Optimal | Good | Good all-climate |
| Rubber (NBR) | Burst Pressure | +10% | Baseline | -5 to -10% | Slight thermal weakening |
| PU | Flexibility | Stiff but tough | Optimal | Good | Best for cold |
| PU | Abrasion Resist | Excellent | Excellent | Good | Slight degradation |
| EPDM | Flexibility | Excellent | Excellent | Excellent | Best temp stability |
| Silicone | Flexibility | Excellent | Excellent | Excellent | Premium, expensive |

**Geographic/Climate Implications:**
- **Hot climates** (Middle East, tropics, Australia): EPDM, stabilized PU, avoid standard PVC
- **Cold climates** (Canada, Nordic, high altitude): PU, EPDM, special rubber compounds
- **Temperate** (Europe, coastal US): Most materials acceptable, PVC competitive on cost
- **High UV** (tropical, high altitude): UV-stabilized materials essential, affects lifetime cost

### 2.4 Economic Properties (CRITICAL FOR ROI)
| Variable | Symbol | Unit | Typical Range | Notes |
|----------|--------|------|---------------|-------|
| Material Cost | c_m | $/kg | PVC: 1.5-3<br>Rubber: 3-8<br>PU: 5-12<br>Aramid: 20-50<br>PTFE: 15-30 | Bulk pricing, regional variation ±30% |
| Processing Cost | c_proc | $/m | Extrusion: 0.5-2<br>Braiding: 1-3<br>Multi-layer: 2-5 | Volume-dependent, setup costs |
| Reinforcement Cost | c_reinf | $/m | Wire: 0.3-1<br>Textile: 0.5-2<br>Aramid: 2-10 | Depends on pressure rating |
| Fitting Cost | c_fit | $/unit | Economy: 2-5<br>Industrial: 5-20<br>High-pressure: 20-100 | Per connection |
| Manufacturing Complexity | - | multiplier | Standard: 1.0x<br>Novel geometry: 1.2-2.0x | Affects c_proc |
| Tooling/Setup Cost | c_setup | $ | 1,000-50,000 | Amortized over production volume |
| Minimum Order Quantity | MOQ | m or units | 100-10,000 | Affects per-unit economics |

---

## 3. REINFORCEMENT VARIABLES

### 3.1 Reinforcement Structure
| Variable | Symbol | Unit | Options/Range | Impact |
|----------|--------|------|---------------|--------|
| Reinforcement Type | - | - | None / Wire / Textile / Aramid / Composite | Strength vs weight tradeoff |
| Number of Layers | n_layer | - | 1-4 | ↑ layers → ↑ strength, ↑ weight, ↑ cost |
| Braid Angle | β | degrees | 30-70 | Affects pressure rating vs flexibility |
| Wire Diameter | d_wire | mm | 0.2-2 | Larger → stronger but may imprint |
| Pitch/Spacing | s_reinf | mm | 1-10 | Tighter → higher strength |

### 3.2 Reinforcement Placement
| Variable | Options | Impact |
|----------|---------|--------|
| Placement | Embedded / Surface / Between layers | Affects roughness if internal |
| Coverage | Full / Spiral / Intermittent | Partial coverage saves weight |

---

## 4. FLUID PROPERTIES

### 4.1 Physical Properties
| Variable | Symbol | Unit | Example Values (Water at 20°C) | Notes |
|----------|--------|------|-------------------------------|-------|
| Density | ρ_f | kg/m³ | Water: 998<br>Oil: 850-900<br>Glycol: 1100 | Affects pressure drop |
| Dynamic Viscosity | μ | Pa·s | Water: 0.001<br>Oil: 0.01-0.1<br>Glycol: 0.015 | Critical for Reynolds number |
| Kinematic Viscosity | ν | m²/s | ν = μ/ρ_f | Used in calculations |
| Compressibility | - | - | Water: nearly incompressible | Usually negligible for liquids |

### 4.2 Temperature Effects
| Variable | Symbol | Unit | Range | Impact |
|----------|--------|------|-------|--------|
| Fluid Temperature | T_f | °C | 0-100 | ↑ T → ↓ viscosity → ↓ friction |
| Vapor Pressure | P_vap | bar | Temperature-dependent | Cavitation risk if local P drops below P_vap |

---

## 5. OPERATING CONDITIONS

### 5.1 Pressure & Flow
| Variable | Symbol | Unit | Typical Range | Impact |
|----------|--------|------|---------------|--------|
| Inlet Pressure | P_in | bar (gauge) | Garden: 2-4<br>Industrial: 5-20<br>Hydraulic: 50-400 | Primary driver of flow |
| Outlet Pressure | P_out | bar | P_in - ΔP | Performance metric |
| Required Min Outlet | P_out,min | bar | Application-specific | Design constraint |
| Volumetric Flow Rate | Q | L/min | Garden: 5-30<br>Industrial: 20-200 | Determines velocity |
| Mass Flow Rate | ṁ | kg/s | ṁ = ρ_f × Q | Alternative flow measure |

### 5.2 Velocity & Flow Regime
| Variable | Symbol | Unit | Formula/Range | Impact |
|----------|--------|------|---------------|--------|
| Flow Velocity | v | m/s | v = 4Q/(πD_i²) | Key for friction calc |
| Reynolds Number | Re | - | Re = ρ_f × v × D_i / μ | Determines flow regime |
| Flow Regime | - | - | Laminar: Re < 2300<br>Transitional: 2300-4000<br>Turbulent: Re > 4000 | Different friction correlations |

### 5.3 System Configuration
| Variable | Unit | Options | Impact |
|----------|------|---------|--------|
| Supply Type | - | Mains / Pump / Gravity / Pressurized tank | Determines available P_in |
| Orientation | - | Horizontal / Vertical / Sloped | Gravity effects (ρgh terms) |
| Elevation Change | m | -50 to +50 | ΔP_gravity = ρ_f × g × Δh |
| Duty Cycle | % | Continuous / Intermittent | Affects thermal effects, wear |

---

## 6. FITTING & CONNECTION VARIABLES

### 6.1 End Fittings
| Variable | Symbol | Unit | Impact |
|----------|--------|------|--------|
| Fitting Type | - | - | Quick-connect / threaded / barbed / flanged |
| Fitting Internal Diameter | D_fitting | mm | Step change → local loss |
| Number of Fittings | n_fit | - | Each adds loss coefficient K |
| Transition Geometry | - | - | Sharp / tapered / smooth |

### 6.2 Local Loss Coefficients
| Component | Loss Coefficient K | Notes |
|-----------|-------------------|-------|
| Sharp entrance | 0.5 | Inlet to hose |
| Sharp exit | 1.0 | Hose to atmosphere |
| Smooth entrance | 0.04-0.1 | Rounded inlet |
| 90° bend (sharp) | 0.9-1.5 | Depends on R/D |
| 90° bend (smooth) | 0.3-0.5 | Larger radius |
| T-junction | 1.0-1.8 | Flow direction dependent |
| Coupling/connector | 0.2-0.5 | Quality dependent |

---

## 7. PERFORMANCE METRICS (Calculated/Output)

### 7.1 Hydraulic Performance
| Metric | Symbol | Unit | Formula/Notes |
|--------|--------|------|---------------|
| Friction Factor | f | - | Moody diagram or correlations (Colebrook-White, etc.) |
| Pressure Drop | ΔP | bar | ΔP = f × (L/D_i) × (ρ_f × v²/2) + ΣK × (ρ_f × v²/2) |
| Head Loss | h_f | m | h_f = ΔP / (ρ_f × g) |
| Pressure Maintenance | η_P | % | η_P = (P_out / P_in) × 100% |
| Volumetric Efficiency | - | % | Q_actual / Q_theoretical |

### 7.2 Energy Metrics
| Metric | Symbol | Unit | Formula/Notes |
|--------|--------|------|---------------|
| Hydraulic Power Loss | P_loss | W | P_loss = ΔP × Q |
| Pump Power Required | P_pump | W | P_pump = ΔP × Q / η_pump |
| Energy per Volume | E_specific | J/L | E_specific = ΔP |
| Annual Energy Cost | C_energy | $/year | Based on duty cycle and electricity cost |

### 7.3 Physical Metrics
| Metric | Symbol | Unit | Formula/Notes |
|--------|--------|------|---------------|
| Hose Weight | W | kg | W = ρ_m × π/4 × (D_o² - D_i²) × L |
| Material Volume | V_m | m³ | V_m = π/4 × (D_o² - D_i²) × L |
| Specific Weight | w | kg/m | w = W / L |
| Burst Pressure | P_burst | bar | P_burst = 2 × σ_allow × t / D_i |
| Safety Factor | SF | - | SF = P_burst / P_operating |

### 7.4 Economic Metrics (PRIMARY OPTIMIZATION TARGETS)
| Metric | Symbol | Unit | Formula/Notes |
|--------|--------|------|---------------|
| Material Cost | C_mat | $ | C_mat = V_m × ρ_m × c_m |
| Reinforcement Cost | C_reinf | $ | C_reinf = c_reinf × L |
| Manufacturing Cost | C_mfg | $ | C_mfg = c_proc × L + C_setup / production_volume |
| Fitting Cost | C_fit | $ | C_fit = n_fittings × c_fit |
| Total Hose Cost | C_hose | $ | C_hose = C_mat + C_reinf + C_mfg + C_fit |
| Cost per Meter | c_pm | $/m | c_pm = C_hose / L |
| Shipping/Handling Cost | C_ship | $ | Weight-dependent, often 5-15% of C_hose |
| Annual Energy Cost | C_energy_annual | $/year | ΔP × Q × hours_per_year × electricity_rate / (η_pump × 3.6e6) |
| Replacement Frequency | f_replace | 1/years | Based on material degradation in environment |
| Annual Replacement Cost | C_replace_annual | $/year | C_hose × f_replace |
| Annual Maintenance Cost | C_maint_annual | $/year | Cleaning, inspection, repairs |
| Lifetime Operating Cost | C_operating | $ | (C_energy_annual + C_replace_annual + C_maint_annual) × lifetime |
| Total Cost of Ownership | **TCO** | $ | **TCO = C_hose + C_operating** |
| **Return on Investment** | **ROI** | **%** | **ROI = (C_savings - C_extra) / C_extra × 100%** |
| Payback Period | T_payback | years | T_payback = C_extra / C_savings_annual |

### 7.4.1 ROI Calculation Details (CRITICAL)
Compare optimized hose vs baseline (standard hose):

**Cost differential:**
```
C_extra = C_hose_optimized - C_hose_baseline
```

**Annual energy savings:**
```
C_energy_savings = (ΔP_baseline - ΔP_optimized) × Q × hours_per_year × electricity_rate / (η_pump × 3.6e6)
```
where electricity_rate in $/kWh, typical 0.10-0.30 $/kWh depending on region

**Annual replacement savings** (if optimized lasts longer):
```
C_replacement_savings = C_hose_baseline × (f_replace_baseline - f_replace_optimized)
```

**Total annual savings:**
```
C_savings_annual = C_energy_savings + C_replacement_savings + C_maintenance_savings
```

**ROI over lifetime:**
```
ROI = (C_savings_annual × lifetime - C_extra) / C_extra × 100%
```

**Target ROI:** >200% (i.e., 3x return) over 3-5 year lifetime for commercial viability
- Industrial: accept 1-2 year payback
- Consumer: need <6 month perceived value (harder to monetize energy savings)

---

## 8. ENVIRONMENTAL & USAGE VARIABLES (Geography & Climate Optimization)

### 8.1 Environmental Conditions (PRIMARY INPUTS FOR OPTIMIZATION)
| Variable | Symbol | Unit | Example Values | Impact on Material Selection |
|----------|--------|------|----------------|------------------------------|
| Ambient Temperature (avg) | T_amb_avg | °C | Tropics: 25-35<br>Temperate: 10-20<br>Cold: -10-10<br>Desert: 20-45 | **Critical** - determines material viability |
| Temperature Range (annual) | ΔT_amb | °C | Stable: ±10°C<br>Continental: ±40°C | Affects material fatigue cycles |
| Daily Temperature Swing | ΔT_daily | °C | Coastal: ±8°C<br>Desert: ±25°C | Thermal cycling stress |
| Peak Temperature | T_peak | °C | Design limit | Must be < material max temp |
| Minimum Temperature | T_min | °C | Design limit | Must be > material min temp |
| UV Index | - | 1-11+ | Indoor: 0<br>Temperate outdoor: 3-7<br>Tropical/altitude: 8-12 | UV degradation rate |
| Annual Sunshine Hours | hours/year | 1000-4000 | Northern Europe: 1500<br>Australia: 3000 | UV exposure accumulation |
| Humidity (avg) | % RH | 20-100 | Desert: 20-40<br>Tropical: 70-90 | Affects some polymers, mold |
| Rainfall/Water Exposure | mm/year or % | 100-4000+ | Outdoor wet vs dry | Hydrolysis, UV washing |
| Chemical Exposure | type | - | None/Oil/Solvents/Acids/Alkali | Material compatibility matrix |
| Abrasion Environment | rating (1-5) | 1-5 | Clean: 1<br>Construction: 4<br>Mining: 5 | External wear, coating needs |
| Dust/Particulate | mg/m³ | varies | Clean: <50<br>Industrial: >150 | Can increase surface roughness |
| Altitude | m | 0-3000+ | Sea level vs mountains | UV intensity, pressure |

### 8.2 Geographic/Climate Zones (Application-Specific Optimization)
| Climate Zone | Typical Regions | Temp Range | UV Index | Recommended Materials | Materials to Avoid |
|--------------|----------------|------------|----------|----------------------|-------------------|
| **Hot-Arid** | Middle East, SW USA, Australia interior | 15-50°C | 9-12 | EPDM, PU (UV-stab), Silicone | Standard PVC, natural rubber |
| **Hot-Humid** | SE Asia, Caribbean, Central Africa | 22-38°C | 8-11 | EPDM, synthetic rubber, PU | Standard PVC (UV), hygroscopic materials |
| **Temperate** | Europe, NE USA, coastal | -5-30°C | 3-7 | Most materials viable, PVC competitive | None if UV-stabilized |
| **Cold** | Canada, Scandinavia, Russia | -30-20°C | 2-6 | PU, EPDM, cold-rated rubber | Standard PVC, soft rubber |
| **High-Altitude** | Mountains, plateaus | -20-25°C | 10-15 | EPDM, PU, UV-resistant | Unstabilized materials |
| **Marine/Coastal** | Coastal areas | 5-30°C | 5-10 | Corrosion-resistant, EPDM, PU | Materials sensitive to salt/moisture |
| **Industrial** | Factories, chemical plants | 0-60°C | Variable | Application-specific chemistry | Generic materials |

**Optimization Implication:** Same application in different climates requires different material profiles for optimal ROI

### 8.3 Usage Patterns & Duty Cycle
| Variable | Symbol | Unit | Example Values | Impact |
|----------|--------|------|----------------|--------|
| Usage Hours per Day | h_day | hours | Residential: 0.5<br>Irrigation: 2-8<br>Industrial: 8-24 | Energy cost accumulation |
| Operating Days per Year | d_year | days | Seasonal: 90-180<br>Year-round: 300-365 | Utilization rate |
| Annual Operating Hours | h_year | hours | h_year = h_day × d_year | **Critical for ROI** |
| Peak vs Average Flow | - | ratio | 1.0-2.0 | Sizing, efficiency |
| Start/Stop Cycles per Day | n_cycles | - | Continuous: 1<br>Intermittent: 5-50 | Fatigue, fitting wear |
| Pressure Cycles | n_P_cycles | - | Static: low<br>Pulsating: high | Material fatigue |
| Storage Condition | - | - | Coiled/hung/straight/indoor/outdoor | UV, kinking, aging |
| Storage Temperature | T_storage | °C | Same as T_amb or controlled | Aging rate when idle |
| Cleaning Frequency | times/year | 0-100+ | Can increase roughness over time |
| Expected Lifetime | L_life | years | Consumer: 2-5<br>Industrial: 5-15 | **Critical for TCO & ROI** |
| Replacement Trigger | - | - | Failure/scheduled/performance degradation | Affects C_replace_annual |

### 8.4 Electricity Cost (Geographic Variable - ROI Driver)
| Region | Electricity Rate | Unit | Impact on ROI |
|--------|-----------------|------|---------------|
| USA (avg) | 0.10-0.15 | $/kWh | Baseline |
| Europe (avg) | 0.20-0.35 | $/kWh | **Higher ROI for efficiency** |
| Middle East | 0.03-0.08 | $/kWh | Lower ROI for efficiency |
| Australia | 0.20-0.30 | $/kWh | High ROI for efficiency |
| Industrial rate | 0.06-0.12 | $/kWh | Often lower than residential |
| Peak vs off-peak | 2-3x variation | - | Time-of-use optimization |

**ROI is highly sensitive to electricity cost** - same efficiency improvement has 3-4x higher ROI in Europe vs Middle East

---

## 9. KEY DIMENSIONLESS GROUPS

| Number | Formula | Physical Meaning | Typical Range | Significance |
|--------|---------|------------------|---------------|--------------|
| Reynolds | Re = ρvD/μ | Inertial / viscous forces | 10³-10⁵ | Flow regime |
| Friction factor | f = f(Re, ε/D) | Wall shear stress | 0.01-0.08 | Pressure drop |
| Relative roughness | ε/D_i | Surface texture | 10⁻⁵-10⁻² | Affects friction |
| Length/diameter | L/D_i | Geometry ratio | 100-10000 | Development length |

---

## 10. CONSTRAINTS & LIMITS

### 10.1 Hard Constraints
| Constraint | Typical Limit | Reason |
|------------|---------------|--------|
| Maximum Operating Pressure | < P_burst / SF | Safety (SF typically 3-10) |
| Minimum Bend Radius | > 5-10 × D_o | Prevent kinking/collapse |
| Maximum Velocity | < 5-8 m/s for water | Erosion, noise, water hammer |
| Temperature Limits | Material-dependent | Degradation, safety |
| Chemical Compatibility | Material-specific | Prevent dissolution/swelling |

### 10.2 Practical Constraints
| Constraint | Reason |
|------------|--------|
| Standard Sizes | Manufacturing, fitting compatibility |
| Handling Weight | Ergonomics, typically <1-2 kg/m for portable hoses |
| Coil Diameter | Storage, transport |
| Cost Ceiling | Market acceptance |
| Certification Requirements | Standards (ISO, DIN, BS, ASTM, etc.) |

---

## 11. CALCULATION RELATIONSHIPS

### 11.1 Core Equations

**Flow velocity:**
```
v = Q / A = 4Q / (π × D_i²)
```

**Reynolds number:**
```
Re = (ρ_f × v × D_i) / μ
```

**Friction factor (turbulent, Colebrook-White):**
```
1/√f = -2 × log₁₀(ε/(3.7×D_i) + 2.51/(Re×√f))
```
(Iterative solution or use Moody chart)

**Friction factor (laminar, Re < 2300):**
```
f = 64 / Re
```

**Pressure drop (Darcy-Weisbach):**
```
ΔP_friction = f × (L/D_i) × (ρ_f × v²/2)
```

**Local losses:**
```
ΔP_local = Σ K × (ρ_f × v²/2)
```

**Total pressure drop:**
```
ΔP_total = ΔP_friction + ΔP_local + ΔP_elevation
```
where `ΔP_elevation = ρ_f × g × Δh`

**Burst pressure (thin wall approximation):**
```
P_burst = 2 × σ_allow × t / D_i
```

**Weight:**
```
W = ρ_m × π/4 × (D_o² - D_i²) × L
```

---

## 12. DATA SOURCES & VALIDATION

### Required Data to Collect
- [ ] Material property databases (polymer suppliers, engineering handbooks)
- [ ] Roughness values for different manufacturing methods
- [ ] Actual hose specifications from manufacturers (catalogs)
- [ ] Friction factor correlations for specific hose types
- [ ] Cost data (material suppliers, manufacturing quotes)
- [ ] Standards documents (pressure ratings, testing methods)

### Validation Approach
- [ ] Cross-check equations with fluid mechanics textbooks
- [ ] Compare calculated pressure drops with manufacturer data sheets
- [ ] Benchmark against published research papers
- [ ] Simple physical tests (flow rate vs pressure for known hoses)

---

## NOTES

- All SI units unless otherwise specified
- Pressure in bar gauge (relative to atmospheric) unless stated absolute
- Temperature in Celsius unless stated otherwise
- Cost data will vary significantly by region and volume
- Many variables are interdependent (e.g., D_i and v for fixed Q)
- Model should allow parameter sweeps to explore design space
- Start with incompressible, steady flow; add complexity later if needed

---

## 13. MULTI-OBJECTIVE OPTIMIZATION FRAMEWORK

### 13.1 Objective Functions
The model must handle competing objectives simultaneously:

**Primary Objectives:**
1. **Minimize TCO:** `TCO = C_hose + C_operating × lifetime`
2. **Maximize Performance:** `η_P = P_out / P_in`
3. **Maximize ROI:** `ROI = (Savings - C_extra) / C_extra`

**Secondary Objectives:**
4. Minimize weight: `W = f(D_o, D_i, L, ρ_m)`
5. Minimize environmental impact: `E_impact = f(material, manufacturing, transport, lifetime)`
6. Maximize durability: `L_life = f(material, environment, usage)`

### 13.2 Constraints
**Hard constraints** (must satisfy):
- `P_burst ≥ SF × P_operating` (safety)
- `T_min_material ≤ T_amb_min` (temperature limits)
- `T_max_material ≥ T_amb_max`
- `Material compatible with fluid`
- `Standard sizes where required`

**Soft constraints** (preferably satisfy):
- `c_pm ≤ market_ceiling` (price competitiveness)
- `W/L ≤ handling_limit` (ergonomics)
- `Certification standards met`

### 13.3 Pareto Front Exploration
For each application scenario × climate zone:
- Vary design parameters (D_i, t, material, roughness)
- Calculate all objectives
- Identify non-dominated solutions (Pareto optimal)
- Trade-off analysis: cost vs performance vs ROI

**Output:** Optimal design profiles for each scenario showing where improvements are possible

---

## NEXT STEPS FOR MODELING

1. ✅ Complete this inventory
2. ⬜ Choose modeling platform (Python recommended - numpy, scipy, pandas, matplotlib)
3. ⬜ Create material property database (separate file with T-dependent properties)
4. ⬜ Create climate/geography database (regional T, UV, electricity costs)
5. ⬜ Implement core hydraulic equations (friction, pressure drop)
6. ⬜ Implement economic calculations (TCO, ROI)
7. ⬜ Define 5-10 test scenarios (application × climate combinations)
8. ⬜ Run baseline calculations (standard hose performance)
9. ⬜ Parameter sensitivity analysis (which variables matter most?)
10. ⬜ Multi-objective optimization (find Pareto fronts)
11. ⬜ Validate against real-world data (manufacturer specs, test data)
12. ⬜ Generate feasibility report (where is there opportunity?)
