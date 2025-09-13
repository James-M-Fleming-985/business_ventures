# Financial Optimizer - Directory Structure Specification

## Document Information
- **Document Version**: 2.0
- **Date**: July 21, 2025
- **Project**: Financial Optimizer - Personal Finance Management Platform
- **Author**: Technical Architecture Team

---

## Table of Contents

1. [Overview](#overview)
2. [Root Level Structure](#root-level-structure)
3. [Core Application Components](#core-application-components)
4. [Modules Structure](#modules-structure)
5. [Services Architecture](#services-architecture)
6. [Shared Utilities](#shared-utilities)
7. [Use Cases Implementation](#use-cases-implementation)
8. [Specifications Documentation](#specifications-documentation)
9. [Development Tools](#development-tools)
10. [Documentation Structure](#documentation-structure)
11. [Assets and Static Files](#assets-and-static-files)
12. [File Naming Conventions](#file-naming-conventions)
13. [Import Path Standards](#import-path-standards)

---

## Overview

The Financial Optimizer follows a modular, scalable directory structure that supports:
- **Goal-based subscription model** with tier-appropriate features
- **Modular architecture** with clear separation of concerns
- **Professional development practices** with organized specifications and tools
- **Scalable growth** from personal to business use cases

This structure enables systematic implementation following the 6-phase development plan while maintaining clean code organization and professional development standards.

---

## Root Level Structure

```
financial_optimizer/
├── README.md                    # Project overview and setup instructions
├── requirements.txt            # Python dependencies
├── mypy.ini                    # Type checking configuration
├── simple_app.py               # Main application entry point
├──
├── core/                       # Core application components
├── modules/                    # Feature modules
├── services/                   # External services and data integration
├── shared/                     # Shared utilities and components
├── use_cases/                  # Use case implementations
├──
├── specifications/             # Technical specifications and documentation
├── dev_tools/                  # Development tools and prototypes
├── docs/                       # Project documentation
├── assets/                     # Static assets (CSS, images, etc.)
└── __pycache__/                # Python bytecode cache (auto-generated)
```

---

## Core Application Components

The `core/` directory contains fundamental application infrastructure and business logic:

```
core/
├── __init__.py                 # Core package initialization
├── base_app.py                 # Base application framework
├── config.py                   # Configuration management
├── engines.py                  # Core calculation engines
├── factory.py                  # Component factories
├── factory_new.py              # Enhanced factory implementations
├── investment_calculations.py   # Investment calculation logic
├── investment_config.py        # Investment configuration settings
├── investment_forms.py         # Investment form components
├── capital_equipment_form.py   # Capital equipment forms
└── __pycache__/                # Python bytecode cache
```

### Key Components:

- **`base_app.py`**: Foundation application class with common functionality
- **`engines.py`**: Mathematical and financial calculation engines
- **`factory.py`**: Factory pattern implementations for component creation
- **`investment_*.py`**: Investment-specific business logic and forms
- **`config.py`**: Centralized configuration management

---

## Modules Structure

The `modules/` directory implements feature modules following the goal-based architecture:

```
modules/
├── __init__.py
├──
├── personal_mode/              # Personal Mode Module (Phase 1)
│   ├── __init__.py
│   ├── main.py                 # Main Personal Mode implementation
│   ├── utils.py                # Personal Mode utilities
│   ├── callbacks/              # Personal mode callbacks
│   │   └── __init__.py
│   ├── layout/                 # Personal mode UI layouts
│   │   └── __init__.py
│   ├── logic/                  # Personal mode business logic
│   │   └── __init__.py
│   ├── models/                 # Personal mode data models
│   │   └── __init__.py
│   └── __pycache__/
├──
├── business_mode/              # Business Mode Module
│   ├── __init__.py
│   ├── utils.py                # Business Mode utilities
│   ├── callbacks/              # Business mode callbacks
│   │   ├── __init__.py
│   │   └── main.py             # Main business callbacks
│   ├── layout/                 # Business mode UI layouts
│   │   ├── __init__.py
│   │   └── main.py             # Main business layouts
│   ├── logic/                  # Business mode business logic
│   │   └── __init__.py
│   ├── models/                 # Business mode data models
│   │   └── __init__.py
│   └── __pycache__/
├──
├── charity_mode/               # Charity Mode Module
│   ├── __init__.py
│   ├── utils.py                # Charity Mode utilities
│   ├── callbacks/              # Charity mode callbacks
│   │   └── __init__.py
│   ├── layout/                 # Charity mode UI layouts
│   │   └── __init__.py
│   ├── logic/                  # Charity mode business logic
│   │   └── __init__.py
│   ├── models/                 # Charity mode data models
│   │   └── __init__.py
│   └── __pycache__/
├──
├── non_profit_mode/            # Non-Profit Mode Module
│   ├── __init__.py
│   ├── utils.py                # Non-Profit Mode utilities
│   ├── callbacks/              # Non-profit mode callbacks
│   │   └── __init__.py
│   ├── layout/                 # Non-profit mode UI layouts
│   │   └── __init__.py
│   ├── logic/                  # Non-profit mode business logic
│   │   └── __init__.py
│   ├── models/                 # Non-profit mode data models
│   │   └── __init__.py
│   └── __pycache__/
├──
├── data_input/                 # Data Input Module (Phase 1)
│   ├── __init__.py
│   ├── utils.py
│   ├── callbacks/              # Data input callbacks
│   ├── layout/                 # Data input UI layouts
│   ├── logic/                  # Data processing logic
│   ├── models/                 # Data models
│   └── __pycache__/
├──
├── financial_dashboard/        # Financial Dashboard Module (Phase 2)
│   ├── __init__.py
│   ├── utils.py
│   ├── callbacks/              # Dashboard callbacks
│   ├── layout/                 # Dashboard layouts
│   ├── logic/                  # Dashboard logic
│   ├── models/                 # Dashboard data models
│   └── __pycache__/
├──
├── investment_mgmt/            # Investment Management Module (Phase 3)
│   ├── __init__.py
│   ├── utils.py
│   ├── callbacks/              # Investment callbacks
│   ├── layout/                 # Investment UI layouts
│   ├── logic/                  # Investment logic
│   ├── models/                 # Investment models
│   └── __pycache__/
├──
├── market_dashboard/           # Market Intelligence Module (Phase 4)
│   ├── utils.py
│   └── layout/                 # Market dashboard layouts
├──
├── investment_analysis/        # Advanced Analysis Module (Phase 5)
│   ├── __init__.py
│   ├── utils.py
│   ├── callbacks/              # Analysis callbacks
│   ├── layout/                 # Analysis layouts
│   ├── logic/                  # Analysis algorithms
│   ├── models/                 # Analysis models
│   └── __pycache__/
└──
└── financial_statements/       # Financial Statements Module (Phase 6)
    ├── __init__.py
    ├── utils.py
    ├── callbacks/              # Statement callbacks
    ├── layout/                 # Statement layouts
    ├── logic/                  # Statement logic
    ├── models/                 # Statement models
    └── __pycache__/
```

### Module Organization Principles:

- **Phase-Aligned**: Modules correspond to implementation phases
- **Self-Contained**: Each module has its own callbacks, layouts, logic, and models
- **Goal-Focused**: Features support goal-based subscription tiers
- **Scalable**: Easy to add new modules and extend existing ones

---

## Services Architecture

The `services/` directory handles external integrations and data services:

```
services/
├── __init__.py
├── market_data_services.py     # Market data API integration
├── market.data.py              # Market data processing
├── notification_service.py     # User notification system
├── sample_data.py              # Sample data generation
├── signal_generator.py         # Trading signal generation
├── storage.py                  # Data persistence layer
├── __pycache__/
├──
├── data_integration/           # Data Integration Services
│   └── data_integration.py
├──
├── market_analysis/            # Market Analysis Services
│   └── __init__.py
├──
├── market_data/                # Market Data Services
│   └── __init__.py
└──
└── reporting/                  # Reporting Services
    └── report_generator.py
```

### Service Categories:

- **Market Data**: Real-time and historical market information
- **Storage**: Database and file system interactions
- **Notifications**: User communication and alerts
- **Reporting**: Report generation and export
- **Integration**: Third-party service connections

---

## Shared Utilities

The `shared/` directory contains common utilities used across modules:

```
shared/
├── __init__.py
├── callbacks.py                # Shared callback functions
├── enhanced_callbacks.py       # Enhanced callback management system
├── error_handling.py           # Error handling utilities
├── io_utils.py                 # Input/output utilities
├── io.py                       # Additional I/O functions
├── layout_new.py               # Enhanced layout utilities
├── layout.py                   # Layout utilities
├── minimal_callbacks.py        # Minimal callback implementations
├── sample_data.py              # Shared sample data
├── stores.py                   # Data store implementations
├── types.py                    # Type definitions
├── __pycache__/
├──
├── analysis/                   # Shared Analysis Tools
│   └── __init__.py
└──
└── components/                 # Shared UI Components
    ├── action_items.py         # Action item components
    ├── header.py               # Header components
    └── __pycache__/
```

### Shared Utilities Purpose:

- **Code Reuse**: Common functionality shared across modules
- **Consistency**: Standardized error handling and layouts
- **Type Safety**: Central type definitions
- **Components**: Reusable UI components

---

## Use Cases Implementation

The `use_cases/` directory implements specific use case scenarios:

```
use_cases/
├── business/                   # Business Use Cases
│   ├── __init__.py
│   └── ...                     # Business-specific implementations
├──
├── charity/                    # Charity Use Cases
│   └── ...                     # Charity-specific implementations
├──
├── non_profit/                 # Non-Profit Use Cases
│   └── ...                     # Non-profit implementations
└──
└── personal/                   # Personal Use Cases
    └── ...                     # Personal finance implementations
```

### Use Case Categories:

- **Personal**: Individual financial management
- **Business**: Business financial optimization
- **Charity**: Charitable organization management
- **Non-Profit**: Non-profit organization finances

---

## Specifications Documentation

The `specifications/` directory contains all technical documentation:

```
specifications/
├── __init__.py
├── WORD_FORMATTING_GUIDE.md   # Documentation formatting standards
├── FINANCIAL_OPTIMIZER_DIRECTORY_STRUCTURE.md  # This document
├──
├── modules/                    # Module Specifications
│   ├── PERSONAL_MODE_SPECIFICATION.md
│   ├── PERSONAL_MODE_TECHNICAL_IMPLEMENTATION.md
│   ├── INVESTMENT_MANAGEMENT_SPECIFICATION.md
│   ├── INVESTMENT_MANAGEMENT_TECHNICAL_SPECIFICATION.md
│   └── ...                     # Additional module specs
├──
├── architecture/               # Architecture Specifications
│   ├── SUBSCRIPTION_MODEL_SPECIFICATION.md
│   ├── SUBSCRIPTION_TIERS_SPECIFICATION.md
│   └── ...                     # Additional architecture docs
└──
└── implementation/             # Implementation Plans
    ├── USER_WORKFLOW_IMPLEMENTATION_PLAN.md
    ├── SPECIFICATION_CHANGE_MANAGEMENT_DOCUMENT.md
    └── ...                     # Additional implementation plans
```

### Documentation Organization:

- **Modules**: Feature-specific specifications
- **Architecture**: System-wide design documents
- **Implementation**: Development plans and workflows

---

## Development Tools

The `dev_tools/` directory contains development utilities and prototypes:

```
dev_tools/
├── __init__.py
├── fix_simple_app.py           # Development utility scripts
├──
├── prototypes/                 # Prototype Applications
│   ├── app_architecture.py     # Architecture prototypes
│   ├── app_baseline.py         # Baseline implementations
│   ├── app_clean_baseline.py   # Clean baseline versions
│   ├── app_minimal_integration.py # Minimal integrations
│   ├── app_simple_baseline.py  # Simple baseline apps
│   ├── app_test.py             # Test applications
│   ├── app.py                  # Main app prototypes
│   ├── final_test.py           # Final testing scripts
│   ├── minimal_test.py         # Minimal test implementations
│   ├── run_enhanced_app.py     # Enhanced app runners
│   ├── simple_app.py           # Simple app prototypes
│   ├── test_quick.py           # Quick testing utilities
│   ├── cleanup_vscode.py       # Development cleanup tools
│   ├── dynamic_forms_workflow.py # Dynamic form workflows
│   ├── enhanced_workflow.py    # Enhanced workflows
│   ├── integration_workflow.py # Integration workflows
│   └── backups/                # Backup files
│       └── ...                 # Backup versions
└──
└── tests/                      # Test Files
    ├── test_app.bat            # Windows test scripts
    ├── test_app.py             # Application tests
    ├── test_simple.py          # Simple test cases
    └── ...                     # Additional test files
```

### Development Tools Purpose:

- **Prototypes**: Experimental implementations and proof-of-concepts
- **Tests**: Testing utilities and test cases
- **Backups**: Version backups and rollback capabilities
- **Utilities**: Development helper scripts

---

## Documentation Structure

The `docs/` directory contains project documentation:

```
docs/
├── PROJECT_STRUCTURE.md        # Project structure overview
├── REORGANIZATION_SUMMARY.md   # Recent reorganization summary
└── ...                         # Additional documentation
```

---

## Assets and Static Files

The `assets/` directory contains static assets:

```
assets/
└── css/
    └── style.css               # Application styling
```

Future expansion may include:
- `images/` - Application images and icons
- `fonts/` - Custom fonts
- `js/` - Client-side JavaScript files

---

## File Naming Conventions

### Python Files:
- **snake_case**: `investment_forms.py`, `market_data_services.py`
- **Descriptive**: Names clearly indicate file purpose
- **Module Alignment**: Names reflect module structure

### Documentation Files:
- **UPPER_CASE**: `PERSONAL_MODE_SPECIFICATION.md`
- **Descriptive**: Clear indication of document content
- **Versioned**: Include version information where applicable

### Directory Names:
- **snake_case**: `data_input/`, `financial_dashboard/`
- **Plural for Collections**: `modules/`, `services/`, `specifications/`
- **Singular for Single Purpose**: `core/`, `shared/`

---

## Import Path Standards

### Core Components:
```python
from core.investment_forms import InvestmentForms
from core.config import Config
from core.engines import CalculationEngine
```

### Module Imports:
```python
from modules.personal_mode import create_personal_mode_layout
from modules.personal_mode.utils import validate_allocation_percentages
from modules.data_input.utils import DataInputUtils
from modules.financial_dashboard.layout import DashboardLayout
```

### Service Imports:
```python
from services.market_data_services import MarketDataService
from services.storage import StorageService
```

### Shared Utilities:
```python
from shared.error_handling import ErrorHandler
from shared.types import FinancialData
from shared.components.header import HeaderComponent
```

### Import Guidelines:

- **Absolute Imports**: Use full module paths from project root
- **Explicit Imports**: Import specific classes/functions, not entire modules
- **Consistent Naming**: Follow established naming conventions
- **Grouped Imports**: Group by category (standard library, third-party, local)

---

## Directory Structure Benefits

### 1. **Scalability**
- Easy to add new modules and features
- Clear boundaries between components
- Supports team development

### 2. **Maintainability**
- Related code grouped together
- Clear separation of concerns
- Easy to locate and modify code

### 3. **Professional Standards**
- Industry-standard directory structure
- Proper documentation organization
- Clean development practices

### 4. **Goal-Based Architecture Support**
- Modules align with implementation phases
- Tier-appropriate feature organization
- Subscription model integration

### 5. **Development Efficiency**
- Clear file organization
- Standardized import paths
- Separated prototypes from production code

---

## Implementation Notes

### Current Status:
- ✅ Directory structure implemented and organized
- ✅ Core application components in place
- ✅ Module structure established
- ✅ Specifications properly documented
- ✅ Development tools separated

### Next Steps:
1. Continue Personal Mode implementation following phase structure
2. Implement goal-based subscription tier features
3. Expand module functionality according to specifications
4. Maintain clean separation between development and production code

---

## Conclusion

This directory structure provides a solid foundation for the Financial Optimizer platform development. It supports:

- **Systematic implementation** following the 6-phase development plan
- **Goal-based subscription model** with tier-appropriate features
- **Professional development practices** with proper organization
- **Scalable architecture** that can grow with the platform

The structure balances immediate development needs with long-term scalability requirements while maintaining clean, professional code organization standards.

---

**Document End**

*For questions or clarifications regarding this directory structure, please refer to the implementation team or technical architecture documentation.*
