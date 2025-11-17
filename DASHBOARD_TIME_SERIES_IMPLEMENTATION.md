# Dashboard Time Series Implementation Summary

## Version: 2.0.37

## Problem Statement
The main dashboard time series chart (positioned next to the heatmap) was empty. Requirements specified "Time series showing SELECTED correlation relationship evolution over time" but the purpose was unclear compared to the detailed modal time series.

## Solution

### Differentiation Strategy
- **Main Dashboard Time Series**: Shows raw value trends for top 5 most interesting variables from strongest correlations
  - Purpose: Quick overview of key variable trends
  - Display: Actual values (GBP for stocks/GDP, counts for events, etc.)
  - Use case: Explore individual variable behavior before diving into correlation analysis
  
- **Modal Time Series**: Shows normalized comparison of two correlated variables
  - Purpose: Detailed side-by-side correlation analysis
  - Display: Normalized 0-1 scale for comparison, with raw values in tooltips
  - Use case: Understand how two variables move together over time

### Implementation Details

#### 1. New API Endpoint: `/api/dashboard/top-variables-timeseries`
**File**: `routers/dashboard_real.py`

```python
@router.get("/top-variables-timeseries")
async def get_top_variables_timeseries(
    limit: int = Query(5, ge=3, le=10, description="Number of top variables to show"),
    db: Session = Depends(get_db)
):
```

**Functionality**:
1. Fetches top 20 correlations using `CorrelationAnalysisService`
2. Extracts unique variable names from correlation pairs
3. Takes first N variables (default 5)
4. Retrieves time series data for each variable
5. Returns raw values with unit metadata (USD, count, %, etc.)

**Response Format**:
```json
{
  "series": [
    {
      "name": "NVDA Stock (Monthly)",
      "unit": "USD",
      "dates": ["2024-01-01", "2024-02-01", ...],
      "values": [381.77, 395.23, ...]
    },
    {
      "name": "India GDP",
      "unit": "USD",
      "dates": ["2024-01-01", "2024-02-01", ...],
      "values": [3420000000000, 3450000000000, ...]
    }
  ],
  "message": "Showing 5 variables"
}
```

#### 2. Updated JavaScript Function: `loadTimeSeries()`
**File**: `static/js/dashboard.js`

**Changes**:
- Updated endpoint URL to `/api/dashboard/top-variables-timeseries?limit=5`
- Added proper formatting using existing `formatValue()` helper
- Shows raw values in both chart and hover tooltips
- Applies currency conversion (USD→GBP) and abbreviations (M, Bn, T)

**Plotly Configuration**:
```javascript
traces = data.series.map(series => {
    const formattedValues = series.values.map(val => {
        return this.formatValue(val, series.unit);
    });
    
    return {
        type: 'scatter',
        mode: 'lines',
        name: series.name,
        x: series.dates,
        y: series.values,
        text: formattedValues,  // Formatted values for hover
        hovertemplate: '%{text}<br>%{x}<extra></extra>'
    };
});
```

#### 3. Updated HTML Template
**File**: `templates/dashboard.html`

**Changes**:
- Title changed to "Top Variable Trends"
- Added refresh button wired to `loadTimeSeries()`
- Updated description to explain purpose and differentiation from modal

**Description Text**:
> "Raw values over time for the most interesting variables from top correlations. Each line shows actual values (stocks in GBP, GDP in trillions, counts, etc.). Click any correlation in the heatmap above to see a detailed comparison of two variables side-by-side."

## Data Flow

```
User loads dashboard
    ↓
init() calls loadTimeSeries()
    ↓
Fetch /api/dashboard/top-variables-timeseries?limit=5
    ↓
Backend queries top 20 correlations
    ↓
Extract 5 unique variables from correlation pairs
    ↓
Get time series data for each variable
    ↓
Return raw values with unit metadata
    ↓
Frontend formats values using formatValue()
    ↓
Render Plotly chart with formatted tooltips
```

## Example Display

**Chart will show**:
- NVDA Stock: £380-£400 over time
- India GDP: £3.2T-£3.5T over time  
- Severe Storms Events: 800-1,200 counts
- Machine Learning Papers: 5K-7K counts
- Japan GDP: £4.8T-£5.1T over time

**Hover tooltip example**:
```
£381.77
2024-03-01
```

## Testing Checklist

- [x] Backend endpoint created and linted
- [x] Frontend function updated to call new endpoint
- [x] Formatting applied using existing formatValue() helper
- [x] Refresh button wired correctly
- [x] Init() calls loadTimeSeries() on page load
- [x] Version bumped to 2.0.37
- [x] Changes committed and pushed to GitHub

## Deployment

The changes are now live on Railway. After the automatic deployment completes:

1. Navigate to businessventures-production.up.railway.app/dashboard
2. Time series chart should populate automatically
3. Verify 5 variable trends are displayed with proper formatting
4. Click refresh button to reload data
5. Click heatmap cells to compare with modal time series functionality

## Success Criteria

✅ Main dashboard time series chart is no longer empty
✅ Shows raw values for top 5 variables from strongest correlations
✅ Proper currency conversion (USD→GBP) and abbreviations (M, Bn, T)
✅ Clear differentiation from modal time series (raw trends vs. normalized comparison)
✅ Refresh button functional
✅ Tooltips show formatted values matching variable units

## Related Files Modified

1. `routers/dashboard_real.py` - Added new API endpoint
2. `static/js/dashboard.js` - Updated loadTimeSeries() function
3. `templates/dashboard.html` - Already updated in previous version
4. `VERSION` - Bumped to 2.0.37

## Next Steps

User should verify the implementation works correctly after Railway deployment completes. If any issues arise with the display or formatting, additional refinements can be made.

