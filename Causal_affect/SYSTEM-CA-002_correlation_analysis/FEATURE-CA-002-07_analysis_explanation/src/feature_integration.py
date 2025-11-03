"""
Feature Integration Module for Analysis Explanation Natural Language Insights
Feature ID: FEATURE-CA-002-07

This module orchestrates the interaction between:
- Correlation Interpreter
- Drift Analyzer
- Natural Language Generator
- Explanation API
"""

from pathlib import Path
import sys
from dataclasses import dataclass
from typing import Dict, List, Optional, Any, Union, Tuple
import logging
from datetime import datetime
import numpy as np
import pandas as pd

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import from layer implementations
from LAYER_CA_002_07_01_Correlation_Interpreter.src.implementation import (
    CorrelationInterpreter,
    CorrelationExplainer
)
from LAYER_CA_002_07_02_Drift_Analyzer.src.implementation import (
    DriftAnalyzer,
    ConceptDriftDetector,
    DataDriftVisualizer
)
from LAYER_CA_002_07_03_Natural_Language_Generator.src.implementation import (
    CorrelationResult,
    NaturalLanguageGenerator
)
from LAYER_CA_002_07_04_Explanation_API.src.implementation import (
    CorrelationExplanation
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class FeatureConfig:
    """Configuration for the Analysis Explanation feature"""
    enable_drift_detection: bool = True
    enable_visualizations: bool = True
    explanation_detail_level: str = "detailed"  # 'brief', 'detailed', 'technical'
    layperson_mode: bool = False
    drift_threshold: float = 0.05
    max_correlations_to_explain: int = 10


@dataclass
class FeatureResponse:
    """Unified response structure for feature operations"""
    success: bool
    data: Optional[Dict[str, Any]] = None
    explanations: Optional[List[str]] = None
    visualizations: Optional[List[Any]] = None
    drift_report: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


class FeatureOrchestrator:
    """
    Orchestrates the Analysis Explanation Natural Language Insights feature.
    
    Coordinates between Correlation Interpreter, Drift Analyzer,
    Natural Language Generator, and Explanation API layers.
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Initialize the feature orchestrator.
        
        Args:
            config: Feature configuration settings
        """
        self.config = config or FeatureConfig()
        
        # Initialize layer instances
        try:
            self.correlation_interpreter = CorrelationInterpreter()
            self.correlation_explainer = CorrelationExplainer()
            self.drift_analyzer = DriftAnalyzer()
            self.concept_drift_detector = ConceptDriftDetector()
            self.drift_visualizer = DataDriftVisualizer()
            self.nlg = NaturalLanguageGenerator()
            self.explanation_api = CorrelationExplanation()
            
            logger.info("Feature orchestrator initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize feature layers: {str(e)}")
            raise
    
    def analyze_and_explain_correlation(
        self,
        data: Union[pd.DataFrame, np.ndarray],
        feature_names: Optional[List[str]] = None,
        target_feature: Optional[str] = None
    ) -> FeatureResponse:
        """
        Analyze correlations in data and generate natural language explanations.
        
        Args:
            data: Input data for correlation analysis
            feature_names: Names of features in the data
            target_feature: Optional specific feature to focus analysis on
            
        Returns:
            FeatureResponse with analysis results and explanations
        """
        try:
            # Step 1: Interpret correlations
            if isinstance(data, pd.DataFrame):
                correlation_matrix = data.corr()
            else:
                correlation_matrix = np.corrcoef(data.T)
            
            interpretation = self.correlation_interpreter.interpret_correlation_matrix(
                correlation_matrix
            )
            
            # Step 2: Generate explanations via API
            api_explanations = self.explanation_api.explain_correlation_matrix(
                correlation_matrix,
                feature_names=feature_names
            )
            
            key_findings = self.explanation_api.get_key_findings(
                correlation_matrix,
                feature_names=feature_names
            )
            
            # Step 3: Generate natural language descriptions
            explanations = []
            if isinstance(interpretation, dict) and 'correlations' in interpretation:
                for corr_info in interpretation['correlations'][:self.config.max_correlations_to_explain]:
                    # Create CorrelationResult object for NLG
                    corr_result = CorrelationResult(
                        value=corr_info.get('value', 0),
                        features=(corr_info.get('feature1'), corr_info.get('feature2'))
                    )
                    
                    nl_explanation = self.nlg.generate_explanation(corr_result)
                    explanations.append(nl_explanation)
            
            # Step 4: Generate layperson explanations if enabled
            if self.config.layperson_mode:
                layperson_explanations = []
                for explanation in api_explanations:
                    layperson_version = self.correlation_explainer.explain_for_layperson(
                        explanation
                    )
                    layperson_explanations.append(layperson_version)
                explanations.extend(layperson_explanations)
            
            # Step 5: Create visualizations if enabled
            visualizations = []
            if self.config.enable_visualizations:
                viz = self.correlation_interpreter.visualize_correlation(
                    correlation_matrix,
                    feature_names=feature_names
                )
                visualizations.append(viz)
            
            # Step 6: Suggest further analysis
            suggestions = self.explanation_api.suggest_further_analysis(
                correlation_matrix,
                feature_names=feature_names
            )
            
            return FeatureResponse(
                success=True,
                data={
                    'correlation_matrix': correlation_matrix,
                    'interpretation': interpretation,
                    'key_findings': key_findings,
                    'suggestions': suggestions
                },
                explanations=explanations,
                visualizations=visualizations
            )
            
        except Exception as e:
            logger.error(f"Error in analyze_and_explain_correlation: {str(e)}")
            return FeatureResponse(
                success=False,
                error=str(e)
            )
    
    def analyze_correlation_drift(
        self,
        reference_data: Union[pd.DataFrame, np.ndarray],
        current_data: Union[pd.DataFrame, np.ndarray],
        feature_names: Optional[List[str]] = None
    ) -> FeatureResponse:
        """
        Analyze drift in correlation patterns between reference and current data.
        
        Args:
            reference_data: Historical/reference dataset
            current_data: Current dataset to compare
            feature_names: Names of features in the data
            
        Returns:
            FeatureResponse with drift analysis and explanations
        """
        try:
            if not self.config.enable_drift_detection:
                return FeatureResponse(
                    success=True,
                    data={'message': 'Drift detection is disabled'},
                    explanations=['Drift detection is not enabled in configuration']
                )
            
            # Step 1: Fit drift analyzer on reference data
            self.drift_analyzer.fit(reference_data)
            
            # Step 2: Detect drift in current data
            drift_detected = self.drift_analyzer.detect_drift(current_data)
            drift_report = self.drift_analyzer.get_drift_report()
            
            # Step 3: Update concept drift detector
            if isinstance(reference_data, pd.DataFrame):
                ref_corr = reference_data.corr()
                curr_corr = current_data.corr()
            else:
                ref_corr = np.corrcoef(reference_data.T)
                curr_corr = np.corrcoef(current_data.T)
            
            # Update detector with correlation differences
            corr_diff = np.abs(curr_corr - ref_corr).mean()
            self.concept_drift_detector.update(corr_diff)
            drift_info = self.concept_drift_detector.get_drift_info()
            
            # Step 4: Generate explanations for drift
            explanations = []
            
            if drift_detected:
                # Explain what drift means
                drift_explanation = self.nlg.explain_correlation_meaning(
                    "Significant correlation drift detected",
                    context={'drift_severity': drift_info.get('severity', 'unknown')}
                )
                explanations.append(drift_explanation)
                
                # Get correlation explanations for both periods
                ref_explanation = self.explanation_api.explain_correlation_matrix(
                    ref_corr,
                    feature_names=feature_names
                )
                curr_explanation = self.explanation_api.explain_correlation_matrix(
                    curr_corr,
                    feature_names=feature_names
                )
                
                explanations.extend([
                    "Reference period correlations:",
                    *ref_explanation[:3],
                    "Current period correlations:",
                    *curr_explanation[:3]
                ])
            
            # Step 5: Create drift visualizations
            visualizations = []
            if self.config.enable_visualizations and drift_detected:
                # Add drift results to visualizer
                self.drift_visualizer.add_drift_result(
                    timestamp=datetime.now(),
                    drift_score=corr_diff,
                    features=feature_names
                )
                
                # Create timeline plot
                timeline_viz = self.drift_visualizer.plot_drift_timeline()
                visualizations.append(timeline_viz)
                
                # Create feature drift plot if features specified
                if feature_names:
                    for feature in feature_names[:5]:  # Limit to 5 features
                        feature_viz = self.drift_visualizer.plot_feature_drift(feature)
                        visualizations.append(feature_viz)
            
            return FeatureResponse(
                success=True,
                data={
                    'drift_detected': drift_detected,
                    'drift_score': corr_diff,
                    'drift_info': drift_info
                },
                explanations=explanations,
                visualizations=visualizations,
                drift_report=drift_report
            )
            
        except Exception as e:
            logger.error(f"Error in analyze_correlation_drift: {str(e)}")
            return FeatureResponse(
                success=False,
                error=str(e)
            )
    
    def explain_specific_correlation(
        self,
        feature1: str,
        feature2: str,
        correlation_value: float,
        data: Optional[pd.DataFrame] = None
    ) -> FeatureResponse:
        """
        Generate detailed explanation for a specific correlation.
        
        Args:
            feature1: First feature name
            feature2: Second feature name
            correlation_value: Correlation coefficient value
            data: Optional data for additional context
            
        Returns:
            FeatureResponse with detailed correlation explanation
        """
        try:
            # Step 1: Interpret the correlation
            interpretation = self.correlation_interpreter.interpret_correlation(
                correlation_value,
                feature1=feature1,
                feature2=feature2
            )
            
            # Step 2: Explain the correlation
            detailed_explanation = self.correlation_interpreter.explain_correlation(
                correlation_value,
                feature1=feature1,
                feature2=feature2
            )
            
            # Step 3: Generate natural language explanation
            corr_result = CorrelationResult(
                value=correlation_value,
                features=(feature1, feature2)
            )
            nl_explanation = self.nlg.generate_explanation(corr_result)
            
            # Step 4: API-level explanation
            api_explanation = self.explanation_api.explain_correlation(
                correlation_value,
                feature1=feature1,
                feature2=feature2
            )
            
            # Step 5: Layperson explanation if enabled
            explanations = [nl_explanation, api_explanation]
            if self.config.layperson_mode:
                layperson_explanation = self.correlation_explainer.explain_for_layperson(
                    api_explanation
                )
                explanations.append(layperson_explanation)
            
            # Step 6: Add meaning context
            meaning = self.nlg.explain_correlation_meaning(
                f"{feature1} vs {feature2}",
                context={'correlation': correlation_value}
            )
            explanations.append(meaning)
            
            return FeatureResponse(
                success=True,
                data={
                    'interpretation': interpretation,
                    'detailed_explanation': detailed_explanation,
                    'correlation_value': correlation_value,
                    'features': [feature1, feature2]
                },
                explanations=explanations
            )
            
        except Exception as e:
            logger.error(f"Error in explain_specific_correlation: {str(e)}")
            return FeatureResponse(
                success=False,
                error=str(e)
            )
    
    def generate_batch_summary(
        self,
        correlation_results: List[Dict[str, Any]],
        include_recommendations: bool = True
    ) -> FeatureResponse:
        """
        Generate summary for a batch of correlation results.
        
        Args:
            correlation_results: List of correlation analysis results
            include_recommendations: Whether to include analysis recommendations
            
        Returns:
            FeatureResponse with batch summary and explanations
        """
        try:
            # Step 1: Generate batch summary using NLG
            summary = self.nlg.generate_batch_summary(correlation_results)
            
            # Step 2: Extract key patterns
            explanations = [summary]
            
            # Process each result for key insights
            for i, result in enumerate(correlation_results[:self.config.max_correlations_to_explain]):
                if 'correlation_matrix' in result:
                    key_findings = self.explanation_api.get_key_findings(
                        result['correlation_matrix'],
                        feature_names=result.get('feature_names')
                    )
                    explanations.append(f"Dataset {i+1} key findings: {', '.join(key_findings[:3])}")
            
            # Step 3: Generate recommendations if requested
            recommendations = []
            if include_recommendations:
                for result in correlation_results:
                    if 'correlation_matrix' in result:
                        suggestions = self.explanation_api.suggest_further_analysis(
                            result['correlation_matrix'],
                            feature_names=result.get('feature_names')
                        )
                        recommendations.extend(suggestions)
                
                # Deduplicate recommendations
                recommendations = list(set(recommendations))
                explanations.append("Recommended analyses: " + ", ".join(recommendations[:5]))
            
            return FeatureResponse(
                success=True,
                data={
                    'batch_size': len(correlation_results),
                    'summary': summary,
                    'recommendations': recommendations if include_recommendations else []
                },
                explanations=explanations
            )
            
        except Exception as e:
            logger.error(f"Error in generate_batch_summary: {str(e)}")
            return FeatureResponse(
                success=False,
                error=str(e)
            )
