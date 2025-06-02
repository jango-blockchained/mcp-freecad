# Changelog

## v0.4.0 - XML-RPC Server Integration

### Added
- XML-RPC server implementation for remote FreeCAD control
- Comprehensive API for document and object management
- Object serialization to JSON-compatible formats
- Screenshot capture functionality
- Command buttons for starting/stopping the XML-RPC server
- Example client script demonstrating XML-RPC usage
- Detailed documentation in README about the XML-RPC integration

### Changed
- Updated toolbar and menu with XML-RPC server controls
- Improved modular code structure with new rpc_server module
- Enhanced InitGui.py to support the new XML-RPC server commands

## v0.3.0 - Enhanced Server Differentiation & Flow Visualization

### Added
- New dedicated indicator for MCP Server (freecad_mcp_server.py)
- Clear visual differentiation between FreeCAD Socket Server and MCP Protocol Server
- Interactive flow visualization window showing message traffic between components
- Connection type selector in flow visualization (Socket, Bridge, Mock)
- Real-time message animation and logging in flow visualization
- Separate tabs in settings dialog for configuring different servers
- Enhanced server information dialogs with clear descriptions of purpose
- Added "FC" and "MCP" text to indicator icons for easy identification

### Changed
- Updated menu structure with separate submenus for each server type
- Improved tooltip information with server-specific details
- Enhanced status tracking for both server types
- Better status visualization with distinct colors for each server
- Updated README with comprehensive information about the new features
- Improved configuration UI with descriptive labels

### Fixed
- Resolved confusion between freecad_socket_server.py and freecad_mcp_server.py
- Fixed potential issues with server path detection and configuration
- Improved handling of server process management 
