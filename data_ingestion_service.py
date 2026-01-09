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
