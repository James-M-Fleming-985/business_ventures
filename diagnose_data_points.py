#!/usr/bin/env python3
"""
Diagnose data point counts for all variables in the database
"""
from database import get_db_session
from models import VariableMetadata, TimeSeriesData
from sqlalchemy import func

print("=" * 80)
print("VARIABLE DATA POINT ANALYSIS")
print("=" * 80)

with get_db_session() as session:
    # Query to count data points per variable
    variable_counts = session.query(
        VariableMetadata.id,
        VariableMetadata.name,
        VariableMetadata.source,
        func.count(TimeSeriesData.id).label('data_points')
    ).outerjoin(
        TimeSeriesData, VariableMetadata.id == TimeSeriesData.variable_id
    ).group_by(
        VariableMetadata.id, VariableMetadata.name, VariableMetadata.source
    ).order_by(
        func.count(TimeSeriesData.id)
    ).all()
    
    print(f"\nTotal variables: {len(variable_counts)}\n")
    
    # Show variables with low data points
    print("VARIABLES WITH LOW DATA POINTS (<10):")
    print("-" * 80)
    print(f"{'Variable Name':<40} {'Source':<20} {'Data Points':>10}")
    print("-" * 80)
    
    low_data_count = 0
    for var_id, name, source, count in variable_counts:
        if count < 10:
            print(f"{name:<40} {source:<20} {count:>10}")
            low_data_count += 1
    
    print(f"\nTotal variables with <10 data points: {low_data_count}")
    
    # Show distribution
    print("\n" + "=" * 80)
    print("DATA POINT DISTRIBUTION:")
    print("-" * 80)
    
    distribution = {}
    for _, _, _, count in variable_counts:
        bucket = f"{count:3d}"
        distribution[bucket] = distribution.get(bucket, 0) + 1
    
    for bucket in sorted(distribution.keys(), key=lambda x: int(x)):
        print(f"n={bucket}: {distribution[bucket]:3d} variables")
    
    # Show variables with good data (60+)
    print("\n" + "=" * 80)
    print("VARIABLES WITH SUFFICIENT DATA (60+ points):")
    print("-" * 80)
    print(f"{'Variable Name':<40} {'Source':<20} {'Data Points':>10}")
    print("-" * 80)
    
    good_data_count = 0
    for var_id, name, source, count in variable_counts:
        if count >= 60:
            print(f"{name:<40} {source:<20} {count:>10}")
            good_data_count += 1
    
    print(f"\nTotal variables with 60+ data points: {good_data_count}")
