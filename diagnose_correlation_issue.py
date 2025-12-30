"""
Diagnostic script to understand why only 6 correlations exist
"""

import os
os.environ.setdefault('DATABASE_URL', 'postgresql://localhost:5432/causal_affect_dev')

from database import get_db_session
from models import VariableMetadata, TimeSeriesData, CorrelationResult
from sqlalchemy import func
import pandas as pd
from datetime import datetime

print("=" * 80)
print("CORRELATION ISSUE DIAGNOSTIC")
print("=" * 80)

with get_db_session() as session:
    # 1. Check total variables and data points
    print("\n1. OVERALL STATISTICS:")
    total_vars = session.query(VariableMetadata).filter(VariableMetadata.is_active == True).count()
    total_data_points = session.query(TimeSeriesData).count()
    total_correlations = session.query(CorrelationResult).count()
    
    print(f"   Active Variables: {total_vars}")
    print(f"   Total Data Points: {total_data_points}")
    print(f"   Stored Correlations: {total_correlations}")
    
    # 2. Data points per variable
    print("\n2. DATA POINTS PER VARIABLE:")
    var_data = session.query(
        VariableMetadata.id,
        VariableMetadata.display_name,
        VariableMetadata.source,
        func.count(TimeSeriesData.id).label('count')
    ).outerjoin(
        TimeSeriesData, 
        TimeSeriesData.variable_id == VariableMetadata.id
    ).filter(
        VariableMetadata.is_active == True
    ).group_by(
        VariableMetadata.id,
        VariableMetadata.display_name,
        VariableMetadata.source
    ).order_by(
        func.count(TimeSeriesData.id).desc()
    ).all()
    
    vars_with_enough_data = 0
    vars_with_some_data = 0
    vars_with_no_data = 0
    
    print(f"\n   {'ID':<5} {'Name':<50} {'Source':<15} {'Points':<10}")
    print("   " + "-" * 90)
    for var_id, name, source, count in var_data:
        status = ""
        if count >= 20:
            vars_with_enough_data += 1
            status = "✓"
        elif count > 0:
            vars_with_some_data += 1
            status = "⚠"
        else:
            vars_with_no_data += 1
            status = "✗"
        
        print(f"   {status} {var_id:<3} {name[:47]:<50} {source:<15} {count:<10}")
    
    print(f"\n   Summary:")
    print(f"   - Variables with ≥20 points (enough for correlation): {vars_with_enough_data}")
    print(f"   - Variables with 1-19 points (insufficient): {vars_with_some_data}")
    print(f"   - Variables with 0 points (no data): {vars_with_no_data}")
    
    # 3. Check date ranges for variables with data
    print("\n3. DATE RANGE ANALYSIS:")
    print("   Checking if variables have overlapping time periods...")
    
    date_ranges = {}
    for var_id, name, source, count in var_data:
        if count > 0:
            dates = session.query(
                func.min(TimeSeriesData.timestamp),
                func.max(TimeSeriesData.timestamp)
            ).filter(
                TimeSeriesData.variable_id == var_id
            ).first()
            
            date_ranges[var_id] = {
                'name': name,
                'source': source,
                'count': count,
                'start': dates[0],
                'end': dates[1]
            }
    
    # Find overlapping periods
    print(f"\n   {'Variable':<50} {'Source':<15} {'Start':<12} {'End':<12} {'Days':<8}")
    print("   " + "-" * 110)
    
    for var_id, info in sorted(date_ranges.items(), key=lambda x: x[1]['start'] or datetime.min):
        if info['start'] and info['end']:
            days = (info['end'] - info['start']).days
            print(f"   {info['name'][:47]:<50} {info['source']:<15} {info['start'].date()} {info['end'].date()} {days:<8}")
    
    # 4. Check existing correlations
    print("\n4. EXISTING CORRELATIONS:")
    correlations = session.query(CorrelationResult).order_by(
        CorrelationResult.abs_correlation.desc()
    ).all()
    
    if correlations:
        print(f"\n   {'Var1':<25} {'Var2':<25} {'r':<8} {'p':<10} {'n':<6}")
        print("   " + "-" * 90)
        for corr in correlations:
            v1_name = corr.variable1.display_name[:22] if corr.variable1 else f"ID {corr.variable1_id}"
            v2_name = corr.variable2.display_name[:22] if corr.variable2 else f"ID {corr.variable2_id}"
            print(f"   {v1_name:<25} {v2_name:<25} {corr.correlation_value:>7.3f} {corr.p_value:>9.4f} {corr.sample_size:>6}")
    else:
        print("   No correlations found in database.")
    
    # 5. Check potential correlations with current data
    print("\n5. POTENTIAL CORRELATION PAIRS:")
    vars_with_data = [(var_id, info) for var_id, info in date_ranges.items() if info['count'] >= 20]
    
    print(f"   {len(vars_with_data)} variables have ≥20 data points")
    print(f"   Potential pairs: {len(vars_with_data) * (len(vars_with_data) - 1) // 2}")
    
    if len(vars_with_data) >= 2:
        print("\n   Checking a sample pair for data alignment...")
        var1_id = vars_with_data[0][0]
        var2_id = vars_with_data[1][0]
        
        var1_data = session.query(TimeSeriesData).filter(
            TimeSeriesData.variable_id == var1_id
        ).order_by(TimeSeriesData.timestamp).all()
        
        var2_data = session.query(TimeSeriesData).filter(
            TimeSeriesData.variable_id == var2_id
        ).order_by(TimeSeriesData.timestamp).all()
        
        df1 = pd.DataFrame([{'timestamp': dp.timestamp, 'value': dp.value} for dp in var1_data])
        df2 = pd.DataFrame([{'timestamp': dp.timestamp, 'value': dp.value} for dp in var2_data])
        
        df1.set_index('timestamp', inplace=True)
        df2.set_index('timestamp', inplace=True)
        
        merged = pd.merge(df1, df2, left_index=True, right_index=True, how='inner')
        
        print(f"\n   Sample Pair: {vars_with_data[0][1]['name']} ↔ {vars_with_data[1][1]['name']}")
        print(f"   Var 1 points: {len(df1)}")
        print(f"   Var 2 points: {len(df2)}")
        print(f"   Aligned points (same timestamps): {len(merged)}")
        print(f"   Status: {'✓ Can correlate' if len(merged) >= 20 else '✗ Insufficient overlap'}")

print("\n" + "=" * 80)
print("DIAGNOSTIC COMPLETE")
print("=" * 80)
