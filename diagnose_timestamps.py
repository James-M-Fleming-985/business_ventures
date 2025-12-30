#!/usr/bin/env python3
"""
Diagnose timestamp alignment issues between variables
"""
import requests

BASE_URL = "https://businessventures-production.up.railway.app"

print("=" * 80)
print("TIMESTAMP ALIGNMENT DIAGNOSTIC")
print("=" * 80)

# Get sample timeseries for a few variables
response = requests.get(f"{BASE_URL}/api/dashboard/timeseries?limit=10")
data = response.json()

if 'series' in data:
    series_list = data['series']
    print(f"\nFound {len(series_list)} time series")
    
    for s in series_list[:5]:
        name = s.get('name', 'Unknown')
        dates = s.get('dates', [])
        values = s.get('values', [])
        
        print(f"\n{name}:")
        print(f"  Total points: {len(dates)}")
        if dates:
            print(f"  First date: {dates[0]}")
            print(f"  Last date: {dates[-1]}")
            print(f"  Sample dates: {dates[:3]}")
else:
    print("No series data returned")
    print(data)
