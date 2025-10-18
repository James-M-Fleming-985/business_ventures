```python
import os
import zlib
import json
import struct
from typing import Dict, List, Optional, Union, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import bz2
import lzma


class CompressionType(Enum):
    """Enumeration of supported compression types."""
    NONE = "none"
    ZLIB = "zlib"
    BZIP2 = "bzip2"
    LZMA = "lzma"


class CompressionError(Exception):
    """Custom exception for compression-related errors."""
    pass


@dataclass
class CompressionStats:
    """Statistics about compression operations."""
    original_size: int
    compressed_size: int
    compression_ratio: float
    algorithm: str


@dataclass
class FileMetadata:
    """Metadata about a compressed file."""
    original_name: str
    original_size: int
    compressed_size: int
    compression_type: str
    checksum: Optional[str] = None


class Compressor:
    """Main compressor class for handling various compression algorithms."""
    
    MAGIC_HEADER = b'COMP'
    VERSION = 1
    
    def __init__(self, compression_type: CompressionType = CompressionType.ZLIB, 
                 compression_level: int = 6):
        """
        Initialize the compressor.
        
        Args:
            compression_type: Type of compression algorithm to use
            compression_level: Compression level (1-9)
        """
        self.compression_type = compression_type
        self.compression_level = max(1, min(9, compression_level))
        self._stats_history: List[CompressionStats] = []
    
    def compress(self, data: Union[str, bytes]) -> bytes:
        """
        Compress data using the configured algorithm.
        
        Args:
            data: Data to compress (string or bytes)
            
        Returns:
            Compressed data as bytes
            
        Raises:
            CompressionError: If compression fails
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        original_size = len(data)
        
        try:
            if self.compression_type == CompressionType.NONE:
                compressed = data
            elif self.compression_type == CompressionType.ZLIB:
                compressed = zlib.compress(data, level=self.compression_level)
            elif self.compression_type == CompressionType.BZIP2:
                compressed = bz2.compress(data, compresslevel=self.compression_level)
            elif self.compression_type == CompressionType.LZMA:
                compressed = lzma.compress(data, format=lzma.FORMAT_XZ, 
                                         preset=self.compression_level)
            else:
                raise CompressionError(f"Unsupported compression type: {self.compression_type}")
            
            compressed_size = len(compressed)
            ratio = 1 - (compressed_size / original_size) if original_size > 0 else 0
            
            stats = CompressionStats(
                original_size=original_size,
                compressed_size=compressed_size,
                compression_ratio=ratio,
                algorithm=self.compression_type.value
            )
            self._stats_history.append(stats)
            
            return compressed
            
        except Exception as e:
            raise CompressionError(f"Compression failed: {str(e)}") from e
    
    def decompress(self, data: bytes) -> bytes:
        """
        Decompress data using the configured algorithm.
        
        Args:
            data: Compressed data
            
        Returns:
            Decompressed data as bytes
            
        Raises:
            CompressionError: If decompression fails
        """
        try:
            if self.compression_type == CompressionType.NONE:
                return data
            elif self.compression_type == CompressionType.ZLIB:
                return zlib.decompress(data)
            elif self.compression_type == CompressionType.BZIP2:
                return bz2.decompress(data)
            elif self.compression_type == CompressionType.LZMA:
                return lzma.decompress(data)
            else:
                raise CompressionError(f"Unsupported compression type: {self.compression_type}")
        except Exception as e:
            raise CompressionError(f"Decompression failed: {str(e)}") from e
    
    def compress_file(self, input_path: Union[str, Path], 
                     output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Compress a file.
        
        Args:
            input_path: Path to input file
            output_path: Path to output file (optional)
            
        Returns:
            Path to compressed file
            
        Raises:
            CompressionError: If file compression fails
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise CompressionError(f"Input file not found: {input_path}")
        
        if output_path is None:
            output_path = input_path.with_suffix(input_path.suffix + '.cmp')
        else:
            output_path = Path(output_path)
        
        try:
            with open(input_path, 'rb') as f:
                data = f.read()
            
            compressed = self.compress(data)
            
            # Create file with metadata header
            metadata = FileMetadata(
                original_name=input_path.name,
                original_size=len(data),
                compressed_size=len(compressed),
                compression_type=self.compression_type.value,
                checksum=str(zlib.crc32(data))
            )
            
            with open(output_path, 'wb') as f:
                # Write magic header and version
                f.write(self.MAGIC_HEADER)
                f.write(struct.pack('B', self.VERSION))
                
                # Write metadata as JSON
                metadata_json = json.dumps(asdict(metadata)).encode('utf-8')
                f.write(struct.pack('I', len(metadata_json)))
                f.write(metadata_json)
                
                # Write compressed data
                f.write(compressed)
            
            return output_path
            
        except Exception as e:
            raise CompressionError(f"File compression failed: {str(e)}") from e
    
    def decompress_file(self, input_path: Union[str, Path], 
                       output_path: Optional[Union[str, Path]] = None) -> Path:
        """
        Decompress a file.
        
        Args:
            input_path: Path to compressed file
            output_path: Path to output file (optional)
            
        Returns:
            Path to decompressed file
            
        Raises:
            CompressionError: If file decompression fails
        """
        input_path = Path(input_path)
        
        if not input_path.exists():
            raise CompressionError(f"Input file not found: {input_path}")
        
        try:
            with open(input_path, 'rb') as f:
                # Read and verify magic header
                magic = f.read(len(self.MAGIC_HEADER))
                if magic != self.MAGIC_HEADER:
                    raise CompressionError("Invalid file format")
                
                # Read version
                version = struct.unpack('B', f.read(1))[0]
                if version != self.VERSION:
                    raise CompressionError(f"Unsupported version: {version}")
                
                # Read metadata
                metadata_size = struct.unpack('I', f.read(4))[0]
                metadata_json = f.read(metadata_size).decode('utf-8')
                metadata = json.loads(metadata_json)
                
                # Read compressed data
                compressed = f.read()
            
            # Temporarily set compression type from metadata
            original_type = self.compression_type
            self.compression_type = CompressionType(metadata['compression_type'])
            
            try:
                decompressed = self.decompress(compressed)
            finally:
                self.compression_type = original_type
            
            # Verify checksum if present
            if metadata.get('checksum'):
                calculated_checksum = str(zlib.crc32(decompressed))
                if calculated_checksum != metadata['checksum']:
                    raise CompressionError("Checksum verification failed")
            
            if output_path is None:
                output_path = input_path.parent / metadata['original_name']
            else:
                output_path = Path(output_path)
            
            with open(output_path, 'wb') as f:
                f.write(decompressed)
            
            return output_path
            
        except Exception as e:
            raise CompressionError(f"File decompression failed: {str(e)}") from e
    
    def get_stats(self) -> Optional[CompressionStats]:
        """
        Get statistics from the last compression operation.
        
        Returns:
            CompressionStats object or None if no operations performed
        """
        return self._stats_history[-1] if self._stats_history else None
    
    def get_all_stats(self) -> List[CompressionStats]:
        """
        Get statistics from all compression operations.
        
        Returns:
            List of CompressionStats objects
        """
        return self._stats_history.copy()
    
    def reset_stats(self) -> None:
        """Reset compression statistics."""
        self._stats_history.clear()
    
    def benchmark(self, data: Union[str, bytes], 
                  algorithms: Optional[List[CompressionType]] = None) -> Dict[str, Any]:
        """
        Benchmark different compression algorithms.
        
        Args:
            data: Data to compress
            algorithms: List of algorithms to test (defaults to all)
            
        Returns:
            Dictionary with benchmark results
        """
        if isinstance(data, str):
            data = data.encode('utf-8')
        
        if algorithms is None:
            algorithms = [ct for ct in CompressionType if ct != CompressionType.NONE]
        
        original_type = self.compression_type
        original_level = self.compression_level
        results = {}
        
        try:
            for algo in algorithms:
                self.compression_type = algo
                algo_results = {}
                
                for level in range(1, 10):
                    self.compression_level = level
                    try:
                        compressed = self.compress(data)
                        stats = self.get_stats()
                        
                        algo_results[f"level_{level}"] = {
                            "compressed_size": stats.compressed_size,
                            "compression_ratio": stats.compression_ratio,
                            "compression_level": level
                        }
                    except Exception:
                        pass
                
                if algo_results:
                    results[algo.value] = algo_results
        
        finally:
            self.compression_type = original_type
            self.compression_level = original_level
        
        return results


class BatchCompressor:
    """Class for handling batch compression operations."""
    
    def __init__(self, compressor: Optional[Compressor] = None):
        """
        Initialize batch compressor.
        
        Args:
            compressor: Compressor instance to use (creates default if None)
        """
        self.compressor = compressor or Compressor()
        self.results: List[Dict[str, Any]] = []
    
    def compress_files(self, file_paths: List[Union[str, Path]], 
                      output_dir: Optional[Union[str, Path]] = None) -> List[Path]:
        """
        Compress multiple files.
        
        Args:
            file_paths: List of paths to compress
            output_dir: Output directory (optional)
            
        Returns:
            List of compressed file paths
        """
        compressed_paths = []
        
        for file_path in file_paths:
            file_path = Path(file_path)
            
            try:
                if output_dir:
                    output_path = Path(output_dir) / (file_path.name + '.cmp')
                else:
                    output_path = None
                
                compressed_path = self.compressor.compress_file(file_path, output_path)
                compressed_paths.append(compressed_path)
                
                self.results.append({
                    'status': 'success',
                    'input': str(file_path),
                    'output': str(compressed_path),
                    'stats': asdict(self.compressor.get_stats())
                })
                
            except Exception as e:
                self.results.append({
                    'status': 'error',
                    'input': str(file_path),
                    'error': str(e)
                })
        
        return compressed_paths
    
    def decompress_files(self, file_paths: List[Union[str, Path]], 
                        output_dir: Optional[Union[str, Path]] = None) -> List[Path]:
        """
        Decompress multiple files.
        
        Args:
            file_paths: List of compressed file paths
            output_dir: Output directory (optional)
            
        Returns:
            List of decompressed file paths
        """
        decompressed_paths = []
        
        for file_path in file_paths:
            file_path = Path(file_path)
            
            try:
                if output_dir:
                    output_path = Path(output_dir) / file_path.stem
                else:
                    output_path = None
                
                decompressed_path = self.compressor.decompress_file(file_path, output_path)
                decompressed_paths.append(decompressed_path)
                
            except Exception:
                pass
        
        return decompressed_paths
    
    def get_results(self) -> List[Dict[str, Any]]:
        """Get batch operation results."""
        return self.results.copy()
    
    def clear_results(self) -> None:
        """Clear batch operation results."""
        self.results.clear()


def create_compressor(algorithm: str = "zlib", level: int = 6) -> Compressor:
    """
    Factory function to create a compressor.
    
    Args:
        algorithm: Compression algorithm name
        level: Compression level
        
    Returns:
        Configured Compressor instance
    """
    try:
        compression_type = CompressionType(algorithm.lower())
    except ValueError:
        raise ValueError(f"Unsupported algorithm: {algorithm}")
    
    return Compressor(compression_type, level)
```