# Configuration Files

This directory contains various configuration templates and specialized configurations for the MCP-FreeCAD project.

## Files

### `config.template.json`
Template configuration file that can be copied to `config.json` in the project root. Contains default settings for:
- Server configuration
- FreeCAD connection settings
- Tool enablement
- Logging configuration

### `cursor_config.json`
Specialized configuration for Cursor IDE integration with additional settings:
- Cursor-specific debugging options
- STDIO transport configuration
- IDE-optimized logging levels

## Usage

1. Copy `config.template.json` to the project root as `config.json`
2. Modify the copied `config.json` file with your specific settings
3. Use `cursor_config.json` as reference for Cursor IDE integration

**Note:** The main `config.json` file should be kept in the project root and is gitignored to prevent sensitive configuration from being committed to the repository. 
