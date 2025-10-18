```python
"""
Partitioner module for handling various partitioning strategies.
"""

from typing import List, Any, Dict, Union, Callable
import math


class Partitioner:
    """
    A class that handles partitioning of data into smaller chunks.
    """
    
    def __init__(self, partition_size: int = 10):
        """
        Initialize the Partitioner with a given partition size.
        
        Args:
            partition_size (int): The size of each partition. Defaults to 10.
        
        Raises:
            ValueError: If partition_size is less than or equal to 0.
        """
        if partition_size <= 0:
            raise ValueError("Partition size must be greater than 0")
        self.partition_size = partition_size
    
    def partition(self, data: List[Any]) -> List[List[Any]]:
        """
        Partition a list of data into smaller chunks.
        
        Args:
            data (List[Any]): The data to partition.
        
        Returns:
            List[List[Any]]: A list of partitions.
        """
        if not data:
            return []
        
        partitions = []
        for i in range(0, len(data), self.partition_size):
            partitions.append(data[i:i + self.partition_size])
        
        return partitions
    
    def partition_dict(self, data: Dict[Any, Any]) -> List[Dict[Any, Any]]:
        """
        Partition a dictionary into smaller dictionaries.
        
        Args:
            data (Dict[Any, Any]): The dictionary to partition.
        
        Returns:
            List[Dict[Any, Any]]: A list of dictionary partitions.
        """
        if not data:
            return []
        
        items = list(data.items())
        partitioned_items = self.partition(items)
        
        return [dict(partition) for partition in partitioned_items]
    
    def partition_by_predicate(self, data: List[Any], predicate: Callable[[Any], bool]) -> Dict[str, List[Any]]:
        """
        Partition data based on a predicate function.
        
        Args:
            data (List[Any]): The data to partition.
            predicate (Callable[[Any], bool]): A function that returns True or False for each element.
        
        Returns:
            Dict[str, List[Any]]: A dictionary with 'true' and 'false' keys containing the partitioned data.
        """
        result = {'true': [], 'false': []}
        
        for item in data:
            if predicate(item):
                result['true'].append(item)
            else:
                result['false'].append(item)
        
        return result
    
    def partition_by_key(self, data: List[Dict[Any, Any]], key: str) -> Dict[Any, List[Dict[Any, Any]]]:
        """
        Partition a list of dictionaries by a specific key.
        
        Args:
            data (List[Dict[Any, Any]]): List of dictionaries to partition.
            key (str): The key to use for partitioning.
        
        Returns:
            Dict[Any, List[Dict[Any, Any]]]: A dictionary where keys are unique values of the specified key,
                                              and values are lists of dictionaries with that key value.
        """
        result = {}
        
        for item in data:
            if key in item:
                key_value = item[key]
                if key_value not in result:
                    result[key_value] = []
                result[key_value].append(item)
        
        return result
    
    def get_partition_count(self, data_size: int) -> int:
        """
        Calculate the number of partitions needed for a given data size.
        
        Args:
            data_size (int): The total size of the data.
        
        Returns:
            int: The number of partitions needed.
        """
        if data_size <= 0:
            return 0
        return math.ceil(data_size / self.partition_size)
    
    def partition_with_overlap(self, data: List[Any], overlap: int = 1) -> List[List[Any]]:
        """
        Partition data with overlapping elements between partitions.
        
        Args:
            data (List[Any]): The data to partition.
            overlap (int): Number of elements to overlap between partitions.
        
        Returns:
            List[List[Any]]: A list of overlapping partitions.
        
        Raises:
            ValueError: If overlap is negative or greater than partition_size.
        """
        if overlap < 0:
            raise ValueError("Overlap cannot be negative")
        if overlap >= self.partition_size:
            raise ValueError("Overlap must be less than partition size")
        
        if not data:
            return []
        
        partitions = []
        step = self.partition_size - overlap
        
        for i in range(0, len(data), step):
            partition = data[i:i + self.partition_size]
            partitions.append(partition)
            if len(partition) < self.partition_size:
                break
        
        return partitions
    
    def partition_balanced(self, data: List[Any], num_partitions: int) -> List[List[Any]]:
        """
        Partition data into a fixed number of balanced partitions.
        
        Args:
            data (List[Any]): The data to partition.
            num_partitions (int): The number of partitions to create.
        
        Returns:
            List[List[Any]]: A list of balanced partitions.
        
        Raises:
            ValueError: If num_partitions is less than or equal to 0.
        """
        if num_partitions <= 0:
            raise ValueError("Number of partitions must be greater than 0")
        
        if not data:
            return [[] for _ in range(num_partitions)]
        
        base_size = len(data) // num_partitions
        remainder = len(data) % num_partitions
        
        partitions = []
        start = 0
        
        for i in range(num_partitions):
            # Add 1 to size for first 'remainder' partitions
            size = base_size + (1 if i < remainder else 0)
            partitions.append(data[start:start + size])
            start += size
        
        return partitions


def create_partitioner(partition_size: int = 10) -> Partitioner:
    """
    Factory function to create a Partitioner instance.
    
    Args:
        partition_size (int): The size of each partition.
    
    Returns:
        Partitioner: A new Partitioner instance.
    """
    return Partitioner(partition_size)


def partition_list(data: List[Any], partition_size: int) -> List[List[Any]]:
    """
    Convenience function to partition a list without creating a Partitioner instance.
    
    Args:
        data (List[Any]): The data to partition.
        partition_size (int): The size of each partition.
    
    Returns:
        List[List[Any]]: A list of partitions.
    """
    partitioner = Partitioner(partition_size)
    return partitioner.partition(data)


def partition_by_type(data: List[Any]) -> Dict[type, List[Any]]:
    """
    Partition a list by the type of each element.
    
    Args:
        data (List[Any]): The data to partition.
    
    Returns:
        Dict[type, List[Any]]: A dictionary where keys are types and values are lists of elements of that type.
    """
    result = {}
    
    for item in data:
        item_type = type(item)
        if item_type not in result:
            result[item_type] = []
        result[item_type].append(item)
    
    return result
```