#!/bin/bash

# Build Progress Monitor
# Checks build_fully_optimized.log every 5 minutes and displays progress

TOTAL_PHASES=43
LOG_FILE="build_fully_optimized.log"

echo "======================================================================="
echo "  CA-006 Build Progress Monitor"
echo "======================================================================="
echo "Total Phases: $TOTAL_PHASES"
echo "Checking every 5 minutes..."
echo ""

while true; do
    clear
    echo "======================================================================="
    echo "  CA-006 Build Progress Monitor - $(date '+%Y-%m-%d %H:%M:%S')"
    echo "======================================================================="
    echo ""
    
    if [ ! -f "$LOG_FILE" ]; then
        echo "⏳ Waiting for build to start..."
        echo "   Log file not found: $LOG_FILE"
        sleep 300
        continue
    fi
    
    # Count completed phases
    COMPLETED=$(grep -c "✅ phase_.*validated" "$LOG_FILE" 2>/dev/null || echo "0")
    IN_PROGRESS=$(grep -c "🤖 Generating code" "$LOG_FILE" 2>/dev/null || echo "0")
    ERRORS=$(grep -c "❌.*failed" "$LOG_FILE" 2>/dev/null || echo "0")
    
    # Remove any whitespace or newlines
    COMPLETED=$(echo "$COMPLETED" | tr -d '[:space:]')
    IN_PROGRESS=$(echo "$IN_PROGRESS" | tr -d '[:space:]')
    ERRORS=$(echo "$ERRORS" | tr -d '[:space:]')
    
    # Ensure numeric values
    COMPLETED=${COMPLETED:-0}
    IN_PROGRESS=${IN_PROGRESS:-0}
    ERRORS=${ERRORS:-0}
    
    # Calculate percentage
    PERCENT=$(awk "BEGIN {printf \"%.0f\", ($COMPLETED * 100 / $TOTAL_PHASES)}")
    
    # Create progress bar
    BAR_WIDTH=50
    FILLED=$(awk "BEGIN {printf \"%.0f\", ($PERCENT * $BAR_WIDTH / 100)}")
    EMPTY=$((BAR_WIDTH - FILLED))
    
    echo "📊 Overall Progress:"
    echo "   [$( printf '%*s' "$FILLED" | tr ' ' '█' )$( printf '%*s' "$EMPTY" | tr ' ' '░' )] ${PERCENT}%"
    echo ""
    echo "   ✅ Completed: $COMPLETED / $TOTAL_PHASES phases"
    echo "   🔄 In Progress: $IN_PROGRESS"
    echo "   ❌ Errors: $ERRORS"
    echo ""
    
    # Show last 5 phase completions
    echo "📝 Recent Activity:"
    grep "Phase:\|✅ phase_.*validated\|❌.*failed" "$LOG_FILE" | tail -10 | sed 's/^/   /' | sed 's/^[ \t]*/   /'
    echo ""
    
    # Check if build is complete
    if [ "$COMPLETED" -eq "$TOTAL_PHASES" ]; then
        echo "======================================================================="
        echo "  ✅ BUILD COMPLETE!"
        echo "======================================================================="
        echo ""
        
        # Count generated files
        if [ -d "src" ]; then
            FILE_COUNT=$(find src -type f -name "*.py" | wc -l)
            echo "   📁 Generated $FILE_COUNT Python files"
        fi
        
        break
    fi
    
    # Show estimated time remaining
    if [ "$COMPLETED" -gt 0 ]; then
        # Average ~30 seconds per phase
        REMAINING=$((TOTAL_PHASES - COMPLETED))
        EST_SECONDS=$((REMAINING * 30))
        EST_MINUTES=$((EST_SECONDS / 60))
        echo "⏱️  Estimated time remaining: ~$EST_MINUTES minutes"
        echo ""
    fi
    
    echo "Next update in 5 minutes... (Press Ctrl+C to stop monitoring)"
    echo ""
    
    # Wait 5 minutes (300 seconds)
    sleep 300
done
