# Causality Analysis - Gap Assessment

**Date:** November 5, 2025  
**Question:** Do we have enough logic and data to identify causation?

---

## 📋 Executive Summary

**Short Answer:** We have the **architecture and code structure** in place, but we're **missing key dependencies and data requirements** for proper causality analysis.

**Current State:** 🟡 Partially Ready (50%)  
**Recommendation:** Add causality analysis as **Phase 2** feature after core dashboard is working

---

## ✅ What We HAVE

### 1. **Complete Architecture & Code Structure**

Located in: `/Causal_affect/SYSTEM-CA-002_correlation_analysis/FEATURE-CA-002-02_causality_testing/`

**5 Causality Testing Layers Built:**

```
✅ LAYER-CA-002-02-01: Granger Causality Test
   - Implementation exists
   - Tests whether X predicts Y (time-lagged)
   - Statistical significance testing

✅ LAYER-CA-002-02-02: VAR Model (Vector Autoregression)
   - Multi-variable time series modeling
   - Captures dynamic relationships
   - Lag order selection via AIC/BIC

✅ LAYER-CA-002-02-03: IRF Calculator (Impulse Response Functions)
   - Shows how shocks propagate through system
   - Quantifies effect size over time
   - Confidence intervals

✅ LAYER-CA-002-02-04: Transfer Entropy
   - Information-theoretic causality measure
   - Detects nonlinear causal relationships
   - Direction and strength of information flow

✅ LAYER-CA-002-02-05: DAG Inference (Directed Acyclic Graphs)
   - Causal network structure discovery
   - PC algorithm implementation
   - Visual causal diagrams
```

### 2. **Feature Orchestrator**

**File:** `feature_integration.py` (613 lines)

**Capabilities:**
- Coordinates all 5 causality layers
- Unified API for running multiple tests
- Comprehensive result aggregation
- Error handling and validation

### 3. **Basic Correlation Analysis** ✅ WORKING NOW

**Current deployment has:**
- Pearson, Spearman, Kendall correlation
- P-value significance testing
- Natural language explanations
- Real-time API endpoints

---

## ❌ What We're MISSING

### 1. **Critical Python Dependencies**

**Not in current `requirements.txt`:**

```python
# TIME SERIES & CAUSALITY ANALYSIS
statsmodels>=0.14.0          # ✅ Already have
pandas>=2.1.3                # ✅ Already have
numpy>=1.26.2                # ✅ Already have

# MISSING - NEEDED FOR CAUSALITY:
pyinform>=0.2.0              # ❌ Transfer entropy
causalnex>=0.11.0            # ❌ DAG inference, Bayesian networks
networkx>=3.0                # ❌ Graph analysis
pgmpy>=0.1.23                # ❌ Probabilistic graphical models
scikit-learn>=1.3.0          # ❌ Already removed (was causing issues)
```

**Impact:** Cannot run Transfer Entropy or DAG Inference without these

### 2. **Time Series Data Requirements**

**For proper causality analysis, we need:**

| Requirement | Current Status | Actual API Capability | Fix Needed |
|-------------|----------------|----------------------|------------|
| **Temporal Resolution** | Mixed (hourly, daily, monthly) | APIs support consistent intervals | ⚠️ Standardize fetching |
| **Historical Depth** | ~30-90 days (current fetch) | **10-50 YEARS available!** | ✅ **Just change API params!** |
| **Frequency Alignment** | Not synchronized | Can request same frequency | ⚠️ Fetch matching intervals |
| **Missing Data Handling** | Basic | Good coverage in APIs | ⚠️ Add interpolation |
| **Stationarity Testing** | Not implemented | N/A - preprocessing step | ❌ Need to build |

**MAJOR DISCOVERY:** The limitation is OUR CODE, not the APIs! We can get years of historical data by simply:

1. **Alpha Vantage**: Change `outputsize='compact'` → `outputsize='full'`
   - Instantly get 20+ years of daily stock data
   
2. **World Bank**: Change `date="2015:2023"` → `date="1990:2023"`  
   - Get 30+ years of GDP, emissions, etc.
   
3. **FRED**: Not implemented yet, but has decades of data
   - Add FRED fetcher → 800,000 time series available
   
4. **USGS**: Use historical API endpoint
   - Archive goes back 100+ years

**Current Data Sources & ACTUAL Historical Depth:**
```
✅ Alpha Vantage (Stocks)     
   - Daily data: 20+ YEARS available (full history)
   - Current fetch: Only last 100 days (compact mode)
   - FIX NEEDED: Change to "full" outputsize → Get ALL history
   
✅ FRED (Economic Data) 
   - 800,000+ time series
   - Most series: 10-50 YEARS of history
   - Monthly/Quarterly/Annual frequencies
   - BEST SOURCE for causality analysis
   
✅ World Bank (GDP, Environment)
   - Annual/Quarterly data
   - Current fetch: 2015-2023 (9 years)
   - Available: Often 50+ years of history
   - FIX NEEDED: Expand date range parameter
   
⚠️  USGS (Earthquakes)        
   - Event-based BUT can aggregate daily
   - Current fetch: Last 30 days only
   - Available: 100+ years in archives
   - FIX NEEDED: Use archive API for historical data
   
⚠️  NASA EONET (Events)       
   - Event-based, current fetch: Active events only
   - Not ideal for time series causality
   
✅ US Census (Demographics)   
   - Annual/Monthly depending on indicator
   - Decades of historical data available
   - Current implementation: Not fetching yet
```

**KEY INSIGHT:** We're currently fetching MINIMAL data, but the APIs support EXTENSIVE history!

**Problem:** Granger causality requires:
- Regular time intervals (daily/weekly/monthly)
- Sufficient history (min 100 observations, ideally 200+)
- Same frequency across all variables

### 3. **Statistical Preprocessing Pipeline**

**Missing components:**

```python
❌ Time Series Alignment
   - Interpolate to common frequency
   - Handle missing values
   - Synchronize timestamps

❌ Stationarity Transformation
   - ADF test (Augmented Dickey-Fuller)
   - Differencing for non-stationary data
   - Log transforms for exponential trends

❌ Lag Selection Optimization
   - Cross-correlation analysis
   - Information criteria (AIC/BIC)
   - Domain knowledge integration

❌ Confounding Variable Control
   - Identify potential confounders
   - Control variable selection
   - Sensitivity analysis
```

### 4. **Computational Resources**

**Causality analysis is computationally expensive:**

| Test | Time Complexity | Data Points Needed | Current Capacity |
|------|----------------|-------------------|------------------|
| Granger | O(n²) per pair | 100-200+ | ✅ OK |
| VAR Model | O(n³) | 200+ | ⚠️ May timeout |
| Transfer Entropy | O(n log n) × bins² | 500+ | ❌ Too slow |
| DAG Inference | O(2^n) worst case | 1000+ | ❌ Not feasible |

**Railway Free Tier Limits:**
- CPU: Shared
- Memory: 512MB-1GB
- Timeout: 30 seconds per request

**Problem:** Full causality analysis could take 30-60 seconds per relationship

### 5. **Domain Knowledge Base**

**For proper causal interpretation, we need:**

```
❌ Known causal mechanisms database
   - Economic theory (GDP → Stocks is well-known)
   - Environmental science (CO2 → Temperature)
   - Medical knowledge (if analyzing health data)

❌ Confounder registry
   - Common confounding variables by domain
   - Temporal confounders (seasonality, trends)
   - Spatial confounders (geographic effects)

❌ Validation framework
   - Expert review system
   - Literature citations
   - Reproducibility checks
```

---

## 🎯 What's FEASIBLE Now vs Later

### ✅ **Phase 1: Can Implement NOW** (with current setup)

**1. Basic Granger Causality Test**
- ✅ Dependencies available (statsmodels)
- ✅ Code already written
- ✅ Works with current data structure
- ⚠️ Limited to well-behaved time series

**Implementation:**
```python
# Add to requirements.txt (already there)
statsmodels==0.14.0

# Add to main.py
from statsmodels.tsa.stattools import grangercausalitytests

@app.post("/api/v1/causality/granger")
async def test_granger_causality(request: GrangerRequest):
    """Test if X Granger-causes Y"""
    result = grangercausalitytests(
        data[[request.y_var, request.x_var]], 
        maxlag=request.max_lag
    )
    return interpret_granger_results(result)
```

**Limitations:**
- Only works for time series data
- Requires stationarity (need to check)
- Minimum 100 data points
- Cannot detect nonlinear causality

**Effort:** 2-3 days

---

### ⚠️ **Phase 2: Feasible with Additional Dependencies** (1-2 weeks)

**2. VAR Models & IRF**
```python
# Add to requirements.txt
statsmodels==0.14.0  # Already have
```

**3. Transfer Entropy** (Nonlinear causality)
```python
# Add to requirements.txt
pyinform==0.2.0      # New dependency
```

**4. Network Graph Visualization**
```python
# Add to requirements.txt
networkx==3.2.0      # New dependency
```

**What we'd get:**
- Direction and strength of causal flow
- Shock propagation analysis
- Nonlinear relationship detection
- Visual causal networks

**Effort:** 1-2 weeks with testing

---

### ❌ **Phase 3: NOT Feasible Yet** (requires major data/infrastructure upgrade)

**5. Full DAG Inference**

**Why not:**
```
❌ Requires 1000+ data points (we have 30-90)
❌ Needs causalnex/pgmpy (complex setup)
❌ Computationally intensive (would timeout)
❌ Requires domain expertise validation
❌ Need proper confounder database
```

**What we'd need:**
- Historical data: 2+ years at daily resolution
- Infrastructure: Dedicated compute (not Railway free tier)
- Domain experts: To validate results
- Confounding variable database: Domain-specific knowledge

**Effort:** 1-2 months + infrastructure costs

---

## 📊 Recommended Approach

### **Option A: Start Simple (Recommended)** 🟢

**Week 1-2: Add Basic Granger Causality**

```markdown
1. Add Granger test to existing correlation analysis
2. Show results in Relationship Context Panel
3. Simple interpretation: "X predicts Y" or "No causal evidence"
4. Only run on time series data (filter out event data)
```

**UI Addition:**
```
┌──────────────────────────────────────┐
│ 🧮 CAUSALITY ANALYSIS (Basic)        │
├──────────────────────────────────────┤
│ Granger Causality Test:              │
│   GDP → Stocks: ✅ Yes (p=0.003)     │
│   Stocks → GDP: ❌ No (p=0.234)      │
│                                      │
│ 💡 GDP changes predict future stock │
│    movements with 3-day lag          │
└──────────────────────────────────────┘
```

**Dependencies to add:**
- None! statsmodels already in requirements.txt

**Pros:**
- ✅ Zero new dependencies
- ✅ Works with current data
- ✅ Quick to implement
- ✅ Scientifically sound

**Cons:**
- ⚠️ Limited to linear relationships
- ⚠️ Only works for time series
- ⚠️ Doesn't detect confounders

---

### **Option B: Enhanced Causality (Phase 2)** 🟡

**Week 3-4: Add Transfer Entropy + Network Graphs**

```markdown
1. Add pyinform for nonlinear causality
2. Add networkx for graph visualization
3. Show information flow between variables
4. Visual causal network in dashboard
```

**New dependencies:**
```python
pyinform==0.2.0
networkx==3.2.0
```

**Pros:**
- ✅ Detects nonlinear causality
- ✅ Visual network graphs
- ✅ Information-theoretic rigor

**Cons:**
- ⚠️ More complex to interpret
- ⚠️ Higher computational cost
- ⚠️ Still needs good time series data

---

### **Option C: Full Solution (Long-term)** 🔴

**Months 2-3: Complete Causality Suite**

```markdown
1. Historical data pipeline (2+ years)
2. Full DAG inference with causalnex
3. Confounder detection system
4. Expert validation workflow
5. Dedicated compute infrastructure
```

**This is a significant project:**
- Data acquisition costs
- Infrastructure costs ($50-200/month)
- Development time (2-3 months)
- Domain expert time

---

## 🎯 REVISED RECOMMENDATION (With Historical Data Available!)

### **GAME CHANGER: We CAN do proper causality analysis NOW!** 

Since the APIs support 10-50 years of historical data, we just need to:

1. **Update Data Fetchers** (1 day of work)
   - Change Alpha Vantage to fetch full history (20+ years daily data)
   - Expand World Bank date ranges (30+ years)
   - Add FRED integration (decades of economic data)
   - Aggregate USGS to daily counts with historical lookback

2. **Add Basic Data Alignment** (1 day of work)
   - Resample all to common frequency (daily or monthly)
   - Handle missing values with forward-fill
   - Store in consistent DataFrame format

3. **Implement Granger Causality** (2 days of work)
   - Already have statsmodels
   - Add stationarity testing (ADF test)
   - Implement lag selection
   - Generate natural language results

**Total Effort: 4-5 days** instead of months!

---

## 💡 NEW Immediate Next Steps

**Week 1: Enable Historical Data Fetching**

1. Update `data_fetcher.py`:
   ```python
   # Change from 30 days to full history
   def fetch_stock_data(self, symbol: str, years: int = 20):
       params = {
           "outputsize": "full"  # ← Changed from "compact"
       }
   
   def fetch_gdp_data(self, country_code: str = "USA", start_year: int = 1990):
       params = {
           "date": f"{start_year}:2023"  # ← Expanded range
       }
   
   # NEW: Add FRED integration
   def fetch_fred_series(self, series_id: str):
       # Get decades of economic data
   ```

2. Add data alignment utilities:
   ```python
   def align_time_series(data_dict, frequency='D'):
       """Align all series to common daily/monthly frequency"""
       # Resample, interpolate, align timestamps
   ```

**Week 2: Implement Granger Causality** ✅ **COMPLETED - Jan 2026**

3. **✅ IMPLEMENTED:** Frequency-aware downsampling for Granger causality
   - Detects frequency of each time series (daily, weekly, monthly, quarterly, yearly)
   - Downsamples to lowest common frequency using real observations
   - Adaptive max_lag based on frequency (4 for quarterly, 12 for monthly, etc.)
   - **Statistical validity:** Uses real downsampled data, NOT interpolated synthetic points
   - **Key improvement:** Interpolation valid for correlation visualization, but INVALID for Granger inference
   
   Implementation details:
   ```python
   # services/granger_causality_service.py
   def _detect_frequency(series) -> int:
       # Returns median days between observations
   
   def _get_resample_rule(freq_days) -> str:
       # Maps to pandas resample rule (D, W, M, Q, Y)
   
   def _get_adaptive_max_lag(freq_days) -> int:
       # Quarterly: 4 lags (~1 year)
       # Monthly: 12 lags (~1 year)
       # Daily: 252 lags (~1 year trading days)
   ```
   
   **Rationale:**
   - Interpolation creates synthetic points that violate Granger test assumptions
   - Downsampling preserves statistical validity with real observations only
   - Power increases as data universe grows (20 quarters → 40 quarters over 5 years)
   - Clear error messaging when insufficient data for robust inference

4. Add causality endpoint to `main.py`:
   ```python
   @app.post("/api/v1/causality/test")
   async def test_causality(request: CausalityRequest):
       # Fetch historical data (now 1000+ points!)
       # Run Granger test with frequency-aware downsampling
       # Return directional causality with confidence
   ```

5. Update dashboard UI to show results

---

## ✅ REVISED Summary Table

| Feature | Dependencies | Data Available | Effort | NEW Recommendation |
|---------|-------------|----------------|---------|-------------------|
| **Granger Test** | ✅ statsmodels | ✅ **20+ years!** | 4-5 days | ✅ **DO IT NOW!** |
| **VAR/IRF** | ✅ statsmodels | ✅ **20+ years!** | +2-3 days | ✅ **Add in Week 2!** |
| **Transfer Entropy** | ❌ pyinform | ✅ Plenty of data | +3-4 days | ⚠️ Phase 2 (need dependency) |
| **Network Graphs** | ❌ networkx | ✅ Plenty of data | +2-3 days | ⚠️ Phase 2 |
| **DAG Inference** | ❌ causalnex | ✅ Plenty of data | +1 week | ⚠️ Phase 3 (complex) |

**KEY CHANGE:** Data is NOT the blocker! We can implement robust causality analysis immediately.

---

## 💡 Immediate Next Steps

**If you want causality analysis in the dashboard:**

1. **Review the simple Granger approach** - Is this valuable enough?
2. **Accept the limitations** - Linear only, time series only
3. **I'll implement it** - 2-3 days of work
4. **Update UI design** - Add Granger section to Relationship Panel

**OR**

1. **Skip causality for now** - Focus on correlation dashboard
2. **Collect more historical data** - Over next 3-6 months
3. **Add causality in v2.0** - With proper data foundation

---

## ❓ Questions for You

1. **Is basic Granger causality (linear, time series only) valuable enough to include now?**

2. **Should we show "inconclusive" when data is insufficient, rather than no causality section?**

3. **Are you okay with "Preliminary" and "Linear only" warnings in the UI?**

4. **Do you want to wait and do causality properly with more data in 3-6 months?**

---

## 📚 Summary Table

| Feature | Current Status | Dependencies Needed | Data Needed | Effort | Recommendation |
|---------|---------------|-------------------|-------------|---------|----------------|
| **Granger Test** | Code exists | ✅ None (have statsmodels) | Time series, 100+ points | 2-3 days | ✅ **Do Now** |
| **VAR/IRF** | Code exists | ✅ None (have statsmodels) | Time series, 200+ points | 1 week | ⚠️ Phase 2 |
| **Transfer Entropy** | Code exists | ❌ pyinform | Time series, 500+ points | 1-2 weeks | ⚠️ Phase 2 |
| **Network Graphs** | Code exists | ❌ networkx | Multiple relationships | 3-5 days | ⚠️ Phase 2 |
| **DAG Inference** | Code exists | ❌ causalnex, pgmpy | 1000+ points, 2+ years | 1-2 months | ❌ Long-term |

---

**What would you like to do?**
