# CA-006 Build Strategy: Layer-by-Layer Implementation
# ======================================================

## Overview

Build FEATURE-CA-006-01 (Analytics Integration) layer-by-layer, with each layer:
1. Generating production code artifacts
2. Running layer-level tests with REAL dependencies
3. Producing artifacts for next layer
4. Final feature-level integration testing
5. Viewing results in web dashboard

## Critical Principle: NO MOCK DATA IN PRODUCTION CODE

**NEVER embed mock data generators in production code.**

- Mock data ONLY exists in test fixtures
- Production code ONLY handles real data
- Web dashboard displays REAL analytics data from test accounts
- Separation: `src/` (production) vs `tests/fixtures/` (mock data)

## Build Sequence for FEATURE-CA-006-01

### Layer 1: Google Analytics Client (LAYER-CA-006-01-01)

**Build Command:**
```bash
python build_layer.py \
  --layer-path "Causal_affect/SYSTEM-CA-006_feedback_iteration/FEATURE-CA-006-01_analytics_integration/LAYER-CA-006-01-01_google_analytics_client" \
  --output-dir "src/feedback_iteration/backend"
```

**Artifacts Generated:**
- `src/feedback_iteration/backend/app/services/google_analytics_client.py`
- `tests/feedback_iteration/backend/test_google_analytics_client.py`
- `tests/fixtures/google_analytics_responses.json` (mock responses for tests ONLY)

**Testing Approach:**
- Unit tests: Use mock responses from `tests/fixtures/`
- Integration tests: Use REAL Google Analytics test account
- View results: Dashboard shows "GA4 Connection: ✅ Connected"

**Verification:**
```bash
# Run tests with real GA4 test account
pytest tests/feedback_iteration/backend/test_google_analytics_client.py --real-api

# Expected output:
# ✅ test_authenticate_with_service_account PASSED
# ✅ test_fetch_pageviews_from_real_account PASSED
# ✅ test_data_transformation PASSED
```

**Web Dashboard View:**
- Navigate to `http://localhost:5173/admin/analytics-status`
- See: "Google Analytics: ✅ Connected - Last sync: 2 min ago"
- See: Real pageview data from test account

---

### Layer 2: Mixpanel Client (LAYER-CA-006-01-02)

**Build Command:**
```bash
python build_layer.py \
  --layer-path "Causal_affect/SYSTEM-CA-006_feedback_iteration/FEATURE-CA-006-01_analytics_integration/LAYER-CA-006-01-02_mixpanel_client" \
  --output-dir "src/feedback_iteration/backend" \
  --depends-on "LAYER-CA-006-01-01"
```

**Artifacts Generated:**
- `src/feedback_iteration/backend/app/services/mixpanel_client.py`
- `tests/feedback_iteration/backend/test_mixpanel_client.py`
- `tests/fixtures/mixpanel_responses.json` (mock for tests ONLY)

**Testing Approach:**
- Unit tests: Mock responses in `tests/fixtures/`
- Integration tests: REAL Mixpanel free account
- No mock data in production code

**Verification:**
```bash
pytest tests/feedback_iteration/backend/test_mixpanel_client.py --real-api
```

**Web Dashboard View:**
- See: "Mixpanel: ✅ Connected - 1,247 events today"
- Real event data from test account

---

### Layer 3: Amplitude Client (LAYER-CA-006-01-03)

**Build Command:**
```bash
python build_layer.py \
  --layer-path "Causal_affect/SYSTEM-CA-006_feedback_iteration/FEATURE-CA-006-01_analytics_integration/LAYER-CA-006-01-03_amplitude_client" \
  --output-dir "src/feedback_iteration/backend" \
  --depends-on "LAYER-CA-006-01-01,LAYER-CA-006-01-02"
```

**Artifacts Generated:**
- `src/feedback_iteration/backend/app/services/amplitude_client.py`
- `tests/feedback_iteration/backend/test_amplitude_client.py`
- `tests/fixtures/amplitude_responses.json`

**Testing Approach:**
- Real Amplitude test account for integration tests
- Mock fixtures ONLY in `tests/fixtures/`

**Web Dashboard View:**
- See: "Amplitude: ✅ Connected - 342 users tracked"

---

### Layer 4: Analytics Aggregator (LAYER-CA-006-01-04)

**Build Command:**
```bash
python build_layer.py \
  --layer-path "Causal_affect/SYSTEM-CA-006_feedback_iteration/FEATURE-CA-006-01_analytics_integration/LAYER-CA-006-01-04_analytics_aggregator" \
  --output-dir "src/feedback_iteration/backend" \
  --depends-on "LAYER-CA-006-01-01,LAYER-CA-006-01-02,LAYER-CA-006-01-03"
```

**Artifacts Generated:**
- `src/feedback_iteration/backend/app/services/analytics_aggregator.py`
- `src/feedback_iteration/backend/app/models/unified_metrics.py`
- `tests/feedback_iteration/backend/test_analytics_aggregator.py`

**Critical: This layer orchestrates ALL providers**
- Takes input from Layers 1, 2, 3
- Produces unified metrics
- NO mock data generators - uses REAL provider clients

**Testing Approach:**
```python
# tests/feedback_iteration/backend/test_analytics_aggregator.py

# Unit test: Mock the provider CLIENTS (not data)
def test_aggregator_merges_provider_data():
    # Mock the CLIENT CALLS (using fixtures)
    mock_ga_client = Mock(spec=GoogleAnalyticsClient)
    mock_ga_client.fetch_metrics.return_value = load_fixture('ga_response.json')
    
    aggregator = AnalyticsAggregator(ga_client=mock_ga_client, ...)
    result = await aggregator.collect_metrics(mvp_id="test-mvp")
    
    assert result.pageviews > 0  # Verify real-looking data structure

# Integration test: Use REAL providers
@pytest.mark.integration
def test_aggregator_with_real_providers():
    # Use REAL clients with test accounts
    aggregator = AnalyticsAggregator(
        ga_client=GoogleAnalyticsClient(test_credentials),
        mixpanel_client=MixpanelClient(test_token),
        amplitude_client=AmplitudeClient(test_key)
    )
    
    result = await aggregator.collect_metrics(mvp_id="real-test-mvp")
    
    # Verify ACTUAL data from providers
    assert result.pageviews > 0
    assert result.provider_attribution['google_analytics'] is not None
```

**Web Dashboard View:**
- See: "Analytics Aggregation: ✅ Active"
- See: Combined metrics from all 3 providers
- See: "Last aggregation: 30 seconds ago"

---

### Layer 5: Analytics Error Handler (LAYER-CA-006-01-05)

**Build Command:**
```bash
python build_layer.py \
  --layer-path "Causal_affect/SYSTEM-CA-006_feedback_iteration/FEATURE-CA-006-01_analytics_integration/LAYER-CA-006-01-05_analytics_error_handler" \
  --output-dir "src/feedback_iteration/backend" \
  --depends-on "LAYER-CA-006-01-04"
```

**Artifacts Generated:**
- `src/feedback_iteration/backend/app/services/analytics_error_handler.py`
- `tests/feedback_iteration/backend/test_analytics_error_handler.py`

**Testing Approach:**
- Simulate REAL error scenarios (rate limits, timeouts)
- Test circuit breaker with actual failed requests
- NO synthetic error generators in production code

**Web Dashboard View:**
- See: "Error Handler: ✅ Active - 0 circuit breakers open"
- See: "Last 24h: 3 retries, 0 fallbacks triggered"

---

## FEATURE-Level Integration Testing

After all 5 layers built, run feature-level integration test:

```bash
python test_feature.py \
  --feature-path "Causal_affect/SYSTEM-CA-006_feedback_iteration/FEATURE-CA-006-01_analytics_integration" \
  --mode integration \
  --use-real-providers
```

**What This Tests:**
1. All 5 layers work together
2. End-to-end flow: API call → GA/Mixpanel/Amplitude → Aggregation → Error handling
3. Uses REAL test accounts for all providers
4. Verifies acceptance criteria from FEATURE-CA-006-01.yaml

**Expected Output:**
```
=== FEATURE-CA-006-01 Integration Test ===

✅ AC-FEAT-006-01-01: Google Analytics authentication SUCCESS
✅ AC-FEAT-006-01-02: Mixpanel authentication SUCCESS
✅ AC-FEAT-006-01-03: Amplitude authentication SUCCESS
✅ AC-FEAT-006-01-04: Collected metrics from all providers in 4.2 seconds (< 5 min) SUCCESS
✅ AC-FEAT-006-01-05: Metrics normalized to common schema SUCCESS
✅ AC-FEAT-006-01-06: Rate limit handling with retry logic SUCCESS
✅ AC-FEAT-006-01-07: Provider fallback on failure SUCCESS

FEATURE-CA-006-01: ✅ PASSED (7/7 acceptance criteria met)

Artifacts:
- Unified metrics stored in: /tmp/feature_test_results/metrics.json
- Test report: /tmp/feature_test_results/report.html
```

---

## Web Dashboard Final View

Navigate to `http://localhost:5173` and verify:

### Analytics Status Page
```
┌─────────────────────────────────────────────────┐
│ Analytics Integration Status                    │
├─────────────────────────────────────────────────┤
│ Google Analytics  : ✅ Connected                │
│ Mixpanel         : ✅ Connected                │
│ Amplitude        : ✅ Connected                │
│ Aggregator       : ✅ Active                   │
│ Error Handler    : ✅ Active (0 failures)      │
├─────────────────────────────────────────────────┤
│ Last Sync: 45 seconds ago                       │
│ Next Sync: in 4m 15s                            │
└─────────────────────────────────────────────────┘
```

### Real Metrics Display
```
┌─────────────────────────────────────────────────┐
│ Test MVP: "TaskFlow Pro"                        │
├─────────────────────────────────────────────────┤
│ Pageviews (24h)    : 3,247  (from GA4)         │
│ Unique Visitors    : 1,856  (from Mixpanel)    │
│ Sessions           : 2,103  (from Amplitude)    │
│ Avg Session (min)  : 4.2    (aggregated)       │
│ Bounce Rate        : 32%    (from GA4)         │
├─────────────────────────────────────────────────┤
│ Data Sources: ✅ GA4 ✅ Mixpanel ✅ Amplitude   │
│ Last Updated: Just now                          │
└─────────────────────────────────────────────────┘
```

---

## Mock Data Strategy (TEST FIXTURES ONLY)

**Location:** `tests/fixtures/` (NEVER in `src/`)

**Purpose:** Fast unit tests without hitting real APIs every time

**Structure:**
```
tests/fixtures/
├── google_analytics/
│   ├── pageviews_response.json
│   ├── users_response.json
│   └── error_responses.json
├── mixpanel/
│   ├── events_response.json
│   └── profiles_response.json
├── amplitude/
│   ├── behavioral_data.json
│   └── cohorts_response.json
└── unified/
    └── expected_merged_output.json
```

**Usage in Tests:**
```python
# tests/feedback_iteration/backend/test_google_analytics_client.py
import json
from pathlib import Path

def load_fixture(filename):
    """Load test fixture from tests/fixtures/"""
    fixture_path = Path(__file__).parent.parent / "fixtures" / "google_analytics" / filename
    with open(fixture_path) as f:
        return json.load(f)

def test_transform_pageviews_data():
    # Use fixture for FAST unit test
    raw_response = load_fixture('pageviews_response.json')
    
    client = GoogleAnalyticsClient()
    result = client._transform_response(raw_response)
    
    assert result['pageviews'] == 3247
    assert result['timestamp'] is not None
```

**Production Code:**
```python
# src/feedback_iteration/backend/app/services/google_analytics_client.py

class GoogleAnalyticsClient:
    """NO mock data generators here - only real API calls"""
    
    async def fetch_metrics(self, property_id: str, date_range: tuple) -> Dict:
        """Fetch REAL metrics from Google Analytics"""
        
        # Authenticate with REAL service account
        credentials = service_account.Credentials.from_service_account_file(
            self.service_account_path
        )
        
        # Make REAL API call
        client = BetaAnalyticsDataClient(credentials=credentials)
        request = RunReportRequest(property=f"properties/{property_id}", ...)
        
        response = await client.run_report(request)  # REAL data
        
        return self._transform_response(response)  # Transform REAL data
```

---

## Layer Build Order Summary

1. **Build Layer 1 (GA Client)** → Test with real GA4 → View in dashboard
2. **Build Layer 2 (Mixpanel)** → Test with real Mixpanel → View in dashboard
3. **Build Layer 3 (Amplitude)** → Test with real Amplitude → View in dashboard
4. **Build Layer 4 (Aggregator)** → Test with real providers → View combined data
5. **Build Layer 5 (Error Handler)** → Test error scenarios → View error handling
6. **Feature Integration Test** → Verify all acceptance criteria → View complete feature
7. **Web Dashboard Review** → See everything working with REAL data

---

## Anti-Pattern Examples (AVOID THESE)

### ❌ WRONG: Mock Data in Production Code
```python
# src/feedback_iteration/backend/app/services/analytics_aggregator.py
class AnalyticsAggregator:
    def collect_metrics(self, mvp_id: str) -> Dict:
        if settings.ENVIRONMENT == "development":
            # ❌ BAD: Mock data generator in production code
            return self._generate_mock_metrics()
        else:
            return self._collect_real_metrics()
    
    def _generate_mock_metrics(self):
        """❌ BAD: This pollutes production codebase"""
        return {
            'pageviews': random.randint(1000, 5000),
            'users': random.randint(500, 2000),
            # This code serves NO production purpose
        }
```

### ✅ CORRECT: Real Code in Production, Mocks in Tests
```python
# src/feedback_iteration/backend/app/services/analytics_aggregator.py
class AnalyticsAggregator:
    """Production code ONLY handles real data"""
    
    async def collect_metrics(self, mvp_id: str) -> UnifiedMetrics:
        """Collect REAL metrics from all providers"""
        
        # Parallel collection from REAL providers
        ga_task = self.ga_client.fetch_metrics(mvp_id, date_range)
        mixpanel_task = self.mixpanel_client.fetch_events(mvp_id, date_range)
        amplitude_task = self.amplitude_client.fetch_analytics(mvp_id, date_range)
        
        results = await asyncio.gather(ga_task, mixpanel_task, amplitude_task)
        
        # Merge REAL data
        return self._merge_provider_data(results)

# tests/fixtures/analytics_fixtures.py
"""Mock data ONLY in test fixtures"""

def mock_google_analytics_response():
    """Test fixture for GA responses"""
    return {
        'pageviews': 3247,
        'users': 1856,
        'timestamp': '2025-10-14T10:00:00Z'
    }

# tests/test_analytics_aggregator.py
def test_aggregator_merges_data():
    """Fast unit test using fixtures"""
    mock_ga = Mock()
    mock_ga.fetch_metrics.return_value = mock_google_analytics_response()
    
    aggregator = AnalyticsAggregator(ga_client=mock_ga, ...)
    result = await aggregator.collect_metrics('test-mvp')
    
    assert result.pageviews == 3247
```

---

## Success Criteria

After building all 5 layers:

✅ **Code Quality**
- NO mock data generators in `src/` directory
- All mock data isolated in `tests/fixtures/`
- Production code ONLY uses real API clients

✅ **Testing**
- Unit tests run fast with fixtures
- Integration tests use REAL test accounts
- All acceptance criteria verified with real data

✅ **Web Dashboard**
- Shows REAL metrics from test accounts
- All provider connections show "✅ Connected"
- Data updates in real-time (<1 min refresh)

✅ **Artifacts**
- Each layer produces working Python modules
- Tests pass with real providers
- Documentation generated automatically

✅ **Traceability**
- Each test maps to acceptance criteria
- Feature test verifies all layer integration
- Requirements satisfied with evidence

---

## Next Steps

1. **Run Layer 1 Build**: Start with Google Analytics Client
2. **Verify Tests Pass**: Using real GA4 test account
3. **View in Dashboard**: See GA connection status
4. **Repeat for Layers 2-5**: Same process
5. **Feature Integration Test**: Verify complete feature
6. **Dashboard Review**: See all features working together

**Ready to start building LAYER-CA-006-01-01 (Google Analytics Client)?**
