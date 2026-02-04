"""
Data Ingestion Service
Fetches data from APIs and stores in database with standardized alignment
"""

from data_fetcher import DataFetcher
from data_alignment_utils import (
    get_standard_monthly_grid,
    normalize_to_standard_grid,
    get_fill_strategy_for_variable_type
)
from database import get_db_session
from models import VariableMetadata, TimeSeriesData, APIStatus, AnalysisJob
from datetime import datetime, timedelta
import logging
import json
from typing import Optional, List

logger = logging.getLogger(__name__)


class DataIngestionService:
    """Service to fetch API data and store in database with alignment"""
    
    def __init__(self):
        self.fetcher = DataFetcher()
        # Generate standard monthly grid for all data
        self.standard_grid = get_standard_monthly_grid(months_back=300)
    
    def fetch_and_store_all_variables(self) -> dict:
        """
        Fetch data for all active variables and store in database
        Returns summary statistics
        """
        logger.info("Starting data ingestion for all variables...")
        
        stats = {
            'total_variables': 0,
            'successful_fetches': 0,
            'failed_fetches': 0,
            'data_points_stored': 0,
            'api_status': {}
        }
        
        # Create analysis job
        with get_db_session() as session:
            job = AnalysisJob(
                job_type='data_fetch',
                status='running',
                start_time=datetime.utcnow()
            )
            session.add(job)
            session.commit()
            job_id = job.id
        
        # Fetch data by source
        stats.update(self._fetch_stock_data())
        stats.update(self._fetch_earthquake_data())
        stats.update(self._fetch_environmental_data())
        stats.update(self._fetch_gdp_data())
        stats.update(self._fetch_arxiv_data())
        stats.update(self._fetch_clinical_trials_data())
        stats.update(self._fetch_google_trends_data())
        stats.update(self._fetch_fred_data())
        stats.update(self._fetch_usgs_earthquakes_data())
        stats.update(self._fetch_wikipedia_pageviews_data())
        
        # Update job status
        with get_db_session() as session:
            job = session.query(AnalysisJob).get(job_id)
            job.status = 'completed'
            job.end_time = datetime.utcnow()
            job.parameters = json.dumps(stats)
            session.commit()
        
        logger.info(f"Data ingestion complete: {stats}")
        return stats
    
    def _fetch_stock_data(self) -> dict:
        """Fetch monthly stock data for all stock variables"""
        logger.info("Fetching monthly stock data...")
        
        with get_db_session() as session:
            stock_vars = session.query(VariableMetadata).filter(
                VariableMetadata.source == 'alpha_vantage',
                VariableMetadata.is_active == True
            ).all()
            
            success_count = 0
            data_points = 0
            
            for var in stock_vars:
                try:
                    params = json.loads(var.parameters)
                    symbol = params.get('symbol')
                    
                    # Fetch monthly data (300 months = 25 years for Granger causality)
                    monthly_prices = self.fetcher.fetch_stock_data_monthly(
                        symbol, months=300
                    )
                    
                    if monthly_prices:
                        # NORMALIZE to standard grid with interpolation
                        fill_method = get_fill_strategy_for_variable_type(
                            'alpha_vantage', var.name
                        )
                        aligned_data = normalize_to_standard_grid(
                            monthly_prices,
                            self.standard_grid,
                            fill_method=fill_method
                        )
                        
                        logger.info(
                            f"{symbol}: {len(monthly_prices)} raw points "
                            f"-> {len(aligned_data)} aligned points"
                        )
                        
                        # Store aligned data points
                        for date_str, price in aligned_data.items():
                            timestamp = datetime.strptime(date_str, "%Y-%m-%d")
                            
                            # Check if data point already exists
                            existing = session.query(TimeSeriesData).filter(
                                TimeSeriesData.variable_id == var.id,
                                TimeSeriesData.timestamp == timestamp
                            ).first()
                            
                            if not existing:
                                data_point = TimeSeriesData(
                                    variable_id=var.id,
                                    timestamp=timestamp,
                                    value=price,
                                    fetched_at=datetime.utcnow()
                                )
                                session.add(data_point)
                                data_points += 1
                        
                        session.commit()
                        success_count += 1
                        self._update_api_status(session, 'alpha_vantage', 'active')
                        logger.info(f"Stored {len(monthly_prices)} monthly prices for {symbol}")
                    else:
                        logger.warning(f"No data for {symbol}")
                        
                except Exception as e:
                    logger.error(f"Error fetching {var.name}: {e}")
                    self._update_api_status(session, 'alpha_vantage', 'failed', str(e))
        
        logger.info(f"Stock data: {success_count} variables, {data_points} data points")
        return {'stocks_fetched': success_count, 'stock_data_points': data_points}
    
    def _fetch_earthquake_data(self) -> dict:
        """Fetch monthly earthquake count data"""
        logger.info("Fetching monthly earthquake data...")
        
        with get_db_session() as session:
            eq_var = session.query(VariableMetadata).filter(
                VariableMetadata.source == 'usgs',
                VariableMetadata.is_active == True
            ).first()
            
            if not eq_var:
                return {'earthquakes_fetched': 0}
            
            try:
                # Fetch monthly aggregated earthquake counts
                monthly_counts = self.fetcher.fetch_earthquake_monthly(months=60)
                
                if monthly_counts:
                    # NORMALIZE to standard grid
                    fill_method = get_fill_strategy_for_variable_type(
                        'usgs', eq_var.name
                    )
                    aligned_data = normalize_to_standard_grid(
                        monthly_counts,
                        self.standard_grid,
                        fill_method=fill_method
                    )
                    
                    logger.info(
                        f"Earthquakes: {len(monthly_counts)} raw points "
                        f"-> {len(aligned_data)} aligned points"
                    )
                    
                    data_points = 0
                    
                    for date_str, count in aligned_data.items():
                        timestamp = datetime.strptime(date_str, "%Y-%m-%d")
                        
                        existing = session.query(TimeSeriesData).filter(
                            TimeSeriesData.variable_id == eq_var.id,
                            TimeSeriesData.timestamp == timestamp
                        ).first()
                        
                        if not existing:
                            data_point = TimeSeriesData(
                                variable_id=eq_var.id,
                                timestamp=timestamp,
                                value=float(count),
                                fetched_at=datetime.utcnow()
                            )
                            session.add(data_point)
                            data_points += 1
                    
                    session.commit()
                    self._update_api_status(session, 'usgs', 'active')
                    logger.info(f"Earthquake data: {len(monthly_counts)} months, {data_points} new data points")
                    return {'earthquakes_fetched': 1, 'earthquake_data_points': data_points}
                    
            except Exception as e:
                logger.error(f"Error fetching earthquake data: {e}")
                self._update_api_status(session, 'usgs', 'failed', str(e))
        
        return {'earthquakes_fetched': 0}
    
    def _fetch_environmental_data(self) -> dict:
        """Fetch monthly environmental event counts from NASA EONET"""
        logger.info("Fetching monthly environmental data...")
        
        with get_db_session() as session:
            env_vars = session.query(VariableMetadata).filter(
                VariableMetadata.source == 'nasa_eonet',
                VariableMetadata.is_active == True
            ).all()
            
            if not env_vars:
                return {'environmental_fetched': 0}
            
            try:
                # Fetch monthly historical data (60 months = 5 years)
                category_monthly_data = self.fetcher.fetch_environmental_events_monthly(months=60)
                
                if not category_monthly_data:
                    logger.warning("No environmental data returned from API")
                    return {'environmental_fetched': 0}
                
                success_count = 0
                data_points = 0
                
                for var in env_vars:
                    params = json.loads(var.parameters)
                    category = params.get('category', '')
                    
                    # Map variable category to API category title
                    category_title = category.replace('_', ' ').title()
                    
                    monthly_counts = category_monthly_data.get(category_title, {})
                    
                    if monthly_counts:
                        # Store all monthly data points
                        for date_str, count in monthly_counts.items():
                            timestamp = datetime.strptime(date_str, "%Y-%m-%d")
                            
                            # Check if data point already exists
                            existing = session.query(TimeSeriesData).filter(
                                TimeSeriesData.variable_id == var.id,
                                TimeSeriesData.timestamp == timestamp
                            ).first()
                            
                            if not existing:
                                data_point = TimeSeriesData(
                                    variable_id=var.id,
                                    timestamp=timestamp,
                                    value=float(count),
                                    fetched_at=datetime.utcnow()
                                )
                                session.add(data_point)
                                data_points += 1
                        
                        session.commit()
                        success_count += 1
                        logger.info(f"Stored {len(monthly_counts)} months for {category_title}")
                    else:
                        logger.warning(f"No data for {category_title}")
                
                self._update_api_status(session, 'nasa_eonet', 'active')
                logger.info(f"Environmental data: {success_count} variables, {data_points} new data points")
                return {'environmental_fetched': success_count, 'environmental_data_points': data_points}
                
            except Exception as e:
                logger.error(f"Error fetching environmental data: {e}")
                self._update_api_status(session, 'nasa_eonet', 'failed', str(e))
                return {'environmental_fetched': 0}
    
    def _fetch_gdp_data(self) -> dict:
        """Fetch annual GDP data from World Bank"""
        logger.info("Fetching annual GDP data...")
        
        with get_db_session() as session:
            gdp_vars = session.query(VariableMetadata).filter(
                VariableMetadata.source == 'worldbank',
                VariableMetadata.is_active.is_(True)
            ).all()
            
            success_count = 0
            data_points = 0
            
            for var in gdp_vars:
                try:
                    params = json.loads(var.parameters)
                    country_code = params.get('country_code')
                    
                    if not country_code:
                        logger.warning(f"No country_code for {var.name}")
                        continue
                    
                    # Fetch annual GDP data (20 years)
                    annual_gdp = self.fetcher.fetch_gdp_data_annual(
                        country_code, years=20
                    )
                    
                    if annual_gdp:
                        # Store annual data points
                        for year, value in annual_gdp.items():
                            # Jan 1st of year
                            timestamp = datetime(int(year), 1, 1)
                            
                            existing = session.query(TimeSeriesData).filter(
                                TimeSeriesData.variable_id == var.id,
                                TimeSeriesData.timestamp == timestamp
                            ).first()
                            
                            if not existing:
                                data_point = TimeSeriesData(
                                    variable_id=var.id,
                                    timestamp=timestamp,
                                    value=value,
                                    fetched_at=datetime.utcnow()
                                )
                                session.add(data_point)
                                data_points += 1
                        
                        session.commit()
                        success_count += 1
                        self._update_api_status(
                            session, 'worldbank', 'active'
                        )
                        logger.info(
                            f"GDP: {len(annual_gdp)} points "
                            f"for {var.display_name}"
                        )
                        
                except Exception as e:
                    logger.error(f"Error fetching GDP {var.name}: {e}")
                    self._update_api_status(
                        session, 'worldbank', 'failed', str(e)
                    )
        
        logger.info(
            f"GDP data: {success_count} variables, "
            f"{data_points} data points"
        )
        return {
            'gdp_fetched': success_count,
            'gdp_data_points': data_points
        }
    
    def _fetch_arxiv_data(self) -> dict:
        """Fetch monthly arXiv paper counts (60 months historical)"""
        logger.info("Fetching monthly arXiv data...")
        
        with get_db_session() as session:
            arxiv_vars = session.query(VariableMetadata).filter(
                VariableMetadata.source == 'arxiv',
                VariableMetadata.is_active == True
            ).all()
            
            success_count = 0
            data_points = 0
            
            for var in arxiv_vars:
                try:
                    params = json.loads(var.parameters)
                    topic = params.get('topic')
                    
                    # Fetch monthly paper counts
                    monthly_counts = self.fetcher.fetch_arxiv_papers_monthly(
                        topic, months=60
                    )
                    
                    if monthly_counts:
                        # NORMALIZE to standard grid
                        fill_method = get_fill_strategy_for_variable_type(
                            'arxiv', var.name
                        )
                        aligned_data = normalize_to_standard_grid(
                            monthly_counts,
                            self.standard_grid,
                            fill_method=fill_method
                        )
                        
                        logger.info(
                            f"{topic}: {len(monthly_counts)} raw points "
                            f"-> {len(aligned_data)} aligned points"
                        )
                        
                        # Store aligned data
                        for date_str, count in aligned_data.items():
                            timestamp = datetime.strptime(date_str, "%Y-%m-%d")
                            
                            # Check if data point already exists
                            existing = session.query(TimeSeriesData).filter(
                                TimeSeriesData.variable_id == var.id,
                                TimeSeriesData.timestamp == timestamp
                            ).first()
                            
                            if not existing:
                                data_point = TimeSeriesData(
                                    variable_id=var.id,
                                    timestamp=timestamp,
                                    value=float(count),
                                    fetched_at=datetime.utcnow()
                                )
                                session.add(data_point)
                                data_points += 1
                        
                        success_count += 1
                        self._update_api_status(session, 'arxiv', 'active')
                        
                except Exception as e:
                    logger.error(f"Error fetching arXiv {var.name}: {e}")
                    self._update_api_status(session, 'arxiv', 'failed', str(e))
            
            session.commit()
        
        logger.info(f"arXiv data: {success_count} variables, {data_points} data points")
        return {'arxiv_fetched': success_count, 'arxiv_data_points': data_points}
    
    def _fetch_clinical_trials_data(self) -> dict:
        """Fetch monthly clinical trial counts (60 months historical)"""
        logger.info("Fetching monthly clinical trials data...")
        
        with get_db_session() as session:
            trial_vars = session.query(VariableMetadata).filter(
                VariableMetadata.source == 'clinicaltrials',
                VariableMetadata.is_active == True
            ).all()
            
            success_count = 0
            data_points = 0
            
            for var in trial_vars:
                try:
                    params = json.loads(var.parameters)
                    condition = params.get('condition')
                    
                    # Fetch monthly trial counts
                    monthly_counts = self.fetcher.fetch_clinical_trials_monthly(
                        condition, months=60
                    )
                    
                    if monthly_counts:
                        # NORMALIZE to standard grid
                        fill_method = get_fill_strategy_for_variable_type(
                            'clinicaltrials', var.name
                        )
                        aligned_data = normalize_to_standard_grid(
                            monthly_counts,
                            self.standard_grid,
                            fill_method=fill_method
                        )
                        
                        logger.info(
                            f"{condition}: {len(monthly_counts)} raw points "
                            f"-> {len(aligned_data)} aligned points"
                        )
                        
                        # Store aligned data
                        for date_str, count in aligned_data.items():
                            timestamp = datetime.strptime(date_str, "%Y-%m-%d")
                            
                            # Check if data point already exists
                            existing = session.query(TimeSeriesData).filter(
                                TimeSeriesData.variable_id == var.id,
                                TimeSeriesData.timestamp == timestamp
                            ).first()
                            
                            if not existing:
                                data_point = TimeSeriesData(
                                    variable_id=var.id,
                                    timestamp=timestamp,
                                    value=float(count),
                                    fetched_at=datetime.utcnow()
                                )
                                session.add(data_point)
                                data_points += 1
                        
                        success_count += 1
                        self._update_api_status(session, 'clinicaltrials', 'active')
                        
                except Exception as e:
                    logger.error(f"Error fetching trials {var.name}: {e}")
                    self._update_api_status(session, 'clinicaltrials', 'failed', str(e))
            
            session.commit()
        
        logger.info(f"Clinical trials: {success_count} variables, {data_points} data points")
        return {'trials_fetched': success_count, 'trials_data_points': data_points}
    
    def _fetch_google_trends_data(self) -> dict:
        """Fetch Google Trends data for all trend variables"""
        # SKIP: Google Trends pytrends is blocked from data centers
        # The API gets rate-limited and blocks all subsequent fetches
        logger.info("Skipping Google Trends (blocked from data centers)")
        return {'google_trends_fetched': 0, 'google_trends_skipped': True}
        
        # Original code below (disabled)
        logger.info("Fetching Google Trends data...")
        
        with get_db_session() as session:
            trends_vars = session.query(VariableMetadata).filter(
                VariableMetadata.source == 'google_trends',
                VariableMetadata.is_active == True
            ).all()
            
            success_count = 0
            data_points = 0
            
            for idx, var in enumerate(trends_vars):
                try:
                    params = json.loads(var.parameters)
                    keyword = params.get('keyword')
                    
                    # Add 5-second delay between requests to avoid rate limiting
                    if idx > 0:
                        import time
                        logger.info(f"Waiting 5 seconds before next Google Trends request...")
                        time.sleep(5)
                    
                    # Fetch monthly data (300 months = 25 years)
                    monthly_trends = self.fetcher.fetch_google_trends_monthly(
                        keyword, months=300
                    )
                    
                    if monthly_trends:
                        # NORMALIZE to standard grid
                        fill_method = get_fill_strategy_for_variable_type(
                            'google_trends', var.name
                        )
                        aligned_data = normalize_to_standard_grid(
                            monthly_trends,
                            self.standard_grid,
                            fill_method=fill_method
                        )
                        
                        logger.info(
                            f"{keyword}: {len(monthly_trends)} raw points "
                            f"-> {len(aligned_data)} aligned points"
                        )
                        
                        # Store aligned data points
                        for date_str, volume in aligned_data.items():
                            timestamp = datetime.strptime(date_str, "%Y-%m-%d")
                            
                            existing = session.query(TimeSeriesData).filter(
                                TimeSeriesData.variable_id == var.id,
                                TimeSeriesData.timestamp == timestamp
                            ).first()
                            
                            if not existing:
                                data_point = TimeSeriesData(
                                    variable_id=var.id,
                                    timestamp=timestamp,
                                    value=float(volume),
                                    fetched_at=datetime.utcnow()
                                )
                                session.add(data_point)
                                data_points += 1
                        
                        success_count += 1
                        self._update_api_status(session, 'google_trends', 'active')
                        
                except Exception as e:
                    logger.error(f"Error fetching Google Trends {var.name}: {e}")
                    self._update_api_status(session, 'google_trends', 'failed', str(e))
            
            session.commit()
        
        logger.info(f"Google Trends: {success_count} variables, {data_points} data points")
        return {'trends_fetched': success_count, 'trends_data_points': data_points}
    
    def _fetch_fred_data(self) -> dict:
        """Fetch FRED economic indicator data for all FRED variables"""
        logger.info("Fetching FRED economic data...")
        
        # Check if FRED client is available
        if not self.fetcher.fred_client:
            logger.error("FRED client not initialized - check FRED_API_KEY environment variable")
            return {'fred_fetched': 0, 'fred_error': 'FRED client not initialized'}
        
        with get_db_session() as session:
            fred_vars = session.query(VariableMetadata).filter(
                VariableMetadata.source == 'fred',
                VariableMetadata.is_active == True
            ).all()
            
            logger.info(f"Found {len(fred_vars)} FRED variables to fetch")
            
            if not fred_vars:
                logger.warning("No FRED variables found in database")
                return {'fred_fetched': 0, 'fred_variables_found': 0}
            
            success_count = 0
            data_points = 0
            
            for idx, var in enumerate(fred_vars):
                try:
                    params = json.loads(var.parameters)
                    indicator_code = params.get('indicator_code')
                    
                    logger.info(f"[{idx+1}/{len(fred_vars)}] Fetching FRED: {indicator_code}")
                    
                    # Fetch monthly data (300 months = 25 years)
                    monthly_data = self.fetcher.fetch_fred_indicator(
                        indicator_code, months=300
                    )
                    
                    if monthly_data:
                        # NORMALIZE to standard grid
                        fill_method = get_fill_strategy_for_variable_type(
                            'fred', var.name
                        )
                        aligned_data = normalize_to_standard_grid(
                            monthly_data,
                            self.standard_grid,
                            fill_method=fill_method
                        )
                        
                        logger.info(
                            f"{indicator_code}: {len(monthly_data)} raw points "
                            f"-> {len(aligned_data)} aligned points"
                        )
                        
                        # Store aligned data points
                        for date_str, value in aligned_data.items():
                            timestamp = datetime.strptime(date_str, "%Y-%m-%d")
                            
                            existing = session.query(TimeSeriesData).filter(
                                TimeSeriesData.variable_id == var.id,
                                TimeSeriesData.timestamp == timestamp
                            ).first()
                            
                            if not existing:
                                data_point = TimeSeriesData(
                                    variable_id=var.id,
                                    timestamp=timestamp,
                                    value=float(value),
                                    fetched_at=datetime.utcnow()
                                )
                                session.add(data_point)
                                data_points += 1
                        
                        success_count += 1
                        self._update_api_status(session, 'fred', 'active')
                        
                except Exception as e:
                    logger.error(f"Error fetching FRED data {var.name}: {e}")
                    self._update_api_status(session, 'fred', 'failed', str(e))
            
            session.commit()
        
        logger.info(f"FRED: {success_count} variables, {data_points} data points")
        return {'fred_fetched': success_count, 'fred_data_points': data_points}
    
    def _fetch_usgs_earthquakes_data(self) -> dict:
        """Fetch USGS earthquake data with count/magnitude aggregation"""
        logger.info("Fetching USGS earthquake data (enhanced)...")
        
        with get_db_session() as session:
            # Get all USGS variables (count, avg_magnitude, max_magnitude)
            usgs_vars = session.query(VariableMetadata).filter(
                VariableMetadata.source == 'usgs_enhanced',
                VariableMetadata.is_active == True
            ).all()
            
            if not usgs_vars:
                return {'usgs_enhanced_fetched': 0}
            
            success_count = 0
            data_points = 0
            
            # Fetch earthquake data once (aggregated)
            try:
                monthly_earthquakes = self.fetcher.fetch_usgs_earthquakes_monthly(
                    region='global', months=300
                )
                
                if monthly_earthquakes:
                    # For each variable (count, avg_magnitude, max_magnitude)
                    for var in usgs_vars:
                        params = json.loads(var.parameters)
                        metric = params.get('metric')  # 'count', 'avg_magnitude', or 'max_magnitude'
                        
                        # Extract specific metric from aggregated data
                        metric_data = {}
                        for date_str, values in monthly_earthquakes.items():
                            metric_data[date_str] = values.get(metric, 0.0)
                        
                        # NORMALIZE to standard grid
                        fill_method = get_fill_strategy_for_variable_type(
                            'usgs_enhanced', var.name
                        )
                        aligned_data = normalize_to_standard_grid(
                            metric_data,
                            self.standard_grid,
                            fill_method=fill_method
                        )
                        
                        logger.info(
                            f"USGS {metric}: {len(metric_data)} raw points "
                            f"-> {len(aligned_data)} aligned points"
                        )
                        
                        # Store aligned data points
                        for date_str, value in aligned_data.items():
                            timestamp = datetime.strptime(date_str, "%Y-%m-%d")
                            
                            existing = session.query(TimeSeriesData).filter(
                                TimeSeriesData.variable_id == var.id,
                                TimeSeriesData.timestamp == timestamp
                            ).first()
                            
                            if not existing:
                                data_point = TimeSeriesData(
                                    variable_id=var.id,
                                    timestamp=timestamp,
                                    value=float(value),
                                    fetched_at=datetime.utcnow()
                                )
                                session.add(data_point)
                                data_points += 1
                        
                        success_count += 1
                    
                    self._update_api_status(session, 'usgs_enhanced', 'active')
                    
            except Exception as e:
                logger.error(f"Error fetching USGS enhanced data: {e}")
                self._update_api_status(session, 'usgs_enhanced', 'failed', str(e))
            
            session.commit()
        
        logger.info(f"USGS Enhanced: {success_count} variables, {data_points} data points")
        return {'usgs_enhanced_fetched': success_count, 'usgs_enhanced_data_points': data_points}
    
    def _fetch_wikipedia_pageviews_data(self) -> dict:
        """
        Fetch Wikipedia pageviews data (LAYER 1: FAST BEHAVIORAL SIGNALS).
        
        Fetches BOTH:
        - DAILY data (90 days) for real-time momentum in Signal Radar
        - MONTHLY data (5 years) for Granger causality correlation with Layer 2
        
        Wikipedia Pageviews API is FREE with no rate limits!
        """
        logger.info("Fetching Wikipedia pageviews data (daily + monthly for Granger)...")
        
        with get_db_session() as session:
            wiki_vars = session.query(VariableMetadata).filter(
                VariableMetadata.source == 'wikipedia',
                VariableMetadata.is_active == True
            ).all()
            
            if not wiki_vars:
                logger.info("No Wikipedia variables found - skipping")
                return {'wikipedia_fetched': 0, 'wikipedia_data_points': 0}
            
            success_count = 0
            data_points = 0
            
            for idx, var in enumerate(wiki_vars):
                try:
                    params = json.loads(var.parameters) if var.parameters else {}
                    article = params.get('article')
                    
                    if not article:
                        logger.warning(f"No article specified for {var.name}")
                        continue
                    
                    # Small delay between requests to be polite to Wikipedia API
                    if idx > 0:
                        import time
                        time.sleep(0.5)  # 500ms delay between articles
                    
                    # ============================================================
                    # FETCH MONTHLY DATA (5 years) - For Granger Causality
                    # This aligns with Layer 2 monthly data for correlation analysis
                    # ============================================================
                    monthly_pageviews = self.fetcher.fetch_wikipedia_pageviews_monthly(
                        article, months=60  # 5 years
                    )
                    
                    if monthly_pageviews:
                        logger.info(
                            f"Wikipedia '{article}': {len(monthly_pageviews)} monthly points (for Granger)"
                        )
                        
                        for date_str, views in monthly_pageviews.items():
                            timestamp = datetime.strptime(date_str, "%Y-%m-%d")
                            
                            existing = session.query(TimeSeriesData).filter(
                                TimeSeriesData.variable_id == var.id,
                                TimeSeriesData.timestamp == timestamp
                            ).first()
                            
                            if existing:
                                if existing.value != float(views):
                                    existing.value = float(views)
                                    existing.fetched_at = datetime.utcnow()
                            else:
                                data_point = TimeSeriesData(
                                    variable_id=var.id,
                                    timestamp=timestamp,
                                    value=float(views),
                                    fetched_at=datetime.utcnow()
                                )
                                session.add(data_point)
                                data_points += 1
                        
                        success_count += 1
                        self._update_api_status(session, 'wikipedia', 'active')
                    
                    # Small delay before daily fetch
                    import time
                    time.sleep(0.3)
                    
                    # ============================================================
                    # FETCH DAILY DATA (90 days) - For Real-time Momentum
                    # This powers the Signal Radar week-over-week momentum display
                    # ============================================================
                    daily_pageviews = self.fetcher.fetch_wikipedia_pageviews_daily(
                        article, days=90
                    )
                    
                    if daily_pageviews:
                        logger.info(
                            f"Wikipedia '{article}': {len(daily_pageviews)} daily points (for momentum)"
                        )
                        
                        for date_str, views in daily_pageviews.items():
                            timestamp = datetime.strptime(date_str, "%Y-%m-%d")
                            
                            existing = session.query(TimeSeriesData).filter(
                                TimeSeriesData.variable_id == var.id,
                                TimeSeriesData.timestamp == timestamp
                            ).first()
                            
                            if existing:
                                if existing.value != float(views):
                                    existing.value = float(views)
                                    existing.fetched_at = datetime.utcnow()
                            else:
                                data_point = TimeSeriesData(
                                    variable_id=var.id,
                                    timestamp=timestamp,
                                    value=float(views),
                                    fetched_at=datetime.utcnow()
                                )
                                session.add(data_point)
                                data_points += 1
                        
                except Exception as e:
                    logger.error(f"Error fetching Wikipedia pageviews {var.name}: {e}")
                    self._update_api_status(session, 'wikipedia', 'failed', str(e))
            
            session.commit()
        
        logger.info(f"Wikipedia: {success_count} variables, {data_points} new data points (daily+monthly)")
        return {'wikipedia_fetched': success_count, 'wikipedia_data_points': data_points}
    
    def _fetch_reddit_activity_data(self) -> dict:
        """
        Fetch Reddit subreddit activity (LAYER 1: FAST BEHAVIORAL SIGNALS).
        Cross-validates Wikipedia signals for higher confidence.
        Reddit API: Free with rate limits (60 req/min with proper User-Agent)
        """
        logger.info("Fetching Reddit DAILY activity data (Layer 1 - Fast Signals)...")
        
        with get_db_session() as session:
            reddit_vars = session.query(VariableMetadata).filter(
                VariableMetadata.source == 'reddit',
                VariableMetadata.is_active == True
            ).all()
            
            if not reddit_vars:
                logger.info("No Reddit variables found - skipping")
                return {'reddit_fetched': 0, 'reddit_data_points': 0}
            
            success_count = 0
            data_points = 0
            
            for idx, var in enumerate(reddit_vars):
                try:
                    params = json.loads(var.parameters) if var.parameters else {}
                    subreddit = params.get('subreddit')
                    
                    if not subreddit:
                        logger.warning(f"No subreddit specified for {var.name}")
                        continue
                    
                    # Rate limit: 2 second delay between Reddit requests
                    if idx > 0:
                        import time
                        time.sleep(2.0)  # Reddit is more rate-limited
                    
                    # Fetch daily activity (30 days available from API)
                    daily_activity = self.fetcher.fetch_reddit_activity_daily(
                        subreddit, days=30
                    )
                    
                    if daily_activity:
                        logger.info(
                            f"Reddit r/{subreddit}: {len(daily_activity)} daily points"
                        )
                        
                        # Store post count as the primary metric
                        for date_str, activity in daily_activity.items():
                            timestamp = datetime.strptime(date_str, "%Y-%m-%d")
                            posts = activity.get('posts', 0)
                            
                            existing = session.query(TimeSeriesData).filter(
                                TimeSeriesData.variable_id == var.id,
                                TimeSeriesData.timestamp == timestamp
                            ).first()
                            
                            if existing:
                                if existing.value != float(posts):
                                    existing.value = float(posts)
                                    existing.fetched_at = datetime.utcnow()
                            else:
                                data_point = TimeSeriesData(
                                    variable_id=var.id,
                                    timestamp=timestamp,
                                    value=float(posts),
                                    fetched_at=datetime.utcnow()
                                )
                                session.add(data_point)
                                data_points += 1
                        
                        success_count += 1
                        self._update_api_status(session, 'reddit', 'active')
                    else:
                        logger.warning(f"No data returned for r/{subreddit}")
                        
                except Exception as e:
                    logger.error(f"Error fetching Reddit r/{subreddit}: {e}")
                    self._update_api_status(session, 'reddit', 'failed', str(e))
            
            session.commit()
        
        logger.info(f"Reddit: {success_count} subreddits, {data_points} new data points")
        return {'reddit_fetched': success_count, 'reddit_data_points': data_points}
    
    def _update_api_status(self, session, source: str, status: str, error: str = None):
        """Update API status in database"""
        api_status = session.query(APIStatus).filter(
            APIStatus.source == source
        ).first()
        
        if not api_status:
            api_status = APIStatus(source=source, status=status)
            session.add(api_status)
        else:
            api_status.status = status
            api_status.checked_at = datetime.utcnow()
            
            if status == 'active':
                api_status.last_success = datetime.utcnow()
                api_status.success_count = (api_status.success_count or 0) + 1
            elif status == 'failed':
                api_status.last_failure = datetime.utcnow()
                api_status.failure_count = (api_status.failure_count or 0) + 1
                api_status.error_message = error
        
        session.commit()
