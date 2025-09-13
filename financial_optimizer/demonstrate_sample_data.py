"""Test Sample Data Loading and Financial Dashboard Display"""

def test_sample_data_values():
    """Test the sample data values that will be loaded"""
    
    sample_data = {
        # Income values
        'gross_salary': 45000,
        'bonuses': 3000,
        'freelance': 800,
        'rental_income': 0,
        'dividends': 150,
        'other_income': 200,
        
        # Expense values
        'rent_mortgage': 1100,
        'transport': 280,
        'groceries': 350,
        'utilities': 120,
        'home_insurance': 85,
        'entertainment': 180,
        
        # Asset values
        'home_value': 220000,
        'savings': 8500,
        'investments': 12000,
        'other_assets': 3000,
        
        # Debt values
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
    
    print("🎯 SAMPLE DATA LOADED FOR FINANCIAL OPTIMIZER")
    print("=" * 60)
    
    # Calculate key metrics
    annual_income = (sample_data['gross_salary'] + sample_data['bonuses'] + 
                    (sample_data['freelance'] * 12) + (sample_data['rental_income'] * 12) +
                    sample_data['dividends'] + (sample_data['other_income'] * 12))
    
    monthly_income = annual_income / 12
    
    monthly_expenses = (sample_data['rent_mortgage'] + sample_data['transport'] + 
                       sample_data['groceries'] + sample_data['utilities'] + 
                       sample_data['home_insurance'] + sample_data['entertainment'])
    
    total_assets = (sample_data['home_value'] + sample_data['savings'] + 
                   sample_data['investments'] + sample_data['other_assets'])
    
    total_debts = (sample_data['mortgage_balance'] + sample_data['credit_cards'] + 
                  sample_data['personal_loans'] + sample_data['student_loans'] + 
                  sample_data['other_debts'])
    
    net_worth = total_assets - total_debts
    
    print("📊 INCOME BREAKDOWN:")
    print(f"   💰 Annual Gross Salary: £{sample_data['gross_salary']:,}")
    print(f"   🎁 Annual Bonuses: £{sample_data['bonuses']:,}")
    print(f"   💼 Monthly Freelance: £{sample_data['freelance']:,}")
    print(f"   📈 Annual Dividends: £{sample_data['dividends']:,}")
    print(f"   ➕ Other Income: £{sample_data['other_income']:,}/month")
    print(f"   📊 TOTAL ANNUAL INCOME: £{annual_income:,.2f}")
    print(f"   📊 TOTAL MONTHLY INCOME: £{monthly_income:,.2f}")
    
    print("\n💳 MONTHLY EXPENSES:")
    print(f"   🏠 Rent/Mortgage: £{sample_data['rent_mortgage']:,}")
    print(f"   🚗 Transport: £{sample_data['transport']:,}")
    print(f"   🛒 Groceries: £{sample_data['groceries']:,}")
    print(f"   ⚡ Utilities: £{sample_data['utilities']:,}")
    print(f"   🛡️ Home Insurance: £{sample_data['home_insurance']:,}")
    print(f"   🎭 Entertainment: £{sample_data['entertainment']:,}")
    print(f"   📊 TOTAL (before debt payments): £{monthly_expenses:,.2f}")
    
    print("\n🏠 ASSETS:")
    print(f"   🏡 Home Value: £{sample_data['home_value']:,}")
    print(f"   💰 Savings: £{sample_data['savings']:,}")
    print(f"   📈 Investments: £{sample_data['investments']:,}")
    print(f"   💎 Other Assets: £{sample_data['other_assets']:,}")
    print(f"   📊 TOTAL ASSETS: £{total_assets:,.2f}")
    
    print("\n💸 DEBTS:")
    print(f"   🏠 Mortgage: £{sample_data['mortgage_balance']:,} @ {sample_data['mortgage_rate']}% ({sample_data['mortgage_years']} years)")
    print(f"   💳 Credit Cards: £{sample_data['credit_cards']:,} @ {sample_data['credit_cards_rate']}%")
    print(f"   💰 Personal Loans: £{sample_data['personal_loans']:,} @ {sample_data['personal_loans_rate']}%")
    print(f"   🎓 Student Loans: £{sample_data['student_loans']:,} @ {sample_data['student_loans_rate']}%")
    print(f"   ➕ Other Debts: £{sample_data['other_debts']:,} @ {sample_data['other_debts_rate']}%")
    print(f"   📊 TOTAL DEBTS: £{total_debts:,.2f}")
    
    print("\n🎯 KEY FINANCIAL METRICS:")
    print(f"   💎 Net Worth: £{net_worth:,.2f}")
    print(f"   📊 Debt-to-Asset Ratio: {(total_debts/total_assets)*100:.1f}%")
    print(f"   💰 Monthly Income vs Fixed Expenses: £{monthly_income:,.2f} vs £{monthly_expenses:,.2f}")
    print(f"   ✅ Available for Debt Payments: £{monthly_income - monthly_expenses:,.2f}")
    
    print("\n🚀 WHAT TO EXPECT IN THE DASHBOARD:")
    print("   📈 Portfolio Performance Chart will show 5-year projections")
    print("   💰 Cash Flow tracking with debt reduction over time")
    print("   📊 Real-time financial metrics and warnings")
    print("   🎯 Investment growth modeling (6% annually)")
    print("   🏠 Property appreciation (2% annually)")
    print("   ⚠️ Debt-to-income ratio warnings if >30%")
    
    return sample_data

if __name__ == "__main__":
    test_sample_data_values()
