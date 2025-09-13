# XML Workspace - Financial Optimizer

## Purpose
This directory contains MS Project XML files for automated reporting and milestone management.

## Project Type
**Financial Analysis** - Repository-specific project management data

## Files
- `Financial Optimization Project.xml` - Financial Analysis project XML file

## Repository-Specific Structure
This XML workspace is tailored for **financial_optimizer** and contains:
- Project structure specific to Financial Analysis
- Milestones relevant to this repository's goals
- Timeline data for financial_optimizer development phases

## Usage
1. **PowerPoint Generation**: Repository-specific Safran PowerPoint generator reads from these XML files
2. **Milestone Queries**: Control Tower milestone system uses this project data
3. **Progress Tracking**: Project progress specific to financial_optimizer
4. **Sync Operations**: Files updated via repository-specific MS Project processes

## Sync Workflow
1. Update repository-specific .mpp files in MS Project
2. Run Control Tower sync for this repo: `python3 control_tower.py ms-project --repo financial_optimizer --action sync`
3. XML files automatically updated with financial_optimizer data
4. PowerPoint reports regenerated with current Financial Analysis data

## Directory Structure
```
xml_workspace/
├── README.md                    # This file
├── Financial Optimization Project.xml # Financial Analysis project data

## Integration Points
- **Control Tower**: Repository-aware project management
- **PowerPoint Generator**: Generates financial_optimizer-specific presentations
- **Sync Scripts**: Repository-specific sync processes

## Important Notes
- **NOT shared across repositories**: Each repo has its own project data
- **Repository-specific**: XML files contain Financial Analysis project structure
- **Independent**: Changes here only affect financial_optimizer presentations

## Last Updated
2025-08-08 08:38:53 - Repository-specific XML workspace setup
