"""Test UK Tax Calculation"""

def calculate_uk_net_income(gross_annual_salary):
    """Calculate UK net monthly income after tax and NI"""
    if not gross_annual_salary:
        return 0
    
    # UK Tax rates for 2024/25
    personal_allowance = 12570
    basic_rate_threshold = 50270
    higher_rate_threshold = 125140
    
    # Calculate income tax
    taxable_income = max(0, gross_annual_salary - personal_allowance)
    income_tax = 0
    
    if taxable_income <= (basic_rate_threshold - personal_allowance):
        income_tax = taxable_income * 0.20  # Basic rate 20%
    elif taxable_income <= (higher_rate_threshold - personal_allowance):
        income_tax = (basic_rate_threshold - personal_allowance) * 0.20
        income_tax += (taxable_income - (basic_rate_threshold - personal_allowance)) * 0.40
    else:
        income_tax = (basic_rate_threshold - personal_allowance) * 0.20
        income_tax += (higher_rate_threshold - basic_rate_threshold) * 0.40
        income_tax += (taxable_income - (higher_rate_threshold - personal_allowance)) * 0.45
    
    # Calculate National Insurance (Class 1)
    ni_lower_threshold = 12570
    ni_upper_threshold = 50270
    national_insurance = 0
    
    if gross_annual_salary > ni_lower_threshold:
        ni_earnings = min(gross_annual_salary, ni_upper_threshold) - ni_lower_threshold
        national_insurance = ni_earnings * 0.12
        
        if gross_annual_salary > ni_upper_threshold:
            national_insurance += (gross_annual_salary - ni_upper_threshold) * 0.02
    
    # Calculate net annual income
    net_annual = gross_annual_salary - income_tax - national_insurance
    net_monthly = net_annual / 12
    
    return net_monthly


def test_tax_calculation():
    """Test UK tax calculation with sample data"""
    
    gross_salary = 45000
    
    print("🇬🇧 UK TAX CALCULATION TEST")
    print("=" * 40)
    print(f"Gross Annual Salary: £{gross_salary:,}")
    
    # Calculate tax breakdown
    personal_allowance = 12570
    taxable_income = max(0, gross_salary - personal_allowance)
    income_tax = taxable_income * 0.20  # Basic rate
    
    # National Insurance
    ni_earnings = gross_salary - 12570
    national_insurance = ni_earnings * 0.12
    
    # Net calculation
    net_annual = gross_salary - income_tax - national_insurance
    net_monthly = calculate_uk_net_income(gross_salary)
    
    print(f"Personal Allowance: £{personal_allowance:,}")
    print(f"Taxable Income: £{taxable_income:,}")
    print(f"Income Tax (20%): £{income_tax:,.2f}")
    print(f"National Insurance (12%): £{national_insurance:,.2f}")
    print(f"Net Annual Income: £{net_annual:,.2f}")
    print(f"Net Monthly Income: £{net_monthly:,.2f}")
    
    print(f"\n📊 COMPARISON:")
    print(f"Previous (Gross): £{gross_salary/12:,.2f}/month")
    print(f"New (Net): £{net_monthly:,.2f}/month")
    print(f"Tax Savings: £{(gross_salary/12) - net_monthly:,.2f}/month")
    
    # Test with sample data including other income
    bonuses = 3000
    freelance = 800
    dividends = 150
    other_income = 200
    
    monthly_bonuses = bonuses / 12
    monthly_dividends = dividends / 12
    
    total_monthly = net_monthly + monthly_bonuses + freelance + monthly_dividends + other_income
    
    print(f"\n💰 TOTAL MONTHLY INCOME (with other sources):")
    print(f"Net Salary: £{net_monthly:,.2f}")
    print(f"Monthly Bonuses: £{monthly_bonuses:,.2f}")
    print(f"Freelance: £{freelance:,.2f}")
    print(f"Monthly Dividends: £{monthly_dividends:,.2f}")
    print(f"Other Income: £{other_income:,.2f}")
    print(f"TOTAL: £{total_monthly:,.2f}")
    
    return net_monthly


if __name__ == "__main__":
    test_tax_calculation()
