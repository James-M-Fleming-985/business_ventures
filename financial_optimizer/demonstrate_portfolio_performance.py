"""Test Portfolio Performance with Sample Data"""

from modules.personal_mode.main import calculate_monthly_debt_payments

def test_portfolio_with_sample_data():
    """Test portfolio performance calculations with the sample data"""
    
    # Sample data that matches the app
    sample_data = {
        'gross_salary': 45000,
        'bonuses': 3000,
        'freelance': 800,
        'rental_income': 0,
        'dividends': 150,
        'other_income': 200,
        'rent_mortgage': 1100,
        'transport': 280,
        'groceries': 350,
        'utilities': 120,
        'home_insurance': 85,
        'entertainment': 180,
        'home_value': 220000,
        'savings': 8500,
        'investments': 12000,
        'other_assets': 3000,
        'mortgage_balance': 180000,
        'mortgage_rate': 3.2,
        'mortgage_years': 23,
        'credit_cards': 3200,
        'credit_cards_rate': 19.9,
        'personal_loans': 8500,
        'personal_loans_rate': 7.5,
        'student_loans': 12000,
        'student_loans_rate': 4.2,
        'other_debts': 1500,
        'other_debts_rate': 11.5
    }
    
    print("💰 PORTFOLIO PERFORMANCE ANALYSIS WITH SAMPLE DATA")
    print("=" * 60)
    
    # Calculate monthly debt payments
    monthly_debt_payments = calculate_monthly_debt_payments(
        sample_data['mortgage_balance'], sample_data['mortgage_rate'], sample_data['mortgage_years'],
        sample_data['credit_cards'], sample_data['credit_cards_rate'], 0,  # credit_cards_payment
        sample_data['personal_loans'], sample_data['personal_loans_rate'], 5,  # personal_loans_years
        sample_data['student_loans'], sample_data['student_loans_rate'], 0,  # student_loans_payment
        sample_data['other_debts'], sample_data['other_debts_rate'], 0  # other_debts_payment
    )
    
    # Calculate cash flow
    monthly_income = (sample_data['gross_salary'] / 12 + sample_data['bonuses'] / 12 + 
                     sample_data['freelance'] + sample_data['rental_income'] + 
                     sample_data['dividends'] / 12 + sample_data['other_income'])
    
    monthly_expenses = (sample_data['rent_mortgage'] + sample_data['transport'] + 
                       sample_data['groceries'] + sample_data['utilities'] + 
                       sample_data['home_insurance'] + sample_data['entertainment'] + monthly_debt_payments)
    
    monthly_cash_flow = monthly_income - monthly_expenses
    
    # Current financial position
    current_assets = (sample_data['home_value'] + sample_data['savings'] + 
                     sample_data['investments'] + sample_data['other_assets'])
    current_debts = (sample_data['mortgage_balance'] + sample_data['credit_cards'] + 
                    sample_data['personal_loans'] + sample_data['student_loans'] + sample_data['other_debts'])
    current_net_worth = current_assets - current_debts
    
    print("📊 CURRENT FINANCIAL SNAPSHOT:")
    print(f"   💰 Monthly Income: £{monthly_income:,.2f}")
    print(f"   💸 Monthly Debt Payments: £{monthly_debt_payments:,.2f}")
    print(f"   💳 Other Monthly Expenses: £{monthly_expenses - monthly_debt_payments:,.2f}")
    print(f"   📊 Total Monthly Expenses: £{monthly_expenses:,.2f}")
    print(f"   💎 Monthly Cash Flow: £{monthly_cash_flow:,.2f}")
    print(f"   🏠 Current Net Worth: £{current_net_worth:,.2f}")
    
    # Calculate debt-to-income ratio
    annual_debt_payments = monthly_debt_payments * 12
    annual_income = monthly_income * 12
    debt_to_income_ratio = (annual_debt_payments / annual_income) * 100
    
    print(f"\n⚠️ DEBT-TO-INCOME ANALYSIS:")
    print(f"   📊 Annual Debt Payments: £{annual_debt_payments:,.2f}")
    print(f"   📊 Annual Income: £{annual_income:,.2f}")
    print(f"   📊 Debt-to-Income Ratio: {debt_to_income_ratio:.1f}%")
    
    if debt_to_income_ratio > 30:
        print("   🚨 WARNING: High debt-to-income ratio (>30%)")
    elif debt_to_income_ratio > 20:
        print("   ⚠️ CAUTION: Moderate debt-to-income ratio")
    else:
        print("   ✅ HEALTHY: Good debt-to-income ratio")
    
    # 5-Year Projections
    print(f"\n📈 5-YEAR PORTFOLIO PERFORMANCE PROJECTIONS:")
    
    for year in range(1, 6):
        months = year * 12
        
        # Asset growth
        property_value = sample_data['home_value'] * (1.02 ** year)
        accumulated_savings = sample_data['savings'] + (monthly_cash_flow * months)
        investment_growth = sample_data['investments'] * (1.06 ** year)
        total_future_assets = property_value + accumulated_savings + investment_growth + sample_data['other_assets']
        
        # Debt reduction (simplified)
        principal_payments = monthly_debt_payments * months * 0.5  # Assume 50% goes to principal
        remaining_debt = max(0, current_debts - principal_payments)
        
        # Future net worth
        future_net_worth = total_future_assets - remaining_debt
        
        # Cash flow impact
        cumulative_cash_flow = monthly_cash_flow * months
        
        print(f"\n   📅 YEAR {year}:")
        print(f"      🏠 Property Value: £{property_value:,.2f} (+{((property_value/sample_data['home_value'])-1)*100:.1f}%)")
        print(f"      💰 Accumulated Savings: £{accumulated_savings:,.2f}")
        print(f"      📈 Investment Growth: £{investment_growth:,.2f} (+{((investment_growth/sample_data['investments'])-1)*100:.1f}%)")
        print(f"      💸 Remaining Debt: £{remaining_debt:,.2f} (-{((current_debts-remaining_debt)/current_debts)*100:.1f}%)")
        print(f"      💎 Projected Net Worth: £{future_net_worth:,.2f}")
        print(f"      💰 Cumulative Cash Flow: £{cumulative_cash_flow:,.2f}")
        print(f"      📊 Net Worth Growth: +£{future_net_worth - current_net_worth:,.2f} ({((future_net_worth/current_net_worth)-1)*100:.1f}%)")
    
    print(f"\n🎯 DASHBOARD VISUALIZATION PREVIEW:")
    print("   📈 Portfolio Performance Chart will display:")
    print("      • Net worth progression over 5 years")
    print("      • Asset growth (property 2%, investments 6% annually)")
    print("      • Debt reduction timeline")
    print("      • Monthly cash flow accumulation")
    print("      • Interactive year-by-year breakdown")
    
    print(f"\n✅ FINANCIAL HEALTH SCORE:")
    score = 0
    if monthly_cash_flow > 0:
        score += 25
        print("   ✅ Positive monthly cash flow (+25 points)")
    if debt_to_income_ratio < 30:
        score += 25
        print("   ✅ Healthy debt-to-income ratio (+25 points)")
    if current_net_worth > 0:
        score += 25
        print("   ✅ Positive net worth (+25 points)")
    if sample_data['savings'] > sample_data['gross_salary'] * 0.1:
        score += 25
        print("   ✅ Emergency fund present (+25 points)")
    
    print(f"\n   🏆 OVERALL FINANCIAL HEALTH: {score}/100")
    
    if score >= 75:
        print("   🌟 EXCELLENT financial position!")
    elif score >= 50:
        print("   ✅ GOOD financial foundation")
    elif score >= 25:
        print("   ⚠️ FAIR - room for improvement")
    else:
        print("   🚨 NEEDS ATTENTION - consider financial planning")
    
    return {
        'monthly_cash_flow': monthly_cash_flow,
        'current_net_worth': current_net_worth,
        'debt_to_income_ratio': debt_to_income_ratio,
        'monthly_debt_payments': monthly_debt_payments,
        'financial_health_score': score
    }

if __name__ == "__main__":
    results = test_portfolio_with_sample_data()
    print(f"\n📊 KEY METRICS SUMMARY:")
    print(f"Monthly Cash Flow: £{results['monthly_cash_flow']:,.2f}")
    print(f"Current Net Worth: £{results['current_net_worth']:,.2f}")
    print(f"Debt-to-Income: {results['debt_to_income_ratio']:.1f}%")
    print(f"Health Score: {results['financial_health_score']}/100")
