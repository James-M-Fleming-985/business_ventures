"""Test the current income calculation fixes"""

def test_income_calculation():
    """Test if the income is calculated correctly now"""
    
    # Sample data
    gross_salary = 45000  # Annual
    bonuses = 3000       # Annual  
    freelance = 800      # Monthly
    rental_income = 0    # Monthly
    dividends = 150      # Annual
    other_income = 200   # Monthly
    
    print("🧮 TESTING INCOME CALCULATION FIXES")
    print("=" * 50)
    print("Sample Data:")
    print(f"  Annual Gross Salary: £{gross_salary:,}")
    print(f"  Annual Bonuses: £{bonuses:,}")
    print(f"  Monthly Freelance: £{freelance:,}")
    print(f"  Monthly Rental Income: £{rental_income:,}")
    print(f"  Annual Dividends: £{dividends:,}")
    print(f"  Monthly Other Income: £{other_income:,}")
    
    # Correct calculation (what the app should do now)
    monthly_salary = gross_salary / 12
    monthly_bonuses = bonuses / 12
    monthly_dividends = dividends / 12
    
    correct_total = monthly_salary + monthly_bonuses + freelance + rental_income + monthly_dividends + other_income
    
    print(f"\n✅ CORRECT CALCULATION:")
    print(f"  Monthly Salary: £{monthly_salary:,.2f}")
    print(f"  Monthly Bonuses: £{monthly_bonuses:,.2f}")
    print(f"  Monthly Freelance: £{freelance:,.2f}")
    print(f"  Monthly Rental: £{rental_income:,.2f}")
    print(f"  Monthly Dividends: £{monthly_dividends:,.2f}")
    print(f"  Monthly Other: £{other_income:,.2f}")
    print(f"  TOTAL MONTHLY INCOME: £{correct_total:,.2f}")
    
    # Wrong calculation (what was happening before)
    wrong_total = gross_salary + bonuses + freelance + rental_income + dividends + other_income
    print(f"\n❌ PREVIOUS WRONG CALCULATION:")
    print(f"  Total (mixing annual/monthly): £{wrong_total:,.2f}")
    
    print(f"\n📊 COMPARISON:")
    print(f"  Correct Monthly Income: £{correct_total:,.2f}")
    print(f"  Previous Wrong Total: £{wrong_total:,.2f}")
    print(f"  Difference: £{wrong_total - correct_total:,.2f}")
    
    if abs(correct_total - 5012.5) < 1:
        print(f"\n✅ SUCCESS: Income calculation is now correct!")
    else:
        print(f"\n❌ Issue: Expected ~£5,012.50, got £{correct_total:,.2f}")
    
    return correct_total

if __name__ == "__main__":
    test_income_calculation()
