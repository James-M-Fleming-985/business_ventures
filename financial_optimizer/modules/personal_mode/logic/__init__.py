"""
Personal Mode Business Logic

This module contains business logic and calculations for Personal Mode
including investment calculations, portfolio optimization, and financial
analysis.
"""

from .financial_calculations import (
    calculate_uk_net_income,
    calculate_financial_projections,
    calculate_compound_interest,
    calculate_debt_amortization,
    calculate_weighted_investment_return,
    validate_financial_inputs,
    format_currency,
    format_percentage
)

__all__ = [
    'calculate_uk_net_income',
    'calculate_financial_projections', 
    'calculate_compound_interest',
    'calculate_debt_amortization',
    'calculate_weighted_investment_return',
    'validate_financial_inputs',
    'format_currency',
    'format_percentage'
]
