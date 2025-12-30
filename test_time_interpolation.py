#!/usr/bin/env python3
"""
Test script to verify time-based interpolation fix
Shows before/after alignment for sample variable pairs
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta

def demo_alignment_issue():
    """Demonstrate the alignment problem and solution"""
    
    print("=" * 80)
    print("TIME SERIES ALIGNMENT DEMO")
    print("=" * 80)
    
    # Create sample data with different frequencies
    print("\n1. CREATING SAMPLE DATA")
    print("-" * 80)
    
    # Daily stock prices (business days only)
    daily_dates = pd.date_range('2024-01-01', '2024-03-31', freq='B')  # Business days
    stock_prices = pd.Series(
        100 + np.cumsum(np.random.randn(len(daily_dates))),
        index=daily_dates,
        name='Stock Price (Daily)'
    )
    print(f"\nDaily Stock Prices: {len(stock_prices)} points")
    print(f"  First: {stock_prices.index[0].date()} = ${stock_prices.iloc[0]:.2f}")
    print(f"  Last:  {stock_prices.index[-1].date()} = ${stock_prices.iloc[-1]:.2f}")
    
    # Monthly GDP (1st of each month)
    monthly_dates = pd.date_range('2024-01-01', '2024-03-01', freq='MS')
    gdp_values = pd.Series(
        [20.5, 20.7, 20.9],
        index=monthly_dates,
        name='GDP (Monthly, $T)'
    )
    print(f"\nMonthly GDP: {len(gdp_values)} points")
    print(f"  First: {gdp_values.index[0].date()} = ${gdp_values.iloc[0]:.1f}T")
    print(f"  Last:  {gdp_values.index[-1].date()} = ${gdp_values.iloc[-1]:.1f}T")
    
    # OLD METHOD: Naive merge (only exact matches)
    print("\n\n2. OLD METHOD (Exact Timestamp Matching)")
    print("-" * 80)
    
    old_aligned = pd.DataFrame({
        'stock': stock_prices,
        'gdp': gdp_values
    })
    old_aligned_clean = old_aligned.dropna()
    
    print(f"\nResult after dropna():")
    print(f"  Aligned points: {len(old_aligned_clean)}")
    print(f"  Status: {'✅ Enough for correlation' if len(old_aligned_clean) >= 20 else '❌ Too few points'}")
    
    if len(old_aligned_clean) > 0:
        print(f"\n  Aligned data:")
        print(old_aligned_clean)
    else:
        print(f"\n  ❌ No overlapping timestamps! Cannot correlate.")
    
    # NEW METHOD: Time-based interpolation
    print("\n\n3. NEW METHOD (Time-Based Interpolation)")
    print("-" * 80)
    
    new_aligned = pd.DataFrame({
        'stock': stock_prices,
        'gdp': gdp_values
    })
    new_aligned = new_aligned.sort_index()
    new_aligned = new_aligned.interpolate(method='time', limit_direction='both')
    new_aligned_clean = new_aligned.dropna()
    
    print(f"\nResult after interpolation + dropna():")
    print(f"  Aligned points: {len(new_aligned_clean)}")
    print(f"  Status: {'✅ Enough for correlation' if len(new_aligned_clean) >= 20 else '❌ Too few points'}")
    
    print(f"\n  Sample of aligned data (first 10 rows):")
    print(new_aligned_clean.head(10).to_string())
    
    # Calculate correlation
    if len(new_aligned_clean) >= 3:
        from scipy import stats
        r, p = stats.pearsonr(new_aligned_clean['stock'], new_aligned_clean['gdp'])
        print(f"\n  Correlation: r = {r:.3f}, p = {p:.4f}")
        print(f"  Significance: {'✅ Significant' if p < 0.05 else '⚠️  Not significant'}")
    
    # Summary
    print("\n\n4. SUMMARY")
    print("-" * 80)
    print(f"  Old method: {len(old_aligned_clean)} aligned points")
    print(f"  New method: {len(new_aligned_clean)} aligned points")
    print(f"  Improvement: +{len(new_aligned_clean) - len(old_aligned_clean)} points")
    print(f"\n  Impact: {(len(new_aligned_clean) / max(len(old_aligned_clean), 1)):.1f}x more data for correlation")
    
    print("\n" + "=" * 80)
    print("CONCLUSION: Time-based interpolation enables cross-frequency correlation!")
    print("=" * 80)


if __name__ == "__main__":
    demo_alignment_issue()
