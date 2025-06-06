#!/usr/bin/env python3
"""
Test script to validate the CapabilityRegistry import fix
"""

import sys
import os

# Add freecad-ai to Python path
freecad_ai_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'freecad-ai')
sys.path.insert(0, freecad_ai_path)

def test_capability_registry_import():
    """Test that the capability registry import works correctly"""
    try:
        print("Testing capability registry import...")

        # Test the import that was failing
        from tools.tool_capabilities import get_capability_registry
        print("✅ Successfully imported get_capability_registry from tools.tool_capabilities")

        # Test creating registry instance
        registry = get_capability_registry()
        print(f"✅ Successfully created registry instance: {type(registry).__name__}")

        # Test the get() method that was missing
        result = registry.get("test_tool_id")
        print(f"✅ Successfully called registry.get() method (returned: {result})")

        # Test other methods used in tool_selector
        try:
            query_result = registry.query(keywords=["test"])
            print(f"✅ Successfully called registry.query() method")
        except Exception as e:
            print(f"⚠️ registry.query() failed: {e}")

        try:
            check_result = registry.check_requirements("test_tool_id")
            print(f"✅ Successfully called registry.check_requirements() method")
        except Exception as e:
            print(f"⚠️ registry.check_requirements() failed: {e}")

        return True

    except Exception as e:
        print(f"❌ Import test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_tool_selector_import():
    """Test that tool_selector can now import without errors"""
    try:
        print("\nTesting tool_selector import...")

        # This was the component that was failing
        from core.tool_selector import ToolSelector
        print("✅ Successfully imported ToolSelector from core.tool_selector")

        # Try to create an instance (this triggered the error before)
        try:
            selector = ToolSelector()
            print("✅ Successfully created ToolSelector instance")
            return True
        except Exception as e:
            print(f"❌ ToolSelector creation failed: {e}")
            import traceback
            traceback.print_exc()
            return False

    except Exception as e:
        print(f"❌ ToolSelector import failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== Testing CapabilityRegistry Fix ===\n")

    test1_passed = test_capability_registry_import()
    test2_passed = test_tool_selector_import()

    print(f"\n=== Test Results ===")
    print(f"Capability Registry Import: {'✅ PASSED' if test1_passed else '❌ FAILED'}")
    print(f"Tool Selector Import: {'✅ PASSED' if test2_passed else '❌ FAILED'}")

    if test1_passed and test2_passed:
        print("\n🎉 All tests passed! The CapabilityRegistry fix is working.")
        exit(0)
    else:
        print("\n💥 Some tests failed. The fix needs more work.")
        exit(1)
