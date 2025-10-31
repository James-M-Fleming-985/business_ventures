```python
"""
Network graph implementation for correlation dashboard.

This module provides functionality for creating and managing network graphs
to visualize correlations between different data points.
"""

import json
import logging
from typing import Dict, List, Optional, Tuple, Any, Union
import numpy as np
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, Future
import threading
from datetime import datetime
import time
import warnings

# Configure logging
logger = logging.getLogger(__name__)


class NetworkGraph:
    """
    A class for creating and managing network graphs for correlation visualization.
    
    Attributes:
        nodes (List[Dict]): List of node dictionaries containing node information
        edges (List[Dict]): List of edge dictionaries containing edge information
        correlation_threshold (float): Minimum correlation value to create an edge
        _lock (threading.Lock): Thread lock for concurrent operations
    """
    
    def __init__(self, correlation_threshold: float = 0.5):
        """
        Initialize NetworkGraph with optional correlation threshold.
        
        Args:
            correlation_threshold (float): Minimum correlation value to create an edge.
                                         Defaults to 0.5.
        """
        self.nodes: List[Dict[str, Any]] = []
        self.edges: List[Dict[str, Any]] = []
        self.correlation_threshold = correlation_threshold
        self._lock = threading.Lock()
        self._executor = ThreadPoolExecutor(max_workers=4)
    
    def add_node(self, node_id: str, label: Optional[str] = None, 
                 attributes: Optional[Dict] = None) -> None:
        """
        Add a node to the network graph.
        
        Args:
            node_id (str): Unique identifier for the node
            label (Optional[str]): Display label for the node
            attributes (Optional[Dict]): Additional attributes for the node
        """
        with self._lock:
            node = {
                'id': node_id,
                'label': label or node_id,
                'attributes': attributes or {}
            }
            
            # Check if node already exists
            if not any(n['id'] == node_id for n in self.nodes):
                self.nodes.append(node)
    
    def add_edge(self, source: str, target: str, weight: float,
                 attributes: Optional[Dict] = None) -> None:
        """
        Add an edge between two nodes.
        
        Args:
            source (str): Source node ID
            target (str): Target node ID
            weight (float): Weight of the edge (typically correlation value)
            attributes (Optional[Dict]): Additional attributes for the edge
        """
        with self._lock:
            # Only add edge if weight meets threshold
            if abs(weight) >= self.correlation_threshold:
                edge = {
                    'source': source,
                    'target': target,
                    'weight': weight,
                    'attributes': attributes or {}
                }
                
                # Avoid duplicate edges
                if not any(e['source'] == source and e['target'] == target 
                          for e in self.edges):
                    self.edges.append(edge)
    
    def build_from_correlation_matrix(self, correlation_matrix: pd.DataFrame) -> None:
        """
        Build network graph from a correlation matrix.
        
        Args:
            correlation_matrix (pd.DataFrame): Correlation matrix with variable names
                                             as index and columns
        """
        start_time = time.time()
        
        # Handle missing data
        correlation_matrix = correlation_matrix.fillna(0)
        
        # Add nodes for each variable
        for var in correlation_matrix.columns:
            self.add_node(var)
        
        # Add edges for correlations above threshold
        futures = []
        with self._executor as executor:
            for i, var1 in enumerate(correlation_matrix.columns):
                for j, var2 in enumerate(correlation_matrix.columns):
                    if i < j:  # Avoid duplicates and self-correlations
                        correlation = correlation_matrix.loc[var1, var2]
                        future = executor.submit(
                            self._add_edge_if_significant,
                            var1, var2, correlation
                        )
                        futures.append(future)
            
            # Wait for all tasks to complete
            for future in futures:
                future.result()
        
        # Ensure completion within 5 seconds for 10K data points
        elapsed = time.time() - start_time
        if elapsed > 5:
            warnings.warn(f"Build took {elapsed:.2f} seconds, exceeding 5 second limit")
    
    def _add_edge_if_significant(self, var1: str, var2: str, correlation: float) -> None:
        """Helper method to add edge if correlation is significant."""
        if abs(correlation) >= self.correlation_threshold:
            self.add_edge(var1, var2, correlation)
    
    def get_neighbors(self, node_id: str) -> List[str]:
        """
        Get all neighbors of a given node.
        
        Args:
            node_id (str): Node ID to find neighbors for
            
        Returns:
            List[str]: List of neighbor node IDs
        """
        neighbors = []
        with self._lock:
            for edge in self.edges:
                if edge['source'] == node_id:
                    neighbors.append(edge['target'])
                elif edge['target'] == node_id:
                    neighbors.append(edge['source'])
        
        return list(set(neighbors))
    
    def get_degree(self, node_id: str) -> int:
        """
        Get the degree (number of connections) of a node.
        
        Args:
            node_id (str): Node ID to calculate degree for
            
        Returns:
            int: Number of connections
        """
        return len(self.get_neighbors(node_id))
    
    def get_edge_weight(self, source: str, target: str) -> Optional[float]:
        """
        Get the weight of an edge between two nodes.
        
        Args:
            source (str): Source node ID
            target (str): Target node ID
            
        Returns:
            Optional[float]: Edge weight if exists, None otherwise
        """
        with self._lock:
            for edge in self.edges:
                if (edge['source'] == source and edge['target'] == target) or \
                   (edge['source'] == target and edge['target'] == source):
                    return edge['weight']
        return None
    
    def to_dict(self) -> Dict[str, List[Dict]]:
        """
        Convert network graph to dictionary representation.
        
        Returns:
            Dict[str, List[Dict]]: Dictionary with 'nodes' and 'edges' lists
        """
        with self._lock:
            return {
                'nodes': self.nodes.copy(),
                'edges': self.edges.copy()
            }
    
    def to_json(self) -> str:
        """
        Convert network graph to JSON string.
        
        Returns:
            str: JSON representation of the network graph
        """
        return json.dumps(self.to_dict(), indent=2)
    
    def filter_by_correlation(self, min_correlation: float) -> 'NetworkGraph':
        """
        Create a new network graph with edges filtered by minimum correlation.
        
        Args:
            min_correlation (float): Minimum correlation value for edges
            
        Returns:
            NetworkGraph: New filtered network graph
        """
        filtered_graph = NetworkGraph(correlation_threshold=min_correlation)
        
        with self._lock:
            # Copy all nodes
            for node in self.nodes:
                filtered_graph.add_node(
                    node['id'], 
                    node['label'], 
                    node.get('attributes')
                )
            
            # Copy edges that meet threshold
            for edge in self.edges:
                if abs(edge['weight']) >= min_correlation:
                    filtered_graph.add_edge(
                        edge['source'],
                        edge['target'],
                        edge['weight'],
                        edge.get('attributes')
                    )
        
        return filtered_graph
    
    def get_clusters(self) -> List[List[str]]:
        """
        Identify clusters of highly correlated nodes.
        
        Returns:
            List[List[str]]: List of clusters, each cluster is a list of node IDs
        """
        visited = set()
        clusters = []
        
        def dfs(node: str, cluster: List[str]) -> None:
            """Depth-first search to find connected components."""
            visited.add(node)
            cluster.append(node)
            
            for neighbor in self.get_neighbors(node):
                if neighbor not in visited:
                    dfs(neighbor, cluster)
        
        with self._lock:
            for node in self.nodes:
                if node['id'] not in visited:
                    cluster = []
                    dfs(node['id'], cluster)
                    if cluster:
                        clusters.append(cluster)
        
        return clusters
    
    def get_centrality_measures(self) -> Dict[str, Dict[str, float]]:
        """
        Calculate various centrality measures for nodes.
        
        Returns:
            Dict[str, Dict[str, float]]: Dictionary with centrality measures
        """
        centrality = {}
        
        with self._lock:
            for node in self.nodes:
                node_id = node['id']
                degree = self.get_degree(node_id)
                
                # Degree centrality
                degree_centrality = degree / (len(self.nodes) - 1) if len(self.nodes) > 1 else 0
                
                # Weighted degree (strength)
                weighted_degree = 0
                for edge in self.edges:
                    if edge['source'] == node_id or edge['target'] == node_id:
                        weighted_degree += abs(edge['weight'])
                
                centrality[node_id] = {
                    'degree': degree,
                    'degree_centrality': degree_centrality,
                    'weighted_degree': weighted_degree
                }
        
        return centrality
    
    def integrate_with_orchestrator(self, orchestrator: Any) -> Dict[str, Any]:
        """
        Integrate network graph with feature orchestrator.
        
        Args:
            orchestrator: Feature orchestrator instance
            
        Returns:
            Dict[str, Any]: Integration status and metadata
        """
        try:
            # Prepare graph data for orchestrator
            graph_data = {
                'graph': self.to_dict(),
                'metadata': {
                    'num_nodes': len(self.nodes),
                    'num_edges': len(self.edges),
                    'correlation_threshold': self.correlation_threshold,
                    'timestamp': datetime.now().isoformat()
                },
                'centrality': self.get_centrality_measures(),
                'clusters': self.get_clusters()
            }
            
            # Register with orchestrator if it has the method
            if hasattr(orchestrator, 'register_component'):
                orchestrator.register_component('network_graph', graph_data)
            
            return {
                'status': 'success',
                'integration_time': datetime.now().isoformat(),
                'data': graph_data
            }
            
        except Exception as e:
            logger.error(f"Failed to integrate with orchestrator: {str(e)}")
            return {
                'status': 'error',
                'error': str(e),
                'integration_time': datetime.now().isoformat()
            }
    
    def __repr__(self) -> str:
        """String representation of NetworkGraph."""
        return f"NetworkGraph(nodes={len(self.nodes)}, edges={len(self.edges)}, " \
               f"threshold={self.correlation_threshold})"
    
    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Network Graph with {len(self.nodes)} nodes and {len(self.edges)} edges"


# Helper functions for statistical calculations
def calculate_correlation_matrix(data: pd.DataFrame, method: str = 'pearson') -> pd.DataFrame:
    """
    Calculate correlation matrix from data.
    
    Args:
        data (pd.DataFrame): Input data with variables as columns
        method (str): Correlation method ('pearson', 'spearman', 'kendall')
        
    Returns:
        pd.DataFrame: Correlation matrix
    """
    # Handle missing data
    data_clean = data.dropna()
    
    if method == 'pearson':
        return data_clean.corr(method='pearson')
    elif method == 'spearman':
        return data_clean.corr(method='spearman')
    elif method == 'kendall':
        return data_clean.corr(method='kendall')
    else:
        raise ValueError(f"Unsupported correlation method: {method}")


def create_network_from_data(data: pd.DataFrame, 
                           correlation_threshold: float = 0.5,
                           method: str = 'pearson') -> NetworkGraph:
    """
    Create a network graph directly from data.
    
    Args:
        data (pd.DataFrame): Input data with variables as columns
        correlation_threshold (float): Minimum correlation for edges
        method (str): Correlation method
        
    Returns:
        NetworkGraph: Constructed network graph
    """
    # Calculate correlation matrix
    corr_matrix = calculate_correlation_matrix(data, method)
    
    # Build network graph
    graph = NetworkGraph(correlation_threshold=correlation_threshold)
    graph.build_from_correlation_matrix(corr_matrix)
    
    return graph
```