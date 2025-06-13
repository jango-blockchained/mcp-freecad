#!/usr/bin/env python3
"""
Simple test to check FreeCAD bridge functionality
"""

import sys
import os
from pathlib import Path

# Add src to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_basic_import():
    """Test if we can import the bridge"""
    try:
        from src.mcp_freecad.server.freecad_bridge import FreeCADBridge
        print("✅ Successfully imported FreeCADBridge")
        return True
    except ImportError as e:
        print(f"❌ Failed to import FreeCADBridge: {e}")
        return False

def test_bridge_creation():
    """Test if we can create a bridge instance"""
    try:
        from src.mcp_freecad.server.freecad_bridge import FreeCADBridge
        bridge = FreeCADBridge()
        print("✅ Successfully created FreeCADBridge instance")
        return True
    except Exception as e:
        print(f"❌ Failed to create FreeCADBridge: {e}")
        return False

def test_freecad_availability():
    """Test if FreeCAD is available"""
    try:
        from src.mcp_freecad.server.freecad_bridge import FreeCADBridge
        bridge = FreeCADBridge()
        available = bridge.is_available()
        print(f"FreeCAD availability: {available}")
        if available:
            print("✅ FreeCAD is available")
        else:
            print("⚠️  FreeCAD is not available (may not be installed)")
        return available
    except Exception as e:
        print(f"❌ Error checking FreeCAD availability: {e}")
        return False

if __name__ == "__main__":
    print("Testing FreeCAD Bridge Components...")
    print("=" * 40)
    
    # Test 1: Import
    if not test_basic_import():
        sys.exit(1)
    
    # Test 2: Creation
    if not test_bridge_creation():
        sys.exit(1)
    
    # Test 3: Availability (this might be False if FreeCAD not installed)
    freecad_available = test_freecad_availability()
    
    print("\n" + "=" * 40)
    if freecad_available:
        print("🎉 All basic tests passed and FreeCAD is available!")
        print("You can now test creating documents and shapes.")
    else:
        print("✅ Bridge code works but FreeCAD may not be installed/configured.")
        print("Install FreeCAD to test the full functionality.")
    
    print("Basic tests completed successfully!")
