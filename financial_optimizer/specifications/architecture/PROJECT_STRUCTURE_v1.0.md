# Financial Optimizer - Project Documentation

This directory contains user-facing documentation for the Financial Optimizer platform.

## Directory Structure

- `/specifications/` - Technical specifications and architecture documents
  - `/modules/` - Module-specific specifications
  - `/architecture/` - System architecture and subscription specifications
  - `/implementation/` - Implementation plans and change management
- `/dev_tools/` - Development tools and prototypes
  - `/prototypes/` - Prototype applications and experiments
  - `/tests/` - Test files and utilities
  - `/backups/` - Backup versions of files
- `/docs/` - User documentation (this directory)

## Key Files

- `simple_app.py` - Main application entry point with enhanced callback management
- `simple_app_legacy.py` - Legacy application entry point (deprecated)
- `core/` - Core application components and business logic
- `modules/` - Feature modules (Personal Mode, Business Mode, etc.)
- `services/` - External services and data providers
- `shared/` - Shared utilities and components
  - `enhanced_callbacks.py` - Enhanced callback management system
- `use_cases/` - Use case specific implementations

## Callback Architecture

The application now uses an Enhanced Callback Management System to prevent dependency cycles and callback conflicts:

- **EnhancedCallbackManager**: Centralized callback registration with conflict detection
- **Module Integration**: Each module registers callbacks through the centralized system
- **Dependency Resolution**: Automatic detection and prevention of circular dependencies
- **Performance Optimization**: Client-side state management reduces server load

See `ENHANCED_CALLBACK_MANAGEMENT_SPECIFICATION_v1.0.md` for detailed information.

## Development Workflow

1. Specifications are maintained in `/specifications/`
2. Prototypes and experiments go in `/dev_tools/prototypes/`
3. Tests are organized in `/dev_tools/tests/`
4. Production code lives in the appropriate module directories
5. Main application runs from `simple_app.py`

For detailed implementation guidance, see the specifications in `/specifications/implementation/`.
