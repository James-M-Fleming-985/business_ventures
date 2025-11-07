# Integration Checklist: Wire Up Existing Implementations

**Date:** 2025-01-07  
**Goal:** Integrate pre-built Lagged Correlation and Granger Causality into production dashboard

---

## ✅ Phase 1: Lagged Correlation Integration (2 days)

### Task 1.1: Copy Implementation Files
- [ ] Copy `Causal_affect/.../LAYER-CA-002-01-05_lagged_correlation/src/implementation.py` → `lag_correlation_service.py`
- [ ] Add imports to requirements.txt (numpy, pandas, scipy if not present)
- [ ] Test import: `from lag_correlation_service import LaggedCorrelationAnalyzer`

### Task 1.2: Create Service Wrapper
- [ ] Create `LagCorrelationService` class in `lag_correlation_service.py`
- [ ] Implement `calculate_optimal_lag(var1_id, var2_id)` method
- [ ] Add `_get_variable_data()` helper to fetch from TimeSeriesData table
- [ ] Add error handling for insufficient data, missing variables

### Task 1.3: Database Schema Update
- [ ] Create migration file: `alembic revision --autogenerate -m "Add optimal_lag column"`
- [ ] Add column: `ALTER TABLE correlation_results ADD COLUMN optimal_lag INTEGER;`
- [ ] Add column: `ALTER TABLE correlation_results ADD COLUMN lag_correlation FLOAT;`
- [ ] Run migration: `alembic upgrade head`
- [ ] Verify in psql: `\d correlation_results`

### Task 1.4: API Endpoint
- [ ] Add route in `routers/dashboard_real.py`:
  ```python
  @router.get("/lag-analysis/{var1_id}/{var2_id}")
  async def get_lag_analysis(var1_id: int, var2_id: int, db: Session = Depends(get_db))
  ```
- [ ] Return format:
  ```json
  {
    "optimal_lag": 30,
    "correlation": 0.72,
    "p_value": 0.001,
    "n_observations": 85,
    "all_lags": {0: 0.3, 15: 0.7, 30: 0.72, 45: 0.6, ...}
  }
  ```
- [ ] Test endpoint: `curl /api/dashboard/lag-analysis/1/2`

### Task 1.5: UI Integration
- [ ] Update `templates/dashboard.html` relationship modal
- [ ] Add section: "Lag Analysis"
- [ ] Display: "Optimal lag: 30 days (r=0.72, p<0.001)"
- [ ] Add lag curve chart (Plotly line chart)
- [ ] Test clicking heatmap tile → modal shows lag analysis

### Task 1.6: Batch Calculation
- [ ] Add to `correlation_analysis_service.py`:
  ```python
  def calculate_all_lags(self, min_correlation=0.3):
      # Calculate optimal lag for all significant correlations
      # Store in database
  ```
- [ ] Add admin endpoint: `/api/admin/calculate-lags`
- [ ] Test batch processing

**Deliverable:** Lag analysis working for all variable pairs, displayed in dashboard

---

## ✅ Phase 2: Granger Causality Integration (2 days)

### Task 2.1: Copy Implementation Files
- [ ] Copy `Causal_affect/.../LAYER-CA-002-02-01_granger_test/src/implementation.py` → `granger_causality_service.py`
- [ ] Add statsmodels to requirements.txt: `statsmodels>=0.14.0`
- [ ] Install: `pip install statsmodels`
- [ ] Test import: `from granger_causality_service import GrangerCausalityTest`

### Task 2.2: Create Service Wrapper
- [ ] Create `GrangerCausalityService` class
- [ ] Implement `test_causality(var1_id, var2_id)` method
- [ ] Implement `test_bidirectional()` to get both X→Y and Y→X
- [ ] Add logic to determine direction:
  ```python
  if x_to_y.reject_null and not y_to_x.reject_null:
      return 'X_to_Y'  # X predicts Y
  elif y_to_x.reject_null and not x_to_y.reject_null:
      return 'Y_to_X'  # Y predicts X
  elif both:
      return 'bidirectional'
  else:
      return 'none'
  ```

### Task 2.3: Database Schema Update
- [ ] Migration: `alembic revision -m "Add Granger causality columns"`
- [ ] Add columns:
  ```sql
  ALTER TABLE correlation_results 
  ADD COLUMN causal_direction VARCHAR(20),
  ADD COLUMN granger_p_value_xy FLOAT,
  ADD COLUMN granger_p_value_yx FLOAT,
  ADD COLUMN granger_f_stat_xy FLOAT,
  ADD COLUMN granger_f_stat_yx FLOAT;
  ```
- [ ] Run migration
- [ ] Verify columns exist

### Task 2.4: API Endpoint
- [ ] Add route in `routers/dashboard_real.py`:
  ```python
  @router.get("/causality/{var1_id}/{var2_id}")
  async def get_causality(var1_id: int, var2_id: int)
  ```
- [ ] Return format:
  ```json
  {
    "direction": "X_to_Y",
    "x_causes_y": {"p_value": 0.001, "f_stat": 12.5, "reject_null": true},
    "y_causes_x": {"p_value": 0.8, "f_stat": 0.3, "reject_null": false},
    "interpretation": "arXiv papers predict NVDA stock"
  }
  ```
- [ ] Test: `curl /api/dashboard/causality/1/2`

### Task 2.5: UI Integration
- [ ] Update relationship modal in `dashboard.html`
- [ ] Add "Causal Direction" section
- [ ] Display with arrow: "arXiv → NVDA (p<0.001)" or "GDP ← Stock (not significant)"
- [ ] Color code: Green for significant, gray for not significant
- [ ] Add tooltip explaining Granger causality

### Task 2.6: Batch Calculation
- [ ] Add to admin endpoint:
  ```python
  @router.post("/api/admin/calculate-causality")
  async def calculate_all_causality():
      # Test Granger for all cross-domain pairs
      # Store in database
  ```
- [ ] Process only significant correlations (p<0.05)
- [ ] Test batch processing

**Deliverable:** Causal direction shown for all pairs in dashboard

---

## ✅ Phase 3: Update Heatmap & Relationship Display (1 day)

### Task 3.1: Update /api/dashboard/relationship Endpoint
- [ ] Include lag analysis in response
- [ ] Include Granger causality in response
- [ ] Return format:
  ```json
  {
    "correlation": 0.72,
    "p_value": 0.001,
    "scatter": {...},
    "lag_analysis": {
      "optimal_lag": 30,
      "correlation_at_lag": 0.72
    },
    "causality": {
      "direction": "X_to_Y",
      "p_value": 0.001
    }
  }
  ```

### Task 3.2: Enhanced Modal Display
- [ ] Update `openModal()` in dashboard.js to fetch all data
- [ ] Display sections:
  1. Correlation Stats (existing)
  2. Scatter Plot (existing)
  3. **NEW:** Lag Analysis (optimal lag, curve chart)
  4. **NEW:** Causal Direction (arrow, p-value)
- [ ] Test modal with all sections visible

### Task 3.3: Leaderboard Update
- [ ] Update `/api/dashboard/leaderboard` to include optimal_lag and causal_direction
- [ ] Display in leaderboard table:
  ```
  | Var1 | Var2 | r | p-value | Direction | Lag |
  |------|------|---|---------|-----------|-----|
  | arXiv| NVDA |0.72| 0.001  | arXiv→NVDA| 30d |
  ```

**Deliverable:** Full exploitation data visible in dashboard

---

## ✅ Phase 4: Testing & Validation (1 day)

### Task 4.1: Unit Tests
- [ ] Test `LagCorrelationService.calculate_optimal_lag()` with mock data
- [ ] Test `GrangerCausalityService.test_causality()` with mock data
- [ ] Test edge cases: insufficient data, all NaN, single value
- [ ] Run: `pytest tests/test_lag_correlation.py`
- [ ] Run: `pytest tests/test_granger_causality.py`

### Task 4.2: Integration Tests
- [ ] Test full flow: Calculate correlation → Calculate lag → Test causality
- [ ] Test with real database data (use top 10 pairs)
- [ ] Verify database updates correctly
- [ ] Check for race conditions in concurrent execution

### Task 4.3: End-to-End Tests
- [ ] Open dashboard in browser
- [ ] Click heatmap tile (e.g., GDP-Stock pair)
- [ ] Verify modal shows:
  - [x] Correlation stats
  - [x] Scatter plot
  - [ ] Lag analysis (new)
  - [ ] Causal direction (new)
- [ ] Click "Forecast" → verify drift forecast still works
- [ ] Click different pairs → verify data updates correctly

### Task 4.4: Performance Tests
- [ ] Batch calculate lags for all 1,195 pairs
- [ ] Measure time: Should complete in <10 minutes
- [ ] Batch calculate Granger for cross-domain pairs only (~200 pairs)
- [ ] Measure time: Should complete in <15 minutes
- [ ] Optimize if needed (use concurrent execution)

**Deliverable:** All tests passing, performance acceptable

---

## ✅ Phase 5: Deployment (1 day)

### Task 5.1: Database Migration
- [ ] Run migrations on Railway Postgres:
  ```bash
  railway run alembic upgrade head
  ```
- [ ] Verify columns added:
  ```sql
  SELECT column_name FROM information_schema.columns 
  WHERE table_name = 'correlation_results' 
  AND column_name IN ('optimal_lag', 'causal_direction', 'granger_p_value_xy');
  ```

### Task 5.2: Batch Calculation
- [ ] Trigger lag calculation for all pairs:
  ```bash
  curl -X POST https://businessventures-production.up.railway.app/api/admin/calculate-lags
  ```
- [ ] Trigger Granger causality for cross-domain pairs:
  ```bash
  curl -X POST https://businessventures-production.up.railway.app/api/admin/calculate-causality
  ```
- [ ] Monitor logs for errors
- [ ] Wait for completion (~20 minutes)

### Task 5.3: Deploy Updated Code
- [ ] Commit changes:
  ```bash
  git add -A
  git commit -m "v2.1.0: Add lag optimization and Granger causality"
  git push
  ```
- [ ] Increment BUILD_VERSION to 2.1.0
- [ ] Verify Railway auto-deploy triggers
- [ ] Monitor deployment logs
- [ ] Wait for healthy status

### Task 5.4: Smoke Tests
- [ ] Health check: `curl /health` → version 2.1.0
- [ ] Test lag endpoint: `curl /api/dashboard/lag-analysis/1/2`
- [ ] Test causality endpoint: `curl /api/dashboard/causality/1/2`
- [ ] Open dashboard → click heatmap tile → verify new sections appear
- [ ] Check for console errors in browser DevTools

**Deliverable:** v2.1.0 deployed with lag optimization and Granger causality live

---

## 📊 Verification Checklist

After deployment, verify:

- [ ] Dashboard loads without errors
- [ ] Heatmap still shows cross-domain pairs (fix from before)
- [ ] Clicking heatmap tile opens modal with 4 sections:
  1. [ ] Correlation stats (r, p-value, sample size)
  2. [ ] Scatter plot (x/y coordinates)
  3. [ ] **Lag analysis** (optimal lag, correlation curve)
  4. [ ] **Causal direction** (arrow, p-values)
- [ ] Leaderboard shows optimal_lag and causal_direction columns
- [ ] Time series drift chart still works
- [ ] Network graph still works
- [ ] No regression in existing features

---

## 🎯 Success Criteria

**After Phase 1 (Lag):**
- [ ] Can query: "What is the optimal lag for arXiv-NVDA pair?"
- [ ] Dashboard displays: "Optimal lag: 30 days, r=0.72"
- [ ] All 1,195 pairs have optimal_lag calculated and stored

**After Phase 2 (Granger):**
- [ ] Can query: "Does GDP predict Stock or vice versa?"
- [ ] Dashboard displays: "GDP → Stock (p<0.001)" with arrow
- [ ] All cross-domain pairs have causal_direction determined

**After Phase 3 (UI):**
- [ ] Modal shows complete exploitation data
- [ ] Leaderboard sortable by lag, direction, correlation
- [ ] Users can identify exploitable relationships at a glance

**After Phase 5 (Deployment):**
- [ ] Production system has full exploitation analysis
- [ ] Ready for next step: Regression coefficients (β₁)
- [ ] Can start building trading strategies

---

## 🚀 Next Steps After This

Once lag optimization and Granger causality are integrated:

1. **Build regression service** (β₀, β₁, R²) using statsmodels OLS
2. **Add backtesting framework** (walk-forward validation)
3. **Create exploitation dashboard** showing E[Return] = P(correct) × β₁ × ΔX
4. **Start paper trading** to validate strategies
5. **Implement real-time monitoring** when ready for production

---

## 📝 Notes

- **Existing implementations are production-ready** - no need to rewrite
- **Focus on integration work** - wire up what you already have
- **Database migrations are straightforward** - just add columns
- **UI changes are minimal** - add sections to existing modal
- **Total effort: ~5-7 days** for complete integration

**You're 70% done!** The hard work (statistical implementations) is complete. Just need plumbing! 🚀
