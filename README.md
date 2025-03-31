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
    "path": "",
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
- `POST /events/document_changed`: Trigger document changed event (for testing)

### Resource URI Scheme

The server uses a URI scheme for addressing resources:

- `cad://model/[document]/[resource]` - CAD model data
- `cad://measurements/[measurement_type]/[objects]` - Measurements
- `cad://materials/[resource_type]/[object_or_material]` - Materials
- `cad://constraints/[resource_type]/[object]` - Constraints

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

### Connecting with FreeCAD

The server attempts to connect to FreeCAD automatically. If FreeCAD is not found, the server will run in mock mode, providing test responses without actual FreeCAD functionality.

## Development

This project is under active development. See the implementation plan for the roadmap and feature schedule.

## License

[MIT License](LICENSE)
