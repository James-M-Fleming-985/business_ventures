# models/financial_statements.py
import pandas as pd
import numpy as np

def create_financial_statements(financial_data, projection_horizon=60):
    """Create integrated financial statements following conventional accounting practices."""
    # Initialize data structures for statements
    income_statements = []
    balance_sheets = []
    cash_flow_statements = []
    
    # Starting balances
    current_assets = sum([s.get("balance", 0) for s in financial_data.get("savings", [])]) + \
                    sum([i.get("value", 0) for i in financial_data.get("investments", [])])
    current_liabilities = sum([d.get("balance", 0) for d in financial_data.get("debts", [])])
    equity = current_assets - current_liabilities
    
    # Process each month
    for month in range(projection_horizon):
        # INCOME STATEMENT
        revenue = sum([i.get("amount", 0) for i in financial_data.get("income", [])])
        expenses = sum([s.get("amount", 0) for s in financial_data.get("spending", [])])
        
        # Calculate conventional metrics
        gross_profit = revenue * 0.7  # Simplified - typically revenue minus COGS
        operating_expenses = expenses * 0.8  # Simplified - excludes interest, taxes
        ebitda = gross_profit - operating_expenses
        interest_expense = sum([d.get("balance", 0) * d.get("rate", 0)/100/12 
                              for d in financial_data.get("debts", [])])
        depreciation = current_assets * 0.01 / 12  # Simplified annual 1% depreciation
        ebit = ebitda - depreciation
        tax_rate = 0.20  # Simplified tax rate
        taxes = max(0, ebit * tax_rate)
        net_income = ebit - interest_expense - taxes
        
        # Store income statement
        income_statements.append({
            "month": month,
            "revenue": revenue,
            "gross_profit": gross_profit,
            "operating_expenses": operating_expenses,
            "ebitda": ebitda,
            "depreciation": depreciation, 
            "ebit": ebit,
            "interest_expense": interest_expense,
            "taxes": taxes,
            "net_income": net_income
        })
        
        # BALANCE SHEET UPDATES
        # Update assets
        current_assets += (revenue - expenses - interest_expense - taxes)
        # Update liabilities (simplified)
        interest_added = interest_expense
        principal_paid = sum([min(d.get("payment", 0), d.get("balance", 0)) 
                            for d in financial_data.get("debts", [])])
        current_liabilities += interest_added - principal_paid
        # Update equity
        equity = current_assets - current_liabilities
        
        # Store balance sheet
        balance_sheets.append({
            "month": month,
            "current_assets": current_assets,
            "long_term_assets": current_assets * 0.5,  # Simplified
            "total_assets": current_assets * 1.5,
            "current_liabilities": current_liabilities * 0.3,  # Simplified
            "long_term_liabilities": current_liabilities * 0.7,
            "total_liabilities": current_liabilities,
            "equity": equity,
            "total_liabilities_and_equity": current_liabilities + equity
        })
        
        # CASH FLOW STATEMENT
        operating_cash_flow = net_income + depreciation
        investing_cash_flow = -current_assets * 0.02  # Simplified reinvestment
        financing_cash_flow = -principal_paid
        net_cash_flow = operating_cash_flow + investing_cash_flow + financing_cash_flow
        
        cash_flow_statements.append({
            "month": month,
            "operating_cash_flow": operating_cash_flow,
            "investing_cash_flow": investing_cash_flow, 
            "financing_cash_flow": financing_cash_flow,
            "net_cash_flow": net_cash_flow,
            "beginning_cash": current_assets - net_cash_flow,
            "ending_cash": current_assets
        })
    
    return {
        "income_statements": income_statements,
        "balance_sheets": balance_sheets,
        "cash_flow_statements": cash_flow_statements
    }