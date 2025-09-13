"""Test the Portfolio Performance Chart Data Display"""

import requests
import time

def test_app_functionality():
    """Test if the app is responding and portfolio performance is working"""
    
    print("🔧 TESTING FINANCIAL OPTIMIZER APP FUNCTIONALITY")
    print("=" * 60)
    
    # Test if app is running
    try:
        response = requests.get("http://127.0.0.1:8050")
        if response.status_code == 200:
            print("✅ App is running successfully on port 8050")
        else:
            print(f"❌ App responded with status code: {response.status_code}")
            return False
    except requests.exceptions.ConnectionError:
        print("❌ Cannot connect to app on port 8050")
        return False
    
    print("\n📋 MANUAL TEST INSTRUCTIONS:")
    print("To test the Portfolio Performance Chart, follow these steps:")
    print()
    print("1. 🌐 Open http://127.0.0.1:8050 in your browser")
    print("2. 📊 Navigate to the 'Data Input' tab")
    print("3. 🔧 Click 'Open Manual Entry' button")
    print("4. 🎯 Click 'Load Sample Data' button (blue button on the left)")
    print("5. 💾 Click 'Save Financial Profile' button")
    print("6. 📈 Navigate to the 'Financial Dashboard' tab")
    print("7. 👀 Look for the 'Portfolio Performance' section")
    print()
    print("Expected Results:")
    print("   📊 Net Worth line (green) should show growth from ~£38k to ~£206k")
    print("   🏠 Total Assets line (blue) should show growth")
    print("   💸 Total Liabilities line (red) should show decline")
    print("   💰 Cumulative Cash Flow line (dashed cyan) should show positive growth")
    print()
    print("If the chart is empty, check the browser console for errors.")
    
    return True

def verify_sample_data():
    """Verify the sample data values that should be loaded"""
    
    print("\n🎯 SAMPLE DATA VERIFICATION")
    print("=" * 40)
    print("When 'Load Sample Data' is clicked, these values should populate:")
    print()
    print("📊 INCOME:")
    print("   • Gross Salary: £45,000")
    print("   • Bonuses: £3,000")
    print("   • Freelance: £800")
    print("   • Dividends: £150")
    print("   • Other Income: £200")
    print()
    print("💳 EXPENSES:")
    print("   • Rent/Mortgage: £1,100")
    print("   • Transport: £280")
    print("   • Groceries: £350")
    print("   • Utilities: £120")
    print("   • Home Insurance: £85")
    print("   • Entertainment: £180")
    print()
    print("🏠 ASSETS:")
    print("   • Home Value: £220,000")
    print("   • Savings: £8,500")
    print("   • Investments: £12,000")
    print("   • Other Assets: £3,000")
    print()
    print("💸 DEBTS:")
    print("   • Mortgage Balance: £180,000 @ 3.2% (23 years)")
    print("   • Credit Cards: £3,200 @ 19.9%")
    print("   • Personal Loans: £8,500 @ 7.5%")
    print("   • Student Loans: £12,000 @ 4.2%")
    print("   • Other Debts: £1,500 @ 11.5%")
    print()
    print("📈 EXPECTED PORTFOLIO PERFORMANCE:")
    print("   • Current Net Worth: ~£38,300")
    print("   • Monthly Cash Flow: ~£1,805")
    print("   • 5-Year Net Worth: ~£206,331")
    print("   • Debt-to-Income Ratio: ~21.8%")

def check_terminal_output():
    """Instructions for checking debug output"""
    
    print("\n🔍 DEBUG OUTPUT VERIFICATION")
    print("=" * 40)
    print("After loading sample data, check the terminal running the app for:")
    print()
    print("Expected debug output:")
    print("   DEBUG: Portfolio callback triggered - save_clicks: X, sample_clicks: Y")
    print("   DEBUG: Sample data - gross_salary: 45000, home_value: 220000")
    print()
    print("If you don't see debug output, the callback may not be triggering.")
    print("Common issues:")
    print("   • Modal didn't save data properly")
    print("   • Callback input/output IDs don't match form field IDs")
    print("   • JavaScript errors preventing callback execution")

if __name__ == "__main__":
    success = test_app_functionality()
    if success:
        verify_sample_data()
        check_terminal_output()
        print("\n✅ App test completed successfully!")
    else:
        print("\n❌ App test failed - check app status")
