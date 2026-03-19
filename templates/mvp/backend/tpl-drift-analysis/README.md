# Temporal Drift Analysis System Template

## Overview
Template for building drift detection systems that analyze relationship stability over time and predict exploitation windows.

## Features
- Multi-timeframe correlation tracking
- Change point detection
- Stability scoring algorithms
- Exploitation window calculations
- Seasonal pattern recognition

## Dependencies
```python
fastapi==0.104.1
numpy==1.24.3
scipy==1.11.3
pandas==2.0.3
scikit-learn==1.3.0
ruptures==1.1.8
statsmodels==0.14.0
```

## Template Variables
- `{{system_name}}`: Name of the drift analysis system
- `{{timeframes}}`: List of analysis timeframes (e.g., ['1W', '1M', '3M', '6M'])
- `{{stability_threshold}}`: Minimum stability score (0-100)
- `{{api_prefix}}`: API route prefix

## Generated Structure
```
drift_analysis/
├── models/
│   ├── drift_result.py
│   ├── stability_score.py
│   └── exploitation_window.py
├── services/
│   ├── drift_detector.py
│   ├── stability_scorer.py
│   ├── changepoint_detector.py
│   └── window_calculator.py
├── api/
│   └── drift_router.py
└── tests/
    ├── test_drift_accuracy.py
    └── test_stability_scoring.py
```

## Key Algorithms
- PELT (Pruned Exact Linear Time) for changepoint detection
- Rolling correlation analysis with multiple windows
- Volatility-adjusted stability scoring
- Exponential decay modeling for relationship persistence

## Output Metrics
- Relationship half-life (days until 50% strength loss)
- Stability score (0-100, higher = more persistent)
- Exploitation window (recommended MVP timeframe)
- Risk assessment (probability of breakdown)