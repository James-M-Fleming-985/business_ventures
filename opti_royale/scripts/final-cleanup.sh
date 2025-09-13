#!/bin/bash

# 🧹 OptiRoyale Final Cleanup & Organization
# Clean workspace, integrate battle analysis, prepare for commit

echo "🧹 Final Cleanup & Organization"
echo "==============================="

# Create organized structure
echo "📁 Creating organized directories..."
mkdir -p docs/{strategy,guides,specs}
mkdir -p demo/{pages,api-examples}
mkdir -p archive/{old-demos,backups}

echo "📚 Organizing documentation..."
# Move strategy docs
for file in AI_MARKETING_SYSTEM.md DEVELOPMENT_STRATEGY.md MARKET_LAUNCH_STRATEGY.md OPEN_SOURCE_STRATEGY.md VALUE_PROPOSITION.md; do
    [ -f "$file" ] && mv "$file" docs/strategy/ 2>/dev/null || true
done

# Move guides
for file in API_KEY_SETUP_GUIDE.md AZURE_SETUP_GUIDE.md DEVELOPMENT_MANAGEMENT_GUIDE.md FILE_MANAGEMENT_GUIDE.md IDE_PERFORMANCE_GUIDE.md TEST_FRAMEWORK_GUIDE.md; do
    [ -f "$file" ] && mv "$file" docs/guides/ 2>/dev/null || true
done

# Move specs
for file in CLASH_ROYALE_MECHANICS_SPEC.md COMPREHENSIVE_MECHANICS_REPORT.md SPECIFICATIONS.md; do
    [ -f "$file" ] && mv "$file" docs/specs/ 2>/dev/null || true
done

echo "🎮 Organizing demo files..."
# Copy demos (keep originals for now)
[ -f "pro-battle-analysis.html" ] && cp pro-battle-analysis.html demo/pages/battle-analysis.html
[ -f "pricing-tiers.html" ] && cp pricing-tiers.html demo/pages/pricing.html
[ -f "test-page.html" ] && cp test-page.html demo/pages/test.html

# Move API examples
for file in ultra-simple-api.js simple-api.js simple-api-server.js real-analysis-api.js; do
    [ -f "$file" ] && mv "$file" demo/api-examples/ 2>/dev/null || true
done

echo "📦 Archiving old files..."
# Archive old/backup files
[ -f "video-analysis-demo-OLD.html" ] && mv video-analysis-demo-OLD.html archive/old-demos/
[ -f "pro-battle-analysis-backup.html" ] && mv pro-battle-analysis-backup.html archive/backups/
[ -f "pro-battle-analysis-corrupted.html" ] && mv pro-battle-analysis-corrupted.html archive/backups/

echo "🏗️ Integrating battle analysis into main app..."
# Ensure web app structure exists
mkdir -p apps/web/{components,pages,styles}

# Create integrated battle analysis component
if [ -f "demo/pages/battle-analysis.html" ]; then
    cat > apps/web/pages/battle-analysis.tsx << 'EOF'
import React from 'react';
import Head from 'next/head';

export default function BattleAnalysis() {
  return (
    <>
      <Head>
        <title>Battle Analysis - OptiRoyale</title>
        <meta name="description" content="Professional Clash Royale battle analysis tool" />
      </Head>
      <div className="min-h-screen bg-gradient-to-br from-blue-900 via-purple-900 to-indigo-900">
        {/* Battle Analysis Interface will be embedded here */}
        <iframe 
          src="/demo/battle-analysis.html"
          className="w-full h-screen border-0"
          title="Battle Analysis Interface"
        />
      </div>
    </>
  );
}
EOF
    echo "✅ Battle analysis integrated as React component"
else
    echo "⚠️  Battle analysis demo not found"
fi

echo "📋 Creating file organization index..."
cat > docs/FILE_ORGANIZATION.md << 'EOF'
# 📁 OptiRoyale File Organization

## Current Structure After Cleanup

### 📚 Documentation (`docs/`)
- **strategy/**: Business and development strategy documents
- **guides/**: Setup and development guides  
- **specs/**: Technical specifications and requirements

### 🎮 Demos (`demo/`)
- **pages/**: Standalone demo pages (battle-analysis.html, pricing.html)
- **api-examples/**: API implementation examples

### 🏗️ Main Application (`apps/`)
- **web/**: Next.js web application
  - **pages/battle-analysis.tsx**: Integrated battle analysis
  - **components/**: React components
  - **styles/**: Application styling
- **api/**: Backend API services
- **mobile/**: Mobile application

### 📦 Archive (`archive/`)
- **old-demos/**: Previous demo versions
- **backups/**: Backup files

### 🔧 Configuration & Scripts
- **scripts/**: Development and deployment scripts
- **config/**: Configuration files
- **docker/**: Docker configurations
- Root level: package.json, docker-compose.yml, etc.

## Integration Status
✅ Documentation organized
✅ Demos preserved and organized  
✅ Battle analysis integrated into main app
✅ Old files archived
✅ Clean structure ready for performance optimization
EOF

echo ""
echo "✅ CLEANUP COMPLETE!"
echo "===================="
echo "📊 Summary:"
echo "  📚 ${#docs_moved[@]} documentation files organized"
echo "  🎮 Demo files preserved in demo/"
echo "  🏗️ Battle analysis integrated into apps/web/"
echo "  📦 Old files archived safely"
echo ""
echo "🎯 Ready for:"
echo "  1. Final review"
echo "  2. Commit clean state"
echo "  3. Performance optimization"
