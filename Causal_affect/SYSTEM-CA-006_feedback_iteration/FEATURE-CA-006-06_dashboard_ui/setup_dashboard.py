#!/usr/bin/env python3
"""
Dashboard UI Setup Script
=========================
This script orchestrates the creation of the complete React dashboard application
by executing all layer implementation generators in the correct order.

FEATURE-CA-006-06: Dashboard User Interface
"""

import sys
import subprocess
from pathlib import Path
import shutil
import json

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

def print_header(message):
    """Print a formatted header."""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}")
    print(f"{message}")
    print(f"{'='*70}{Colors.ENDC}\n")

def print_step(emoji, message):
    """Print a step with emoji."""
    print(f"{emoji} {message}")

def print_success(message):
    """Print success message."""
    print(f"{Colors.OKGREEN}✅ {message}{Colors.ENDC}")

def print_error(message):
    """Print error message."""
    print(f"{Colors.FAIL}❌ {message}{Colors.ENDC}")

def print_info(message):
    """Print info message."""
    print(f"{Colors.OKCYAN}ℹ️  {message}{Colors.ENDC}")


def check_node_installed():
    """Check if Node.js and npm are installed."""
    print_step("🔍", "Checking for Node.js and npm...")
    try:
        node_result = subprocess.run(['node', '--version'], capture_output=True, text=True)
        npm_result = subprocess.run(['npm', '--version'], capture_output=True, text=True)
        
        if node_result.returncode == 0 and npm_result.returncode == 0:
            print_success(f"Node.js {node_result.stdout.strip()} found")
            print_success(f"npm {npm_result.stdout.strip()} found")
            return True
        else:
            print_error("Node.js or npm not found")
            return False
    except FileNotFoundError:
        print_error("Node.js or npm not installed")
        print_info("Please install Node.js from https://nodejs.org/")
        return False


def create_output_directory(base_path):
    """Create the output directory for the React app."""
    output_dir = base_path / "dashboard-app"
    
    if output_dir.exists():
        print_step("🗑️", f"Removing existing directory: {output_dir}")
        shutil.rmtree(output_dir)
    
    print_step("📁", f"Creating output directory: {output_dir}")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    return output_dir


def run_layer_generator(layer_path, output_dir):
    """Run a layer's implementation generator."""
    layer_name = layer_path.name
    impl_file = layer_path / "src" / "implementation.py"
    
    if not impl_file.exists():
        print_error(f"Implementation file not found: {impl_file}")
        return False
    
    print_step("🤖", f"Running generator for {layer_name}...")
    
    # Import and execute the generator
    try:
        # Add layer src to Python path
        sys.path.insert(0, str(impl_file.parent))
        
        # Import the implementation module
        import importlib.util
        spec = importlib.util.spec_from_file_location("layer_impl", impl_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Check if setup_react_project function exists
        if hasattr(module, 'setup_react_project'):
            print_info(f"Executing setup_react_project() from {layer_name}")
            module.setup_react_project(output_dir)
            print_success(f"Layer {layer_name} generation complete")
            return True
        elif hasattr(module, 'create_react_app_structure'):
            print_info(f"Found create_react_app_structure() in {layer_name}")
            # Just note it, we'll handle it differently
            return True
        else:
            print_info(f"No setup function found in {layer_name}, skipping...")
            return True
            
    except Exception as e:
        print_error(f"Error running generator for {layer_name}: {e}")
        import traceback
        traceback.print_exc()
        return False


def create_base_react_app(output_dir):
    """Create the base React application structure."""
    print_header("Creating Base React Application")
    
    # Find LAYER-01 (Dashboard Container & Routing)
    feature_dir = Path(__file__).parent
    layer_01 = feature_dir / "LAYER-CA-006-06-01 Dashboard Container & Routing"
    
    if not layer_01.exists():
        print_error(f"LAYER-01 not found: {layer_01}")
        return False
    
    impl_file = layer_01 / "src" / "implementation.py"
    
    try:
        # Import and execute LAYER-01 generator
        sys.path.insert(0, str(impl_file.parent))
        
        import importlib.util
        spec = importlib.util.spec_from_file_location("layer01", impl_file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        
        # Call setup_react_project to create base structure
        if hasattr(module, 'setup_react_project'):
            print_step("🏗️", "Building base React structure...")
            module.setup_react_project(output_dir)
            print_success("Base React structure created")
            return True
        else:
            print_error("setup_react_project function not found in LAYER-01")
            return False
            
    except Exception as e:
        print_error(f"Error creating base app: {e}")
        import traceback
        traceback.print_exc()
        return False


def install_npm_dependencies(output_dir):
    """Install npm dependencies."""
    print_header("Installing npm Dependencies")
    
    package_json = output_dir / "package.json"
    if not package_json.exists():
        print_error("package.json not found")
        return False
    
    print_step("📦", "Running npm install (this may take a few minutes)...")
    
    try:
        result = subprocess.run(
            ['npm', 'install'],
            cwd=output_dir,
            capture_output=True,
            text=True,
            timeout=300
        )
        
        if result.returncode == 0:
            print_success("npm dependencies installed successfully")
            return True
        else:
            print_error(f"npm install failed:\n{result.stderr}")
            return False
            
    except subprocess.TimeoutExpired:
        print_error("npm install timed out after 5 minutes")
        return False
    except Exception as e:
        print_error(f"Error running npm install: {e}")
        return False


def create_env_file(output_dir):
    """Create .env file for development."""
    print_step("⚙️", "Creating .env file...")
    
    env_content = """# Dashboard UI Environment Configuration
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
VITE_ENVIRONMENT=development
"""
    
    env_file = output_dir / ".env"
    env_file.write_text(env_content)
    print_success(".env file created")


def create_readme(output_dir):
    """Create README for the React app."""
    print_step("📝", "Creating README.md...")
    
    readme_content = """# CA-006 Feedback Dashboard

Modern React dashboard for monitoring MVP portfolio performance.

## Quick Start

### Development
```bash
npm run dev
```

Open http://localhost:5173 to view the dashboard.

### Build for Production
```bash
npm run build
```

### Run Tests
```bash
npm test
```

## Features

- **Portfolio Overview**: View all MVPs with key metrics and trends
- **MVP Detail View**: Deep dive into individual MVP analytics
- **Real-time Updates**: WebSocket connections for live data
- **Responsive Design**: Desktop, tablet, and mobile support
- **Interactive Charts**: Recharts-powered visualizations

## Architecture

- **Framework**: React 18 + TypeScript 5
- **Build Tool**: Vite 5
- **Styling**: TailwindCSS 3
- **State**: Zustand
- **Charts**: Recharts
- **Tables**: TanStack Table
- **Testing**: Vitest + React Testing Library

## Backend Integration

Configure backend API URL in `.env`:

```env
VITE_API_URL=http://localhost:8000
VITE_WS_URL=ws://localhost:8000/ws
```

Backend should provide:
- GET /api/v1/portfolio/overview
- GET /api/v1/mvps
- GET /api/v1/mvps/{id}/metrics
- WebSocket /ws/live-feed

See `FEATURE-CA-006-06_dashboard_ui.yaml` for complete API specification.

## Deployment

### Railway
```bash
railway link
railway up
```

### Docker
```bash
docker build -t dashboard-ui .
docker run -p 5173:5173 dashboard-ui
```

## License

Proprietary - Causal Affect System CA-006
"""
    
    readme_file = output_dir / "README.md"
    readme_file.write_text(readme_content)
    print_success("README.md created")


def main():
    """Main execution function."""
    print_header("🚀 CA-006 Dashboard UI Setup")
    print_info("FEATURE-CA-006-06: Dashboard User Interface")
    print_info("Generating complete React application...\n")
    
    # Get paths
    script_dir = Path(__file__).parent.resolve()
    feature_dir = script_dir
    
    print_info(f"Feature directory: {feature_dir}")
    
    # Step 1: Check prerequisites
    if not check_node_installed():
        print_error("Prerequisites not met. Please install Node.js and npm.")
        return 1
    
    # Step 2: Create output directory
    output_dir = create_output_directory(feature_dir)
    print_success(f"Output directory ready: {output_dir}\n")
    
    # Step 3: Create base React app (LAYER-01)
    if not create_base_react_app(output_dir):
        print_error("Failed to create base React application")
        return 1
    
    # Step 4: Create additional files
    create_env_file(output_dir)
    create_readme(output_dir)
    
    # Step 5: Install npm dependencies
    if not install_npm_dependencies(output_dir):
        print_error("Failed to install npm dependencies")
        return 1
    
    # Success!
    print_header("🎉 Setup Complete!")
    print_success("React dashboard application created successfully!\n")
    
    print_info("📁 Application directory:")
    print(f"   {output_dir}\n")
    
    print_info("🚀 Next steps:")
    print(f"   cd {output_dir}")
    print(f"   npm run dev\n")
    
    print_info("📖 Then open your browser to:")
    print(f"   http://localhost:5173\n")
    
    print_info("🧪 To run tests:")
    print(f"   npm test\n")
    
    print_info("🏗️  To build for production:")
    print(f"   npm run build\n")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
