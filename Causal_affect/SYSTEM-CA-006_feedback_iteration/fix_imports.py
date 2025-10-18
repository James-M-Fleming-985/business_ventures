#!/usr/bin/env python3
"""
Fix API router imports to use correct feature-based imports.
This ensures the system follows the spec's feature isolation architecture.
"""

import re
from pathlib import Path

# Map of incorrect imports to correct feature-based imports
IMPORT_FIXES = {
    "engagement.py": {
        "from app.models.engagement import": "from features.FEATURE_CA_006_02_engagement_tracking.models.metrics import",
        "from app.services.engagement import": "from features.FEATURE_CA_006_02_engagement_tracking.services.engagement_service import",
        "from app.models.user import User": "# User model handled separately",
    },
    "revenue.py": {
        "from app.models.revenue import": "from features.FEATURE_CA_006_03_revenue_tracking.models.revenue import",
        "from app.services.revenue import": "from features.FEATURE_CA_006_03_revenue_tracking.services.revenue_service import",
        "from app.models.user import User": "# User model handled separately",
    }
}

def fix_file_imports(file_path: Path, fixes: dict):
    """Fix imports in a single file."""
    if not file_path.exists():
        print(f"  ⚠️  File not found: {file_path}")
        return False
    
    content = file_path.read_text()
    original_content = content
    
    for old_pattern, new_pattern in fixes.items():
        if old_pattern in content:
            content = content.replace(old_pattern, new_pattern)
            print(f"  ✓ Fixed: {old_pattern}")
    
    if content != original_content:
        file_path.write_text(content)
        return True
    return False

def main():
    backend_path = Path("/workspaces/business_ventures/Causal_affect/SYSTEM-CA-006_feedback_iteration/src/backend")
    api_path = backend_path / "app" / "api"
    
    print("🔧 Fixing API router imports to use feature-based architecture...\n")
    
    fixed_count = 0
    for filename, fixes in IMPORT_FIXES.items():
        file_path = api_path / filename
        print(f"Processing {filename}:")
        if fix_file_imports(file_path, fixes):
            fixed_count += 1
        print()
    
    print(f"\n✅ Fixed {fixed_count} file(s)")
    print("\nNote: You may need to adjust model names to match actual definitions in feature directories.")

if __name__ == "__main__":
    main()
