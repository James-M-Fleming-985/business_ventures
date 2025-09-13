"""
Module for economic climate analysis and scenario recommendations.
"""
import requests
import pandas as pd
import numpy as np
from datetime import datetime
import json
import os

# Cache directory for economic data
CACHE_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data', 'cache')
os.makedirs(CACHE_DIR, exist_ok=True)

def get_economic_data(region):
    """
    Fetch economic data for the specified region.
    Uses World Bank API for consistent shared data.
    
    Args:
        region (str): Region code ('UK', 'EU', 'US', 'ASIA', 'IN')
        
    Returns:
        dict: Economic indicators including GDP growth, inflation, unemployment
    """
    # Map regions to World Bank country codes
    region_mapping = {
        'UK': 'GBR',
        'EU': 'EUU',  # European Union
        'US': 'USA',
        'ASIA': 'EAS',  # East Asia & Pacific
        'IN': 'IND'
    }
    
    # Cache file path
    cache_file = os.path.join(CACHE_DIR, f"{region.lower()}_economic_data.json")
    
    # Check if we have cached data less than 24 hours old
    if os.path.exists(cache_file):
        file_age = datetime.now().timestamp() - os.path.getmtime(cache_file)
        if file_age < 86400:  # 24 hours in seconds
            with open(cache_file, 'r') as f:
                return json.load(f)
    
    # If no cached data or old, fetch new data
    try:
        country_code = region_mapping.get(region, 'GBR')  # Default to UK if region not found
        
        # World Bank API endpoints for different indicators
        indicators = {
            'gdp_growth': 'NY.GDP.MKTP.KD.ZG',  # GDP growth (annual %)
            'inflation': 'FP.CPI.TOTL.ZG',      # Inflation, consumer prices (annual %)
            'unemployment': 'SL.UEM.TOTL.ZS',   # Unemployment, total (% of labor force)
            'interest_rate': 'FR.INR.LEND',     # Lending interest rate (%)
            'business_confidence': 'IC.BUS.EASE.XQ'  # Ease of doing business index
        }
        
        # Get the most recent data for each indicator
        data = {}
        for key, indicator in indicators.items():
            url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/{indicator}?format=json&per_page=5&mrnev=1"
            response = requests.get(url, timeout=10)
            
            if response.status_code == 200:
                response_data = response.json()
                if response_data and len(response_data) > 1 and response_data[1]:
                    # Extract the most recent value and year
                    most_recent = next((item for item in response_data[1] if item['value'] is not None), None)
                    if most_recent:
                        data[key] = {
                            'value': most_recent['value'],
                            'year': most_recent['date']
                        }
                    else:
                        data[key] = {'value': None, 'year': None}
                else:
                    data[key] = {'value': None, 'year': None}
            else:
                data[key] = {'value': None, 'year': None}
                
        # Save to cache
        with open(cache_file, 'w') as f:
            json.dump(data, f)
            
        return data
        
    except Exception as e:
        print(f"Error fetching economic data: {e}")
        # Return simulated data if API fails
        return generate_simulated_economic_data(region)

def generate_simulated_economic_data(region):
    """
    Generate simulated economic data when API is unavailable.
    Based on generally accepted recent values.
    
    Args:
        region (str): Region code
        
    Returns:
        dict: Simulated economic indicators
    """
    # Default values based on recent shared averages (as of 2023)
    defaults = {
        'UK': {'gdp_growth': 1.2, 'inflation': 4.0, 'unemployment': 3.8, 'interest_rate': 5.25, 'business_confidence': 78},
        'EU': {'gdp_growth': 0.8, 'inflation': 2.9, 'unemployment': 6.0, 'interest_rate': 4.0, 'business_confidence': 75},
        'US': {'gdp_growth': 2.5, 'inflation': 3.7, 'unemployment': 3.7, 'interest_rate': 5.5, 'business_confidence': 82},
        'ASIA': {'gdp_growth': 4.5, 'inflation': 2.2, 'unemployment': 5.2, 'interest_rate': 3.8, 'business_confidence': 68},
        'IN': {'gdp_growth': 6.3, 'inflation': 5.1, 'unemployment': 7.8, 'interest_rate': 6.5, 'business_confidence': 63}
    }
    
    # Get region defaults or use UK as fallback
    region_defaults = defaults.get(region, defaults['UK'])
    current_year = datetime.now().year
    
    # Create simulated data with the current year
    result = {}
    for key, value in region_defaults.items():
        result[key] = {'value': value, 'year': str(current_year)}
    
    return result

def analyze_economic_climate(economic_data):
    """
    Analyze economic data and recommend a scenario type.
    
    Args:
        economic_data (dict): Economic indicators
        
    Returns:
        dict: Analysis results and recommended scenario
    """
    # Extract values from economic data
    try:
        gdp_growth = economic_data['gdp_growth']['value'] 
        inflation = economic_data['inflation']['value']
        unemployment = economic_data['unemployment']['value']
        
        # Calculate economic health score (simple weighted average)
        # Higher GDP growth is good, lower inflation and unemployment are good
        economic_score = (
            (gdp_growth * 0.5) +              # GDP growth (positive impact)
            ((5 - min(inflation, 10)) * 0.3) + # Inflation (negative impact, capped at 10%)
            ((10 - min(unemployment, 20)) * 0.2) # Unemployment (negative impact, capped at 20%)
        )
        
        # Determine scenario based on economic score
        if economic_score >= 7.5:
            scenario = "boom"
            description = "Strong economic growth with controlled inflation. Excellent conditions for investment."
        elif economic_score >= 6:
            scenario = "optimistic"
            description = "Good economic indicators suggesting growth opportunities with moderate risk."
        elif economic_score >= 4:
            scenario = "baseline"
            description = "Stable economic conditions with balanced growth prospects."
        elif economic_score >= 2.5:
            scenario = "pessimistic"
            description = "Economic challenges present with slower growth and higher risks."
        else:
            scenario = "downturn"
            description = "Difficult economic conditions suggesting cautious approach to investments."
        
        return {
            "recommended_scenario": scenario,
            "economic_score": round(economic_score, 1),
            "description": description,
            "indicators": {
                "gdp_growth": gdp_growth,
                "inflation": inflation,
                "unemployment": unemployment
            }
        }
    except (KeyError, TypeError) as e:
        # Fallback to baseline if data is incomplete
        return {
            "recommended_scenario": "baseline",
            "economic_score": 5.0,
            "description": "Using baseline scenario due to incomplete economic data.",
            "indicators": {
                "gdp_growth": economic_data.get('gdp_growth', {}).get('value', 'N/A'),
                "inflation": economic_data.get('inflation', {}).get('value', 'N/A'),
                "unemployment": economic_data.get('unemployment', {}).get('value', 'N/A')
            }
        }