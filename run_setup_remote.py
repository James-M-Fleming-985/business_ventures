"""
Remote setup trigger - calls Railway API endpoint to run setup
"""
import requests
import time

BASE_URL = "https://businessventures-production.up.railway.app"

print("=" * 60)
print("Triggering setup of 113 new variables on Railway...")
print("=" * 60)

# Create a simple endpoint call that will run the setup
response = requests.post(f"{BASE_URL}/api/admin/setup-new-data-sources", timeout=120)

if response.status_code == 200:
    result = response.json()
    print("\n✅ Setup complete!")
    print(f"\nResults:")
    print(f"- Google Trends: {result.get('trends_added', 0)} variables")
    print(f"- FRED: {result.get('fred_added', 0)} variables")
    print(f"- USGS Enhanced: {result.get('usgs_added', 0)} variables")
    print(f"- Total: {result.get('total_added', 0)} variables")
else:
    print(f"\n❌ Error: {response.status_code}")
    print(response.text)
