# Railway Deployment Instructions

Your Railway project "Causal Affect" is ready at:
https://railway.app/project/561cf2bc-95df-4ba3-9493-cf307dd274ee

## Current Setup:
- Project: Causal Affect
- Environment: production  
- Service: thriving-unity (ready for deployment)
- Database: Postgres (already configured)

## Deploy Steps:

### 1. Connect GitHub Repository
1. Go to Railway dashboard
2. Click "thriving-unity" service
3. Settings → Source → "Connect Repo"
4. Select your GitHub repository
5. Set root directory if needed: `cloned_repos/business_ventures`

### 2. Set Environment Variables
In Railway dashboard → Variables tab, add:

```bash
# Security Keys (REQUIRED)
SECRET_KEY=kzs6bCPuakEZbhTy0QWBL6RemHWg9hBPM9bvXCMmd4U
JWT_SECRET_KEY=EeYuhDw23Ep4wG6_K8Av5MOzsHoHxtuk2vA41Hivhnw
ENCRYPTION_KEY=kI4Yw4mfxz1P7k4EF2fnxKrgrZkXhNVf8ym4zTtN_2g=

# API Keys (REQUIRED)
ALPHA_VANTAGE_API_KEY=LXZVLRE451QDNO34

# Database (auto-provided by Railway Postgres)
DATABASE_URL=${{Postgres.DATABASE_URL}}

# Optional - Collect Later
FRED_API_KEY=
OPENWEATHER_API_KEY=
```

### 3. Deploy
Railway will automatically:
- Detect `railway.toml` configuration
- Install dependencies from `requirements.txt`
- Start server: `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 2`
- Configure healthcheck at `/health`
- Enable autoscaling (1-3 replicas)

### 4. Verify Deployment
Once deployed, test these endpoints:

```bash
# Replace with your Railway URL
export RAILWAY_URL=https://thriving-unity.up.railway.app

# Health check
curl $RAILWAY_URL/health

# API docs
open $RAILWAY_URL/docs

# Test correlation endpoint
curl -X POST $RAILWAY_URL/api/v1/correlations \
  -H "Content-Type: application/json" \
  -d '{
    "data": {
      "ice_cream_sales": [100, 120, 140, 160, 180, 200],
      "temperature": [70, 75, 80, 85, 90, 95]
    },
    "method": "pearson"
  }'
```

## What's Working:
✅ 8 API data sources tested and ready
✅ Correlation analysis (r=0.99 for ice cream/temperature)
✅ Statistical forecasting with ARIMA
✅ Natural language explanations
✅ Interactive API docs at /docs

## Next Steps After Deployment:
1. Add custom domain (optional)
2. Monitor logs in Railway dashboard
3. Collect FRED + OpenWeather API keys (optional)
4. Extract patterns for template system
