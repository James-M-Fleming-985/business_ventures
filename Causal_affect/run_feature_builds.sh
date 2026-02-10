#!/usr/bin/env bash
# ================================================
# FEATURE BUILD RUNNER
# ================================================
# Builds Causal Affect features using AI Code Generator
# Run this and let it work - no babysitting required!
#
# USAGE:
#   ./run_feature_builds.sh              # Build all features
#   ./run_feature_builds.sh 06           # Build just FEATURE-CA-002-06
#   ./run_feature_builds.sh 06 08        # Build specific features

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CONTROL_TOWER="/workspaces/control_tower"
BUILD_SCRIPT="$CONTROL_TOWER/build_feature.py"
LOG_DIR="$SCRIPT_DIR/build_logs"
SYSTEM_DIR="$SCRIPT_DIR/SYSTEM-CA-002_correlation_analysis"

# Colors
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

mkdir -p "$LOG_DIR"

log() {
    echo -e "${GREEN}[$(date '+%H:%M:%S')]${NC} $1"
}

error() {
    echo -e "${RED}[$(date '+%H:%M:%S')] ERROR:${NC} $1"
}

warn() {
    echo -e "${YELLOW}[$(date '+%H:%M:%S')] WARNING:${NC} $1"
}

# Check prerequisites
if [ ! -f "$BUILD_SCRIPT" ]; then
    error "build_feature.py not found at $BUILD_SCRIPT"
    exit 1
fi

if [ -z "$ANTHROPIC_API_KEY" ]; then
    error "ANTHROPIC_API_KEY not set"
    echo "Run: export ANTHROPIC_API_KEY='your-key'"
    exit 1
fi

# Determine which features to build
if [ $# -eq 0 ]; then
    # Build all features in order
    FEATURE_NUMS=("06" "08" "09" "10")
else
    FEATURE_NUMS=("$@")
fi

echo ""
echo "================================================"
echo "  🚀 CAUSAL AFFECT - FEATURE BUILD RUNNER"
echo "================================================"
echo "  Features to build: ${FEATURE_NUMS[*]}"
echo "  Log directory: $LOG_DIR"
echo "  Started at: $(date)"
echo "================================================"
echo ""

# Summary tracking
TOTAL=0
SUCCESS=0
FAILED=0

for NUM in "${FEATURE_NUMS[@]}"; do
    FEATURE="FEATURE-CA-002-$NUM"
    ((TOTAL++))
    
    # Find the YAML file
    YAML_PATTERN="$SYSTEM_DIR/${FEATURE}_*/${FEATURE}*.yaml"
    YAML_PATH=$(find "$SYSTEM_DIR" -path "$YAML_PATTERN" -type f 2>/dev/null | head -1)
    
    if [ -z "$YAML_PATH" ]; then
        error "YAML not found for $FEATURE"
        ((FAILED++))
        continue
    fi
    
    LOG_FILE="$LOG_DIR/${FEATURE}_$(date '+%Y%m%d_%H%M%S').log"
    
    echo ""
    log "Building $FEATURE..."
    log "YAML: $(basename "$YAML_PATH")"
    log "Log: $LOG_FILE"
    
    # Run the build
    if python "$BUILD_SCRIPT" "$YAML_PATH" 2>&1 | tee "$LOG_FILE"; then
        log "✅ $FEATURE complete!"
        ((SUCCESS++))
        
        # Commit changes
        log "Committing changes..."
        cd "$SCRIPT_DIR"
        git add -A
        git commit -m "AI-generated: $FEATURE implementation" || true
    else
        error "❌ $FEATURE failed! Check log: $LOG_FILE"
        ((FAILED++))
    fi
    
    echo ""
    echo "----------------------------------------"
done

# Final summary
echo ""
echo "================================================"
echo "  📊 BUILD SUMMARY"
echo "================================================"
echo "  Total:   $TOTAL features"
echo "  Success: $SUCCESS ✅"
echo "  Failed:  $FAILED ❌"
echo "  Ended:   $(date)"
echo "================================================"

if [ $FAILED -eq 0 ]; then
    log "All builds complete! Pushing to GitHub..."
    cd "$SCRIPT_DIR"
    git push origin main
    log "✅ Pushed to main - Railway will auto-deploy"
else
    warn "Some builds failed. Review logs before pushing."
fi
