"""
Simplified Data Fetcher for Causal Affect Platform
Uses real APIs to fetch correlation data
"""

import requests
import os
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)


class DataFetcher:
    """Fetch real-world data from working APIs for correlation analysis."""
    
    def __init__(self):
        self.alpha_vantage_key = os.getenv('ALPHA_VANTAGE_API_KEY')
        if not self.alpha_vantage_key:
            logger.critical("⚠️  ALPHA_VANTAGE_API_KEY not set - stock data fetching will fail!")
            logger.critical("   Get a free key at: https://www.alphavantage.co/support/#api-key")
        
        # Initialize FRED client
        self.fred_key = os.getenv('FRED_API_KEY')
        self.fred_client = None
        if self.fred_key:
            try:
                from fredapi import Fred
                self.fred_client = Fred(api_key=self.fred_key)
                logger.info("✅ FRED client initialized")
            except Exception as e:
                logger.error(f"Failed to initialize FRED client: {e}")
        else:
            logger.warning("⚠️  FRED_API_KEY not set - economic data fetching will be limited")
        
        # Initialize Google Trends client (no key needed)
        self.trends_client = None
        try:
            from pytrends.request import TrendReq
            self.trends_client = TrendReq(hl='en-US', tz=360)
            logger.info("✅ Google Trends client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Google Trends client: {e}")
        
    def fetch_stock_data(self, symbol: str, days: int = 30) -> Optional[List[float]]:
        """Fetch stock price data from Alpha Vantage."""
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return None
            
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "apikey": self.alpha_vantage_key,
                "outputsize": "full"  # 20+ years of historical data
            }
            
            response = requests.get(url, params=params, timeout=30)
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
    
    def fetch_stock_data_monthly(
        self, symbol: str, months: int = 300
    ) -> Optional[Dict[str, float]]:
        """
        Fetch monthly stock data (end-of-month closing prices).
        Returns dict of {month_start_date: end_of_month_price}
        Default: 300 months (25 years) for better Granger causality coverage
        """
        if not self.alpha_vantage_key:
            logger.warning("Alpha Vantage API key not configured")
            return None
            
        try:
            url = "https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_MONTHLY",
                "symbol": symbol,
                "apikey": self.alpha_vantage_key
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if "Monthly Time Series" not in data:
                logger.error(f"Unexpected response: {data}")
                return None
            
            # Extract end-of-month prices, convert to first-of-month keys
            time_series = data["Monthly Time Series"]
            monthly_prices = {}
            
            for date_str in sorted(time_series.keys(), reverse=True)[:months]:
                # date_str is like "2025-11-29" (last day of month)
                # Convert to first day of month for consistency
                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                first_of_month = date_obj.replace(day=1).strftime("%Y-%m-%d")
                monthly_prices[first_of_month] = float(
                    time_series[date_str]["4. close"]
                )
            
            return monthly_prices
            
        except Exception as e:
            logger.error(
                f"Error fetching monthly stock data for {symbol}: {e}"
            )
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
    
    def fetch_earthquake_monthly(self, months: int = 60) -> Optional[Dict[str, int]]:
        """
        Fetch monthly earthquake counts (sum of all earthquakes per month).
        Uses USGS Earthquake Catalog API for historical data.
        Returns dict of {month_start_date: total_count}
        """
        try:
            # Calculate date range for historical data
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)
            
            # USGS Earthquake Catalog API (no auth required)
            url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
            params = {
                "format": "geojson",
                "starttime": start_date.strftime("%Y-%m-%d"),
                "endtime": end_date.strftime("%Y-%m-%d"),
                "minmagnitude": 2.5,  # Significant earthquakes only
                "orderby": "time"
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Count earthquakes per month
            monthly_counts = {}
            for feature in data.get("features", []):
                timestamp = feature["properties"]["time"] / 1000
                date_obj = datetime.fromtimestamp(timestamp)
                first_of_month = date_obj.replace(day=1).strftime("%Y-%m-%d")
                monthly_counts[first_of_month] = monthly_counts.get(first_of_month, 0) + 1
            
            logger.info(f"Fetched {len(data.get('features', []))} earthquakes across {len(monthly_counts)} months")
            return monthly_counts
            
        except Exception as e:
            logger.error(f"Error fetching monthly earthquake data: {e}")
            return None
    
    def fetch_earthquake_count_monthly(self, months: int = 60) -> Optional[Dict[str, int]]:
        """
        Fetch monthly earthquake counts for correlation analysis.
        Returns dict of {month_start_date: total_earthquakes}
        Uses USGS Earthquake Catalog API for full historical data.
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)
            
            url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
            params = {
                "format": "geojson",
                "starttime": start_date.strftime("%Y-%m-%d"),
                "endtime": end_date.strftime("%Y-%m-%d"),
                "minmagnitude": 2.5,
                "orderby": "time"
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Count earthquakes per month
            monthly_counts = {}
            for feature in data.get("features", []):
                timestamp = feature["properties"]["time"] / 1000
                date = datetime.fromtimestamp(timestamp)
                month_start = date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                month_key = month_start.strftime("%Y-%m-%d")
                monthly_counts[month_key] = monthly_counts.get(month_key, 0) + 1
            
            logger.info(f"Fetched earthquake data for {len(monthly_counts)} months")
            return monthly_counts
            
        except Exception as e:
            logger.error(f"Error fetching monthly earthquake data: {e}")
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
    
    def fetch_gdp_monthly(self, country_code: str = "USA") -> Optional[Dict[str, float]]:
        """
        Fetch GDP data and forward-fill to monthly frequency.
        GDP is reported annually, so we spread each year's value across 12 months.
        Returns dict of {month_start_date: gdp_value}
        """
        try:
            # Dynamic date range: get last 10 years of data
            current_year = datetime.now().year
            start_year = current_year - 10
            
            url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.MKTP.CD"
            params = {
                "format": "json",
                "date": f"{start_year}:{current_year}",
                "per_page": 100
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if len(data) < 2 or not isinstance(data[1], list):
                return None
            
            # Extract annual values
            annual_data = {}
            for item in data[1]:
                if item.get("value"):
                    year = int(item["date"])
                    annual_data[year] = float(item["value"])
            
            # Forward-fill to monthly
            monthly_data = {}
            for year in sorted(annual_data.keys()):
                gdp_value = annual_data[year]
                # Create 12 monthly entries for this year
                for month in range(1, 13):
                    date_key = f"{year}-{month:02d}-01"
                    monthly_data[date_key] = gdp_value
            
            return monthly_data
            
        except Exception as e:
            logger.error(f"Error fetching monthly GDP data: {e}")
            return None
    
    def fetch_gdp_data_monthly(self, country_code: str = "USA") -> Optional[Dict[str, float]]:
        """
        Fetch GDP data and forward-fill to monthly frequency.
        Returns dict of {month_start_date: gdp_value}
        GDP is annual, so each year's value is repeated for 12 months.
        """
        try:
            # Dynamic date range: get last 10 years of data
            current_year = datetime.now().year
            start_year = current_year - 10
            
            url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.MKTP.CD"
            params = {
                "format": "json",
                "date": f"{start_year}:{current_year}",
                "per_page": 100
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if len(data) < 2 or not isinstance(data[1], list):
                return None
            
            # Extract annual values
            annual_data = {}
            for item in data[1]:
                if item.get("value"):
                    year = int(item["date"])
                    annual_data[year] = float(item["value"])
            
            # Forward-fill to monthly
            monthly_data = {}
            for year in sorted(annual_data.keys()):
                gdp_value = annual_data[year]
                for month in range(1, 13):  # Jan=1, Dec=12
                    month_start = datetime(year, month, 1)
                    month_key = month_start.strftime("%Y-%m-%d")
                    monthly_data[month_key] = gdp_value
            
            logger.info(f"Fetched GDP data for {country_code}: {len(annual_data)} years -> {len(monthly_data)} months")
            return monthly_data
            
        except Exception as e:
            logger.error(f"Error fetching monthly GDP data: {e}")
            return None
    
    def fetch_arxiv_papers_monthly(self, topic: str, months: int = 60) -> Optional[Dict[str, int]]:
        """
        Fetch monthly counts of arXiv papers on a topic.
        Queries arXiv API for papers submitted in each month.
        Returns dict of {month_start_date: paper_count}
        """
        try:
            monthly_counts = {}
            end_date = datetime.now()
            
            # Query each month individually (arXiv API limitation)
            for i in range(months):
                month_start = end_date - timedelta(days=(months - i) * 30)
                month_end = month_start + timedelta(days=30)
                
                # Format dates for arXiv API
                start_str = month_start.strftime("%Y%m%d")
                end_str = month_end.strftime("%Y%m%d")
                
                url = "http://export.arxiv.org/api/query"
                params = {
                    "search_query": f"all:{topic} AND submittedDate:[{start_str} TO {end_str}]",
                    "start": 0,
                    "max_results": 1  # We only need the count
                }
                
                try:
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    
                    # Extract total results from feed
                    import xml.etree.ElementTree as ET
                    root = ET.fromstring(response.content)
                    ns = {'opensearch': 'http://a9.com/-/spec/opensearch/1.1/'}
                    total = root.find('.//opensearch:totalResults', ns)
                    count = int(total.text) if total is not None else 0
                    
                    # Store with month start date
                    month_key = month_start.replace(day=1).strftime("%Y-%m-%d")
                    monthly_counts[month_key] = count
                    
                except Exception as e:
                    logger.warning(f"Error fetching arXiv for {month_start.strftime('%Y-%m')}: {e}")
                    continue
            
            logger.info(f"Fetched arXiv '{topic}' data for {len(monthly_counts)} months")
            return monthly_counts
            
        except Exception as e:
            logger.error(f"Error fetching monthly arXiv data: {e}")
            return None
    
    def fetch_clinical_trials_monthly(self, condition: str, months: int = 60) -> Optional[Dict[str, int]]:
        """
        Fetch monthly counts of clinical trials for a condition.
        Queries ClinicalTrials.gov API for trials started in each month.
        Returns dict of {month_start_date: trial_count}
        """
        try:
            monthly_counts = {}
            end_date = datetime.now()
            
            # Query each month
            for i in range(months):
                month_start = end_date - timedelta(days=(months - i) * 30)
                month_end = month_start + timedelta(days=30)
                
                url = "https://clinicaltrials.gov/api/v2/studies"
                params = {
                    "query.cond": condition,
                    "filter.advanced": f"AREA[StartDate]RANGE[{month_start.strftime('%m/%d/%Y')}, {month_end.strftime('%m/%d/%Y')}]",
                    "pageSize": 1
                }
                
                try:
                    response = requests.get(url, params=params, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                    
                    count = data.get("totalCount", 0)
                    month_key = month_start.replace(day=1).strftime("%Y-%m-%d")
                    monthly_counts[month_key] = count
                    
                except Exception as e:
                    logger.warning(f"Error fetching trials for {month_start.strftime('%Y-%m')}: {e}")
                    continue
            
            logger.info(f"Fetched clinical trials '{condition}' data for {len(monthly_counts)} months")
            return monthly_counts
            
        except Exception as e:
            logger.error(f"Error fetching monthly clinical trials data: {e}")
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
    
    def fetch_environmental_events_monthly(self, months: int = 60) -> Optional[Dict[str, Dict[str, int]]]:
        """
        Fetch monthly environmental event counts from NASA EONET.
        Returns dict of {category_title: {month_start_date: count}}
        
        Args:
            months: Number of months of historical data to fetch
            
        Returns:
            Nested dict mapping category names to monthly counts
            e.g., {"Wildfires": {"2025-01-01": 15, "2025-02-01": 12, ...}, ...}
        """
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)
            
            # NASA EONET API with date range
            url = "https://eonet.gsfc.nasa.gov/api/v3/events"
            params = {
                "start": start_date.strftime("%Y-%m-%d"),
                "end": end_date.strftime("%Y-%m-%d"),
                "limit": 10000  # Get all events in range
            }
            
            logger.info(f"Fetching EONET events from {params['start']} to {params['end']}...")
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            events = data.get("events", [])
            logger.info(f"Found {len(events)} environmental events")
            
            # Count events by category and month
            # Structure: {category: {month: count}}
            category_monthly_counts = {}
            
            for event in events:
                # Get event start date from first geometry
                geometries = event.get("geometry", [])
                if not geometries:
                    continue
                    
                event_date_str = geometries[0].get("date")
                if not event_date_str:
                    continue
                
                # Parse date and normalize to first of month
                try:
                    event_date = datetime.fromisoformat(event_date_str.replace('Z', '+00:00'))
                    month_start = event_date.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
                    month_key = month_start.strftime("%Y-%m-%d")
                except:
                    continue
                
                # Count by category
                for category in event.get("categories", []):
                    cat_title = category.get("title", "Unknown")
                    
                    if cat_title not in category_monthly_counts:
                        category_monthly_counts[cat_title] = {}
                    
                    if month_key not in category_monthly_counts[cat_title]:
                        category_monthly_counts[cat_title][month_key] = 0
                    
                    category_monthly_counts[cat_title][month_key] += 1
            
            # Log summary
            for category, monthly_data in category_monthly_counts.items():
                logger.info(f"{category}: {len(monthly_data)} months of data")
            
            return category_monthly_counts
            
        except Exception as e:
            logger.error(f"Error fetching monthly environmental events: {e}")
            return None
    
    def fetch_gdp_data_annual(self, country_code: str, years: int = 20) -> Optional[Dict[str, float]]:
        """
        Fetch annual GDP data from World Bank API.
        Returns dict of {year: gdp_value}
        
        Args:
            country_code: ISO3 country code (e.g., 'USA', 'DEU', 'JPN')
            years: Number of years to fetch (default 20)
        """
        try:
            # World Bank API endpoint
            current_year = datetime.now().year
            start_year = current_year - years
            
            url = f"https://api.worldbank.org/v2/country/{country_code}/indicator/NY.GDP.MKTP.CD"
            params = {
                'format': 'json',
                'date': f'{start_year}:{current_year}',
                'per_page': 100
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()
            
            if len(data) < 2:
                logger.error(f"Unexpected response format from World Bank API")
                return None
            
            # Parse GDP data
            gdp_data = {}
            for record in data[1]:  # Second element contains the data
                year = record.get('date')
                value = record.get('value')
                
                if year and value is not None:
                    # Store as year string for consistency
                    gdp_data[year] = float(value)
            
            logger.info(f"Fetched {len(gdp_data)} years of GDP data for {country_code}")
            return gdp_data
            
        except Exception as e:
            logger.error(f"Error fetching GDP data for {country_code}: {e}")
            return None

    def fetch_google_trends_monthly(self, keyword: str, months: int = 300) -> Optional[Dict[str, float]]:
        """
        Fetch Google Trends monthly search volume for a keyword.
        Returns dict of {"YYYY-MM-01": search_volume}
        
        Args:
            keyword: Search keyword (e.g., "wedding planning", "moving companies")
            months: Number of months to fetch (default 300 = 25 years)
        """
        if not self.trends_client:
            logger.error("Google Trends client not initialized")
            return None
        
        try:
            from dateutil.relativedelta import relativedelta
            import time
            import pandas as pd
            
            # Split into smaller chunks to avoid rate limiting
            # Google Trends allows max 5 years per request without issues
            chunk_months = 60  # 5 years per chunk
            all_data = {}
            
            end_date = datetime.now()
            remaining_months = months
            current_end = end_date
            
            while remaining_months > 0:
                chunk_size = min(chunk_months, remaining_months)
                current_start = current_end - relativedelta(months=chunk_size)
                
                timeframe = f"{current_start.strftime('%Y-%m-%d')} {current_end.strftime('%Y-%m-%d')}"
                
                max_retries = 3
                for attempt in range(max_retries):
                    try:
                        # Add delay between chunks to avoid rate limiting
                        if len(all_data) > 0:
                            time.sleep(3)  # 3 seconds between chunks
                        
                        # Reinitialize client on retry
                        if attempt > 0:
                            wait_time = (attempt + 1) * 10
                            logger.info(f"Waiting {wait_time}s before retry {attempt + 1}...")
                            time.sleep(wait_time)
                            from pytrends.request import TrendReq
                            self.trends_client = TrendReq(hl='en-US', tz=360, timeout=(10, 25))
                        
                        self.trends_client.build_payload([keyword], timeframe=timeframe)
                        df = self.trends_client.interest_over_time()
                        
                        if df is not None and not df.empty:
                            for index, row in df.iterrows():
                                month_key = index.strftime('%Y-%m-01')
                                all_data[month_key] = float(row[keyword])
                        
                        break  # Success, move to next chunk
                        
                    except Exception as e:
                        if '429' in str(e) and attempt < max_retries - 1:
                            logger.warning(f"Rate limited on attempt {attempt + 1} for chunk, will retry...")
                            continue
                        elif attempt == max_retries - 1:
                            logger.error(f"Failed to fetch chunk after {max_retries} attempts: {e}")
                            # Continue to next chunk rather than failing completely
                            break
                
                # Move to next chunk
                remaining_months -= chunk_size
                current_end = current_start - relativedelta(days=1)
            
            if all_data:
                logger.info(f"Fetched {len(all_data)} months of Google Trends data for '{keyword}' across {months//chunk_months + 1} chunks")
                return all_data
            else:
                logger.warning(f"No Google Trends data found for keyword: {keyword}")
                return None
            
        except Exception as e:
            logger.error(f"Error fetching Google Trends for '{keyword}': {e}")
            return None

    def fetch_fred_indicator(self, indicator_code: str, months: int = 300) -> Optional[Dict[str, float]]:
        """
        Fetch economic indicator from FRED (Federal Reserve Economic Data).
        Returns dict of {"YYYY-MM-01": indicator_value}
        
        Args:
            indicator_code: FRED indicator code (e.g., "UNRATE" for unemployment)
            months: Number of months to fetch (default 300 = 25 years)
        """
        if not self.fred_client:
            logger.error("FRED client not initialized (missing FRED_API_KEY)")
            return None
        
        try:
            from dateutil.relativedelta import relativedelta
            
            end_date = datetime.now()
            start_date = end_date - relativedelta(months=months)
            
            # Fetch data
            series = self.fred_client.get_series(
                indicator_code,
                observation_start=start_date.strftime('%Y-%m-%d'),
                observation_end=end_date.strftime('%Y-%m-%d')
            )
            
            if series is None or series.empty:
                logger.warning(f"No FRED data found for indicator: {indicator_code}")
                return None
            
            # Convert to monthly dict
            fred_data = {}
            for index, value in series.items():
                # Normalize to first of month
                month_key = index.strftime('%Y-%m-01')
                fred_data[month_key] = float(value)
            
            logger.info(f"Fetched {len(fred_data)} months of FRED data for '{indicator_code}'")
            return fred_data
            
        except Exception as e:
            logger.error(f"Error fetching FRED indicator '{indicator_code}': {e}")
            return None

    def fetch_usgs_earthquakes_monthly(self, region: str = "global", months: int = 300) -> Optional[Dict[str, Dict[str, float]]]:
        """
        Fetch earthquake data from USGS and aggregate by month.
        Returns dict of {"YYYY-MM-01": {"count": X, "avg_magnitude": Y, "max_magnitude": Z}}
        
        Args:
            region: Region filter ("global", "us", "california") - default global
            months: Number of months to fetch (default 300 = 25 years)
        """
        try:
            from dateutil.relativedelta import relativedelta
            from collections import defaultdict
            
            end_date = datetime.now()
            start_date = end_date - relativedelta(months=months)
            
            # USGS Earthquake API
            url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
            params = {
                'format': 'geojson',
                'starttime': start_date.strftime('%Y-%m-%d'),
                'endtime': end_date.strftime('%Y-%m-%d'),
                'minmagnitude': 4.0,  # Only significant earthquakes
                'orderby': 'time'
            }
            
            # Add region-specific filters
            if region == "us":
                params.update({
                    'minlatitude': 24.0,
                    'maxlatitude': 50.0,
                    'minlongitude': -125.0,
                    'maxlongitude': -65.0
                })
            elif region == "california":
                params.update({
                    'minlatitude': 32.5,
                    'maxlatitude': 42.0,
                    'minlongitude': -124.5,
                    'maxlongitude': -114.0
                })
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Aggregate by month
            monthly_data = defaultdict(lambda: {'magnitudes': []})
            
            for feature in data.get('features', []):
                props = feature.get('properties', {})
                timestamp = props.get('time')
                magnitude = props.get('mag')
                
                if timestamp and magnitude:
                    # Convert timestamp to month key
                    dt = datetime.fromtimestamp(timestamp / 1000)  # USGS uses milliseconds
                    month_key = dt.strftime('%Y-%m-01')
                    monthly_data[month_key]['magnitudes'].append(magnitude)
            
            # Calculate aggregates
            earthquake_data = {}
            for month_key, data in monthly_data.items():
                mags = data['magnitudes']
                earthquake_data[month_key] = {
                    'count': float(len(mags)),
                    'avg_magnitude': float(sum(mags) / len(mags)),
                    'max_magnitude': float(max(mags))
                }
            
            logger.info(f"Fetched {len(earthquake_data)} months of USGS earthquake data ({region})")
            return earthquake_data
            
        except Exception as e:
            logger.error(f"Error fetching USGS earthquake data: {e}")
            return None
    def fetch_wikipedia_pageviews_monthly(self, article: str, months: int = 60) -> Optional[Dict[str, float]]:
        """
        Fetch Wikipedia pageviews data (LAYER 1: FAST BEHAVIORAL SIGNALS).
        Returns dict of {"YYYY-MM-01": monthly_pageviews}
        
        This is a FREE API with no rate limits - replaces Google Trends!
        
        Args:
            article: Wikipedia article title (e.g., "Bitcoin", "Artificial_intelligence")
            months: Number of months to fetch (default 60 = 5 years)
        
        Returns:
            Dict mapping month to total pageviews for that month
        """
        try:
            from dateutil.relativedelta import relativedelta
            from collections import defaultdict
            
            end_date = datetime.now()
            start_date = end_date - relativedelta(months=months)
            
            # Wikipedia Pageviews API (free, no rate limits)
            # https://wikimedia.org/api/rest_v1/metrics/pageviews/
            url = f"https://wikimedia.org/api/rest_v1/metrics/pageviews/per-article/en.wikipedia/all-access/all-agents/{article}/monthly/{start_date.strftime('%Y%m')}01/{end_date.strftime('%Y%m')}01"
            
            headers = {
                'User-Agent': 'CausalAffectPlatform/1.0 (business_ventures; data analysis)'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 404:
                logger.warning(f"Wikipedia article not found: {article}")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # Parse monthly data
            pageview_data = {}
            for item in data.get('items', []):
                # Format: YYYYMMDDHH -> YYYY-MM-01
                timestamp_str = item.get('timestamp', '')
                if len(timestamp_str) >= 8:
                    year = timestamp_str[:4]
                    month = timestamp_str[4:6]
                    month_key = f"{year}-{month}-01"
                    pageview_data[month_key] = float(item.get('views', 0))
            
            logger.info(f"Fetched {len(pageview_data)} months of Wikipedia pageviews for '{article}'")
            return pageview_data
            
        except Exception as e:
            logger.error(f"Error fetching Wikipedia pageviews for '{article}': {e}")
            return None

    def fetch_reddit_activity_monthly(self, subreddit: str, months: int = 60) -> Optional[Dict[str, Dict[str, float]]]:
        """
        Fetch Reddit activity metrics (LAYER 1: FAST BEHAVIORAL SIGNALS).
        Uses Pushshift/Reddit API to get post/comment counts.
        
        Args:
            subreddit: Subreddit name (e.g., "personalfinance", "technology")
            months: Number of months to fetch
        
        Returns:
            Dict mapping month to {posts: X, comments: Y, score_avg: Z}
            
        NOTE: Reddit API has restrictions. For production, consider:
        - Reddit Developer Account (free, 100 requests/minute)
        - Pullpush.io (pushshift.io replacement)
        """
        try:
            # For now, use Reddit's public JSON endpoint
            # This is rate-limited but works for basic data
            url = f"https://www.reddit.com/r/{subreddit}/top.json?t=all&limit=100"
            
            headers = {
                'User-Agent': 'CausalAffectPlatform/1.0'
            }
            
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 429:
                logger.warning(f"Reddit rate limit hit for r/{subreddit}")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            # This is a simplified implementation - for full history would need Pushshift
            # For now, return None and log that full implementation is needed
            logger.info(f"Reddit API connected for r/{subreddit} - full implementation pending")
            
            # Return placeholder indicating API works but needs full implementation
            return None
            
        except Exception as e:
            logger.error(f"Error fetching Reddit data for r/{subreddit}: {e}")
            return None

    def fetch_github_repo_stars_monthly(self, repo: str, months: int = 60) -> Optional[Dict[str, float]]:
        """
        Fetch GitHub repository star history (LAYER 1: FAST BEHAVIORAL SIGNALS).
        Uses GitHub API to track star growth over time.
        
        Args:
            repo: Repository in format "owner/repo" (e.g., "facebook/react")
            months: Number of months to fetch
        
        Returns:
            Dict mapping month to cumulative star count
            
        NOTE: GitHub API is rate-limited (60 requests/hour unauthenticated)
        For production, use GITHUB_TOKEN for 5000 requests/hour
        """
        try:
            github_token = os.getenv('GITHUB_TOKEN')
            
            headers = {
                'Accept': 'application/vnd.github.v3+json',
                'User-Agent': 'CausalAffectPlatform/1.0'
            }
            
            if github_token:
                headers['Authorization'] = f'token {github_token}'
            
            # Get repo info
            url = f"https://api.github.com/repos/{repo}"
            response = requests.get(url, headers=headers, timeout=30)
            
            if response.status_code == 404:
                logger.warning(f"GitHub repo not found: {repo}")
                return None
            
            if response.status_code == 403:
                logger.warning(f"GitHub rate limit hit for {repo}")
                return None
            
            response.raise_for_status()
            data = response.json()
            
            current_stars = data.get('stargazers_count', 0)
            created_at = datetime.strptime(data.get('created_at', '2020-01-01T00:00:00Z')[:10], '%Y-%m-%d')
            
            # Note: Full star history requires GitHub GraphQL API with pagination
            # For now, return current stars as a point-in-time snapshot
            today = datetime.now()
            month_key = today.strftime('%Y-%m-01')
            
            logger.info(f"GitHub {repo}: {current_stars} stars (snapshot)")
            
            return {month_key: float(current_stars)}
            
        except Exception as e:
            logger.error(f"Error fetching GitHub stars for '{repo}': {e}")
            return None