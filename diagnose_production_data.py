#!/usr/bin/env python3
"""
Query production API to diagnose data point counts
"""
import requests
import json
from collections import defaultdict

BASE_URL = "https://businessventures-production.up.railway.app"

print("=" * 80)
print("PRODUCTION API DATA ANALYSIS")
print("=" * 80)

# Get heatmap data with all correlations (no filtering)
print("\nFetching correlations from production API...")
response = requests.get(f"{BASE_URL}/api/dashboard/heatmap?top_n=50&min_strength=0.0&cross_domain=false")

if response.status_code != 200:
    print(f"Error: {response.status_code}")
    print(response.text)
    exit(1)

data = response.json()
labels = data.get('labels', [])
metadata = data.get('metadata', [])

print(f"Found {len(labels)} variables in correlation matrix\n")

# Analyze sample sizes for each variable
variable_sample_sizes = {}
for i in range(len(labels)):
    var_name = labels[i]
    samples = []
    
    for j in range(len(labels)):
        if i != j and metadata[i][j] and 'sample_size' in metadata[i][j]:
            samples.append(metadata[i][j]['sample_size'])
    
    if samples:
        variable_sample_sizes[var_name] = {
            'min': min(samples),
            'max': max(samples),
            'avg': sum(samples) / len(samples),
            'count': len(samples)
        }

# Print variables sorted by minimum sample size
print("VARIABLES RANKED BY MINIMUM SAMPLE SIZE:")
print("-" * 80)
print(f"{'Variable Name':<45} {'Min':>5} {'Max':>5} {'Avg':>6} {'Pairs':>5}")
print("-" * 80)

sorted_vars = sorted(variable_sample_sizes.items(), key=lambda x: x[1]['min'])

for var_name, stats in sorted_vars[:30]:  # Show worst 30
    print(f"{var_name:<45} {stats['min']:>5} {stats['max']:>5} {stats['avg']:>6.1f} {stats['count']:>5}")

# Count variables by sample size bucket
print("\n" + "=" * 80)
print("SAMPLE SIZE DISTRIBUTION:")
print("-" * 80)

buckets = defaultdict(int)
for var_name, stats in variable_sample_sizes.items():
    min_samples = stats['min']
    if min_samples < 5:
        bucket = "0-4"
    elif min_samples < 10:
        bucket = "5-9"
    elif min_samples < 20:
        bucket = "10-19"
    elif min_samples < 30:
        bucket = "20-29"
    elif min_samples < 50:
        bucket = "30-49"
    else:
        bucket = "50+"
    buckets[bucket] += 1

for bucket in ["0-4", "5-9", "10-19", "20-29", "30-49", "50+"]:
    count = buckets.get(bucket, 0)
    print(f"{bucket:>8} data points: {count:>3} variables")

print("\n" + "=" * 80)
print("CRITICAL ISSUES:")
print("-" * 80)

critical_vars = [var for var, stats in variable_sample_sizes.items() if stats['min'] < 10]
print(f"Variables with <10 data points: {len(critical_vars)}")
print("These variables have insufficient data for reliable correlation analysis.")
print("\nRecommendation: Re-fetch data for these variables with 60 months of history.")
