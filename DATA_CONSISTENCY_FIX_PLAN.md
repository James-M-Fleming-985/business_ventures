# Data Universe Consistency Issue - Root Cause Analysis

## Problem
Time series and heat map visualizations show only 3-4 data points for some variables, making correlation analysis unreliable.

## Affected Variables
### Critical (3-4 data points):
- **Stock Data**: AMZN, V, NVDA - **3 points each**
- **GDP Data**: Poland, Japan, Australia - **3 points each**
- **Environmental**: Severe Storms - **4 points**
- **arXiv Papers**: Machine Learning - **4 points**

## Root Causes Identified

### 1. Missing Alpha Vantage API Key (CRITICAL)
**Impact**: All stock data variables have only 3 data points
**Cause**: `ALPHA_VANTAGE_API_KEY` environment variable not set in production
**Solution**: Add API key to Railway environment variables

```bash
# In Railway dashboard, add:
ALPHA_VANTAGE_API_KEY=<your_key_here>
```

### 2. World Bank API Timeout
**Impact**: Some GDP variables have limited data
**Cause**: World Bank API has 10-second timeout, but API is slow
**Solution**: Increase timeout to 30 seconds

### 3. NASA EONET Limited Historical Data
**Impact**: Some environmental event categories (Severe Storms) naturally have sparse data
**Cause**: EONET only tracks recent events for some categories
**Solution**: 
- Keep variables with sparse data but flag them
- Consider alternative data sources for these categories
- Or remove variables with consistently <10 data points

### 4. USGS Earthquake API Date Range Issue
**Impact**: Earthquake data not fetching
**Cause**: API returns 400 error for large date ranges (5 years)
**Solution**: Fetch in smaller chunks (1 year at a time)

## Fixes Implemented

### Fix 1: Increase API Timeouts
```python
# In data_fetcher.py
response = requests.get(url, params=params, timeout=30)  # Was 10
```

### Fix 2: Fix USGS Earthquake Fetching
```python
# Fetch in 1-year chunks instead of all at once
def fetch_earthquake_monthly(self, months: int = 60) -> Optional[Dict[str, int]]:
    # Split into yearly chunks to avoid API errors
```

### Fix 3: Add Environment Variable Check
```python
# Alert if API keys are missing
if not self.alpha_vantage_key:
    logger.critical("ALPHA_VANTAGE_API_KEY not set - stock data will fail!")
```

## Action Items

### Immediate (Deploy Today)
1. ✅ Increase API timeouts from 10s to 30s
2. ✅ Fix USGS earthquake API to fetch in chunks
3. ✅ Add API key validation warnings
4. ⏳ Add ALPHA_VANTAGE_API_KEY to Railway environment
5. ⏳ Run data refetch script to backfill missing data

### Short Term (This Week)
1. Add data quality check endpoint: `/api/admin/data-quality`
2. Create automated alerts for variables with <60 data points
3. Add retry logic for failed API calls
4. Document minimum data requirements per variable

### Medium Term (This Month)
1. Implement data quality dashboard
2. Add automatic re-fetch for stale/insufficient data
3. Consider removing variables that consistently fail to fetch data
4. Add alternative data sources for sparse categories

## Expected Outcomes
After fixes deployed:
- Stock variables: 3 → 60+ data points
- GDP variables: 3-9 → 120 data points (10 years × 12 months)
- Earthquake data: 0 → 60 data points
- arXiv papers: 4-21 → 60 data points
- Environmental events: Keep only categories with 30+ data points

## Testing
```bash
# Test data fetcher locally
python3 test_data_fetcher.py

# Run refetch script (after API key added)
python3 refetch_missing_data.py

# Verify data counts
python3 diagnose_production_data.py
```

## Monitoring
Add to health check endpoint:
```python
@app.get("/api/admin/data-health")
async def data_health_check(db: Session = Depends(get_db)):
    # Return count of variables with <60 data points
    # Alert if count > 5
```
