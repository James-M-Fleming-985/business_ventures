```python
import json
import time
from http.server import HTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs
from typing import Dict, Any, List, Optional, Tuple
import re
from collections import deque
from threading import Lock


class PerformanceTracker:
    """Track API response times for p95 calculation."""
    
    def __init__(self, window_size: int = 100):
        self.response_times = deque(maxlen=window_size)
        self.lock = Lock()
    
    def add_response_time(self, response_time: float):
        """Add a response time measurement."""
        with self.lock:
            self.response_times.append(response_time)
    
    def get_p95(self) -> float:
        """Get the 95th percentile response time."""
        with self.lock:
            if not self.response_times:
                return 0.0
            sorted_times = sorted(self.response_times)
            index = int(len(sorted_times) * 0.95)
            return sorted_times[min(index, len(sorted_times) - 1)]


performance_tracker = PerformanceTracker()


class Engine:
    """Represents a calculation engine."""
    
    def __init__(self, id: str, name: str, description: str, input_schema: Dict[str, Any], 
                 formulas: Dict[str, str], calculations: Dict[str, Any]):
        self.id = id
        self.name = name
        self.description = description
        self.input_schema = input_schema
        self.formulas = formulas
        self.calculations = calculations
    
    def validate_inputs(self, inputs: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """Validate inputs against the engine's schema."""
        required = self.input_schema.get('required', [])
        properties = self.input_schema.get('properties', {})
        
        # Check required fields
        for field in required:
            if field not in inputs:
                return False, f"Missing required field: {field}"
        
        # Validate field types and constraints
        for field, value in inputs.items():
            if field not in properties:
                continue
            
            schema = properties[field]
            field_type = schema.get('type')
            
            # Type validation
            if field_type == 'number':
                if not isinstance(value, (int, float)):
                    return False, f"Field '{field}' must be a number"
            elif field_type == 'integer':
                if not isinstance(value, int):
                    return False, f"Field '{field}' must be an integer"
            elif field_type == 'string':
                if not isinstance(value, str):
                    return False, f"Field '{field}' must be a string"
            
            # Range validation
            if 'minimum' in schema and value < schema['minimum']:
                return False, f"Field '{field}' value {value} is below minimum {schema['minimum']}"
            if 'maximum' in schema and value > schema['maximum']:
                return False, f"Field '{field}' value {value} is above maximum {schema['maximum']}"
        
        return True, None
    
    def calculate(self, inputs: Dict[str, Any]) -> Dict[str, Any]:
        """Perform calculations based on inputs."""
        results = {}
        
        # Create evaluation context
        context = inputs.copy()
        
        # Evaluate each calculation
        for key, formula in self.calculations.items():
            try:
                # Simple evaluation - in production use a safe expression evaluator
                result = eval(formula, {"__builtins__": {}}, context)
                results[key] = result
                context[key] = result  # Make result available for subsequent calculations
            except Exception as e:
                results[key] = None
        
        return results


# Initialize engines
engines = {
    "solar": Engine(
        id="solar",
        name="Solar Energy Calculator",
        description="Calculate solar panel requirements and savings",
        input_schema={
            "type": "object",
            "properties": {
                "panel_wattage": {
                    "type": "number",
                    "minimum": 100,
                    "maximum": 600,
                    "description": "Wattage per solar panel"
                },
                "sunlight_hours": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 12,
                    "description": "Average daily sunlight hours"
                },
                "electricity_rate": {
                    "type": "number",
                    "minimum": 0.01,
                    "maximum": 1.0,
                    "description": "Cost per kWh"
                }
            },
            "required": ["panel_wattage", "sunlight_hours", "electricity_rate"]
        },
        formulas={
            "daily_kwh": "panel_wattage * sunlight_hours / 1000",
            "monthly_kwh": "daily_kwh * 30",
            "monthly_savings": "monthly_kwh * electricity_rate"
        },
        calculations={
            "daily_kwh": "panel_wattage * sunlight_hours / 1000",
            "monthly_kwh": "daily_kwh * 30",
            "monthly_savings": "monthly_kwh * electricity_rate"
        }
    ),
    "wind": Engine(
        id="wind",
        name="Wind Energy Calculator",
        description="Calculate wind turbine energy output",
        input_schema={
            "type": "object",
            "properties": {
                "turbine_capacity": {
                    "type": "number",
                    "minimum": 1,
                    "maximum": 10000,
                    "description": "Turbine capacity in kW"
                },
                "capacity_factor": {
                    "type": "number",
                    "minimum": 0.1,
                    "maximum": 0.5,
                    "description": "Capacity factor (0.1 to 0.5)"
                },
                "hours_per_year": {
                    "type": "integer",
                    "minimum": 8000,
                    "maximum": 8760,
                    "description": "Operating hours per year"
                }
            },
            "required": ["turbine_capacity", "capacity_factor", "hours_per_year"]
        },
        formulas={
            "annual_kwh": "turbine_capacity * capacity_factor * hours_per_year",
            "monthly_kwh": "annual_kwh / 12"
        },
        calculations={
            "annual_kwh": "turbine_capacity * capacity_factor * hours_per_year",
            "monthly_kwh": "annual_kwh / 12"
        }
    )
}


class APIHandler(BaseHTTPRequestHandler):
    """HTTP request handler for the API."""
    
    def do_GET(self):
        """Handle GET requests."""
        start_time = time.time()
        
        path = urlparse(self.path).path
        
        if path == '/api/engines':
            self._handle_get_engines()
        elif re.match(r'^/api/engines/[^/]+/input-schema$', path):
            engine_id = path.split('/')[3]
            self._handle_get_input_schema(engine_id)
        else:
            self._send_response(404, {"error": "Not found"})
        
        response_time = (time.time() - start_time) * 1000
        performance_tracker.add_response_time(response_time)
    
    def do_POST(self):
        """Handle POST requests."""
        start_time = time.time()
        
        path = urlparse(self.path).path
        
        if re.match(r'^/api/engines/[^/]+/calculate$', path):
            engine_id = path.split('/')[3]
            self._handle_calculate(engine_id)
        else:
            self._send_response(404, {"error": "Not found"})
        
        response_time = (time.time() - start_time) * 1000
        performance_tracker.add_response_time(response_time)
    
    def _handle_get_engines(self):
        """Handle GET /api/engines."""
        engine_list = [
            {
                "id": engine.id,
                "name": engine.name,
                "description": engine.description
            }
            for engine in engines.values()
        ]
        self._send_response(200, engine_list)
    
    def _handle_get_input_schema(self, engine_id: str):
        """Handle GET /api/engines/{id}/input-schema."""
        if engine_id not in engines:
            self._send_response(404, {"error": f"Engine '{engine_id}' not found"})
            return
        
        engine = engines[engine_id]
        self._send_response(200, engine.input_schema)
    
    def _handle_calculate(self, engine_id: str):
        """Handle POST /api/engines/{id}/calculate."""
        if engine_id not in engines:
            self._send_response(404, {"error": f"Engine '{engine_id}' not found"})
            return
        
        # Read request body
        content_length = int(self.headers.get('Content-Length', 0))
        if content_length == 0:
            self._send_response(400, {"error": "Request body is required"})
            return
        
        try:
            body = self.rfile.read(content_length).decode('utf-8')
            inputs = json.loads(body)
        except json.JSONDecodeError:
            self._send_response(400, {"error": "Invalid JSON"})
            return
        
        engine = engines[engine_id]
        
        # Validate inputs
        valid, error = engine.validate_inputs(inputs)
        if not valid:
            self._send_response(400, {"error": error})
            return
        
        # Calculate results
        results = engine.calculate(inputs)
        
        response = {
            "results": results,
            "formulas": engine.formulas
        }
        
        self._send_response(200, response)
    
    def _send_response(self, status_code: int, data: Any):
        """Send JSON response."""
        self.send_response(status_code)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))
    
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass


def run_server(host: str = 'localhost', port: int = 8080):
    """Run the API server."""
    server = HTTPServer((host, port), APIHandler)
    print(f"Server running on http://{host}:{port}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        server.shutdown()


if __name__ == "__main__":
    run_server()
```