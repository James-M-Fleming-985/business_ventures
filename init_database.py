"""
Database Initialization and Migration Script
Creates all tables in Railway Postgres database
"""

import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from models import Base, VariableMetadata, APIStatus
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def get_database_url():
    """Get database URL from environment or Railway"""
    # Railway automatically sets DATABASE_URL
    database_url = os.getenv('DATABASE_URL')
    
    if not database_url:
        # Fallback for local development
        database_url = os.getenv(
            'DATABASE_URL_FALLBACK',
            'postgresql://postgres:postgres@localhost:5432/causal_affect'
        )
    
    # Railway uses postgres:// but SQLAlchemy needs postgresql://
    if database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    return database_url


def create_tables(engine):
    """Create all database tables"""
    logger.info("Creating database tables...")
    Base.metadata.create_all(engine)
    logger.info("✅ All tables created successfully")


def seed_initial_data(session):
    """Seed initial variable metadata and API status"""
    logger.info("Seeding initial data...")
    
    # Check if already seeded
    existing_vars = session.query(VariableMetadata).count()
    if existing_vars > 0:
        logger.info(f"Database already has {existing_vars} variables, skipping seed")
        return
    
    # Seed stock variables
    stock_symbols = ['NVDA', 'AAPL', 'MSFT', 'GOOGL', 'AMZN', 'TSLA', 'META', 'JPM', 'V', 'WMT']
    for symbol in stock_symbols:
        var = VariableMetadata(
            name=f'stock_{symbol.lower()}',
            display_name=f'{symbol} Stock Price',
            unit='USD',
            data_type='time_series',
            source='alpha_vantage',
            api_endpoint='TIME_SERIES_DAILY',
            update_frequency='daily',
            parameters=f'{{"symbol": "{symbol}"}}'
        )
        session.add(var)
    
    # Seed earthquake variable
    session.add(VariableMetadata(
        name='earthquake_count',
        display_name='Daily Earthquake Count',
        unit='count',
        data_type='time_series',
        source='usgs',
        api_endpoint='earthquake.usgs.gov/earthquakes/feed',
        update_frequency='daily',
        parameters='{"feed": "all_month"}'
    ))
    
    # Seed environmental event variables
    env_categories = [
        'wildfires', 'severe_storms', 'volcanoes', 'sea_lake_ice',
        'floods', 'droughts', 'dust_haze', 'landslides', 'snow', 'water_color'
    ]
    for category in env_categories:
        display = category.replace('_', ' ').title()
        session.add(VariableMetadata(
            name=f'env_{category}',
            display_name=f'{display} Events',
            unit='count',
            data_type='event',
            source='nasa_eonet',
            api_endpoint='eonet.gsfc.nasa.gov/api/v3/events',
            update_frequency='realtime',
            parameters=f'{{"category": "{category}"}}'
        ))
    
    # Seed GDP variables
    countries = [
        ('USA', 'United States'), ('GBR', 'United Kingdom'), ('CHN', 'China'),
        ('JPN', 'Japan'), ('DEU', 'Germany'), ('FRA', 'France'),
        ('IND', 'India'), ('BRA', 'Brazil'), ('CAN', 'Canada'), ('AUS', 'Australia'),
        ('KOR', 'South Korea'), ('MEX', 'Mexico'), ('ITA', 'Italy'), ('ESP', 'Spain'),
        ('NLD', 'Netherlands'), ('SAU', 'Saudi Arabia'), ('TUR', 'Turkey'),
        ('CHE', 'Switzerland'), ('POL', 'Poland'), ('SWE', 'Sweden')
    ]
    for code, name in countries:
        session.add(VariableMetadata(
            name=f'gdp_{code.lower()}',
            display_name=f'{name} GDP',
            unit='USD',
            data_type='time_series',
            source='worldbank',
            api_endpoint='api.worldbank.org/v2/country/indicator',
            update_frequency='annual',
            parameters=f'{{"country_code": "{code}", "indicator": "NY.GDP.MKTP.CD"}}'
        ))
    
    # Seed arXiv topic variables
    topics = [
        ('artificial_intelligence', 'Artificial Intelligence'),
        ('machine_learning', 'Machine Learning'),
        ('quantum_physics', 'Quantum Physics'),
        ('astrophysics', 'Astrophysics'),
        ('biotechnology', 'Biotechnology'),
        ('neuroscience', 'Neuroscience'),
        ('climate_science', 'Climate Science'),
        ('robotics', 'Robotics'),
        ('cryptography', 'Cryptography'),
        ('nanotechnology', 'Nanotechnology')
    ]
    for topic_id, topic_name in topics:
        session.add(VariableMetadata(
            name=f'arxiv_{topic_id}',
            display_name=f'{topic_name} Papers',
            unit='count',
            data_type='count',
            source='arxiv',
            api_endpoint='export.arxiv.org/api/query',
            update_frequency='realtime',
            parameters=f'{{"topic": "{topic_name}"}}'
        ))
    
    # Seed clinical trial variables
    conditions = [
        'Cancer', 'Diabetes', 'COVID-19', 'Alzheimer', 'Heart Disease',
        'Obesity', 'Depression', 'Asthma', 'HIV/AIDS', 'Parkinson'
    ]
    for condition in conditions:
        session.add(VariableMetadata(
            name=f'trials_{condition.lower().replace("/", "_").replace(" ", "_")}',
            display_name=f'{condition} Clinical Trials',
            unit='count',
            data_type='count',
            source='clinicaltrials',
            api_endpoint='clinicaltrials.gov/api/v2/studies',
            update_frequency='realtime',
            parameters=f'{{"condition": "{condition}"}}'
        ))
    
    # Seed API status entries
    api_sources = [
        'alpha_vantage', 'usgs', 'nasa_eonet',
        'worldbank', 'arxiv', 'clinicaltrials'
    ]
    for source in api_sources:
        session.add(APIStatus(
            source=source,
            status='unknown',
            failure_count=0,
            success_count=0
        ))
    
    session.commit()
    
    # Count seeded variables
    total_vars = session.query(VariableMetadata).count()
    logger.info(f"✅ Seeded {total_vars} variables")
    logger.info(f"   - Stocks: {len(stock_symbols)}")
    logger.info(f"   - Earthquakes: 1")
    logger.info(f"   - Environmental: {len(env_categories)}")
    logger.info(f"   - GDP: {len(countries)}")
    logger.info(f"   - arXiv: {len(topics)}")
    logger.info(f"   - Clinical Trials: {len(conditions)}")
    logger.info(f"   - Total correlation pairs: {total_vars * total_vars}")


def verify_schema(engine):
    """Verify all tables were created"""
    logger.info("Verifying database schema...")
    
    with engine.connect() as conn:
        result = conn.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public' 
            ORDER BY table_name
        """))
        tables = [row[0] for row in result]
    
    expected_tables = [
        'variable_metadata',
        'time_series_data',
        'correlation_results',
        'rolling_correlations',
        'analysis_jobs',
        'api_status'
    ]
    
    logger.info(f"Found tables: {tables}")
    
    for table in expected_tables:
        if table in tables:
            logger.info(f"  ✅ {table}")
        else:
            logger.error(f"  ❌ {table} MISSING!")
            return False
    
    return True


def main():
    """Main initialization function"""
    logger.info("=" * 60)
    logger.info("Correlation Discovery Engine - Database Initialization")
    logger.info("=" * 60)
    
    try:
        # Get database URL
        database_url = get_database_url()
        logger.info(f"Database URL: {database_url.split('@')[1] if '@' in database_url else 'localhost'}")
        
        # Create engine
        engine = create_engine(database_url, echo=False)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.fetchone()[0]
            logger.info(f"✅ Connected to PostgreSQL: {version.split(',')[0]}")
        
        # Create tables
        create_tables(engine)
        
        # Verify schema
        if not verify_schema(engine):
            logger.error("Schema verification failed!")
            sys.exit(1)
        
        # Seed initial data
        Session = sessionmaker(bind=engine)
        session = Session()
        
        try:
            seed_initial_data(session)
        finally:
            session.close()
        
        logger.info("=" * 60)
        logger.info("✅ Database initialization complete!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
