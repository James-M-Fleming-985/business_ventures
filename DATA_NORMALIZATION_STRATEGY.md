# Data Normalization Strategy for Cross-Domain Correlation Analysis

**Date**: November 9, 2025  
**Issue**: Zero cross-domain correlations due to misaligned timestamps  
**Goal**: Enable meaningful correlations across ALL data sources

---

## Problem Statement

Current system has **0 cross-domain correlations** despite 61 variables from 6 data sources because:
- Different sources use different time frequencies (daily, annual, snapshot)
- No overlapping timestamps = impossible to calculate correlations
- Example: Stocks are daily (2025-11-09), GDP is annual (2015-01-01, 2016-01-01)

**CRITICAL**: Correlation calculation requires matching timestamps across variables.

---

## Current Data Types & Frequencies

### 1. **Stocks (Alpha Vantage)** - PRICE DATA
- **Raw Type**: Daily closing prices (USD)
- **Current Frequency**: Daily
- **Current Range**: Last 30 days only
- **Example**: `NVDA: [145.23, 147.89, 143.12, ...]`
- **Issue**: Daily granularity doesn't match other sources

### 2. **GDP (World Bank)** - CURRENCY/VALUE DATA
- **Raw Type**: Annual GDP (USD, billions)
- **Current Frequency**: Annual (Jan 1 of each year)
- **Current Range**: 2015-2023 (9 data points per country)
- **Example**: `USA: [18238B, 18745B, 19543B, ...]`
- **Issue**: Only 9 timestamps, doesn't overlap with daily data

### 3. **Earthquakes (USGS)** - COUNT DATA
- **Raw Type**: Number of earthquakes per day
- **Current Frequency**: Daily
- **Current Range**: Last 30 days
- **Example**: `[12, 15, 8, 23, 19, ...]`
- **Issue**: Daily granularity, short history

### 4. **Environmental Events (NASA EONET)** - COUNT DATA
- **Raw Type**: Current active events by category
- **Current Frequency**: Snapshot (single point in time)
- **Current Range**: NOW only
- **Example**: `{Wildfires: 14, Storms: 8, Volcanoes: 3}`
- **Issue**: No time series at all!

### 5. **arXiv Papers** - COUNT DATA
- **Raw Type**: Number of papers matching topic
- **Current Frequency**: Snapshot/search result
- **Current Range**: Total count (not time-based)
- **Example**: `{AI: 45000, ML: 38000, QC: 12000}`
- **Issue**: Not stored as time series currently

### 6. **Clinical Trials** - COUNT DATA
- **Raw Type**: Number of active trials for condition
- **Current Frequency**: Snapshot
- **Current Range**: NOW only
- **Example**: `{Cancer: 5234, Diabetes: 1289, COVID: 423}`
- **Issue**: Not stored as time series

---

## Data Type Categories

### Category A: CONTINUOUS NUMERIC (Prices, Values)
- **Sources**: Stocks, GDP
- **Characteristic**: Represents absolute value at point in time
- **Correlation Type**: Value-to-value (price correlation)
- **Normalization**: Sample at consistent intervals

### Category B: DISCRETE COUNTS (Events, Papers, Trials)
- **Sources**: Earthquakes, Environmental, arXiv, Clinical Trials
- **Characteristic**: Integer counts of events/items
- **Correlation Type**: Count-to-count (activity correlation)
- **Normalization**: Aggregate/sum over consistent intervals

### Category C: RATES (Derived Metrics)
- **Sources**: Can be derived from any
- **Characteristic**: Change over time (growth rate, velocity)
- **Correlation Type**: Rate-to-rate (momentum correlation)
- **Normalization**: Calculate delta between periods

---

## Proposed Normalization Strategy

### TARGET: Monthly Frequency (First Day of Month)

All data sources normalized to timestamps: `2015-01-01, 2015-02-01, 2015-03-01, ...`

This provides:
- ✅ Sufficient granularity for meaningful trends
- ✅ Reduces noise from daily volatility
- ✅ Feasible for all data sources
- ✅ Creates overlapping timestamps across ALL sources

---

## Normalization Rules by Source

### 1. Stocks → Monthly End-of-Month Prices
```python
# INPUT: Daily prices for 30 days
[145.23, 147.89, 143.12, ..., 152.45]  # Nov 1-30

# OUTPUT: Single monthly value
2025-11-01: 152.45  # Last trading day of month
```

**Rationale**: End-of-month captures the final valuation for the period

**Extended History**: Fetch 5+ years of monthly data (60+ points per stock)

### 2. GDP → Forward-Fill Annual to Monthly
```python
# INPUT: Annual GDP values
2015-01-01: 18238B
2016-01-01: 18745B

# OUTPUT: Monthly values (forward-fill)
2015-01-01: 18238B
2015-02-01: 18238B
2015-03-01: 18238B
...
2015-12-01: 18238B
2016-01-01: 18745B  # New value
2016-02-01: 18745B
```

**Rationale**: GDP is reported annually; forward-fill spreads value across year

**Alternative**: Linear interpolation (but GDP doesn't change linearly)

### 3. Earthquakes → Monthly Sum
```python
# INPUT: Daily earthquake counts for November
Nov 1: 12, Nov 2: 15, Nov 3: 8, ..., Nov 30: 19

# OUTPUT: Single monthly value
2025-11-01: 456  # Sum of all November earthquakes
```

**Rationale**: Total seismic activity per month is meaningful metric

**Extended History**: Fetch USGS historical data (available back to 1900s)

### 4. Environmental Events → Monthly Sum
```python
# CURRENT: Snapshot of active events
{Wildfires: 14, Storms: 8}

# PROPOSED: Track events daily, aggregate monthly
# Nov 1: {Wildfires: 10, Storms: 5}
# Nov 2: {Wildfires: 12, Storms: 6}
# ...
# Nov 30: {Wildfires: 14, Storms: 8}

# OUTPUT: Monthly totals
2025-11-01: {Wildfires: 367, Storms: 198}
```

**Rationale**: Environmental activity over time period

**Alternative**: Use daily snapshot counts if historical aggregation not available

### 5. arXiv Papers → Monthly Publication Counts
```python
# CURRENT: Total papers matching topic (all time)
AI: 45000

# PROPOSED: Papers published per month
# Use arXiv API date filter: submittedDate:[202511* TO 202511*]

# OUTPUT: Monthly publication counts
2025-11-01: 1245  # AI papers published in November
2025-10-01: 1189  # AI papers published in October
```

**Rationale**: Research output velocity over time

**Implementation**: Query arXiv with date ranges for each month

### 6. Clinical Trials → Monthly Active Trial Counts
```python
# CURRENT: Currently active trials
Cancer: 5234

# PROPOSED: Snapshot count at beginning of each month

# OUTPUT: Monthly counts
2025-11-01: 5234  # Active trials on Nov 1
2025-10-01: 5189  # Active trials on Oct 1
```

**Rationale**: Clinical research activity level over time

**Alternative**: Count trials STARTED per month (may be more volatile)

---

## Implementation Impact

### Before Normalization
```
Stocks:       2025-11-01, 2025-11-02, 2025-11-03, ..., 2025-11-30 (30 points)
GDP:          2015-01-01, 2016-01-01, ..., 2023-01-01 (9 points)
Earthquakes:  2025-11-01, 2025-11-02, ..., 2025-11-30 (30 points)

OVERLAP: ZERO matching timestamps
CORRELATIONS: ZERO cross-domain correlations
```

### After Normalization
```
Stocks:       2020-01-01, 2020-02-01, ..., 2025-11-01 (71 points)
GDP:          2020-01-01, 2020-02-01, ..., 2025-11-01 (71 points)
Earthquakes:  2020-01-01, 2020-02-01, ..., 2025-11-01 (71 points)
Environmental:2020-01-01, 2020-02-01, ..., 2025-11-01 (71 points)
arXiv:        2020-01-01, 2020-02-01, ..., 2025-11-01 (71 points)
Trials:       2020-01-01, 2020-02-01, ..., 2025-11-01 (71 points)

OVERLAP: 71 matching monthly timestamps across ALL sources
CORRELATIONS: 61 variables × 61 variables = 3,721 potential pairs
CROSS-DOMAIN: ~50-60% of pairs (1,800+ cross-domain correlations)
```

---

## Data Quality Considerations

### Spurious Correlations
**Risk**: With normalized data, may find correlations that are meaningless
- Example: "NVDA stock correlates with wildfire count" (both trending up)

**Mitigation**:
1. **Time-lag analysis**: Check if one leads/lags the other
2. **Detrending**: Remove long-term trends, correlate residuals
3. **Domain expertise**: Flag unlikely relationships for review
4. **Statistical significance**: Require p-value < 0.05
5. **Minimum data points**: Require ≥30 overlapping points

### Data Availability
Some sources may not have historical data:
- **Environmental**: NASA EONET may only have recent events
- **Clinical Trials**: May need to start collecting from now forward

**Solution**: Start collecting NOW, backfill where possible

### Update Frequency
**Target**: Monthly updates (first week of new month)
- Stocks: Fetch end-of-previous-month price
- GDP: Annual update (once per year in April)
- Earthquakes: Aggregate previous month's data
- Environmental: Aggregate previous month's events
- arXiv: Query papers from previous month
- Trials: Snapshot trial count

---

## Correlation Calculation Requirements

### Minimum Requirements for Valid Correlation
1. **Minimum 30 overlapping data points** (statistical significance)
2. **Same timestamp alignment** (both monthly, both first-of-month)
3. **No missing values** (or interpolated with flagging)
4. **Numeric values** (normalized to float)

### Correlation Methods (from Causal_affect)
1. **Pearson**: Linear relationships (prices, values)
2. **Spearman**: Monotonic relationships (ranks, counts)
3. **Kendall Tau**: Robust to outliers (event counts)

**Recommendation**: Use Spearman for mixed data types (robust, handles non-linear)

---

## Database Schema Impact

### Current: TimeSeriesData Table
```sql
CREATE TABLE time_series_data (
    id SERIAL PRIMARY KEY,
    variable_id INTEGER REFERENCES variable_metadata(id),
    timestamp TIMESTAMP NOT NULL,
    value NUMERIC NOT NULL,
    fetched_at TIMESTAMP DEFAULT NOW()
);
```

**Good news**: Schema already supports normalized timestamps! ✅

**Migration**: Just need to change ingestion logic, existing schema works.

---

## Implementation Checklist

### Phase 1: Update Data Fetchers (1-2 days)
- [ ] Modify `data_fetcher.py`:
  - [ ] `fetch_stock_data()`: Return monthly end-of-month prices for 5 years
  - [ ] `fetch_earthquake_count()`: Return monthly sums for 5 years
  - [ ] `fetch_environmental_events()`: Return monthly aggregates
  - [ ] `fetch_gdp_data()`: Keep annual, add forward-fill logic
  - [ ] `fetch_arxiv_papers()`: Add date filtering for monthly counts
  - [ ] `fetch_clinical_trials()`: Add timestamp parameter for historical snapshots

### Phase 2: Update Ingestion Service (1 day)
- [ ] Modify `data_ingestion_service.py`:
  - [ ] Generate monthly timestamps for last 5 years
  - [ ] Call fetchers with monthly aggregation
  - [ ] Store normalized data with first-of-month timestamps
  - [ ] Add logging for normalization process

### Phase 3: Data Migration (automated)
- [ ] Clear existing TimeSeriesData (misaligned timestamps)
- [ ] Re-ingest all variables with monthly normalization
- [ ] Verify all sources have ≥30 overlapping points

### Phase 4: Recalculate Correlations (automated)
- [ ] Trigger correlation calculation with normalized data
- [ ] Verify cross-domain correlations exist (target: 1,000+)
- [ ] Test heatmap displays disparate relationships

### Phase 5: Validation (1 day)
- [ ] Spot-check correlations make sense
- [ ] Verify timestamps align across sources
- [ ] Test frontend heatmap display
- [ ] Monitor for spurious correlations

---

## Expected Outcomes

### Success Metrics
- ✅ **≥1,000 cross-domain correlations** (vs. current 0)
- ✅ **71 overlapping monthly timestamps** across all sources
- ✅ **Heatmap shows disparate relationships** (stocks ↔ earthquakes, GDP ↔ arXiv)
- ✅ **Tiles clickable** with scatter plots showing relationship

### Example Cross-Domain Correlations Expected
1. **Tech Stock Prices ↔ AI Paper Publications**: Positive correlation (research drives valuations)
2. **GDP ↔ Clinical Trial Counts**: Positive correlation (economic health enables research)
3. **Earthquake Activity ↔ Environmental Events**: May correlate with volcanic activity
4. **Stock Market ↔ Wildfire Events**: Negative correlation (disasters impact economy)

---

## Risks & Mitigation

### Risk 1: Historical Data Unavailable
Some APIs may not provide historical monthly data.

**Mitigation**: 
- Start collecting NOW for future correlations
- Use what's available (even 12 months = valid correlation)
- Backfill manually where possible

### Risk 2: Spurious Correlations Dominate
May find many meaningless correlations.

**Mitigation**:
- Implement statistical significance filters (p-value)
- Add time-lag analysis to detect causal direction
- Use domain expertise to flag unlikely pairs
- Implement Granger causality for validation

### Risk 3: Monthly Granularity Too Coarse
May lose important daily patterns.

**Mitigation**:
- Start with monthly, prove concept
- Add weekly normalization option later
- Keep raw daily data for drill-down

---

## Next Steps

**IMMEDIATE**:
1. Get user approval on normalization strategy
2. Estimate API rate limits for historical data fetching
3. Begin Phase 1 implementation (data fetchers)

**THIS WEEK**:
1. Complete all 5 phases
2. Deploy v2.0.7 with normalized data
3. Verify heatmap shows cross-domain correlations

**FUTURE**:
1. Add detrending for spurious correlation detection
2. Implement time-lag analysis
3. Add Granger causality from Causal_affect
4. Expand to 156 variables
