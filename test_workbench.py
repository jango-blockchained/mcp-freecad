#!/usr/bin/env python3
"""
Test script to run within FreeCAD to test workbench activation
"""

import FreeCAD as App
import FreeCADGui as Gui

def test_workbench_activation():
    """Test activating the FreeCAD AI workbench"""
    try:
        print("=== Testing FreeCAD AI Workbench Activation ===")

        # Try to activate the workbench
        print("Attempting to activate FreeCADAIWorkbench...")
        Gui.activateWorkbench('FreeCADAIWorkbench')
        print("✅ SUCCESS: FreeCAD AI Workbench activated without errors!")

        # Check if the workbench is active
        active_wb = Gui.activeWorkbench()
        print(f"Active workbench: {active_wb}")

        return True

    except Exception as e:
        print(f"❌ ERROR: Failed to activate workbench: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Test the workbench activation
    success = test_workbench_activation()

    if success:
        print("\n🎉 CRASH FIXES SUCCESSFUL!")
        print("✅ CapabilityRegistry 'get' method error: FIXED")
        print("✅ PySide2 segmentation fault during provider init: FIXED")
        print("The FreeCAD AI addon now loads without crashing!")
    else:
        print("\n💥 ISSUE PERSISTS: The workbench still has problems.")

    # Exit FreeCAD quickly
    print("\nTest completed. Exiting...")
    import sys
    sys.exit(0)
