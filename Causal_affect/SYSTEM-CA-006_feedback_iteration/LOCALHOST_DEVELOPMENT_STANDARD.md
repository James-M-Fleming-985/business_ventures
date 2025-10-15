# Full-Stack Local Development Standard
# =====================================
# CA-006 Feedback Iteration System
# Created: October 15, 2025

## Purpose
This document defines the STANDARD workflow for viewing a complete full-stack system on localhost, ensuring all developers follow the same process.

---

## Overview: Full-Stack System Components

A complete system has:
1. **Backend API** (Python/FastAPI) - Serves data, business logic
2. **Frontend UI** (React/TypeScript) - User interface, visualizations
3. **Database** (PostgreSQL) - Data persistence
4. **Cache** (Redis) - Optional, for performance

---

## Standard Workflow: View System on Localhost

### Step 1: Verify Backend Implementation Exists

**Check for:**
```bash
cd /workspaces/business_ventures/Causal_affect/SYSTEM-CA-006_feedback_iteration

# Look for FastAPI application
find . -name "main.py" -o -name "app.py" | grep -E "app|backend|api"

# Look for requirements.txt
find . -name "requirements.txt"

# Look for feature implementations
ls -la FEATURE-CA-006-0*/src/
```

**Expected:**
- ✅ Backend API entry point (main.py with FastAPI app)
- ✅ Requirements file with dependencies
- ✅ Feature implementation files (generated code)

**If missing:**
- ❌ Backend hasn't been integrated yet
- ⚠️ Individual features generated but not combined into unified API

---

### Step 2: Verify Frontend Implementation Exists

**Check for:**
```bash
# Look for React application
find . -name "package.json" | grep -E "dashboard|frontend|ui"

# Look for src directory with React components
ls -la */src/*.jsx */src/*.tsx 2>/dev/null
```

**Expected:**
- ✅ package.json with React dependencies
- ✅ src/ directory with components
- ✅ Vite/Webpack configuration

**If missing:**
- ❌ Frontend hasn't been extracted from generators
- ⚠️ Need to run setup script to create React app

---

### Step 3: Start Backend Server

**Standard Commands:**
```bash
# Navigate to backend directory
cd /path/to/backend

# Create virtual environment (first time only)
python3 -m venv venv
source venv/bin/activate

# Install dependencies (first time only)
pip install -r requirements.txt

# Set environment variables
export DATABASE_URL="postgresql://user:pass@localhost:5432/ca006"
export REDIS_URL="redis://localhost:6379"

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

**Expected Output:**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
INFO:     Application startup complete
```

**Verify:**
```bash
# Test API is responding
curl http://localhost:8000/health
# Should return: {"status": "healthy"}

# Check API documentation
open http://localhost:8000/docs  # Swagger UI
```

---

### Step 4: Start Frontend Dev Server

**Standard Commands:**
```bash
# Navigate to frontend directory
cd /path/to/frontend

# Install dependencies (first time only)
npm install

# Configure API endpoint
cat > .env << EOF
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_ENVIRONMENT=development
EOF

# Start dev server
npm run dev
```

**Expected Output:**
```
VITE vX.X.X  ready in XXX ms

➜  Local:   http://localhost:5173/
➜  Network: http://192.168.x.x:5173/
```

**Verify:**
```bash
# Open browser
open http://localhost:5173

# Check browser console (F12)
# Should see successful API calls, no CORS errors
```

---

### Step 5: Verify Full Integration

**Checklist:**
- [ ] Backend running on port 8000
- [ ] Frontend running on port 5173
- [ ] Frontend can fetch data from backend
- [ ] No CORS errors in browser console
- [ ] Real data (not mock data) displayed
- [ ] WebSocket connections established (if applicable)
- [ ] API calls visible in Network tab

**Test Integration:**
```bash
# From browser console (F12):
fetch('http://localhost:8000/api/v1/portfolio/overview')
  .then(r => r.json())
  .then(console.log)

# Should return real portfolio data, not mock data
```

---

## Common Issues & Solutions

### Issue 1: Backend Not Found
**Problem:** No main.py or unified backend application
**Solution:** 
- Features were generated individually
- Need to create integration layer combining all features
- Use `create_integrated_backend.py` script

### Issue 2: Frontend Shows Mock Data
**Problem:** VITE_API_URL not configured or backend not running
**Solution:**
- Check `.env` file has correct API URL
- Verify backend is running on port 8000
- Check browser console for network errors

### Issue 3: CORS Errors
**Problem:** Backend not allowing frontend origin
**Solution:**
- Add CORS middleware to FastAPI:
```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### Issue 4: Port Already in Use
**Problem:** Port 8000 or 5173 already occupied
**Solution:**
```bash
# Find and kill process
lsof -ti:8000 | xargs kill -9
lsof -ti:5173 | xargs kill -9

# Or use different ports
uvicorn app.main:app --port 8001
npm run dev -- --port 5174
```

---

## CA-006 Specific Structure

### Expected Directory Structure:
```
SYSTEM-CA-006_feedback_iteration/
├── backend/                          # Integrated backend (TO BE CREATED)
│   ├── app/
│   │   ├── main.py                   # FastAPI app entry point
│   │   ├── api/
│   │   │   └── v1/                   # API routes
│   │   │       ├── analytics.py      # From FEATURE-01
│   │   │       ├── engagement.py     # From FEATURE-02
│   │   │       ├── revenue.py        # From FEATURE-03
│   │   │       ├── prioritization.py # From FEATURE-04
│   │   │       └── archive.py        # From FEATURE-05
│   │   ├── models/                   # Pydantic models
│   │   ├── services/                 # Business logic
│   │   └── database/                 # DB connections
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                         # React dashboard (EXISTS as dashboard-app-complete)
│   ├── src/
│   │   ├── main.jsx
│   │   ├── App.jsx
│   │   ├── components/
│   │   └── pages/
│   ├── package.json
│   └── .env
│
├── FEATURE-CA-006-01_analytics_integration/     # Individual feature (generated)
├── FEATURE-CA-006-02_engagement_tracking/       # Individual feature (generated)
├── FEATURE-CA-006-03_revenue_tracking/          # Individual feature (generated)
├── FEATURE-CA-006-04_prioritization_engine/     # Individual feature (generated)
├── FEATURE-CA-006-05_archive_automation/        # Individual feature (generated)
└── FEATURE-CA-006-06_dashboard_ui/              # Frontend feature
    ├── dashboard-app-complete/                  # ✅ EXISTS
    └── create_complete_dashboard.py
```

---

## Current State Assessment

### ✅ What Exists:
1. **FEATURE-01 through FEATURE-05** - Backend features generated (Python code)
2. **FEATURE-06** - Frontend dashboard exists (dashboard-app-complete)
3. **UI_VISUALIZATION.md** - Complete UI specification

### ❌ What's Missing:
1. **Integrated Backend** - No unified FastAPI app combining all features
2. **Database Setup** - No PostgreSQL/Redis running
3. **API Routes** - Features not exposed as REST endpoints
4. **Backend-Frontend Connection** - Frontend using mock data only

---

## Recommended Action Plan

### Option A: Quick Demo (Frontend Only) ✅ CURRENT STATE
**What you see:** Beautiful UI with sample data
**Time:** 2 minutes
**Pros:** Instant visual feedback
**Cons:** Not real system, no backend integration

### Option B: Integrated Backend + Frontend (RECOMMENDED)
**What you get:** Full working system with real data flow
**Time:** 30-60 minutes
**Steps:**
1. Create integrated backend combining FEATURES 1-5
2. Set up database (SQLite for quick start, or PostgreSQL)
3. Create API routes for all endpoints
4. Connect frontend to backend
5. Test full data flow

### Option C: Docker Compose (Production-Like)
**What you get:** Production-ready local environment
**Time:** 60-90 minutes
**Steps:**
1. Create docker-compose.yml
2. Backend container (FastAPI + PostgreSQL + Redis)
3. Frontend container (Vite dev server)
4. Nginx reverse proxy (optional)
5. One command to start everything

---

## Standard Commands Summary

### Check What Exists:
```bash
# Backend
ls -la backend/app/main.py 2>/dev/null && echo "✅ Backend exists" || echo "❌ Backend missing"

# Frontend  
ls -la frontend/package.json 2>/dev/null && echo "✅ Frontend exists" || echo "❌ Frontend missing"

# Database
psql -l 2>/dev/null && echo "✅ PostgreSQL running" || echo "❌ PostgreSQL not running"
```

### Start Everything:
```bash
# Terminal 1: Backend
cd backend && source venv/bin/activate && uvicorn app.main:app --reload

# Terminal 2: Frontend
cd frontend && npm run dev

# Terminal 3: Database (if needed)
docker run -p 5432:5432 -e POSTGRES_PASSWORD=password postgres
```

### Stop Everything:
```bash
pkill -f uvicorn
pkill -f vite
docker stop $(docker ps -q)
```

---

## Verification Checklist

Before reporting "system is running on localhost", verify:

- [ ] Backend API responds to health check
- [ ] Backend API documentation accessible (http://localhost:8000/docs)
- [ ] Frontend loads in browser (http://localhost:5173)
- [ ] Frontend console shows no errors
- [ ] Network tab shows successful API calls to backend
- [ ] Data in UI matches backend responses (not mock data)
- [ ] Database has data (check via psql or admin tool)
- [ ] WebSocket connections established (if applicable)
- [ ] All features functional (analytics, engagement, revenue, etc.)

---

## CA-006 Current Reality

**TODAY (October 15, 2025):**

✅ **Frontend:** Complete dashboard running on http://localhost:5173
- Beautiful UI matching UI_VISUALIZATION.md
- Charts, tables, metrics all working
- **BUT: Using mock/sample data only**

❌ **Backend:** Not integrated yet
- Individual features generated (FEATURES 1-5)
- No unified FastAPI application
- No API endpoints exposed
- No database connected

**TO GET FULL SYSTEM:**
Need to create integrated backend that:
1. Combines all 5 feature implementations
2. Exposes REST API endpoints
3. Connects to database
4. Serves data to frontend

---

## Next Step Decision

**Developer, you need to choose:**

### Path 1: Accept Frontend Demo ✅
- Keep current dashboard with mock data
- Good for UI review, design feedback
- **Time:** 0 minutes (already done)

### Path 2: Build Integrated Backend 🛠️
- I can create script to combine FEATURES 1-5
- Set up FastAPI with all endpoints
- Connect to SQLite (quick) or PostgreSQL
- Connect frontend to real backend
- **Time:** 30-60 minutes of development

### Path 3: Full Production Setup 🚀
- Docker Compose with all services
- Production-ready configuration
- Database migrations
- Full testing suite
- **Time:** 1-2 hours

**Which path do you want to take?**

---

## Documentation Standard

Every system should include:
1. **README.md** - Quick start guide
2. **LOCALHOST_DEVELOPMENT_STANDARD.md** - This file
3. **DEPLOYMENT_GUIDE.md** - Production deployment
4. **.env.example** - Environment variables template
5. **docker-compose.yml** - Local development stack (optional)

---

## Contact

For questions about this standard:
- Review this document first
- Check if backend/frontend both exist and are running
- Verify ports 8000 (backend) and 5173 (frontend)
- Check browser console and network tab for errors

**Last Updated:** October 15, 2025  
**System:** CA-006 Feedback Iteration System  
**Status:** Frontend Complete, Backend Integration Pending
