
"""
FreeCAD AI In-Application Test Script

Run this script within FreeCAD to test if the AI components
are working correctly after the fixes.
"""

import sys
import os

def test_freecad_ai_in_app():
    """Test FreeCAD AI components from within FreeCAD."""
    
    print("Testing FreeCAD AI components within FreeCAD...")
    
    # Get addon directory
    addon_dir = os.path.dirname(__file__)
    freecad_ai_dir = os.path.join(addon_dir, 'freecad-ai')
    
    if freecad_ai_dir not in sys.path:
        sys.path.insert(0, freecad_ai_dir)
    
    test_results = {}
    
    # Test Agent Manager
    try:
        from gui.main_widget import MCPMainWidget
        widget = MCPMainWidget()
        
        # Check if agent manager was initialized
        if hasattr(widget, 'agent_manager') and widget.agent_manager is not None:
            print("✓ Agent Manager: AVAILABLE")
            test_results['agent_manager'] = True
        else:
            print("✗ Agent Manager: NOT AVAILABLE") 
            test_results['agent_manager'] = False
            
        # Check if provider service was initialized
        if hasattr(widget, 'provider_service') and widget.provider_service is not None:
            print("✓ Provider Service: AVAILABLE")
            test_results['provider_service'] = True
        else:
            print("✗ Provider Service: NOT AVAILABLE")
            test_results['provider_service'] = False
            
        # Test tools registry
        if (hasattr(widget, 'agent_manager') and widget.agent_manager is not None and
            hasattr(widget.agent_manager, 'tool_registry') and widget.agent_manager.tool_registry is not None):
            print("✓ Tools Registry: AVAILABLE")
            test_results['tools_registry'] = True
        else:
            print("✗ Tools Registry: NOT AVAILABLE")
            test_results['tools_registry'] = False
            
    except Exception as e:
        print(f"✗ Widget initialization failed: {e}")
        test_results['widget_init'] = False
    
    # Summary
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    print(f"\nTest Results: {passed}/{total} components working")
    
    if passed == total:
        print("🎉 All FreeCAD AI components are working correctly!")
    else:
        print("⚠️ Some components are still not working. Check the fixes.")
    
    return test_results

# Run the test if executed directly
if __name__ == "__main__":
    test_freecad_ai_in_app()
