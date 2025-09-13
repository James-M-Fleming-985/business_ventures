#!/usr/bin/env python3
"""
Financial Calculations Module

Advanced financial modeling functions for Personal Mode dashboard
Implements UK-specific tax calculations, compound interest, debt amortization,
and comprehensive financial projections for 6-360 month time ranges.

Based on Personal Mode Implementation Roadmap mathematical framework
"""

import numpy as np
from typing import Dict, List, Tuple, Any
from datetime import datetime, timedelta


def calculate_uk_net_income(gross_annual_salary: float) -> float:
    """
    Calculate UK net monthly income after tax and National Insurance
    
    Uses 2024/25 tax rates:
    - Personal Allowance: £12,570
    - Basic Rate (20%): £12,570 - £50,270
    - Higher Rate (40%): £50,270 - £125,140
    - Additional Rate (45%): Above £125,140
    
    National Insurance (Class 1):
    - 12% on earnings £12,570 - £50,270
    - 2% on earnings above £50,270
    """
    
    if not gross_annual_salary or gross_annual_salary <= 0:
        return 0

    # UK Tax thresholds for 2024/25
    personal_allowance = 12570
    basic_rate_threshold = 50270
    higher_rate_threshold = 125140

    # Calculate income tax
    taxable_income = max(0, gross_annual_salary - personal_allowance)
    income_tax = 0

    if taxable_income <= (basic_rate_threshold - personal_allowance):
        income_tax = taxable_income * 0.20  # Basic rate 20%
    elif taxable_income <= (higher_rate_threshold - personal_allowance):
        basic_tax = (basic_rate_threshold - personal_allowance) * 0.20
        higher_tax = (taxable_income - (basic_rate_threshold - personal_allowance)) * 0.40
        income_tax = basic_tax + higher_tax
    else:
        basic_tax = (basic_rate_threshold - personal_allowance) * 0.20
        higher_tax = (higher_rate_threshold - basic_rate_threshold) * 0.40
        additional_tax = (taxable_income - (higher_rate_threshold - personal_allowance)) * 0.45
        income_tax = basic_tax + higher_tax + additional_tax

    # Calculate National Insurance (Class 1)
    ni_lower_threshold = 12570
    ni_upper_threshold = 50270
    national_insurance = 0

    if gross_annual_salary > ni_lower_threshold:
        ni_earnings_basic = min(gross_annual_salary, ni_upper_threshold) - ni_lower_threshold
        national_insurance = ni_earnings_basic * 0.12  # 12% on basic rate

        if gross_annual_salary > ni_upper_threshold:
            ni_earnings_higher = gross_annual_salary - ni_upper_threshold
            national_insurance += ni_earnings_higher * 0.02  # 2% on higher rate

    # Calculate net income
    net_annual = gross_annual_salary - income_tax - national_insurance
    net_monthly = net_annual / 12

    return max(0, net_monthly)


def calculate_compound_interest(
    principal: float, 
    annual_rate: float, 
    years: float,
    monthly_contribution: float = 0
) -> float:
    """
    Calculate compound interest with optional monthly contributions
    
    Formula for compound interest with regular contributions:
    FV = P(1+r)^t + PMT[((1+r)^t - 1) / r]
    
    Where:
    - P = Principal amount
    - r = Annual interest rate (as decimal)
    - t = Time in years
    - PMT = Monthly contribution
    """
    
    if annual_rate == 0:
        return principal + (monthly_contribution * 12 * years)
    
    monthly_rate = annual_rate / 12
    total_months = years * 12
    
    # Compound interest on principal
    future_value_principal = principal * ((1 + monthly_rate) ** total_months)
    
    # Future value of monthly contributions
    if monthly_contribution > 0:
        future_value_contributions = monthly_contribution * (
            ((1 + monthly_rate) ** total_months - 1) / monthly_rate
        )
    else:
        future_value_contributions = 0
    
    return future_value_principal + future_value_contributions


def calculate_simple_interest(
    principal: float,
    annual_rate: float,
    years: float,
    monthly_contribution: float = 0
) -> float:
    """
    Calculate simple interest with monthly contributions
    
    Formula: FV = P(1 + rt) + PMT * t * (1 + r*t/2)
    """
    
    simple_interest_principal = principal * (1 + annual_rate * years)
    simple_interest_contributions = monthly_contribution * 12 * years * (1 + annual_rate * years / 2)
    
    return simple_interest_principal + simple_interest_contributions


def calculate_debt_amortization(
    extra_payment: float,
    interest_rate: float,
    years: float,
    principal_balance: float = 200000
) -> float:
    """
    Calculate interest savings from extra debt payments
    
    Uses standard mortgage amortization formula to determine
    interest savings from additional principal payments
    """
    
    if interest_rate == 0 or years == 0:
        return extra_payment * 12 * years
    
    monthly_rate = interest_rate / 12
    total_months = years * 12
    
    # Standard payment calculation
    standard_payment = principal_balance * (
        monthly_rate * (1 + monthly_rate) ** total_months
    ) / ((1 + monthly_rate) ** total_months - 1)
    
    # Payment with extra amount
    extra_payment_total = standard_payment + extra_payment
    
    # Calculate payoff time reduction and interest savings
    if extra_payment > 0:
        # Simplified interest savings calculation
        interest_savings = extra_payment * 12 * years * (interest_rate / 2)
        return max(0, interest_savings)
    
    return 0


def calculate_weighted_investment_return(
    savings_amount: float,
    savings_rate: float,
    investment_amount: float,
    investment_rate: float
) -> float:
    """
    Calculate weighted average return for dual savings/investment categories
    
    Formula: Weighted Return = (Amount1 * Rate1 + Amount2 * Rate2) / Total Amount
    """
    
    total_amount = savings_amount + investment_amount
    
    if total_amount == 0:
        return 0
    
    weighted_return = (
        (savings_amount * savings_rate) + (investment_amount * investment_rate)
    ) / total_amount
    
    return weighted_return


def calculate_financial_projections(
    control_inputs: Dict[str, float],
    baseline_data: Dict[str, float],
    time_range_months: int
) -> Dict[str, List[float]]:
    """
    Calculate comprehensive financial projections over specified time range
    
    Combines control panel inputs with user baseline data to project:
    - Net Worth progression
    - Total Assets growth
    - Total Liabilities reduction  
    - Cumulative Cash Flow accumulation
    
    Time ranges: 6 months to 360 months (30 years)
    """
    
    # Initialize projection arrays
    projections = {
        'net_worth': [],
        'total_assets': [],
        'total_liabilities': [],
        'cumulative_cash_flow': [],
        'monthly_cash_flow': []
    }
    
    # Extract control panel inputs with defaults
    monthly_income = control_inputs.get('monthly_income', 3500)
    income_growth = control_inputs.get('income_growth', 0.03)
    monthly_housing = control_inputs.get('monthly_housing', 1200)
    housing_rate_change = control_inputs.get('housing_rate_change', 0)
    monthly_utilities = control_inputs.get('monthly_utilities', 150)
    utilities_inflation = control_inputs.get('utilities_inflation', 0.05)
    monthly_transport = control_inputs.get('monthly_transport', 200)
    transport_inflation = control_inputs.get('transport_inflation', 0.03)
    monthly_food = control_inputs.get('monthly_food', 300)
    food_inflation = control_inputs.get('food_inflation', 0.04)
    monthly_savings = control_inputs.get('monthly_savings', 300)
    savings_rate = control_inputs.get('savings_rate', 0.03)
    monthly_investments = control_inputs.get('monthly_investments', 500)
    investment_return = control_inputs.get('investment_return', 0.07)
    investment_type = control_inputs.get('investment_type', 'compound')
    
    # Extract baseline data with defaults
    starting_assets = baseline_data.get('starting_assets', 50000)
    starting_liabilities = baseline_data.get('starting_liabilities', 180000)
    
    # Initialize running totals
    current_assets = starting_assets
    current_liabilities = starting_liabilities
    cumulative_cash = 0
    
    # Calculate projections for each month
    for month in range(1, time_range_months + 1):
        year = (month - 1) / 12
        
        # Apply annual growth rates
        current_monthly_income = monthly_income * ((1 + income_growth) ** year)
        current_housing = monthly_housing * ((1 + housing_rate_change) ** year)
        current_utilities = monthly_utilities * ((1 + utilities_inflation) ** year)
        current_transport = monthly_transport * ((1 + transport_inflation) ** year)
        current_food = monthly_food * ((1 + food_inflation) ** year)
        
        # Calculate monthly cash flow
        monthly_cash_flow = (
            current_monthly_income - 
            current_housing - 
            current_utilities - 
            current_transport - 
            current_food -
            monthly_savings -
            monthly_investments
        )
        
        # Update cumulative cash flow
        cumulative_cash += monthly_cash_flow
        
        # Update assets with savings and investment returns
        monthly_rate_savings = savings_rate / 12
        monthly_rate_investments = investment_return / 12
        
        if investment_type == 'compound':
            # Compound interest on existing assets plus new contributions
            current_assets = current_assets * (1 + monthly_rate_investments)
            current_assets += monthly_savings + monthly_investments
        else:
            # Simple interest approach
            current_assets += monthly_savings + monthly_investments
            current_assets += current_assets * monthly_rate_investments
        
        # Update liabilities (assuming mortgage-style reduction)
        if current_liabilities > 0:
            # Simplified debt reduction: principal payment reduces balance
            monthly_principal_payment = max(50, current_housing * 0.3)  # Estimate 30% goes to principal
            current_liabilities = max(0, current_liabilities - monthly_principal_payment)
        
        # Calculate net worth
        net_worth = current_assets - current_liabilities
        
        # Store projections
        projections['net_worth'].append(net_worth)
        projections['total_assets'].append(current_assets)
        projections['total_liabilities'].append(current_liabilities)
        projections['cumulative_cash_flow'].append(cumulative_cash)
        projections['monthly_cash_flow'].append(monthly_cash_flow)
    
    return projections


def calculate_opportunity_cost(
    monthly_amount: float,
    time_months: int,
    opportunity_rate: float = 0.07
) -> float:
    """
    Calculate opportunity cost of spending vs investing
    
    Shows how much wealth is lost by spending money instead of investing it
    """
    
    if monthly_amount <= 0 or time_months <= 0:
        return 0
    
    years = time_months / 12
    
    # Calculate what the money could have grown to if invested
    potential_future_value = calculate_compound_interest(
        0, opportunity_rate, years, monthly_amount
    )
    
    # Opportunity cost is the potential gains foregone
    total_contributions = monthly_amount * time_months
    opportunity_cost = potential_future_value - total_contributions
    
    return max(0, opportunity_cost)


def calculate_principal_payment(
    financial_inputs: Dict[str, float],
    month: int
) -> float:
    """
    Calculate monthly principal payment for debt reduction modeling
    
    Uses standard amortization to determine how much of each payment
    goes toward principal vs interest
    """
    
    monthly_payment = financial_inputs.get('mortgage', 1200)
    annual_rate = financial_inputs.get('mortgage_rate', 0.03)
    loan_term_years = 25  # Standard UK mortgage term
    
    if annual_rate == 0:
        return monthly_payment
    
    monthly_rate = annual_rate / 12
    total_months = loan_term_years * 12
    remaining_months = max(1, total_months - month + 1)
    
    # Calculate remaining balance using amortization formula
    principal_balance = 200000  # Estimated average UK mortgage
    
    # Standard mortgage payment calculation
    if monthly_rate > 0:
        monthly_interest = principal_balance * monthly_rate
        monthly_principal = monthly_payment - monthly_interest
        return max(0, monthly_principal)
    
    return monthly_payment


def format_currency(amount: float, currency: str = "£") -> str:
    """Format currency with proper thousand separators"""
    return f"{currency}{amount:,.0f}"


def format_percentage(rate: float) -> str:
    """Format percentage with one decimal place"""
    return f"{rate*100:.1f}%"


def validate_financial_inputs(inputs: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and sanitize financial inputs
    
    Ensures all values are within reasonable ranges and data types
    """
    
    validated = {}
    
    # Define validation rules
    validation_rules = {
        'monthly_income': {'min': 0, 'max': 50000, 'default': 3500},
        'income_growth': {'min': -0.1, 'max': 0.2, 'default': 0.03},
        'monthly_housing': {'min': 0, 'max': 10000, 'default': 1200},
        'monthly_utilities': {'min': 0, 'max': 1000, 'default': 150},
        'monthly_transport': {'min': 0, 'max': 2000, 'default': 200},
        'monthly_food': {'min': 0, 'max': 2000, 'default': 300},
        'monthly_savings': {'min': 0, 'max': 5000, 'default': 300},
        'monthly_investments': {'min': 0, 'max': 10000, 'default': 500},
        'savings_rate': {'min': 0, 'max': 0.15, 'default': 0.03},
        'investment_return': {'min': 0, 'max': 0.25, 'default': 0.07},
        'time_range_months': {'min': 6, 'max': 360, 'default': 60}
    }
    
    for key, rules in validation_rules.items():
        value = inputs.get(key, rules['default'])
        
        # Convert to float if possible
        try:
            value = float(value)
        except (ValueError, TypeError):
            value = rules['default']
        
        # Apply min/max constraints
        value = max(rules['min'], min(rules['max'], value))
        validated[key] = value
    
    # Handle string inputs
    validated['investment_type'] = inputs.get('investment_type', 'compound')
    if validated['investment_type'] not in ['simple', 'compound']:
        validated['investment_type'] = 'compound'
    
    return validated
