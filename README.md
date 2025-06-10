# 🛠️ MCP-FreeCAD Integration

> **Status:** Active Development - Clean, organized codebase with multiple connection methods and comprehensive tool providers.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python Version](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/)
[![Code style: flake8](https://img.shields.io/badge/code%20style-flake8-orange.svg)](https://flake8.pycqa.org/en/latest/)
[![Project Status: Active](https://img.shields.io/badge/repo%20status-active-green.svg)]()

This project provides a robust integration between AI assistants and FreeCAD CAD software using the **Model Context Protocol (MCP)**. It allows external applications to interact with FreeCAD through a standardized interface, offering multiple connection methods and specialized tools.

---

## 🤖 **AI Provider Models (2025)**

The MCP-FreeCAD integration supports multiple AI providers with the latest 2025 models. Choose the right model for your specific use case:

### **OpenAI Models**

#### **Production Models:**
- **gpt-4o** - Default multimodal model (text, image, audio)
  - Context: 128K tokens
  - Pricing: ~$5 per 1M input tokens
  - Best for: General CAD tasks, multimodal interactions

- **gpt-4.1** - Next-generation with 1M token context
  - Features: Text, Image, Audio, Video support
  - Pricing: ~$2.5 per 1M input tokens
  - Best for: Complex CAD projects, large document analysis

- **gpt-4-turbo** - Fast, cost-effective
  - Context: 128K tokens
  - Best for: High-volume operations, batch processing

#### **Reasoning Models:**
- **o3** - Advanced reasoning for complex CAD logic
  - Pricing: ~$10 per 1M input tokens
  - Best for: Complex geometry calculations, design optimization

- **o4-mini** / **o4-mini-high** - Cost-effective reasoning
  - Pricing: ~$0.15 per 1M input tokens
  - Best for: Simple calculations, quick iterations

### **Anthropic Claude Models**

#### **Claude 4 Series (2025):**
- **claude-opus-4** - Most advanced model
  - Max Context: 200K tokens
  - Pricing: $15/$75 per million tokens (input/output)
  - Features: Extended thinking, tool use, memory handling
  - Best for: Complex CAD workflows, autonomous design tasks

- **claude-sonnet-4** - Balanced efficiency
  - Max Context: 200K tokens  
  - Pricing: $3/$15 per million tokens
  - Features: Superior coding, hybrid reasoning
  - Best for: General CAD operations, scripting assistance

- **claude-haiku-3.5** - Fast, lightweight
  - Best for: Quick queries, simple operations

### **Google AI Models**

#### **Gemini 2.5 Series (Latest):**
- **gemini-2.5-pro-preview-05-06** - Most advanced
  - Context: 1M tokens
  - Features: Enhanced reasoning, thinking mode
  - Best for: Complex CAD analysis, large assemblies

- **gemini-2.5-flash-preview-04-17** - Performance optimized
  - Features: Adaptive thinking, cost-effective
  - Best for: Balanced performance and cost

#### **Gemini 2.0 Series (Stable):**
- **gemini-2.0-flash-001** - Production ready
  - Features: 2x faster than Gemini 1.5 Pro
  - Best for: Real-time CAD assistance

- **gemini-2.0-flash-lite** - Cost-optimized
  - Best for: High-volume, simple operations

### **OpenRouter (Unified Access)**

OpenRouter provides access to all models through a single API:

#### **Model Format:** `provider/model-name`

**Popular Models:**
- `anthropic/claude-sonnet-4` - Recommended general use
- `openai/gpt-4o` - OpenAI's flagship
- `google/gemini-2.5-pro-preview` - Google's latest

**Free Models (50-1000 requests/day):**
- `deepseek/deepseek-r1` - Advanced reasoning
- `deepseek/deepseek-v3` - General purpose
- `google/gemini-2.5-flash-preview` - Google free tier

### **Model Selection Guide**

| **Use Case** | **Recommended Model** | **Alternative** |
|-------------|---------------------|----------------|
| **General CAD Work** | `claude-sonnet-4` | `gpt-4o`, `gemini-2.0-flash-001` |
| **Complex Reasoning** | `claude-opus-4` | `o3`, `gemini-2.5-pro-preview-05-06` |
| **Multimodal Tasks** | `gpt-4o` | `gpt-4.1`, `claude-opus-4` |
| **Cost-Effective** | `o4-mini` | `claude-haiku-3.5`, `gemini-2.0-flash-lite` |
| **High Volume** | `gpt-4-turbo` | `claude-sonnet-4`, `gemini-2.0-flash-001` |
| **Free Usage** | `deepseek/deepseek-r1` | `google/gemini-2.5-flash-preview` |

### **Configuration Example**

```json
{
  "providers": {
    "anthropic": {
      "enabled": true,
      "model": "claude-sonnet-4",
      "thinking_mode": true,
      "max_tokens": 64000
    },
    "openai": {
      "enabled": true,
      "model": "gpt-4o",
      "max_tokens": 32000
    },
    "google": {
      "enabled": true,
      "model": "gemini-2.0-flash-001",
      "thinking_mode": true
    },
    "openrouter": {
      "enabled": true,
      "model": "anthropic/claude-sonnet-4",
      "free_models": ["deepseek/deepseek-r1"]
    }
  }
}
```

### **API Usage Examples**

```python
# Using specific provider
from freecad_ai import CADAssistant

# Initialize with Claude Sonnet 4
assistant = CADAssistant(provider="anthropic", model="claude-sonnet-4")

# Create complex geometry
result = assistant.generate_cad_script(
    "Create a parametric gear with 20 teeth, 5mm module, and 20° pressure angle"
)

# Using OpenRouter for cost optimization
assistant_free = CADAssistant(
    provider="openrouter", 
    model="deepseek/deepseek-r1"
)

# Quick operations with free model
result = assistant_free.create_primitive("box", length=10, width=5, height=3)
```

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
