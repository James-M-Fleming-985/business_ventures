```python
"""
Implementation for LAYER-CA-001-03-03 Indexer module.
"""

import os
import json
import hashlib
from typing import Dict, List, Any, Optional, Union
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class IndexEntry:
    """Represents an entry in the index."""
    
    def __init__(self, path: str, metadata: Optional[Dict[str, Any]] = None):
        self.path = path
        self.metadata = metadata or {}
        self.checksum = None
        self.size = None
        self.modified_time = None
        self.created_time = None
        self._update_file_info()
    
    def _update_file_info(self):
        """Update file information from the filesystem."""
        try:
            if os.path.exists(self.path):
                stat = os.stat(self.path)
                self.size = stat.st_size
                self.modified_time = datetime.fromtimestamp(stat.st_mtime).isoformat()
                self.created_time = datetime.fromtimestamp(stat.st_ctime).isoformat()
                
                # Calculate checksum for files
                if os.path.isfile(self.path):
                    self.checksum = self._calculate_checksum()
        except Exception as e:
            logger.error(f"Error updating file info for {self.path}: {e}")
    
    def _calculate_checksum(self) -> str:
        """Calculate SHA256 checksum of the file."""
        sha256_hash = hashlib.sha256()
        try:
            with open(self.path, "rb") as f:
                for byte_block in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(byte_block)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Error calculating checksum for {self.path}: {e}")
            return ""
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert entry to dictionary format."""
        return {
            "path": self.path,
            "metadata": self.metadata,
            "checksum": self.checksum,
            "size": self.size,
            "modified_time": self.modified_time,
            "created_time": self.created_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'IndexEntry':
        """Create entry from dictionary."""
        entry = cls(data["path"], data.get("metadata", {}))
        entry.checksum = data.get("checksum")
        entry.size = data.get("size")
        entry.modified_time = data.get("modified_time")
        entry.created_time = data.get("created_time")
        return entry


class Indexer:
    """Main indexer class for creating and managing file indexes."""
    
    def __init__(self, index_path: Optional[str] = None):
        """
        Initialize the indexer.
        
        Args:
            index_path: Path to store the index file. Defaults to .index.json
        """
        self.index_path = index_path or ".index.json"
        self.entries: Dict[str, IndexEntry] = {}
        self._load_index()
    
    def _load_index(self):
        """Load existing index from disk."""
        if os.path.exists(self.index_path):
            try:
                with open(self.index_path, 'r') as f:
                    data = json.load(f)
                    for path, entry_data in data.items():
                        self.entries[path] = IndexEntry.from_dict(entry_data)
            except Exception as e:
                logger.error(f"Error loading index: {e}")
                self.entries = {}
    
    def save_index(self):
        """Save index to disk."""
        try:
            data = {path: entry.to_dict() for path, entry in self.entries.items()}
            with open(self.index_path, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving index: {e}")
            raise
    
    def add_file(self, path: str, metadata: Optional[Dict[str, Any]] = None) -> IndexEntry:
        """
        Add a file to the index.
        
        Args:
            path: Path to the file
            metadata: Optional metadata for the file
            
        Returns:
            The created index entry
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        
        entry = IndexEntry(path, metadata)
        self.entries[path] = entry
        self.save_index()
        return entry
    
    def add_directory(self, path: str, recursive: bool = True, 
                     file_pattern: Optional[str] = None) -> List[IndexEntry]:
        """
        Add all files in a directory to the index.
        
        Args:
            path: Path to the directory
            recursive: Whether to include subdirectories
            file_pattern: Optional glob pattern for files to include
            
        Returns:
            List of created index entries
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Directory not found: {path}")
        
        if not os.path.isdir(path):
            raise ValueError(f"Path is not a directory: {path}")
        
        entries = []
        
        if recursive:
            for root, dirs, files in os.walk(path):
                for file in files:
                    file_path = os.path.join(root, file)
                    if file_pattern:
                        from fnmatch import fnmatch
                        if not fnmatch(file, file_pattern):
                            continue
                    entry = self.add_file(file_path)
                    entries.append(entry)
        else:
            for item in os.listdir(path):
                item_path = os.path.join(path, item)
                if os.path.isfile(item_path):
                    if file_pattern:
                        from fnmatch import fnmatch
                        if not fnmatch(item, file_pattern):
                            continue
                    entry = self.add_file(item_path)
                    entries.append(entry)
        
        return entries
    
    def remove_file(self, path: str) -> bool:
        """
        Remove a file from the index.
        
        Args:
            path: Path to the file
            
        Returns:
            True if file was removed, False if not found
        """
        if path in self.entries:
            del self.entries[path]
            self.save_index()
            return True
        return False
    
    def get_entry(self, path: str) -> Optional[IndexEntry]:
        """
        Get an index entry by path.
        
        Args:
            path: Path to the file
            
        Returns:
            IndexEntry or None if not found
        """
        return self.entries.get(path)
    
    def update_entry(self, path: str, metadata: Optional[Dict[str, Any]] = None) -> IndexEntry:
        """
        Update an entry in the index.
        
        Args:
            path: Path to the file
            metadata: New metadata (if provided)
            
        Returns:
            The updated entry
        """
        if path not in self.entries:
            raise KeyError(f"Entry not found: {path}")
        
        entry = self.entries[path]
        if metadata is not None:
            entry.metadata = metadata
        entry._update_file_info()
        self.save_index()
        return entry
    
    def search(self, query: Union[str, Dict[str, Any]]) -> List[IndexEntry]:
        """
        Search the index.
        
        Args:
            query: Search query (string for path search, dict for metadata search)
            
        Returns:
            List of matching entries
        """
        results = []
        
        if isinstance(query, str):
            # Path-based search
            for path, entry in self.entries.items():
                if query.lower() in path.lower():
                    results.append(entry)
        elif isinstance(query, dict):
            # Metadata-based search
            for entry in self.entries.values():
                match = True
                for key, value in query.items():
                    if key not in entry.metadata or entry.metadata[key] != value:
                        match = False
                        break
                if match:
                    results.append(entry)
        
        return results
    
    def verify_integrity(self) -> Dict[str, Any]:
        """
        Verify the integrity of all indexed files.
        
        Returns:
            Dictionary with verification results
        """
        results = {
            "total": len(self.entries),
            "valid": 0,
            "invalid": 0,
            "missing": 0,
            "errors": []
        }
        
        for path, entry in self.entries.items():
            try:
                if not os.path.exists(path):
                    results["missing"] += 1
                    results["errors"].append({
                        "path": path,
                        "error": "File not found"
                    })
                elif os.path.isfile(path):
                    current_checksum = entry._calculate_checksum()
                    if current_checksum == entry.checksum:
                        results["valid"] += 1
                    else:
                        results["invalid"] += 1
                        results["errors"].append({
                            "path": path,
                            "error": "Checksum mismatch",
                            "expected": entry.checksum,
                            "actual": current_checksum
                        })
                else:
                    # Directory entries are considered valid if they exist
                    results["valid"] += 1
            except Exception as e:
                results["invalid"] += 1
                results["errors"].append({
                    "path": path,
                    "error": str(e)
                })
        
        return results
    
    def clear(self):
        """Clear all entries from the index."""
        self.entries.clear()
        self.save_index()
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the index.
        
        Returns:
            Dictionary with index statistics
        """
        total_size = sum(entry.size or 0 for entry in self.entries.values())
        file_types = {}
        
        for entry in self.entries.values():
            ext = os.path.splitext(entry.path)[1].lower()
            if ext:
                file_types[ext] = file_types.get(ext, 0) + 1
        
        return {
            "total_files": len(self.entries),
            "total_size": total_size,
            "file_types": file_types,
            "index_path": self.index_path
        }
    
    def export_index(self, output_path: str, format: str = "json"):
        """
        Export the index to a file.
        
        Args:
            output_path: Path to export the index to
            format: Export format (json, csv, etc.)
        """
        if format == "json":
            data = {path: entry.to_dict() for path, entry in self.entries.items()}
            with open(output_path, 'w') as f:
                json.dump(data, f, indent=2)
        elif format == "csv":
            import csv
            with open(output_path, 'w', newline='') as f:
                writer = csv.writer(f)
                writer.writerow(["path", "size", "checksum", "modified_time", "created_time"])
                for entry in self.entries.values():
                    writer.writerow([
                        entry.path,
                        entry.size,
                        entry.checksum,
                        entry.modified_time,
                        entry.created_time
                    ])
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def import_index(self, input_path: str):
        """
        Import an index from a file.
        
        Args:
            input_path: Path to import the index from
        """
        if not os.path.exists(input_path):
            raise FileNotFoundError(f"Import file not found: {input_path}")
        
        with open(input_path, 'r') as f:
            data = json.load(f)
            self.entries.clear()
            for path, entry_data in data.items():
                self.entries[path] = IndexEntry.from_dict(entry_data)
        
        self.save_index()


def create_indexer(index_path: Optional[str] = None) -> Indexer:
    """
    Factory function to create an indexer instance.
    
    Args:
        index_path: Optional path for the index file
        
    Returns:
        Indexer instance
    """
    return Indexer(index_path)


# Additional utility functions
def quick_index_directory(directory: str, output_path: Optional[str] = None) -> Indexer:
    """
    Quickly index a directory and return the indexer.
    
    Args:
        directory: Directory to index
        output_path: Optional path for the index file
        
    Returns:
        Indexer instance with the directory indexed
    """
    indexer = Indexer(output_path)
    indexer.add_directory(directory)
    return indexer


def verify_file_integrity(file_path: str, expected_checksum: str) -> bool:
    """
    Verify a file's integrity against an expected checksum.
    
    Args:
        file_path: Path to the file
        expected_checksum: Expected SHA256 checksum
        
    Returns:
        True if checksum matches, False otherwise
    """
    entry = IndexEntry(file_path)
    return entry.checksum == expected_checksum
```