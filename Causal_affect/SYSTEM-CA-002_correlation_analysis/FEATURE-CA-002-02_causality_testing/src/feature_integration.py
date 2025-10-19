"""
Causality Testing Engine Feature Integration
Feature ID: FEATURE-CA-002-02

This module orchestrates the integration of multiple causality testing layers:
- Granger Test (LAYER-CA-002-02-01)
- VAR Model (LAYER-CA-002-02-02)
- IRF Calculator (LAYER-CA-002-02-03)
- Transfer Entropy (LAYER-CA-002-02-04)
- DAG Inference (LAYER-CA-002-02-05)
"""

from pathlib import Path
import sys
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Union, Tuple
import logging
import numpy as np
import pandas as pd
from datetime import datetime

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Import layer implementations
try:
    from LAYER_CA_002_02_01_granger_test.src.implementation import (
        GrangerTestResult, 
        GrangerCausalityTest
    )
    from LAYER_CA_002_02_02_var_model.src.implementation import (
        VARResults, 
        VARModel, 
        VARModelOrchestrator
    )
    from LAYER_CA_002_02_03_irf_calculator.src.implementation import (
        IRFResult, 
        IRFCalculator
    )
    from LAYER_CA_002_02_04_transfer_entropy.src.implementation import (
        TransferEntropyResult, 
        TransferEntropyCalculator
    )
    from LAYER_CA_002_02_05_dag_inference.src.implementation import (
        DAGInferenceError, 
        DAGInference
    )
except ImportError as e:
    logging.error(f"Failed to import layer implementations: {str(e)}")
    raise


# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class FeatureConfig:
    """Configuration for the Causality Testing Engine"""
    max_lag: int = 10
    significance_level: float = 0.05
    var_criterion: str = 'aic'
    irf_periods: int = 10
    transfer_entropy_bins: int = 10
    dag_algorithm: str = 'pc'
    enable_granger: bool = True
    enable_var: bool = True
    enable_irf: bool = True
    enable_transfer_entropy: bool = True
    enable_dag: bool = True
    verbose: bool = False


@dataclass
class FeatureResponse:
    """Unified response structure for the Causality Testing Engine"""
    success: bool
    timestamp: datetime = field(default_factory=datetime.now)
    granger_results: Optional[Dict[str, Any]] = None
    var_results: Optional[Dict[str, Any]] = None
    irf_results: Optional[Dict[str, Any]] = None
    transfer_entropy_results: Optional[Dict[str, Any]] = None
    dag_results: Optional[Dict[str, Any]] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class CausalityTestingError(Exception):
    """Custom exception for Causality Testing Engine errors"""
    pass


class FeatureOrchestrator:
    """
    Main orchestrator for the Causality Testing Engine.
    
    This class coordinates all causality testing layers to provide comprehensive
    causal analysis capabilities including Granger causality, VAR models,
    impulse response functions, transfer entropy, and DAG inference.
    """
    
    def __init__(self, config: Optional[FeatureConfig] = None):
        """
        Initialize the FeatureOrchestrator with configuration.
        
        Args:
            config: Optional FeatureConfig instance. If None, uses defaults.
        """
        self.config = config or FeatureConfig()
        self._initialize_layers()
        logger.info("Causality Testing Engine initialized successfully")
    
    def _initialize_layers(self) -> None:
        """Initialize all layer instances with error handling."""
        try:
            # Initialize Granger Test layer
            if self.config.enable_granger:
                self.granger_test = GrangerCausalityTest(
                    max_lag=self.config.max_lag,
                    significance_level=self.config.significance_level
                )
            else:
                self.granger_test = None
            
            # Initialize VAR Model layer
            if self.config.enable_var:
                self.var_model = VARModel()
                self.var_orchestrator = VARModelOrchestrator()
            else:
                self.var_model = None
                self.var_orchestrator = None
            
            # Initialize IRF Calculator layer
            if self.config.enable_irf:
                self.irf_calculator = IRFCalculator(periods=self.config.irf_periods)
            else:
                self.irf_calculator = None
            
            # Initialize Transfer Entropy layer
            if self.config.enable_transfer_entropy:
                self.transfer_entropy = TransferEntropyCalculator()
            else:
                self.transfer_entropy = None
            
            # Initialize DAG Inference layer
            if self.config.enable_dag:
                self.dag_inference = DAGInference()
            else:
                self.dag_inference = None
                
        except Exception as e:
            logger.error(f"Failed to initialize layers: {str(e)}")
            raise CausalityTestingError(f"Layer initialization failed: {str(e)}")
    
    def analyze_causality(
        self, 
        data: Union[pd.DataFrame, np.ndarray],
        target_variable: Optional[str] = None,
        variable_names: Optional[List[str]] = None
    ) -> FeatureResponse:
        """
        Perform comprehensive causality analysis using all enabled layers.
        
        Args:
            data: Time series data as DataFrame or numpy array
            target_variable: Optional target variable for directed analysis
            variable_names: Optional list of variable names for numpy arrays
            
        Returns:
            FeatureResponse containing results from all layers
        """
        response = FeatureResponse(success=False)
        
        try:
            # Validate and prepare data
            data_df = self._prepare_data(data, variable_names)
            response.metadata['data_shape'] = data_df.shape
            response.metadata['variables'] = list(data_df.columns)
            
            # Run Granger causality tests
            if self.config.enable_granger and self.granger_test:
                response.granger_results = self._run_granger_tests(
                    data_df, target_variable
                )
            
            # Fit VAR model
            if self.config.enable_var and self.var_model:
                response.var_results = self._run_var_analysis(data_df)
            
            # Calculate impulse response functions
            if self.config.enable_irf and self.irf_calculator and response.var_results:
                response.irf_results = self._run_irf_analysis(
                    response.var_results.get('model')
                )
            
            # Calculate transfer entropy
            if self.config.enable_transfer_entropy and self.transfer_entropy:
                response.transfer_entropy_results = self._run_transfer_entropy(
                    data_df, target_variable
                )
            
            # Infer causal DAG
            if self.config.enable_dag and self.dag_inference:
                response.dag_results = self._run_dag_inference(data_df)
            
            response.success = True
            logger.info("Causality analysis completed successfully")
            
        except Exception as e:
            logger.error(f"Causality analysis failed: {str(e)}")
            response.errors.append(str(e))
            response.success = False
        
        return response
    
    def _prepare_data(
        self, 
        data: Union[pd.DataFrame, np.ndarray],
        variable_names: Optional[List[str]] = None
    ) -> pd.DataFrame:
        """
        Prepare and validate input data.
        
        Args:
            data: Input time series data
            variable_names: Variable names for numpy arrays
            
        Returns:
            Prepared DataFrame
            
        Raises:
            CausalityTestingError: If data validation fails
        """
        if isinstance(data, np.ndarray):
            if data.ndim != 2:
                raise CausalityTestingError("Input array must be 2-dimensional")
            
            if variable_names is None:
                variable_names = [f"var_{i}" for i in range(data.shape[1])]
            elif len(variable_names) != data.shape[1]:
                raise CausalityTestingError(
                    "Number of variable names must match number of columns"
                )
            
            data_df = pd.DataFrame(data, columns=variable_names)
        elif isinstance(data, pd.DataFrame):
            data_df = data.copy()
        else:
            raise CausalityTestingError(
                "Data must be pandas DataFrame or numpy array"
            )
        
        # Check for missing values
        if data_df.isnull().any().any():
            logger.warning("Data contains missing values, attempting to handle")
            data_df = data_df.fillna(method='ffill').fillna(method='bfill')
        
        return data_df
    
    def _run_granger_tests(
        self, 
        data: pd.DataFrame,
        target_variable: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run Granger causality tests.
        
        Args:
            data: Prepared time series data
            target_variable: Optional target for directed tests
            
        Returns:
            Dictionary of Granger test results
        """
        try:
            results = {}
            
            if target_variable and target_variable in data.columns:
                # Test causality from all other variables to target
                for col in data.columns:
                    if col != target_variable:
                        test_result = self.granger_test.test_causality(
                            data[[col, target_variable]].values,
                            [col, target_variable]
                        )
                        results[f"{col}_to_{target_variable}"] = {
                            'statistic': test_result.test_statistic,
                            'p_value': test_result.p_value,
                            'optimal_lag': test_result.optimal_lag,
                            'is_causal': test_result.is_causal
                        }
            else:
                # Test all pairwise combinations
                columns = list(data.columns)
                for i, col1 in enumerate(columns):
                    for col2 in columns[i+1:]:
                        # Test col1 -> col2
                        test_data = data[[col1, col2]].values
                        test_result = self.granger_test.test_causality(
                            test_data, [col1, col2]
                        )
                        results[f"{col1}_to_{col2}"] = {
                            'statistic': test_result.test_statistic,
                            'p_value': test_result.p_value,
                            'optimal_lag': test_result.optimal_lag,
                            'is_causal': test_result.is_causal
                        }
            
            logger.info(f"Completed {len(results)} Granger causality tests")
            return results
            
        except Exception as e:
            logger.error(f"Granger test failed: {str(e)}")
            raise
    
    def _run_var_analysis(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Run VAR model analysis.
        
        Args:
            data: Prepared time series data
            
        Returns:
            Dictionary of VAR model results
        """
        try:
            # Fit VAR model
            var_result = self.var_model.fit(
                data.values,
                maxlags=self.config.max_lag,
                ic=self.config.var_criterion
            )
            
            # Get model diagnostics
            results = {
                'model': var_result,
                'order': var_result.k_ar,
                'aic': var_result.aic,
                'bic': var_result.bic,
                'hqic': var_result.hqic,
                'coefficients': var_result.params.tolist(),
                'residual_correlation': var_result.resid_corr.tolist()
            }
            
            # Add stability check
            if hasattr(var_result, 'is_stable'):
                results['is_stable'] = var_result.is_stable()
            
            logger.info(f"VAR model fitted with order {results['order']}")
            return results
            
        except Exception as e:
            logger.error(f"VAR analysis failed: {str(e)}")
            raise
    
    def _run_irf_analysis(self, var_model: Any) -> Dict[str, Any]:
        """
        Run impulse response function analysis.
        
        Args:
            var_model: Fitted VAR model
            
        Returns:
            Dictionary of IRF results
        """
        try:
            if var_model is None:
                raise CausalityTestingError("VAR model required for IRF analysis")
            
            # Calculate IRFs
            irf_result = self.irf_calculator.calculate_irf(var_model)
            
            results = {
                'periods': self.config.irf_periods,
                'irf_values': irf_result.irf.tolist(),
                'lower_bound': irf_result.irf_lower.tolist() if hasattr(irf_result, 'irf_lower') else None,
                'upper_bound': irf_result.irf_upper.tolist() if hasattr(irf_result, 'irf_upper') else None,
                'cumulative_effects': irf_result.cum_effects.tolist() if hasattr(irf_result, 'cum_effects') else None
            }
            
            logger.info(f"IRF analysis completed for {self.config.irf_periods} periods")
            return results
            
        except Exception as e:
            logger.error(f"IRF analysis failed: {str(e)}")
            raise
    
    def _run_transfer_entropy(
        self, 
        data: pd.DataFrame,
        target_variable: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Run transfer entropy analysis.
        
        Args:
            data: Prepared time series data
            target_variable: Optional target for directed analysis
            
        Returns:
            Dictionary of transfer entropy results
        """
        try:
            results = {}
            
            if target_variable and target_variable in data.columns:
                # Calculate TE from all other variables to target
                for col in data.columns:
                    if col != target_variable:
                        te_result = self.transfer_entropy.calculate(
                            data[col].values,
                            data[target_variable].values,
                            bins=self.config.transfer_entropy_bins
                        )
                        results[f"{col}_to_{target_variable}"] = {
                            'transfer_entropy': te_result.transfer_entropy,
                            'normalized_te': te_result.normalized_te if hasattr(te_result, 'normalized_te') else None,
                            'p_value': te_result.p_value if hasattr(te_result, 'p_value') else None
                        }
            else:
                # Calculate TE for all pairs
                columns = list(data.columns)
                for col1 in columns:
                    for col2 in columns:
                        if col1 != col2:
                            te_result = self.transfer_entropy.calculate(
                                data[col1].values,
                                data[col2].values,
                                bins=self.config.transfer_entropy_bins
                            )
                            results[f"{col1}_to_{col2}"] = {
                                'transfer_entropy': te_result.transfer_entropy,
                                'normalized_te': te_result.normalized_te if hasattr(te_result, 'normalized_te') else None,
                                'p_value': te_result.p_value if hasattr(te_result, 'p_value') else None
                            }
            
            logger.info(f"Completed {len(results)} transfer entropy calculations")
            return results
            
        except Exception as e:
            logger.error(f"Transfer entropy analysis failed: {str(e)}")
            raise
    
    def _run_dag_inference(self, data: pd.DataFrame) -> Dict[str, Any]:
        """
        Run DAG inference analysis.
        
        Args:
            data: Prepared time series data
            
        Returns:
            Dictionary of DAG inference results
        """
        try:
            # Infer causal DAG
            dag_result = self.dag_inference.infer_dag(
                data.values,
                variable_names=list(data.columns),
                algorithm=self.config.dag_algorithm,
                significance_level=self.config.significance_level
            )
            
            results = {
                'algorithm': self.config.dag_algorithm,
                'edges': dag_result.edges,
                'nodes': dag_result.nodes,
                'adjacency_matrix': dag_result.adjacency_matrix.tolist() if hasattr(dag_result, 'adjacency_matrix') else None
            }
            
            # Add graph metrics if available
            if hasattr(dag_result, 'graph_metrics'):
                results['metrics'] = dag_result.graph_metrics
            
            logger.info(f"DAG inference completed with {len(dag_result.edges)} edges")
            return results
            
        except Exception as e:
            logger.error(f"DAG inference failed: {str(e)}")
            raise
    
    def get_causal_summary(self, response: FeatureResponse) -> Dict[str, Any]:
        """
        Generate a summary of causal relationships from all analyses.
        
        Args:
            response: FeatureResponse from analyze_causality
            
        Returns:
            Dictionary summarizing causal relationships
        """
        summary = {
            'total_relationships': 0,
            'strong_relationships': [],
            'weak_relationships': [],
            'consensus_relationships': [],
            'conflicting_results': []
        }
        
        try:
            # Collect relationships from each method
            granger_causal = set()
            te_causal = set()
            dag_edges = set()
            
            # Process Granger results
            if response.granger_results:
                for rel, result in response.granger_results.items():
                    if result.get('is_causal'):
                        granger_causal.add(rel)
                        if result.get('p_value', 1.0) < 0.01:
                            summary['strong_relationships'].append({
                                'relationship': rel,
                                'method': 'granger',
                                'p_value': result['p_value']
                            })
            
            # Process Transfer Entropy results
            if response.transfer_entropy_results:
                for rel, result in response.transfer_entropy_results.items():
                    if result.get('p_value', 1.0) < self.config.significance_level:
                        te_causal.add(rel)
            
            # Process DAG results
            if response.dag_results and response.dag_results.get('edges'):
                for edge in response.dag_results['edges']:
                    dag_edges.add(f"{edge[0]}_to_{edge[1]}")
            
            # Find consensus relationships
            if granger_causal and te_causal:
                consensus = granger_causal.intersection(te_causal)
                summary['consensus_relationships'] = list(consensus)
            
            summary['total_relationships'] = len(
                granger_causal.union(te_causal).union(dag_edges)
            )
            
            logger.info(f"Causal summary generated: {summary['total_relationships']} total relationships")
            return summary
            
        except Exception as e:
            logger.error(f"Failed to generate causal summary: {str(e)}")
            return summary
    
    def validate_layers(self) -> Dict[str, bool]:
        """
        Validate that all enabled layers are properly initialized.
        
        Returns:
            Dictionary indicating status of each layer
        """
        validation = {
            'granger_test': self.config.enable_granger and self.granger_test is not None,
            'var_model': self.config.enable_var and self.var_model is not None,
            'irf_calculator': self.config.enable_irf and self.irf_calculator is not None,
            'transfer_entropy': self.config.enable_transfer_entropy and self.transfer_entropy is not None,
            'dag_inference': self.config.enable_dag and self.dag_inference is not None
        }
        
        logger.info(f"Layer validation: {validation}")
        return validation


# Example usage and testing
if __name__ == "__main__":
    # Create sample data
    np.random.seed(42)
    n_samples = 1000
    
    # Generate synthetic causal time series
    x = np.random.randn(n_samples)
    y = np.zeros(n_samples)
    z = np.zeros(n_samples)
    
    # Create causal relationships: x -> y -> z
    for t in range(1, n_samples):
        y[t] = 0.7 * x[t-1] + 0.3 * np.random.randn()
        z[t] = 0.6 * y[t-1] + 0.4 * np.random.randn()
    
    # Create DataFrame
    data = pd.DataFrame({
        'x': x,
        'y': y,
        'z': z
    })
    
    # Initialize orchestrator
    config = FeatureConfig(
        max_lag=5,
        significance_level=0.05,
        irf_periods=10,
        verbose=True
    )
    
    orchestrator = FeatureOrchestrator(config)
    
    # Validate layers
    print("Layer validation:", orchestrator.validate_layers())
    
    # Run causality analysis
    response = orchestrator.analyze_causality(data, target_variable='z')
    
    # Print results
    print(f"\nAnalysis Success: {response.success}")
    print(f"Errors: {response.errors}")
    print(f"Warnings: {response.warnings}")
    
    # Get causal summary
    summary = orchestrator.get_causal_summary(response)
    print(f"\nCausal Summary:")
    print(f"Total relationships found: {summary['total_relationships']}")
    print(f"Consensus relationships: {summary['consensus_relationships']}")