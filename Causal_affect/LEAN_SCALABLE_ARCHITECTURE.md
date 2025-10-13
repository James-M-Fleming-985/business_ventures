# Causal Affect: Lean + Scalable Architecture (Railway-First)

**Date:** October 13, 2025  
**Strategy:** Solo founder, automation-focused, Railway + managed services  
**Philosophy:** Build scalable from day 1, but start lean and grow with revenue

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Railway Platform                          │
├─────────────────────────────────────────────────────────────┤
│ Core Causal Affect Services:                                │
│  • API Gateway (FastAPI)                 - 1 service        │
│  • Data Ingestion Workers (Celery)      - 2-4 workers      │
│  • Correlation Engine (Celery)          - 2-4 workers      │
│  • Forecasting Engine (Celery)          - 1-2 workers      │
│  • Opportunity Assessor (FastAPI)       - 1 service        │
│  • MVP Generator (FastAPI)              - 1 service        │
│  • Dashboard Frontend (React)           - 1 service        │
│                                                              │
│ Data Layer (Railway):                                       │
│  • PostgreSQL (primary database)        - 1 instance        │
│  • Redis (cache + queue)                - 1 instance        │
│                                                              │
│ Generated MVPs:                                             │
│  • MVP-1, MVP-2, ... MVP-N             - 1 service each    │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│              External Managed Services                       │
├─────────────────────────────────────────────────────────────┤
│ • Supabase (backup PostgreSQL + Auth)   - Free → $25/mo    │
│ • Upstash (Redis + Kafka for streaming) - Free → $10/mo    │
│ • Neon (serverless Postgres backup)     - Free → $20/mo    │
│ • Cloudflare R2 (object storage)        - Free → $15/mo    │
│ • TimescaleDB Cloud (time-series only)  - $50/mo (optional)│
└─────────────────────────────────────────────────────────────┘
```

## Revised Performance Targets (Scalable but Realistic)

### Phase 1: Launch (Month 1-3)
| Metric | Original | Lean Scalable | Rationale |
|--------|----------|---------------|-----------|
| **Data Volume** | 10+ TB | **50-100 GB** | Enough to find real patterns, manageable costs |
| **API Sources** | 15-20 | **8-12 sources** | Cover major data categories, not overwhelming |
| **Correlations** | 10000+ | **1000-2000** | Statistically significant, faster to process |
| **Ingestion Time** | 15 min | **30-60 min** | Acceptable for overnight/scheduled jobs |
| **Correlation Time** | 10 min | **15-20 min** | Real-time not critical, batch is fine |
| **Forecast Time** | 5 min | **5-10 min** | Keep original - this is critical path |
| **MVP Deployment** | 30 min | **10-15 min** | Railway is FAST, leverage it |
| **Active MVPs** | Unlimited | **10-20 concurrent** | Monitor, scale, archive the losers |

### Phase 2: Growth (Month 4-12)
| Metric | Target | Infrastructure Adjustment |
|--------|--------|---------------------------|
| **Data Volume** | 500 GB - 1 TB | Add TimescaleDB Cloud, optimize queries |
| **API Sources** | 15-20 sources | Add workers, implement rate limiting |
| **Correlations** | 5000-10000 | Add Dask/Ray for parallel processing |
| **Active MVPs** | 50-100 concurrent | Evaluate Railway limits, consider multi-region |
| **Cost** | $500-1000/mo | Revenue from successful MVPs funds growth |

### Phase 3: Scale (Year 2+)
| Metric | Target | Infrastructure Adjustment |
|--------|--------|---------------------------|
| **Data Volume** | 5-10 TB | Consider dedicated infrastructure or AWS |
| **Correlations** | 10000+ | Distributed computing cluster |
| **Active MVPs** | 200+ concurrent | Hybrid Railway + Kubernetes if needed |

## Technology Stack (Railway-Optimized)

### Backend
- **FastAPI** (Railway-native Python support)
- **Celery + Redis** (Railway Redis add-on)
- **PostgreSQL** (Railway PostgreSQL add-on)
- **SQLAlchemy** (ORM for portability)

### Data Processing
- **Pandas + NumPy** (start here, scale to Dask if needed)
- **SciPy** (correlation + statistics)
- **Statsmodels** (ARIMA forecasting)
- **Prophet** (Facebook's forecasting - easy to use)

### Frontend
- **React + Vite** (fast Railway deployments)
- **TailwindCSS** (no build complexity)
- **Recharts** (simple, works offline)
- **WebSockets** (real-time updates via Railway)

### Storage
- **PostgreSQL** (relational data - Railway)
- **Redis** (caching + queues - Railway)
- **Cloudflare R2** (large files, backups - $0.015/GB)
- **TimescaleDB Cloud** (optional, add when time-series queries slow)

### External APIs (8-12 Critical Sources)

**Category 1: Financial Markets (3-4 sources)**
- Alpha Vantage (stocks, forex, crypto)
- CoinGecko (crypto markets)
- Federal Reserve Economic Data (FRED)
- Yahoo Finance (backup/free option)

**Category 2: Web Analytics (2-3 sources)**
- Google Trends API
- Twitter/X API (trending topics)
- Reddit API (subreddit activity)

**Category 3: E-commerce (2-3 sources)**
- Amazon Product Advertising API
- Shopify API (store data if available)
- eBay API

**Category 4: Developer Ecosystem (1-2 sources)**
- GitHub API (trending repos, stars)
- npm API (package downloads)

**Total: 8-12 sources covering major opportunity categories**

## Deployment Strategy: Railway-First

### Core Platform Deployment
```yaml
# railway.json (root project)
{
  "build": {
    "builder": "NIXPACKS",
    "buildCommand": "pip install -r requirements.txt"
  },
  "deploy": {
    "startCommand": "uvicorn app.main:app --host 0.0.0.0 --port $PORT",
    "healthcheckPath": "/health",
    "restartPolicyType": "ON_FAILURE"
  }
}
```

### Generated MVP Deployment
```yaml
# railway.json (per MVP)
{
  "build": {
    "builder": "NIXPACKS"
  },
  "deploy": {
    "startCommand": "npm start",
    "healthcheckPath": "/",
    "restartPolicyType": "ON_FAILURE"
  },
  "regions": ["us-west"],
  "scaling": {
    "minInstances": 1,
    "maxInstances": 3
  }
}
```

### Key Railway Features Leveraged
1. **Automatic Git Deployments** - Push to GitHub, Railway deploys
2. **Environment Variables** - Secrets management built-in
3. **PostgreSQL Add-on** - One-click database provisioning
4. **Redis Add-on** - One-click cache/queue
5. **Custom Domains** - Free SSL certificates
6. **Rollbacks** - One-click rollback to previous deployment
7. **Metrics** - Built-in monitoring (CPU, memory, network)
8. **Logs** - Centralized logging with search

## Cost Projection (Lean + Scalable)

### Month 1-3 (Launch Phase)
```
Railway Pro:                $20/month (base)
Causal Affect Core:         $50/month (1 backend, 4 workers, 1 frontend)
PostgreSQL:                 $25/month (10 GB)
Redis:                      $10/month (512 MB)
5 Active MVPs:              $50/month ($10 each)
Cloudflare R2:              $5/month (50 GB storage)
External APIs:              $50/month (some free tiers + paid)
──────────────────────────────────────
TOTAL:                      ~$210/month
```

### Month 4-12 (Growth Phase)
```
Railway Pro:                $20/month
Causal Affect Core:         $150/month (scaled workers)
PostgreSQL:                 $75/month (100 GB)
Redis:                      $25/month (2 GB)
TimescaleDB Cloud:          $50/month (time-series optimization)
20 Active MVPs:             $200/month ($10 each)
Cloudflare R2:              $20/month (200 GB)
External APIs:              $100/month (higher tier plans)
Supabase:                   $25/month (backup + auth)
──────────────────────────────────────
TOTAL:                      ~$665/month
```

### Revenue Required for Profitability
- **5 MVPs @ $50/month MRR each** = $250/month → Covers launch costs
- **20 MVPs @ $50/month MRR each** = $1000/month → Covers growth costs + profit
- **Target: 30% of MVPs generate $50+/month** (6 out of 20 = $300+ profit)

## Data Processing Approach (50-100 GB, 8-12 APIs)

### Ingestion Strategy
```python
# Parallel API ingestion (4 workers)
# 8-12 APIs × 5-10 GB each = 50-100 GB total
# Target: 30-60 minutes (acceptable for batch processing)

class DataIngestionOrchestrator:
    def ingest_all_sources(self):
        # Railway Celery workers
        tasks = [
            ingest_financial_data.delay(),      # 20-30 GB
            ingest_web_analytics.delay(),       # 10-15 GB
            ingest_ecommerce_data.delay(),      # 15-20 GB
            ingest_developer_data.delay(),      # 5-10 GB
        ]
        
        # Wait for all (30-60 min total)
        results = [task.get() for task in tasks]
        
        # Validate: Expect 50-100 GB ingested
        assert sum(r['bytes_ingested'] for r in results) > 50_000_000_000
```

### Correlation Strategy
```python
# 1000-2000 correlations (manageable, meaningful)
# If 100 variables across 8-12 sources
# 100 × 99 / 2 = 4,950 possible correlations
# Filter to top 1000-2000 by initial relevance score

class CorrelationEngine:
    def calculate_correlations(self, variables: List[Variable]):
        # Parallel processing (4 workers)
        # Target: 15-20 minutes for 1000-2000 correlations
        
        # Pre-filter to reduce computation
        relevant_pairs = self.filter_likely_correlations(variables)
        
        # Parallel correlation calculation
        correlations = parallel_correlate(relevant_pairs, n_workers=4)
        
        # Keep top 1000-2000 by statistical significance
        return sorted(correlations, key=lambda c: c.p_value)[:2000]
```

## Scaling Triggers (When to Upgrade)

### Add TimescaleDB Cloud ($50/mo)
**Trigger:** PostgreSQL queries on time-series data take >5 seconds

### Add More Workers ($50/mo)
**Trigger:** Ingestion/correlation taking >90 minutes consistently

### Add Dask/Ray ($100/mo compute)
**Trigger:** Need to process 5000+ correlations regularly

### Consider Kubernetes ($500+/mo)
**Trigger:** 100+ active MVPs, Railway limits reached, need multi-region

### Move to Dedicated Infrastructure ($1000+/mo)
**Trigger:** $50k+/month revenue, need full control, complex networking

## Development Workflow (Solo Founder Optimized)

### Local Development
```bash
# Docker Compose for local testing
docker-compose up  # PostgreSQL + Redis locally

# Connect to Railway for staging
railway link
railway run python manage.py test
```

### Deployment
```bash
# Automatic on git push (Railway watches GitHub)
git add .
git commit -m "Add new correlation algorithm"
git push origin main
# Railway deploys automatically in ~3-5 minutes
```

### Monitoring
- Railway dashboard (CPU, memory, logs)
- Uptime monitoring: UptimeRobot (free tier)
- Error tracking: Sentry (free tier, 5k errors/month)
- Analytics: PostHog (free tier, self-hosted on Railway)

## Migration Path (If You Outgrow Railway)

Railway is designed for growth, but if you hit limits:

### Option 1: Railway → Kubernetes (Year 2+)
- Export Docker images
- Deploy to GKE/EKS
- Keep Railway for MVPs (they're perfect for it)

### Option 2: Railway → Serverless (Alternative)
- Core logic → AWS Lambda / Google Cloud Functions
- Keep Railway for long-running workers
- Best for spiky/unpredictable workloads

### Option 3: Hybrid (Most Likely)
- Causal Affect core → Dedicated infrastructure
- MVP deployments → Railway forever (it's ideal for this)
- Data processing → Cloud batch jobs (AWS Batch, GCP Dataflow)

## Key Advantages of This Approach

✅ **Solo-Founder Friendly:** No DevOps complexity, focus on product  
✅ **Scalable:** Can grow to 500 GB-1 TB without major rewrites  
✅ **Cost-Effective:** Start at $200/mo, scale with revenue  
✅ **Fast Iteration:** Railway deploys in 5 minutes, not 30  
✅ **Portable:** Standard PostgreSQL/Redis, can migrate if needed  
✅ **Automated:** Railway handles scaling, monitoring, SSL, domains  
✅ **Revenue-Focused:** Multiple MVPs = multiple revenue experiments  

## Success Metrics (Revised)

### Technical Success
- ✅ 50-100 GB ingested daily
- ✅ 8-12 API sources connected
- ✅ 1000-2000 correlations analyzed
- ✅ 5-10 opportunities identified per week
- ✅ 10-minute MVP deployments
- ✅ 10-20 active MVPs monitored

### Business Success
- ✅ 1 MVP generating $500+/month (within 6 months)
- ✅ 5 MVPs generating $100+/month (within 9 months)
- ✅ 10 MVPs generating $50+/month (within 12 months)
- ✅ Total MRR: $2000+/month (covers costs + salary)

**Outcome:** Profitable solo SaaS business with automation doing the heavy lifting.
