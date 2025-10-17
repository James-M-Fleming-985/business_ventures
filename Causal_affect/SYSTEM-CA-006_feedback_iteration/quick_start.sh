#!/bin/bash
# Quick start script for CA-006 Dashboard

pkill -9 -f "uvicorn" 2>/dev/null || true
pkill -9 -f "vite" 2>/dev/null || true
sleep 2

cd /workspaces/business_ventures/Causal_affect/SYSTEM-CA-006_feedback_iteration/src/backend
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 &

cd /workspaces/business_ventures/Causal_affect/SYSTEM-CA-006_feedback_iteration/FEATURE-CA-006-06_dashboard_ui/dashboard-app-complete
npm run dev &

sleep 5

echo ""
echo "✅ Dashboard Started!"
echo ""
echo "   Frontend: http://localhost:5173 (or check PORTS tab for forwarded URL)"
echo "   Backend:  http://localhost:8000"
echo ""
echo "Check VS Code's PORTS panel (bottom) and click the globe icon!"
