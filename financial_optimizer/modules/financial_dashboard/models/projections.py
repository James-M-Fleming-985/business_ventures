# models/projections.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def project_financials(financial_data, months=60, investment_amount=0, 
                      investment_type='cash', investment_rate=5.0, 
                      investment_lifespan=5, efficiency_impact=0,
                      calculate_baseline=False,
                      # New parameters
                      oee_availability=0, oee_performance=0, oee_quality=0,
                      staff_count=1, ramp_up_period=3, training_cost=2000):
    """
    Project financial metrics over time based on input data.
    Enhanced to handle OEE components and staff onboarding.
    """
    # Initialize data structures for tracking
    dates = [(datetime.now() + timedelta(days=30*i)).strftime('%Y-%m-%d') for i in range(months)]
    net_worth = []
    assets = []
    liabilities = []
    cash_flow = []
    ebitda = []
    revenue = []
    
    # Starting values (extracted from financial_data)
    current_assets = sum([s.get("balance", 0) for s in financial_data.get("savings", [])]) + \
                    sum([i.get("value", 0) for i in financial_data.get("investments", [])])
    current_liabilities = sum([d.get("balance", 0) for d in financial_data.get("debts", [])])
    monthly_income = sum([i.get("amount", 0) for i in financial_data.get("income", [])])
    monthly_expenses = sum([s.get("amount", 0) for s in financial_data.get("spending", [])])
    
    # Handle investment based on type
    investment_monthly_impact = 0
    investment_depreciation = 0
    efficiency_factor = 1.0
    
    # For tracking staff ramp-up
    staff_productivity = []
    if investment_type == 'staffing':
        # Initialize staffing productivity trajectory
        for month in range(months):
            if month < ramp_up_period:
                # Linear ramp-up from 25% to 100% productivity
                prod_factor = 0.25 + (0.75 * month / ramp_up_period)
            else:
                # Full productivity plus any ongoing improvement
                prod_factor = 1.0 + (month - ramp_up_period) * (efficiency_impact / 100 / 12)
                
            staff_productivity.append(prod_factor)
    
    if investment_amount > 0:
        if investment_type == 'cash':
            # Cash investment simply adds to assets
            current_assets += investment_amount
            
            # Also generates returns based on rate
            investment_monthly_impact = investment_amount * (investment_rate / 100 / 12)
            
        elif investment_type in ['equipment', 'it']:
            # Equipment is added to assets
            current_assets += investment_amount
            
            # But depreciates over time
            investment_depreciation = investment_amount / (investment_lifespan * 12)
            
            # Calculate combined OEE impact
            if oee_availability > 0 or oee_performance > 0 or oee_quality > 0:
                # Combined OEE calculation (multiplicative effect)
                oee_impact = (1 + oee_availability/100) * (1 + oee_performance/100) * (1 + oee_quality/100) - 1
                # Convert to percentage
                oee_impact = oee_impact * 100
                # Use the higher of manual efficiency or calculated OEE
                efficiency_impact = max(efficiency_impact, oee_impact)
            
            # Apply efficiency to revenue and costs
            efficiency_factor = 1 + (efficiency_impact / 100)
            
        elif investment_type == 'property':
            # Property is added to assets
            current_assets += investment_amount
            
            # Property may appreciate
            investment_monthly_impact = investment_amount * (investment_rate / 100 / 12)
            
        elif investment_type in ['rd', 'marketing', 'training']:
            # These investments may not show up directly as assets
            current_assets += investment_amount * 0.5  # Only half counted as tangible asset
            
            # But they affect revenue growth or efficiency
            efficiency_factor = 1 + (efficiency_impact / 100)
            
        elif investment_type == 'staffing':
            # New staff investment - initial costs
            initial_training_cost = staff_count * training_cost
            monthly_staff_cost = investment_amount - initial_training_cost  # Remaining is salary
            
            # Add one-time training expense
            monthly_expenses += initial_training_cost / 3  # Spread over first quarter
            
            # Staff costs are operating expenses, not assets
            monthly_expenses += monthly_staff_cost / 12  # Convert to monthly
        
        # Handle personal finance specific investment types
        elif investment_type == 'stocks':
            current_assets += investment_amount
            # Higher volatility but potentially higher returns
            investment_monthly_impact = investment_amount * (investment_rate / 100 / 12)
            
        elif investment_type == 'bonds':
            current_assets += investment_amount
            # Lower but more stable returns
            investment_monthly_impact = investment_amount * (investment_rate / 100 / 12)
            
        elif investment_type == 'education':
            # Education as an investment in future earning potential
            current_assets += investment_amount * 0.2  # Mostly intangible asset
            # Improves income growth rate
            efficiency_factor = 1 + (efficiency_impact / 100)
            
        elif investment_type == 'business':
            # Business investments have higher risk/reward
            current_assets += investment_amount * 0.7
            investment_monthly_impact = investment_amount * (investment_rate / 100 / 12)
            efficiency_factor = 1 + (efficiency_impact / 100)
    
    # Calculate initial values
    assets.append(current_assets)
    liabilities.append(current_liabilities)
    net_worth.append(current_assets - current_liabilities)
    cash_flow.append(monthly_income - monthly_expenses)
    ebitda.append(monthly_income * 0.7 - monthly_expenses * 0.8)  # Simplified EBITDA
    revenue.append(monthly_income)
    
    # Project future months
    for month in range(1, months):
        # Apply growth to income (with efficiency factor for certain investments)
        income_growth_factor = 1 + sum([i.get("growth", 0)/100/12 for i in financial_data.get("income", [])])
        
        # Adjust growth based on investment efficiency impacts
        if investment_amount > 0:
            if investment_type in ['marketing', 'rd', 'it']:
                income_growth_factor *= efficiency_factor
            elif investment_type == 'staffing' and month < len(staff_productivity):
                # Apply staff productivity factor to income
                staffing_impact = staff_productivity[month] * staff_count * 0.01
                income_growth_factor *= (1 + staffing_impact)
            elif investment_type in ['equipment']:
                # Equipment can increase production capacity
                income_growth_factor *= efficiency_factor
            
        new_income = monthly_income * income_growth_factor + investment_monthly_impact
        
        # Apply growth to expenses (with efficiency factor for operational investments)
        expense_growth_factor = 1 + 0.02/12  # Assumed 2% annual inflation
        
        # Adjust expenses based on investment efficiency impacts
        if investment_amount > 0 and investment_type in ['equipment', 'training', 'it']:
            expense_growth_factor /= efficiency_factor  # Reduce expenses
            
        new_expenses = monthly_expenses * expense_growth_factor
        
        # Add depreciation to expenses if applicable
        if investment_depreciation > 0:
            new_expenses += investment_depreciation
        
        # Calculate monthly cash flow
        monthly_cash_flow = new_income - new_expenses
        
        # Update asset values
        new_assets = current_assets + monthly_cash_flow
        
        # Update liabilities (simplified)
        debt_payment = sum([min(d.get("payment", 0), d.get("balance", 0)) 
                          for d in financial_data.get("debts", [])])
        new_liabilities = current_liabilities - debt_payment
        
        # Calculate projected EBITDA
        projected_ebitda = new_income * 0.7 - new_expenses * 0.8  # Simplified calculation
        
        # Store updated values
        assets.append(new_assets)
        liabilities.append(new_liabilities)
        net_worth.append(new_assets - new_liabilities)
        cash_flow.append(monthly_cash_flow)
        ebitda.append(projected_ebitda)
        revenue.append(new_income)
        
        # Update for next iteration
        current_assets = new_assets
        current_liabilities = new_liabilities
        monthly_income = new_income
        monthly_expenses = new_expenses
    
    # Create projection DataFrame
    projection_data = pd.DataFrame({
        'date': dates,
        'net_worth': net_worth,
        'assets': assets,
        'liabilities': liabilities,
        'cash_flow': cash_flow,
        'ebitda': ebitda,
        'revenue': revenue,
        'operating_margin': [e/r*100 if r > 0 else 0 for e, r in zip(ebitda, revenue)],
    })
    
    # Add additional calculated metrics
    projection_data['net_worth_growth'] = projection_data['net_worth'].pct_change() * 100
    projection_data['revenue_growth'] = projection_data['revenue'].pct_change() * 100
    projection_data['ebitda_growth'] = projection_data['ebitda'].pct_change() * 100
    
    # Calculate net profit (simplified)
    projection_data['net_profit'] = projection_data['ebitda'] * 0.7
    
    # If requested, also calculate baseline for comparison
    if calculate_baseline and investment_amount > 0:
        # Recursively call this function with no investment
        baseline_data = project_financials(
            financial_data, 
            months=months,
            investment_amount=0,
            calculate_baseline=False
        )
        return projection_data, baseline_data
    
    return projection_data