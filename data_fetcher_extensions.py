"""
EXTENSION: New Data Sources for Consumer-Focused MVP Opportunities
Add to data_fetcher.py after existing methods
"""

import json
from collections import defaultdict
from dateutil.relativedelta import relativedelta
from pytrends.request import TrendReq
from fredapi import Fred


class DataFetcherExtensions:
    """
    Extensions to DataFetcher class for 6 new consumer-focused data sources.
    Append these methods to the existing DataFetcher class in data_fetcher.py
    """
    
    def __init__(self):
        # Add to existing __init__
        self.openweather_key = os.getenv('OPENWEATHER_API_KEY')
        self.fred_key = os.getenv('FRED_API_KEY')
        
        # Initialize FRED client if key available
        self.fred_client = None
        if self.fred_key:
            try:
                self.fred_client = Fred(api_key=self.fred_key)
            except Exception as e:
                logger.error(f"Failed to initialize FRED client: {e}")
        
        # Initialize Google Trends client (no key needed)
        try:
            self.trends_client = TrendReq(hl='en-US', tz=360)
        except Exception as e:
            logger.error(f"Failed to initialize Google Trends client: {e}")
            self.trends_client = None
    
    # ===== GOOGLE TRENDS =====
    
    def fetch_google_trends_monthly(self, keyword: str, months: int = 300) -> Optional[Dict[str, float]]:
        """
        Fetch Google Trends search volume for a keyword (monthly aggregation).
        
        Args:
            keyword: Search term (e.g., "wedding planning", "moving companies")
            months: Number of months of historical data (default: 300 = 25 years)
            
        Returns:
            Dict mapping "YYYY-MM-01" to search volume index (0-100)
        """
        if not self.trends_client:
            logger.warning("Google Trends client not initialized")
            return None
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - timedelta(days=months * 30)
            
            # Build payload for Google Trends
            self.trends_client.build_payload(
                [keyword],
                timeframe=f'{start_date.strftime("%Y-%m-%d")} {end_date.strftime("%Y-%m-%d")}'
            )
            
            # Get interest over time
            data = self.trends_client.interest_over_time()
            
            if data.empty:
                logger.warning(f"No Google Trends data for keyword: {keyword}")
                return None
            
            # Convert to monthly dict
            trends_data = {}
            for index, row in data.iterrows():
                # Format as YYYY-MM-01
                month_key = index.strftime("%Y-%m-01")
                trends_data[month_key] = float(row[keyword])
            
            logger.info(f"Fetched {len(trends_data)} months of Google Trends data for '{keyword}'")
            return trends_data
            
        except Exception as e:
            logger.error(f"Error fetching Google Trends for '{keyword}': {e}")
            return None
    
    # ===== OPENWEATHER API =====
    
    def fetch_openweather_monthly(self, city: str, months: int = 300) -> Optional[Dict[str, Dict[str, float]]]:
        """
        Fetch weather data aggregated monthly.
        NOTE: Free tier only has 1,000 calls/day. For historical data, use separate historical API.
        
        Args:
            city: City name (e.g., "London", "New York")
            months: Number of months to fetch (limited by API)
            
        Returns:
            Dict with monthly aggregates: {
                "YYYY-MM-01": {
                    "avg_temp": 15.5,
                    "total_rainfall": 80.0,
                    "avg_uv_index": 5.2
                }
            }
        """
        if not self.openweather_key:
            logger.warning("OpenWeather API key not configured")
            return None
        
        try:
            # LIMITATION: OpenWeather free tier doesn't have easy historical monthly aggregates
            # For MVP, we'll use current weather and note this needs historical weather API upgrade
            
            # Get geocoding for city
            geo_url = "http://api.openweathermap.org/geo/1.0/direct"
            geo_params = {
                "q": city,
                "limit": 1,
                "appid": self.openweather_key
            }
            
            geo_response = requests.get(geo_url, params=geo_params, timeout=10)
            geo_response.raise_for_status()
            geo_data = geo_response.json()
            
            if not geo_data:
                logger.error(f"City not found: {city}")
                return None
            
            lat = geo_data[0]['lat']
            lon = geo_data[0]['lon']
            
            # For now, return current month as placeholder
            # TODO: Integrate historical weather API for full time series
            current_month = datetime.now().strftime("%Y-%m-01")
            
            weather_data = {
                current_month: {
                    "avg_temp": 0.0,  # Placeholder
                    "total_rainfall": 0.0,
                    "avg_uv_index": 0.0
                }
            }
            
            logger.warning(f"OpenWeather monthly aggregation not fully implemented - returning placeholder")
            return weather_data
            
        except Exception as e:
            logger.error(f"Error fetching OpenWeather data for {city}: {e}")
            return None
    
    # ===== FRED ECONOMIC DATA =====
    
    def fetch_fred_indicator(self, indicator_code: str, months: int = 300) -> Optional[Dict[str, float]]:
        """
        Fetch economic indicator from FRED (Federal Reserve Economic Data).
        
        Args:
            indicator_code: FRED series ID (e.g., "UNRATE" for unemployment, "UMCSENT" for consumer confidence)
            months: Number of months of historical data
            
        Returns:
            Dict mapping "YYYY-MM-01" to indicator value
        """
        if not self.fred_client:
            logger.warning("FRED client not initialized - check FRED_API_KEY")
            return None
        
        try:
            # Calculate date range
            end_date = datetime.now()
            start_date = end_date - relativedelta(months=months)
            
            # Fetch series from FRED
            series = self.fred_client.get_series(
                indicator_code,
                observation_start=start_date.strftime("%Y-%m-%d"),
                observation_end=end_date.strftime("%Y-%m-%d")
            )
            
            if series.empty:
                logger.warning(f"No FRED data for indicator: {indicator_code}")
                return None
            
            # Convert to monthly dict
            fred_data = {}
            for index, value in series.items():
                # Format as YYYY-MM-01
                month_key = index.strftime("%Y-%m-01")
                fred_data[month_key] = float(value)
            
            logger.info(f"Fetched {len(fred_data)} months of FRED data for {indicator_code}")
            return fred_data
            
        except Exception as e:
            logger.error(f"Error fetching FRED indicator {indicator_code}: {e}")
            return None
    
    # ===== USPTO PATENTS =====
    
    def fetch_uspto_patents_monthly(self, category: str, months: int = 300) -> Optional[Dict[str, int]]:
        """
        Fetch USPTO patent applications by category (monthly counts).
        
        Args:
            category: Patent category (e.g., "AI", "medical_device", "clean_energy")
            months: Number of months of historical data
            
        Returns:
            Dict mapping "YYYY-MM-01" to monthly patent count
        """
        try:
            # USPTO Patent API endpoint
            # NOTE: This is a simplified implementation - real USPTO API requires more complex queries
            
            # For MVP, we'll create a placeholder that searches USPTO bulk data
            # TODO: Implement full USPTO Patent Search API integration
            
            logger.warning(f"USPTO patent fetching for '{category}' not fully implemented - using placeholder")
            
            # Return placeholder data
            patent_data = {}
            end_date = datetime.now()
            for i in range(min(months, 36)):  # Last 3 years as placeholder
                month_date = end_date - relativedelta(months=i)
                month_key = month_date.strftime("%Y-%m-01")
                patent_data[month_key] = 0  # Placeholder count
            
            return patent_data
            
        except Exception as e:
            logger.error(f"Error fetching USPTO patents for category {category}: {e}")
            return None
    
    # ===== UK IPO PATENTS =====
    
    def fetch_ukipo_patents_monthly(self, category: str, months: int = 300) -> Optional[Dict[str, int]]:
        """
        Fetch UK IPO (Intellectual Property Office) patent applications by category.
        
        Args:
            category: Patent category (e.g., "AI", "fintech", "clean_energy")
            months: Number of months of historical data
            
        Returns:
            Dict mapping "YYYY-MM-01" to monthly patent count
        """
        try:
            # UK IPO Public Data API
            # NOTE: UK IPO provides open data but requires parsing their bulk datasets
            # For MVP, using placeholder
            
            logger.warning(f"UK IPO patent fetching for '{category}' not fully implemented - using placeholder")
            
            # Return placeholder data
            patent_data = {}
            end_date = datetime.now()
            for i in range(min(months, 36)):  # Last 3 years as placeholder
                month_date = end_date - relativedelta(months=i)
                month_key = month_date.strftime("%Y-%m-01")
                patent_data[month_key] = 0  # Placeholder count
            
            return patent_data
            
        except Exception as e:
            logger.error(f"Error fetching UK IPO patents for category {category}: {e}")
            return None
    
    # ===== USGS EARTHQUAKES =====
    
    def fetch_usgs_earthquakes_monthly(self, region: str = "global", months: int = 300) -> Optional[Dict[str, Dict[str, float]]]:
        """
        Fetch USGS earthquake data aggregated monthly.
        
        Args:
            region: Geographic region (e.g., "global", "california", "japan")
            months: Number of months of historical data
            
        Returns:
            Dict mapping "YYYY-MM-01" to monthly earthquake metrics: {
                "count": 15,
                "avg_magnitude": 4.8,
                "max_magnitude": 6.2
            }
        """
        try:
            # USGS Earthquake API
            end_date = datetime.now()
            start_date = end_date - relativedelta(months=months)
            
            url = "https://earthquake.usgs.gov/fdsnws/event/1/query"
            params = {
                "format": "geojson",
                "starttime": start_date.strftime("%Y-%m-%d"),
                "endtime": end_date.strftime("%Y-%m-%d"),
                "minmagnitude": 4.0,  # Only significant earthquakes
                "orderby": "time"
            }
            
            response = requests.get(url, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            if not data.get('features'):
                logger.warning(f"No USGS earthquake data for region: {region}")
                return None
            
            # Aggregate by month
            monthly_earthquakes = defaultdict(lambda: {"count": 0, "magnitudes": []})
            
            for feature in data['features']:
                # Get earthquake time and magnitude
                timestamp = feature['properties']['time'] / 1000  # Convert from ms
                magnitude = feature['properties']['mag']
                
                # Convert to month key
                eq_date = datetime.fromtimestamp(timestamp)
                month_key = eq_date.strftime("%Y-%m-01")
                
                monthly_earthquakes[month_key]["count"] += 1
                monthly_earthquakes[month_key]["magnitudes"].append(magnitude)
            
            # Calculate monthly aggregates
            earthquake_data = {}
            for month_key, stats in monthly_earthquakes.items():
                magnitudes = stats["magnitudes"]
                earthquake_data[month_key] = {
                    "count": stats["count"],
                    "avg_magnitude": sum(magnitudes) / len(magnitudes) if magnitudes else 0,
                    "max_magnitude": max(magnitudes) if magnitudes else 0
                }
            
            logger.info(f"Fetched {len(earthquake_data)} months of USGS earthquake data")
            return earthquake_data
            
        except Exception as e:
            logger.error(f"Error fetching USGS earthquakes: {e}")
            return None
