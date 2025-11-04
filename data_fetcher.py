"""
Simplified Data Fetcher for Causal Affect Platform
Uses real APIs to fetch correlation data
"""

import requests
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


class DataFetcher:
    """Fetch real-world data from working APIs for correlation analysis."""
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        
    def fetch_stock_data(self, symbol: str, days: int = 30) -> Optional[List[float]]:
        """Fetch stock price data from Alpha Vantage."""
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return None
            
        try:
            url = f"https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "apikey": self.alpha_vantage_key,
                "outputsize": "compact"  # Last 100 days
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if "Time Series (Daily)" not in data:
                logger.error(f"Unexpected response: {data}")
                return None
            
            # Extract closing prices, most recent first
            time_series = data["Time Series (Daily)"]
            prices = []
            for date in sorted(time_series.keys(), reverse=True)[:days]:
                prices.append(float(time_series[date]["4. close"]))
            
            prices.reverse()  # Oldest to newest
            return prices
            
        except Exception as e:
            logger.error(f"Error fetching stock data for {symbol}: {e}")
            return None
    
    def fetch_earthquake_count(self, days: int = 30) -> Optional[List[int]]:
        """Fetch daily earthquake counts from USGS."""
        try:
            url = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/all_month.geojson"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Count earthquakes per day
            daily_counts = {}
            for feature in data.get("features", []):
                timestamp = feature["properties"]["time"] / 1000  # Convert from ms
                date = datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d")
                daily_counts[date] = daily_counts.get(date, 0) + 1
            
            # Get last N days
            end_date = datetime.now()
            counts = []
            for i in range(days):
                date = (end_date - timedelta(days=days-i-1)).strftime("%Y-%m-%d")
                counts.append(daily_counts.get(date, 0))
            
            return counts
            
        except Exception as e:
            logger.error(f"Error fetching earthquake data: {e}")
            return None
    
    def fetch_environmental_events(self, days: int = 30) -> Optional[Dict[str, int]]:
        """Fetch environmental event counts from NASA EONET."""
        try:
            url = "https://eonet.gsfc.nasa.gov/api/v3/events"
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            # Count events by category
            categories = {}
            for event in data.get("events", []):
                for category in event.get("categories", []):
                    cat_title = category.get("title", "Unknown")
                    categories[cat_title] = categories.get(cat_title, 0) + 1
            
            return categories
            
        except Exception as e:
            logger.error(f"Error fetching environmental events: {e}")
            return None
    
    def fetch_gdp_data(self, country_code: str = "USA") -> Optional[List[float]]:
        """Fetch GDP data from World Bank."""
        try:
            url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.MKTP.CD"
            params = {
                "format": "json",
                "date": "2015:2023",
                "per_page": 100
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if len(data) < 2 or not isinstance(data[1], list):
                return None
            
            # Extract values, oldest to newest
            values = []
            for item in reversed(data[1]):
                if item.get("value"):
                    values.append(float(item["value"]))
            
            return values
            
        except Exception as e:
            logger.error(f"Error fetching GDP data: {e}")
            return None
    
    def fetch_arxiv_papers(self, topic: str = "artificial intelligence", max_results: int = 100) -> Optional[int]:
        """Fetch count of arXiv papers on a topic."""
        try:
            url = "http://export.arxiv.org/api/query"
            params = {
                "search_query": f"all:{topic}",
                "start": 0,
                "max_results": max_results
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            # Count entries in response
            count = response.text.count("<entry>")
            return count
            
        except Exception as e:
            logger.error(f"Error fetching arXiv data: {e}")
            return None
    
    def fetch_clinical_trials(self, condition: str = "Cancer") -> Optional[int]:
        """Fetch count of clinical trials for a condition."""
        try:
            url = "https://clinicaltrials.gov/api/v2/studies"
            params = {
                "query.cond": condition,
                "pageSize": 1
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            return data.get("totalCount", 0)
            
        except Exception as e:
            logger.error(f"Error fetching clinical trials: {e}")
            return None
    
    def get_sample_correlation_data(self) -> Dict[str, List[float]]:
        """Get sample data demonstrating real API capabilities."""
        result = {}
        
        # Try to fetch real stock data
        tech_stocks = self.fetch_stock_data("NVDA", days=30)
        if tech_stocks:
            result["nvidia_stock"] = tech_stocks
        
        # Try to fetch earthquake data
        earthquakes = self.fetch_earthquake_count(days=30)
        if earthquakes:
            result["earthquake_count"] = earthquakes
        
        # If no real data, use synthetic example
        if not result:
            result = {
                "ice_cream_sales": [100, 120, 140, 160, 180, 200, 220, 240],
                "temperature": [70, 75, 80, 85, 90, 95, 98, 100]
            }
        
        return result
