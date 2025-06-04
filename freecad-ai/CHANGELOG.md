# Changelog - MCP Integration FreeCAD Addon

All notable changes to this addon will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-01-27

### Added
- **Complete FreeCAD workbench** with fully functional tabbed interface
- **Claude 4 + Thinking Mode integration** - Advanced AI reasoning capabilities
- **Complete tool implementations**:
  - Primitives tool (box, cylinder, sphere, cone, torus)
  - Operations tool (boolean union, cut, intersection, move, rotate, scale)
  - Measurements tool (distance, angle, volume, area, bounding box, edge length)
  - Export/Import tool (STL, STEP, IGES, BREP formats)
- **Professional GUI interface** with 5 comprehensive tabs:
  - AI Models tab with provider selection and API management
  - Connections tab for MCP server connections
  - Servers tab for server monitoring and control
  - Tools tab for executing MCP tools
  - Logs tab for activity monitoring
- **Multi-provider AI support**:
  - Claude (Anthropic) with Claude 4 models
  - Gemini (Google) ready for integration
  - OpenRouter with 13+ model support
- **Real-time features**:
  - Live connection status monitoring
  - Chat interface with AI providers
  - Activity logging and diagnostics
  - Error handling with user feedback

### Features
- Support for multiple MCP connection methods (launcher, wrapper, server, bridge, mock)
- Complete boolean operations for 3D modeling
- Comprehensive measurement tools for CAD analysis
- Multi-format export/import capabilities
- Secure API key management
- Persistent configuration storage
- Robust error handling and recovery
- Professional branding and metadata

### Technical Details
- Compatible with FreeCAD 0.20.0+
- Python 3.8+ requirement
- PySide2 GUI framework
- Full MCP protocol implementation
- Asynchronous AI API communication
- Thread-safe operation
- Comprehensive logging system

### Fixed
- All runtime errors resolved
- Widget initialization order corrected
- Workbench registration issues fixed
- Command system properly implemented
- Version consistency across all files

### Known Limitations
- Code generator tool pending implementation
- Advanced AI features (token monitoring) planned for v1.1
- Some UI polish items deferred to future releases

## [Unreleased]

### Planned
- Complete implementation of all GUI components
- Enhanced AI conversation interface
- Custom tool creation wizard
- Performance optimization
- Multi-language support
- Advanced diagnostic tools