"""
Fix script to refetch data for variables with insufficient data points.
This will specifically target variables with <60 data points and re-fetch with proper error handling.
"""

import os
import sys
from datetime import datetime, timedelta
import logging

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

from database import get_db_session
from models import VariableMetadata, TimeSeriesData, APIStatus
from data_fetcher import DataFetcher
import json

def count_data_points(session, variable_id):
    """Count existing data points for a variable"""
    return session.query(TimeSeriesData).filter(
        TimeSeriesData.variable_id == variable_id
    ).count()

def refetch_stock_data(session, variable, fetcher):
    """Refetch stock data with proper error handling"""
    try:
        params = json.loads(variable.parameters)
        symbol = params.get('symbol')
        
        logger.info(f"Refetching stock data for {symbol}...")
        
        # Fetch 60 months of monthly data
        monthly_prices = fetcher.fetch_stock_data_monthly(symbol, months=60)
        
        if not monthly_prices:
            logger.error(f"No data returned for {symbol}")
            return 0
        
        logger.info(f"Got {len(monthly_prices)} months for {symbol}")
        
        # Store each month
        stored = 0
        for date_str, price in monthly_prices.items():
            timestamp = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Check if already exists
            existing = session.query(TimeSeriesData).filter(
                TimeSeriesData.variable_id == variable.id,
                TimeSeriesData.timestamp == timestamp
            ).first()
            
            if not existing:
                data_point = TimeSeriesData(
                    variable_id=variable.id,
                    timestamp=timestamp,
                    value=price,
                    fetched_at=datetime.utcnow()
                )
                session.add(data_point)
                stored += 1
        
        session.commit()
        logger.info(f"Stored {stored} new data points for {symbol}")
        return stored
        
    except Exception as e:
        logger.error(f"Error refetching {variable.name}: {e}")
        session.rollback()
        return 0

def refetch_gdp_data(session, variable, fetcher):
    """Refetch GDP data with proper error handling"""
    try:
        params = json.loads(variable.parameters)
        country_code = params.get('country_code')
        
        logger.info(f"Refetching GDP data for {country_code}...")
        
        # Fetch monthly GDP data (forward-filled from annual)
        monthly_gdp = fetcher.fetch_gdp_data_monthly(country_code)
        
        if not monthly_gdp:
            logger.error(f"No GDP data returned for {country_code}")
            return 0
        
        logger.info(f"Got {len(monthly_gdp)} months for {country_code}")
        
        # Store each month
        stored = 0
        for date_str, gdp_value in monthly_gdp.items():
            timestamp = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Check if already exists
            existing = session.query(TimeSeriesData).filter(
                TimeSeriesData.variable_id == variable.id,
                TimeSeriesData.timestamp == timestamp
            ).first()
            
            if not existing:
                data_point = TimeSeriesData(
                    variable_id=variable.id,
                    timestamp=timestamp,
                    value=gdp_value,
                    fetched_at=datetime.utcnow()
                )
                session.add(data_point)
                stored += 1
        
        session.commit()
        logger.info(f"Stored {stored} new data points for {country_code}")
        return stored
        
    except Exception as e:
        logger.error(f"Error refetching {variable.name}: {e}")
        session.rollback()
        return 0

def refetch_arxiv_data(session, variable, fetcher):
    """Refetch arXiv data with proper error handling"""
    try:
        params = json.loads(variable.parameters)
        topic = params.get('topic')
        
        logger.info(f"Refetching arXiv data for '{topic}'...")
        
        # Fetch 60 months of paper counts
        monthly_counts = fetcher.fetch_arxiv_papers_monthly(topic, months=60)
        
        if not monthly_counts:
            logger.error(f"No arXiv data returned for '{topic}'")
            return 0
        
        logger.info(f"Got {len(monthly_counts)} months for '{topic}'")
        
        # Store each month
        stored = 0
        for date_str, count in monthly_counts.items():
            timestamp = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Check if already exists
            existing = session.query(TimeSeriesData).filter(
                TimeSeriesData.variable_id == variable.id,
                TimeSeriesData.timestamp == timestamp
            ).first()
            
            if not existing:
                data_point = TimeSeriesData(
                    variable_id=variable.id,
                    timestamp=timestamp,
                    value=float(count),
                    fetched_at=datetime.utcnow()
                )
                session.add(data_point)
                stored += 1
        
        session.commit()
        logger.info(f"Stored {stored} new data points for '{topic}'")
        return stored
        
    except Exception as e:
        logger.error(f"Error refetching {variable.name}: {e}")
        session.rollback()
        return 0

def refetch_environmental_data(session, variable, fetcher):
    """Refetch environmental event data with proper error handling"""
    try:
        params = json.loads(variable.parameters)
        category = params.get('category')
        
        logger.info(f"Refetching environmental data for '{category}'...")
        
        # Fetch 60 months of event counts
        category_monthly_data = fetcher.fetch_environmental_events_monthly(months=60)
        
        if not category_monthly_data or category not in category_monthly_data:
            logger.error(f"No environmental data returned for '{category}'")
            return 0
        
        monthly_counts = category_monthly_data[category]
        logger.info(f"Got {len(monthly_counts)} months for '{category}'")
        
        # Store each month
        stored = 0
        for date_str, count in monthly_counts.items():
            timestamp = datetime.strptime(date_str, "%Y-%m-%d")
            
            # Check if already exists
            existing = session.query(TimeSeriesData).filter(
                TimeSeriesData.variable_id == variable.id,
                TimeSeriesData.timestamp == timestamp
            ).first()
            
            if not existing:
                data_point = TimeSeriesData(
                    variable_id=variable.id,
                    timestamp=timestamp,
                    value=float(count),
                    fetched_at=datetime.utcnow()
                )
                session.add(data_point)
                stored += 1
        
        session.commit()
        logger.info(f"Stored {stored} new data points for '{category}'")
        return stored
        
    except Exception as e:
        logger.error(f"Error refetching {variable.name}: {e}")
        session.rollback()
        return 0

def main():
    """Main refetch script"""
    logger.info("=" * 80)
    logger.info("DATA REFETCH SCRIPT - Fixing variables with insufficient data")
    logger.info("=" * 80)
    
    fetcher = DataFetcher()
    
    with get_db_session() as session:
        # Get all active variables
        variables = session.query(VariableMetadata).filter(
            VariableMetadata.is_active == True
        ).all()
        
        logger.info(f"Found {len(variables)} active variables")
        
        # Check each variable's data point count
        refetch_needed = []
        for var in variables:
            count = count_data_points(session, var.id)
            if count < 60:
                refetch_needed.append((var, count))
                logger.info(f"❌ {var.name}: {count} data points (needs refetch)")
            else:
                logger.info(f"✓ {var.name}: {count} data points (sufficient)")
        
        logger.info(f"\nVariables needing refetch: {len(refetch_needed)}")
        
        if not refetch_needed:
            logger.info("All variables have sufficient data!")
            return
        
        # Refetch data for each variable
        total_refetched = 0
        for var, old_count in refetch_needed:
            logger.info(f"\n{'=' * 60}")
            logger.info(f"Processing: {var.name} (currently {old_count} points)")
            
            if var.source == 'alpha_vantage':
                new_points = refetch_stock_data(session, var, fetcher)
            elif var.source == 'worldbank':
                new_points = refetch_gdp_data(session, var, fetcher)
            elif var.source == 'arxiv':
                new_points = refetch_arxiv_data(session, var, fetcher)
            elif var.source == 'nasa_eonet':
                new_points = refetch_environmental_data(session, var, fetcher)
            else:
                logger.warning(f"Unknown source: {var.source}")
                continue
            
            new_count = count_data_points(session, var.id)
            logger.info(f"Result: {old_count} → {new_count} points ({new_points} new)")
            total_refetched += new_points
        
        logger.info(f"\n{'=' * 80}")
        logger.info(f"REFETCH COMPLETE")
        logger.info(f"Total new data points added: {total_refetched}")
        logger.info(f"{'=' * 80}")

if __name__ == "__main__":
    main()
