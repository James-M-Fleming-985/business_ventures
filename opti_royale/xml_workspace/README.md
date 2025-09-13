# XML Workspace - Opti Royale

## Purpose
This directory contains MS Project XML files for automated reporting and milestone management.

## Project Type
**Optimization Platform** - Repository-specific project management data

## Files
- `Optimization Royale Project.xml` - Optimization Platform project XML file

## Repository-Specific Structure
This XML workspace is tailored for **opti_royale** and contains:
- Project structure specific to Optimization Platform
- Milestones relevant to this repository's goals
- Timeline data for opti_royale development phases

## Usage
1. **PowerPoint Generation**: Repository-specific Safran PowerPoint generator reads from these XML files
2. **Milestone Queries**: Control Tower milestone system uses this project data
3. **Progress Tracking**: Project progress specific to opti_royale
4. **Sync Operations**: Files updated via repository-specific MS Project processes

## Sync Workflow
1. Update repository-specific .mpp files in MS Project
2. Run Control Tower sync for this repo: `python3 control_tower.py ms-project --repo opti_royale --action sync`
3. XML files automatically updated with opti_royale data
4. PowerPoint reports regenerated with current Optimization Platform data

## Directory Structure
```
xml_workspace/
├── README.md                    # This file
├── Optimization Royale Project.xml # Optimization Platform project data

## Integration Points
- **Control Tower**: Repository-aware project management
- **PowerPoint Generator**: Generates opti_royale-specific presentations
- **Sync Scripts**: Repository-specific sync processes

## Important Notes
- **NOT shared across repositories**: Each repo has its own project data
- **Repository-specific**: XML files contain Optimization Platform project structure
- **Independent**: Changes here only affect opti_royale presentations

## Last Updated
2025-08-08 08:38:53 - Repository-specific XML workspace setup
