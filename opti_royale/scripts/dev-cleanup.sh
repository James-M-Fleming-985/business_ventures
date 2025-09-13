#!/bin/bash

# Development Environment Cleanup Script
# Standard practice for memory-constrained development environments

echo "🧹 Development Environment Cleanup"
echo "=================================="

# Kill TypeScript language servers (they restart automatically)
echo "Stopping TypeScript servers..."
pkill -f "tsserver.js" 2>/dev/null || true

# Clear Node.js caches
echo "Clearing Node.js caches..."
npm cache clean --force 2>/dev/null || true

# Clear build artifacts and caches
echo "Clearing build caches..."
find /workspaces/opti_royale -name "node_modules/.cache" -type d -exec rm -rf {} + 2>/dev/null || true
find /workspaces/opti_royale -name ".next" -type d -exec rm -rf {} + 2>/dev/null || true
find /workspaces/opti_royale -name ".turbo" -type d -exec rm -rf {} + 2>/dev/null || true
find /workspaces/opti_royale -name "dist" -type d -exec rm -rf {} + 2>/dev/null || true

# Clear temporary files
echo "Clearing temporary files..."
rm -rf /tmp/vscode-typescript* 2>/dev/null || true
rm -rf /tmp/turbo* 2>/dev/null || true

# Force garbage collection if Node processes exist
echo "Triggering garbage collection..."
pkill -USR1 node 2>/dev/null || true

# Memory status
echo ""
echo "📊 Memory Status After Cleanup:"
free -h | grep Mem

echo ""
echo "✅ Cleanup completed!"
echo "💡 Run this script when environment gets sluggish"
