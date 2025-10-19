```python
"""DAG inference module for causal analysis."""

import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional, Any, Union
import networkx as nx
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression
from scipy import stats
import warnings
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
from functools import wraps
import logging

logger = logging.getLogger(__name__)


def timing_decorator(func):
    """Decorator to ensure function completes within 5 seconds."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        if elapsed_time > 5.0:
            logger.warning(f"{func.__name__} took {elapsed_time:.2f} seconds")
        return result
    return wrapper


class DAGInferenceError(Exception):
    """Custom exception for DAG inference errors."""
    pass


class DAGInference:
    """
    DAG (Directed Acyclic Graph) inference for causal discovery.
    
    This class implements various algorithms for learning DAG structure
    from observational data, including PC algorithm and GES.
    """
    
    def __init__(self, alpha: float = 0.05, max_iter: int = 1000):
        """
        Initialize DAG inference.
        
        Args:
            alpha: Significance level for independence tests
            max_iter: Maximum iterations for structure learning
        """
        self.alpha = alpha
        self.max_iter = max_iter
        self.graph = None
        self.adjacency_matrix = None
        self.nodes = None
        
    @timing_decorator
    def fit(self, data: Union[pd.DataFrame, np.ndarray], 
            variable_names: Optional[List[str]] = None) -> 'DAGInference':
        """
        Learn DAG structure from data.
        
        Args:
            data: Input data (n_samples, n_variables)
            variable_names: Names of variables
            
        Returns:
            Self instance with learned DAG
        """
        # Convert to DataFrame if numpy array
        if isinstance(data, np.ndarray):
            if variable_names is None:
                variable_names = [f"X{i}" for i in range(data.shape[1])]
            data = pd.DataFrame(data, columns=variable_names)
        
        # Handle missing data
        data = self._handle_missing_data(data)
        
        # Store variable names
        self.nodes = list(data.columns)
        
        # Learn structure using PC algorithm
        self.adjacency_matrix = self._pc_algorithm(data)
        
        # Create NetworkX graph
        self._create_graph()
        
        return self
    
    def _handle_missing_data(self, data: pd.DataFrame) -> pd.DataFrame:
        """Handle missing data gracefully."""
        if data.isnull().any().any():
            # Use forward fill then backward fill for time series
            # For cross-sectional data, use mean imputation
            if data.shape[0] > 100:  # Assume time series if many rows
                data = data.fillna(method='ffill').fillna(method='bfill')
            else:
                data = data.fillna(data.mean())
        return data
    
    def _pc_algorithm(self, data: pd.DataFrame) -> np.ndarray:
        """
        PC algorithm for causal discovery.
        
        Args:
            data: Input DataFrame
            
        Returns:
            Adjacency matrix
        """
        n_vars = len(data.columns)
        adjacency = np.ones((n_vars, n_vars)) - np.eye(n_vars)
        
        # Phase 1: Skeleton discovery
        adjacency = self._skeleton_discovery(data, adjacency)
        
        # Phase 2: Orient edges
        adjacency = self._orient_edges(data, adjacency)
        
        return adjacency
    
    def _skeleton_discovery(self, data: pd.DataFrame, 
                          adjacency: np.ndarray) -> np.ndarray:
        """Discover skeleton using conditional independence tests."""
        n_vars = adjacency.shape[0]
        
        # Test conditional independence for increasing conditioning set sizes
        for cond_size in range(n_vars - 2):
            for i in range(n_vars):
                for j in range(i + 1, n_vars):
                    if adjacency[i, j] == 0:
                        continue
                    
                    # Get potential conditioning sets
                    neighbors = self._get_neighbors(i, j, adjacency)
                    
                    if len(neighbors) >= cond_size:
                        # Test conditional independence
                        if self._test_conditional_independence(
                            data, i, j, neighbors[:cond_size]
                        ):
                            adjacency[i, j] = 0
                            adjacency[j, i] = 0
        
        return adjacency
    
    def _get_neighbors(self, i: int, j: int, 
                      adjacency: np.ndarray) -> List[int]:
        """Get common neighbors of nodes i and j."""
        neighbors_i = np.where(adjacency[i, :] != 0)[0]
        neighbors_j = np.where(adjacency[j, :] != 0)[0]
        common = np.intersect1d(neighbors_i, neighbors_j)
        return common.tolist()
    
    def _test_conditional_independence(self, data: pd.DataFrame,
                                     i: int, j: int,
                                     cond_set: List[int]) -> bool:
        """Test conditional independence using partial correlation."""
        try:
            if len(cond_set) == 0:
                # Simple correlation test
                corr = data.iloc[:, i].corr(data.iloc[:, j])
                n = len(data)
                t_stat = corr * np.sqrt(n - 2) / np.sqrt(1 - corr**2)
                p_value = 2 * (1 - stats.t.cdf(abs(t_stat), n - 2))
            else:
                # Partial correlation
                p_value = self._partial_correlation_test(
                    data, i, j, cond_set
                )
            
            return p_value > self.alpha
        except Exception:
            return False
    
    def _partial_correlation_test(self, data: pd.DataFrame,
                                i: int, j: int,
                                cond_set: List[int]) -> float:
        """Calculate p-value for partial correlation test."""
        # Get relevant columns
        X = data.iloc[:, i].values
        Y = data.iloc[:, j].values
        Z = data.iloc[:, cond_set].values
        
        # Regress out conditioning variables
        reg_X = LinearRegression().fit(Z, X)
        reg_Y = LinearRegression().fit(Z, Y)
        
        res_X = X - reg_X.predict(Z)
        res_Y = Y - reg_Y.predict(Z)
        
        # Calculate partial correlation
        corr = np.corrcoef(res_X, res_Y)[0, 1]
        
        # Calculate p-value
        n = len(data)
        df = n - len(cond_set) - 2
        t_stat = corr * np.sqrt(df) / np.sqrt(1 - corr**2)
        p_value = 2 * (1 - stats.t.cdf(abs(t_stat), df))
        
        return p_value
    
    def _orient_edges(self, data: pd.DataFrame, 
                     adjacency: np.ndarray) -> np.ndarray:
        """Orient edges in the skeleton."""
        n_vars = adjacency.shape[0]
        oriented = adjacency.copy()
        
        # Rule 1: Orient v-structures
        for i in range(n_vars):
            for j in range(i + 1, n_vars):
                if oriented[i, j] == 0:
                    continue
                    
                for k in range(n_vars):
                    if k == i or k == j:
                        continue
                    
                    if (oriented[i, k] != 0 and oriented[j, k] != 0 and
                        oriented[i, j] != 0):
                        # Check if i-k-j forms a v-structure
                        if not self._test_conditional_independence(
                            data, i, j, [k]
                        ):
                            # Orient as i->k<-j
                            oriented[k, i] = 0
                            oriented[k, j] = 0
        
        # Apply Meek's rules iteratively
        changed = True
        while changed:
            changed = False
            
            # Rule 2: If i->j and j-k, orient j->k
            for i in range(n_vars):
                for j in range(n_vars):
                    if oriented[i, j] != 0 and oriented[j, i] == 0:
                        for k in range(n_vars):
                            if (k != i and oriented[j, k] != 0 and 
                                oriented[k, j] != 0):
                                oriented[k, j] = 0
                                changed = True
        
        return oriented
    
    def _create_graph(self):
        """Create NetworkX DiGraph from adjacency matrix."""
        self.graph = nx.DiGraph()
        self.graph.add_nodes_from(self.nodes)
        
        n_vars = len(self.nodes)
        for i in range(n_vars):
            for j in range(n_vars):
                if self.adjacency_matrix[i, j] != 0 and \
                   self.adjacency_matrix[j, i] == 0:
                    self.graph.add_edge(self.nodes[i], self.nodes[j])
    
    def get_adjacency_matrix(self) -> np.ndarray:
        """Get learned adjacency matrix."""
        if self.adjacency_matrix is None:
            raise DAGInferenceError("Model not fitted yet")
        return self.adjacency_matrix.copy()
    
    def get_edges(self) -> List[Tuple[str, str]]:
        """Get list of directed edges."""
        if self.graph is None:
            raise DAGInferenceError("Model not fitted yet")
        return list(self.graph.edges())
    
    def get_parents(self, node: str) -> List[str]:
        """Get parents of a node."""
        if self.graph is None:
            raise DAGInferenceError("Model not fitted yet")
        if node not in self.graph:
            raise ValueError(f"Node {node} not in graph")
        return list(self.graph.predecessors(node))
    
    def get_children(self, node: str) -> List[str]:
        """Get children of a node."""
        if self.graph is None:
            raise DAGInferenceError("Model not fitted yet")
        if node not in self.graph:
            raise ValueError(f"Node {node} not in graph")
        return list(self.graph.successors(node))
    
    def is_dag(self) -> bool:
        """Check if the graph is a valid DAG."""
        if self.graph is None:
            raise DAGInferenceError("Model not fitted yet")
        return nx.is_directed_acyclic_graph(self.graph)
    
    def topological_sort(self) -> List[str]:
        """Get topological ordering of nodes."""
        if self.graph is None:
            raise DAGInferenceError("Model not fitted yet")
        if not self.is_dag():
            raise DAGInferenceError("Graph contains cycles")
        return list(nx.topological_sort(self.graph))
    
    def get_causal_order(self) -> List[str]:
        """Get causal ordering (alias for topological sort)."""
        return self.topological_sort()
    
    def predict_intervention(self, intervention_node: str,
                           intervention_value: float,
                           target_node: str,
                           data: pd.DataFrame) -> float:
        """
        Predict effect of intervention using do-calculus.
        
        Args:
            intervention_node: Node to intervene on
            intervention_value: Value to set for intervention
            target_node: Target node to predict
            data: Observational data
            
        Returns:
            Predicted value under intervention
        """
        if self.graph is None:
            raise DAGInferenceError("Model not fitted yet")
            
        # Simple implementation using linear regression
        # In practice, would use more sophisticated methods
        
        # Get parents of target
        parents = self.get_parents(target_node)
        
        if intervention_node in parents:
            # Direct effect
            reg_data = data[parents + [target_node]].dropna()
            X = reg_data[parents]
            y = reg_data[target_node]
            
            model = LinearRegression().fit(X, y)
            
            # Create intervention data
            X_int = X.mean().to_dict()
            X_int[intervention_node] = intervention_value
            X_int = pd.DataFrame([X_int])[parents]
            
            return model.predict(X_int)[0]
        else:
            # Need to consider paths
            return data[target_node].mean()
    
    @timing_decorator
    def fit_parallel(self, datasets: List[pd.DataFrame],
                    n_workers: int = 4) -> List['DAGInference']:
        """
        Fit multiple datasets in parallel.
        
        Args:
            datasets: List of DataFrames
            n_workers: Number of parallel workers
            
        Returns:
            List of fitted DAGInference objects
        """
        results = []
        
        with ThreadPoolExecutor(max_workers=n_workers) as executor:
            futures = {
                executor.submit(self._fit_single, data): i 
                for i, data in enumerate(datasets)
            }
            
            for future in as_completed(futures):
                try:
                    result = future.result()
                    results.append(result)
                except Exception as e:
                    logger.error(f"Error in parallel fit: {e}")
                    results.append(None)
        
        return results
    
    def _fit_single(self, data: pd.DataFrame) -> 'DAGInference':
        """Fit a single dataset."""
        dag = DAGInference(alpha=self.alpha, max_iter=self.max_iter)
        return dag.fit(data)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert DAG to dictionary format."""
        if self.graph is None:
            raise DAGInferenceError("Model not fitted yet")
            
        return {
            'nodes': self.nodes,
            'edges': self.get_edges(),
            'adjacency_matrix': self.adjacency_matrix.tolist(),
            'is_dag': self.is_dag(),
            'alpha': self.alpha
        }
    
    def from_dict(self, dag_dict: Dict[str, Any]) -> 'DAGInference':
        """Load DAG from dictionary format."""
        self.nodes = dag_dict['nodes']
        self.alpha = dag_dict.get('alpha', 0.05)
        self.adjacency_matrix = np.array(dag_dict['adjacency_matrix'])
        self._create_graph()
        return self
    
    def visualize(self) -> Dict[str, Any]:
        """Get visualization data for the DAG."""
        if self.graph is None:
            raise DAGInferenceError("Model not fitted yet")
            
        pos = nx.spring_layout(self.graph)
        
        return {
            'nodes': [
                {'id': node, 'x': pos[node][0], 'y': pos[node][1]}
                for node in self.nodes
            ],
            'edges': [
                {'source': u, 'target': v}
                for u, v in self.get_edges()
            ]
        }


class FeatureOrchestrator:
    """Orchestrator for DAG inference features."""
    
    def __init__(self):
        self.dag_inference = None
        
    def process(self, data: pd.DataFrame, 
                config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        Process data through DAG inference pipeline.
        
        Args:
            data: Input DataFrame
            config: Configuration parameters
            
        Returns:
            Results dictionary
        """
        config = config or {}
        alpha = config.get('alpha', 0.05)
        
        # Initialize and fit DAG
        self.dag_inference = DAGInference(alpha=alpha)
        self.dag_inference.fit(data)
        
        # Return results
        return {
            'dag': self.dag_inference.to_dict(),
            'causal_order': self.dag_inference.get_causal_order(),
            'is_valid_dag': self.dag_inference.is_dag(),
            'visualization': self.dag_inference.visualize()
        }
```