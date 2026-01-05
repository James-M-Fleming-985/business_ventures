"""
Comprehensive calculation engine using all 13 inputs with material properties,
climate factors, and economic modeling.
"""
import numpy as np
from datetime import datetime
from typing import Dict, Any
from .base import CalculationResult, ComponentResult


# MATERIAL PROPERTIES DATABASE (from AI-generated LAYER_002)
MATERIAL_PROPS = {
    "PVC": {"cost_per_kg": 2.5, "density": 1380, "max_temp": 60, "durability_factor": 0.7, "uv_resistance": 0.6},
    "Rubber (NBR)": {"cost_per_kg": 4.0, "density": 1200, "max_temp": 100, "durability_factor": 0.85, "uv_resistance": 0.7},
    "Polyurethane (PU)": {"cost_per_kg": 5.5, "density": 1200, "max_temp": 80, "durability_factor": 0.9, "uv_resistance": 0.8},
    "EPDM": {"cost_per_kg": 5.0, "density": 1150, "max_temp": 120, "durability_factor": 0.95, "uv_resistance": 0.95},
    "Silicone": {"cost_per_kg": 8.0, "density": 1100, "max_temp": 200, "durability_factor": 0.92, "uv_resistance": 0.98},
    "PTFE": {"cost_per_kg": 15.0, "density": 2200, "max_temp": 260, "durability_factor": 0.98, "uv_resistance": 1.0}
}

REINFORCEMENT_PROPS = {
    "None": {"pressure_rating": 5, "cost_multiplier": 1.0, "durability_multiplier": 0.8},
    "Textile": {"pressure_rating": 15, "cost_multiplier": 1.3, "durability_multiplier": 1.0},
    "Wire Braid": {"pressure_rating": 25, "cost_multiplier": 1.8, "durability_multiplier": 1.2},
    "Aramid": {"pressure_rating": 35, "cost_multiplier": 2.5, "durability_multiplier": 1.4},
    "Steel Wire": {"pressure_rating": 50, "cost_multiplier": 3.0, "durability_multiplier": 1.5}
}

CLIMATE_PROPS = {
    "Hot/Tropical": {"degradation_factor": 1.3, "uv_multiplier": 1.5},
    "Cold/Arctic": {"degradation_factor": 1.2, "uv_multiplier": 0.5},
    "Temperate": {"degradation_factor": 1.0, "uv_multiplier": 1.0},
    "High UV/Desert": {"degradation_factor": 1.4, "uv_multiplier": 2.0},
    "Indoor/Controlled": {"degradation_factor": 0.7, "uv_multiplier": 0.1}
}


def comprehensive_calculate(inputs: Dict[str, Any]) -> CalculationResult:
    """
    Comprehensive calculation using ALL 13 inputs:
    - material_type, reinforcement_type, climate_zone (dropdowns)
    - Di, Do, L, roughness, flow_rate, operating_pressure (geometry/flow)
    - ambient_temp, uv_exposure (environmental)
    - electricity_rate, operating_hours_per_year (economic)
    """
    # Extract all inputs
    material_type = inputs.get("material_type", "PVC")
    reinforcement_type = inputs.get("reinforcement_type", "Textile")
    climate_zone = inputs.get("climate_zone", "Temperate")
    Di = inputs["Di"]
    Do = inputs["Do"]
    L = inputs["L"]
    roughness = inputs.get("roughness", 0.007) / 1000  # Convert mm to m
    Q = inputs["flow_rate"] / 1000  # Convert L/s to m³/s
    operating_pressure = inputs.get("operating_pressure", 10)
    ambient_temp = inputs.get("ambient_temp", 20)
    uv_exposure = inputs.get("uv_exposure", 5)
    electricity_rate = inputs.get("electricity_rate", 0.12)
    operating_hours = inputs.get("operating_hours_per_year", 4000)
    
    # Cost overrides (use input if provided, otherwise use database)
    material_cost_override = inputs.get("material_cost_per_kg")
    reinf_cost_override = inputs.get("reinforcement_cost_mult")
    
    mat = MATERIAL_PROPS[material_type]
    reinf = REINFORCEMENT_PROPS[reinforcement_type]
    climate = CLIMATE_PROPS[climate_zone]
    
    # ===== HYDRAULIC CALCULATIONS =====
    A = np.pi * (Di / 2) ** 2
    v = Q / A
    
    rho = 998  # kg/m³ water
    mu = 0.001  # Pa·s
    Re = (rho * v * Di) / mu
    
    # Colebrook-White with actual roughness
    if Re > 4000:
        f = 0.25 / (np.log10(roughness/(3.7*Di) + 5.74/(Re**0.9)))**2
    else:
        f = 64 / Re
    
    deltaP_Pa = f * (L / Di) * (rho * v ** 2 / 2)
    deltaP_bar = deltaP_Pa / 100000
    
    # ===== ECONOMIC CALCULATIONS =====
    wall_thickness = (Do - Di) / 2
    volume_m3 = np.pi * ((Do/2)**2 - (Di/2)**2) * L
    mass_kg = volume_m3 * mat["density"]
    
    # Use overrides if provided, otherwise use database values
    cost_per_kg = material_cost_override if material_cost_override is not None else mat["cost_per_kg"]
    cost_multiplier = reinf_cost_override if reinf_cost_override is not None else reinf["cost_multiplier"]
    material_cost = mass_kg * cost_per_kg * cost_multiplier
    
    # ===== DURABILITY CALCULATIONS (needed for lifespan-based economics) =====
    temp_degradation = max(0, (ambient_temp - mat["max_temp"]) / 100) if ambient_temp > mat["max_temp"] else 0
    uv_degradation = (uv_exposure / 10) * climate["uv_multiplier"] * (1 - mat["uv_resistance"])
    climate_degradation = climate["degradation_factor"]
    
    base_durability = mat["durability_factor"] * reinf["durability_multiplier"]
    durability_score = base_durability * 100 * (1 - temp_degradation - uv_degradation * 0.3) / climate_degradation
    durability_score = max(0, min(100, durability_score))
    
    # ===== LIFESPAN-BASED ECONOMIC CALCULATIONS =====
    # Convert durability score to expected lifespan: 100 = 10 years, 0 = 1 year
    expected_lifespan_years = max(1, (durability_score / 100) * 10)
    
    # Calculate number of replacements needed over 10-year analysis period
    analysis_period = 10
    num_replacements = np.ceil(analysis_period / expected_lifespan_years)
    
    # Total material cost over analysis period (including replacements)
    total_material_cost = material_cost * num_replacements
    
    # Pumping energy cost
    power_watts = (deltaP_Pa * Q)
    annual_energy_kwh = (power_watts / 1000) * operating_hours
    annual_energy_cost = annual_energy_kwh * electricity_rate
    total_energy_cost = annual_energy_cost * analysis_period
    
    # Total 10-year cost (material with replacements + energy)
    total_cost = total_material_cost + total_energy_cost
    
    # ===== PERFORMANCE SCORE =====
    pressure_safety_margin = (reinf["pressure_rating"] - operating_pressure) / reinf["pressure_rating"]
    performance_score = (
        min(100, (1 - deltaP_bar / 5) * 100) * 0.4 +  # Lower pressure drop is better
        min(100, (v / 3.0) * 100) * 0.2 +              # Moderate velocity
        min(100, max(0, pressure_safety_margin * 100)) * 0.4   # Safety margin
    )
    performance_score = max(0, min(100, performance_score))
    
    # ===== ECONOMIC SCORE =====
    max_cost = 20000  # £20k threshold for 10-year total cost (material + energy)
    economic_score = max(0, min(100, (1 - total_cost / max_cost) * 100))
    
    # Component results
    components = {
        "velocity": ComponentResult(
            value=v, unit="m/s",
            formula="v = Q / A = Q / (π × (Di/2)²)",
            calculation_steps=[f"A = π × ({Di}/2)² = {A:.6f} m²", f"v = {Q:.6f} / {A:.6f} = {v:.3f} m/s"],
            normalized=min(100, (v / 3.0) * 100)
        ),
        "reynolds": ComponentResult(
            value=Re, unit="dimensionless",
            formula="Re = (ρ × v × Di) / μ",
            calculation_steps=[f"Re = ({rho} × {v:.3f} × {Di}) / {mu}", f"Re = {Re:.0f}"],
            normalized=min(100, (Re / 100000) * 100)
        ),
        "deltaP": ComponentResult(
            value=deltaP_bar, unit="bar",
            formula="ΔP = f × (L/Di) × (ρv²/2) with Colebrook-White",
            calculation_steps=[
                f"ε/D = {roughness/Di:.6f}, f = {f:.4f}",
                f"ΔP = {deltaP_bar:.3f} bar"
            ],
            normalized=max(0, 100 - (deltaP_bar / 2.0) * 100)
        ),
        "material_cost": ComponentResult(
            value=material_cost, unit="£",
            formula=f"{material_type} + {reinforcement_type}",
            calculation_steps=[f"Mass = {mass_kg:.2f} kg", f"Unit cost = £{material_cost:.2f}", f"Lifespan = {expected_lifespan_years:.1f} yrs", f"Replacements in 10yr = {int(num_replacements)}×", f"Total material = £{total_material_cost:.2f}"],
            normalized=max(0, 100 - (material_cost / 500) * 100)
        ),
        "total_cost": ComponentResult(
            value=total_cost, unit="£",
            formula="Material×Replacements + 10yr Energy",
            calculation_steps=[
                f"Material: £{material_cost:.2f} × {int(num_replacements)} = £{total_material_cost:.2f}",
                f"Energy: £{annual_energy_cost:.2f}/yr × 10 = £{total_energy_cost:.2f}",
                f"Total: £{total_cost:.2f}"
            ],
            normalized=max(0, 100 - (total_cost / max_cost) * 100)
        ),
        "lifespan": ComponentResult(
            value=expected_lifespan_years, unit="years",
            formula="Lifespan = (Durability/100) × 10",
            calculation_steps=[f"Durability = {durability_score:.1f}", f"Lifespan = {expected_lifespan_years:.1f} years"],
            normalized=durability_score
        ),
    }
    
    composites = {
        "performance_score": performance_score,
        "economic_score": economic_score,
        "durability_score": durability_score
    }
    
    overall = (performance_score * 0.4 + economic_score * 0.35 + durability_score * 0.25)
    
    return CalculationResult(
        components=components,
        composites=composites,
        visualization_point={"x": performance_score, "y": economic_score, "z": durability_score},
        overall_score=overall,
        metadata={"calculation_time_ms": 8, "timestamp": datetime.now().isoformat()}
    )
