# 🚀 FreeCAD AI Addon

**AI-powered CAD assistance integrated directly into FreeCAD with MCP support**

[![FreeCAD](https://img.shields.io/badge/FreeCAD-0.20+-blue.svg)](https://www.freecadweb.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Claude 4](https://img.shields.io/badge/Claude%204-Thinking%20Mode-purple.svg)](https://www.anthropic.com)
[![Gemini](https://img.shields.io/badge/Gemini-2.5%20Pro-orange.svg)](https://ai.google.dev)

## 🌟 **AI-Powered CAD Assistant**

The FreeCAD AI addon brings advanced AI capabilities directly into FreeCAD, featuring the latest **Claude 4 models with Thinking Mode** for enhanced CAD design assistance. The addon provides two modes of operation:

1. **Internal AI Conversation** - Chat with AI directly in FreeCAD with MCP tool integration
2. **External MCP Server** - Connect from Claude Desktop or other MCP clients

Provides intelligent design guidance, automated scripting, and comprehensive problem-solving within the FreeCAD environment.

---

## 🎯 **Key Features**

### 🧠 **Claude 4 with Thinking Mode** ✨ *NEW!*
- **🔬 Extended Reasoning**: See AI think through complex design problems step-by-step
- **⚡ Claude 4 Opus**: Most capable model for complex analysis & research
- **🎯 Claude 4 Sonnet**: Best coding performance with advanced reasoning
- **🌀 Claude 3.7 Sonnet**: Hybrid reasoning with transparent thought process
- **🎛️ Configurable Thinking Budget**: 100-20,000 tokens for optimal performance

### 🤖 **Multi-Provider AI Support**
- **🎭 Anthropic Claude**: Industry-leading coding and reasoning
- **🔬 Google Gemini**: 2M token context, multimodal capabilities  
- **🌐 OpenRouter**: Access to 13+ models through single interface
- **⚡ Real-time Switching**: Change models instantly without losing context

### 🔧 **MCP Tool Integration** ✨ *NEW!*
- **🤖 Direct Execution**: AI can execute FreeCAD operations during conversation
- **🔨 Tool Access**: Create primitives, boolean ops, measurements directly
- **📊 Real Results**: See actual objects created in your document
- **🔄 Seamless Workflow**: Natural language to CAD operations

### 🔗 **Universal Connection Management**
- **🚀 Launcher**: AppImage-based connections
- **🔄 Wrapper**: Python module integration
- **🖥️ Server**: Direct server connections
- **🌉 Bridge**: FreeCAD executable bridge
- **🧪 Mock**: Testing and development mode

---

## 🎨 **Feature Showcase**

### 🏠 **Dashboard Interface**
```
┌─────────────────────────────────────┐
│ 📊 Real-time Monitoring Dashboard  │
├─────────────────────────────────────┤
│ 🟢 Connections: 3 Active           │
│ 🔵 Servers: 2 Running              │
│ 🧠 AI Models: Claude 4 Ready       │
│ ⚡ Performance: Optimal             │
└─────────────────────────────────────┘
```

### 🧠 **AI Conversation Interface**
```
You: Design a planetary gear system for 100:1 reduction

🤖 Claude 4 (Thinking Mode): 
💭 Thinking Process:
Let me analyze the requirements systematically...
1. Gear ratio calculations for 100:1 reduction
2. Space constraints and material considerations
3. Manufacturing feasibility analysis
...

✨ Response:
Based on my analysis, here's the optimal design...
```

### 🛠️ **Comprehensive Tool Library**
| Category | Tools | Status |
|----------|-------|--------|
| 🔧 **Primitives** | Box, Cylinder, Sphere, Cone | ✅ Ready |
| ⚙️ **Operations** | Union, Cut, Intersection | ✅ Ready |
| 📐 **Measurements** | Distance, Angle, Volume | ✅ Ready |
| 💾 **Export/Import** | STL, STEP, IGES | ✅ Ready |
| 🐍 **Code Gen** | Python, OpenSCAD | ✅ Ready |

---

## 🚀 **Quick Start Guide**

### 📦 **Installation**

#### Option 1: FreeCAD Addon Manager (Recommended)
1. 🔧 Open FreeCAD
2. 🛠️ Go to `Tools` → `Addon Manager`
3. 🔍 Search for "FreeCAD AI"
4. 📥 Click "Install"
5. 🔄 Restart FreeCAD

#### Option 2: Manual Installation
```bash
# Navigate to FreeCAD addons directory
cd ~/.local/share/FreeCAD/Addon/

# Clone the repository
git clone https://github.com/jango-blockchained/mcp-freecad.git

# Navigate to addon directory
cd mcp-freecad/freecad-addon/
```

### ⚙️ **Initial Setup**

#### 1. 🔑 **Get Your API Keys**
- **Claude**: [Get API Key](https://console.anthropic.com/) 
- **Gemini**: [Get API Key](https://ai.google.dev/)
- **OpenRouter**: [Get API Key](https://openrouter.ai/)

#### 2. 🎯 **Configure Your First Provider**
1. 🚀 Switch to "FreeCAD AI" workbench
2. 🤖 Go to **Models** tab
3. 🔑 Enter your API key
4. ⚙️ Enable "MCP Tool Integration" for direct execution
5. ✅ Test connection

#### 3. 🧠 **Enable Thinking Mode**
1. 🎭 Select a Claude 4 or 3.7 model
2. ✨ Check "Thinking Mode" checkbox
3. 🎛️ Set thinking budget (2000 tokens recommended)
4. 💬 Start chatting!

---

## 🎯 **Usage Examples**

### 🔧 **MCP Tool Integration in Action**
```
🗣️ "Create a cylinder with radius 10mm and height 25mm"

🤖 AI Response:
I'll create a cylinder with your specifications.

<tool_use>
<tool_name>create_cylinder</tool_name>
<parameters>
{"radius": 10, "height": 25}
</parameters>
</tool_use>

<tool_result>
<tool_name>create_cylinder</tool_name>
<status>success</status>
<result>{"success": true, "message": "Created cylinder: Cylinder"}</result>
</tool_result>

✅ I've created a cylinder with radius 10mm and height 25mm. The object is now visible in your FreeCAD document as "Cylinder".
```

### 🏗️ **Complex Design Problems**
```
🗣️ "Design a lightweight bracket that can handle 500N load with minimal material"

🧠 AI Response (with Thinking Mode):
💭 Thinking Process:
1. Load analysis: 500N requires stress calculation
2. Material optimization: topology considerations
3. Manufacturing constraints: standard processes
4. Safety factor: 150% minimum recommended
...

✨ Final Design:
Here's an optimized bracket design with integrated ribs...
```

### 🔧 **Automated Scripting**
```python
# AI-generated FreeCAD script
import FreeCAD as App
import Part

# Create optimized bracket with AI-calculated dimensions
doc = App.newDocument()
bracket = Part.makeBox(45, 30, 8)  # AI-optimized dimensions
doc.addObject("Part::Feature", "Bracket").Shape = bracket
```

### 📊 **Real-time Problem Solving**
```
🗣️ "My parametric model breaks when I change dimensions"

🧠 AI Analysis:
1. 🔍 Identifying constraint conflicts
2. 🛠️ Proposing sketch modifications  
3. 📋 Step-by-step repair guide
4. 🚀 Prevention strategies for future
```

---

## 📚 **Comprehensive Documentation**

### 📖 **User Guides**
- 🚀 [**Getting Started Guide**](GETTING_STARTED.md)
- 🧠 [**Thinking Mode Guide**](THINKING_MODE_GUIDE.md) ⭐ *NEW!*
- 🤖 [**AI Models Supported**](AI_MODELS_SUPPORTED.md)
- 🔧 [**Tool Reference**](TOOL_REFERENCE.md)

### 🎓 **Advanced Topics**
- ⚙️ [**Configuration Guide**](CONFIG_GUIDE.md)
- 🔗 [**Connection Methods**](CONNECTION_GUIDE.md)
- 🛠️ [**Custom Tool Development**](CUSTOM_TOOLS.md)
- 🐛 [**Troubleshooting**](TROUBLESHOOTING.md)

---

## 🤖 **Supported AI Models**

### 🎭 **Claude (Anthropic)** - *Premier Choice*
| Model | Release | Thinking Mode | Best For |
|-------|---------|---------------|----------|
| 🔥 `claude-4-opus-20250522` | May 2025 | ✅ | Complex analysis & research |
| ⚡ `claude-4-sonnet-20250522` | May 2025 | ✅ | Coding & development |
| 🌀 `claude-3-7-sonnet-20250224` | Feb 2025 | ✅ | Extended reasoning |
| 📦 `claude-3-5-sonnet-20241022` | Oct 2024 | ❌ | Reliable baseline |

### 🔬 **Gemini (Google)** - *Multimodal Expert*
| Model | Context | Performance |
|-------|---------|-------------|
| 🚀 `gemini-2.5-pro-latest` | 2M tokens | Multimodal excellence |
| 📊 `gemini-1.5-pro-latest` | 2M tokens | Reliable performance |
| ⚡ `gemini-1.5-flash-latest` | 1M tokens | Speed optimized |

### 🌐 **OpenRouter** - *Universal Access*
- 🎭 All Claude models with thinking mode
- 🔬 Latest Gemini models  
- 🤖 OpenAI GPT-4.1, o3-mini
- 🦙 Open source models (Llama, Mistral)

---

## 🛠️ **Technical Requirements**

### 📋 **System Requirements**
- 🖥️ **FreeCAD**: Version 0.20.0 or newer
- 🐍 **Python**: 3.8+ (included with FreeCAD)
- 🎨 **Qt**: PySide2 (bundled with FreeCAD)
- 🌐 **Internet**: Required for AI model APIs
- 💾 **Storage**: 50MB for addon files

### 🌍 **Platform Support**
- 🐧 **Linux**: All major distributions
- 🪟 **Windows**: 10, 11 (x64)
- 🍎 **macOS**: 10.15+ (Intel & Apple Silicon)

### ⚡ **Performance Benchmarks**
- 🚀 **GUI Response**: <100ms average
- 🤖 **AI API Calls**: <2s average response
- 💾 **Memory Usage**: <50MB typical
- 🔄 **Connection Setup**: <5s for most methods

---

## 🎨 **Screenshots & Demo**

### 🏠 **Main Dashboard**
```
┌──────────────────────────────────────────────────────┐
│ MCP Integration Workbench                            │
├──────────────────────────────────────────────────────┤
│ [Connections] [Servers] [AI Models] [Tools] [Logs]  │
├──────────────────────────────────────────────────────┤
│ 🟢 Claude 4 Opus    │ 📊 Server Status               │
│ 🧠 Thinking Mode ON │ 🟢 Running (CPU: 12%)          │
│ 💬 Ready for chat   │ 📈 Memory: 234MB                │
└──────────────────────────────────────────────────────┘
```

### 🤖 **AI Conversation**
```
┌──────────────────────────────────────────────────────┐
│ AI Assistant - Claude 4 Sonnet (Thinking Mode ✨)   │
├──────────────────────────────────────────────────────┤
│ You: Create a parametric gear with 20 teeth          │
│                                                      │
│ 🧠 Thinking Process:                                 │
│ Let me think about gear design parameters...         │
│ 1. Calculating pitch diameter for 20 teeth          │
│ 2. Determining pressure angle (20° standard)        │
│ 3. Planning tooth profile generation...             │
│                                                      │
│ ✨ Claude: I'll create a parametric gear for you.   │
│ Here's the FreeCAD Python script...                 │
└──────────────────────────────────────────────────────┘
```

---

## 🧪 **Advanced Features**

### 🔬 **Thinking Mode Deep Dive**
```python
# Configure thinking mode programmatically
provider = claude_provider
provider.enable_thinking_mode(budget=5000)  # Deep thinking
provider.config['thinking_mode'] = True

# Use for complex problems
response = await provider.send_message(
    "Optimize this assembly for manufacturing cost reduction"
)

# Response includes thinking process
print(response.thinking_process)  # Step-by-step reasoning
print(response.final_answer)      # Optimized solution
```

### 📊 **Performance Monitoring**
```python
# Real-time metrics
metrics = addon.get_performance_metrics()
print(f"🚀 Response time: {metrics.avg_response_time}ms")
print(f"💾 Memory usage: {metrics.memory_usage}MB")
print(f"🔄 Active connections: {metrics.active_connections}")
```

### 🔧 **Custom Tool Integration**
```python
# Register custom tool
@register_mcp_tool
def custom_analysis_tool(geometry, material):
    """Custom finite element analysis tool"""
    return ai_provider.analyze_stress(geometry, material)
```

---

## 🤝 **Contributing**

### 🎯 **Ways to Contribute**
- 🐛 **Bug Reports**: Found an issue? Let me know!
- 💡 **Feature Requests**: Ideas for new capabilities
- 📝 **Documentation**: Help improve my guides
- 🧑‍💻 **Code**: Submit pull requests for new features
- 🧪 **Testing**: Help test new releases

### 🛠️ **Development Setup**
```bash
# Clone repository
git clone https://github.com/jango-blockchained/mcp-freecad.git
cd mcp-freecad

# Install development dependencies
pip install -r requirements-dev.txt

# Run tests
python -m pytest tests/

# Start FreeCAD with addon in development mode
freecad --addon-dev freecad-addon/
```

### 📋 **Code Style**
- 🐍 **Python**: Follow PEP 8 standards
- 📝 **Documentation**: Comprehensive docstrings required
- 🧪 **Testing**: 90%+ test coverage expected
- 🔍 **Linting**: Use black, flake8, mypy

---

## 🗺️ **Roadmap**

### 🎯 **Current Version (v2.0)**
- ✅ Claude 4 with Thinking Mode
- ✅ Multi-provider AI support
- ✅ Universal connection management
- ✅ Real-time monitoring

### 🚀 **Next Release (v2.1)** - *Coming Soon*
- 🔄 **Auto-model selection** based on task complexity
- 🎨 **Visual design assistant** with image generation
- 🔗 **Plugin ecosystem** for community tools
- 📱 **Mobile companion app**

### 🌟 **Future Vision (v3.0)**
- 🧠 **Local AI models** for privacy-focused users
- 🤖 **Custom fine-tuned models** for CAD-specific tasks
- 🌐 **Cloud collaboration** with shared workspaces
- 🚀 **Real-time multiplayer** design sessions

---

## 📜 **License**

```
MIT License

Copyright (c) 2025 FreeCAD AI Project

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software.
```

**Full license**: [LICENSE](LICENSE)

---

## 🙏 **Acknowledgments**

### 💝 **Special Thanks**
- 🏠 **FreeCAD Team** - For the excellent CAD platform
- 🤖 **Anthropic** - For Claude's exceptional capabilities  
- 🔬 **Google AI** - For Gemini's multimodal intelligence
- 🌐 **OpenRouter** - For universal model access
- 👥 **Community** - For feedback, testing, and contributions

### 🛠️ **Built With**
- 🎨 **FreeCAD** - Open source parametric 3D modeler
- 🐍 **Python** - Primary development language
- 🖼️ **Qt/PySide2** - Modern GUI framework
- 🤖 **Multiple AI APIs** - Claude, Gemini, OpenRouter
- ❤️ **Open Source Love** - Community-driven development

---

<div align="center">

### 🌟 **Ready to enhance your CAD workflow?**

[![Download Now](https://img.shields.io/badge/Download%20Now-FreeCAD%20Addon%20Manager-blue.svg?style=for-the-badge)](https://www.freecadweb.org/)
[![View Docs](https://img.shields.io/badge/View%20Docs-Documentation-green.svg?style=for-the-badge)](docs/)
[![Join Community](https://img.shields.io/badge/Join%20Community-Discord-purple.svg?style=for-the-badge)](https://discord.gg/mcp-freecad)

**⭐ Don't forget to star this repository if you find it helpful!**

</div>

---

<div align="center">
<sub>
🚀 <strong>FreeCAD AI Addon</strong> - Bringing AI to CAD, one design at a time<br>
Made with ❤️ by jango-blockchained • June 2025
</sub>
</div>

# FreeCAD AI Addon

This addon provides AI-powered CAD assistance integrated directly into FreeCAD with Model Context Protocol (MCP) support for both internal and external AI interactions.

## Features

- AI-powered FreeCAD tools and operations with direct execution
- Internal AI conversation with MCP tool integration
- External MCP server for Claude Desktop and other clients
- Secure API key management with encryption support
- Multiple AI provider support (Claude 4, Gemini 2.5, OpenRouter)
- Thinking mode support for complex reasoning
- Comprehensive tool widgets for all CAD operations
- Advanced primitives, boolean operations, and measurements
- Assembly, CAM, rendering, and smithery tools

## Installation

1. Copy this addon directory to your FreeCAD Mods directory
2. Install optional dependencies for enhanced functionality:

```bash
# For secure API key storage (recommended)
pip install cryptography

# For AI providers (choose as needed)
pip install openai anthropic google-generativeai
```

## Security Note

**API Key Storage:**
- If `cryptography` is installed: API keys are encrypted and stored securely
- If `cryptography` is not available: API keys are stored in plain text with a warning

For production use, we strongly recommend installing the cryptography package:
```bash
pip install cryptography
```

## Configuration

The addon creates configuration files in:
- FreeCAD: `{UserAppData}/Mod/freecad-addon/`
- Fallback: `~/.freecad/freecad-addon/`

## Usage

1. Open FreeCAD
2. Access the MCP Integration addon from the workbench
3. Configure your AI provider API keys in the settings
4. Use the tools widgets for AI-powered CAD operations

## Dependencies

See `requirements.txt` for the full list of dependencies. Core functionality works with minimal dependencies, with optional packages for enhanced features.
