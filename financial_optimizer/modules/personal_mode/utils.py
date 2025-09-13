"""
Personal Mode Utility Functions

This module contains utility functions for the Personal Mode module
including data processing, validation, and helper functions.
"""


def validate_allocation_percentages(allocations):
    """Validate that allocation percentages sum to 100%"""
    total = sum(allocations.values()) if allocations else 0
    return abs(total - 100) < 0.01


def format_currency(amount, currency="£"):
    """Format monetary amounts with proper currency symbols"""
    if amount is None:
        return f"{currency}0.00"
    return f"{currency}{amount:,.2f}"


def calculate_investment_capacity(monthly_income, monthly_expenses):
    """Calculate available investment capacity from cash flow"""
    if not monthly_income or not monthly_expenses:
        return 0
    return max(0, monthly_income - monthly_expenses)
