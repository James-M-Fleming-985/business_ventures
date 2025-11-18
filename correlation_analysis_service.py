"""
Correlation Analysis Service
Calculates N×N correlation matrix for all variable pairs

CRITICAL: Operates at VARIABLE-LEVEL GRANULARITY, not domain-level aggregates.

This service analyzes individual variables (e.g., "Bitcoin Close Price", "UK Ice Cream Sales")
across ALL data sources, calculating correlations for every possible pair in the data universe.

Example:
  ✅ CORRECT: "Bitcoin Close Price" (alphavantage) ↔ "UK Ice Cream Sales" (worldbank)
  ❌ WRONG:   "Finance" ↔ "Market Data" (meaningless domain aggregates)

The cross_domain filter ensures we only surface non-obvious cross-domain variable relationships
where source1 ≠ source2, avoiding same-source pairs that everyone already knows about.

Key Insight: With 61 variables across 6 sources, this generates 3,721 unique variable pairs.
The system ranks by absolute correlation strength to surface the strongest signals.
"""

from database import get_db_session
from models import (
    VariableMetadata, TimeSeriesData, CorrelationResult,
    RollingCorrelation, AnalysisJob
)
from correlation_analyzer import CorrelationAnalyzer
from datetime import datetime, timedelta
import logging
import json
import pandas as pd
from typing import List, Tuple, Optional

logger = logging.getLogger(__name__)


class CorrelationAnalysisService:
    """Service to calculate correlations between all variable pairs"""
    
    def __init__(self):
        self.analyzer = CorrelationAnalyzer()
    
    def calculate_all_correlations(
        self,
        method: str = 'pearson',
        min_threshold: float = 0.0,
        significance_level: float = 0.05
    ) -> dict:
        """
        Calculate N×N correlation matrix for ALL variable pairs
        
        Args:
            method: 'pearson', 'spearman', or 'kendall'
            min_threshold: Minimum |r| to store (0.0 = store all)
            significance_level: p-value threshold for significance (0.05)
        
        Returns:
            Statistics about calculated correlations
        """
        logger.info(f"Calculating {method} correlations for all variable pairs...")
        
        # Create analysis job
        with get_db_session() as session:
            job = AnalysisJob(
                job_type='full_correlation',
                status='running',
                start_time=datetime.utcnow(),
                parameters=json.dumps({
                    'method': method,
                    'min_threshold': min_threshold,
                    'significance_level': significance_level
                })
            )
            session.add(job)
            session.commit()
            job_id = job.id
        
        try:
            # Get all variables with data
            with get_db_session() as session:
                variables = session.query(VariableMetadata).filter(
                    VariableMetadata.is_active.is_(True)
                ).all()
                
                var_ids = [v.id for v in variables]
                var_count = len(var_ids)
                
                logger.info(f"Found {var_count} active variables")
                logger.info(f"Will calculate {var_count * var_count} correlations")
        
            # Calculate correlations for all pairs
            total_pairs = 0
            significant_pairs = 0
            stored_pairs = 0
            
            # Process in batches to avoid memory issues
            for i, var1_id in enumerate(var_ids):
                if i % 10 == 0:
                    logger.info(f"Processing variable {i+1}/{var_count}...")
                
                # Get data for var1
                var1_data = self._get_variable_data(var1_id)
                if var1_data is None or len(var1_data) == 0:
                    continue
                
                # Calculate correlations with all other variables
                for var2_id in var_ids:
                    # Skip self-correlation and duplicates (only upper triangle)
                    if var2_id <= var1_id:
                        continue
                    
                    total_pairs += 1
                    
                    # Get data for var2
                    var2_data = self._get_variable_data(var2_id)
                    if var2_data is None or len(var2_data) == 0:
                        continue
                    
                    # Calculate correlation
                    result = self._calculate_pair_correlation(
                        var1_id, var2_id,
                        var1_data, var2_data,
                        method, job_id
                    )
                    
                    if result:
                        if result['is_significant']:
                            significant_pairs += 1
                        
                        if abs(result['correlation_value']) >= min_threshold:
                            self._store_correlation(result, job_id)
                            stored_pairs += 1
            
            # Update job status
            with get_db_session() as session:
                job = session.query(AnalysisJob).get(job_id)
                job.status = 'completed'
                job.end_time = datetime.utcnow()
                job.variables_count = var_count
                job.correlation_pairs_calculated = total_pairs
                job.significant_correlations_found = significant_pairs
                session.commit()
            
            stats = {
                'variables_count': var_count,
                'total_pairs_calculated': total_pairs,
                'significant_correlations': significant_pairs,
                'stored_correlations': stored_pairs,
                'method': method,
                'job_id': job_id
            }
            
            logger.info(f"Correlation analysis complete: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"Correlation analysis failed: {e}")
            
            with get_db_session() as session:
                job = session.query(AnalysisJob).get(job_id)
                job.status = 'failed'
                job.end_time = datetime.utcnow()
                job.error_message = str(e)
                session.commit()
            
            raise
    
    def _get_variable_data(self, variable_id: int) -> Optional[pd.Series]:
        """Get time series data for a variable"""
        with get_db_session() as session:
            data_points = session.query(TimeSeriesData).filter(
                TimeSeriesData.variable_id == variable_id
            ).order_by(TimeSeriesData.timestamp).all()
            
            if not data_points or len(data_points) < 3:
                return None
            
            # Convert to pandas Series
            values = [dp.value for dp in data_points]
            timestamps = [dp.timestamp for dp in data_points]
            
            return pd.Series(values, index=timestamps)
    
    def _calculate_pair_correlation(
        self,
        var1_id: int,
        var2_id: int,
        var1_data: pd.Series,
        var2_data: pd.Series,
        method: str,
        job_id: int
    ) -> Optional[dict]:
        """Calculate correlation between two variables"""
        try:
            # Align time series (handle different timestamps)
            try:
                aligned_data = pd.DataFrame({
                    'var1': var1_data,
                    'var2': var2_data
                })
                aligned_data = aligned_data.dropna()
            except Exception as e:
                logger.error(f"DataFrame alignment error for {var1_id}-{var2_id}: {e}")
                return None
            
            # Check minimum sample size
            # (20 points minimum for reliable correlation)
            try:
                sample_size = int(len(aligned_data))
                if sample_size < 20:
                    return None
            except Exception as e:
                logger.error(f"Sample size check error for {var1_id}-{var2_id}: {e}")
                return None
            
            # Extract numpy arrays
            try:
                x = aligned_data['var1'].values
                y = aligned_data['var2'].values
            except Exception as e:
                logger.error(f"Array extraction error for {var1_id}-{var2_id}: {e}")
                return None
            
            # Calculate correlation using correlation_analyzer.py
            try:
                if method == 'pearson':
                    r, p = self.analyzer.pearson_correlation(x, y)
                elif method == 'spearman':
                    r, p = self.analyzer.spearman_correlation(x, y)
                elif method == 'kendall':
                    r, p = self.analyzer.kendall_correlation(x, y)
                else:
                    raise ValueError(f"Unknown method: {method}")
            except Exception as e:
                logger.error(f"Correlation calculation error for {var1_id}-{var2_id}: {e}")
                return None
            
            # Build result dictionary with explicit type conversions
            try:
                result = {
                    'variable1_id': int(var1_id),
                    'variable2_id': int(var2_id),
                    'correlation_value': float(r) if r is not None else 0.0,
                    'p_value': float(p) if p is not None else 1.0,
                    'method': str(method),
                    'sample_size': sample_size,
                    'start_date': pd.Timestamp(aligned_data.index.min()).to_pydatetime(),
                    'end_date': pd.Timestamp(aligned_data.index.max()).to_pydatetime(),
                    'is_significant': bool(float(p) < 0.05) if p is not None else False,
                    'abs_correlation': float(abs(r)) if r is not None else 0.0
                }
                return result
            except Exception as e:
                logger.error(f"Result building error for {var1_id}-{var2_id}: {e}")
                return None
            
        except Exception as e:
            logger.error(f"Unexpected error calculating correlation {var1_id}-{var2_id}: {e}", exc_info=True)
            return None
    
    def _store_correlation(self, result: dict, job_id: int):
        """Store correlation result in database"""
        with get_db_session() as session:
            # Fetch source tags from variable metadata
            var1_meta = session.query(VariableMetadata).filter_by(id=result['variable1_id']).first()
            var2_meta = session.query(VariableMetadata).filter_by(id=result['variable2_id']).first()
            
            corr = CorrelationResult(
                variable1_id=result['variable1_id'],
                variable2_id=result['variable2_id'],
                correlation_value=result['correlation_value'],
                p_value=result['p_value'],
                method=result['method'],
                sample_size=result['sample_size'],
                start_date=result['start_date'],
                end_date=result['end_date'],
                is_significant=result['is_significant'],
                abs_correlation=result['abs_correlation'],
                analysis_job_id=job_id,
                calculated_at=datetime.utcnow(),
                source1=var1_meta.source if var1_meta else None,
                source2=var2_meta.source if var2_meta else None
            )
            session.add(corr)
            session.commit()
    
    def calculate_rolling_correlations(
        self,
        var1_id: int,
        var2_id: int,
        window_days: int = 30,
        method: str = 'pearson'
    ) -> List[dict]:
        """
        Calculate rolling correlation for drift analysis
        
        Args:
            var1_id: First variable ID
            var2_id: Second variable ID
            window_days: Rolling window size in days
            method: Correlation method
        
        Returns:
            List of rolling correlation results
        """
        logger.info(f"Calculating rolling correlation {var1_id}-{var2_id} (window={window_days})")
        
        # Get data for both variables
        var1_data = self._get_variable_data(var1_id)
        var2_data = self._get_variable_data(var2_id)
        
        if var1_data is None or var2_data is None:
            return []
        
        # Align data
        aligned = pd.DataFrame({
            'var1': var1_data,
            'var2': var2_data
        }).dropna()
        
        if len(aligned) < window_days:
            return []
        
        # Calculate rolling correlations
        results = []
        
        for i in range(len(aligned) - window_days + 1):
            window_data = aligned.iloc[i:i+window_days]
            
            try:
                x = window_data['var1'].values
                y = window_data['var2'].values
                
                if method == 'pearson':
                    r, p = self.analyzer.pearson_correlation(x, y)
                elif method == 'spearman':
                    r, p = self.analyzer.spearman_correlation(x, y)
                else:
                    r, p = self.analyzer.kendall_correlation(x, y)
                
                result = {
                    'window_start': window_data.index.min(),
                    'window_end': window_data.index.max(),
                    'window_size_days': window_days,
                    'correlation_value': r,
                    'p_value': p
                }
                
                results.append(result)
                
                # Store in database
                with get_db_session() as session:
                    rolling_corr = RollingCorrelation(
                        variable1_id=var1_id,
                        variable2_id=var2_id,
                        window_start=result['window_start'],
                        window_end=result['window_end'],
                        window_size_days=window_days,
                        correlation_value=r,
                        p_value=p,
                        method=method,
                        calculated_at=datetime.utcnow()
                    )
                    session.add(rolling_corr)
                    session.commit()
                
            except Exception as e:
                logger.warning(f"Error in rolling window {i}: {e}")
                continue
        
        logger.info(f"Calculated {len(results)} rolling correlation windows")
        return results
    
    def get_top_correlations(
        self,
        limit: int = 20,
        min_significance: float = 0.05,
        method: str = None,
        cross_domain: bool = False
    ) -> List[dict]:
        """
        Get top N correlations ranked by absolute strength
        
        Args:
            limit: Number of top correlations to return
            min_significance: Maximum p-value (0.05 = 95% confidence)
            method: Filter by correlation method (None = all)
            cross_domain: Only return correlations between different data sources
        
        Returns:
            List of top correlation results
        """
        with get_db_session() as session:
            query = session.query(CorrelationResult).filter(
                CorrelationResult.p_value <= min_significance
            )
            
            if method:
                query = query.filter(CorrelationResult.method == method)
            
            # Get results with relationships eagerly loaded
            from sqlalchemy.orm import joinedload
            results = (
                query.options(
                    joinedload(CorrelationResult.variable1),
                    joinedload(CorrelationResult.variable2)
                )
                .order_by(CorrelationResult.abs_correlation.desc())
                .limit(limit * 10 if cross_domain else limit)  # Get many more candidates for diversity
                .all()
            )
            
            correlations = []
            source_pair_count = {}  # Track how many times each source pair appears
            
            for r in results:
                # If cross_domain, filter out same-source correlations
                if cross_domain:
                    if r.variable1.source == r.variable2.source:
                        continue
                    
                    # Enforce diversity: limit same source-pair combinations to avoid GDP dominance
                    source_pair = tuple(sorted([r.variable1.source, r.variable2.source]))
                    current_count = source_pair_count.get(source_pair, 0)
                    
                    # Allow max 3 pairs from same source combination (e.g., max 3 alphavantage-worldbank)
                    if current_count >= 3:
                        continue
                    
                    source_pair_count[source_pair] = current_count + 1
                
                correlations.append({
                    'variable1_id': r.variable1_id,
                    'variable2_id': r.variable2_id,
                    'variable1_name': r.variable1.display_name,
                    'variable2_name': r.variable2.display_name,
                    'variable1_source': r.variable1.source,
                    'variable2_source': r.variable2.source,
                    'correlation_value': r.correlation_value,
                    'p_value': r.p_value,
                    'method': r.method,
                    'sample_size': r.sample_size,
                    'is_significant': r.is_significant,
                    'start_date': (
                        r.start_date.strftime('%Y-%m-%d')
                        if r.start_date else None
                    ),
                    'end_date': (
                        r.end_date.strftime('%Y-%m-%d')
                        if r.end_date else None
                    )
                })
                
                if len(correlations) >= limit:
                    break
            
            logger.info(
                f"Returned {len(correlations)} cross-domain "
                f"correlations with source diversity"
            )
            if cross_domain:
                logger.info(
                    f"Source pair distribution: "
                    f"{dict(source_pair_count)}"
                )
            
            return correlations
