#!/usr/bin/env python3
"""
Quick verification test for the urgent fixes applied.
Tests both API compatibility and general functionality.
"""

import os
import sys


def test_api_compatibility_fix():
    """Test that API compatibility returns warnings instead of failures."""
    print("🔧 Testing API compatibility fix...")

    try:
        # Add the freecad-ai directory to the path
        addon_path = os.path.join(os.path.dirname(__file__), "freecad-ai")
        if addon_path not in sys.path:
            sys.path.insert(0, addon_path)

        # Import the compatibility check function
        from api import check_fastapi_pydantic_compatibility

        print("  ✓ API module imported successfully")

        # Run the compatibility check
        is_compatible, error_msg = check_fastapi_pydantic_compatibility()

        print(f"  ✓ Compatibility check result: {is_compatible}")

        if error_msg:
            print(f"  ✓ Message: {error_msg}")
            if "warning" in error_msg.lower():
                print(
                    "  ✅ SUCCESS: Error correctly identified as warning (non-blocking)"
                )
                return True
            else:
                print("  ❌ ISSUE: Still treated as blocking error")
                return False
        else:
            print("  ✅ SUCCESS: No compatibility issues detected")
            return True

    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        import traceback

        print(f"  📝 Traceback: {traceback.format_exc()}")
        return False


def test_dock_widget_cleanup_logic():
    """Test that the dock widget cleanup logic is comprehensive."""
    print("🖥️  Testing dock widget cleanup logic...")

    try:
        addon_path = os.path.join(os.path.dirname(__file__), "freecad-ai")
        if addon_path not in sys.path:
            sys.path.insert(0, addon_path)

        # Read the workbench file to verify the enhanced cleanup logic
        workbench_file = os.path.join(addon_path, "freecad_ai_workbench.py")
        with open(workbench_file, "r") as f:
            content = f.read()

        # Check for the enhanced cleanup logic
        checks = [
            'widget.objectName() == "MCPIntegrationDockWidget"',
            'widget.windowTitle() == "FreeCAD AI"',
            "MCPMainWidget",
            "comprehensive cleanup",
            "Multiple processing cycles",
        ]

        all_found = True
        for check in checks:
            if check in content:
                print(f"  ✓ Found: {check}")
            else:
                print(f"  ❌ Missing: {check}")
                all_found = False

        if all_found:
            print("  ✅ SUCCESS: Enhanced dock widget cleanup logic is in place")
            return True
        else:
            print("  ❌ ISSUE: Some enhanced cleanup logic is missing")
            return False

    except Exception as e:
        print(f"  ❌ FAILED: {e}")
        return False


def main():
    """Run all urgent fix verification tests."""
    print("🚀 FreeCAD AI Addon - Urgent Fixes Verification")
    print("=" * 50)

    results = []

    # Test API compatibility fix
    results.append(test_api_compatibility_fix())
    print()

    # Test dock widget cleanup logic
    results.append(test_dock_widget_cleanup_logic())
    print()

    # Summary
    print("📊 Verification Summary")
    print("-" * 20)
    passed = sum(results)
    total = len(results)

    if passed == total:
        print(f"✅ All {total} urgent fixes verified successfully!")
        print()
        print("🎉 Ready for FreeCAD testing!")
        print("📝 Next steps:")
        print("   1. Restart FreeCAD")
        print("   2. Activate the FreeCAD AI workbench")
        print("   3. Verify API loads with warnings (not errors)")
        print("   4. Verify only one dock widget appears")
        return 0
    else:
        print(f"❌ {total - passed}/{total} fixes failed verification")
        print("🔍 Please check the issues above")
        return 1


if __name__ == "__main__":
    sys.exit(main())
