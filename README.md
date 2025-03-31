# MCP-FreeCAD Integration

This project provides a flexible and robust integration between external applications and FreeCAD CAD software. It offers multiple connection methods to accommodate different environments and requirements.

## Components

### 1. FreeCAD Connection (`freecad_connection.py`)

A unified interface for connecting to FreeCAD through different methods:

- **Socket Server Connection**: Communicates with a running FreeCAD process via a socket server
- **CLI Bridge Connection**: Uses command-line calls to interact with FreeCAD
- **Mock Connection**: Provides a fallback for testing and development

### 2. FreeCAD Server (`freecad_server.py`)

A socket-based server that runs inside FreeCAD and provides a network API for external applications.

```bash
# Run inside FreeCAD's Python console
exec(open("/path/to/freecad_server.py").read())

# Or from command line
freecad -c /path/to/freecad_server.py --host localhost --port 12345 --debug
```

### 3. FreeCAD Bridge (`freecad_bridge.py`)

A Python module that provides a bridge to FreeCAD via command-line interface, allowing operations without relying on direct module imports.

### 4. FreeCAD Client (`freecad_client.py`)

A client library for applications to interact with FreeCAD, using the unified connection interface.

```bash
# Command-line usage examples
python freecad_client.py --host localhost --port 12345 version
python freecad_client.py create-document MyModel
python freecad_client.py create-box --length 20 --width 15 --height 10
python freecad_client.py export output.stl --type stl
```

## Getting Started

1. **Install FreeCAD** on your system
2. **Copy the integration files** to your project
3. **Choose a connection method**:
   - Server: Run `freecad_server.py` inside FreeCAD
   - Bridge: Use the bridge for command-line communication
   - Auto: Let the system choose the best available method

## Example Usage

```python
from freecad_connection import FreeCADConnection

# Create a connection with automatic method selection
fc = FreeCADConnection(auto_connect=True)

# Check if FreeCAD is available
if fc.is_connected():
    print(f"Connected to FreeCAD using {fc.get_connection_type()} method")
    
    # Get FreeCAD version
    version_info = fc.get_version()
    print(f"FreeCAD version: {version_info.get('version', 'Unknown')}")
    
    # Create a document
    doc_result = fc.create_document("TestModel")
    
    # Create objects
    box = fc.create_box(length=20, width=15, height=10)
    cylinder = fc.create_cylinder(radius=5, height=15)
    
    # Export to STL
    fc.export_document("output.stl", file_type="stl")
else:
    print("Could not connect to FreeCAD")
```

## Troubleshooting

- **Socket connection failing**: Ensure the FreeCAD server is running and the port is not blocked
- **Bridge connection failing**: Verify FreeCAD is properly installed and accessible in your PATH
- **Import errors**: Check that all required files are in your project directory

## License

This project is licensed under the MIT License - see the LICENSE file for details.
