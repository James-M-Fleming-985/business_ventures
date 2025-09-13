#!/usr/bin/env python3
"""
User Data Repository for Financial Optimizer Personal Mode
Handles all data persistence operations following repository pattern.

This module provides:
- Clean separation between data access and business logic
- Standardized CRUD operations for user financial data
- Backup and recovery functionality
- Import/export capabilities
"""

import json
import os
from datetime import datetime
from typing import Dict, Any, Optional, List
from pathlib import Path

class UserDataRepository:
    """Repository pattern implementation for user financial data persistence"""
    
    def __init__(self):
        self.data_dir = Path("data/user_data")
        self.current_data_file = self.data_dir / "current_user_data.json"
        self.backup_dir = self.data_dir / "backups"
        
        # Create directories if they don't exist
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
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
    
    def save(self, financial_data: Dict[str, Any], create_backup: bool = True) -> Dict[str, Any]:
        """
        Save user financial data with optional backup creation
        
        Args:
            financial_data: Complete financial data dictionary
            create_backup: Whether to create a timestamped backup
            
        Returns:
            Status dictionary with success/error information
        """
        try:
            # Update metadata
            current_time = datetime.now().isoformat()
            financial_data["metadata"]["last_updated"] = current_time
            
            if financial_data["metadata"]["created_date"] is None:
                financial_data["metadata"]["created_date"] = current_time
            
            # Create backup if requested
            if create_backup:
                backup_result = self._create_backup(financial_data)
                if not backup_result["success"]:
                    return backup_result
            
            # Save current data
            with open(self.current_data_file, 'w') as f:
                json.dump(financial_data, f, indent=2, default=str)
            
            return {
                "success": True,
                "message": f"Financial data saved successfully at {current_time}",
                "file_path": str(self.current_data_file),
                "backup_created": create_backup
            }
            
        except Exception as e:
            return {
                "success": False,
                "message": f"Error saving financial data: {str(e)}",
                "error": str(e)
            }
    
    def load(self) -> Dict[str, Any]:
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
    
    def get_backups(self) -> List[Dict[str, Any]]:
        """
        Get list of all available backups
        
        Returns:
            List of backup information dictionaries
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
            
            return backups
            
        except Exception as e:
            return []
    
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
            current_result = self.load()
            if current_result["success"]:
                self._create_backup(current_result["data"])
            
            # Restore the backup as current data
            restore_result = self.save(backup_data, create_backup=False)
            
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
            current_result = self.load()
            if current_result["success"]:
                backup_result = self._create_backup(current_result["data"])
                if not backup_result["success"]:
                    return {
                        "success": False,
                        "message": "Failed to create backup before reset"
                    }
            
            # Reset to defaults
            default_copy = self.default_data.copy()
            default_copy["metadata"]["created_date"] = datetime.now().isoformat()
            
            reset_result = self.save(default_copy, create_backup=False)
            
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
    
    def export_to_file(self, export_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Export financial data to a specified location
        
        Args:
            export_path: Path to export file (optional)
            
        Returns:
            Status dictionary with export information
        """
        try:
            # Load current data
            load_result = self.load()
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
    
    def import_from_file(self, import_path: str) -> Dict[str, Any]:
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
            save_result = self.save(merged_data, create_backup=True)
            
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
    
    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary information about saved data
        
        Returns:
            Summary dictionary
        """
        try:
            load_result = self.load()
            backups = self.get_backups()
            
            if load_result["success"]:
                data = load_result["data"]
                
                return {
                    "success": True,
                    "has_saved_data": load_result["source"] != "defaults",
                    "last_updated": data["metadata"].get("last_updated", "Never"),
                    "created_date": data["metadata"].get("created_date", "Never"),
                    "version": data["metadata"].get("version", "Unknown"),
                    "backup_count": len(backups),
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
    
    def _create_backup(self, financial_data: Dict[str, Any]) -> Dict[str, Any]:
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

# Global repository instance for easy access across the application
user_data_repository = UserDataRepository()
