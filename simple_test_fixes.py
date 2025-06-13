#!/usr/bin/env python3
"""
Simple test to verify FreeCAD AI fixes are working
"""

import sys
import os

# Add freecad-ai to path
freecad_ai_dir = os.path.join(os.path.dirname(__file__), 'freecad-ai')
sys.path.insert(0, freecad_ai_dir)

print("Testing FreeCAD AI fixes...")

# Test 1: Qt compatibility
try:
    sys.path.insert(0, os.path.join(freecad_ai_dir, 'gui'))
    from qt_compatibility import QT_VERSION, HAS_QT, is_qt_available
    print(f"✓ Qt compatibility: {QT_VERSION}, Available: {is_qt_available()}")
except Exception as e:
    print(f"✗ Qt compatibility failed: {e}")

# Test 2: Agent manager wrapper
try:
    sys.path.insert(0, os.path.join(freecad_ai_dir, 'core'))
    from agent_manager_wrapper import is_agent_manager_available
    available = is_agent_manager_available()
    print(f"✓ Agent manager wrapper: Available: {available}")
except Exception as e:
    print(f"✗ Agent manager wrapper failed: {e}")

# Test 3: Provider service wrapper
try:
    sys.path.insert(0, os.path.join(freecad_ai_dir, 'ai'))
    from provider_service_wrapper import is_provider_service_available
    available = is_provider_service_available()
    print(f"✓ Provider service wrapper: Available: {available}")
except Exception as e:
    print(f"✗ Provider service wrapper failed: {e}")

print("\nFixes verification complete!")
