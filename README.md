# 🛠️ MCP-FreeCAD Integration

> **Status:** Active Development - Clean, organized codebase with multiple connection methods and comprehensive tool providers.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Code style: flake8](https://img.shields.io/badge/code%20style-flake8-orange.svg)](https://flake8.pycqa.org/en/latest/)
[![Project Status: Active](https://img.shields.io/badge/repo%20status-active-green.svg)]()

This project provides a robust integration between AI assistants and FreeCAD CAD software using the **Model Context Protocol (MCP)**. It allows external applications to interact with FreeCAD through a standardized interface, offering multiple connection methods and specialized tools.

---

## 🚀 **Quick Start**

### Option 1: FreeCAD Addon (Recommended for Users)
For the best user experience with GUI integration:

📦 **[FreeCAD MCP Integration Addon](freecad-ai/README.md)**

- 🧠 **Claude 4 with Thinking Mode** - Advanced AI reasoning
- 🤖 **Multi-Provider Support** - Claude, Gemini, OpenRouter with 13+ models  
- 🎨 **Modern GUI** - Professional tabbed interface
- 🔗 **Universal Connections** - All MCP connection methods
- 📊 **Performance Monitoring** - Real-time diagnostics

### Option 2: MCP Server (For Developers/Integration)

```bash
# Clone the repository
git clone https://github.com/jango-blockchained/mcp-freecad.git
cd mcp-freecad

# Install dependencies
pip install -r requirements.txt

# Start the MCP server
python -m src.mcp_freecad.main

# Or with custom config
python -m src.mcp_freecad.main --config my_config.json --debug
```

---

## 🏗️ **Architecture Overview**

### Core Components

```
src/mcp_freecad/
├── main.py                 # Main entry point
├── __init__.py            # Package exports and registry
├── client/                # FreeCAD connection management
│   └── freecad_connection_manager.py
├── server/                # MCP server implementation
│   └── freecad_mcp_server.py
├── tools/                 # Tool providers
│   ├── base.py           # Base tool provider class
│   ├── primitives.py     # Primitive shapes (box, cylinder, etc.)
│   ├── model_manipulation.py # Transform, boolean ops, etc.
│   ├── export_import.py  # File format handling
│   ├── measurement.py    # Analysis tools
│   └── code_generator.py # Code generation
├── core/                  # Core infrastructure
│   ├── server.py         # FastAPI-based server
│   ├── cache.py          # Resource caching
│   ├── diagnostics.py    # Performance monitoring
│   └── recovery.py       # Connection recovery
└── connections/           # Connection backends
```

### Connection Methods

The system supports multiple ways to connect to FreeCAD:

1. **🚀 Launcher** (Recommended) - Uses AppImage with AppRun
2. **🔌 Server** - Socket-based connection to FreeCAD server
3. **🌉 Bridge** - CLI-based connection using FreeCAD executable
4. **📡 RPC** - XML-RPC connection to FreeCAD
5. **📦 Wrapper** - Subprocess wrapper connection
6. **🎭 Mock** - For testing without FreeCAD

---

## 🛠️ **Available Tools**

### Primitive Creation
- `create_box` - Create box primitives
- `create_cylinder` - Create cylinders
- `create_sphere` - Create spheres  
- `create_cone` - Create cones

### Model Manipulation
- `transform` - Move, rotate objects
- `boolean_operation` - Union, difference, intersection
- `fillet_edge` - Round edges
- `chamfer_edge` - Chamfer edges
- `mirror` - Mirror objects across planes
- `scale` - Scale objects uniformly or non-uniformly

### Document Management
- `create_document` - Create new documents
- `list_documents` - List open documents
- `list_objects` - List objects in documents

### Export/Import
- `export_stl` - Export to STL format
- Additional formats coming soon

---

## 📋 **Usage Examples**

### Python API

```python
from src.mcp_freecad import FreeCADConnection, PrimitiveToolProvider

# Create connection (auto-selects best method)
fc = FreeCADConnection(auto_connect=True)

if fc.is_connected():
    print(f"Connected via: {fc.get_connection_type()}")
    
    # Create a document
    doc_name = fc.create_document("MyProject")
    
    # Create objects
    box = fc.create_box(length=20, width=10, height=5)
    cylinder = fc.create_cylinder(radius=3, height=10)
    
    # Export
    fc.export_stl(box, "my_box.stl")
```

### Tool Provider Usage

```python
from src.mcp_freecad.tools.primitives import PrimitiveToolProvider

# Initialize tool provider
primitives = PrimitiveToolProvider()

# Execute tools
result = await primitives.execute_tool("create_box", {
    "length": 10.0,
    "width": 5.0, 
    "height": 3.0
})

print(f"Created: {result.result['object_id']}")
```

### MCP Server Integration

```python
from src.mcp_freecad.core.server import MCPServer
from src.mcp_freecad import TOOL_PROVIDERS

# Setup server
server = MCPServer()

# Register tool providers
server.register_tool("primitives", TOOL_PROVIDERS["primitives"]())
server.register_tool("model_manipulation", TOOL_PROVIDERS["model_manipulation"]())

# Initialize and run
await server.initialize()
```

---

## ⚙️ **Configuration**

### Basic Configuration (`config.json`)

```json
{
  "server": {
    "name": "mcp-freecad-server",
    "version": "0.7.11"
  },
  "freecad": {
    "connection_method": "auto",
    "host": "localhost",
    "port": 12345,
    "freecad_path": "freecad"
  },
  "tools": {
    "enable_primitives": true,
    "enable_model_manipulation": true,
    "enable_export_import": true
  }
}
```

### Connection Method Configuration

```json
{
  "freecad": {
    "connection_method": "launcher",
    "use_apprun": true,
    "apprun_path": "/path/to/squashfs-root/AppRun",
    "script_path": "/path/to/freecad_launcher_script.py"
  }
}
```

---

## 🔧 **Development**

### Project Structure

- **`src/mcp_freecad/`** - Main package
- **`freecad-ai/`** - FreeCAD GUI addon
- **`tests/`** - Test suite
- **`docs/`** - Documentation
- **`scripts/`** - Setup and utility scripts

### Adding New Tools

1. Create a new tool provider in `src/mcp_freecad/tools/`
2. Inherit from `ToolProvider` base class
3. Implement required methods (`tool_schema`, `execute_tool`)
4. Register in `TOOL_PROVIDERS` in `__init__.py`

```python
from .base import ToolProvider, ToolResult, ToolSchema

class MyToolProvider(ToolProvider):
    @property
    def tool_schema(self) -> ToolSchema:
        return ToolSchema(
            name="my_tool",
            description="My custom tool",
            parameters={...},
            returns={...}
        )
    
    async def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> ToolResult:
        # Implementation
        return self.format_result(status="success", result=result)
```

### Testing

```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest tests/ --cov=src --cov-report=html

# Run specific test
python -m pytest tests/test_primitives.py -v
```

---

## 🐳 **Docker Support**

```bash
# Build and run with Docker Compose
docker compose up

# Build from scratch
docker compose build --no-cache
docker compose up
```

---

## 📚 **Documentation**

- [FreeCAD Integration Guide](docs/FREECAD_INTEGRATION.md)
- [Connection Methods](docs/CONNECTION_METHODS.md)
- [Tool Development](docs/TOOL_DEVELOPMENT.md)
- [Configuration Reference](docs/CONFIGURATION.md)

---

## 🤝 **Contributing**

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

---

## 📄 **License**

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 **Acknowledgments**

- FreeCAD development team for the excellent CAD software
- Anthropic for the Model Context Protocol (MCP) framework
- Contributors and community members

---

<div align="center">
<sub>
🛠️ <strong>MCP-FreeCAD Integration</strong> - Bridging AI and CAD through advanced connectivity<br>
Crafted with ❤️ by jango-blockchained • 2025
</sub>
</div>
