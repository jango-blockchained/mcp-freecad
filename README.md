# MCP-FreeCAD Integration

This repository contains the implementation of the Model Context Protocol (MCP) integration for FreeCAD, allowing AI assistants to interact with FreeCAD through a standardized protocol.

## Overview

The MCP-FreeCAD integration enables AI assistants to:
- Access CAD model structure and properties
- Create and modify CAD objects
- Receive real-time notifications about model changes
- Execute FreeCAD commands and operations

## Repository Structure

- `src/`: Source code for the MCP-FreeCAD server
  - `mcp_freecad/`: Core MCP implementation for FreeCAD
    - `api/`: API endpoint implementations
    - `core/`: Core server components
    - `events/`: Event handling system
    - `extractor/`: CAD context extraction
    - `resources/`: Resource providers
    - `tools/`: Tool providers
- `app.py`: Main application entry point
- `config.json`: Server configuration
- `test_api.py`: API testing script
- `requirements.txt`: Python dependencies
- `mcp-freecad-implementation-plan.md`: Detailed implementation plan

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/mcp-freecad.git
cd mcp-freecad
```

2. Create a Python virtual environment and install dependencies:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. (Optional) Install FreeCAD if you want to connect to a real FreeCAD instance:
```bash
# On Ubuntu/Debian
sudo apt install freecad
```

## Configuration

Edit `config.json` to configure the server:
```json
{
  "auth": {
    "api_key": "development"
  },
  "server": {
    "host": "localhost",
    "port": 8080
  },
  "freecad": {
    "path": "/usr/bin/freecad",
    "auto_connect": true
  }
}
```

## Usage

### Starting the Server

```bash
source venv/bin/activate  # On Windows: venv\Scripts\activate
PYTHONPATH=. python app.py
```

The server will run at http://localhost:8080 by default.

### Testing the API

1. Start the server in one terminal
2. In another terminal, run the test script:
```bash
source venv/bin/activate
python test_api.py
```

### API Endpoints

- `GET /`: Server status
- `GET /resources/cad_model`: Get information about the current CAD model
- `GET /resources/measurements/{measurement_type}`: Get measurements (distance, area, volume, etc.)
- `GET /resources/materials/{resource_type}`: Access material library and object materials
- `GET /resources/constraints/{resource_type}`: Access geometric and assembly constraints
- `POST /tools/primitives.create_box`: Create a box primitive
- `POST /tools/model_manipulation.transform`: Transform objects (translate, rotate)
- `POST /tools/model_manipulation.boolean_operation`: Perform boolean operations (union, difference, intersection)
- `POST /tools/model_manipulation.fillet_edge`: Create fillets on object edges
- `POST /tools/model_manipulation.chamfer_edge`: Create chamfers on object edges
- `POST /tools/model_manipulation.mirror`: Mirror objects across planes
- `POST /tools/model_manipulation.scale`: Scale objects uniformly or non-uniformly
- `POST /tools/model_manipulation.offset`: Create offset surfaces
- `POST /tools/model_manipulation.thicken`: Convert surfaces to solids with thickness
- `POST /tools/measurement.distance`: Measure distance between points, edges, or faces
- `POST /tools/measurement.angle`: Measure angle between edges, faces, or vectors
- `POST /tools/measurement.area`: Calculate area of faces or entire objects
- `POST /tools/measurement.volume`: Calculate volume of solid objects
- `POST /tools/measurement.center_of_mass`: Find object's center of mass
- `POST /tools/measurement.bounding_box`: Get object dimensions and extents
- `POST /tools/export_import.export`: Export objects to various file formats
- `POST /tools/export_import.import`: Import objects from various file formats
- `POST /tools/export_import.list_formats`: List supported import and export formats
- `POST /tools/export_import.convert`: Convert between different file formats
- `POST /tools/code_generation.generate_script`: Generate FreeCAD Python scripts
- `POST /tools/code_generation.execute_script`: Execute Python scripts in FreeCAD
- `POST /tools/code_generation.save_snippet`: Save code snippets to library
- `POST /tools/code_generation.load_snippet`: Load code snippets from library
- `POST /tools/code_generation.get_script_history`: Get history of generated scripts
- `POST /tools/code_generation.generate_primitive_script`: Generate script for creating primitives
- `POST /tools/code_generation.generate_transform_script`: Generate script for transforming objects
- `POST /tools/code_generation.generate_boolean_script`: Generate script for boolean operations
- `GET /events`: Connect to SSE stream for real-time events
- `POST /events/subscribe`: Update event subscription for a client
- `POST /events/document_changed`: Trigger document changed event (for testing)
- `GET /events/command_history`: Get history of executed commands
- `GET /events/error_history`: Get error history
- `POST /events/report_error`: Manually report an error

### Resource URI Scheme

The server uses a URI scheme for addressing resources:

- `cad://model/[document]/[resource]` - CAD model data
- `cad://measurements/[measurement_type]/[objects]` - Measurements
- `cad://materials/[resource_type]/[object_or_material]` - Materials
- `cad://constraints/[resource_type]/[object]` - Constraints

### Event System

The MCP-FreeCAD server includes a comprehensive event system that provides real-time notifications about changes to the CAD model and application state. Events are delivered through Server-Sent Events (SSE), allowing clients to maintain a persistent connection and receive updates as they occur.

#### Event Providers

##### Document Event Provider
Monitors document-related events in FreeCAD and notifies clients:

- **Document Changed**: Triggered when objects in a document are modified
- **Document Created**: Triggered when a new document is created
- **Document Closed**: Triggered when a document is closed
- **Active Document Changed**: Triggered when the active document changes
- **Selection Changed**: Triggered when the user selection changes in the GUI

##### Command Execution Event Provider
Tracks FreeCAD command execution:

- **Command Executed**: Triggered when a FreeCAD command is executed
- Maintains a history of executed commands for auditing and analysis

##### Error Event Provider
Captures and reports errors that occur in FreeCAD:

- **Error**: Triggered when an error occurs in FreeCAD or the MCP server
- Provides detailed error information including message, traceback, and context
- Maintains an error history for debugging and troubleshooting

#### Event Subscription

Clients can subscribe to specific event types:

```
GET /events?types=document_changed,selection_changed
```

The server supports dynamic subscription updates:

```
POST /events/subscribe
Content-Type: application/json

{
  "event_types": ["document_changed", "error"]
}
```

#### Event Format

Events are delivered in SSE format:

```
event: document_changed
data: {"document": "Unnamed", "objects": ["Box001"], "timestamp": 1616161616}

event: selection_changed
data: {"selected": ["Box001"], "deselected": [], "timestamp": 1616161620}
```

### Tool Providers

#### Primitives Tool Provider
Creates basic 3D primitives such as boxes, cylinders, spheres, and cones.

#### Model Manipulation Tool Provider
Provides tools for manipulating and transforming CAD objects:

- **Transform**: Translate and rotate objects
- **Boolean Operations**: Union, difference, and intersection between objects
- **Fillet**: Create rounded edges with a specified radius
- **Chamfer**: Create beveled edges with specified distances
- **Mirror**: Create mirrored copies of objects across planes
- **Scale**: Resize objects uniformly or non-uniformly
- **Offset**: Create offset surfaces from faces or shells
- **Thicken**: Convert surfaces to solids with specified thickness

#### Measurement Tool Provider
Provides tools for measuring geometric properties:

- **Distance**: Measure distances between points, edges, or faces
- **Angle**: Calculate angles between edges, faces, or vectors
- **Area**: Measure surface area of faces or entire objects
- **Volume**: Calculate volume of solid objects
- **Center of Mass**: Determine center of mass coordinates
- **Bounding Box**: Calculate object dimensions and extents

#### Export/Import Tool Provider
Provides tools for file format conversion and data exchange:

- **Export**: Export CAD objects to various file formats (STEP, IGES, STL, etc.)
- **Import**: Import CAD objects from supported file formats
- **List Formats**: Retrieve information about supported import and export formats
- **Convert**: Convert files from one format to another

Supported formats include:
- STEP/STP (ISO 10303-21)
- IGES/IGS
- BREP (Boundary representation)
- STL (Stereolithography)
- OBJ (Wavefront)
- DXF (AutoCAD Drawing Exchange Format)
- VRML/WRL
- FCStd (Native FreeCAD format)

#### Code Generation Tool Provider
Provides tools for generating and executing Python scripts for FreeCAD:

- **Generate Script**: Create custom Python scripts with proper imports and documentation
- **Execute Script**: Run Python scripts directly in the FreeCAD environment
- **Save/Load Snippets**: Maintain a library of reusable code snippets
- **Script History**: Keep track of previously generated and executed scripts
- **Generate Primitive Scripts**: Generate scripts for creating basic geometric primitives
- **Generate Transform Scripts**: Create scripts for transforming objects (translate, rotate, scale)
- **Generate Boolean Scripts**: Generate scripts for boolean operations between objects

This tool provider enables programmatic control of FreeCAD through Python scripting, allowing for more complex operations and automation.

### Optimization Features

The MCP-FreeCAD server includes several optimization features to enhance performance, reliability, and diagnostics:

#### Caching System

The server implements an in-memory caching system to improve response times for frequently accessed data:

- **Time-To-Live (TTL) Caching**: Cache entries expire after a configurable TTL
- **Size-Limited Cache**: Prevents memory overflow by limiting cache size
- **Cache Statistics**: Tracks hit/miss rates and other performance metrics
- **API Endpoints**:
  - `GET /cache/stats`: View cache statistics and cached keys
  - `POST /cache/clear`: Clear all cached data
  - `DELETE /cache/item/{key}`: Remove specific item from cache

#### Recovery Mechanism

The recovery system handles transient failures and connection issues with FreeCAD:

- **Automatic Retries**: Retries failed operations with configurable limits
- **Exponential Backoff**: Increases delay between retries
- **Failure Statistics**: Tracks retry counts and failure patterns
- **Fallback Responses**: Provides graceful degradation when operations cannot be completed

#### Performance Monitoring

The server includes comprehensive performance monitoring tools:

- **Request Timing**: Measures execution time for all API endpoints
- **System Resource Monitoring**: Tracks CPU, memory, and disk usage
- **Health Endpoints**:
  - `GET /health`: Basic health check endpoint
  - `GET /health/detailed`: Detailed system and server information
- **Diagnostics Endpoints**:
  - `GET /diagnostics`: Complete performance overview
  - `GET /diagnostics/slow_endpoints`: Identifies performance bottlenecks
  - `GET /diagnostics/errors`: Error aggregation and analysis
  - `POST /diagnostics/reset`: Reset performance counters

#### Testing Optimization Features

A test script is provided to verify optimization functionality:

```bash
source venv/bin/activate
python test_optimization.py
```

Advanced testing options:
```bash
# Run stress test with custom parameters
python test_optimization.py --stress --requests 50 --concurrency 10

# Test against a custom server
python test_optimization.py --url http://your-server:8080 --key your-api-key
```

The optimization features can be configured in the `config.json` file:

```json
{
  "cache": {
    "enabled": true,
    "default_ttl": 30.0,
    "max_size": 100
  },
  "recovery": {
    "max_retries": 5,
    "retry_delay": 2.0,
    "backoff_factor": 1.5,
    "max_delay": 30.0
  },
  "performance": {
    "monitoring_enabled": true,
    "metrics_retention": 3600,
    "sample_rate": 1.0
  }
}
```

### Connecting with FreeCAD

The server attempts to connect to FreeCAD automatically. If FreeCAD is not found, the server will run in mock mode, providing test responses without actual FreeCAD functionality.

## Development

This project is under active development. See the implementation plan for the roadmap and feature schedule.

## License

[MIT License](LICENSE)
