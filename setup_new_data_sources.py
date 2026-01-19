"""
Setup New Data Sources: Google Trends, FRED, USGS Enhanced
Adds consumer-facing variables to enable MVP exploitation
"""

from database import get_db_session
from models import VariableMetadata
from datetime import datetime
import json
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def setup_google_trends_variables():
    """Add Google Trends keywords for consumer signals - MAXIMIZE data universe"""
    
    # Consumer behavior keywords across multiple categories
    keywords = [
        # Life Events
        'wedding planning', 'moving companies', 'funeral homes', 'divorce lawyer', 
        'baby names', 'pregnancy test', 'engagement rings', 'retirement planning',
        
        # Employment & Career
        'job search', 'resume builder', 'interview tips', 'career change',
        'unemployment benefits', 'remote work', 'work from home',
        
        # Health & Wellness
        'diet plan', 'weight loss', 'gym membership', 'personal trainer',
        'mental health', 'therapy near me', 'meditation app', 'quit smoking',
        
        # Home & Property
        'home improvement', 'mortgage calculator', 'home inspection', 'pest control',
        'interior design', 'landscaping ideas', 'home security', 'solar panels',
        
        # Finance & Shopping
        'credit score', 'debt consolidation', 'tax preparation', 'stock market',
        'cryptocurrency', 'insurance quotes', 'best credit card', 'loan calculator',
        
        # Education & Learning
        'online courses', 'coding bootcamp', 'language learning', 'college applications',
        'test prep', 'tutoring services', 'scholarships',
        
        # Travel & Leisure
        'vacation packages', 'flight deals', 'hotel booking', 'travel insurance',
        'rental car', 'cruise deals', 'backpacking gear',
        
        # Technology & Services
        'web hosting', 'vpn service', 'antivirus software', 'cloud storage',
        'video conferencing', 'project management software',
        
        # Automotive
        'car insurance', 'auto repair', 'oil change', 'car buying',
        'lease vs buy', 'electric cars',
        
        # Legal & Professional
        'lawyer near me', 'legal advice', 'notary public', 'trademark registration',
        'business formation', 'patent attorney'
    ]
    
    trends_variables = []
    for keyword in keywords:
        trends_variables.append({
            'name': f'Google Trends: {keyword.title()}',
            'display_name': f'Google Trends: {keyword.title()}',
            'source': 'google_trends',
            'data_type': 'time_series',
            'parameters': json.dumps({'keyword': keyword}),
            'unit': 'search_volume',
            'is_active': True
        })
    
    with get_db_session() as session:
        for var_data in trends_variables:
            # Check if already exists
            existing = session.query(VariableMetadata).filter(
                VariableMetadata.name == var_data['name']
            ).first()
            
            if existing:
                logger.info(f"✓ Already exists: {var_data['name']}")
                continue
            
            var = VariableMetadata(**var_data)
            session.add(var)
            logger.info(f"✅ Added: {var_data['name']}")
        
        session.commit()
    
    logger.info(f"Google Trends setup complete: {len(trends_variables)} variables")


def setup_fred_variables():
    """Add FRED economic indicators - MAXIMIZE data universe"""
    
    # Comprehensive set of FRED indicators across economic categories
    indicators = [
        # Labor Market
        ('UNRATE', 'Unemployment Rate', 'percent'),
        ('PAYEMS', 'Total Nonfarm Payrolls', 'thousands'),
        ('CIVPART', 'Labor Force Participation Rate', 'percent'),
        ('UNEMPLOY', 'Unemployment Level', 'thousands'),
        ('EMRATIO', 'Employment-Population Ratio', 'percent'),
        ('U6RATE', 'Total unemployed plus discouraged workers', 'percent'),
        ('ICSA', 'Initial Jobless Claims', 'thousands'),
        
        # Consumer & Sentiment
        ('UMCSENT', 'Consumer Sentiment Index', 'index'),
        ('CPIAUCSL', 'Consumer Price Index', 'index'),
        ('PCEPI', 'Personal Consumption Expenditures Price Index', 'index'),
        ('PSAVERT', 'Personal Saving Rate', 'percent'),
        ('PCE', 'Personal Consumption Expenditures', 'billions_usd'),
        
        # Housing & Construction
        ('HOUST', 'Housing Starts', 'thousands'),
        ('PERMIT', 'Building Permits', 'thousands'),
        ('MORTGAGE30US', '30-Year Fixed Mortgage Rate', 'percent'),
        ('CSUSHPISA', 'Case-Shiller Home Price Index', 'index'),
        ('RRVRUSQ156N', 'Rental Vacancy Rate', 'percent'),
        ('EXHOSLUSM495S', 'Existing Home Sales', 'millions'),
        
        # Retail & Sales
        ('RSXFS', 'Retail Sales Excluding Food Services', 'millions_usd'),
        ('MRTSSM44X72USS', 'Retail Sales: Food Services and Drinking Places', 'millions_usd'),
        ('ECOMSA', 'E-Commerce Retail Sales', 'millions_usd'),
        ('GAFO', 'Retail Sales: Clothing and Accessories', 'millions_usd'),
        
        # Energy & Commodities
        ('GASREGW', 'Gas Prices Regular', 'dollars_per_gallon'),
        ('DCOILWTICO', 'Crude Oil Prices WTI', 'dollars_per_barrel'),
        ('DHHNGSP', 'Natural Gas Price', 'dollars_per_mmbtu'),
        ('GOLDAMGBD228NLBM', 'Gold Price', 'dollars_per_ounce'),
        
        # Manufacturing & Industry
        ('INDPRO', 'Industrial Production Index', 'index'),
        ('IPMAN', 'Manufacturing Production Index', 'index'),
        ('TCU', 'Capacity Utilization', 'percent'),
        ('NEWORDER', 'New Orders for Durable Goods', 'millions_usd'),
        
        # Finance & Credit
        ('FEDFUNDS', 'Federal Funds Rate', 'percent'),
        ('DGS10', '10-Year Treasury Constant Maturity Rate', 'percent'),
        ('TDSP', 'Total Consumer Credit', 'billions_usd'),
        ('TOTCI', 'Commercial and Industrial Loans', 'billions_usd'),
        
        # GDP & Economic Growth
        ('GDP', 'Gross Domestic Product', 'billions_usd'),
        ('GDPC1', 'Real GDP', 'billions_chained_2017_usd'),
        ('GDPPOT', 'Real Potential GDP', 'billions_chained_2017_usd'),
        
        # Trade & International
        ('BOPGSTB', 'Trade Balance Goods and Services', 'millions_usd'),
        ('EXPGS', 'Exports of Goods and Services', 'billions_usd'),
        ('IMPGS', 'Imports of Goods and Services', 'billions_usd'),
        
        # Demographics & Population
        ('POPTHM', 'Population', 'thousands'),
        
        # Business & Confidence
        ('VIXCLS', 'CBOE Volatility Index', 'index'),
        ('BUSINV', 'Total Business Inventories', 'millions_usd'),
    ]
    
    fred_variables = []
    for code, desc, unit in indicators:
        fred_variables.append({
            'name': f'FRED: {desc}',
            'display_name': f'FRED: {desc}',
            'source': 'fred',
            'data_type': 'time_series',
            'parameters': json.dumps({'indicator_code': code}),
            'unit': unit,
            'is_active': True
        })
    
    with get_db_session() as session:
        for var_data in fred_variables:
            # Check if already exists
            existing = session.query(VariableMetadata).filter(
                VariableMetadata.name == var_data['name']
            ).first()
            
            if existing:
                logger.info(f"✓ Already exists: {var_data['name']}")
                continue
            
            var = VariableMetadata(**var_data)
            session.add(var)
            logger.info(f"✅ Added: {var_data['name']}")
        
        session.commit()
    
    logger.info(f"FRED setup complete: {len(fred_variables)} variables")


def setup_usgs_enhanced_variables():
    """Add USGS enhanced earthquake metrics"""
    
    usgs_variables = [
        {
            'name': 'USGS: Earthquake Count (Global)',
            'display_name': 'USGS: Earthquake Count (Global)',
            'source': 'usgs_enhanced',
            'data_type': 'count',
            'parameters': json.dumps({'region': 'global', 'metric': 'count'}),
            'unit': 'count',
            'is_active': True
        },
        {
            'name': 'USGS: Earthquake Avg Magnitude (Global)',
            'display_name': 'USGS: Earthquake Avg Magnitude (Global)',
            'source': 'usgs_enhanced',
            'data_type': 'time_series',
            'parameters': json.dumps({'region': 'global', 'metric': 'avg_magnitude'}),
            'unit': 'magnitude',
            'is_active': True
        },
        {
            'name': 'USGS: Earthquake Max Magnitude (Global)',
            'display_name': 'USGS: Earthquake Max Magnitude (Global)',
            'source': 'usgs_enhanced',
            'data_type': 'time_series',
            'parameters': json.dumps({'region': 'global', 'metric': 'max_magnitude'}),
            'unit': 'magnitude',
            'is_active': True
        }
    ]
    
    with get_db_session() as session:
        for var_data in usgs_variables:
            # Check if already exists
            existing = session.query(VariableMetadata).filter(
                VariableMetadata.name == var_data['name']
            ).first()
            
            if existing:
                logger.info(f"✓ Already exists: {var_data['name']}")
                continue
            
            var = VariableMetadata(**var_data)
            session.add(var)
            logger.info(f"✅ Added: {var_data['name']}")
        
        session.commit()
    
    logger.info(f"USGS Enhanced setup complete: {len(usgs_variables)} variables")


def main():
    """Setup all new data sources"""
    logger.info("=" * 60)
    logger.info("Setting up new data sources for MVP exploitation")
    logger.info("=" * 60)
    
    setup_google_trends_variables()
    logger.info("")
    
    setup_fred_variables()
    logger.info("")
    
    setup_usgs_enhanced_variables()
    logger.info("")
    
    logger.info("=" * 60)
    logger.info("✅ Setup complete!")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Data Universe Expansion:")
    logger.info(f"- ~60 Google Trends consumer signals")
    logger.info(f"- ~50 FRED economic indicators")
    logger.info(f"- 3 USGS earthquake metrics")
    logger.info(f"= ~113 NEW variables added to correlation matrix")
    logger.info("")
    logger.info("Correlation pair combinations:")
    logger.info(f"- Previous: 61 variables = 1,830 pairs")
    logger.info(f"- After: 174 variables = 15,051 pairs")
    logger.info(f"- Growth: 8.2x more correlation opportunities!")
    logger.info("")
    logger.info("Next steps:")
    logger.info("1. Run data ingestion: python -c 'from data_ingestion_service import DataIngestionService; DataIngestionService().fetch_and_store_all_variables()'")
    logger.info("2. Check dashboard for new correlations")
    logger.info("3. Test Granger causality with consumer signals")
    logger.info("")
    logger.info("High-value correlation examples to discover:")
    logger.info("- Google Trends: Job Search ↔ FRED: Unemployment Rate")
    logger.info("- Google Trends: Wedding Planning ↔ FRED: Consumer Sentiment")
    logger.info("- Google Trends: Home Improvement ↔ FRED: Housing Starts")
    logger.info("- Google Trends: Mortgage Calculator ↔ FRED: Mortgage Rates")
    logger.info("- Google Trends: Credit Score ↔ FRED: Consumer Credit")
    logger.info("- Google Trends: Electric Cars ↔ FRED: Gas Prices")


if __name__ == '__main__':
    main()
