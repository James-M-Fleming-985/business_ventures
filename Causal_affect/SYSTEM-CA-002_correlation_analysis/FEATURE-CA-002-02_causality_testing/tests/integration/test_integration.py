"""
Integration tests for Causality Testing Engine (FEATURE-CA-002-02)

Tests the integration between:
- LAYER-CA-002-02-01: Granger Test
- LAYER-CA-002-02-02: VAR Model
- LAYER-CA-002-02-03: IRF Calculator
- LAYER-CA-002-02-04: Transfer Entropy
- LAYER-CA-002-02-05: DAG Inference
"""

import pytest
import numpy as np
import pandas as pd
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime, timedelta
import networkx as nx

# Assuming these imports from the actual implementation
from feature_integration import CausalityTestingEngine
from layers.granger_test import GrangerCausalityTest
from layers.var_model import VARModel
from layers.irf_calculator import IRFCalculator
from layers.transfer_entropy import TransferEntropyCalculator
from layers.dag_inference import DAGInference


class TestCausalityTestingEngineIntegration:
    """Integration tests for the Causality Testing Engine"""

    @pytest.fixture
    def sample_time_series_data(self):
        """Generate sample multivariate time series data"""
        np.random.seed(42)
        n_samples = 1000
        
        # Create correlated time series
        noise1 = np.random.normal(0, 0.1, n_samples)
        noise2 = np.random.normal(0, 0.1, n_samples)
        noise3 = np.random.normal(0, 0.1, n_samples)
        
        # Series with causal relationships
        series1 = np.zeros(n_samples)
        series2 = np.zeros(n_samples)
        series3 = np.zeros(n_samples)
        
        for t in range(2, n_samples):
            series1[t] = 0.7 * series1[t-1] + 0.2 * series1[t-2] + noise1[t]
            series2[t] = 0.5 * series2[t-1] + 0.3 * series1[t-1] + noise2[t]  # series1 causes series2
            series3[t] = 0.4 * series3[t-1] + 0.2 * series2[t-1] + 0.1 * series1[t-2] + noise3[t]
        
        data = pd.DataFrame({
            'series1': series1,
            'series2': series2,
            'series3': series3
        }, index=pd.date_range('2023-01-01', periods=n_samples, freq='H'))
        
        return data

    @pytest.fixture
    def causality_engine(self):
        """Create a CausalityTestingEngine instance"""
        config = {
            'max_lag': 5,
            'significance_level': 0.05,
            'var_ic': 'aic',
            'irf_periods': 10,
            'entropy_bins': 10,
            'dag_algorithm': 'pc',
            'bootstrap_samples': 100
        }
        return CausalityTestingEngine(config)

    @pytest.fixture
    def mock_granger_layer(self):
        """Mock Granger causality test layer"""
        mock = Mock(spec=GrangerCausalityTest)
        mock.test_causality.return_value = {
            'series1->series2': {'p_value': 0.001, 'f_statistic': 15.2, 'causality': True},
            'series2->series1': {'p_value': 0.45, 'f_statistic': 0.8, 'causality': False},
            'series2->series3': {'p_value': 0.002, 'f_statistic': 12.5, 'causality': True}
        }
        return mock

    def test_complete_causality_pipeline_integration(self, causality_engine, sample_time_series_data):
        """
        Test 1: Complete pipeline from Granger test to DAG inference
        Scenario: Process time series through all layers and verify consistent results
        """
        # Execute complete pipeline
        results = causality_engine.analyze_causality(sample_time_series_data)
        
        # Verify all components were executed
        assert 'granger_results' in results
        assert 'var_model' in results
        assert 'irf_results' in results
        assert 'transfer_entropy' in results
        assert 'causal_dag' in results
        
        # Verify consistency between layers
        granger_pairs = results['granger_results']['significant_pairs']
        dag_edges = list(results['causal_dag'].edges())
        
        # All Granger-significant pairs should be considered in DAG
        for pair in granger_pairs:
            source, target = pair.split('->')
            # Either direct edge or indirect path should exist
            assert (
                (source, target) in dag_edges or
                nx.has_path(results['causal_dag'], source, target)
            )
        
        # Verify VAR model was fitted with appropriate data
        assert results['var_model']['model_order'] > 0
        assert results['var_model']['fitted']
        
        # Verify IRF was calculated for significant relationships
        assert len(results['irf_results']['responses']) > 0
        
        # Verify transfer entropy complements Granger results
        for pair, te_value in results['transfer_entropy'].items():
            if pair in granger_pairs:
                # Significant Granger pairs should have higher transfer entropy
                assert te_value['normalized_te'] > 0.1

    def test_granger_to_var_integration(self, causality_engine, sample_time_series_data, mock_granger_layer):
        """
        Test 2: Integration between Granger test and VAR model
        Scenario: Granger results should inform VAR model variable selection
        """
        with patch.object(causality_engine, 'granger_test', mock_granger_layer):
            # Run Granger test
            granger_results = causality_engine.granger_test.test_causality(sample_time_series_data)
            
            # Identify variables with causal relationships
            causal_vars = set()
            for pair, result in granger_results.items():
                if result['causality']:
                    source, target = pair.split('->')
                    causal_vars.update([source, target])
            
            # Fit VAR model with subset of variables
            var_data = sample_time_series_data[list(causal_vars)]
            var_results = causality_engine.var_model.fit(var_data)
            
            # Verify VAR model uses only causally related variables
            assert set(var_results['variables']) == causal_vars
            assert var_results['model_order'] >= 1
            
            # Verify model quality metrics
            assert 'aic' in var_results['information_criteria']
            assert var_results['residual_correlation'] is not None

    def test_var_to_irf_integration(self, causality_engine, sample_time_series_data):
        """
        Test 3: Integration between VAR model and IRF calculator
        Scenario: IRF should be calculated based on fitted VAR model
        """
        # Fit VAR model
        var_results = causality_engine.var_model.fit(sample_time_series_data)
        
        # Calculate IRF using VAR results
        irf_results = causality_engine.irf_calculator.calculate_irf(
            var_model=var_results['model'],
            periods=10
        )
        
        # Verify IRF dimensions match VAR model
        n_vars = len(sample_time_series_data.columns)
        assert irf_results['irf_matrix'].shape == (10, n_vars, n_vars)
        
        # Verify cumulative IRF is calculated
        assert 'cumulative_irf' in irf_results
        assert irf_results['cumulative_irf'].shape == irf_results['irf_matrix'].shape
        
        # Verify orthogonalized IRF if requested
        oirf_results = causality_engine.irf_calculator.calculate_irf(
            var_model=var_results['model'],
            periods=10,
            orthogonalized=True
        )
        assert 'oirf_matrix' in oirf_results
        
        # Verify confidence intervals
        if 'confidence_intervals' in irf_results:
            assert irf_results['confidence_intervals']['lower'].shape == irf_results['irf_matrix'].shape
            assert irf_results['confidence_intervals']['upper'].shape == irf_results['irf_matrix'].shape

    def test_transfer_entropy_dag_integration(self, causality_engine, sample_time_series_data):
        """
        Test 4: Integration between Transfer Entropy and DAG Inference
        Scenario: Transfer entropy results should inform DAG structure learning
        """
        # Calculate transfer entropy for all pairs
        te_results = {}
        columns = sample_time_series_data.columns
        
        for i, source in enumerate(columns):
            for j, target in enumerate(columns):
                if i != j:
                    pair_key = f"{source}->{target}"
                    te_results[pair_key] = causality_engine.transfer_entropy.calculate_te(
                        source=sample_time_series_data[source].values,
                        target=sample_time_series_data[target].values,
                        lag=1
                    )
        
        # Build adjacency matrix from transfer entropy
        n_vars = len(columns)
        te_matrix = np.zeros((n_vars, n_vars))
        
        for i, source in enumerate(columns):
            for j, target in enumerate(columns):
                if i != j:
                    pair_key = f"{source}->{target}"
                    te_matrix[i, j] = te_results[pair_key]['transfer_entropy']
        
        # Infer DAG structure using transfer entropy as weights
        dag_results = causality_engine.dag_inference.infer_structure(
            data=sample_time_series_data,
            prior_knowledge={'edge_weights': te_matrix}
        )
        
        # Verify DAG properties
        assert nx.is_directed_acyclic_graph(dag_results['graph'])
        assert set(dag_results['graph'].nodes()) == set(columns)
        
        # Verify high TE pairs are more likely to be edges
        edges = list(dag_results['graph'].edges())
        edge_te_values = []
        non_edge_te_values = []
        
        for i, source in enumerate(columns):
            for j, target in enumerate(columns):
                if i != j:
                    te_value = te_matrix[i, j]
                    if (source, target) in edges:
                        edge_te_values.append(te_value)
                    else:
                        non_edge_te_values.append(te_value)
        
        # Edges should have higher average TE
        if edge_te_values and non_edge_te_values:
            assert np.mean(edge_te_values) > np.mean(non_edge_te_values)

    def test_multi_layer_error_propagation(self, causality_engine):
        """
        Test 5: Error handling and propagation across layers
        Scenario: Errors in one layer should be handled gracefully
        """
        # Test with invalid data (too short for causality testing)
        short_data = pd.DataFrame({
            'x': [1, 2, 3],
            'y': [4, 5, 6]
        })
        
        with pytest.raises(ValueError, match="Insufficient data"):
            causality_engine.analyze_causality(short_data)
        
        # Test with missing values
        data_with_nan = pd.DataFrame({
            'x': [1, 2, np.nan, 4, 5, 6, 7, 8, 9, 10],
            'y': [1, 2, 3, 4, np.nan, 6, 7, 8, 9, 10]
        })
        
        results = causality_engine.analyze_causality(
            data_with_nan, 
            handle_missing='interpolate'
        )
        
        # Should complete analysis with interpolated data
        assert results is not None
        assert 'warnings' in results
        assert any('missing values' in w for w in results['warnings'])
        
        # Test with single variable (no causality possible)
        single_var_data = pd.DataFrame({
            'x': np.random.randn(100)
        })
        
        with pytest.raises(ValueError, match="At least two variables required"):
            causality_engine.analyze_causality(single_var_data)
        
        # Test VAR model failure cascading to IRF
        with patch.object(causality_engine.var_model, 'fit') as mock_var:
            mock_var.side_effect = Exception("VAR fitting failed")
            
            results = causality_engine.analyze_causality(
                sample_time_series_data,
                continue_on_error=True
            )
            
            # Should have partial results
            assert results['granger_results'] is not None
            assert results['var_model'] is None
            assert results['irf_results'] is None  # Depends on VAR
            assert 'errors' in results
            assert any('VAR' in str(e) for e in results['errors'])

    def test_performance_with_large_dataset(self, causality_engine):
        """
        Test 6: Performance and scalability with larger datasets
        """
        # Generate larger dataset
        n_samples = 5000
        n_variables = 10
        
        data = pd.DataFrame(
            np.random.randn(n_samples, n_variables),
            columns=[f'var_{i}' for i in range(n_variables)],
            index=pd.date_range('2020-01-01', periods=n_samples, freq='H')
        )
        
        # Add some causal structure
        for i in range(1, n_variables):
            data[f'var_{i}'] += 0.3 * data[f'var_{i-1}'].shift(1).fillna(0)
        
        import time
        start_time = time.time()
        
        results = causality_engine.analyze_causality(
            data,
            subset_analysis=True,  # Use subset for efficiency
            max_pairs=20  # Limit number of pairs tested
        )
        
        execution_time = time.time() - start_time
        
        # Should complete within reasonable time
        assert execution_time < 60  # 60 seconds max
        
        # Verify subset analysis worked
        assert 'subset_info' in results
        assert results['subset_info']['total_pairs'] == n_variables * (n_variables - 1)
        assert results['subset_info']['tested_pairs'] <= 20

    def test_configuration_propagation(self, sample_time_series_data):
        """
        Test 7: Configuration propagation across layers
        """
        # Custom configuration
        custom_config = {
            'max_lag': 3,
            'significance_level': 0.01,
            'var_ic': 'bic',
            'irf_periods': 20,
            'entropy_bins': 15,
            'dag_algorithm': 'ges',
            'bootstrap_samples': 200,
            'parallel_processing': True,
            'n_jobs': 4
        }
        
        engine = CausalityTestingEngine(custom_config)
        results = engine.analyze_causality(sample_time_series_data)
        
        # Verify configurations were applied
        assert results['config']['max_lag'] == 3
        assert results['config']['significance_level'] == 0.01
        
        # Verify VAR used BIC
        assert results['var_model']['ic_used'] == 'bic'
        
        # Verify IRF periods
        assert results['irf_results']['periods'] == 20
        
        # Verify parallel processing was used where applicable
        if 'execution_stats' in results:
            assert results['execution_stats']['parallel'] == True
            assert results['execution_stats']['n_jobs'] == 4

    def test_circular_dependency_detection(self, causality_engine):
        """
        Test 8: Detection and handling of circular dependencies
        """
        # Create data with potential circular causality
        n_samples = 500
        t = np.arange(n_samples)
        
        # Circular relationship: A -> B -> C -> A
        A = np.sin(0.1 * t) + np.random.normal(0, 0.1, n_samples)
        B = np.roll(A, 5) + np.random.normal(0, 0.1, n_samples)  # B follows A
        C = np.roll(B, 5) + np.random.normal(0, 0.1, n_samples)  # C follows B
        A[10:] += 0.3 * np.roll(C, 5)[10:]  # A follows C (creating circle)
        
        circular_data = pd.DataFrame({
            'A': A,
            'B': B,
            'C': C
        })
        
        results = causality_engine.analyze_causality(circular_data)
        
        # DAG inference should break the cycle
        assert nx.is_directed_acyclic_graph(results['causal_dag'])
        
        # Should detect and report the circular dependency
        assert 'circular_dependencies' in results
        if results['circular_dependencies']:
            assert len(results['circular_dependencies']) > 0
            # Verify the circular path was identified
            circular_paths = results['circular_dependencies']
            assert any(set(['A', 'B', 'C']).issubset(set(path)) for path in circular_paths)

    def test_incremental_analysis(self, causality_engine, sample_time_series_data):
        """
        Test 9: Incremental analysis with new data
        """
        # Split data into initial and new batches
        split_point = len(sample_time_series_data) // 2
        initial_data = sample_time_series_data.iloc[:split_point]
        new_data = sample_time_series_data.iloc[split_point:]
        
        # Initial analysis
        initial_results = causality_engine.analyze_causality(initial_data)
        
        # Incremental update with new data
        updated_results = causality_engine.update_analysis(
            previous_results=initial_results,
            new_data=new_data
        )
        
        # Verify incremental update
        assert updated_results['data_info']['total_samples'] == len(sample_time_series_data)
        assert updated_results['data_info']['incremental_update'] == True
        
        # Results should potentially be different (more accurate with more data)
        # But structure should be similar
        initial_edges = set(initial_results['causal_dag'].edges())
        updated_edges = set(updated_results['causal_dag'].edges())
        
        # Jaccard similarity should be reasonably high
        if initial_edges or updated_edges:
            jaccard = len(initial_edges & updated_edges) / len(initial_edges | updated_edges)
            assert jaccard > 0.5  # At least 50% similarity

    def test_layer_caching_integration(self, causality_engine, sample_time_series_data):
        """
        Test 10: Caching mechanisms between layers
        """
        # Enable caching
        causality_engine.enable_caching()
        
        # First run - should compute everything
        start_time = time.time()
        results1 = causality_engine.analyze_causality(sample_time_series_data)
        first_run_time = time.time() - start_time
        
        # Second run with same data - should use cache
        start_time = time.time()
        results2 = causality_engine.analyze_causality(sample_time_series_data)
        second_run_time = time.time() - start_time
        
        # Second run should be significantly faster
        assert second_run_time < first_run_time * 0.5
        
        # Results should be identical
        assert results1['granger_results'] == results2['granger_results']
        
        # Verify cache statistics
        cache_stats = causality_engine.get_cache_stats()
        assert cache_stats['hits'] > 0
        assert cache_stats['hit_rate'] > 0.5
        
        # Modify data slightly - should invalidate relevant caches
        modified_data = sample_time_series_data.copy()
        modified_data.iloc[-1, 0] += 0.1
        
        results3 = causality_engine.analyze_causality(modified_data)
        
        # Results should be different
        assert results3['granger_results'] != results1['granger_results']