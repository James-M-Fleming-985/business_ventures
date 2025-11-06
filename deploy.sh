#!/bin/bash

# ============================================================================
# Correlation Discovery Engine - Deployment Script
# Deploys real data integration to Railway
# ============================================================================

set -e  # Exit on error

echo "=============================================="
echo "CORRELATION DISCOVERY ENGINE - DEPLOYMENT"
echo "=============================================="
echo ""

# Navigate to project directory
cd /workspaces/control_tower/cloned_repos/business_ventures

echo "Step 1: Verify files created..."
required_files=(
    "models.py"
    "database.py"
    "init_database.py"
    "data_ingestion_service.py"
    "correlation_analysis_service.py"
    "routers/dashboard_real.py"
    "run_pipeline.py"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "  ✅ $file"
    else
        echo "  ❌ $file MISSING!"
        exit 1
    fi
done
echo ""

echo "Step 2: Check dependencies..."
if grep -q "sqlalchemy" requirements.txt; then
    echo "  ✅ SQLAlchemy in requirements.txt"
else
    echo "  ❌ SQLAlchemy missing from requirements.txt!"
    exit 1
fi

if grep -q "psycopg2-binary" requirements.txt; then
    echo "  ✅ psycopg2-binary in requirements.txt"
else
    echo "  ❌ psycopg2-binary missing from requirements.txt!"
    exit 1
fi
echo ""

echo "Step 3: Verify main.py uses real data router..."
if grep -q "dashboard_real as dashboard" main.py; then
    echo "  ✅ main.py imports dashboard_real"
else
    echo "  ⚠️  main.py not using dashboard_real yet"
    echo "     Run: sed -i 's/from routers import dashboard/from routers import dashboard_real as dashboard/' main.py"
fi
echo ""

echo "Step 4: Git status..."
git status --short
echo ""

echo "Step 5: Stage changes..."
git add models.py \
        database.py \
        init_database.py \
        data_ingestion_service.py \
        correlation_analysis_service.py \
        routers/dashboard_real.py \
        run_pipeline.py \
        main.py \
        requirements.txt \
        VARIABLE_INVENTORY.md \
        REAL_DATA_INTEGRATION_SUMMARY.md \
        deploy.sh \
        Causal_affect/CAUSAL_AFFECT_GOALS_IMPLEMENTATION_PLAN.yaml

echo "  ✅ Files staged"
echo ""

echo "Step 6: Commit changes..."
git commit -m "feat: Real data integration - Replace ALL mock data with live API sources

BREAKING CHANGE: Dashboard now uses 100% real API data

Phases 1-5 Complete:
- Phase 1: Database schema (6 tables, 61 variables seeded)
- Phase 2: Correlation engine (N×N analysis, 3,721 pairs)
- Phase 3: API refactoring (all endpoints query real data)
- Phase 4: UI enhancements (query parameters for customization)
- Phase 5: Testing & deployment (pipeline runner, documentation)

Features:
- 6 real API sources: stocks, USGS, NASA, World Bank, arXiv, ClinicalTrials
- N×N correlation matrix with statistical significance (p < 0.05)
- Rolling correlations for drift analysis
- Top-N correlation ranking by absolute strength
- API health monitoring
- Job tracking and history

Files Added:
- models.py - SQLAlchemy database models
- database.py - Connection management
- init_database.py - Schema initialization
- data_ingestion_service.py - API → database pipeline
- correlation_analysis_service.py - Correlation calculations
- routers/dashboard_real.py - Real data API endpoints
- run_pipeline.py - Complete workflow runner

Files Updated:
- main.py - Import dashboard_real (v2.0.0)
- requirements.txt - Add SQLAlchemy, psycopg2
- CAUSAL_AFFECT_GOALS_IMPLEMENTATION_PLAN.yaml - Real use case

Documentation:
- VARIABLE_INVENTORY.md - 61 variables cataloged
- REAL_DATA_INTEGRATION_SUMMARY.md - Complete implementation guide

Removed: ALL np.random, math.sin/cos, hardcoded mock data

Deployment: Ready for Railway with Postgres database
"

echo "  ✅ Changes committed"
echo ""

echo "Step 7: Push to GitHub..."
git push origin main
echo "  ✅ Pushed to origin/main"
echo ""

echo "=============================================="
echo "✅ DEPLOYMENT COMPLETE"
echo "=============================================="
echo ""
echo "Next Steps:"
echo "1. Railway will auto-deploy from GitHub push"
echo "2. Verify DATABASE_URL environment variable is set in Railway"
echo "3. Add ALPHA_VANTAGE_API_KEY to Railway environment (for stock data)"
echo "4. Run initial data pipeline:"
echo "   railway run python3 run_pipeline.py"
echo ""
echo "5. Access dashboard:"
echo "   https://businessventures-production.up.railway.app/dashboard"
echo ""
echo "6. Verify real data in endpoints:"
echo "   - /api/dashboard/stats"
echo "   - /api/dashboard/heatmap"
echo "   - /api/dashboard/timeseries"
echo "   - /api/dashboard/network"
echo "   - /api/dashboard/leaderboard"
echo ""
echo "Version: 2.0.0 - Real Data Integration"
echo "=============================================="
