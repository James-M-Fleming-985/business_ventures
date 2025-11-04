# Causal Affect Platform - Deployment Guide

## 📋 Pre-Deployment Checklist

### ✅ Completed
- [x] CA-003-01: 5-layer ensemble drift forecasting system built
- [x] CA-002-07: 4-layer natural language explanation system built
- [x] Dependencies consolidated in `requirements.txt`
- [x] Railway configuration files created (`railway.toml`, `Procfile`)
- [x] Environment variables template created (`.env.template`)
- [x] Main FastAPI application created (`main.py`)

### 🔧 TODO Before Deployment
- [ ] Wire actual feature orchestrators into main.py
- [ ] Run integration tests locally
- [ ] Run E2E tests with test data
- [ ] Set production environment variables in Railway
- [ ] Configure PostgreSQL database in Railway
- [ ] Configure Redis cache in Railway
- [ ] Test health check endpoint

---

## 🚀 Railway Deployment Steps

### 1. Initial Setup

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login to Railway
railway login

# Link to project (or create new)
railway link
# OR
railway init
```

### 2. Configure Services

**Add PostgreSQL:**
```bash
railway add --plugin postgresql
```

**Add Redis:**
```bash
railway add --plugin redis
```

### 3. Set Environment Variables

Copy `.env.template` to Railway:

```bash
# Set each variable in Railway dashboard or via CLI
railway variables set SECRET_KEY="your-production-secret-key"
railway variables set JWT_SECRET_KEY="your-jwt-secret"
railway variables set ENCRYPTION_KEY="your-encryption-key"
railway variables set ENVIRONMENT="production"
railway variables set LOG_LEVEL="INFO"

# Railway auto-injects DATABASE_URL and REDIS_URL
```

### 4. Deploy

```bash
# Deploy from current branch
railway up

# OR deploy specific folder
railway up --path .

# Follow deployment logs
railway logs
```

### 5. Verify Deployment

```bash
# Get deployment URL
railway status

# Test health endpoint
curl https://your-app.railway.app/health

# Test API docs
open https://your-app.railway.app/docs
```

---

## 📊 API Endpoints

### Health & Monitoring

- `GET /health` - Health check
- `GET /` - Root endpoint with API info
- `GET /docs` - Swagger UI
- `GET /redoc` - ReDoc documentation

### CA-003-01: Drift Forecasting

- `POST /api/v1/forecast` - Generate drift forecast
  ```json
  {
    "data": [100, 105, 103, 108, 110, 115],
    "horizon": 30,
    "model_type": "ensemble",
    "confidence_level": 0.95
  }
  ```

- `GET /api/v1/forecast/{forecast_id}` - Retrieve forecast

### CA-002: Correlation Analysis

- `POST /api/v1/correlations` - Analyze correlations
  ```json
  {
    "data": {
      "ice_cream_sales": [100, 120, 140, 160, 180],
      "temperature": [70, 75, 80, 85, 90]
    },
    "method": "pearson",
    "min_threshold": 0.3
  }
  ```

### CA-002-07: Natural Language Explanations

- `POST /api/v1/explanations` - Generate explanation
  ```json
  {
    "correlation": 0.87,
    "var1": "ice_cream_sales",
    "var2": "temperature",
    "p_value": 0.001,
    "style": "detailed"
  }
  ```

- `POST /api/v1/drift/analyze` - Analyze drift patterns

---

## 🧪 Testing Before Deployment

### 1. Install Dependencies Locally

```bash
cd /workspaces/control_tower/cloned_repos/business_ventures

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 2. Run Local Server

```bash
# Start FastAPI server
uvicorn main:app --reload --host 0.0.0.0 --port 8000

# Server will start at http://localhost:8000
# API docs at http://localhost:8000/docs
```

### 3. Test Endpoints

```bash
# Health check
curl http://localhost:8000/health

# Test forecast endpoint (mock data)
curl -X POST http://localhost:8000/api/v1/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "data": [100, 105, 103, 108, 110, 115, 112, 118, 120],
    "horizon": 30,
    "model_type": "ensemble",
    "confidence_level": 0.95
  }'

# Test explanation endpoint
curl -X POST http://localhost:8000/api/v1/explanations \
  -H "Content-Type: application/json" \
  -d '{
    "correlation": 0.87,
    "var1": "ice_cream_sales",
    "var2": "temperature",
    "p_value": 0.001,
    "style": "detailed"
  }'
```

### 4. Run Integration Tests

```bash
# Navigate to feature directory
cd Causal_affect/SYSTEM-CA-003_drift_forecasting/FEATURE-CA-003-01_time_series_forecasting_models

# Run integration tests
pytest tests/integration/test_integration.py -v

# Run with coverage
pytest tests/integration/test_integration.py --cov=src --cov-report=html
```

---

## 🔧 Integration Work Needed

### Priority 1: Wire Feature Orchestrators

**File**: `main.py`

Currently using mock responses. Need to import actual implementations:

```python
# TODO items in main.py:

# 1. CA-003-01 Forecasting
from Causal_affect.SYSTEM_CA_003_drift_forecasting.FEATURE_CA_003_01_time_series_forecasting_models.src.feature_integration import FeatureOrchestrator as ForecastOrchestrator

# 2. CA-002-07 Natural Language
from Causal_affect.SYSTEM_CA_002_correlation_analysis.FEATURE_CA_002_07_analysis_explanation.src.feature_integration import FeatureOrchestrator as ExplanationOrchestrator

# 3. Initialize on startup
forecast_orchestrator = ForecastOrchestrator()
explanation_orchestrator = ExplanationOrchestrator()
```

### Priority 2: Fix Import Paths

The generated code has import path mismatches. Need to:

1. Check actual module structure in `Causal_affect/`
2. Update imports in `feature_integration.py` files
3. Ensure `__init__.py` files exist in all packages
4. Test imports work correctly

### Priority 3: Add Database Models

For production:
- Create SQLAlchemy models for forecasts, correlations, analyses
- Add database migrations with Alembic
- Implement persistence layer

### Priority 4: Add Caching

- Implement Redis caching for frequently accessed forecasts
- Cache correlation analysis results
- Add cache invalidation logic

---

## 📈 Monitoring & Observability

### Logs

```bash
# View Railway logs
railway logs

# Follow logs in real-time
railway logs --follow
```

### Metrics

Railway provides automatic metrics:
- CPU usage
- Memory usage
- Request count
- Response times

Access via Railway dashboard.

### Custom Metrics (Future)

Add Prometheus metrics:
- Forecast generation time
- Model accuracy tracking
- API endpoint latency
- Error rates by endpoint

---

## 🔐 Security Checklist

- [ ] Change all secret keys in production
- [ ] Enable HTTPS only (Railway does this automatically)
- [ ] Configure CORS for specific origins
- [ ] Add rate limiting
- [ ] Implement API key authentication
- [ ] Add input validation on all endpoints
- [ ] Enable security headers
- [ ] Set up WAF rules if needed

---

## 💰 Cost Estimate

**Railway Pricing (Hobby Plan: $5/month)**:
- API service: Included
- PostgreSQL: Included  
- Redis: Included
- Custom domain: Free

**Estimated Monthly Cost**: $5-20 depending on usage

---

## 🚨 Rollback Plan

If deployment fails:

```bash
# Rollback to previous deployment
railway rollback

# OR redeploy specific version
railway up --detach <deployment-id>
```

---

## 📞 Support

- Railway Docs: https://docs.railway.app
- FastAPI Docs: https://fastapi.tiangolo.com
- Project Issues: Create issue in business_ventures repo

---

## ✅ Next Steps

1. **Immediate** (Before Deployment):
   - Fix import paths in feature_integration.py
   - Wire orchestrators into main.py
   - Run integration tests locally
   - Test with sample data

2. **Pre-Production**:
   - Set up staging environment in Railway
   - Deploy to staging
   - Run E2E tests against staging
   - Load testing

3. **Production Deploy**:
   - Set production env vars
   - Deploy to production
   - Monitor health checks
   - Test all endpoints

4. **Post-Deploy**:
   - Set up monitoring alerts
   - Configure backup strategy
   - Document API for users
   - Create example notebooks
