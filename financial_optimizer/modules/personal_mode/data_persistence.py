#!/usr/bin/env python3
"""
User Data Persistence System for Financial Optimizer Personal Mode
Handles saving, loading, and managing user financial data across sessions.

Key Features:
- Save user financial data locally to prevent re-entry
- Auto-load saved data on startup
- Backup system with timestamps
- Reset to baseline functionality
- Export/import capabilities
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

class UserDataManager:
    """Manages user financial data persistence"""
    
    def __init__(self):
        self.data_dir = Path("data/user_data")
        self.current_data_file = self.data_dir / "current_user_data.json"
        self.backup_dir = self.data_dir / "backups"
        self.versions_dir = self.data_dir / "versions"
        self.changes_log = self.data_dir / "changes_log.json"
        
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self.versions_dir.mkdir(parents=True, exist_ok=True)
        
        # Default financial data structure
        self.default_data = {
            "personal_info": {
                "name": "",
                "age": 30,
                "location": "UK",
                "currency": "GBP"
            },
            "income": {
                "gross_salary": 45000,
                "bonuses": 5000,
                "freelance": 0,
                "benefits": 2000,
                "other_income": 0
            },
            "housing": {
                "mortgage_rent": 1200,
                "insurance": 100,
                "utilities": 150,
                "maintenance": 50,
                "council_tax": 120
            },
            "transport": {
                "car_payment": 300,
                "fuel": 120,
                "insurance": 80,
                "maintenance": 50,
                "public_transport": 0
            },
            "lifestyle": {
                "food_groceries": 400,
                "dining_out": 150,
                "entertainment": 100,
                "subscriptions": 50,
                "clothing": 100,
                "healthcare": 80,
                "personal_care": 50,
                "miscellaneous": 100
            },
            "financial": {
                "savings_account": 15000,
                "checking_account": 3000,
                "investments": 25000,
                "retirement": 35000,
                "emergency_fund": 10000
            },
            "debts": {
                "mortgage_balance": 180000,
                "car_loan": 15000,
                "student_loans": 25000,
                "credit_cards": 5000,
                "other_debt": 0
            },
            "goals": {
                "retirement_age": 65,
                "target_retirement_income": 3000,
                "house_deposit_target": 50000,
                "emergency_fund_months": 6
            },
            "metadata": {
                "created_date": None,
                "last_updated": None,
                "version": "1.0",
                "data_source": "manual_entry"
            }
        }
    
    def save_user_data(self, financial_data: Dict[str, Any], create_backup: bool = True, change_description: str = "Manual update") -> Dict[str, Any]:
        """
        Save user financial data with versioning and change tracking
        
        Args:
            financial_data: Complete financial data dictionary
            create_backup: Whether to create a timestamped backup
            change_description: Description of what changed (for audit trail)
            
        Returns:
            Status dictionary with success/error information
        """
        try:
            # Load current data to detect changes
            current_result = self.load_user_data()
            has_changes = False
            changes_detected = []
            
            if current_result["success"] and current_result["source"] != "defaults":
                changes_detected = self._detect_changes(current_result["data"], financial_data)
                has_changes = len(changes_detected) > 0
            
            # Update metadata
            current_time = datetime.now().isoformat()
            financial_data["metadata"]["last_updated"] = current_time
            
            if financial_data["metadata"]["created_date"] is None:
                financial_data["metadata"]["created_date"] = current_time
            
            # Create version snapshot if there are changes
            version_info = None
            if has_changes or current_result["source"] == "defaults":
                version_info = self._create_version_snapshot(financial_data, change_description, changes_detected)
            
            # Create backup if requested
            if create_backup:
                backup_result = self.create_backup(financial_data)
                if not backup_result["success"]:
                    return backup_result
            
            # Save current data
            with open(self.current_data_file, 'w') as f:
                json.dump(financial_data, f, indent=2, default=str)
            
            # Log the change
            if has_changes or current_result["source"] == "defaults":
                self._log_change(change_description, changes_detected, version_info)
            
            return {
                "success": True,
                "message": f"Financial data saved successfully at {current_time}",
                "file_path": str(self.current_data_file),
                "backup_created": create_backup,
                "changes_detected": len(changes_detected),
                "version_created": version_info is not None,
                "version_id": version_info["version_id"] if version_info else None
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error saving financial data: {str(e)}",
                "error": str(e)
            }
    
    def load_user_data(self) -> Dict[str, Any]:
        """
        Load user financial data or return defaults if none exists
        
        Returns:
            Financial data dictionary
        """
        try:
            if self.current_data_file.exists():
                with open(self.current_data_file, 'r') as f:
                    data = json.load(f)
                
                # Validate and merge with defaults to ensure all fields exist
                merged_data = self._merge_with_defaults(data)
                
                return {
                    "success": True,
                    "data": merged_data,
                    "source": "saved_data",
                    "last_updated": merged_data["metadata"].get("last_updated", "Unknown")
                }
            else:
                # Return default data if no saved data exists
                default_copy = self.default_data.copy()
                default_copy["metadata"]["created_date"] = datetime.now().isoformat()
                
                return {
                    "success": True,
                    "data": default_copy,
                    "source": "defaults",
                    "message": "No saved data found. Using default values."
                }
                
        except Exception as e:
            # Return defaults if loading fails
            return {
                "success": False,
                "data": self.default_data.copy(),
                "source": "defaults_due_to_error",
                "error": str(e),
                "message": f"Error loading saved data: {str(e)}. Using defaults."
            }
    
    def create_backup(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a timestamped backup of financial data
        
        Args:
            financial_data: Financial data to backup
            
        Returns:
            Status dictionary
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_file = self.backup_dir / f"financial_data_backup_{timestamp}.json"
            
            with open(backup_file, 'w') as f:
                json.dump(financial_data, f, indent=2, default=str)
            
            return {
                "success": True,
                "message": f"Backup created: {backup_file.name}",
                "backup_path": str(backup_file)
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error creating backup: {str(e)}",
                "error": str(e)
            }
    
    def list_backups(self) -> Dict[str, Any]:
        """
        List all available backups
        
        Returns:
            Dictionary with backup list and metadata
        """
        try:
            backup_files = list(self.backup_dir.glob("financial_data_backup_*.json"))
            backup_files.sort(reverse=True)  # Most recent first
            
            backups = []
            for backup_file in backup_files:
                # Extract timestamp from filename
                timestamp_str = backup_file.stem.replace("financial_data_backup_", "")
                try:
                    timestamp = datetime.strptime(timestamp_str, "%Y%m%d_%H%M%S")
                    formatted_date = timestamp.strftime("%Y-%m-%d %H:%M:%S")
                except:
                    formatted_date = timestamp_str
                
                backups.append({
                    "filename": backup_file.name,
                    "path": str(backup_file),
                    "timestamp": timestamp_str,
                    "formatted_date": formatted_date,
                    "size_kb": round(backup_file.stat().st_size / 1024, 2)
                })
            
            return {
                "success": True,
                "backups": backups,
                "count": len(backups)
            }
            
        except Exception as e:
            return {
                "success": False,
                "backups": [],
                "count": 0,
                "error": str(e)
            }
    
    def restore_from_backup(self, backup_filename: str) -> Dict[str, Any]:
        """
        Restore financial data from a specific backup
        
        Args:
            backup_filename: Name of the backup file to restore
            
        Returns:
            Status dictionary
        """
        try:
            backup_path = self.backup_dir / backup_filename
            
            if not backup_path.exists():
                return {
                    "success": False,
                    "message": f"Backup file not found: {backup_filename}"
                }
            
            # Load backup data
            with open(backup_path, 'r') as f:
                backup_data = json.load(f)
            
            # Create a backup of current data before restoring
            current_result = self.load_user_data()
            if current_result["success"]:
                self.create_backup(current_result["data"])
            
            # Restore the backup as current data
            restore_result = self.save_user_data(backup_data, create_backup=False)
            
            if restore_result["success"]:
                return {
                    "success": True,
                    "message": f"Successfully restored from backup: {backup_filename}",
                    "restored_from": backup_filename
                }
            else:
                return restore_result
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error restoring from backup: {str(e)}",
                "error": str(e)
            }
    
    def reset_to_defaults(self) -> Dict[str, Any]:
        """
        Reset user data to default values
        
        Returns:
            Status dictionary
        """
        try:
            # Create backup of current data before reset
            current_result = self.load_user_data()
            if current_result["success"]:
                backup_result = self.create_backup(current_result["data"])
                if not backup_result["success"]:
                    return {
                        "success": False,
                        "message": "Failed to create backup before reset"
                    }
            
            # Reset to defaults
            default_copy = self.default_data.copy()
            default_copy["metadata"]["created_date"] = datetime.now().isoformat()
            
            reset_result = self.save_user_data(default_copy, create_backup=False)
            
            if reset_result["success"]:
                return {
                    "success": True,
                    "message": "Financial data reset to defaults. Previous data backed up.",
                    "backup_created": True
                }
            else:
                return reset_result
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error resetting to defaults: {str(e)}",
                "error": str(e)
            }
    
    def export_data(self, export_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Export financial data to a specified location
        
        Args:
            export_path: Path to export file (optional)
            
        Returns:
            Status dictionary with export information
        """
        try:
            # Load current data
            load_result = self.load_user_data()
            if not load_result["success"]:
                return load_result
            
            # Generate export filename if not provided
            if export_path is None:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                export_path = f"financial_data_export_{timestamp}.json"
            
            # Export data
            with open(export_path, 'w') as f:
                json.dump(load_result["data"], f, indent=2, default=str)
            
            return {
                "success": True,
                "message": f"Financial data exported to: {export_path}",
                "export_path": export_path
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error exporting data: {str(e)}",
                "error": str(e)
            }
    
    def import_data(self, import_path: str) -> Dict[str, Any]:
        """
        Import financial data from a file
        
        Args:
            import_path: Path to import file
            
        Returns:
            Status dictionary
        """
        try:
            if not os.path.exists(import_path):
                return {
                    "success": False,
                    "message": f"Import file not found: {import_path}"
                }
            
            # Load import data
            with open(import_path, 'r') as f:
                import_data = json.load(f)
            
            # Validate and merge with defaults
            merged_data = self._merge_with_defaults(import_data)
            
            # Save imported data
            save_result = self.save_user_data(merged_data, create_backup=True)
            
            if save_result["success"]:
                return {
                    "success": True,
                    "message": f"Financial data imported from: {import_path}",
                    "import_path": import_path,
                    "backup_created": True
                }
            else:
                return save_result
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error importing data: {str(e)}",
                "error": str(e)
            }
    
    def _merge_with_defaults(self, user_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge user data with defaults to ensure all required fields exist
        
        Args:
            user_data: User's financial data
            
        Returns:
            Merged data dictionary
        """
        def deep_merge(default: dict, user: dict) -> dict:
            result = default.copy()
            for key, value in user.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value
            return result
        
        return deep_merge(self.default_data, user_data)
    
    def _detect_changes(self, old_data: Dict[str, Any], new_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Detect changes between old and new financial data
        
        Args:
            old_data: Previous financial data
            new_data: New financial data
            
        Returns:
            List of changes with details
        """
        changes = []
        
        def compare_values(old_val, new_val, path: str):
            if old_val != new_val:
                # Determine change type
                if isinstance(old_val, (int, float)) and isinstance(new_val, (int, float)):
                    change_type = "value_change"
                    difference = new_val - old_val
                    percent_change = (difference / old_val * 100) if old_val != 0 else float('inf')
                else:
                    change_type = "content_change"
                    difference = None
                    percent_change = None
                
                changes.append({
                    "field": path,
                    "change_type": change_type,
                    "old_value": old_val,
                    "new_value": new_val,
                    "difference": difference,
                    "percent_change": percent_change,
                    "timestamp": datetime.now().isoformat()
                })
        
        def recursive_compare(old_dict, new_dict, path=""):
            for key in set(list(old_dict.keys()) + list(new_dict.keys())):
                current_path = f"{path}.{key}" if path else key
                
                if key not in old_dict:
                    changes.append({
                        "field": current_path,
                        "change_type": "field_added",
                        "old_value": None,
                        "new_value": new_dict[key],
                        "difference": None,
                        "percent_change": None,
                        "timestamp": datetime.now().isoformat()
                    })
                elif key not in new_dict:
                    changes.append({
                        "field": current_path,
                        "change_type": "field_removed",
                        "old_value": old_dict[key],
                        "new_value": None,
                        "difference": None,
                        "percent_change": None,
                        "timestamp": datetime.now().isoformat()
                    })
                elif isinstance(old_dict[key], dict) and isinstance(new_dict[key], dict):
                    recursive_compare(old_dict[key], new_dict[key], current_path)
                else:
                    compare_values(old_dict[key], new_dict[key], current_path)
        
        # Skip metadata comparison to avoid noise
        old_data_filtered = {k: v for k, v in old_data.items() if k != "metadata"}
        new_data_filtered = {k: v for k, v in new_data.items() if k != "metadata"}
        
        recursive_compare(old_data_filtered, new_data_filtered)
        return changes
    
    def _create_version_snapshot(self, financial_data: Dict[str, Any], description: str, changes: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Create a versioned snapshot of financial data
        
        Args:
            financial_data: Financial data to snapshot
            description: Description of changes
            changes: List of detected changes
            
        Returns:
            Version information
        """
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            version_id = f"v_{timestamp}"
            version_file = self.versions_dir / f"{version_id}.json"
            
            version_data = {
                "version_id": version_id,
                "timestamp": datetime.now().isoformat(),
                "description": description,
                "changes": changes,
                "change_count": len(changes),
                "financial_data": financial_data
            }
            
            with open(version_file, 'w') as f:
                json.dump(version_data, f, indent=2, default=str)
            
            return {
                "version_id": version_id,
                "version_file": str(version_file),
                "change_count": len(changes)
            }
            
        except Exception as e:
            print(f"Warning: Could not create version snapshot: {e}")
            return None
    
    def _log_change(self, description: str, changes: List[Dict[str, Any]], version_info: Dict[str, Any]):
        """
        Log change to the changes log file
        
        Args:
            description: Change description
            changes: List of changes
            version_info: Version information
        """
        try:
            # Load existing log
            if self.changes_log.exists():
                with open(self.changes_log, 'r') as f:
                    log_data = json.load(f)
            else:
                log_data = {"changes": []}
            
            # Add new change entry
            log_entry = {
                "timestamp": datetime.now().isoformat(),
                "description": description,
                "change_count": len(changes),
                "version_id": version_info["version_id"] if version_info else None,
                "major_changes": [
                    {
                        "field": change["field"],
                        "old_value": change["old_value"],
                        "new_value": change["new_value"],
                        "change_type": change["change_type"]
                    }
                    for change in changes[:5]  # Store top 5 changes in summary
                ]
            }
            
            log_data["changes"].insert(0, log_entry)  # Most recent first
            
            # Keep only last 50 changes to prevent file bloat
            log_data["changes"] = log_data["changes"][:50]
            
            # Save updated log
            with open(self.changes_log, 'w') as f:
                json.dump(log_data, f, indent=2, default=str)
                
        except Exception as e:
            print(f"Warning: Could not log change: {e}")
    
    def get_version_history(self) -> Dict[str, Any]:
        """
        Get version history with change summaries
        
        Returns:
            Dictionary with version history
        """
        try:
            versions = []
            version_files = list(self.versions_dir.glob("v_*.json"))
            version_files.sort(reverse=True)  # Most recent first
            
            for version_file in version_files:
                try:
                    with open(version_file, 'r') as f:
                        version_data = json.load(f)
                    
                    versions.append({
                        "version_id": version_data["version_id"],
                        "timestamp": version_data["timestamp"],
                        "description": version_data["description"],
                        "change_count": version_data["change_count"],
                        "file_size_kb": round(version_file.stat().st_size / 1024, 2)
                    })
                except Exception as e:
                    print(f"Warning: Could not read version {version_file}: {e}")
            
            return {
                "success": True,
                "versions": versions,
                "total_versions": len(versions)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "versions": [],
                "total_versions": 0
            }
    
    def revert_to_version(self, version_id: str, create_backup: bool = True) -> Dict[str, Any]:
        """
        Revert financial data to a specific version
        
        Args:
            version_id: Version ID to revert to
            create_backup: Whether to backup current state before reverting
            
        Returns:
            Status dictionary
        """
        try:
            version_file = self.versions_dir / f"{version_id}.json"
            
            if not version_file.exists():
                return {
                    "success": False,
                    "message": f"Version not found: {version_id}"
                }
            
            # Load version data
            with open(version_file, 'r') as f:
                version_data = json.load(f)
            
            # Create backup of current state if requested
            if create_backup:
                current_result = self.load_user_data()
                if current_result["success"]:
                    backup_result = self.create_backup(current_result["data"])
                    if not backup_result["success"]:
                        return {
                            "success": False,
                            "message": "Failed to create backup before revert"
                        }
            
            # Revert to version data
            financial_data = version_data["financial_data"]
            financial_data["metadata"]["last_updated"] = datetime.now().isoformat()
            
            # Save reverted data
            revert_result = self.save_user_data(
                financial_data, 
                create_backup=False, 
                change_description=f"Reverted to version {version_id}"
            )
            
            if revert_result["success"]:
                return {
                    "success": True,
                    "message": f"Successfully reverted to version {version_id}",
                    "reverted_to": version_id,
                    "backup_created": create_backup
                }
            else:
                return revert_result
                
        except Exception as e:
            return {
                "success": False,
                "message": f"Error reverting to version: {str(e)}",
                "error": str(e)
            }
    
    def get_change_log(self, limit: int = 20) -> Dict[str, Any]:
        """
        Get recent change log entries
        
        Args:
            limit: Maximum number of entries to return
            
        Returns:
            Dictionary with change log entries
        """
        try:
            if not self.changes_log.exists():
                return {
                    "success": True,
                    "changes": [],
                    "total_changes": 0
                }
            
            with open(self.changes_log, 'r') as f:
                log_data = json.load(f)
            
            changes = log_data.get("changes", [])[:limit]
            
            return {
                "success": True,
                "changes": changes,
                "total_changes": len(log_data.get("changes", [])),
                "showing": len(changes)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "changes": [],
                "total_changes": 0
            }
    
    def compare_versions(self, version_id_1: str, version_id_2: str) -> Dict[str, Any]:
        """
        Compare two versions of financial data
        
        Args:
            version_id_1: First version ID
            version_id_2: Second version ID
            
        Returns:
            Comparison results
        """
        try:
            # Load both versions
            version_file_1 = self.versions_dir / f"{version_id_1}.json"
            version_file_2 = self.versions_dir / f"{version_id_2}.json"
            
            if not version_file_1.exists():
                return {"success": False, "message": f"Version not found: {version_id_1}"}
            
            if not version_file_2.exists():
                return {"success": False, "message": f"Version not found: {version_id_2}"}
            
            with open(version_file_1, 'r') as f:
                data_1 = json.load(f)["financial_data"]
            
            with open(version_file_2, 'r') as f:
                data_2 = json.load(f)["financial_data"]
            
            # Detect differences
            differences = self._detect_changes(data_1, data_2)
            
            return {
                "success": True,
                "version_1": version_id_1,
                "version_2": version_id_2,
                "differences": differences,
                "difference_count": len(differences)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Error comparing versions: {str(e)}"
            }
    
    def get_data_summary(self) -> Dict[str, Any]:
        """
        Get summary information about saved data
        
        Returns:
            Summary dictionary
        """
        try:
            load_result = self.load_user_data()
            backup_result = self.list_backups()
            
            if load_result["success"]:
                data = load_result["data"]
                
                return {
                    "success": True,
                    "has_saved_data": load_result["source"] != "defaults",
                    "last_updated": data["metadata"].get("last_updated", "Never"),
                    "created_date": data["metadata"].get("created_date", "Never"),
                    "version": data["metadata"].get("version", "Unknown"),
                    "backup_count": backup_result.get("count", 0),
                    "current_file_exists": self.current_data_file.exists(),
                    "data_source": load_result["source"]
                }
            else:
                return {
                    "success": False,
                    "error": load_result.get("error", "Unknown error")
                }
                
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Global instance for easy access
user_data_manager = UserDataManager()
