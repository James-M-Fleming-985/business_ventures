#!/bin/bash

# Financial Optimizer File Creation Script
# Ensures files are created in the correct directories

echo "🏗️  Financial Optimizer File Creator"
echo "================================="
echo ""

# Function to create business mode specification
create_business_spec() {
    echo "Creating Business Mode Specification..."
    echo "Enter specification name (e.g., 'TAB_LAYOUT_STRATEGY'):"
    read spec_name
    
    version="1.0"
    date_str=$(date +"%-B %-d, %Y")
    filename="/workspaces/financial_optimizer/specifications/modules/BUSINESS_MODE_${spec_name}_v${version}.md"
    
    cat > "$filename" << EOF
# Business Mode ${spec_name} Specification
## Financial Optimizer Application - Business Mode Implementation

**Document Version**: ${version}
**Date**: ${date_str}
**Project**: Financial Optimizer - Business Mode ${spec_name}
**Author**: Technical Architecture Team
**Classification**: Internal Use

---

## Executive Summary

[Add specification content here]

---

## Main Section

[Content goes here]

---

**Document Status**: Draft
**Next Steps**: Define implementation steps

---

END OF SPECIFICATION
EOF
    
    echo "✅ Created: $filename"
    code "$filename"
}

# Function to create python module
create_python_module() {
    echo "Creating Python Module..."
    echo "Select target directory:"
    echo "1. /core/ (core functionality)"
    echo "2. /modules/ (feature modules)"
    echo "3. /services/ (service modules)"
    echo "4. /shared/ (shared utilities)"
    echo "5. /dev_tools/prototypes/ (prototypes)"
    
    read -p "Enter choice (1-5): " choice
    
    echo "Enter module name (without .py):"
    read module_name
    
    case $choice in
        1) target_dir="/workspaces/financial_optimizer/core" ;;
        2) target_dir="/workspaces/financial_optimizer/modules" ;;
        3) target_dir="/workspaces/financial_optimizer/services" ;;
        4) target_dir="/workspaces/financial_optimizer/shared" ;;
        5) target_dir="/workspaces/financial_optimizer/dev_tools/prototypes" ;;
        *) echo "Invalid choice"; exit 1 ;;
    esac
    
    filename="${target_dir}/${module_name}.py"
    date_str=$(date +"%Y-%m-%d")
    
    cat > "$filename" << EOF
"""${module_name} - Financial Optimizer

Created: ${date_str}
Author: Development Team
Purpose: [Add purpose description]
"""

from typing import Dict, List, Optional, Any
import logging

# Configure logging
logger = logging.getLogger(__name__)


class ${module_name^}:
    """[Add class description]"""

    def __init__(self):
        """Initialize ${module_name^}"""
        pass


def main():
    """Main function"""
    pass


if __name__ == "__main__":
    main()
EOF
    
    echo "✅ Created: $filename"
    code "$filename"
}

# Main menu
echo "What would you like to create?"
echo "1. Business Mode Specification"
echo "2. Personal Mode Specification"  
echo "3. Python Module"
echo "4. Implementation Plan"
echo "5. Exit"
echo ""

read -p "Enter your choice (1-5): " main_choice

case $main_choice in
    1) create_business_spec ;;
    2) echo "Personal Mode specs - use same pattern as business mode" ;;
    3) create_python_module ;;
    4) echo "Implementation plans go in /specifications/implementation/" ;;
    5) echo "Goodbye!"; exit 0 ;;
    *) echo "Invalid choice" ;;
esac
