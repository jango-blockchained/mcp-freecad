#!/usr/bin/env python3
"""
Test script to verify that FreeCAD addon imports work correctly.

This script tests all the import paths that were causing issues in the FreeCAD addon.
"""

import sys
import os

# Add the freecad-ai directory to the path to simulate how FreeCAD loads it
addon_path = os.path.join(os.path.dirname(__file__), "freecad-ai")
sys.path.insert(0, addon_path)

def test_imports():
    """Test all the imports that were causing issues."""
    print("Testing FreeCAD addon imports...")

    # Test tools.base import
    try:
        from tools.base import ToolProvider, ToolResult, ToolSchema
        print("✅ tools.base import successful")
    except ImportError as e:
        print(f"❌ tools.base import failed: {e}")

    # Test tools.advanced imports
    try:
        from tools.advanced import ADVANCED_TOOLS_AVAILABLE
        print(f"✅ tools.advanced import successful (available: {ADVANCED_TOOLS_AVAILABLE})")

        if ADVANCED_TOOLS_AVAILABLE:
            # Test individual advanced tools
            advanced_tools = []
            try:
                from tools.advanced import AssemblyToolProvider
                advanced_tools.append("AssemblyToolProvider")
            except ImportError:
                pass

            try:
                from tools.advanced import CAMToolProvider
                advanced_tools.append("CAMToolProvider")
            except ImportError:
                pass

            try:
                from tools.advanced import RenderingToolProvider
                advanced_tools.append("RenderingToolProvider")
            except ImportError:
                pass

            try:
                from tools.advanced import SmitheryToolProvider
                advanced_tools.append("SmitheryToolProvider")
            except ImportError:
                pass

            print(f"   Available advanced tools: {advanced_tools}")

    except ImportError as e:
        print(f"❌ tools.advanced import failed: {e}")

    # Test events imports
    try:
        from events import EVENTS_AVAILABLE
        print(f"✅ events import successful (available: {EVENTS_AVAILABLE})")
    except ImportError as e:
        print(f"❌ events import failed: {e}")

    # Test api imports
    try:
        from api import API_AVAILABLE
        print(f"✅ api import successful (available: {API_AVAILABLE})")
    except ImportError as e:
        print(f"❌ api import failed: {e}")

    # Test clients imports
    try:
        from clients import CLIENTS_AVAILABLE
        print(f"✅ clients import successful (available: {CLIENTS_AVAILABLE})")
    except ImportError as e:
        print(f"❌ clients import failed: {e}")

    # Test core imports
    try:
        from core.server import MCPServer
        print("✅ core.server import successful")
    except ImportError as e:
        print(f"❌ core.server import failed: {e}")

if __name__ == "__main__":
    test_imports()
    print("\nImport testing completed!")
