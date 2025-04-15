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

1. **freecad_socket_server.py**:
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
# Install Python 3.11 (if not available in standard repositories)
```

### Installing Python 3.11

Since Python 3.11 might not be available in standard repositories, here are several options:

#### Option 1: Using deadsnakes PPA (Ubuntu)
```bash
# Add the deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update

# Install Python 3.11
sudo apt install python3.11 python3.11-venv python3.11-dev
```

#### Option 2: Using pyenv (Any Linux)
```bash
# Install pyenv
curl https://pyenv.run | bash

# Add to your shell configuration (.bashrc or .zshrc)
echo 'export PATH="$HOME/.pyenv/bin:$PATH"' >> ~/.bashrc
echo 'eval "$(pyenv init --path)"' >> ~/.bashrc
echo 'eval "$(pyenv virtualenv-init -)"' >> ~/.bashrc
source ~/.bashrc

# Install Python 3.11
pyenv install 3.11.0

# Set as local version
pyenv local 3.11.0
```

#### Option 3: Use the FreeCAD's built-in Python
If you've extracted the FreeCAD AppImage, you can use its built-in Python:
```bash
# Use FreeCAD's Python to create a virtual environment
./squashfs-root/usr/bin/python -m venv freecad-py-venv
source freecad-py-venv/bin/activate

# Then modify the start_mcp_environment.sh script to use this Python
```

After installing Python 3.11 using one of these methods, you can run:
```bash
./start_mcp_environment.sh  # Now it will find Python 3.11
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
