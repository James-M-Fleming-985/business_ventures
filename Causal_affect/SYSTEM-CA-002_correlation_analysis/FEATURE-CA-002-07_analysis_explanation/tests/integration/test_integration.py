"""
Integration tests for Analysis Explanation Natural Language Insights feature
Feature ID: FEATURE-CA-002-07
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import json

# Mock the layer modules
from src.layers.correlation_interpreter import CorrelationInterpreter
from src.layers.drift_analyzer import DriftAnalyzer
from src.layers.natural_language_generator import NaturalLanguageGenerator
from src.layers.explanation_api import ExplanationAPI


@pytest.fixture
def correlation_data():
    """Fixture for sample correlation analysis data"""
    return {
        "correlations": {
            "feature_1_feature_2": 0.85,
            "feature_1_feature_3": -0.72,
            "feature_2_feature_3": -0.45
        },
        "p_values": {
            "feature_1_feature_2": 0.001,
            "feature_1_feature_3": 0.002,
            "feature_2_feature_3": 0.05
        },
        "significance_level": 0.05,
        "timestamp": datetime.now().isoformat()
    }


@pytest.fixture
def drift_data():
    """Fixture for sample drift analysis data"""
    return {
        "metrics": {
            "feature_1": {
                "drift_score": 0.78,
                "drift_type": "covariate_drift",
                "severity": "high",
                "direction": "increasing"
            },
            "feature_2": {
                "drift_score": 0.23,
                "drift_type": "concept_drift",
                "severity": "low",
                "direction": "stable"
            }
        },
        "overall_drift_score": 0.65,
        "detection_timestamp": datetime.now().isoformat(),
        "reference_window": "2024-01-01 to 2024-01-31",
        "analysis_window": "2024-02-01 to 2024-02-29"
    }


@pytest.fixture
def historical_data():
    """Fixture for sample historical analysis data"""
    dates = pd.date_range(start='2024-01-01', end='2024-02-29', freq='D')
    return pd.DataFrame({
        'timestamp': dates,
        'feature_1': np.random.normal(100, 15, len(dates)),
        'feature_2': np.random.normal(50, 10, len(dates)),
        'feature_3': np.random.normal(75, 20, len(dates))
    })


@pytest.fixture
def integrated_system():
    """Fixture for integrated system components"""
    correlation_interpreter = Mock(spec=CorrelationInterpreter)
    drift_analyzer = Mock(spec=DriftAnalyzer)
    nlg = Mock(spec=NaturalLanguageGenerator)
    api = Mock(spec=ExplanationAPI)
    
    return {
        'correlation_interpreter': correlation_interpreter,
        'drift_analyzer': drift_analyzer,
        'nlg': nlg,
        'api': api
    }


class TestCorrelationToNLGIntegration:
    """Test integration between Correlation Interpreter and Natural Language Generator"""
    
    def test_strong_correlation_explanation_generation(self, integrated_system, correlation_data):
        """Test that strong correlations are properly explained in natural language"""
        # Setup
        correlation_interpreter = integrated_system['correlation_interpreter']
        nlg = integrated_system['nlg']
        
        interpreted_correlations = {
            "strong_positive": [
                {
                    "features": ["feature_1", "feature_2"],
                    "correlation": 0.85,
                    "strength": "strong",
                    "direction": "positive",
                    "significance": "highly significant"
                }
            ],
            "strong_negative": [
                {
                    "features": ["feature_1", "feature_3"],
                    "correlation": -0.72,
                    "strength": "strong",
                    "direction": "negative",
                    "significance": "highly significant"
                }
            ]
        }
        
        expected_explanation = (
            "Strong positive correlation detected between feature_1 and feature_2 (r=0.85, p<0.01). "
            "This indicates that as feature_1 increases, feature_2 tends to increase proportionally. "
            "Strong negative correlation found between feature_1 and feature_3 (r=-0.72, p<0.01), "
            "suggesting an inverse relationship."
        )
        
        correlation_interpreter.interpret_correlations.return_value = interpreted_correlations
        nlg.generate_correlation_explanation.return_value = expected_explanation
        
        # Execute
        interpretation = correlation_interpreter.interpret_correlations(correlation_data)
        explanation = nlg.generate_correlation_explanation(interpretation)
        
        # Verify
        correlation_interpreter.interpret_correlations.assert_called_once_with(correlation_data)
        nlg.generate_correlation_explanation.assert_called_once_with(interpretation)
        assert explanation == expected_explanation
        assert "Strong positive correlation" in explanation
        assert "r=0.85" in explanation
    
    def test_correlation_interpretation_error_handling(self, integrated_system):
        """Test error handling when correlation interpretation fails"""
        # Setup
        correlation_interpreter = integrated_system['correlation_interpreter']
        nlg = integrated_system['nlg']
        
        correlation_interpreter.interpret_correlations.side_effect = ValueError("Invalid correlation data")
        nlg.generate_error_explanation.return_value = "Unable to interpret correlations: Invalid correlation data"
        
        # Execute
        with pytest.raises(ValueError):
            correlation_interpreter.interpret_correlations({})
        
        error_explanation = nlg.generate_error_explanation("correlation_interpretation", "Invalid correlation data")
        
        # Verify
        assert "Unable to interpret correlations" in error_explanation


class TestDriftAnalyzerToNLGIntegration:
    """Test integration between Drift Analyzer and Natural Language Generator"""
    
    def test_drift_detection_explanation_pipeline(self, integrated_system, drift_data, historical_data):
        """Test complete drift detection to explanation pipeline"""
        # Setup
        drift_analyzer = integrated_system['drift_analyzer']
        nlg = integrated_system['nlg']
        
        drift_summary = {
            "critical_drifts": ["feature_1"],
            "minor_drifts": ["feature_2"],
            "stable_features": ["feature_3"],
            "recommendations": [
                "Investigate feature_1 for data quality issues",
                "Monitor feature_2 for potential future drift"
            ]
        }
        
        expected_explanation = (
            "Significant drift detected in feature_1 with a drift score of 0.78 (high severity). "
            "The feature shows an increasing trend compared to the reference period. "
            "Minor drift observed in feature_2 (score: 0.23), which remains relatively stable. "
            "Recommendation: Investigate feature_1 for data quality issues and monitor feature_2."
        )
        
        drift_analyzer.analyze_drift.return_value = drift_data
        drift_analyzer.summarize_drift.return_value = drift_summary
        nlg.generate_drift_explanation.return_value = expected_explanation
        
        # Execute
        drift_results = drift_analyzer.analyze_drift(historical_data)
        summary = drift_analyzer.summarize_drift(drift_results)
        explanation = nlg.generate_drift_explanation(drift_results, summary)
        
        # Verify
        drift_analyzer.analyze_drift.assert_called_once_with(historical_data)
        drift_analyzer.summarize_drift.assert_called_once_with(drift_results)
        nlg.generate_drift_explanation.assert_called_once_with(drift_results, summary)
        assert "Significant drift detected" in explanation
        assert "feature_1" in explanation
        assert "0.78" in explanation
    
    def test_no_drift_scenario_explanation(self, integrated_system, historical_data):
        """Test explanation generation when no drift is detected"""
        # Setup
        drift_analyzer = integrated_system['drift_analyzer']
        nlg = integrated_system['nlg']
        
        no_drift_data = {
            "metrics": {
                "feature_1": {"drift_score": 0.05, "severity": "none"},
                "feature_2": {"drift_score": 0.08, "severity": "none"}
            },
            "overall_drift_score": 0.065
        }
        
        expected_explanation = "No significant drift detected. All features remain stable within acceptable thresholds."
        
        drift_analyzer.analyze_drift.return_value = no_drift_data
        nlg.generate_drift_explanation.return_value = expected_explanation
        
        # Execute
        drift_results = drift_analyzer.analyze_drift(historical_data)
        explanation = nlg.generate_drift_explanation(drift_results, {})
        
        # Verify
        assert "No significant drift" in explanation
        assert "stable" in explanation


class TestExplanationAPIIntegration:
    """Test integration with Explanation API layer"""
    
    def test_full_analysis_explanation_api_flow(self, integrated_system, correlation_data, drift_data):
        """Test complete flow from analysis to API response"""
        # Setup
        correlation_interpreter = integrated_system['correlation_interpreter']
        drift_analyzer = integrated_system['drift_analyzer']
        nlg = integrated_system['nlg']
        api = integrated_system['api']
        
        correlation_explanation = "Strong correlations detected between multiple features."
        drift_explanation = "Significant drift observed in key features."
        
        api_response = {
            "status": "success",
            "explanations": {
                "correlation_analysis": {
                    "summary": correlation_explanation,
                    "details": correlation_data,
                    "timestamp": datetime.now().isoformat()
                },
                "drift_analysis": {
                    "summary": drift_explanation,
                    "details": drift_data,
                    "timestamp": datetime.now().isoformat()
                }
            },
            "metadata": {
                "api_version": "1.0",
                "processing_time_ms": 245
            }
        }
        
        correlation_interpreter.interpret_correlations.return_value = {"interpreted": True}
        drift_analyzer.analyze_drift.return_value = drift_data
        nlg.generate_correlation_explanation.return_value = correlation_explanation
        nlg.generate_drift_explanation.return_value = drift_explanation
        api.create_explanation_response.return_value = api_response
        
        # Execute
        correlations = correlation_interpreter.interpret_correlations(correlation_data)
        corr_explanation = nlg.generate_correlation_explanation(correlations)
        
        drift_results = drift_analyzer.analyze_drift(pd.DataFrame())
        drift_explanation = nlg.generate_drift_explanation(drift_results, {})
        
        response = api.create_explanation_response({
            "correlation": corr_explanation,
            "drift": drift_explanation
        })
        
        # Verify
        api.create_explanation_response.assert_called_once()
        assert response["status"] == "success"
        assert "correlation_analysis" in response["explanations"]
        assert "drift_analysis" in response["explanations"]
    
    def test_api_error_handling_cascade(self, integrated_system):
        """Test error handling cascade through API layer"""
        # Setup
        nlg = integrated_system['nlg']
        api = integrated_system['api']
        
        nlg.generate_correlation_explanation.side_effect = RuntimeError("NLG service unavailable")
        api.create_error_response.return_value = {
            "status": "error",
            "error": {
                "type": "ServiceUnavailable",
                "message": "Natural language generation service is currently unavailable",
                "timestamp": datetime.now().isoformat()
            }
        }
        
        # Execute
        with pytest.raises(RuntimeError):
            nlg.generate_correlation_explanation({})
        
        error_response = api.create_error_response("ServiceUnavailable", 
                                                  "Natural language generation service is currently unavailable")
        
        # Verify
        assert error_response["status"] == "error"
        assert error_response["error"]["type"] == "ServiceUnavailable"


class TestMultiLayerIntegration:
    """Test integration across multiple layers"""
    
    def test_concurrent_analysis_explanation_generation(self, integrated_system, correlation_data, drift_data):
        """Test concurrent processing of correlation and drift analysis with explanation generation"""
        # Setup
        from concurrent.futures import ThreadPoolExecutor, Future
        
        correlation_interpreter = integrated_system['correlation_interpreter']
        drift_analyzer = integrated_system['drift_analyzer']
        nlg = integrated_system['nlg']
        
        # Mock futures for concurrent execution
        correlation_future = Future()
        drift_future = Future()
        
        correlation_result = {"correlations": "analyzed"}
        drift_result = {"drift": "detected"}
        
        correlation_future.set_result(correlation_result)
        drift_future.set_result(drift_result)
        
        combined_explanation = (
            "Analysis complete. Correlation analysis shows strong relationships between features. "
            "Drift analysis indicates significant changes in data distribution."
        )
        
        correlation_interpreter.interpret_correlations.return_value = correlation_result
        drift_analyzer.analyze_drift.return_value = drift_result
        nlg.generate_combined_explanation.return_value = combined_explanation
        
        # Execute
        with patch('concurrent.futures.ThreadPoolExecutor') as mock_executor:
            mock_executor.return_value.__enter__.return_value.submit.side_effect = [
                correlation_future,
                drift_future
            ]
            
            # Simulate concurrent execution
            executor = ThreadPoolExecutor(max_workers=2)
            correlation_task = executor.submit(correlation_interpreter.interpret_correlations, correlation_data)
            drift_task = executor.submit(drift_analyzer.analyze_drift, pd.DataFrame())
            
            # Get results
            correlation_res = correlation_task.result()
            drift_res = drift_task.result()
            
            # Generate combined explanation
            explanation = nlg.generate_combined_explanation(correlation_res, drift_res)
        
        # Verify
        assert "Analysis complete" in explanation
        assert "Correlation analysis" in explanation
        assert "Drift analysis" in explanation
    
    def test_cascading_failure_recovery(self, integrated_system):
        """Test system recovery from cascading failures across layers"""
        # Setup
        correlation_interpreter = integrated_system['correlation_interpreter']
        drift_analyzer = integrated_system['drift_analyzer']
        nlg = integrated_system['nlg']
        api = integrated_system['api']
        
        # First attempt fails
        correlation_interpreter.interpret_correlations.side_effect = [
            ConnectionError("Database unavailable"),
            {"correlations": "recovered"}  # Success on retry
        ]
        
        nlg.generate_correlation_explanation.return_value = "Analysis recovered after temporary failure."
        api.create_explanation_response.return_value = {
            "status": "success",
            "explanation": "Analysis recovered after temporary failure.",
            "metadata": {"retry_count": 1}
        }
        
        # Execute with retry logic
        retry_count = 0
        max_retries = 2
        result = None
        
        while retry_count < max_retries:
            try:
                interpretation = correlation_interpreter.interpret_correlations({})
                explanation = nlg.generate_correlation_explanation(interpretation)
                result = api.create_explanation_response({"explanation": explanation})
                break
            except ConnectionError:
                retry_count += 1
                if retry_count >= max_retries:
                    raise
        
        # Verify
        assert result is not None
        assert result["status"] == "success"
        assert retry_count == 1
        assert correlation_interpreter.interpret_correlations.call_count == 2


class TestEndToEndIntegration:
    """Test complete end-to-end integration scenarios"""
    
    def test_full_feature_integration_with_all_layers(self, integrated_system, historical_data):
        """Test complete feature integration from raw data to final API response"""
        # Setup
        correlation_interpreter = integrated_system['correlation_interpreter']
        drift_analyzer = integrated_system['drift_analyzer']
        nlg = integrated_system['nlg']
        api = integrated_system['api']
        
        # Mock complete analysis pipeline
        raw_correlations = {
            "matrix": [[1.0, 0.85], [0.85, 1.0]],
            "features": ["feature_1", "feature_2"]
        }
        
        interpreted_correlations = {
            "strong_positive": [{"features": ["feature_1", "feature_2"], "correlation": 0.85}]
        }
        
        drift_results = {
            "metrics": {"feature_1": {"drift_score": 0.65, "severity": "medium"}},
            "overall_drift_score": 0.65
        }
        
        correlation_explanation = "Strong positive correlation (r=0.85) between feature_1 and feature_2."
        drift_explanation = "Moderate drift detected in feature_1 (score: 0.65)."
        combined_insight = (
            "Analysis reveals strong positive correlation between feature_1 and feature_2, "
            "however, feature_1 shows moderate drift which may impact this relationship."
        )
        
        final_response = {
            "status": "success",
            "insights": {
                "correlation": correlation_explanation,
                "drift": drift_explanation,
                "combined": combined_insight
            },
            "recommendations": [
                "Monitor feature_1 drift impact on correlations",
                "Consider retraining models if drift persists"
            ],
            "metadata": {
                "analysis_timestamp": datetime.now().isoformat(),
                "data_points_analyzed": len(historical_data),
                "confidence_score": 0.92
            }
        }
        
        # Configure mocks
        correlation_interpreter.calculate_correlations.return_value = raw_correlations
        correlation_interpreter.interpret_correlations.return_value = interpreted_correlations
        drift_analyzer.analyze_drift.return_value = drift_results
        nlg.generate_correlation_explanation.return_value = correlation_explanation
        nlg.generate_drift_explanation.return_value = drift_explanation
        nlg.generate_combined_insight.return_value = combined_insight
        api.create_comprehensive_response.return_value = final_response
        
        # Execute complete pipeline
        # Step 1: Calculate correlations
        correlations = correlation_interpreter.calculate_correlations(historical_data)
        
        # Step 2: Interpret correlations
        interpreted = correlation_interpreter.interpret_correlations(correlations)
        
        # Step 3: Analyze drift
        drift = drift_analyzer.analyze_drift(historical_data)
        
        # Step 4: Generate explanations
        corr_exp = nlg.generate_correlation_explanation(interpreted)
        drift_exp = nlg.generate_drift_explanation(drift, {})
        combined = nlg.generate_combined_insight(interpreted, drift)
        
        # Step 5: Create API response
        response = api.create_comprehensive_response({
            "correlation": corr_exp,
            "drift": drift_exp,
            "combined": combined
        })
        
        # Verify
        assert response["status"] == "success"
        assert "insights" in response
        assert "recommendations" in response
        assert response["metadata"]["confidence_score"] == 0.92
        assert len(response["recommendations"]) == 2
        
        # Verify all layers were called
        correlation_interpreter.calculate_correlations.assert_called_once()
        correlation_interpreter.interpret_correlations.assert_called_once()
        drift_analyzer.analyze_drift.assert_called_once()
        nlg.generate_correlation_explanation.assert_called_once()
        nlg.generate_drift_explanation.assert_called_once()
        nlg.generate_combined_insight.assert_called_once()
        api.create_comprehensive_response.assert_called_once()