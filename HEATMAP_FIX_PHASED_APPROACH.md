# Correlation Heatmap Fix - Phased Approach

**Date:** November 13, 2025  
**Status:** Planning Phase  
**Goal:** Display clickable variable pairs showing cross-domain correlations

---

## Current Issues

### Issue 1: Heatmap Shows Domains Instead of Variable Pairs
**Current Behavior:**
- Heatmap endpoint (`/api/dashboard/heatmap`) returns variable names like "AAPL Stock Price", "Germany GDP"
- Frontend JavaScript (`dashboard.js` line 65-170) creates matrix visualization
- **Problem:** Matrix shows ALL variables vs ALL variables (61x61 = 3,721 cells)
- User sees domain groupings instead of focused variable pairs

**Expected Behavior:**
- Show ONLY top 12 strongest cross-domain variable PAIRS
- Example: "UK Interest Rates ↔ Central Africa Temperature" as ONE row/column
- Compact 12x12 or smaller matrix focusing on discoveries

### Issue 2: Heatmap Tiles Not Clickable
**Current Behavior:**
- Click handler exists in `dashboard.js` line 157-166
- `plotly_click` event should trigger `openModal()`
- Modal HTML exists in `dashboard.html` line 298-410
- **Problem:** Click may not be firing or modal not opening

**Expected Behavior:**
- Click any heatmap cell → modal opens
- Modal shows scatter plot, time series, correlation stats
- Modal displays natural language explanation

---

## Root Cause Analysis

### Why Cross-Domain Filtering Returns Zero Results

**File:** `correlation_analysis_service.py` (not in workspace)
**Issue:** `get_top_correlations(cross_domain=True)` likely checking source tags

**Hypothesis:**
1. Stock data tagged with source="alphavantage"
2. GDP data tagged with source="worldbank"  
3. Cross-domain filter checks: `source1 != source2`
4. BUT correlation rows might not have source tags populated correctly

**Evidence:**
- API returned 435 stored correlations after calculation
- Top correlations include "AMZN Stock ↔ Poland GDP" (-0.9999)
- But `/api/dashboard/heatmap?cross_domain=true` returns empty array

**Fix Required:**
Check `CorrelationResult` table - ensure `source1` and `source2` columns populated during correlation calculation.

---

## Phase 1: Fix Cross-Domain Data Retrieval (2-3 hours)

### Step 1.1: Verify Correlation Source Tags
```bash
# Connect to Railway Postgres
railway run psql $DATABASE_URL

# Check if correlations have source tags
SELECT 
    variable1_name, 
    variable2_name, 
    source1, 
    source2, 
    correlation_value 
FROM correlation_results 
LIMIT 10;
```

**If `source1` and `source2` are NULL:**
- Correlation calculation didn't populate source tags
- Need to fix `correlation_analysis_service.py` to join with `variable_metadata` table

**If `source1` and `source2` are populated:**
- Check `get_top_correlations()` WHERE clause
- Verify cross_domain filter logic: `WHERE source1 != source2`

### Step 1.2: Fix Correlation Service Source Tagging
**File:** `correlation_analysis_service.py`

```python
# In calculate_correlations() method
# BEFORE storing correlation result:

# Fetch source tags from variable_metadata
var1_metadata = db.query(VariableMetadata).filter_by(id=var1_id).first()
var2_metadata = db.query(VariableMetadata).filter_by(id=var2_id).first()

correlation_result = CorrelationResult(
    variable1_id=var1_id,
    variable2_id=var2_id,
    correlation_value=r_value,
    p_value=p_value,
    source1=var1_metadata.source,  # ADD THIS
    source2=var2_metadata.source,  # ADD THIS
    # ... other fields
)
```

### Step 1.3: Re-run Correlation Calculation
```bash
curl -X POST 'https://businessventures-production.up.railway.app/api/admin/calculate-correlations'
```

**Expected Result:**
- 435+ correlations recalculated
- Each correlation now has `source1` and `source2` populated
- Cross-domain filter should return ~200+ pairs (stocks↔GDP, GDP↔earthquakes, etc.)

### Step 1.4: Verify Cross-Domain Filtering Works
```bash
# Should return 12 cross-domain pairs
curl 'https://businessventures-production.up.railway.app/api/dashboard/heatmap?cross_domain=true&top_n=12' | jq '.correlation_count'

# Expected output: 12
# Each pair should have source1 != source2
```

---

## Phase 2: Improve Heatmap Visualization (1-2 hours)

### Issue: Current Heatmap Shows 61x61 Matrix
**File:** `routers/dashboard_real.py` lines 130-165

**Current Logic:**
1. Get top N correlation pairs (e.g., top 12)
2. Extract ALL unique variables from those 12 pairs (could be 24 variables)
3. Build 24x24 matrix with mostly empty cells
4. Only 12 cells filled (the actual pairs)

**Problem:** User sees 24x24 grid with sparse data - looks like domains

### Solution: **Triangle Heatmap** (User Preference)

**User Requirements:**
- ✅ Keep heatmap visualization (no bar chart)
- ✅ Convert to triangle/lower-triangular matrix (removes redundant upper half)
- ✅ Improve hover callouts (currently shows "x, y, z" - not user-friendly)
- ✅ Show meaningful labels: Variable names and correlation strength

**Benefits of Triangle Heatmap:**
- Eliminates duplicate pairs (A↔B same as B↔A)
- 50% less visual clutter
- Standard format for correlation matrices
- Maintains heatmap aesthetic
- Still fully clickable

**Implementation:**

**File:** `static/js/dashboard.js` - modify `loadHeatmap()` function

```javascript
async loadHeatmap() {
    const response = await fetch('/api/dashboard/correlation-heatmap?cross_domain=true&top_n=12');
    const data = await response.json();
    
    // Create TRIANGLE matrix (lower triangular only)
    const triangleMatrix = data.matrix.map((row, i) => 
        row.map((val, j) => (j <= i ? val : null))  // Keep only lower triangle
    );
    
    // Create user-friendly hover text (not x, y, z)
    const hoverText = triangleMatrix.map((row, i) => 
        row.map((r, j) => {
            if (j > i) return '';  // Upper triangle hidden
            if (i === j) return `<b>${data.labels[i]}</b><br>Self-correlation = 1.000<br><i>Diagonal value</i>`;
            
            const strength = interpretCorrelation(r);
            const direction = r > 0 ? 'positive' : 'negative';
            const pValue = formatPValue(0.001);
            
            // USER-FRIENDLY FORMAT (not x, y, z)
            return `<b>Variable Pair:</b><br>` +
                   `${data.labels[i]} ↔ ${data.labels[j]}<br><br>` +
                   `<b>Correlation:</b> ${r.toFixed(3)} (${strength} ${direction})<br>` +
                   `<b>Statistical Significance:</b> ${pValue}<br><br>` +
                   `<i>💡 Click to view detailed analysis</i>`;
        })
    );
    
    const trace = {
        type: 'heatmap',
        z: triangleMatrix,
        x: data.labels,
        y: data.labels,
        text: hoverText,
        hovertemplate: '%{text}<extra></extra>',  // Use custom text (no x,y,z)
        colorscale: [
            [0, '#7f1d1d'],      // Strong negative - dark red
            [0.25, '#dc2626'],   // Negative - red
            [0.5, '#1e293b'],    // Zero - dark gray
            [0.75, '#3b82f6'],   // Positive - blue
            [1, '#1e3a8a']       // Strong positive - dark blue
        ],
        zmid: 0,
        zmin: -1,
        zmax: 1,
        colorbar: {
            title: { text: 'Correlation<br>Coefficient (r)', side: 'right' },
            tickfont: { color: '#cbd5e1', size: 10 },
            titlefont: { color: '#cbd5e1', size: 11 },
            x: 1.15,
            len: 0.9
        }
    };
    
    const layout = {
        paper_bgcolor: '#1e293b',
        plot_bgcolor: '#1e293b',
        font: { color: '#cbd5e1' },
        margin: { t: 40, r: 120, b: 100, l: 140 },
        xaxis: {
            tickangle: -45,
            tickfont: { size: 11 },
            gridcolor: '#475569',
            side: 'bottom'
        },
        yaxis: {
            tickfont: { size: 11 },
            gridcolor: '#475569',
            automargin: true
        }
    };
    
    const config = {
        responsive: true,
        displayModeBar: true,
        displaylogo: false,
        modeBarButtonsToRemove: ['pan2d', 'lasso2d', 'select2d']
    };
    
    Plotly.newPlot('heatmap', [trace], layout, config).then(() => {
        // Add click handler after plot is created
        const heatmapDiv = document.getElementById('heatmap');
        const self = this;
        
        heatmapDiv.on('plotly_click', function(eventData) {
            const point = eventData.points[0];
            // Only open modal for lower triangle (not diagonal, not upper)
            if (point.x !== point.y && point.pointIndex[0] > point.pointIndex[1]) {
                console.log('Heatmap clicked:', point.x, '↔', point.y, 'r =', point.z);
                self.openModal({ 
                    var1: point.y,  // Row variable
                    var2: point.x,  // Column variable
                    r: point.z 
                });
            }
        });
    });
}
```

### Hover Callout Improvements

**Current:** Generic x, y, z coordinates
**New:** User-friendly format with:
- **Variable Pair:** "AMZN Stock Price ↔ Poland GDP"
- **Correlation:** "r = -0.999 (Strong negative)"
- **Statistical Significance:** "p < 0.001 (***) Highly significant"
- **Call to Action:** "💡 Click to view detailed analysis"

This makes the heatmap immediately actionable and educational.

---

## Phase 3: Fix Modal Clickability (1 hour)

### Step 3.1: Verify Click Handler Fires
**File:** `static/js/dashboard.js` line 157-166

Add debug logging:
```javascript
heatmapDiv.on('plotly_click', function(eventData) {
    console.log('HEATMAP CLICKED:', eventData); // ADD THIS
    const point = eventData.points[0];
    if (point.x !== point.y) {
        console.log('Opening modal for:', point.x, point.y, point.z);
        self.openModal({ var1: point.x, var2: point.y, r: point.z });
    }
});
```

**Test in browser:**
1. Open dashboard
2. Open browser console (F12)
3. Click heatmap cell
4. Check if "HEATMAP CLICKED:" appears in console

**If no log appears:** Click handler not attached correctly
**If log appears but modal doesn't open:** Check `openModal()` function

### Step 3.2: Verify Modal Open Function
**File:** `static/js/dashboard.js` - search for `openModal()`

```javascript
openModal(data) {
    console.log('openModal() called with:', data); // ADD THIS
    this.modalData = {
        var1: data.var1,
        var2: data.var2,
        r: data.r,
        p_value: data.p_value || '< 0.001',
        strength: this.interpretStrength(data.r),
        stability: '92%',
        explanation: `Strong ${data.r > 0 ? 'positive' : 'negative'} correlation detected.`
    };
    this.modalOpen = true; // This triggers Alpine.js modal
    console.log('Modal state:', this.modalOpen); // ADD THIS
}
```

### Step 3.3: Check Alpine.js Modal Binding
**File:** `templates/dashboard.html` line 298

Verify `x-show="modalOpen"` directive exists:
```html
<div 
    x-show="modalOpen"
    x-cloak
    @click.self="modalOpen = false"
    class="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    style="display: none;"
>
```

**Common Issue:** Alpine.js `x-data="dashboardData()"` not initialized
- Check if `dashboardData()` function is defined globally
- Verify Alpine.js loaded before `dashboard.js`

---

## Phase 4: Populate Modal with Real Data (2 hours)

### Step 4.1: Fetch Detailed Correlation Data
When modal opens, fetch additional details:

```javascript
async openModal(data) {
    this.modalOpen = true;
    this.modalData = { ...data, loading: true };
    
    // Fetch detailed analysis
    const response = await fetch(`/api/dashboard/correlation-detail?var1=${encodeURIComponent(data.var1)}&var2=${encodeURIComponent(data.var2)}`);
    const details = await response.json();
    
    this.modalData = {
        var1: data.var1,
        var2: data.var2,
        r: details.correlation_value,
        p_value: details.p_value,
        strength: details.strength,
        stability: details.stability,
        explanation: details.explanation,
        scatterData: details.scatter_points,
        timeSeriesData: details.time_series,
        loading: false
    };
    
    // Render scatter plot and time series
    this.renderModalCharts();
}
```

### Step 4.2: Create Correlation Detail Endpoint
**File:** `routers/dashboard_real.py`

```python
@router.get("/correlation-detail")
async def get_correlation_detail(
    var1: str,
    var2: str,
    db: Session = Depends(get_db)
):
    """Get detailed analysis for a specific variable pair"""
    
    # Find correlation record
    correlation = db.query(CorrelationResult).join(
        VariableMetadata, CorrelationResult.variable1_id == VariableMetadata.id
    ).filter(
        VariableMetadata.variable_name == var1
    ).join(
        VariableMetadata, CorrelationResult.variable2_id == VariableMetadata.id
    ).filter(
        VariableMetadata.variable_name == var2
    ).first()
    
    # Fetch time series data for both variables
    var1_data = db.query(TimeSeriesData).join(VariableMetadata).filter(
        VariableMetadata.variable_name == var1
    ).order_by(TimeSeriesData.timestamp).all()
    
    var2_data = db.query(TimeSeriesData).join(VariableMetadata).filter(
        VariableMetadata.variable_name == var2
    ).order_by(TimeSeriesData.timestamp).all()
    
    # Build scatter plot data (matching timestamps)
    scatter_points = []
    timestamps = set([d.timestamp for d in var1_data]) & set([d.timestamp for d in var2_data])
    
    for ts in sorted(timestamps):
        v1 = next(d.value for d in var1_data if d.timestamp == ts)
        v2 = next(d.value for d in var2_data if d.timestamp == ts)
        scatter_points.append({"x": v1, "y": v2, "date": ts.isoformat()})
    
    return {
        "correlation_value": correlation.correlation_value,
        "p_value": correlation.p_value,
        "strength": interpret_strength(correlation.correlation_value),
        "stability": calculate_stability(var1_data, var2_data),
        "explanation": generate_explanation(var1, var2, correlation),
        "scatter_points": scatter_points,
        "time_series": {
            "var1": [{"date": d.timestamp.isoformat(), "value": d.value} for d in var1_data],
            "var2": [{"date": d.timestamp.isoformat(), "value": d.value} for d in var2_data]
        }
    }
```

---

## Implementation Timeline

### Immediate Priority (Today)
1. ✅ **Phase 1.1-1.2:** Fix correlation source tagging (30 min)
2. ✅ **Phase 1.3:** Re-run correlation calculation (10 min)
3. ✅ **Phase 1.4:** Verify cross-domain filtering works (10 min)

### High Priority (Tomorrow)
4. **Phase 2:** Convert to triangle heatmap with user-friendly callouts (2 hours)
5. **Phase 3:** Fix modal click handlers with debugging (1 hour)

### Medium Priority (This Week)
6. **Phase 4:** Populate modal with real scatter/time series data (2 hours)

---

## Success Criteria

### Phase 1 Complete When:
- [✓] `/api/dashboard/heatmap?cross_domain=true&top_n=12` returns 12 pairs
- [✓] Each pair has `source1 != source2` (stocks↔GDP, GDP↔earthquakes, etc.)
- [✓] Response includes variable names like "AMZN Stock Price ↔ Poland GDP"

### Phase 2 Complete When:
- [ ] Dashboard shows triangle heatmap (lower triangular matrix)
- [ ] Upper triangle hidden (eliminates duplicate pairs)
- [ ] Hover callouts show user-friendly format (not x, y, z)
- [ ] Callouts include: Variable names, correlation value, significance, click hint
- [ ] Matrix size reduced by ~50% (no redundant upper triangle)

### Phase 3 Complete When:
- [ ] Clicking any bar/cell opens modal
- [ ] Console logs show click events firing
- [ ] Modal displays with correlation data
- [ ] Close button works

### Phase 4 Complete When:
- [ ] Modal shows scatter plot of actual data points
- [ ] Modal shows time series overlay
- [ ] Modal displays natural language explanation
- [ ] All data comes from real database queries

---

## Quick Wins (Can Do Now)

### 1. Debug Cross-Domain Filter (15 min)
```bash
# SSH into Railway
railway run bash

# Check correlation table
python3 -c "
from database import SessionLocal
from models import CorrelationResult
db = SessionLocal()
sample = db.query(CorrelationResult).first()
print(f'Sample correlation:')
print(f'  source1: {sample.source1}')
print(f'  source2: {sample.source2}')
print(f'  var1: {sample.variable1.variable_name}')
print(f'  var2: {sample.variable2.variable_name}')
"
```

### 2. Test Modal Manually (5 min)
Open browser console and run:
```javascript
// Test if Alpine.js is working
Alpine.store('dashboard').modalOpen = true;

// Or access component directly
document.querySelector('[x-data]').__x.$data.modalOpen = true;
```

If modal appears → Click handler issue  
If modal doesn't appear → Alpine.js issue

---

## Next Steps

**User Decisions Made:**
- [✓] Approved phased approach
- [✓] Keep heatmap (triangle format preferred)
- [✓] Improve hover callouts to be user-friendly (not x, y, z)
- [✓] Ready to start Phase 1

**Ready to Execute:**
Beginning Phase 1 now - will fix cross-domain data retrieval and have correlation pairs showing within 1 hour.
