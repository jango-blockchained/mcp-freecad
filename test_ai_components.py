#!/usr/bin/env python3
"""
Test script to diagnose FreeCAD AI component initialization issues
"""

import os
import sys
import traceback

# Add the freecad-ai directory to Python path
freecad_ai_dir = os.path.join(os.path.dirname(__file__), 'freecad-ai')
if freecad_ai_dir not in sys.path:
    sys.path.insert(0, freecad_ai_dir)

print("=" * 60)
print("FreeCAD AI Component Diagnostic Test")
print("=" * 60)

# Test 1: Basic imports
print("\n1. Testing basic imports...")
try:
    import FreeCAD
    print("✓ FreeCAD imported successfully")
except ImportError as e:
    print(f"✗ FreeCAD import failed: {e}")

# Test 2: Agent Manager import and initialization
print("\n2. Testing Agent Manager...")
try:
    sys.path.insert(0, os.path.join(freecad_ai_dir, 'core'))
    from agent_manager import AgentManager
    print("✓ AgentManager class imported successfully")
    
    # Try to create instance
    agent_manager = AgentManager()
    print("✓ AgentManager instance created successfully")
    print(f"  - Current mode: {agent_manager.current_mode}")
    print(f"  - Execution state: {agent_manager.execution_state}")
    print(f"  - Tool registry available: {agent_manager.tool_registry is not None}")
    
except Exception as e:
    print(f"✗ AgentManager failed: {e}")
    print(f"  Traceback: {traceback.format_exc()}")

# Test 3: Provider Integration Service
print("\n3. Testing Provider Integration Service...")
try:
    sys.path.insert(0, os.path.join(freecad_ai_dir, 'ai'))
    from provider_integration_service import get_provider_service
    print("✓ Provider service function imported successfully")
    
    # Try to get instance
    provider_service = get_provider_service()
    print("✓ Provider service instance created successfully")
    print(f"  - Config manager available: {provider_service.config_manager is not None}")
    print(f"  - AI manager available: {provider_service.ai_manager is not None}")
    
except Exception as e:
    print(f"✗ Provider service failed: {e}")
    print(f"  Traceback: {traceback.format_exc()}")

# Test 4: Main Widget
print("\n4. Testing Main Widget...")
try:
    sys.path.insert(0, os.path.join(freecad_ai_dir, 'gui'))
    from main_widget import MCPMainWidget
    print("✓ MCPMainWidget class imported successfully")
    
    # Try to check Qt availability
    try:
        from PySide2 import QtWidgets
        app = QtWidgets.QApplication.instance()
        if app is None:
            print("  ⚠ No QApplication instance - would need one for widget creation")
        else:
            print("  ✓ QApplication available")
    except ImportError:
        print("  ✗ PySide2 not available")
    
except Exception as e:
    print(f"✗ Main widget failed: {e}")
    print(f"  Traceback: {traceback.format_exc()}")

# Test 5: Dependencies check
print("\n5. Checking key dependencies...")
dependencies = [
    'aiohttp',
    'anthropic',
    'openai',
    'google-generativeai',
    'asyncio',
    'threading',
    'json',
    'logging'
]

for dep in dependencies:
    try:
        __import__(dep.replace('-', '_'))
        print(f"✓ {dep}")
    except ImportError:
        print(f"✗ {dep}")

# Test 6: Check file existence
print("\n6. Checking critical files...")
critical_files = [
    'freecad-ai/core/agent_manager.py',
    'freecad-ai/ai/provider_integration_service.py',
    'freecad-ai/gui/main_widget.py',
    'freecad-ai/config/config_manager.py',
    'freecad-ai/ai/ai_manager.py'
]

for file_path in critical_files:
    full_path = os.path.join(os.path.dirname(__file__), file_path)
    if os.path.exists(full_path):
        print(f"✓ {file_path}")
    else:
        print(f"✗ {file_path}")

print("\n" + "=" * 60)
print("Test completed")
print("=" * 60)
