#!/usr/bin/env python3
"""
Demonstration of JSON File Export Location and Format
"""

import json
import os
from datetime import datetime
from pathlib import Path

def demonstrate_export_locations():
    """Show where JSON files are saved on different operating systems"""
    
    print("📁 JSON Export File Locations")
    print("=" * 50)
    
    # Get user's home directory
    home_dir = Path.home()
    
    # Default download locations by OS
    download_locations = {
        "Windows": home_dir / "Downloads",
        "macOS": home_dir / "Downloads", 
        "Linux": home_dir / "Downloads"
    }
    
    print("\n🎯 Default Browser Download Locations:")
    for os_name, path in download_locations.items():
        print(f"   {os_name}: {path}")
    
    # Sample filename generation
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    sample_filename = f"Personal_Finance_Profile_{timestamp}.json"
    
    print(f"\n📄 Sample Export Filename:")
    print(f"   {sample_filename}")
    
    # Sample profile structure
    sample_profile = {
        "profileMetadata": {
            "profileName": "Personal Finance Profile",
            "version": "1.0",
            "lastModified": datetime.now().isoformat(),
            "autoSaveEnabled": True
        },
        "financialData": {
            "income": {"grossSalary": 4500, "netSalary": 3200},
            "expenses": {"housing": 1200, "food": 400},
            "assets": {"savings": 15000, "investments": 25000},
            "liabilities": {"mortgage": 150000, "creditCards": 3000}
        },
        "exportMetadata": {
            "exportedAt": datetime.now().isoformat(),
            "exportVersion": "1.0",
            "fileFormat": "Financial Optimizer JSON Profile"
        }
    }
    
    # Show file size
    json_string = json.dumps(sample_profile, indent=2)
    file_size = len(json_string.encode('utf-8'))
    
    print(f"\n📊 Export File Details:")
    print(f"   File Size: {file_size:,} bytes ({file_size/1024:.1f} KB)")
    print(f"   Format: UTF-8 encoded JSON")
    print(f"   Structure: {len(sample_profile)} main sections")
    
    # Check current Downloads folder
    downloads_path = home_dir / "Downloads"
    if downloads_path.exists():
        print(f"\n✅ Your Downloads folder exists at:")
        print(f"   {downloads_path}")
        
        # Check for existing financial profile files
        existing_files = list(downloads_path.glob("*financial_profile*.json"))
        if existing_files:
            print(f"\n📋 Existing financial profile exports found:")
            for file in existing_files[-3:]:  # Show last 3
                stat = file.stat()
                modified = datetime.fromtimestamp(stat.st_mtime)
                print(f"   {file.name} ({modified.strftime('%Y-%m-%d %H:%M')})")
        else:
            print(f"\n📝 No existing financial profile exports found")
    else:
        print(f"\n⚠️  Downloads folder not found at {downloads_path}")
    
    return sample_filename, json_string

def show_browser_download_behavior():
    """Explain how browser downloads work"""
    
    print("\n" + "=" * 50)
    print("🌐 Browser Download Behavior")
    print("=" * 50)
    
    print("\n📥 How Export Works:")
    print("   1. User clicks 'Export Profile' button")
    print("   2. JavaScript creates data URL with JSON content")
    print("   3. Browser triggers automatic download")
    print("   4. File saved to default Downloads folder")
    print("   5. Success notification shown to user")
    
    print("\n⚙️  User Can Control:")
    print("   • Change browser download location in settings")
    print("   • Choose 'Save As' to pick different location")
    print("   • Rename file during download")
    print("   • Move file after download")
    
    print("\n🔒 Security & Privacy:")
    print("   • Files never leave user's device")
    print("   • No server storage required")
    print("   • User has complete control over data")
    print("   • Can backup to cloud storage if desired")

if __name__ == "__main__":
    filename, content = demonstrate_export_locations()
    show_browser_download_behavior()
    
    print(f"\n🎉 Ready to export! Files will be saved as:")
    print(f"   {Path.home() / 'Downloads' / filename}")
