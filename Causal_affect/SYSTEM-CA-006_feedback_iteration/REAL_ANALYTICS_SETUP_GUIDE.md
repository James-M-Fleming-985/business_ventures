# Real Analytics Providers Setup Guide
# =====================================
# CA-006 Feedback Dashboard - Production-Ready Analytics Integration

## Overview

This guide walks through setting up **real** analytics providers (all free tiers) for CA-006.
**NO MOCKS** - we'll use actual APIs with real data from day one.

All three providers offer generous free tiers that are perfect for testing and early MVPs:
- **Google Analytics 4**: Completely free, unlimited properties
- **Mixpanel**: Free up to 100,000 events/month
- **Amplitude**: Free up to 10 million events/month

**Total Setup Time**: ~30 minutes
**Cost**: $0/month for development and early production

---

## Provider 1: Google Analytics 4 (GA4)

### Why GA4?
- ✅ Completely free forever
- ✅ Most widely used analytics platform
- ✅ Excellent for pageview and session tracking
- ✅ Built-in real-time dashboard
- ✅ Server-side API available

### Setup Steps (10 minutes)

#### 1. Create GA4 Property
```bash
# Go to: https://analytics.google.com/
# Click: Admin (bottom left)
# Click: Create Property
# Property name: "Causal Affect - CA-006 Test MVP"
# Timezone: Your timezone
# Currency: USD
# Click: Next
# Industry: Technology
# Business size: Small
# Click: Create
```

#### 2. Create Data Stream (Optional for Data API)
```bash
# OPTION A: Use placeholder URL (recommended)
# After property creation:
# Click: "Add stream"
# Choose: Web
# Website URL: https://example.com (GA4 requires valid format, we'll update to Railway URL later)
# Stream name: "CA-006 Development"
# Click: Create stream

# Save these values:
MEASUREMENT_ID="G-DMQ68JCNX5"  # Shows at top of stream details

# OPTION B: Skip data stream for now
# The Data API works at the PROPERTY level, not stream level
# You can add a data stream later when you have a real Railway URL
# Just use the Property ID from step 7 below
```

#### 3. Enable Data API Access
```bash
# In GA4 Admin:
# Click: Property Settings → Service Accounts
# Click: "Enable Data API"
# Click: "Create service account" → Opens Google Cloud Console
```

#### 4. Create Service Account (Google Cloud)
```bash
# In Google Cloud Console:
# Project: Select or create project "causal-affect-analytics"
# Go to: IAM & Admin → Service Accounts
# Click: "+ CREATE SERVICE ACCOUNT"
# Service account name: "ca-006-analytics-client"
# Service account ID: ca-006-analytics-client@...
# Description: "CA-006 Feedback Dashboard Analytics Access"
# Click: CREATE AND CONTINUE
# Role: Select "Viewer" (for read-only access)
# Click: CONTINUE → DONE
```

#### 5. Generate Service Account Key
```bash
# In Service Accounts list:
# Click: ca-006-analytics-client@...
# Click: Keys tab
# Click: ADD KEY → Create new key
# Key type: JSON
# Click: CREATE
# Save file as: google-analytics-service-account.json

# IMPORTANT: Keep this file secure! Never commit to git.
```

#### 6. Grant Analytics Access
```bash
# First, get your EXACT service account email:
# Method 1: From Google Cloud Console
#   Go to: IAM & Admin → Service Accounts
#   Find: ca-006-analytics-client
#   Copy the full email (looks like: ca-006-analytics-client@PROJECT-ID.iam.gserviceaccount.com)
#
# Method 2: From the JSON key file you downloaded
#   Open: google-analytics-service-account.json
#   Find: "client_email" field
#   Copy the value (e.g., "ca-006-analytics-client@causal-affect-analytics.iam.gserviceaccount.com")

# Back in GA4 Admin:
# Property Access Management → Add users
# Email: [PASTE YOUR EXACT SERVICE ACCOUNT EMAIL FROM ABOVE]
#   Example: ca-006-analytics-client@causal-affect-analytics.iam.gserviceaccount.com
#   (Replace PROJECT-ID with your actual project ID)
# Role: Viewer
# Click: Add

# TROUBLESHOOTING: If you get a red error:
# - Make sure you copied the FULL email including @...iam.gserviceaccount.com
# - Check there are no extra spaces
# - The email should match exactly what's in your JSON key file
```

#### 7. Environment Variables
```bash
# Backend .env
GA4_MEASUREMENT_ID="G-XXXXXXXXXX"
GA4_PROPERTY_ID="properties/123456789"  # From GA4 Admin → Property Settings
GA4_SERVICE_ACCOUNT_PATH="./secrets/google-analytics-service-account.json"
```

#### 8. Install Client Library
```bash
cd /workspaces/business_ventures/Causal_affect/src/feedback_iteration/backend
pip install google-analytics-data>=0.17.0 google-auth>=2.23.0
```

#### 9. Test Connection
```python
# Quick test script
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from google.analytics.data_v1beta.types import RunReportRequest
import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "./secrets/google-analytics-service-account.json"

client = BetaAnalyticsDataClient()
property_id = "properties/123456789"  # Your property ID

request = RunReportRequest(
    property=property_id,
    date_ranges=[{"start_date": "7daysAgo", "end_date": "today"}],
    metrics=[{"name": "activeUsers"}],
)

response = client.run_report(request)
print(f"✅ GA4 Connected! Active users (7d): {response.rows[0].metric_values[0].value if response.rows else 0}")
```

---

## Provider 2: Mixpanel

### Why Mixpanel?
- ✅ Free up to 100K events/month (plenty for testing)
- ✅ Excellent event-based analytics
- ✅ Real-time funnel analysis
- ✅ Cohort and retention tracking
- ✅ Simple REST API

### Setup Steps (10 minutes)

#### 1. Create Account
```bash
# Go to: https://mixpanel.com/register/
# Sign up with email
# Company name: "Causal Affect"
# Use case: "Product Analytics"
# Click: Get Started
```

#### 2. Create Project
```bash
# Project name: "CA-006 Feedback Dashboard"
# Data residency: US or EU (your preference)
# Click: Create Project
```

#### 3. Get API Credentials
```bash
# In Mixpanel:
# Click: Settings (gear icon) → Project Settings
# Copy these values:

PROJECT_TOKEN="abc123..."        # For sending events
API_SECRET="def456..."           # For querying data

# Click: Settings → Personal Settings → API
# Click: Generate Secret → Copy

API_KEY="your_api_key"           # For Data Export API
```

#### 4. Environment Variables
```bash
# Backend .env
MIXPANEL_PROJECT_TOKEN="abc123..."
MIXPANEL_API_SECRET="def456..."
MIXPANEL_API_KEY="your_api_key"
```

#### 5. Install Client Library
```bash
pip install mixpanel>=4.10.0
```

#### 6. Test Connection
```python
# Quick test script
from mixpanel import Mixpanel
import requests
from datetime import datetime, timedelta

# Test event sending
mp = Mixpanel("YOUR_PROJECT_TOKEN")
mp.track("test-user-123", "CA-006 Test Event", {
    "source": "setup_test",
    "timestamp": datetime.now().isoformat()
})
print("✅ Event sent to Mixpanel!")

# Test data retrieval
url = "https://data.mixpanel.com/api/2.0/events"
params = {
    "event": '["CA-006 Test Event"]',
    "unit": "day",
    "interval": 7,
    "type": "general"
}
headers = {
    "Accept": "application/json",
    "Authorization": f"Basic {YOUR_API_SECRET}"  # Base64 encoded
}
response = requests.get(url, params=params, headers=headers)
print(f"✅ Mixpanel Connected! Response: {response.status_code}")
```

---

## Provider 3: Amplitude

### Why Amplitude?
- ✅ Free up to 10M events/month (very generous)
- ✅ Advanced behavioral analytics
- ✅ User journey tracking
- ✅ Predictive analytics
- ✅ Excellent free tier

### Setup Steps (10 minutes)

#### 1. Create Account
```bash
# Go to: https://amplitude.com/get-started
# Sign up with email
# Company: "Causal Affect"
# Role: "Developer"
# Use case: "Product Analytics"
# Click: Get Started (Free Plan)
```

#### 2. Create Project
```bash
# After signup:
# Organization name: "Causal Affect"
# First project: "CA-006 Feedback Dashboard"
# Platform: "Web"
# Click: Create
```

#### 3. Get API Credentials
```bash
# In Amplitude Dashboard:
# Click: Settings → Projects → CA-006 Feedback Dashboard
# Copy these values:

API_KEY="1234567890abcdef..."     # For sending events
SECRET_KEY="fedcba0987654321..."  # For Export API
```

#### 4. Environment Variables
```bash
# Backend .env
AMPLITUDE_API_KEY="1234567890abcdef..."
AMPLITUDE_SECRET_KEY="fedcba0987654321..."
```

#### 5. Install Client Library
```bash
pip install amplitude-analytics>=1.1.0
```

#### 6. Test Connection
```python
# Quick test script
from amplitude import Amplitude

# Initialize client
client = Amplitude("YOUR_API_KEY")

# Send test event
client.track({
    "user_id": "test-user-123",
    "event_type": "CA-006 Test Event",
    "event_properties": {
        "source": "setup_test",
        "test": True
    }
})

print("✅ Event sent to Amplitude!")

# Note: Data retrieval requires Export API (separate endpoint)
# Will be implemented in LAYER-CA-006-01-03
```

---

## Quick Start Summary

### All Environment Variables
```bash
# Create: /workspaces/business_ventures/Causal_affect/src/feedback_iteration/backend/.env

# Google Analytics 4
GA4_MEASUREMENT_ID="G-XXXXXXXXXX"
GA4_PROPERTY_ID="properties/123456789"
GA4_SERVICE_ACCOUNT_PATH="./secrets/google-analytics-service-account.json"

# Mixpanel
MIXPANEL_PROJECT_TOKEN="abc123..."
MIXPANEL_API_SECRET="def456..."
MIXPANEL_API_KEY="your_api_key"

# Amplitude
AMPLITUDE_API_KEY="1234567890abcdef..."
AMPLITUDE_SECRET_KEY="fedcba0987654321..."

# App Config
ENVIRONMENT="development"
LOG_LEVEL="debug"
```

### All Dependencies
```bash
# Add to requirements.txt
google-analytics-data>=0.17.0
google-auth>=2.23.0
mixpanel>=4.10.0
amplitude-analytics>=1.1.0
httpx>=0.25.0
python-dotenv>=1.0.0
```

### Generate Real Test Data

Instead of mocks, we'll send real events to test the pipeline:

```python
# scripts/generate_test_events.py
"""
Send real test events to all analytics providers
Run this to populate dashboards with realistic data
"""

import os
from datetime import datetime, timedelta
import random
from google.analytics.data_v1beta import BetaAnalyticsDataClient
from mixpanel import Mixpanel
from amplitude import Amplitude

def generate_test_events(num_events=100):
    """Generate realistic test events for all providers"""
    
    # Initialize clients
    mp = Mixpanel(os.getenv("MIXPANEL_PROJECT_TOKEN"))
    amp = Amplitude(os.getenv("AMPLITUDE_API_KEY"))
    
    # Generate events over last 7 days
    for i in range(num_events):
        user_id = f"test-user-{random.randint(1, 50)}"
        timestamp = datetime.now() - timedelta(
            days=random.randint(0, 7),
            hours=random.randint(0, 23)
        )
        
        # Random event type
        event_types = ["page_view", "button_click", "form_submit", "purchase"]
        event_type = random.choice(event_types)
        
        # Send to Mixpanel
        mp.track(user_id, event_type, {
            "timestamp": timestamp.isoformat(),
            "page": f"/page-{random.randint(1, 10)}",
            "session_id": f"session-{random.randint(1, 100)}"
        })
        
        # Send to Amplitude
        amp.track({
            "user_id": user_id,
            "event_type": event_type,
            "time": int(timestamp.timestamp() * 1000),
            "event_properties": {
                "page": f"/page-{random.randint(1, 10)}",
                "session_id": f"session-{random.randint(1, 100)}"
            }
        })
    
    print(f"✅ Generated {num_events} test events across all providers!")

if __name__ == "__main__":
    generate_test_events(100)
```

---

## Testing Strategy

### Layer-by-Layer Verification

**LAYER-CA-006-01-01 (Google Analytics Client)**
```bash
# Test with real GA4 data
python -c "
from app.services.google_analytics_client import GoogleAnalyticsClient
client = GoogleAnalyticsClient()
metrics = client.fetch_metrics('properties/123456789', '7daysAgo', 'today')
print(f'✅ Real GA4 metrics: {metrics}')
"
```

**LAYER-CA-006-01-02 (Mixpanel Client)**
```bash
# Test with real Mixpanel data
python -c "
from app.services.mixpanel_client import MixpanelClient
client = MixpanelClient()
events = client.fetch_events('7daysAgo', 'today')
print(f'✅ Real Mixpanel events: {len(events)}')
"
```

**LAYER-CA-006-01-03 (Amplitude Client)**
```bash
# Test with real Amplitude data
python -c "
from app.services.amplitude_client import AmplitudeClient
client = AmplitudeClient()
analytics = client.fetch_analytics('7daysAgo', 'today')
print(f'✅ Real Amplitude analytics: {analytics}')
"
```

**LAYER-CA-006-01-04 (Analytics Aggregator)**
```bash
# Test with all providers
python -c "
from app.services.analytics_aggregator import AnalyticsAggregator
aggregator = AnalyticsAggregator()
unified = aggregator.collect_metrics('mvp-001', ('7daysAgo', 'today'))
print(f'✅ Unified metrics from all providers: {unified}')
"
```

---

## Advantages of Real Providers vs Mocks

### ✅ Real Providers
- **Authentic Testing**: Test actual API behaviors, rate limits, errors
- **Real Latency**: Understand actual performance characteristics
- **Production-Ready**: Code works in production without changes
- **Free Forever**: All three have generous free tiers
- **Better Development**: See real data in dashboards immediately
- **No Mock Pollution**: Zero mock code in production codebase

### ❌ Mocks (Why We're Avoiding)
- Mock data generators creep into production code
- Don't test real API edge cases
- False confidence (tests pass, production fails)
- Mock data never matches real patterns
- Extra maintenance burden
- Delays finding real API issues

---

## Security Best Practices

### Secret Management
```bash
# NEVER commit secrets to git!
# Add to .gitignore:
echo "*.json" >> .gitignore
echo ".env" >> .gitignore
echo "secrets/" >> .gitignore

# Store secrets securely
mkdir -p secrets/
chmod 700 secrets/
mv google-analytics-service-account.json secrets/

# For production (Railway):
# Add secrets via Railway dashboard or CLI:
railway variables set GA4_PROPERTY_ID="properties/123456789"
railway variables set MIXPANEL_PROJECT_TOKEN="abc123..."
railway variables set AMPLITUDE_API_KEY="1234567890abcdef..."
```

### Credential Rotation
```bash
# Rotate credentials every 90 days
# Set calendar reminder to:
# 1. Generate new service account key (GA4)
# 2. Regenerate API secrets (Mixpanel, Amplitude)
# 3. Update Railway environment variables
# 4. Delete old credentials
```

---

## Next Steps

1. ✅ Complete setup for all 3 providers (~30 min)
2. ✅ Test each provider connection independently
3. ✅ Run `generate_test_events.py` to populate data
4. ✅ Verify data appears in provider dashboards
5. ✅ Ready for AI Code Generator to build layers with real APIs

**NO MOCKS NEEDED** - Real providers are ready to use! 🚀
