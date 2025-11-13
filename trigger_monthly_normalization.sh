#!/bin/bash
# Script to trigger data reingest and correlation calculation with monthly normalization

echo "================================================"
echo "Monthly Data Normalization Pipeline"
echo "================================================"
echo ""

BASE_URL="https://business-ventures-production.up.railway.app"

# Function to check if Railway is deployed
check_deployment() {
    echo "Checking deployment status..."
    response=$(curl -s "$BASE_URL/health")
    
    if echo "$response" | grep -q '"version"'; then
        version=$(echo "$response" | python3 -c "import sys, json; print(json.load(sys.stdin).get('version', 'unknown'))")
        echo "✅ Deployment active: v$version"
        return 0
    else
        echo "⏳ Deployment not ready yet..."
        return 1
    fi
}

# Wait for deployment
echo "Step 1: Waiting for Railway deployment..."
attempts=0
max_attempts=10

while [ $attempts -lt $max_attempts ]; do
    if check_deployment; then
        break
    fi
    attempts=$((attempts + 1))
    echo "   Attempt $attempts/$max_attempts - waiting 30 seconds..."
    sleep 30
done

if [ $attempts -eq $max_attempts ]; then
    echo "❌ Deployment check timed out after $((max_attempts * 30)) seconds"
    exit 1
fi

echo ""
echo "================================================"
echo "Step 2: Trigger Data Ingestion (Monthly)"
echo "================================================"
echo ""
echo "This will fetch and normalize data to monthly frequency:"
echo "  - Stocks: 60 months of end-of-month prices"
echo "  - GDP: Forward-filled to monthly (2015-2023)"
echo "  - Earthquakes: Monthly aggregated counts"
echo "  - Environmental: Monthly event counts"
echo "  - arXiv: Monthly publication counts"
echo "  - Clinical Trials: Monthly snapshots"
echo ""
echo "Triggering data ingestion..."
echo ""

response=$(curl -s -X POST "$BASE_URL/api/admin/fetch-data" \
    -H "Content-Type: application/json" \
    -w "\n%{http_code}")

http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" = "200" ]; then
    echo "✅ Data ingestion successful!"
    echo ""
    echo "$body" | python3 -m json.tool
    
    # Extract stats
    total_vars=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('stats', {}).get('total_variables', 0))")
    data_points=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('stats', {}).get('data_points_stored', 0))")
    
    echo ""
    echo "📊 Summary:"
    echo "   Total Variables: $total_vars"
    echo "   Data Points Stored: $data_points"
else
    echo "❌ Data ingestion failed (HTTP $http_code)"
    echo "$body"
    exit 1
fi

echo ""
echo "================================================"
echo "Step 3: Calculate Correlations"
echo "================================================"
echo ""
echo "This will calculate correlations with monthly-aligned timestamps."
echo "Expected: 1,000+ cross-domain correlations (vs. previous 0)"
echo ""
echo "Triggering correlation calculation..."
echo ""

response=$(curl -s -X POST "$BASE_URL/api/admin/calculate-correlations" \
    -H "Content-Type: application/json" \
    -w "\n%{http_code}")

http_code=$(echo "$response" | tail -n 1)
body=$(echo "$response" | head -n -1)

if [ "$http_code" = "200" ]; then
    echo "✅ Correlation calculation successful!"
    echo ""
    echo "$body" | python3 -m json.tool
    
    # Extract correlation count
    total_corr=$(echo "$body" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('stats', {}).get('total_correlations', 0))" 2>/dev/null || echo "unknown")
    
    echo ""
    echo "📊 Summary:"
    echo "   Total Correlations: $total_corr"
else
    echo "❌ Correlation calculation failed (HTTP $http_code)"
    echo "$body"
    exit 1
fi

echo ""
echo "================================================"
echo "Step 4: Verify Cross-Domain Correlations"
echo "================================================"
echo ""
echo "Checking heatmap for cross-domain correlations..."
echo ""

response=$(curl -s "$BASE_URL/api/dashboard/correlation-heatmap?cross_domain=true&top_n=12")

labels_count=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(len(data.get('labels', [])))")
corr_count=$(echo "$response" | python3 -c "import sys, json; data=json.load(sys.stdin); print(data.get('correlation_count', 0))")

if [ "$labels_count" -gt 0 ]; then
    echo "✅ Cross-domain correlations found!"
    echo ""
    echo "   Heatmap Labels: $labels_count"
    echo "   Correlations: $corr_count"
    echo ""
    echo "First 5 variable pairs:"
    echo "$response" | python3 -c "
import sys, json
data = json.load(sys.stdin)
labels = data.get('labels', [])
for i, label in enumerate(labels[:5], 1):
    print(f'   {i}. {label}')
"
else
    echo "❌ No cross-domain correlations found"
    echo "   This may indicate data ingestion needs more time or API rate limits"
fi

echo ""
echo "================================================"
echo "Pipeline Complete!"
echo "================================================"
echo ""
echo "Next steps:"
echo "  1. Check frontend heatmap display"
echo "  2. Verify tiles are clickable"
echo "  3. Test scatter plot modals"
echo ""
