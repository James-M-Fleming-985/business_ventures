# models/investment_analysis.py
import numpy as np
from scipy import optimize

def calculate_investment_metrics(cash_flows, initial_investment):
    """Calculate standard investment metrics used in financial analysis."""
    if not cash_flows or initial_investment <= 0:
        return {
            "npv": 0,
            "irr": None,
            "payback_period": float('inf'),
            "roi": 0
        }
    
    # Ensure cash_flows includes initial investment as first (negative) value
    all_flows = [-initial_investment] + cash_flows
    
    # Net Present Value (NPV) with 10% discount rate
    discount_rate = 0.10
    npv = sum(cf / ((1 + discount_rate) ** t) for t, cf in enumerate(all_flows))
    
    # Internal Rate of Return (IRR)
    def npv_function(rate):
        return sum(cf / ((1 + rate) ** t) for t, cf in enumerate(all_flows))
    
    try:
        irr = optimize.newton(npv_function, 0.1)  # Use Newton's method to find root
    except:
        try:
            irr = optimize.brentq(npv_function, -0.99, 2.0)  # Fallback method with bounds
        except:
            irr = None  # Unable to calculate IRR
    
    # Payback Period (simple)
    cumulative = -initial_investment
    payback_period = len(all_flows)
    for i, cf in enumerate(all_flows[1:], 1):
        cumulative += cf
        if cumulative >= 0:
            # Linear interpolation for more accurate payback period
            if i > 1 and cumulative > 0:
                previous_cumulative = cumulative - cf
                payback_period = (i-1) + abs(previous_cumulative) / abs(cf)
            else:
                payback_period = i
            break
    
    # Return on Investment (ROI)
    total_return = sum(all_flows[1:])
    roi = (total_return / initial_investment) * 100
    
    # Return metrics
    return {
        "npv": npv,
        "irr": irr * 100 if irr is not None else None,  # Convert to percentage
        "payback_period": payback_period,
        "roi": roi
    }

def compare_investments(base_projection, alt_projection, investment_amount):
    """Compare two investment scenarios and return relative performance metrics."""
    if investment_amount <= 0:
        return {
            "relative_roi": 0,
            "roi_difference": 0,
            "better_option": "none",
            "roi_ratio": 1.0
        }
    
    # Extract relevant metrics from both projections
    base_final_worth = base_projection['net_worth'].iloc[-1]
    base_initial_worth = base_projection['net_worth'].iloc[0]
    base_roi = ((base_final_worth - base_initial_worth) / investment_amount) * 100
    
    alt_final_worth = alt_projection['net_worth'].iloc[-1]
    alt_initial_worth = alt_projection['net_worth'].iloc[0]
    alt_roi = ((alt_final_worth - alt_initial_worth) / investment_amount) * 100
    
    # Calculate comparison metrics
    roi_difference = base_roi - alt_roi
    better_option = "primary" if roi_difference > 0 else "alternative" if roi_difference < 0 else "equal"
    roi_ratio = base_roi / alt_roi if alt_roi != 0 else float('inf')
    
    return {
        "primary_roi": base_roi,
        "alternative_roi": alt_roi,
        "roi_difference": roi_difference,
        "better_option": better_option,
        "roi_ratio": roi_ratio
    }