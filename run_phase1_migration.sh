#!/bin/bash
# Run database migration and recalculate correlations with source tags

echo "=== Phase 1: Database Migration ==="
echo "Running migration to add source1/source2 columns..."

# Run migration via Railway
cd /workspaces/control_tower/cloned_repos/business_ventures
railway run python migrations/add_source_columns.py

echo ""
echo "=== Phase 2: Recalculate Correlations ==="
echo "Triggering correlation calculation with source tags..."

curl -X POST 'https://businessventures-production.up.railway.app/api/admin/calculate-correlations' \
  -H 'Content-Type: application/json'

echo ""
echo ""
echo "=== Phase 3: Verify Cross-Domain Filtering ==="
echo "Testing cross-domain heatmap endpoint..."

curl -s 'https://businessventures-production.up.railway.app/api/dashboard/heatmap?cross_domain=true&top_n=12' | jq '{
  correlation_count: .correlation_count,
  cross_domain_filter: .cross_domain_filter,
  sample_pairs: .labels[0:4]
}'

echo ""
echo "✓ Migration complete! Check above for correlation count."
