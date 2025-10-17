#!/bin/bash
# CA-006 Dashboard Startup Script
# Starts backend API and frontend dashboard, then opens in browser

set -e

echo "🚀 Starting CA-006 Feedback Dashboard..."
echo ""

# Kill any existing processes
echo "📋 Cleaning up existing processes..."
pkill -f "uvicorn.*8000" 2>/dev/null || true
pkill -f "node.*vite" 2>/dev/null || true
sleep 2

# Get the workspace root
WORKSPACE_ROOT="/workspaces/business_ventures/Causal_affect/SYSTEM-CA-006_feedback_iteration"

# Start backend
echo "🔧 Starting FastAPI backend on port 8000..."
cd "$WORKSPACE_ROOT/src/backend"
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload > /tmp/ca006-backend.log 2>&1 &
BACKEND_PID=$!
echo "   Backend PID: $BACKEND_PID"

# Wait for backend to be ready
echo "   Waiting for backend to start..."
for i in {1..10}; do
    if curl -s http://localhost:8000/health > /dev/null 2>&1; then
        echo "   ✅ Backend is ready!"
        break
    fi
    sleep 1
done

# Start frontend
echo "🎨 Starting Vite frontend dev server..."
cd "$WORKSPACE_ROOT/FEATURE-CA-006-06_dashboard_ui/dashboard-app-complete"
npm run dev > /tmp/ca006-frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   Frontend PID: $FRONTEND_PID"

# Wait for frontend to be ready
echo "   Waiting for frontend to start..."
sleep 5

# Detect the frontend port (Vite might use 5173 or 5174)
FRONTEND_PORT=$(lsof -i :5173 -i :5174 2>/dev/null | grep LISTEN | awk '{print $9}' | cut -d: -f2 | head -1)

if [ -z "$FRONTEND_PORT" ]; then
    echo "   ⚠️  Could not detect frontend port, trying 5173..."
    FRONTEND_PORT=5173
fi

echo "   ✅ Frontend is ready on port $FRONTEND_PORT!"
echo ""

# Display URLs
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✨ CA-006 Dashboard is running!"
echo ""
echo "   📊 Frontend Dashboard: http://localhost:$FRONTEND_PORT"
echo "   🔌 Backend API:        http://localhost:8000"
echo "   📖 API Documentation:  http://localhost:8000/docs"
echo ""
echo "   💡 Tip: Copy the URLs above into your browser"
echo ""
echo "   Logs:"
echo "   - Backend:  tail -f /tmp/ca006-backend.log"
echo "   - Frontend: tail -f /tmp/ca006-frontend.log"
echo ""
echo "   To stop: pkill -f 'uvicorn.*8000'; pkill -f 'node.*vite'"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Try to open in browser
echo "🌐 Attempting to open in browser..."
if [ -n "$BROWSER" ]; then
    $BROWSER http://localhost:$FRONTEND_PORT &
    echo "   ✅ Browser command executed"
else
    echo "   ⚠️  No browser command found"
    echo "   Please open http://localhost:$FRONTEND_PORT manually"
fi

echo ""
echo "Press Ctrl+C to view logs, or check VS Code PORTS panel for forwarded URLs"
echo ""

# Keep script running and show live logs
tail -f /tmp/ca006-frontend.log /tmp/ca006-backend.log
