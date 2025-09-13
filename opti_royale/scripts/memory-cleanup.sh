#!/bin/bash

# 🧹 OptiRoyale Memory Management Script
# Aggressive memory optimization for development environment

echo "🧹 OptiRoyale Memory Cleanup & Optimization"
echo "=========================================="
echo "$(date): Starting aggressive memory optimization..."

# Check initial memory state
echo ""
echo "📊 BEFORE OPTIMIZATION:"
free -h

# Kill memory-heavy processes
echo ""
echo "🔫 Stopping memory-heavy processes..."
pkill -f "next-server" 2>/dev/null
pkill -f "turbo.*daemon" 2>/dev/null
pkill -f "esbuild.*service" 2>/dev/null

# Restart TypeScript servers with lower memory
echo "🔄 Restarting TypeScript servers with optimized settings..."
pkill -f "tsserver.js" 2>/dev/null

# Clear temporary files and caches
echo "🗑️  Clearing temporary files and caches..."
rm -rf /tmp/vscode-typescript* /tmp/tsc-* 2>/dev/null
rm -rf /workspaces/opti_royale/.turbo-cache 2>/dev/null
rm -rf /workspaces/opti_royale/.turbo 2>/dev/null
rm -rf /workspaces/opti_royale/apps/web/.next 2>/dev/null
find /workspaces/opti_royale -name "*.log" -delete 2>/dev/null

# Clear npm cache
echo "📦 Clearing npm cache..."
npm cache clean --force 2>/dev/null

# Drop OS caches (requires sudo)
echo "💧 Dropping OS caches..."
sync
echo 3 | sudo tee /proc/sys/vm/drop_caches > /dev/null 2>&1

# Wait for system to stabilize
sleep 2

# Check final memory state
echo ""
echo "📊 AFTER OPTIMIZATION:"
free -h

# Calculate improvement
BEFORE_FREE=$(free -m | awk 'NR==2{printf "%.0f", $7}')
AFTER_FREE=$(free -m | awk 'NR==2{printf "%.0f", $7}')

if [ $AFTER_FREE -gt $BEFORE_FREE ]; then
    IMPROVEMENT=$((AFTER_FREE - BEFORE_FREE))
    echo ""
    echo "✅ SUCCESS: Freed ${IMPROVEMENT}MB of memory!"
else
    echo ""
    echo "ℹ️  Memory state maintained."
fi

# Show top memory consumers
echo ""
echo "🔍 Top memory consumers:"
ps aux --sort=-%mem | head -5

echo ""
echo "✅ Memory optimization complete - $(date)"
echo "=========================================="
