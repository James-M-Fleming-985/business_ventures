#!/usr/bin/env python3
"""
Update technical_constraints.framework to explicitly require @react-three/fiber
The orchestrator only reads technical_constraints, not code_generation_constraints
"""

import yaml
from pathlib import Path

base_dir = Path("/workspaces/business_ventures/feasibility_tool/SYSTEM-001 FEASIBILITY PLATFORM/FEATURE-002 Advanced 3D Visualizations")

# Updated framework specification that the orchestrator will actually use
UPDATED_FRAMEWORK = "React 18.2.0 + @react-three/fiber (use Canvas, useFrame, useThree - NO manual Scene/Renderer/Camera)"

layer_yamls = sorted(base_dir.glob("LAYER_*/LAYER-*.yaml"))

print(f"Updating {len(layer_yamls)} layer YAML files\n")

for yaml_file in layer_yamls:
    content = yaml_file.read_text()
    
    # Update the framework line in technical_constraints
    lines = content.split('\n')
    updated_lines = []
    
    for line in lines:
        if '  framework: "React 18.2.0"' in line:
            updated_lines.append(f'  framework: "{UPDATED_FRAMEWORK}"')
            print(f"✓ Updated {yaml_file.name}")
        else:
            updated_lines.append(line)
    
    yaml_file.write_text('\n'.join(updated_lines))

print("\n✅ All files updated with explicit @react-three/fiber requirement")
