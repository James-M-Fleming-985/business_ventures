"""
Data Quality Diagnostic for Causal Affect Platform
Analyzes the health of the data universe and identifies issues
"""

from database import get_db_session
from models import VariableMetadata, TimeSeriesData, CorrelationResult
from sqlalchemy import func, and_
from datetime import datetime, timedelta
import pandas as pd
from collections import defaultdict
import json


def analyze_data_quality():
    """Comprehensive data quality analysis"""
    print("=" * 80)
    print("CAUSAL AFFECT PLATFORM - DATA QUALITY DIAGNOSTIC")
    print("=" * 80)
    print()
    
    with get_db_session() as session:
        # 1. VARIABLE INVENTORY
        print("📊 VARIABLE INVENTORY")
        print("-" * 80)
        variables = session.query(VariableMetadata).filter(
            VariableMetadata.is_active.is_(True)
        ).all()
        
        print(f"Total Active Variables: {len(variables)}")
        
        # Group by source
        source_counts = defaultdict(int)
        for v in variables:
            source_counts[v.source] += 1
        
        print("\nVariables by Source:")
        for source, count in sorted(source_counts.items()):
            print(f"  • {source:20s}: {count:3d} variables")
        
        print()
        
        # 2. TIME SERIES DATA COVERAGE
        print("📅 TIME SERIES DATA COVERAGE")
        print("-" * 80)
        
        total_data_points = session.query(TimeSeriesData).count()
        print(f"Total Data Points: {total_data_points:,}")
        print()
        
        # Analyze each variable's data
        print("Per-Variable Analysis:")
        print(f"{'Variable':<40} {'Source':<15} {'Points':>6} {'Start':>12} {'End':>12} {'Days':>5}")
        print("-" * 100)
        
        var_stats = []
        for var in variables:
            data_count = session.query(TimeSeriesData).filter(
                TimeSeriesData.variable_id == var.id
            ).count()
            
            if data_count == 0:
                print(f"{var.display_name:<40} {var.source:<15} {0:>6} {'NO DATA':>12} {'NO DATA':>12} {0:>5}")
                var_stats.append({
                    'name': var.display_name,
                    'source': var.source,
                    'points': 0,
                    'start': None,
                    'end': None,
                    'days': 0
                })
                continue
            
            # Get date range
            first = session.query(TimeSeriesData).filter(
                TimeSeriesData.variable_id == var.id
            ).order_by(TimeSeriesData.timestamp.asc()).first()
            
            last = session.query(TimeSeriesData).filter(
                TimeSeriesData.variable_id == var.id
            ).order_by(TimeSeriesData.timestamp.desc()).first()
            
            days_span = (last.timestamp - first.timestamp).days
            start_str = first.timestamp.strftime('%Y-%m-%d')
            end_str = last.timestamp.strftime('%Y-%m-%d')
            
            # Check if data is current (within last 30 days)
            days_old = (datetime.utcnow() - last.timestamp).days
            currency_flag = "⚠️" if days_old > 30 else "✅"
            
            print(f"{var.display_name:<40} {var.source:<15} {data_count:>6} {start_str:>12} {end_str:>12} {days_span:>5} {currency_flag}")
            
            var_stats.append({
                'name': var.display_name,
                'source': var.source,
                'points': data_count,
                'start': first.timestamp,
                'end': last.timestamp,
                'days': days_span,
                'days_old': days_old
            })
        
        print()
        
        # 3. DATA CURRENCY CHECK
        print("⏰ DATA CURRENCY CHECK")
        print("-" * 80)
        
        current_data = [v for v in var_stats if v['end'] and v['days_old'] <= 30]
        stale_data = [v for v in var_stats if v['end'] and v['days_old'] > 30]
        no_data = [v for v in var_stats if v['points'] == 0]
        
        print(f"Current (< 30 days old): {len(current_data)} variables")
        print(f"Stale (> 30 days old):   {len(stale_data)} variables")
        print(f"No Data:                 {len(no_data)} variables")
        print()
        
        if stale_data:
            print("⚠️  STALE DATA SOURCES:")
            for v in stale_data[:10]:  # Show first 10
                print(f"  • {v['name']:<40} Last: {v['end'].strftime('%Y-%m-%d')} ({v['days_old']} days old)")
            if len(stale_data) > 10:
                print(f"  ... and {len(stale_data) - 10} more")
        print()
        
        # 4. TIME SERIES OVERLAP ANALYSIS
        print("🔗 TIME SERIES OVERLAP ANALYSIS")
        print("-" * 80)
        print("Checking which variable pairs have enough overlapping data for correlation...")
        print()
        
        # Get all timestamps for each variable
        var_timestamps = {}
        for var in variables:
            timestamps = session.query(TimeSeriesData.timestamp).filter(
                TimeSeriesData.variable_id == var.id
            ).all()
            var_timestamps[var.id] = set(t[0] for t in timestamps)
        
        # Calculate overlap matrix
        overlap_counts = []
        total_pairs = 0
        pairs_with_20plus = 0
        pairs_with_10to19 = 0
        pairs_with_3to9 = 0
        pairs_with_lt3 = 0
        
        for i, var1 in enumerate(variables):
            for var2 in variables[i+1:]:
                total_pairs += 1
                
                if var1.id not in var_timestamps or var2.id not in var_timestamps:
                    pairs_with_lt3 += 1
                    continue
                
                overlap = len(var_timestamps[var1.id] & var_timestamps[var2.id])
                
                if overlap >= 20:
                    pairs_with_20plus += 1
                    overlap_counts.append((var1.display_name, var2.display_name, overlap))
                elif overlap >= 10:
                    pairs_with_10to19 += 1
                elif overlap >= 3:
                    pairs_with_3to9 += 1
                else:
                    pairs_with_lt3 += 1
        
        print(f"Total Variable Pairs: {total_pairs:,}")
        print()
        print(f"Pairs with ≥20 overlapping timestamps: {pairs_with_20plus:>6} ({pairs_with_20plus/total_pairs*100:5.1f}%) ✅ RELIABLE")
        print(f"Pairs with 10-19 overlapping:          {pairs_with_10to19:>6} ({pairs_with_10to19/total_pairs*100:5.1f}%) ⚠️  MARGINAL")
        print(f"Pairs with 3-9 overlapping:            {pairs_with_3to9:>6} ({pairs_with_3to9/total_pairs*100:5.1f}%) ❌ UNRELIABLE")
        print(f"Pairs with <3 overlapping:             {pairs_with_lt3:>6} ({pairs_with_lt3/total_pairs*100:5.1f}%) ❌ IMPOSSIBLE")
        print()
        
        if pairs_with_20plus > 0:
            print(f"Top 20 Variable Pairs with Most Overlap:")
            for var1_name, var2_name, overlap in sorted(overlap_counts, key=lambda x: x[2], reverse=True)[:20]:
                print(f"  • {var1_name:<30} ↔ {var2_name:<30} {overlap:>4} points")
        print()
        
        # 5. CORRELATION QUALITY CHECK
        print("🔬 CORRELATION QUALITY CHECK")
        print("-" * 80)
        
        total_corrs = session.query(CorrelationResult).count()
        print(f"Total Stored Correlations: {total_corrs:,}")
        
        if total_corrs > 0:
            # Sample size distribution
            sample_size_bins = [
                (0, 2, "0-2 points (INVALID)"),
                (3, 9, "3-9 points (UNRELIABLE)"),
                (10, 19, "10-19 points (MARGINAL)"),
                (20, 49, "20-49 points (RELIABLE)"),
                (50, 999999, "50+ points (EXCELLENT)")
            ]
            
            print("\nCorrelation Sample Size Distribution:")
            for min_size, max_size, label in sample_size_bins:
                count = session.query(CorrelationResult).filter(
                    and_(
                        CorrelationResult.sample_size >= min_size,
                        CorrelationResult.sample_size <= max_size
                    )
                ).count()
                pct = count / total_corrs * 100 if total_corrs > 0 else 0
                print(f"  {label:<30}: {count:>6} ({pct:5.1f}%)")
            
            # Show suspicious correlations (near-perfect with small sample)
            print("\n⚠️  SUSPICIOUS CORRELATIONS (|r| > 0.95 with n < 20):")
            suspicious = session.query(CorrelationResult).filter(
                and_(
                    CorrelationResult.abs_correlation > 0.95,
                    CorrelationResult.sample_size < 20
                )
            ).limit(10).all()
            
            if suspicious:
                for corr in suspicious:
                    print(f"  • {corr.variable1.display_name:<30} ↔ {corr.variable2.display_name:<30}")
                    print(f"    r = {corr.correlation_value:7.4f}, n = {corr.sample_size:3d} ❌ UNRELIABLE")
            else:
                print("  None found ✅")
        
        print()
        
        # 6. RECOMMENDATIONS
        print("💡 RECOMMENDATIONS")
        print("-" * 80)
        
        recommendations = []
        
        if no_data:
            recommendations.append(
                f"⚠️  {len(no_data)} variables have NO DATA - check data fetchers"
            )
        
        if stale_data:
            recommendations.append(
                f"⚠️  {len(stale_data)} variables have STALE DATA (>30 days old) - refresh needed"
            )
        
        if pairs_with_20plus < total_pairs * 0.1:
            recommendations.append(
                f"❌ Only {pairs_with_20plus/total_pairs*100:.1f}% of pairs have sufficient overlap - need more frequent data collection or longer history"
            )
        
        if total_corrs > 0:
            low_sample_corrs = session.query(CorrelationResult).filter(
                CorrelationResult.sample_size < 20
            ).count()
            if low_sample_corrs > 0:
                recommendations.append(
                    f"❌ {low_sample_corrs} correlations have <20 data points - recalculate with higher threshold"
                )
        
        if not recommendations:
            recommendations.append("✅ Data quality looks good!")
        
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
        
        print()
        print("=" * 80)
        print("DIAGNOSTIC COMPLETE")
        print("=" * 80)
        
        # Return summary for programmatic use
        return {
            'total_variables': len(variables),
            'variables_with_data': len([v for v in var_stats if v['points'] > 0]),
            'current_variables': len(current_data),
            'stale_variables': len(stale_data),
            'no_data_variables': len(no_data),
            'total_pairs': total_pairs,
            'reliable_pairs': pairs_with_20plus,
            'total_correlations': total_corrs,
            'recommendations': recommendations
        }


if __name__ == "__main__":
    summary = analyze_data_quality()
    
    # Save summary to JSON
    with open('data_quality_summary.json', 'w') as f:
        json.dump(summary, f, indent=2)
    print("\n📄 Summary saved to data_quality_summary.json")
