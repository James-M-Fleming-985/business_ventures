"""
Composite Signal Aggregator
Aggregates fast-moving signals from multiple sources (Wikipedia, Reddit, Twitter, etc.)
into weighted composite signals for cleaner Signal Radar display.

This module handles dynamic keyword discovery - keywords are NOT pre-configured,
they emerge from real-time human behavior across data sources.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from collections import defaultdict
from enum import Enum
import numpy as np
import logging

logger = logging.getLogger(__name__)


class MatchingMode(Enum):
    """Keyword matching modes for signal aggregation"""
    SIMPLE = "simple"          # Exact keyword match (case-insensitive)
    FUZZY = "fuzzy"            # Fuzzy string matching (TODO: future implementation)
    SOPHISTICATED = "sophisticated"  # ML/NLP-based semantic matching (TODO: future implementation)


# Available matching modes for UI dropdown
MATCHING_MODES = [
    {
        'value': 'simple',
        'label': 'Simple (Exact Match)',
        'description': 'Groups signals with identical keywords (case-insensitive)',
        'implemented': True
    },
    {
        'value': 'fuzzy',
        'label': 'Fuzzy Matching',
        'description': 'Groups similar keywords (e.g., "layoff" ≈ "layoffs")',
        'implemented': False  # TODO: Implement fuzzy matching
    },
    {
        'value': 'sophisticated',
        'label': 'ML Semantic Matching',
        'description': 'Groups semantically related keywords using NLP',
        'implemented': False  # TODO: Implement ML-based matching
    }
]


# Source reliability weights (based on historical prediction accuracy)
SOURCE_WEIGHTS = {
    'wikipedia': 0.35,      # Most reliable, stable data
    'google_trends': 0.30,  # Good reliability, less noise
    'reddit': 0.20,         # More volatile, community-driven
    'twitter': 0.15,        # Most noisy, bot issues
    'arxiv': 0.40,          # Highly reliable for research topics
}


@dataclass
class SourceSignal:
    """Individual signal from a single source"""
    keyword: str              # e.g., "layoff"
    source: str               # e.g., "wikipedia"
    momentum: float           # e.g., 64.6
    data_points: int          # Number of observations
    timestamp: str            # When this was measured
    raw_data: Optional[np.ndarray] = None  # Time series data


@dataclass
class CompositeSignal:
    """Aggregated signal combining multiple sources for same keyword"""
    keyword: str              # Canonical keyword (normalized)
    composite_momentum: float # Weighted average momentum
    sources: List[SourceSignal]
    source_count: int
    confidence_level: str     # "Very High", "High", "Moderate", "Low"
    confidence_stars: int     # 1-4 stars
    agreement_score: float    # 0-100% (how aligned are sources?)
    composite_timeseries: Optional[np.ndarray] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


def normalize_keyword(keyword: str, mode: MatchingMode = MatchingMode.SIMPLE) -> str:
    """
    Normalize keyword for grouping based on matching mode.
    
    Args:
        keyword: Raw keyword from data source
        mode: Matching mode to use
        
    Returns:
        Normalized keyword for comparison
    """
    if mode == MatchingMode.SIMPLE:
        # Simple mode: exact match (case-insensitive, whitespace normalized)
        normalized = keyword.strip().lower()
        normalized = normalized.replace('_', ' ')
        normalized = ' '.join(normalized.split())  # Collapse multiple spaces
        return normalized
    
    elif mode == MatchingMode.FUZZY:
        # TODO: Implement fuzzy matching
        # Will use libraries like fuzzywuzzy or rapidfuzz
        # For now, fall back to simple
        logger.warning("Fuzzy matching not yet implemented, using simple mode")
        return normalize_keyword(keyword, MatchingMode.SIMPLE)
    
    elif mode == MatchingMode.SOPHISTICATED:
        # TODO: Implement ML/NLP semantic matching
        # Will use spaCy, word embeddings, or similar
        # For now, fall back to simple
        logger.warning("Sophisticated matching not yet implemented, using simple mode")
        return normalize_keyword(keyword, MatchingMode.SIMPLE)
    
    else:
        logger.warning(f"Unknown matching mode {mode}, using simple mode")
        return normalize_keyword(keyword, MatchingMode.SIMPLE)


def get_source_weight(source: str) -> float:
    """
    Get reliability weight for a data source.
    
    Args:
        source: Source name (e.g., 'wikipedia', 'twitter')
        
    Returns:
        Weight between 0 and 1 (higher = more reliable)
    """
    source_lower = source.lower()
    return SOURCE_WEIGHTS.get(source_lower, 0.25)  # Default 25% if unknown


def calculate_agreement_score(sources: List[SourceSignal]) -> float:
    """
    Calculate how well sources agree on momentum direction and magnitude.
    
    Agreement criteria:
    - All same sign (all positive or all negative): Base score
    - Low variance in magnitude: Bonus points
    - Mixed signs: Penalty
    
    Args:
        sources: List of source signals for same keyword
        
    Returns:
        Agreement score from 0-100%
    """
    if len(sources) == 1:
        return 100.0  # Single source always agrees with itself
    
    momentums = [s.momentum for s in sources]
    
    # Check if all same sign
    all_positive = all(m > 0 for m in momentums)
    all_negative = all(m < 0 for m in momentums)
    
    if all_positive or all_negative:
        # Calculate variance as % of mean
        variance = np.var(momentums)
        mean_abs = np.mean(np.abs(momentums))
        
        if mean_abs > 0:
            # Lower variance = higher agreement
            variance_ratio = variance / (mean_abs ** 2)
            agreement = 100 * (1 - min(variance_ratio, 1.0))
        else:
            agreement = 100.0
    else:
        # Mixed signals - penalize based on disagreement ratio
        positive_count = sum(1 for m in momentums if m > 0)
        negative_count = len(momentums) - positive_count
        majority = max(positive_count, negative_count)
        
        # Base agreement on majority, but penalize for conflict
        agreement = 100 * (majority / len(momentums)) - 30
        agreement = max(agreement, 0)
    
    return min(agreement, 100.0)


def get_confidence_level(source_count: int, agreement: float) -> tuple[str, int]:
    """
    Determine confidence level based on number of sources and agreement.
    
    Args:
        source_count: Number of sources validating this signal
        agreement: Agreement score (0-100%)
        
    Returns:
        Tuple of (confidence_label, star_count)
    """
    if source_count >= 4 and agreement >= 90:
        return ("Very High", 4)  # ⭐⭐⭐⭐
    elif source_count >= 3 and agreement >= 80:
        return ("High", 3)       # ⭐⭐⭐
    elif source_count >= 2 and agreement >= 70:
        return ("Moderate", 2)   # ⭐⭐
    else:
        return ("Low", 1)        # ⭐


def create_weighted_timeseries(sources: List[SourceSignal]) -> Optional[np.ndarray]:
    """
    Create composite time series as weighted average of source time series.
    
    Args:
        sources: List of source signals with raw_data
        
    Returns:
        Weighted composite time series, or None if data unavailable
    """
    # Filter sources that have time series data
    sources_with_data = [s for s in sources if s.raw_data is not None]
    
    if not sources_with_data:
        return None
    
    # Find minimum length (for alignment)
    min_length = min(len(s.raw_data) for s in sources_with_data)
    
    if min_length == 0:
        return None
    
    # Align all time series to same length (take most recent data)
    aligned_data = [s.raw_data[-min_length:] for s in sources_with_data]
    weights = np.array([get_source_weight(s.source) for s in sources_with_data])
    
    # Normalize weights to sum to 1
    weights = weights / weights.sum()
    
    # Calculate weighted average at each time point
    composite = np.average(aligned_data, axis=0, weights=weights)
    
    return composite


def aggregate_signals(
    raw_signals: List[SourceSignal],
    matching_mode: MatchingMode = MatchingMode.SIMPLE
) -> List[CompositeSignal]:
    """
    Aggregate signals from multiple sources into composite signals.
    
    This is the main function that groups signals by keyword and creates
    weighted composites for Signal Radar display.
    
    Args:
        raw_signals: List of individual source signals (dynamically discovered)
        matching_mode: How to match keywords across sources (simple, fuzzy, sophisticated)
        
    Returns:
        List of composite signals, sorted by momentum (strongest first)
    """
    # Group signals by normalized keyword
    keyword_groups = defaultdict(list)
    
    for signal in raw_signals:
        normalized_key = normalize_keyword(signal.keyword, matching_mode)
        keyword_groups[normalized_key].append(signal)
    
    # Create composite signals
    composite_signals = []
    
    for keyword, sources in keyword_groups.items():
        # Calculate weighted average momentum
        total_weight = sum(get_source_weight(s.source) for s in sources)
        
        if total_weight == 0:
            logger.warning(f"Zero total weight for keyword '{keyword}', skipping")
            continue
        
        composite_momentum = sum(
            s.momentum * get_source_weight(s.source) for s in sources
        ) / total_weight
        
        # Calculate agreement score
        agreement = calculate_agreement_score(sources)
        
        # Determine confidence level and stars
        confidence_label, stars = get_confidence_level(len(sources), agreement)
        
        # Create composite time series (if data available)
        composite_ts = create_weighted_timeseries(sources)
        
        # Create composite signal
        composite = CompositeSignal(
            keyword=keyword,
            composite_momentum=composite_momentum,
            sources=sources,
            source_count=len(sources),
            confidence_level=confidence_label,
            confidence_stars=stars,
            agreement_score=agreement,
            composite_timeseries=composite_ts,
            metadata={
                'total_weight': total_weight,
                'source_names': [s.source for s in sources],
                'individual_momentums': [s.momentum for s in sources],
                'matching_mode': matching_mode.value
            }
        )
        
        composite_signals.append(composite)
    
    # Sort by absolute momentum (strongest signals first)
    composite_signals.sort(key=lambda x: abs(x.composite_momentum), reverse=True)
    
    logger.info(
        f"Aggregated {len(raw_signals)} signals into {len(composite_signals)} "
        f"composite signals using {matching_mode.value} matching"
    )
    
    return composite_signals


def get_available_matching_modes() -> List[Dict[str, Any]]:
    """
    Get list of available matching modes for UI dropdown.
    
    Returns:
        List of matching mode configurations
    """
    return MATCHING_MODES


def get_signal_details(composite: CompositeSignal) -> Dict[str, Any]:
    """
    Get detailed breakdown for modal display.
    
    Args:
        composite: Composite signal to detail
        
    Returns:
        Dictionary with source breakdown, weights, etc.
    """
    source_breakdown = []
    
    for source in composite.sources:
        weight = get_source_weight(source.source)
        source_breakdown.append({
            'source_name': source.source.title(),
            'momentum': source.momentum,
            'weight_percent': weight * 100,
            'data_points': source.data_points,
            'timestamp': source.timestamp
        })
    
    # Sort by weight (highest first)
    source_breakdown.sort(key=lambda x: x['weight_percent'], reverse=True)
    
    return {
        'keyword': composite.keyword.title(),
        'composite_momentum': round(composite.composite_momentum, 1),
        'source_count': composite.source_count,
        'confidence_level': composite.confidence_level,
        'confidence_stars': composite.confidence_stars,
        'agreement_score': round(composite.agreement_score, 1),
        'sources': source_breakdown,
        'metadata': composite.metadata
    }


# Example usage
if __name__ == "__main__":
    # Simulate dynamic signals discovered from trending data
    test_signals = [
        SourceSignal("Layoff", "wikipedia", 64.6, 500, "2026-01-23T10:00:00Z"),
        SourceSignal("layoff", "twitter", 72.1, 1200, "2026-01-23T10:00:00Z"),
        SourceSignal("layoffs", "reddit", 60.3, 800, "2026-01-23T10:00:00Z"),
        SourceSignal("Unemployment", "google_trends", 45.8, 600, "2026-01-23T10:00:00Z"),
        SourceSignal("Taylor Swift", "wikipedia", 120.5, 1500, "2026-01-23T10:00:00Z"),
        SourceSignal("taylor swift", "twitter", 110.2, 3000, "2026-01-23T10:00:00Z"),
        SourceSignal("AI Research", "arxiv", 43.0, 200, "2026-01-23T10:00:00Z"),
    ]
    
    # Aggregate
    composites = aggregate_signals(test_signals)
    
    # Display results
    for comp in composites:
        print(f"\n{'='*60}")
        print(f"🎯 {comp.keyword.upper()} SIGNAL")
        print(f"   Momentum: {comp.composite_momentum:+.1f}%")
        print(f"   Confidence: {comp.confidence_level} {'⭐' * comp.confidence_stars}")
        print(f"   Sources: {comp.source_count} validated")
        print(f"   Agreement: {comp.agreement_score:.0f}%")
        print(f"\n   Source Breakdown:")
        for src in comp.sources:
            weight = get_source_weight(src.source)
            print(f"   ├─ {src.source.title():15s} {src.momentum:+6.1f}% (weight: {weight*100:.0f}%)")
