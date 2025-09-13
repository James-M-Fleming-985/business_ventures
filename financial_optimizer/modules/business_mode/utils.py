"""
Business Mode Utility Functions

This module contains utility functions for the Business Mode module
including business calculations, validation, and helper functions.
"""


def validate_business_metrics(revenue, expenses):
    """Validate business financial metrics"""
    if not revenue or not expenses:
        return False
    return revenue >= 0 and expenses >= 0


def format_business_currency(amount, currency="£"):
    """Format business monetary amounts with proper currency symbols"""
    if amount is None:
        return f"{currency}0.00"
    return f"{currency}{amount:,.2f}"


def calculate_business_cash_flow(revenue, expenses):
    """Calculate business cash flow from revenue and expenses"""
    if not revenue or not expenses:
        return 0
    return revenue - expenses
