#!/usr/bin/env python3
"""
Add technical_constraints section to all layer YAML files.
This is the CRITICAL missing configuration that caused Python generation instead of TypeScript.
"""

import re
from pathlib import Path

# Directory containing layer folders
base_dir = Path("/workspaces/business_ventures/feasibility_tool/SYSTEM-001 FEASIBILITY PLATFORM/FEATURE-002 Advanced 3D Visualizations")

# Technical constraints section to add
TECH_CONSTRAINTS = """
# ====================================================================================
# TECHNICAL CONSTRAINTS - CRITICAL: Tells orchestrator which language to generate
# ====================================================================================
technical_constraints:
  language: "TypeScript"
  framework: "React 18.2.0"
  output_file_type: ".tsx"
  runtime: "Browser (Node.js 18+ for build)"
"""

# Find all layer YAML files
layer_yamls = list(base_dir.glob("LAYER_*/LAYER-*.yaml"))

print(f"Found {len(layer_yamls)} layer YAML files")

for yaml_file in sorted(layer_yamls):
    print(f"\nProcessing: {yaml_file.name}")
    
    content = yaml_file.read_text()
    
    # Check if already has technical_constraints
    if "technical_constraints:" in content:
        print("  ✓ Already has technical_constraints section - skipping")
        continue
    
    # Find the line after derivation_rationale section ends
    # Look for the pattern: "derivation_rationale: |" followed by indented text, then a separator line
    pattern = r'(derivation_rationale:.*?\n(?:    .*\n)*)\n(# =+\n# REQUIREMENT DEFINITION)'
    
    match = re.search(pattern, content, re.MULTILINE)
    
    if match:
        # Insert technical_constraints between derivation_rationale and REQUIREMENT DEFINITION
        new_content = content[:match.end(1)] + TECH_CONSTRAINTS + "\n" + content[match.start(2):]
        
        yaml_file.write_text(new_content)
        print("  ✓ Added technical_constraints section")
    else:
        print("  ✗ Could not find insertion point - manual review needed")
        print(f"    Pattern not found in {yaml_file.name}")

print("\n✅ Done! All layer YAMLs updated.")
print("\nNext step: Run build_feature.py again to generate TypeScript/React code")
