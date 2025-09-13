# models/scenarios.py
import pandas as pd
import numpy as np
from modules.financial_dashboard.models.projections import project_financials

def define_standard_scenarios():
    """Define standard financial scenarios for analysis."""
    return {
        "baseline": {
            "name": "Baseline",
            "description": "Current projections with no adjustments",
            "params": {
                "revenue_factor": 1.0,
                "expense_factor": 1.0,
                "interest_rate_factor": 1.0,
                "efficiency_factor": 1.0
            }
        },
        "optimistic": {
            "name": "Optimistic",
            "description": "Higher growth, better efficiency, favorable rates",
            "params": {
                "revenue_factor": 1.2,
                "expense_factor": 0.95,
                "interest_rate_factor": 0.9,
                "efficiency_factor": 1.25
            }
        },
        "pessimistic": {
            "name": "Pessimistic",
            "description": "Lower growth, higher costs, unfavorable rates",
            "params": {
                "revenue_factor": 0.85,
                "expense_factor": 1.15,
                "interest_rate_factor": 1.2,
                "efficiency_factor": 0.8
            }
        },
        "recession": {
            "name": "Economic Downturn",
            "description": "Significant revenue drop, cost pressures, high rates",
            "params": {
                "revenue_factor": 0.7,
                "expense_factor": 1.1,
                "interest_rate_factor": 1.5,
                "efficiency_factor": 0.9
            }
        },
        "expansion": {
            "name": "Economic Boom",
            "description": "Exceptional growth, favorable borrowing conditions",
            "params": {
                "revenue_factor": 1.35,
                "expense_factor": 1.05,
                "interest_rate_factor": 0.8,
                "efficiency_factor": 1.2
            }
        }
    }

def get_business_scenarios():
    """Get pre-defined business scenarios."""
    standard = define_standard_scenarios()
    
    # Add business-specific scenarios
    business_specific = {
        "supply_chain_disruption": {
            "name": "Supply Chain Disruption",
            "description": "Increased costs and decreased efficiency due to supply issues",
            "params": {
                "revenue_factor": 0.9,
                "expense_factor": 1.25,
                "interest_rate_factor": 1.0,
                "efficiency_factor": 0.7
            }
        },
        "technological_breakthrough": {
            "name": "Technological Breakthrough",
            "description": "Major efficiency gains from new technology adoption",
            "params": {
                "revenue_factor": 1.15,
                "expense_factor": 0.85,
                "interest_rate_factor": 1.0,
                "efficiency_factor": 1.5
            }
        }
    }
    
    return {**standard, **business_specific}

def get_personal_scenarios():
    """Get pre-defined personal finance scenarios."""
    standard = define_standard_scenarios()
    
    # Add personal finance-specific scenarios
    personal_specific = {
        "career_advancement": {
            "name": "Career Advancement",
            "description": "Significant income increase due to promotion or new job",
            "params": {
                "revenue_factor": 1.4,
                "expense_factor": 1.1,
                "interest_rate_factor": 1.0,
                "efficiency_factor": 1.0
            }
        },
        "market_crash": {
            "name": "Market Crash",
            "description": "Significant decrease in investment returns",
            "params": {
                "revenue_factor": 0.9,
                "expense_factor": 1.0,
                "interest_rate_factor": 1.3,
                "efficiency_factor": 0.7,
                "investment_return_factor": 0.5
            }
        },
        "early_retirement": {
            "name": "Early Retirement",
            "description": "Decreased income with focus on passive revenue streams",
            "params": {
                "revenue_factor": 0.6,
                "expense_factor": 0.8,
                "interest_rate_factor": 1.0,
                "efficiency_factor": 1.0
            }
        }
    }
    
    return {**standard, **personal_specific}

def run_scenario_analysis(financial_data, base_months=60, investment_amount=0, investment_type='cash',
                         investment_rate=5.0, investment_lifespan=5, efficiency_impact=0,
                         scenario_params=None, mode="business"):
    """
    Run financial projections with various scenarios.
    
    Args:
        financial_data: Base financial data
        base_months: Projection period in months
        investment_*: Investment parameters
        scenario_params: Specific scenario parameters to override defaults
        mode: "business" or "personal"
    
    Returns:
        Dictionary of projection dataframes for each scenario
    """
    # Get appropriate scenario sets based on mode
    if mode == "business":
        scenarios = get_business_scenarios()
    else:
        scenarios = get_personal_scenarios()
    
    # If specific scenarios provided, filter to those only
    if scenario_params and isinstance(scenario_params, list):
        scenarios = {k: v for k, v in scenarios.items() if k in scenario_params}
    
    results = {}
    
    # Run projections for each scenario
    for scenario_key, scenario in scenarios.items():
        # Apply scenario factors to base data
        modified_data = _apply_scenario_factors(financial_data, scenario["params"])
        
        # Adjust investment parameters based on scenario
        adjusted_rate = investment_rate
        adjusted_efficiency = efficiency_impact
        
        if "interest_rate_factor" in scenario["params"]:
            adjusted_rate *= scenario["params"]["interest_rate_factor"]
        
        if "efficiency_factor" in scenario["params"]:
            adjusted_efficiency *= scenario["params"]["efficiency_factor"]
        
        # Run projection with scenario adjustments
        projection = project_financials(
            modified_data,
            months=base_months,
            investment_amount=investment_amount,
            investment_type=investment_type,
            investment_rate=adjusted_rate,
            investment_lifespan=investment_lifespan,
            efficiency_impact=adjusted_efficiency
        )
        
        # Store result with scenario metadata
        results[scenario_key] = {
            "name": scenario["name"],
            "description": scenario["description"],
            "projection": projection
        }
    
    return results

def _apply_scenario_factors(financial_data, scenario_params):
    """Apply scenario factors to the financial data."""
    # Create a deep copy to avoid modifying original data
    import copy
    modified_data = copy.deepcopy(financial_data)
    
    # Apply revenue factor to income sources
    revenue_factor = scenario_params.get("revenue_factor", 1.0)
    if "income" in modified_data:
        for item in modified_data["income"]:
            item["amount"] = item["amount"] * revenue_factor
    
    # Apply expense factor to spending
    expense_factor = scenario_params.get("expense_factor", 1.0)
    if "spending" in modified_data:
        for item in modified_data["spending"]:
            item["amount"] = item["amount"] * expense_factor
    
    # Apply interest rate factors to debts
    interest_rate_factor = scenario_params.get("interest_rate_factor", 1.0)
    if "debts" in modified_data:
        for item in modified_data["debts"]:
            item["rate"] = item["rate"] * interest_rate_factor
    
    # Apply return factors to investments
    investment_return_factor = scenario_params.get("investment_return_factor", 1.0)
    if "investments" in modified_data:
        for item in modified_data["investments"]:
            item["return"] = item["return"] * investment_return_factor
    
    return modified_data

def get_scenario_summary(scenario_results):
    """Generate summary statistics for scenario comparison."""
    summary = []
    
    for scenario_key, data in scenario_results.items():
        projection = data["projection"]
        final_month = len(projection) - 1
        
        summary.append({
            "scenario_key": scenario_key,
            "name": data["name"],
            "description": data["description"],
            "final_net_worth": projection["net_worth"].iloc[-1],
            "final_cash_flow": projection["cash_flow"].iloc[-1],
            "final_revenue": projection["revenue"].iloc[-1],
            "final_ebitda": projection["ebitda"].iloc[-1],
            "avg_growth_rate": projection["net_worth_growth"].mean(),
            "min_cash_flow": projection["cash_flow"].min(),
            "max_cash_flow": projection["cash_flow"].max()
        })
    
    return pd.DataFrame(summary)