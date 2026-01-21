"""
Setup Layer 1 (Fast/Behavioral) Data Sources

This script adds Wikipedia Pageviews variables to the database.
Wikipedia API is FREE with no rate limits - replaces Google Trends!

Layer 1 signals are behavioral indicators that move faster than
market/economic data (Layer 2/3), enabling early signal detection.

Run with: python setup_layer1_fast_signals.py
"""

import sys
import os
import json
from datetime import datetime

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from database import get_db_session
from models import VariableMetadata


# ==============================================================================
# LAYER 1: FAST BEHAVIORAL SIGNALS - Wikipedia Pageviews
# ==============================================================================
# These topics are chosen to correlate with Layer 2/3 variables:
# - Economic/market indicators (stocks, GDP)
# - Research/innovation (arXiv, clinical trials)
# - Consumer behavior patterns

WIKIPEDIA_ARTICLES = [
    # TECHNOLOGY & AI (correlates with: NVDA, tech stocks, arXiv AI papers)
    {"article": "Artificial_intelligence", "display_name": "Wikipedia: Artificial Intelligence", "category": "technology"},
    {"article": "ChatGPT", "display_name": "Wikipedia: ChatGPT", "category": "technology"},
    {"article": "Machine_learning", "display_name": "Wikipedia: Machine Learning", "category": "technology"},
    {"article": "Cryptocurrency", "display_name": "Wikipedia: Cryptocurrency", "category": "technology"},
    {"article": "Bitcoin", "display_name": "Wikipedia: Bitcoin", "category": "technology"},
    {"article": "Ethereum", "display_name": "Wikipedia: Ethereum", "category": "technology"},
    {"article": "Nvidia", "display_name": "Wikipedia: Nvidia", "category": "technology"},
    {"article": "Electric_vehicle", "display_name": "Wikipedia: Electric Vehicle", "category": "technology"},
    {"article": "Tesla,_Inc.", "display_name": "Wikipedia: Tesla Inc", "category": "technology"},
    
    # ECONOMY & MARKETS (correlates with: stocks, GDP, FRED indicators)
    {"article": "Recession", "display_name": "Wikipedia: Recession", "category": "economy"},
    {"article": "Inflation", "display_name": "Wikipedia: Inflation", "category": "economy"},
    {"article": "Stock_market", "display_name": "Wikipedia: Stock Market", "category": "economy"},
    {"article": "Interest_rate", "display_name": "Wikipedia: Interest Rate", "category": "economy"},
    {"article": "Unemployment", "display_name": "Wikipedia: Unemployment", "category": "economy"},
    {"article": "Mortgage", "display_name": "Wikipedia: Mortgage", "category": "economy"},
    {"article": "Federal_Reserve", "display_name": "Wikipedia: Federal Reserve", "category": "economy"},
    
    # HEALTH & MEDICINE (correlates with: clinical trials, pharma stocks)
    {"article": "COVID-19", "display_name": "Wikipedia: COVID-19", "category": "health"},
    {"article": "Vaccine", "display_name": "Wikipedia: Vaccine", "category": "health"},
    {"article": "Cancer", "display_name": "Wikipedia: Cancer", "category": "health"},
    {"article": "Diabetes", "display_name": "Wikipedia: Diabetes", "category": "health"},
    {"article": "Mental_health", "display_name": "Wikipedia: Mental Health", "category": "health"},
    {"article": "Obesity", "display_name": "Wikipedia: Obesity", "category": "health"},
    
    # CONSUMER BEHAVIOR (correlates with: retail, consumer sentiment)
    {"article": "Remote_work", "display_name": "Wikipedia: Remote Work", "category": "consumer"},
    {"article": "Online_shopping", "display_name": "Wikipedia: Online Shopping", "category": "consumer"},
    {"article": "Travel", "display_name": "Wikipedia: Travel", "category": "consumer"},
    {"article": "Real_estate", "display_name": "Wikipedia: Real Estate", "category": "consumer"},
    {"article": "Home_improvement", "display_name": "Wikipedia: Home Improvement", "category": "consumer"},
    
    # EMPLOYMENT & CAREER (correlates with: unemployment rate, job market)
    {"article": "Job_hunting", "display_name": "Wikipedia: Job Hunting", "category": "employment"},
    {"article": "Layoff", "display_name": "Wikipedia: Layoff", "category": "employment"},
    {"article": "Resignation", "display_name": "Wikipedia: Resignation", "category": "employment"},
    
    # ENERGY & ENVIRONMENT (correlates with: oil prices, energy stocks)
    {"article": "Oil_price", "display_name": "Wikipedia: Oil Price", "category": "energy"},
    {"article": "Solar_power", "display_name": "Wikipedia: Solar Power", "category": "energy"},
    {"article": "Natural_gas", "display_name": "Wikipedia: Natural Gas", "category": "energy"},
    {"article": "Climate_change", "display_name": "Wikipedia: Climate Change", "category": "energy"},
    
    # GEOPOLITICS (correlates with: VIX, market volatility)
    {"article": "War", "display_name": "Wikipedia: War", "category": "geopolitics"},
    {"article": "Sanctions", "display_name": "Wikipedia: Sanctions", "category": "geopolitics"},
    {"article": "Trade_war", "display_name": "Wikipedia: Trade War", "category": "geopolitics"},
]


# ==============================================================================
# LAYER 1: FAST BEHAVIORAL SIGNALS - Reddit Subreddit Activity
# ==============================================================================
# Cross-validation source for Wikipedia signals
# When BOTH Wikipedia AND Reddit show spikes, confidence is higher!

REDDIT_SUBREDDITS = [
    # EMPLOYMENT & CAREER (cross-validates: wiki_layoff, wiki_job-hunting)
    {"subreddit": "layoffs", "display_name": "Reddit: r/layoffs", "category": "employment"},
    {"subreddit": "recruitinghell", "display_name": "Reddit: r/recruitinghell", "category": "employment"},
    {"subreddit": "antiwork", "display_name": "Reddit: r/antiwork", "category": "employment"},
    {"subreddit": "jobs", "display_name": "Reddit: r/jobs", "category": "employment"},
    {"subreddit": "careerguidance", "display_name": "Reddit: r/careerguidance", "category": "employment"},
    
    # FINANCE & ECONOMY (cross-validates: wiki_recession, wiki_inflation)
    {"subreddit": "personalfinance", "display_name": "Reddit: r/personalfinance", "category": "finance"},
    {"subreddit": "povertyfinance", "display_name": "Reddit: r/povertyfinance", "category": "finance"},
    {"subreddit": "investing", "display_name": "Reddit: r/investing", "category": "finance"},
    {"subreddit": "stocks", "display_name": "Reddit: r/stocks", "category": "finance"},
    {"subreddit": "wallstreetbets", "display_name": "Reddit: r/wallstreetbets", "category": "finance"},
    
    # CRYPTO (cross-validates: wiki_bitcoin, wiki_cryptocurrency)
    {"subreddit": "cryptocurrency", "display_name": "Reddit: r/cryptocurrency", "category": "crypto"},
    {"subreddit": "bitcoin", "display_name": "Reddit: r/bitcoin", "category": "crypto"},
    {"subreddit": "ethereum", "display_name": "Reddit: r/ethereum", "category": "crypto"},
    
    # TECHNOLOGY (cross-validates: wiki_artificial-intelligence)
    {"subreddit": "technology", "display_name": "Reddit: r/technology", "category": "technology"},
    {"subreddit": "MachineLearning", "display_name": "Reddit: r/MachineLearning", "category": "technology"},
    {"subreddit": "artificial", "display_name": "Reddit: r/artificial", "category": "technology"},
    
    # HOUSING (cross-validates: wiki_real-estate, wiki_mortgage)
    {"subreddit": "REBubble", "display_name": "Reddit: r/REBubble", "category": "housing"},
    {"subreddit": "RealEstate", "display_name": "Reddit: r/RealEstate", "category": "housing"},
    {"subreddit": "FirstTimeHomeBuyer", "display_name": "Reddit: r/FirstTimeHomeBuyer", "category": "housing"},
]


def setup_wikipedia_variables():
    """Add Wikipedia pageviews variables to database"""
    print("=" * 60)
    print("SETTING UP LAYER 1: FAST BEHAVIORAL SIGNALS")
    print("=" * 60)
    print(f"Adding {len(WIKIPEDIA_ARTICLES)} Wikipedia pageview variables...")
    print()
    
    added = 0
    skipped = 0
    
    with get_db_session() as session:
        for wiki in WIKIPEDIA_ARTICLES:
            # Create unique variable name
            var_name = f"wiki_{wiki['article'].lower().replace(',', '').replace('.', '').replace('_', '-')}"
            
            # Check if already exists
            existing = session.query(VariableMetadata).filter(
                VariableMetadata.name == var_name
            ).first()
            
            if existing:
                print(f"  ⏭️  Skipping (exists): {wiki['display_name']}")
                skipped += 1
                continue
            
            # Create variable metadata
            var = VariableMetadata(
                name=var_name,
                display_name=wiki['display_name'],
                unit="pageviews",
                data_type="time_series",
                source="wikipedia",
                api_endpoint="https://wikimedia.org/api/rest_v1/metrics/pageviews/",
                update_frequency="monthly",
                parameters=json.dumps({
                    "article": wiki['article'],
                    "category": wiki['category']
                }),
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            session.add(var)
            added += 1
            print(f"  ✅ Added: {wiki['display_name']}")
        
        session.commit()
    
    print()
    print("=" * 60)
    print(f"SUMMARY: Added {added} new variables, skipped {skipped} existing")
    print("=" * 60)
    print()
    print("Next steps:")
    print("  1. Deploy to Railway: git push")
    print("  2. Trigger data fetch: POST /api/admin/fetch-data")
    print("  3. Recalculate correlations: POST /api/admin/calculate-correlations")
    print()
    
    return {"added": added, "skipped": skipped}


def setup_reddit_variables():
    """Add Reddit subreddit activity variables to database"""
    print("=" * 60)
    print("SETTING UP LAYER 1: REDDIT BEHAVIORAL SIGNALS")
    print("=" * 60)
    print(f"Adding {len(REDDIT_SUBREDDITS)} Reddit subreddit variables...")
    print()
    
    added = 0
    skipped = 0
    
    with get_db_session() as session:
        for reddit in REDDIT_SUBREDDITS:
            # Create unique variable name
            var_name = f"reddit_{reddit['subreddit'].lower()}"
            
            # Check if already exists
            existing = session.query(VariableMetadata).filter(
                VariableMetadata.name == var_name
            ).first()
            
            if existing:
                print(f"  ⏭️  Skipping (exists): {reddit['display_name']}")
                skipped += 1
                continue
            
            # Create variable metadata
            var = VariableMetadata(
                name=var_name,
                display_name=reddit['display_name'],
                unit="posts",
                data_type="time_series",
                source="reddit",
                api_endpoint="https://reddit.com/",
                update_frequency="daily",
                parameters=json.dumps({
                    "subreddit": reddit['subreddit'],
                    "category": reddit['category']
                }),
                is_active=True,
                created_at=datetime.utcnow()
            )
            
            session.add(var)
            added += 1
            print(f"  ✅ Added: {reddit['display_name']}")
        
        session.commit()
    
    print()
    print("=" * 60)
    print(f"SUMMARY: Added {added} Reddit variables, skipped {skipped} existing")
    print("=" * 60)
    
    return {"added": added, "skipped": skipped}


if __name__ == "__main__":
    setup_wikipedia_variables()
    setup_reddit_variables()
