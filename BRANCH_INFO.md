# Branch Information for MCP-FreeCAD

This repository has been organized into multiple branches to support different FreeCAD integration approaches:

## Branch Structure

### Main Branch (`main`)
- Contains the **production-ready** implementation 
- Requires Python 3.11 (matching FreeCAD's libraries)
- No mock implementations or fallbacks
- Designed for real FreeCAD operations
- Fails explicitly if FreeCAD libraries cannot be loaded

### Mock Implementation Branch (`mock-implementation`)
- Contains both real and mock implementations
- Includes fallback to mock mode when FreeCAD libraries can't be loaded
- Works with Python 3.12 or other versions
- Useful for development and testing without proper FreeCAD setup

## Key Implementation Differences

| Feature | `main` branch | `mock-implementation` branch |
|---------|--------------|----------------------------|
| FreeCAD module | Required | Optional (with mock fallback) |
| Python version | 3.11 required | Any version supported |
| Error handling | Fails on missing FreeCAD | Falls back to mock mode |
| Server exit | Exits if no FreeCAD | Continues with mock implementation |
| Script files | start_mcp_environment.sh requires Python 3.11 | start_mcp_environment.sh works with any Python |

## Specific File Changes

The following files were modified to remove mock implementation:

1. **freecad_server.py**:
   - Removed all mock classes (MockFreeCAD, MockDocument, MockObject)
   - Added explicit error handling that exits if FreeCAD modules can't be loaded
   - Improved error messages to guide users to install FreeCAD properly

2. **start_mcp_environment.sh**:
   - Updated to require Python 3.11
   - Added checks to ensure FreeCAD is available
   - Removed references to mock mode

## Choosing the Right Branch

### Use the `main` branch if:
- You need actual FreeCAD operations
- You have Python 3.11 installed
- You want a production-grade setup

### Use the `mock-implementation` branch if:
- You're developing/testing the API structure
- You can't install Python 3.11
- You don't need actual FreeCAD operations

## Switching Between Branches

To switch to the mock implementation branch:
```bash
git checkout mock-implementation
./start_mcp_environment.sh  # Will work with Python 3.12
```

To switch to the main branch:
```bash
git checkout main
# Make sure you have Python 3.11 installed
sudo apt-get install python3.11 python3.11-venv python3.11-dev
./start_mcp_environment.sh  # Requires Python 3.11
```

## Implementation Differences

The main differences between branches:

1. **Error Handling**:
   - `main`: Fails if FreeCAD libraries can't be loaded
   - `mock-implementation`: Falls back to mock mode

2. **Python Version**:
   - `main`: Strictly requires Python 3.11
   - `mock-implementation`: Works with any Python version

3. **Dependencies**:
   - `main`: Requires actual FreeCAD installation
   - `mock-implementation`: Can work without FreeCAD 
