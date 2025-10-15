```python
import hashlib
import json
import os
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
from cryptography.fernet import Fernet
import tarfile
import tempfile


class DataPreservationService:
    """Service for preserving, archiving, and restoring MVP data with integrity verification."""
    
    def __init__(self, encryption_key: Optional[bytes] = None):
        """
        Initialize the Data Preservation Service.
        
        Args:
            encryption_key: Optional encryption key for sensitive data. If not provided, generates new key.
        """
        self.encryption_key = encryption_key or Fernet.generate_key()
        self.cipher = Fernet(self.encryption_key)
        self.manifest = {
            "version": "1.0",
            "created_at": datetime.utcnow().isoformat(),
            "files": {},
            "checksums": {},
            "encrypted_files": [],
        }
    
    def calculate_checksum(self, data: bytes) -> str:
        """
        Calculate SHA-256 checksum for data.
        
        Args:
            data: Bytes data to checksum
            
        Returns:
            Hexadecimal SHA-256 checksum string
        """
        return hashlib.sha256(data).hexdigest()
    
    def calculate_file_checksum(self, filepath: Path) -> str:
        """
        Calculate SHA-256 checksum for a file.
        
        Args:
            filepath: Path to file
            
        Returns:
            Hexadecimal SHA-256 checksum string
        """
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def encrypt_data(self, data: bytes) -> bytes:
        """
        Encrypt sensitive data.
        
        Args:
            data: Raw bytes to encrypt
            
        Returns:
            Encrypted bytes
        """
        return self.cipher.encrypt(data)
    
    def decrypt_data(self, encrypted_data: bytes) -> bytes:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted bytes
            
        Returns:
            Decrypted raw bytes
        """
        return self.cipher.decrypt(encrypted_data)
    
    def export_data(
        self,
        source_dir: Path,
        output_archive: Path,
        sensitive_patterns: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Export 100% of MVP data without loss.
        
        Args:
            source_dir: Source directory to export
            output_archive: Output archive path
            sensitive_patterns: List of filename patterns for sensitive data (e.g., ['config', 'secret'])
            
        Returns:
            Export manifest with checksums and metadata
        """
        if sensitive_patterns is None:
            sensitive_patterns = ['config', 'secret', 'credential', 'key', 'password']
        
        source_dir = Path(source_dir)
        output_archive = Path(output_archive)
        
        if not source_dir.exists():
            raise ValueError(f"Source directory does not exist: {source_dir}")
        
        # Create temporary working directory
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            archive_content_dir = temp_path / "data"
            archive_content_dir.mkdir(parents=True, exist_ok=True)
            
            # Process all files
            for root, dirs, files in os.walk(source_dir):
                root_path = Path(root)
                rel_root = root_path.relative_to(source_dir)
                
                for file in files:
                    source_file = root_path / file
                    rel_file_path = rel_root / file
                    dest_file = archive_content_dir / rel_file_path
                    
                    # Create destination directory
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Read original file
                    with open(source_file, 'rb') as f:
                        file_data = f.read()
                    
                    # Calculate original checksum
                    original_checksum = self.calculate_checksum(file_data)
                    
                    # Check if file is sensitive
                    is_sensitive = any(pattern.lower() in file.lower() for pattern in sensitive_patterns)
                    
                    if is_sensitive:
                        # Encrypt sensitive data
                        encrypted_data = self.encrypt_data(file_data)
                        with open(dest_file, 'wb') as f:
                            f.write(encrypted_data)
                        
                        stored_checksum = self.calculate_checksum(encrypted_data)
                        self.manifest["encrypted_files"].append(str(rel_file_path))
                    else:
                        # Copy non-sensitive data as-is
                        with open(dest_file, 'wb') as f:
                            f.write(file_data)
                        stored_checksum = original_checksum
                    
                    # Store metadata
                    file_key = str(rel_file_path)
                    self.manifest["files"][file_key] = {
                        "original_checksum": original_checksum,
                        "stored_checksum": stored_checksum,
                        "size": len(file_data),
                        "encrypted": is_sensitive,
                        "path": file_key
                    }
                    self.manifest["checksums"][file_key] = original_checksum
            
            # Save manifest
            manifest_path = temp_path / "manifest.json"
            with open(manifest_path, 'w') as f:
                json.dump(self.manifest, f, indent=2)
            
            # Save encryption key
            key_path = temp_path / "encryption.key"
            with open(key_path, 'wb') as f:
                f.write(self.encryption_key)
            
            # Create restoration documentation
            self._generate_restoration_docs(temp_path)
            
            # Create tar archive
            output_archive.parent.mkdir(parents=True, exist_ok=True)
            with tarfile.open(output_archive, 'w:gz') as tar:
                tar.add(archive_content_dir, arcname='data')
                tar.add(manifest_path, arcname='manifest.json')
                tar.add(key_path, arcname='encryption.key')
                tar.add(temp_path / "RESTORATION.md", arcname='RESTORATION.md')
        
        return self.manifest
    
    def verify_integrity(
        self,
        archive_path: Path,
        expected_checksums: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """
        Verify data integrity with SHA-256 checksums.
        
        Args:
            archive_path: Path to archive
            expected_checksums: Optional dict of expected checksums
            
        Returns:
            Verification report with status and details
        """
        archive_path = Path(archive_path)
        
        if not archive_path.exists():
            raise ValueError(f"Archive does not exist: {archive_path}")
        
        verification_report = {
            "valid": True,
            "verified_files": 0,
            "total_files": 0,
            "failures": [],
            "details": {}
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract archive
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(temp_path)
            
            # Load manifest
            manifest_path = temp_path / "manifest.json"
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Load encryption key
            key_path = temp_path / "encryption.key"
            with open(key_path, 'rb') as f:
                encryption_key = f.read()
            cipher = Fernet(encryption_key)
            
            data_dir = temp_path / "data"
            verification_report["total_files"] = len(manifest["files"])
            
            # Verify each file
            for file_key, file_info in manifest["files"].items():
                file_path = data_dir / file_key
                
                if not file_path.exists():
                    verification_report["valid"] = False
                    verification_report["failures"].append({
                        "file": file_key,
                        "error": "File not found in archive"
                    })
                    continue
                
                # Read file
                with open(file_path, 'rb') as f:
                    stored_data = f.read()
                
                # Calculate stored checksum
                stored_checksum = hashlib.sha256(stored_data).hexdigest()
                
                # Verify stored checksum
                if stored_checksum != file_info["stored_checksum"]:
                    verification_report["valid"] = False
                    verification_report["failures"].append({
                        "file": file_key,
                        "error": "Stored checksum mismatch",
                        "expected": file_info["stored_checksum"],
                        "actual": stored_checksum
                    })
                    continue
                
                # Decrypt if necessary and verify original checksum
                if file_info.get("encrypted", False):
                    try:
                        original_data = cipher.decrypt(stored_data)
                    except Exception as e:
                        verification_report["valid"] = False
                        verification_report["failures"].append({
                            "file": file_key,
                            "error": f"Decryption failed: {str(e)}"
                        })
                        continue
                else:
                    original_data = stored_data
                
                original_checksum = hashlib.sha256(original_data).hexdigest()
                
                if original_checksum != file_info["original_checksum"]:
                    verification_report["valid"] = False
                    verification_report["failures"].append({
                        "file": file_key,
                        "error": "Original checksum mismatch",
                        "expected": file_info["original_checksum"],
                        "actual": original_checksum
                    })
                    continue
                
                # Check against expected checksums if provided
                if expected_checksums and file_key in expected_checksums:
                    if original_checksum != expected_checksums[file_key]:
                        verification_report["valid"] = False
                        verification_report["failures"].append({
                            "file": file_key,
                            "error": "Expected checksum mismatch",
                            "expected": expected_checksums[file_key],
                            "actual": original_checksum
                        })
                        continue
                
                verification_report["verified_files"] += 1
                verification_report["details"][file_key] = {
                    "checksum": original_checksum,
                    "status": "valid"
                }
        
        return verification_report
    
    def restore_data(
        self,
        archive_path: Path,
        destination_dir: Path,
        verify: bool = True
    ) -> Dict[str, Any]:
        """
        Restore data from archive.
        
        Args:
            archive_path: Path to archive
            destination_dir: Destination directory for restoration
            verify: Whether to verify integrity before restoration
            
        Returns:
            Restoration report
        """
        archive_path = Path(archive_path)
        destination_dir = Path(destination_dir)
        
        if not archive_path.exists():
            raise ValueError(f"Archive does not exist: {archive_path}")
        
        # Verify integrity first if requested
        if verify:
            verification = self.verify_integrity(archive_path)
            if not verification["valid"]:
                raise ValueError(f"Archive integrity verification failed: {verification['failures']}")
        
        restoration_report = {
            "success": True,
            "restored_files": 0,
            "total_files": 0,
            "failures": []
        }
        
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)
            
            # Extract archive
            with tarfile.open(archive_path, 'r:gz') as tar:
                tar.extractall(temp_path)
            
            # Load manifest
            manifest_path = temp_path / "manifest.json"
            with open(manifest_path, 'r') as f:
                manifest = json.load(f)
            
            # Load encryption key
            key_path = temp_path / "encryption.key"
            with open(key_path, 'rb') as f:
                encryption_key = f.read()
            cipher = Fernet(encryption_key)
            
            data_dir = temp_path / "data"
            restoration_report["total_files"] = len(manifest["files"])
            
            # Restore each file
            for file_key, file_info in manifest["files"].items():
                try:
                    source_file = data_dir / file_key
                    dest_file = destination_dir / file_key
                    
                    # Create destination directory
                    dest_file.parent.mkdir(parents=True, exist_ok=True)
                    
                    # Read stored data
                    with open(source_file, 'rb') as f:
                        stored_data = f.read()
                    
                    # Decrypt if necessary
                    if file_info.get("encrypted", False):
                        original_data = cipher.decrypt(stored_data)
                    else:
                        original_data = stored_data
                    
                    # Write to destination
                    with open(dest_file, 'wb') as f:
                        f.write(original_data)
                    
                    restoration_report["restored_files"] += 1
                    
                except Exception as e:
                    restoration_report["success"] = False
                    restoration_report["failures"].append({
                        "file": file_key,
                        "error": str(e)
                    })
        
        return restoration_report
    
    def _generate_restoration_docs(self, output_dir: Path):
        """
        Generate complete restoration documentation.
        
        Args:
            output_dir: Directory to write documentation
        """
        doc_content = """# Data Restoration Documentation

## Overview
This archive contains a complete backup of MVP data with integrity verification and encryption for sensitive data.

## Archive Contents
- `data/` - All exported data files
- `manifest.json` - File manifest with checksums and metadata
- `encryption.key` - Encryption key for sensitive data
- `RESTORATION.md` - This documentation

## Restoration Process

### Prerequisites
- Python 3.7 or higher
- cryptography library: `pip install cryptography`

### Quick Restoration
```python
from data_preservation_service import DataPreservationService

# Initialize service
service = DataPreservationService()

# Restore data
report = service.restore_data(
    archive_path="backup.tar.gz",
    destination_dir="restored_data",
    verify=True
)

print(f"Restored {report['restored_files']} files")
```

### Manual Restoration Steps

1. **Extract Archive**
   ```bash
   tar -xzf backup.tar.gz
   ```

2. **Verify Integrity**
   - Check manifest.json for file checksums
   - Verify each file's SHA-256 checksum matches

3. **Decrypt Sensitive Files**
   - Load encryption.key
   - Decrypt files listed in manifest.json under "encrypted_files"

4. **Restore Files**
   - Copy decrypted files to destination
   - Preserve directory structure

## Data Integrity