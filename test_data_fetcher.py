#!/usr/bin/env python3
"""
Test the data fetcher methods to see what they actually return
"""
import os
from data_fetcher import DataFetcher
from datetime import datetime

print("=" * 80)
print("DATA FETCHER TEST - Checking what APIs actually return")
print("=" * 80)

fetcher = DataFetcher()

# Test 1: Alpha Vantage Stock Data
print("\n1. Testing Alpha Vantage (Stock Data)")
print("-" * 80)
print(f"API Key set: {'Yes' if fetcher.alpha_vantage_key else 'No'}")

if fetcher.alpha_vantage_key:
    result = fetcher.fetch_stock_data_monthly("NVDA", months=60)
    if result:
        print(f"✓ Got {len(result)} months of NVDA data")
        dates = sorted(result.keys())
        print(f"  Date range: {dates[0]} to {dates[-1]}")
        print(f"  Sample values: {list(result.values())[:3]}")
    else:
        print("✗ No data returned")
else:
    print("✗ API key not configured")

# Test 2: World Bank GDP Data
print("\n2. Testing World Bank (GDP Data)")
print("-" * 80)
result = fetcher.fetch_gdp_data_monthly("POL")  # Poland
if result:
    print(f"✓ Got {len(result)} months of Poland GDP data")
    dates = sorted(result.keys())
    print(f"  Date range: {dates[0]} to {dates[-1]}")
    print(f"  Sample values: {list(result.values())[:3]}")
else:
    print("✗ No data returned")

# Test 3: arXiv Papers
print("\n3. Testing arXiv (Paper Counts)")
print("-" * 80)
print("Note: This makes 60 API calls, may take a minute...")
result = fetcher.fetch_arxiv_papers_monthly("machine learning", months=6)  # Only test 6 months
if result:
    print(f"✓ Got {len(result)} months of ML paper data")
    dates = sorted(result.keys())
    if dates:
        print(f"  Date range: {dates[0]} to {dates[-1]}")
        print(f"  Sample values: {list(result.values())[:3]}")
else:
    print("✗ No data returned")

# Test 4: NASA EONET Environmental Events
print("\n4. Testing NASA EONET (Environmental Events)")
print("-" * 80)
result = fetcher.fetch_environmental_events_monthly(months=60)
if result:
    print(f"✓ Got data for {len(result)} categories")
    for category, monthly_data in list(result.items())[:3]:
        print(f"  {category}: {len(monthly_data)} months")
        dates = sorted(monthly_data.keys())
        if dates:
            print(f"    Date range: {dates[0]} to {dates[-1]}")
else:
    print("✗ No data returned")

# Test 5: USGS Earthquakes
print("\n5. Testing USGS (Earthquake Data)")
print("-" * 80)
result = fetcher.fetch_earthquake_monthly(months=60)
if result:
    print(f"✓ Got {len(result)} months of earthquake data")
    dates = sorted(result.keys())
    print(f"  Date range: {dates[0]} to {dates[-1]}")
    print(f"  Sample values: {list(result.values())[:3]}")
else:
    print("✗ No data returned")

print("\n" + "=" * 80)
print("TEST COMPLETE")
print("=" * 80)
