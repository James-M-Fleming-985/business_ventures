# Correlation Discovery Engine - Variable Inventory

**Date**: November 6, 2025  
**Project**: Causal Affect - Correlation Discovery Engine  
**Status**: Active Development

## Executive Summary

The Causal Affect platform currently integrates **6 real-world API sources** providing a minimum of **61 variables** for correlation analysis, with expansion potential to **156+ variables**. This creates a correlation matrix of **3,721+ correlation pairs** (conservative estimate) or **24,336+ pairs** (expanded).

**CRITICAL REQUIREMENT**: NO MOCK DATA - All analysis must use real API data to ensure MVP developers build on accurate insights.

---

## Data Source Breakdown

### 1. Stock Market Data (Alpha Vantage)
- **API**: Alpha Vantage TIME_SERIES_DAILY
- **Status**: Requires API key
- **Cost**: Free tier (5 calls/min, 500 calls/day)
- **Variables**: 10 (conservative) to 50 (expanded)
- **Examples**:
  - NVDA Stock Price (USD)
  - AAPL Stock Price (USD)
  - MSFT Stock Price (USD)
  - GOOGL Stock Price (USD)
  - AMZN Stock Price (USD)
- **Data Type**: Time series, daily closing prices
- **Historical Range**: 100 days (compact), 20+ years (full)

### 2. Earthquake Data (USGS)
- **API**: USGS Earthquake Feed
- **Status**: Active, no key required
- **Cost**: Free
- **Variables**: 1
- **Examples**:
  - Daily Earthquake Count (count)
- **Data Type**: Time series, daily event counts
- **Historical Range**: 30 days (month feed)

### 3. Environmental Events (NASA EONET)
- **API**: NASA Earth Observatory Natural Event Tracker
- **Status**: Active, no key required
- **Cost**: Free
- **Variables**: 10 (conservative) to 15 (expanded)
- **Examples**:
  - Wildfire Events (count)
  - Severe Storm Events (count)
  - Volcano Events (count)
  - Sea/Lake Ice Events (count)
  - Flood Events (count)
  - Drought Events (count)
  - Dust/Haze Events (count)
  - Landslide Events (count)
  - Snow Events (count)
  - Water Color Events (count)
- **Data Type**: Event counts by category
- **Historical Range**: Active events

### 4. GDP Data (World Bank)
- **API**: World Bank Data API
- **Status**: Active, no key required
- **Cost**: Free
- **Variables**: 20 (conservative) to 50 (expanded)
- **Examples**:
  - USA GDP (USD)
  - GBR GDP (USD)
  - CHN GDP (USD)
  - JPN GDP (USD)
  - DEU GDP (USD)
  - FRA GDP (USD)
- **Data Type**: Time series, annual GDP values
- **Historical Range**: 2015-2023

### 5. Research Papers (arXiv)
- **API**: arXiv API
- **Status**: Active, no key required
- **Cost**: Free
- **Variables**: 10 (conservative) to 20 (expanded)
- **Examples**:
  - Artificial Intelligence Papers (count)
  - Machine Learning Papers (count)
  - Quantum Physics Papers (count)
  - Astrophysics Papers (count)
  - Biotechnology Papers (count)
- **Data Type**: Paper counts by topic
- **Historical Range**: All time, searchable

### 6. Clinical Trials (ClinicalTrials.gov)
- **API**: ClinicalTrials.gov API v2
- **Status**: Active, no key required
- **Cost**: Free
- **Variables**: 10 (conservative) to 20 (expanded)
- **Examples**:
  - Cancer Clinical Trials (count)
  - Diabetes Clinical Trials (count)
  - COVID-19 Clinical Trials (count)
  - Alzheimer Clinical Trials (count)
  - Heart Disease Clinical Trials (count)
- **Data Type**: Active trial counts by condition
- **Historical Range**: Current active trials

---

## Variable Count Summary

### Conservative Estimate
| Data Source | Variables | Correlation Impact |
|-------------|-----------|-------------------|
| Stocks | 10 | 10 time series |
| Earthquakes | 1 | 1 time series |
| Environmental | 10 | 10 event categories |
| GDP | 20 | 20 country series |
| arXiv Papers | 10 | 10 topic counts |
| Clinical Trials | 10 | 10 condition counts |
| **TOTAL** | **61** | **3,721 pairs** |

**Correlation Matrix**: 61 × 61 = **3,721 unique correlation pairs**

### Expanded Estimate
| Data Source | Variables | Correlation Impact |
|-------------|-----------|-------------------|
| Stocks | 50 | 50 time series |
| Earthquakes | 1 | 1 time series |
| Environmental | 15 | 15 event categories |
| GDP | 50 | 50 country series |
| arXiv Papers | 20 | 20 topic counts |
| Clinical Trials | 20 | 20 condition counts |
| **TOTAL** | **156** | **24,336 pairs** |

**Correlation Matrix**: 156 × 156 = **24,336 unique correlation pairs**

---

## Scalability Considerations

### Current State
- **Variables**: 61 (minimum)
- **Correlation Pairs**: 3,721
- **Storage**: Railway Postgres (suitable for current scale)
- **Update Frequency**: Daily (configurable)

### Future State
- **Variables**: 156+ (with expansion)
- **Correlation Pairs**: 24,336+
- **Historical Data**: 50 years target
- **Storage Target**: 10TB+
- **Migration Path**: TimescaleDB when scaling beyond Postgres limits

### N×N Growth Pattern
The correlation matrix grows **exponentially** with variable count:
- 10 variables → 100 pairs
- 50 variables → 2,500 pairs
- 100 variables → 10,000 pairs
- 200 variables → 40,000 pairs

**Optimization Strategy**: Calculate and store correlation results, use materialized views, implement caching for frequently accessed pairs.

---

## Implementation in Code

### data_fetcher.py Methods
```python
class DataFetcher:
    def fetch_stock_data(symbol: str, days: int) -> List[float]
    def fetch_earthquake_count(days: int) -> List[int]
    def fetch_environmental_events(days: int) -> Dict[str, int]
    def fetch_gdp_data(country_code: str) -> List[float]
    def fetch_arxiv_papers(topic: str, max_results: int) -> int
    def fetch_clinical_trials(condition: str) -> int
```

### Current Status
- ✅ **data_fetcher.py**: Working, 6 API integrations implemented
- ✅ **correlation_analyzer.py**: Working, Pearson/Spearman/Kendall methods
- ❌ **routers/dashboard.py**: Currently uses 100% mock data (NEEDS REFACTORING)
- ⏳ **Database schema**: Not yet created (Railway Postgres available)

---

## Next Steps

1. **Database Setup**: Create schema for time_series_data, correlation_results, analysis_jobs, variable_metadata
2. **Data Ingestion**: Schedule daily API fetches using data_fetcher.py
3. **Correlation Engine**: Calculate N×N matrix for all 61+ variable pairs
4. **API Refactoring**: Remove ALL mock data from dashboard endpoints
5. **UI Enhancement**: Add date range selector, analysis frequency selector, top-N display control

**Critical Success Factor**: Maintain ZERO tolerance for mock/synthetic data in production. MVP developers must build on accurate, real-world insights.

---

## Variable Catalog (Sample)

| ID | Variable Name | Unit | Source | API Endpoint | Update Frequency |
|----|--------------|------|--------|--------------|------------------|
| 1 | NVDA Stock Price | USD | Alpha Vantage | TIME_SERIES_DAILY | Daily |
| 2 | AAPL Stock Price | USD | Alpha Vantage | TIME_SERIES_DAILY | Daily |
| 3 | Daily Earthquake Count | count | USGS | earthquake feed | Daily |
| 4 | Wildfire Events | count | NASA EONET | events API | Real-time |
| 5 | USA GDP | USD | World Bank | country indicator | Annual |
| 6 | AI Papers Count | count | arXiv | query API | Real-time |
| 7 | Cancer Trials | count | ClinicalTrials.gov | studies API | Real-time |
| ... | ... | ... | ... | ... | ... |

*Full catalog will be populated in database variable_metadata table*
