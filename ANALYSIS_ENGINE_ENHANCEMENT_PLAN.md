# Analysis Engine Enhancement Plan
**Date**: November 13, 2025  
**Goal**: Transform correlation engine to support metric-level granularity and scale to thousands of variables

## Current State Analysis

### What We Have (Entity-Level)
- **61 variables** = 61 entities (one variable per stock, country, etc.)
- **Variable Examples**:
  - `stock_nvda` → "NVDA Stock Price" (single price value)
  - `gdp_brazil` → "Brazil GDP" (single GDP value)
  - `earthquake_count` → "Daily Earthquake Count"

### What We Need (Metric-Level)
- **200+ variables** = Multiple metrics per entity
- **Variable Examples**:
  ```
  Bitcoin entity → 4 variables:
    - "Bitcoin - Close Price (USD)"
    - "Bitcoin - Open Price (USD)"
    - "Bitcoin - Trading Volume"
    - "Bitcoin - Market Cap (USD)"
  
  UK Commodities entity → 2 variables:
    - "UK Commodities - Cornetto Sales (£)"
    - "UK Commodities - Cornetto Sales Volume (units)"
  
  NVDA entity → 5 variables:
    - "NVDA - Close Price (USD)"
    - "NVDA - Open Price (USD)"
    - "NVDA - High Price (USD)"
    - "NVDA - Low Price (USD)"
    - "NVDA - Trading Volume"
  ```

### Business Impact
**Current Problem**: Can only discover entity-level correlations  
❌ "Bitcoin ↔ UK Commodities" (too broad, not actionable)

**Desired Outcome**: Discover metric-level correlations  
✅ "Bitcoin - Close Price (USD) ↔ UK Commodities - Cornetto Sales (£)" (specific, exploitable)

**Use Case**: User can identify that Bitcoin close price correlates with Cornetto ice cream sales, then:
1. Buy Bitcoin
2. Launch Cornetto sales campaign
3. Flood market with Cornetto sales
4. Watch Bitcoin price rise due to correlation

## Architecture Changes Required

### Phase 1: Database Schema (No Breaking Changes)
Current `VariableMetadata` columns:
```python
id: Integer
name: String(255)              # Technical ID: "stock_nvda"
display_name: String(255)      # User display: "NVDA Stock Price"
unit: String(50)               # "USD", "count", etc.
data_type: String(50)          # "time_series", "count", "event"
source: String(100)            # "alpha_vantage", "worldbank", etc.
```

**Add New Columns** (backward compatible):
```python
entity_name: String(255)       # "Bitcoin", "NVDA", "UK Commodities"
metric_name: String(255)       # "Close Price", "Sales Revenue", "Volume"
metric_unit: String(50)        # "USD", "£", "units", "shares"
```

**Migration Strategy**:
1. Add new columns with NULL allowed
2. Populate existing variables: `entity_name = display_name`, `metric_name = NULL`
3. New variables use full format: `display_name = f"{entity_name} - {metric_name} ({metric_unit})"`

### Phase 2: Data Fetcher Refactoring
Transform from single-metric to multi-metric fetchers.

#### Current Pattern (Single Metric)
```python
def fetch_stock_data_monthly(symbol: str) -> Dict[str, float]:
    """Returns ONE price stream"""
    # API call to Alpha Vantage
    return {
        "2025-01-01": 150.25,   # Only close price
        "2025-02-01": 152.30,
        ...
    }
```

#### New Pattern (Multiple Metrics)
```python
def fetch_stock_metrics_monthly(symbol: str) -> Dict[str, Dict[str, float]]:
    """Returns MULTIPLE metrics per stock"""
    # API call to Alpha Vantage (or upgrade to better API)
    return {
        f"{symbol} - Close Price (USD)": {
            "2025-01-01": 150.25,
            "2025-02-01": 152.30,
        },
        f"{symbol} - Open Price (USD)": {
            "2025-01-01": 149.80,
            "2025-02-01": 151.50,
        },
        f"{symbol} - Trading Volume": {
            "2025-01-01": 1500000,
            "2025-02-01": 1650000,
        },
        f"{symbol} - Market Cap (USD)": {
            "2025-01-01": 500000000000,
            "2025-02-01": 505000000000,
        }
    }
```

### Phase 3: New Data Sources

#### Crypto API (CoinGecko - FREE TIER)
**Endpoint**: `https://api.coingecko.com/api/v3/coins/{id}/market_chart/range`

**Metrics Available**:
- Close Price (USD, GBP, EUR)
- Market Cap
- Trading Volume (24h)

**Example Variables Created**:
```
Bitcoin - Close Price (USD)
Bitcoin - Close Price (GBP)
Bitcoin - Market Cap (USD)
Bitcoin - Trading Volume
Ethereum - Close Price (USD)
Ethereum - Market Cap (USD)
```

**Implementation**:
```python
def fetch_crypto_metrics_monthly(coin_id: str, months: int = 60) -> Dict[str, Dict[str, float]]:
    """
    Fetch multiple crypto metrics from CoinGecko
    
    Args:
        coin_id: "bitcoin", "ethereum", etc.
        months: Number of months of historical data
    
    Returns:
        Dict of {metric_name: {timestamp: value}}
    """
    # Calculate date range
    end_date = datetime.now()
    start_date = end_date - timedelta(days=months * 30)
    
    # API call
    url = f"https://api.coingecko.com/api/v3/coins/{coin_id}/market_chart/range"
    params = {
        "vs_currency": "usd",
        "from": int(start_date.timestamp()),
        "to": int(end_date.timestamp())
    }
    
    response = requests.get(url, params=params)
    data = response.json()
    
    # Parse into monthly aggregates
    prices_monthly = aggregate_to_monthly(data["prices"])
    market_caps_monthly = aggregate_to_monthly(data["market_caps"])
    volumes_monthly = aggregate_to_monthly(data["total_volumes"])
    
    return {
        f"{coin_id.title()} - Close Price (USD)": prices_monthly,
        f"{coin_id.title()} - Market Cap (USD)": market_caps_monthly,
        f"{coin_id.title()} - Trading Volume": volumes_monthly
    }
```

#### UK Commodities API (ONS - Office for National Statistics)
**Endpoint**: `https://api.ons.gov.uk/timeseries/{series_id}/dataset/QNA/data`

**Metrics Available**:
- Retail sales (£ millions)
- Consumer price indices
- Production indices
- Food & beverage sales

**Example Variables Created**:
```
UK Retail - Ice Cream Sales (£)
UK Retail - Chocolate Sales (£)
UK Retail - Total Food Sales (£)
UK Consumer Price Index - Food
```

**Note**: ONS doesn't have product-level data like "Cornetto sales". For that, we'd need:
- **Nielsen/IRI**: Commercial retail scan data (paid)
- **Kantar**: Consumer panel data (paid)
- **Alternative**: Use ice cream category sales as proxy

#### Economic Indicators (FRED - Federal Reserve Economic Data)
**Endpoint**: `https://api.stlouisfed.org/fred/series/observations`

**Metrics Available** (examples):
- Interest rates (US Fed Rate, UK Bank Rate)
- Inflation rates (CPI, RPI)
- Unemployment rates
- GDP growth rates
- Currency exchange rates

**Example Variables Created**:
```
US Economy - Federal Funds Rate (%)
UK Economy - Bank of England Rate (%)
US Economy - CPI Inflation (%)
UK Economy - Unemployment Rate (%)
USD/GBP - Exchange Rate
```

### Phase 4: Data Ingestion Service Updates

#### Current: Single Variable per API Call
```python
def _fetch_stock_data(self, symbol: str):
    """Creates ONE VariableMetadata entry"""
    data = data_fetcher.fetch_stock_data_monthly(symbol)
    
    # Create single variable
    var = VariableMetadata(
        name=f"stock_{symbol.lower()}",
        display_name=f"{symbol} Stock Price",
        source="alpha_vantage"
    )
    session.add(var)
    
    # Store single time series
    for timestamp, value in data.items():
        ts = TimeSeriesData(variable_id=var.id, timestamp=timestamp, value=value)
        session.add(ts)
```

#### New: Multiple Variables per API Call
```python
def _fetch_stock_metrics(self, symbol: str):
    """Creates MULTIPLE VariableMetadata entries"""
    metrics_data = data_fetcher.fetch_stock_metrics_monthly(symbol)
    
    # Create multiple variables, one per metric
    for metric_display_name, time_series in metrics_data.items():
        # Parse metric components
        # "NVDA - Close Price (USD)" → entity="NVDA", metric="Close Price", unit="USD"
        entity, metric_with_unit = metric_display_name.split(" - ")
        metric, unit = metric_with_unit.rsplit(" (", 1)
        unit = unit.rstrip(")")
        
        # Create variable
        var = VariableMetadata(
            name=f"stock_{symbol.lower()}_{metric.lower().replace(' ', '_')}",
            display_name=metric_display_name,
            entity_name=entity,
            metric_name=metric,
            metric_unit=unit,
            unit=unit,
            source="alpha_vantage",
            data_type="time_series"
        )
        session.add(var)
        session.flush()  # Get var.id
        
        # Store time series for this metric
        for timestamp, value in time_series.items():
            ts = TimeSeriesData(
                variable_id=var.id,
                timestamp=timestamp,
                value=value
            )
            session.add(ts)
```

## Performance & Scalability

### Correlation Calculation: N×N Matrix

#### Current Workload
- 61 variables → 61×61 = **3,721 correlation pairs**
- Current time: ~5 seconds
- All pairs stored in database

#### Target Workload (Phase 1: 200 variables)
- 200 variables → 200×200 = **40,000 correlation pairs**
- Estimated time: ~2 minutes (optimized)
- Storage: ~5MB in database

#### Future Workload (Phase 2: 1,000 variables)
- 1,000 variables → 1,000×1,000 = **1,000,000 correlation pairs**
- Estimated time: ~30 minutes (batch processing)
- Storage: ~100MB in database

### Optimization Strategies

#### 1. Batch Processing
```python
def calculate_all_correlations(self, batch_size: int = 50):
    """Process variables in batches to avoid memory issues"""
    variables = session.query(VariableMetadata).all()
    
    for i in range(0, len(variables), batch_size):
        batch = variables[i:i + batch_size]
        
        # Calculate correlations for this batch
        for var1 in batch:
            for var2 in variables:
                if var2.id <= var1.id:
                    continue
                
                # Calculate correlation
                result = self._calculate_pair_correlation(var1, var2)
                
                # Store if significant
                if result['p_value'] < 0.05:
                    session.add(CorrelationResult(**result))
        
        session.commit()
        logger.info(f"Processed batch {i//batch_size + 1}")
```

#### 2. Parallel Processing
```python
from concurrent.futures import ProcessPoolExecutor
import multiprocessing

def calculate_all_correlations_parallel(self):
    """Use multiple CPU cores for calculation"""
    variables = session.query(VariableMetadata).all()
    
    # Create variable pairs (upper triangle only)
    pairs = [
        (var1.id, var2.id)
        for i, var1 in enumerate(variables)
        for var2 in variables[i+1:]
    ]
    
    # Process in parallel (one pair per worker)
    num_workers = multiprocessing.cpu_count()
    
    with ProcessPoolExecutor(max_workers=num_workers) as executor:
        results = executor.map(
            calculate_correlation_worker,
            pairs,
            chunksize=100
        )
    
    # Store results
    for result in results:
        if result['p_value'] < 0.05:
            session.add(CorrelationResult(**result))
    
    session.commit()
```

#### 3. Incremental Updates
```python
def calculate_new_correlations_only(self):
    """Only calculate correlations for new variables"""
    
    # Find variables without correlations
    existing_var_ids = session.query(
        CorrelationResult.variable1_id,
        CorrelationResult.variable2_id
    ).distinct().all()
    
    existing_set = {
        tuple(sorted([v1, v2])) for v1, v2 in existing_var_ids
    }
    
    all_vars = session.query(VariableMetadata).all()
    
    # Only calculate missing pairs
    for i, var1 in enumerate(all_vars):
        for var2 in all_vars[i+1:]:
            pair = tuple(sorted([var1.id, var2.id]))
            
            if pair not in existing_set:
                result = self._calculate_pair_correlation(var1, var2)
                session.add(CorrelationResult(**result))
    
    session.commit()
```

#### 4. Database Indexing
```sql
-- Optimize correlation lookups
CREATE INDEX idx_corr_strength ON correlation_results(abs_correlation DESC);
CREATE INDEX idx_corr_significance ON correlation_results(is_significant, abs_correlation DESC);
CREATE INDEX idx_corr_source_domain ON correlation_results(source1, source2);
CREATE INDEX idx_corr_vars ON correlation_results(variable1_id, variable2_id);

-- Optimize time series joins
CREATE INDEX idx_ts_var_timestamp ON time_series_data(variable_id, timestamp);
CREATE INDEX idx_ts_timestamp ON time_series_data(timestamp);
```

#### 5. Caching Top Results
```python
class CorrelationAnalysisService:
    def __init__(self):
        self._top_correlations_cache = None
        self._cache_timestamp = None
    
    def get_top_correlations(self, limit: int = 20, cross_domain: bool = False):
        """Cache top correlations for 1 hour"""
        cache_key = f"{limit}_{cross_domain}"
        
        # Check cache
        if (self._top_correlations_cache and 
            self._cache_timestamp and
            (datetime.now() - self._cache_timestamp).seconds < 3600):
            return self._top_correlations_cache.get(cache_key)
        
        # Calculate and cache
        results = self._fetch_top_correlations(limit, cross_domain)
        
        if not self._top_correlations_cache:
            self._top_correlations_cache = {}
        
        self._top_correlations_cache[cache_key] = results
        self._cache_timestamp = datetime.now()
        
        return results
```

## Implementation Roadmap

### Week 1: Foundation (Database & Core Refactoring)
- [ ] Day 1: Add new columns to VariableMetadata (entity_name, metric_name, metric_unit)
- [ ] Day 2: Create migration script to populate existing variables
- [ ] Day 3: Refactor data_fetcher.py to support multi-metric pattern
- [ ] Day 4: Update data_ingestion_service.py to create multiple variables per entity
- [ ] Day 5: Test with existing Alpha Vantage stocks (add volume, market cap if available)

### Week 2: New Data Sources
- [ ] Day 1: Integrate CoinGecko API for crypto metrics (Bitcoin, Ethereum, etc.)
- [ ] Day 2: Integrate FRED API for economic indicators (interest rates, inflation)
- [ ] Day 3: Research UK commodities data sources (ONS or commercial)
- [ ] Day 4: Implement chosen commodities API
- [ ] Day 5: Test data ingestion with all new sources

### Week 3: Performance & Optimization
- [ ] Day 1: Implement batch processing for correlation calculation
- [ ] Day 2: Add parallel processing with multiprocessing
- [ ] Day 3: Create incremental update logic (only new pairs)
- [ ] Day 4: Add database indexes for performance
- [ ] Day 5: Implement caching for top correlations

### Week 4: Testing & Validation
- [ ] Day 1: Test with 200 variables (40,000 pairs)
- [ ] Day 2: Verify specific correlations: "Bitcoin Close ↔ Cornetto Sales"
- [ ] Day 3: Performance benchmarking (calculation time, query time)
- [ ] Day 4: Load testing (simulate 1,000 variables)
- [ ] Day 5: Production deployment and monitoring

## Success Criteria

### Functional Requirements
✅ **Metric-Level Granularity**: Variables display as "Bitcoin - Close Price (USD)", not "Bitcoin"  
✅ **Cross-Domain Discovery**: Can identify "Bitcoin Close ↔ UK Ice Cream Sales"  
✅ **Scalability**: Handles 200+ variables (40,000+ pairs) efficiently  
✅ **Performance**: Correlation calculation completes in < 5 minutes for 200 variables  
✅ **Backward Compatibility**: Existing 61 entity-level variables still work  

### Business Value
✅ **Exploitable Insights**: User can discover actionable metric-level correlations  
✅ **Nuanced Analysis**: Differentiates between "Bitcoin Open" vs "Bitcoin Close" correlations  
✅ **Strategic Opportunities**: Identifies specific intervention points (e.g., launch Cornetto sales to boost Bitcoin)  

## Risk Assessment

### Technical Risks
1. **API Rate Limits**: Free tier APIs may throttle requests
   - **Mitigation**: Implement exponential backoff, use paid tiers if needed
   
2. **Data Alignment**: Different APIs may have different timestamps
   - **Mitigation**: Monthly aggregation normalizes all data to first-of-month

3. **Calculation Time**: 40,000 pairs could take too long
   - **Mitigation**: Parallel processing, batch jobs, incremental updates

### Data Quality Risks
1. **Missing Metrics**: Some data sources may not have all desired metrics
   - **Mitigation**: Use proxy metrics, find alternative data sources

2. **Proxy Data**: "Cornetto sales" may not exist, must use "ice cream sales"
   - **Mitigation**: Document proxy relationships, validate correlations

### Business Risks
1. **Correlation ≠ Causation**: Strong correlation doesn't mean exploitable
   - **Mitigation**: Add causality analysis layer (Granger causality tests)

2. **Spurious Correlations**: May discover meaningless relationships
   - **Mitigation**: Cross-domain filtering, p-value thresholds, manual review

## Next Steps (Immediate)

1. ✅ Deploy modal fix (v2.0.11)
2. 🔄 Test modal functionality in production
3. ⏳ Begin database schema enhancement (add entity_name, metric_name columns)
4. ⏳ Refactor data_fetcher.py for multi-metric support
5. ⏳ Integrate CoinGecko API for Bitcoin metrics (proof of concept)

---
**Last Updated**: November 13, 2025  
**Status**: Modal fix deployed, ready to begin engine enhancement
