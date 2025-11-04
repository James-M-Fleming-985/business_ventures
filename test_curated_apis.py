#!/usr/bin/env python3
"""
Test all 13 Curated APIs for Causal Affect Platform
Tests both authenticated and open APIs
"""

import requests
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_api(name, test_func, category):
    """Helper function to test an API and report results"""
    try:
        result = test_func()
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {status} - {name}")
        return result
    except Exception as e:
        print(f"  ❌ ERROR - {name}: {str(e)[:80]}")
        return False

def main():
    print("\n" + "="*70)
    print("🧪 TESTING CAUSAL AFFECT API STACK (13 APIs)")
    print("="*70 + "\n")

    results = {"passed": 0, "failed": 0, "total": 13}

    # ===== TIER 1: POLITICAL & ECONOMIC =====
    print("📊 TIER 1: Political & Economic Data")
    
    # 1. FRED - Economic Data (REQUIRES KEY - SKIP FOR NOW)
    fred_key = os.getenv('FRED_API_KEY')
    if fred_key:
        def test_fred():
            r = requests.get(f'https://api.stlouisfed.org/fred/series/observations?series_id=UNRATE&api_key={fred_key}&file_type=json&limit=5')
            return r.status_code == 200
        if test_api("FRED (Unemployment Rate)", test_fred, "economic"):
            results["passed"] += 1
        else:
            results["failed"] += 1
    else:
        print("  ⏩ SKIP - FRED (No API key - collect later)")
        results["failed"] += 1

    # 2. World Bank - No key needed
    def test_worldbank():
        r = requests.get('https://api.worldbank.org/v2/country/USA/indicator/NY.GDP.MKTP.CD?format=json&date=2020:2023')
        return r.status_code == 200 and r.json()
    if test_api("World Bank (US GDP)", test_worldbank, "economic"):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # 3. Alpha Vantage - Markets
    av_key = os.getenv('ALPHA_VANTAGE_API_KEY')
    if av_key:
        def test_alphavantage():
            r = requests.get(f'https://www.alphavantage.co/query?function=TIME_SERIES_DAILY&symbol=IBM&apikey={av_key}')
            data = r.json()
            return r.status_code == 200 and 'Time Series (Daily)' in data
        if test_api("Alpha Vantage (IBM Stock)", test_alphavantage, "financial"):
            results["passed"] += 1
        else:
            results["failed"] += 1
    else:
        print("  ❌ FAIL - Alpha Vantage (No API key)")
        results["failed"] += 1

    # 4. US Census - Demographics (works without key)
    def test_census():
        r = requests.get('https://api.census.gov/data/2021/acs/acs1?get=NAME,B01001_001E&for=state:06')
        return r.status_code == 200 and isinstance(r.json(), list)
    if test_api("US Census (Population)", test_census, "demographic"):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # ===== TIER 2: ENVIRONMENTAL & DISASTER =====
    print("\n🌍 TIER 2: Environmental & Disaster Data")

    # 5. OpenWeatherMap - REQUIRES KEY - SKIP FOR NOW
    ow_key = os.getenv('OPENWEATHER_API_KEY')
    if ow_key:
        def test_openweather():
            r = requests.get(f'https://api.openweathermap.org/data/2.5/air_pollution?lat=40.7128&lon=-74.0060&appid={ow_key}')
            return r.status_code == 200
        if test_api("OpenWeather (Air Pollution)", test_openweather, "environmental"):
            results["passed"] += 1
        else:
            results["failed"] += 1
    else:
        print("  ⏩ SKIP - OpenWeather (No API key - collect later)")
        results["failed"] += 1

    # 6. USGS Earthquakes - No key
    def test_usgs():
        r = requests.get('https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_day.geojson')
        data = r.json()
        return r.status_code == 200 and 'features' in data
    if test_api("USGS (Earthquakes 24h)", test_usgs, "disaster"):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # 7. NASA EONET - Environmental Events
    def test_nasa_eonet():
        r = requests.get('https://eonet.gsfc.nasa.gov/api/v3/events')
        data = r.json()
        return r.status_code == 200 and 'events' in data
    if test_api("NASA EONET (Wildfires/Storms)", test_nasa_eonet, "environmental"):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # ===== TIER 3: SOCIAL & GEOPOLITICAL =====
    print("\n📰 TIER 3: Social & Geopolitical Data")

    # 8. Google Trends - No key (requires pytrends library)
    try:
        from pytrends.request import TrendReq
        def test_google_trends():
            pytrends = TrendReq(hl='en-US', tz=360)
            pytrends.build_payload(['artificial intelligence'], timeframe='today 3-m')
            trends_data = pytrends.interest_over_time()
            return not trends_data.empty
        if test_api("Google Trends (AI Interest)", test_google_trends, "social"):
            results["passed"] += 1
        else:
            results["failed"] += 1
    except ImportError:
        print("  ⏩ SKIP - Google Trends (pytrends not installed)")
        results["failed"] += 1

    # 9. GDELT - Optional, skip for now
    print("  ⏩ SKIP - GDELT (Optional - requires BigQuery setup)")
    results["failed"] += 1

    # ===== TIER 4: SCIENCE & ADVANCED MEDICINE =====
    print("\n🔬 TIER 4: Science & Advanced Medicine")

    # 10. PubMed/NIH - Medical Research
    def test_pubmed():
        r = requests.get('https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi?db=pubmed&term=CRISPR&retmax=5&retmode=json')
        data = r.json()
        return r.status_code == 200 and 'esearchresult' in data
    if test_api("PubMed (CRISPR Research)", test_pubmed, "medical"):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # 11. arXiv - Scientific Research
    def test_arxiv():
        r = requests.get('http://export.arxiv.org/api/query?search_query=all:quantum+computing&start=0&max_results=5')
        return r.status_code == 200 and 'entry' in r.text
    if test_api("arXiv (Quantum Computing Papers)", test_arxiv, "scientific"):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # 12. USPTO Patents - Innovation
    def test_uspto():
        r = requests.get('https://developer.uspto.gov/ibd-api/v1/application/grants?searchText=artificial+intelligence&start=0&rows=5')
        return r.status_code == 200
    if test_api("USPTO (AI Patents)", test_uspto, "innovation"):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # 13. ClinicalTrials.gov - Medical Innovation
    def test_clinicaltrials():
        r = requests.get('https://clinicaltrials.gov/api/v2/studies?query.cond=Cancer&query.intr=Immunotherapy&pageSize=5')
        data = r.json()
        return r.status_code == 200 and 'studies' in data
    if test_api("ClinicalTrials.gov (Cancer Immunotherapy)", test_clinicaltrials, "medical"):
        results["passed"] += 1
    else:
        results["failed"] += 1

    # ===== SUMMARY =====
    print("\n" + "="*70)
    print("📊 TEST SUMMARY")
    print("="*70)
    print(f"  Total APIs:  {results['total']}")
    print(f"  ✅ Passed:   {results['passed']}")
    print(f"  ❌ Failed:   {results['failed']}")
    print(f"  Success Rate: {results['passed']/results['total']*100:.1f}%")
    print("="*70 + "\n")

    if results['failed'] > 0:
        print("⚠️  NEXT STEPS TO GET 100%:")
        if not os.getenv('FRED_API_KEY'):
            print("  - Collect FRED API key: https://fred.stlouisfed.org/docs/api/api_key.html")
        if not os.getenv('OPENWEATHER_API_KEY'):
            print("  - Collect OpenWeather API key: https://home.openweathermap.org/users/sign_up")
        print("  - Optional: Setup GDELT via Google BigQuery")
        print()

if __name__ == "__main__":
    main()
