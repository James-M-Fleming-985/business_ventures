# Current Dataset Granularity Analysis
**Date**: November 13, 2025  
**Question**: Can we prove the concept with existing datasets, or do we need more granular data sources?

---

## Current Data Inventory (61 Variables)

### 1. **Alpha Vantage Stocks** (10 variables)
**Current Granularity**: Entity-level (ONE metric per stock)
- AAPL Stock Price, AMZN Stock Price, GOOGL Stock Price, etc.
- **What we get**: End-of-month closing price ONLY
- **What's missing**: Open, High, Low, Volume, Market Cap

**API Capability Check**:
```python
# Alpha Vantage TIME_SERIES_MONTHLY response includes:
{
  "Monthly Time Series": {
    "2025-11-29": {
      "1. open": "150.00",        # ✅ AVAILABLE
      "2. high": "155.00",        # ✅ AVAILABLE  
      "3. low": "148.00",         # ✅ AVAILABLE
      "4. close": "152.50",       # ✅ CURRENTLY USED
      "5. volume": "50000000"     # ✅ AVAILABLE
    }
  }
}
```

**✅ VERDICT**: We can extract **5 metrics per stock** from existing API!
- Stock - Close Price (USD)
- Stock - Open Price (USD)
- Stock - High Price (USD)
- Stock - Low Price (USD)
- Stock - Trading Volume

**Proof of Concept**: YES, with minor refactoring of data_fetcher.py

---

### 2. **World Bank GDP** (20 variables)
**Current Granularity**: Entity-level (ONE metric per country)
- Australia GDP, Brazil GDP, Canada GDP, etc.
- **What we get**: GDP value only
- **What's missing**: GDP growth %, GDP per capita, other economic indicators

**API Capability Check**:
World Bank API supports multiple indicators per country:
```
https://api.worldbank.org/v2/country/USA/indicator/{INDICATOR_CODE}

Available indicators:
- NY.GDP.MKTP.CD          # GDP (current US$) ✅ CURRENTLY USED
- NY.GDP.MKTP.KD.ZG       # GDP growth (annual %) ✅ AVAILABLE
- NY.GDP.PCAP.CD          # GDP per capita (current US$) ✅ AVAILABLE
- FP.CPI.TOTL.ZG          # Inflation, consumer prices (annual %) ✅ AVAILABLE
- SL.UEM.TOTL.ZS          # Unemployment, total (% of total labor force) ✅ AVAILABLE
```

**✅ VERDICT**: We can extract **5+ metrics per country** from World Bank API!
- Country - GDP (USD)
- Country - GDP Growth (%)
- Country - GDP Per Capita (USD)
- Country - Inflation Rate (%)
- Country - Unemployment Rate (%)

**Proof of Concept**: YES, API supports multiple indicators

---

### 3. **USGS Earthquakes** (1 variable)
**Current Granularity**: Aggregate count
- Daily Earthquake Count
- **What we get**: Count of earthquakes per month
- **What's missing**: Magnitude distribution, depth, geographic clustering

**API Capability Check**:
USGS Earthquake API provides detailed event data:
```json
{
  "features": [
    {
      "properties": {
        "mag": 5.2,              # ✅ AVAILABLE
        "place": "Pacific Ocean",
        "time": 1699900800000,
        "depth": 10.0,           # ✅ AVAILABLE
        "type": "earthquake"
      },
      "geometry": {
        "coordinates": [-125.0, 40.0, 10.0]  # ✅ AVAILABLE
      }
    }
  ]
}
```

**Potential Metrics** (requires aggregation):
- Earthquakes - Total Count (currently used)
- Earthquakes - Average Magnitude
- Earthquakes - Maximum Magnitude
- Earthquakes - Average Depth (km)
- Earthquakes - Count by Region (Pacific, Atlantic, etc.)

**⚠️ VERDICT**: Limited granularity improvement
- Can extract **3-4 metrics** but less business relevance
- Earthquakes don't have multiple "products" like stocks/GDP

**Proof of Concept**: PARTIAL - can improve but limited value

---

### 4. **NASA EONET Environmental Events** (10 variables)
**Current Granularity**: Event counts by type
- Wildfires Events, Severe Storms Events, Volcanoes Events, etc.
- **What we get**: Count of events per month by type
- **What's missing**: Event severity, duration, geographic distribution

**API Capability Check**:
EONET provides event-level data but limited metrics:
```json
{
  "events": [
    {
      "title": "Wildfire - California",
      "categories": [{"id": "wildfires"}],
      "geometries": [{
        "date": "2025-11-01T00:00:00Z",
        "coordinates": [-120.0, 38.0]
      }]
    }
  ]
}
```

**Potential Metrics**:
- Event Type - Count (currently used)
- Event Type - Duration (days)
- Event Type - Geographic Spread (area)

**⚠️ VERDICT**: Limited granularity improvement
- Can extract **2-3 metrics per event type**
- No "price" or "volume" equivalent

**Proof of Concept**: PARTIAL - can improve but limited

---

### 5. **ArXiv Research Papers** (10 variables)
**Current Granularity**: Paper counts by topic
- AI Papers, Cryptography Papers, Climate Science Papers, etc.
- **What we get**: Count of papers published per month
- **What's missing**: Citation counts, author counts, collaboration metrics

**API Capability Check**:
ArXiv API provides paper-level data:
```xml
<entry>
  <title>Paper Title</title>
  <author><name>Author Name</name></author>
  <published>2025-11-01T00:00:00Z</published>
  <category term="cs.AI"/>
</entry>
```

**Potential Metrics**:
- Topic - Paper Count (currently used)
- Topic - Author Count (unique authors)
- Topic - Multi-author Papers (%)
- Topic - Average Authors per Paper

**⚠️ VERDICT**: Limited granularity improvement
- Can extract **3-4 metrics** but citations not available via API
- No "economic value" metrics

**Proof of Concept**: PARTIAL - can improve but limited value

---

### 6. **ClinicalTrials.gov** (10 variables)
**Current Granularity**: Trial counts by condition
- Cancer Trials, COVID-19 Trials, Alzheimer Trials, etc.
- **What we get**: Count of trials per month
- **What's missing**: Trial phase, enrollment, funding

**API Capability Check**:
ClinicalTrials API provides trial-level data:
```json
{
  "StudyFieldsResponse": {
    "StudyFields": [{
      "NCTId": "NCT12345678",
      "Phase": ["Phase 3"],              # ✅ AVAILABLE
      "EnrollmentCount": 500,             # ✅ AVAILABLE
      "StudyType": "Interventional",
      "CompletionDate": "2026-12-01"
    }]
  }
}
```

**Potential Metrics**:
- Condition - Trial Count (currently used)
- Condition - Phase 3 Trial Count
- Condition - Average Enrollment Size
- Condition - Completed Trials (%)

**✅ VERDICT**: Can extract **4-5 metrics per condition**
- Proof of Concept: YES, API supports it

---

## Summary: Can We Prove the Concept?

### ✅ **YES - With Current Data Sources!**

**High-Value Granularity Opportunities** (prove concept without new APIs):

1. **Stock Data** (10 stocks × 5 metrics = **50 variables**)
   - Close, Open, High, Low, Volume
   - **Business Value**: Discover if "NVDA Close" correlates differently than "NVDA Volume"
   - **Exploitability**: High - can trade on specific price/volume correlations

2. **GDP Data** (20 countries × 5 metrics = **100 variables**)
   - GDP, GDP Growth %, GDP Per Capita, Inflation, Unemployment
   - **Business Value**: "Brazil GDP Growth %" vs "AMZN Stock Close Price"
   - **Exploitability**: High - macroeconomic trading signals

3. **Clinical Trials** (10 conditions × 4 metrics = **40 variables**)
   - Total, Phase 3, Enrollment, Completion Rate
   - **Business Value**: "Cancer Phase 3 Trials" vs "Pharma Stock Prices"
   - **Exploitability**: Medium - biotech investment insights

**Total with Current APIs**: **190 variables** (vs current 61)

---

## Recommendation: Two-Phase Approach

### **Phase 1: Prove Concept with Current APIs** (Recommended START HERE)

**Refactor existing data fetchers to extract multiple metrics:**

1. **Week 1**: Stocks (61 → 50 new variables)
   - Modify `fetch_stock_data_monthly()` to return 5 metrics
   - Granularity example: "NVDA - Close Price (USD)" vs "NVDA - Trading Volume"
   
2. **Week 2**: GDP (20 → 100 new variables)
   - Add `fetch_gdp_indicators()` for growth %, per capita, inflation, unemployment
   - Granularity example: "Brazil - GDP Growth (%)" vs "Brazil - Unemployment Rate (%)"

3. **Week 3**: Clinical Trials (10 → 40 new variables)
   - Add phase breakdown, enrollment metrics
   - Granularity example: "Cancer - Phase 3 Trials" vs "Cancer - Average Enrollment"

**Result**: 190 variables computing **18,050 correlation pairs**

**Test Cases for Proof of Concept**:
```
✅ "NVDA - Close Price (USD)" ↔ "Japan - GDP Growth (%)"
✅ "AMZN - Trading Volume" ↔ "Brazil - Inflation Rate (%)"
✅ "Cancer - Phase 3 Trials" ↔ "Pharma Stock Prices"
```

**Advantages**:
- ✅ No new API integrations needed
- ✅ Prove granularity concept works
- ✅ Validate N×N calculation performance (18K pairs)
- ✅ Test if metric-level correlations differ from entity-level
- ✅ 2-3 weeks implementation time

---

### **Phase 2: Add New High-Value Sources** (After proof of concept)

**Only if Phase 1 proves valuable, add:**

1. **Crypto (CoinGecko)**: Bitcoin/Ethereum with Close, Volume, Market Cap
   - Enables: "Bitcoin - Close Price (USD)" ↔ "Gold Price"
   
2. **Commodities (Quandl/FRED)**: Gold, Oil, Agriculture prices
   - Enables: "Gold - Price per Ounce (USD)" ↔ "Inflation Rate"

3. **UK Retail (ONS)**: Ice cream sales, consumer goods
   - Enables: Your "Cornetto Sales" use case (if data available)

**Total Phase 2**: 250+ variables, 31,250+ correlation pairs

---

## Immediate Next Steps

### 1. **Fix Modal** (IN PROGRESS - v2.0.12 deploying)
   - JavaScript data structure mismatch fixed
   - Test clicking heatmap tiles

### 2. **Refactor Stock Data Fetcher** (PROVE CONCEPT)
   ```python
   def fetch_stock_metrics_monthly(symbol: str, months: int = 60):
       """Returns dict of 5 metrics: close, open, high, low, volume"""
       # Parse Alpha Vantage response
       return {
           f"{symbol} - Close Price (USD)": {...},
           f"{symbol} - Open Price (USD)": {...},
           f"{symbol} - High Price (USD)": {...},
           f"{symbol} - Low Price (USD)": {...},
           f"{symbol} - Trading Volume": {...}
       }
   ```

### 3. **Test Granular Correlations**
   - Run correlation analysis on 50 stock metrics
   - Verify: Does "NVDA Close" correlate differently than "NVDA Volume"?
   - If YES → proceed with GDP, Trials
   - If NO → reconsider approach

---

## Answer to Your Question

**Q: Can we prove the concept with datasets we have, or do we need more?**

**A: YES - You can FULLY prove the concept with current datasets!**

**Why:**
1. ✅ Alpha Vantage already provides 5 metrics per stock (we only use 1)
2. ✅ World Bank already provides 5+ indicators per country (we only use 1)
3. ✅ ClinicalTrials already provides 4+ metrics per condition (we only use 1)
4. ✅ These yield **190 variables** = **18,050 correlation pairs** to analyze
5. ✅ Covers your use case: specific metric correlations vs broad entity correlations

**Example Granular Discoveries You Can Make NOW**:
- "Does NVDA's **closing price** correlate with Brazil's **GDP growth %**?"
- "Does Amazon's **trading volume** spike correlate with **unemployment rate** changes?"
- "Do **Phase 3 cancer trials** correlate with pharma **stock volatility**?"

**You DON'T need "Cornetto Sales" to prove the concept works.**

Prove it with stocks/GDP first, THEN add commodities if validated.

---

**Next Action**: Deploy modal fix, test it works, then refactor stock fetcher for multi-metric extraction.
