# Task: Implement Settings Widget for API Keys and Provider Configuration

## Task ID: TASK_02_implement_settings_widget
## Status: pending
## Priority: high
## Created: 2024-12-28

## Objective
Implement a comprehensive settings widget to manage API keys, IDE provider settings, and configuration persistence to resolve the "API Keys missing after restart" and "Missing IDE Provider settings" issues.

## Current State
- settings_widget.py is just a placeholder with "Implementation in progress"
- API keys are not persisted after restart
- IDE provider settings are missing
- No configuration interface available

## Requirements
1. **API Key Management Section**:
   - OpenAI API key input with secure storage
   - Anthropic API key input with secure storage
   - Google API key input with secure storage
   - Other provider API keys as needed
   - Validation and testing of API keys

2. **IDE Provider Settings Section**:
   - Provider selection (OpenAI, Anthropic, Google, etc.)
   - Model selection per provider
   - Temperature and other model parameters
   - Connection timeout settings
   - Retry configuration

3. **General Settings Section**:
   - Auto-save configuration
   - Logging level configuration
   - UI theme preferences
   - Default tool parameters

4. **Configuration Persistence**:
   - Secure storage of sensitive data (API keys)
   - Automatic save on changes
   - Configuration validation
   - Import/export configuration

## Implementation Plan
1. Design tabbed interface for different setting categories
2. Implement secure API key storage with encryption
3. Create provider configuration interface
4. Add configuration validation and testing
5. Implement auto-save functionality
6. Add import/export capabilities
7. Integrate with config_manager.py

## Dependencies
- config_manager.py (needs completion)
- PySide2 GUI framework
- Cryptography library for secure storage
- Provider API libraries for validation

## Output Files
- `/home/jango/Git/mcp-freecad/freecad-addon/gui/settings_widget.py` (complete implementation)
- Configuration schema updates

## Success Criteria
- API keys can be entered and are persisted after restart
- IDE provider settings are configurable and saved
- Settings are validated before saving
- Secure storage prevents key exposure
- Configuration can be imported/exported
- Auto-save prevents data loss

## Security Considerations
- API keys must be encrypted at rest
- No keys should appear in logs
- Secure key validation without exposure
- Safe configuration file permissions

## Notes
- Must integrate with existing config_manager.py
- Should follow FreeCAD security best practices
- Need to handle different operating system key storage 
