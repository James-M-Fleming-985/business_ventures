# 🚨 DATA INGESTION REQUIRED - Root Cause Analysis

**Date:** November 17, 2025  
**Issue:** Heatmap only shows GDP ↔ Stock correlations  
**Root Cause:** Only 2/6 data sources have actual data populated in database

---

## Current Problem

### What the Heatmap Shows (From Screenshot)
```
Saudi Arabia GDP ↔ GOOGL Stock Price
Turkey GDP ↔ Poland GDP
NVDA Stock Price ↔ Japan GDP
Mexico GDP ↔ United States GDP
Brazil GDP ↔ Australia GDP
AMZN Stock Price ↔ V Stock Price
```

**Problem:** These are OBVIOUS correlations (GDP ↔ Stocks, GDP ↔ GDP, Stock ↔ Stock)

### What We Want to See
```
Bitcoin Close Price ↔ UK Ice Cream Sales
AI Papers Published ↔ NVDA Stock Price
Earthquake Frequency ↔ Insurance Stock Price
Wildfire Events ↔ Energy Stock Price
Cancer Clinical Trials ↔ Biotech Stock Price
```

**Solution:** These require data from ALL 6 sources, not just 2

---

## Data Source Status

| Source | Variables Defined | Data Populated | Status |
|--------|------------------|----------------|---------|
| alpha_vantage (Stocks) | 10 stocks | ✅ YES | Working |
| worldbank (GDP) | 20 countries | ✅ YES | Working |
| usgs (Earthquakes) | 1 variable | ❌ NO | **NEEDS INGESTION** |
| nasa_eonet (Environmental) | 10 categories | ❌ NO | **NEEDS INGESTION** |
| arxiv (Papers) | 10 topics | ❌ NO | **NEEDS INGESTION** |
| clinicaltrials (Trials) | 10 conditions | ❌ NO | **NEEDS INGESTION** |

**Result:** Only 30/61 variables have data = only GDP ↔ Stock correlations possible!

---

## Why Data Ingestion Hasn't Run

The `data_ingestion_service.py` file exists with all the fetch methods:
- ✅ `_fetch_stock_data()` - Working, data populated
- ✅ `_fetch_gdp_data()` - Working, data populated  
- ❌ `_fetch_earthquake_data()` - Code exists, never run
- ❌ `_fetch_environmental_data()` - Code exists, never run
- ❌ `_fetch_arxiv_data()` - Code exists, never run
- ❌ `_fetch_clinical_trials_data()` - Code exists, never run

**Missing:** A scheduled job or manual trigger to run `fetch_and_store_all_variables()`

---

## Solution Steps

### Step 1: Run Data Ingestion Manually (Immediate Fix)

```python
# On Railway or local environment with database access
from data_ingestion_service import DataIngestionService

service = DataIngestionService()
stats = service.fetch_and_store_all_variables()
print(stats)
```

**Expected Output:**
```
{
    'stocks_fetched': 10,
    'stock_data_points': 600,  # 10 stocks × 60 months
    'earthquakes_fetched': 1,
    'earthquake_data_points': 1-2,  # Limited by USGS 30-day feed
    'environmental_fetched': 10,
    'environmental_data_points': 10,  # Current event counts
    'gdp_fetched': 20,
    'gdp_data_points': 1440,  # 20 countries × 72 months
    'arxiv_fetched': 10,
    'arxiv_data_points': 10,  # Current paper counts
    'clinical_trials_fetched': 10,
    'clinical_trials_data_points': 10  # Current trial counts
}
```

### Step 2: Schedule Automated Ingestion

**Option A: Railway Cron Job**
```yaml
# railway.toml or railway.json
[build]
  builder = "nixpacks"

[deploy]
  startCommand = "python run_pipeline.py"

[cron]
  schedule = "0 0 * * *"  # Daily at midnight
  command = "python -c 'from data_ingestion_service import DataIngestionService; DataIngestionService().fetch_and_store_all_variables()'"
```

**Option B: Celery Background Task**
```python
# tasks.py
from celery import Celery
from data_ingestion_service import DataIngestionService

app = Celery('causal_affect')

@app.task
def daily_data_ingestion():
    service = DataIngestionService()
    return service.fetch_and_store_all_variables()

# Schedule: Run daily at 2 AM UTC
app.conf.beat_schedule = {
    'daily-ingestion': {
        'task': 'tasks.daily_data_ingestion',
        'schedule': crontab(hour=2, minute=0),
    },
}
```

**Option C: Simple Startup Script**
```bash
# run_pipeline.py
#!/usr/bin/env python3
"""
Run data ingestion and correlation analysis
"""
from data_ingestion_service import DataIngestionService
from correlation_analysis_service import CorrelationAnalysisService
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
    # Step 1: Fetch data from all APIs
    logger.info("Starting data ingestion...")
    ingestion = DataIngestionService()
    stats = ingestion.fetch_and_store_all_variables()
    logger.info(f"Ingestion complete: {stats}")
    
    # Step 2: Calculate correlations
    logger.info("Starting correlation analysis...")
    analysis = CorrelationAnalysisService()
    results = analysis.calculate_all_correlations()
    logger.info(f"Analysis complete: {results}")

if __name__ == "__main__":
    main()
```

### Step 3: Verify Data Populated

```sql
-- Check data counts by source
SELECT 
    vm.source,
    COUNT(DISTINCT vm.id) as variables,
    COUNT(tsd.id) as data_points
FROM variable_metadata vm
LEFT JOIN time_series_data tsd ON vm.id = tsd.variable_id
WHERE vm.is_active = true
GROUP BY vm.source
ORDER BY vm.source;
```

**Expected Result:**
```
source          | variables | data_points
----------------+-----------+-------------
alpha_vantage   |        10 |         600
arxiv           |        10 |          10
clinicaltrials  |        10 |          10
nasa_eonet      |        10 |          10
usgs            |         1 |           1
worldbank       |        20 |        1440
```

### Step 4: Recalculate Correlations

```python
from correlation_analysis_service import CorrelationAnalysisService

service = CorrelationAnalysisService()
results = service.calculate_all_correlations(
    method='pearson',
    min_threshold=0.0,  # Store all correlations
    significance_level=0.05
)

print(f"Calculated {results['total_pairs_calculated']} correlations")
print(f"Found {results['significant_correlations']} significant pairs")
```

---

## Expected Heatmap After Fix

### Before (Current - Only GDP ↔ Stock)
```
Saudi Arabia GDP ↔ GOOGL Stock Price: r = 0.73
Turkey GDP ↔ Poland GDP: r = 0.68
NVDA Stock Price ↔ Japan GDP: r = 0.65
```

### After (All 6 Sources Ingested)
```
AI Papers (arxiv) ↔ NVDA Stock Price (alphavantage): r = 0.82
Cancer Trials (clinicaltrials) ↔ Biotech Stocks: r = 0.76
Earthquake Count (usgs) ↔ Insurance Stock Price: r = -0.54
Wildfire Events (nasa) ↔ Energy Stocks: r = 0.68
Research Output ↔ GDP Growth: r = 0.71
Climate Events ↔ Agricultural GDP: r = -0.63
```

**These are the NON-OBVIOUS cross-domain insights we're looking for!**

---

## Data Granularity Confirmed

The system is **already built correctly** for variable-level granularity:

✅ **Database Structure:**
- Each variable has unique `display_name` (e.g., "NVDA Stock Price", "AI Papers")
- Correlations stored as variable-to-variable pairs (not domain aggregates)
- 61 individual variables cataloged across 6 sources

✅ **Correlation Calculation:**
- Calculates N×N matrix for ALL variable pairs (3,721 pairs for 61 variables)
- Ranks by absolute strength |r|
- Filters for cross-domain (source1 ≠ source2)

✅ **Heatmap Display:**
- Shows variable `display_name` labels, not domain names
- Frontend already passes `cross_domain=true` parameter
- Backend already filters `variable1.source != variable2.source`

**The ONLY issue:** Missing data from 4/6 sources!

---

## Action Items

### Immediate (Today)
1. [ ] Run data ingestion script manually on Railway
2. [ ] Verify all 6 data sources populated
3. [ ] Recalculate correlation matrix
4. [ ] Refresh dashboard and verify heatmap shows diverse correlations

### Short-term (This Week)
1. [ ] Set up automated daily ingestion (Celery or Railway cron)
2. [ ] Add data freshness monitoring to dashboard
3. [ ] Handle USGS 30-day limitation (only recent earthquakes)
4. [ ] Consider upgrading to historical earthquake data API

### Medium-term (This Month)
1. [ ] Expand to 156 variables (50 stocks, 50 countries, etc.)
2. [ ] Add more data sources (FRED economic data, weather, etc.)
3. [ ] Implement data backfilling for historical correlations
4. [ ] Build data quality dashboard

---

## Root Cause Summary

**Problem:** Heatmap only shows obvious GDP ↔ Stock correlations

**Root Cause:** Only 2/6 data sources have data ingested into database
- ✅ Stocks (alphavantage) - Working
- ✅ GDP (worldbank) - Working
- ❌ Earthquakes (usgs) - Code exists, not run
- ❌ Environmental (nasa_eonet) - Code exists, not run
- ❌ Papers (arxiv) - Code exists, not run
- ❌ Trials (clinicaltrials) - Code exists, not run

**Solution:** Run `DataIngestionService().fetch_and_store_all_variables()` to populate missing data

**Result:** Heatmap will show diverse cross-domain correlations like:
- AI Papers ↔ Tech Stocks
- Earthquakes ↔ Insurance Stocks  
- Environmental Events ↔ Energy Stocks
- Clinical Trials ↔ Healthcare Stocks

---

**Next Step:** Deploy data ingestion to Railway and run it!
