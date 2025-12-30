#!/bin/bash
# Quick deploy script for correlation fix
# Run: bash deploy_correlation_fix.sh

set -e

echo "🚀 Deploying Correlation Interpolation Fix to Railway"
echo "=================================================="
echo ""

# Check if in correct directory
if [ ! -f "correlation_analysis_service.py" ]; then
    echo "❌ Error: Must run from /workspaces/business_ventures"
    exit 1
fi

# Check git status
echo "📋 Checking git status..."
git status

# Stage changes
echo ""
echo "📦 Staging changes..."
git add correlation_analysis_service.py
git add HEATMAP_CORRELATION_FIX.md 2>/dev/null || true
git add diagnose_correlation_issue.py 2>/dev/null || true

# Commit
echo ""
echo "💾 Committing changes..."
git commit -m "Fix: Add time-based interpolation for cross-frequency correlations

- Update minimum data points check from 3 to 20
- Add time-based interpolation to align different sampling frequencies
- Allow daily and monthly data to be properly correlated
- Expected to increase correlations from 6 to 100+"

# Push to GitHub
echo ""
echo "⬆️  Pushing to GitHub..."
git push origin main

echo ""
echo "✅ Deployment complete!"
echo ""
echo "Railway will automatically deploy from GitHub."
echo "Monitor at: https://railway.com/project/561cf2bc-95df-4ba3-9493-cf307dd274ee"
echo ""
echo "Next steps:"
echo "1. Wait for Railway deployment (2-3 minutes)"
echo "2. Trigger correlation recalculation via admin panel"
echo "3. Check dashboard for updated heatmap"
echo ""
echo "📖 See HEATMAP_CORRELATION_FIX.md for detailed instructions"
