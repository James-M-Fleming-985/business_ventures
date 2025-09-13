"""
Core financial calculation engines that all use cases share.
These are the fundamental building blocks that remain consistent.
"""

from typing import Dict, Any, List, Optional, Union, Tuple
import pandas as pd
from datetime import datetime, timedelta


def calculate_net_worth(
    assets: List[Dict[str, Any]], liabilities: List[Dict[str, Any]]
) -> float:
    """Calculate net worth from assets and liabilities."""
    total_assets = sum(float(asset.get("value", 0)) for asset in assets)
    total_liabilities = sum(
        float(liability.get("value", 0)) for liability in liabilities
    )
    return total_assets - total_liabilities


def calculate_monthly_cash_flow(
    income: List[Dict[str, Any]], expenses: List[Dict[str, Any]]
) -> float:
    """Calculate monthly cash flow from income and expenses."""
    total_income = sum(float(item.get("amount", 0)) for item in income)
    total_expenses = sum(float(item.get("amount", 0)) for item in expenses)
    return total_income - total_expenses


def project_growth(
    initial_value: float, growth_rate: float, periods: int
) -> List[float]:
    """Project growth over time periods."""
    values = [initial_value]
    for period in range(periods):
        next_value = values[-1] * (1 + growth_rate / 100 / 12)  # Monthly growth
        values.append(next_value)
    return values


def calculate_investment_impact(
    initial_amount: float, investment_amount: float, return_rate: float, periods: int
) -> List[float]:
    """Calculate the impact of an investment over time."""
    values = []
    current_value = initial_amount

    for period in range(periods):
        if period == 0:
            current_value += investment_amount

        # Apply return rate
        current_value *= 1 + return_rate / 100 / 12
        values.append(current_value)

    return values


def generate_date_range(start_date: datetime, periods: int) -> List[datetime]:
    """Generate a date range for projections."""
    return [start_date + timedelta(days=30 * i) for i in range(periods)]
