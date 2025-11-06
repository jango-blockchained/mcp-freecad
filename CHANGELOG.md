# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2025-11-06

### Added
- Unified MCP server with both FastMCP and standard modes
- Command-line argument support for server configuration
- Comprehensive tool provider system for FreeCAD primitives and model manipulation
- Multiple connection methods: server, bridge, RPC, launcher, and wrapper
- FreeCAD GUI addon with multi-provider AI support (Claude, OpenAI, Google, OpenRouter)
- Modern tabbed interface for FreeCAD integration
- Performance monitoring and diagnostics
- Docker support with docker-compose configuration
- Comprehensive test suite with pytest
- CI/CD workflow with GitHub Actions
- Project documentation (README, CONTRIBUTING)

### Changed
- Consolidated multiple MCP server files into single unified `mcp_server.py`
- Cleaned up codebase by removing test and development files from root
- Organized scripts directory, keeping only essential utilities
- Updated .gitignore for better coverage
- Improved logging and error handling

### Removed
- Legacy `cursor_mcp_server.py` and `cursor_mcp_server_old.py` (merged into `mcp_server.py`)
- Root-level test files (moved to `tests/` directory)
- Development and diagnostic scripts
- Status and fix summary markdown files

## [0.7.11] - 2025-11-05

### Added
- Initial MCP protocol integration
- FreeCAD connection manager with multiple connection types
- Basic tool providers for primitives and model manipulation
- FastMCP server implementation
- FreeCAD addon infrastructure

### Fixed
- Connection stability improvements
- Error handling in tool providers
- FreeCAD module import issues

## [0.7.0] - 2025-11-01

### Added
- Project initialization
- Basic FreeCAD integration
- MCP protocol support
- Initial documentation

[1.0.0]: https://github.com/jango-blockchained/mcp-freecad/releases/tag/v1.0.0
[0.7.11]: https://github.com/jango-blockchained/mcp-freecad/releases/tag/v0.7.11
[0.7.0]: https://github.com/jango-blockchained/mcp-freecad/releases/tag/v0.7.0
