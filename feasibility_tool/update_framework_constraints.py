#!/usr/bin/env python3
"""
Update framework field in technical_constraints to explicitly require @react-three/fiber
"""

import re
from pathlib import Path

base_dir = Path("/workspaces/business_ventures/feasibility_tool/SYSTEM-001 FEASIBILITY PLATFORM/FEATURE-002 Advanced 3D Visualizations")

NEW_FRAMEWORK = 'React 18.2.0 + @react-three/fiber (use Canvas, useFrame, useThree - NO manual Scene/Renderer/Camera)'

layer_yamls = list(base_dir.glob("LAYER_*/LAYER-*.yaml"))

print(f"Found {len(layer_yamls)} layer YAML files")

for yaml_file in sorted(layer_yamls):
    print(f"\nProcessing: {yaml_file.name}")
    
    content = yaml_file.read_text()
    
    # Find and replace the framework line in technical_constraints
    pattern = r'(technical_constraints:\s+language: "TypeScript"\s+framework: )"[^"]*"'
    
    new_content = re.sub(pattern, rf'\1"{NEW_FRAMEWORK}"', content)
    
    if new_content != content:
        yaml_file.write_text(new_content)
        print("  ✓ Updated framework constraint")
    else:
        print("  - No change needed or pattern not found")

print("\n✅ Done! All framework constraints updated.")
