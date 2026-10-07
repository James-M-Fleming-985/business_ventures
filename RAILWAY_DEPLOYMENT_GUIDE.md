# Railway Deployment Guide

## 🚀 Deploy Causal Affect Platform to Railway

### Step 1: Login to Railway
```bash
cd /workspaces/control_tower/cloned_repos/business_ventures
railway login
```
This will open a browser window to authenticate.

### Step 2: Initialize Railway Project
```bash
railway init
```
- Select "Create a new project"
- Name it: `causal-affect-platform`

### Step 3: Link to GitHub Repository
```bash
railway link
```
- Select the `business_ventures` repository

### Step 4: Set Environment Variables
```bash
# Security keys (from .env)
railway variables set SECRET_KEY="<ROTATED-REDACTED-SECRET_KEY>"
railway variables set JWT_SECRET_KEY="<ROTATED-REDACTED-JWT_SECRET_KEY>"
railway variables set ENCRYPTION_KEY="<ROTATED-REDACTED-ENCRYPTION_KEY>"

# API Keys
railway variables set ALPHA_VANTAGE_API_KEY="<ROTATED-REDACTED-ALPHA_VANTAGE_API_KEY>"
railway variables set FRED_API_KEY=""  # Optional - add later
railway variables set OPENWEATHER_API_KEY=""  # Optional - add later

# Application config
railway variables set ENVIRONMENT="production"
railway variables set DEBUG="False"
railway variables set LOG_LEVEL="INFO"
```

### Step 5: Add PostgreSQL (Optional)
```bash
railway add --plugin postgresql
```

### Step 6: Add Redis (Optional)
```bash
railway add --plugin redis
```

### Step 7: Deploy!
```bash
railway up
```

### Step 8: Get Deployment URL
```bash
railway domain
```

### Step 9: Test Deployed API
```bash
RAILWAY_URL=$(railway status --json | jq -r '.environment.domains[0]')
curl https://$RAILWAY_URL/health
curl https://$RAILWAY_URL/docs  # Interactive API documentation
```

## 🧪 Testing Deployed Endpoints

### Health Check
```bash
curl https://your-app.railway.app/health
```

### Correlation Analysis
```bash
curl -X POST https://your-app.railway.app/api/v1/correlations \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "ice_cream_sales": [100, 120, 140, 160, 180, 200],
      "temperature": [70, 75, 80, 85, 90, 95]
    },
    "method": "pearson",
    "min_threshold": 0.5
  }'
```

### Natural Language Explanation
```bash
curl -X POST https://your-app.railway.app/api/v1/explanations \
  -H "Content-Type: application/json" \
  -d '{
    "correlation": 0.99,
    "var1": "ice_cream_sales",
    "var2": "temperature",
    "p_value": 0.001,
    "style": "detailed"
  }'
```

### Drift Forecasting
```bash
curl -X POST https://your-app.railway.app/api/v1/forecast \
  -H "Content-Type: application/json" \
  -d '{
    "data": [100, 105, 103, 108, 110, 115, 112, 118, 120],
    "horizon": 7,
    "model_type": "linear",
    "confidence_level": 0.95
  }'
```

## 📊 What's Deployed

### Working Endpoints:
- ✅ `GET /health` - Health check
- ✅ `GET /` - API info
- ✅ `GET /docs` - Interactive API documentation
- ✅ `POST /api/v1/correlations` - Statistical correlation analysis
- ✅ `POST /api/v1/explanations` - Natural language explanations
- ✅ `POST /api/v1/forecast` - Time series forecasting

### Working Data Sources (8 APIs):
- ✅ Alpha Vantage - Stock market data
- ✅ World Bank - Global economic indicators
- ✅ US Census - Demographics
- ✅ USGS - Earthquake data
- ✅ NASA EONET - Environmental events
- ✅ PubMed - Medical research
- ✅ arXiv - Scientific papers
- ✅ ClinicalTrials.gov - Clinical trials

### Features:
- Real statistical correlation analysis (Pearson, Spearman, Kendall)
- P-values and significance testing
- Natural language explanations
- Linear trend forecasting with confidence intervals
- Automatic dependency installation (requirements.txt)
- Health monitoring endpoint
- CORS enabled for web clients

## 🔧 Troubleshooting

### View Logs
```bash
railway logs
```

### Check Deployment Status
```bash
railway status
```

### Redeploy
```bash
git push origin main  # Railway auto-deploys on push
# OR
railway up  # Manual deployment
```

### Environment Variables
```bash
railway variables  # List all variables
```

## 🎯 Next Steps After Deployment

1. **Test all endpoints** using the `/docs` interactive UI
2. **Monitor logs** for any errors
3. **Add remaining API keys** (FRED, OpenWeather) if needed
4. **Set up custom domain** (optional)
5. **Extract patterns** for template system
6. **Scale up** if needed (Railway auto-scales)

## 📈 Expected Performance

- **Cold start**: ~3-5 seconds
- **Response time**: 50-200ms for most endpoints
- **API rate limits**: Depends on external APIs (Alpha Vantage: 5/min, 500/day)
- **Concurrent requests**: Uvicorn with 2 workers handles 100+ req/s

## ✅ Success Criteria

Deployment is successful when:
- [ ] Health endpoint returns 200 OK
- [ ] /docs shows interactive API documentation
- [ ] Correlation analysis returns valid results
- [ ] Explanations generate meaningful text
- [ ] Forecasting produces trend predictions
- [ ] No errors in Railway logs
