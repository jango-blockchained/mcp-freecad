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
- `POST /tools/primitives.create_box`: Create a box primitive
- `POST /events/document_changed`: Trigger document changed event (for testing)

### Connecting with FreeCAD

The server attempts to connect to FreeCAD automatically. If FreeCAD is not found, the server will run in mock mode, providing test responses without actual FreeCAD functionality.

## Development

This project is under active development. See the implementation plan for the roadmap and feature schedule.

## License

[MIT License](LICENSE)
