#!/usr/bin/env python3
"""
FreeCAD AI Fix Verification Script

This script can be run within FreeCAD to verify that the fixes
for the Agent Manager and Provider Service issues are working.

To use:
1. Open FreeCAD
2. Open the Python console (View -> Panels -> Python console)
3. Run: exec(open('/path/to/this/script').read())
"""

import os
import sys

def verify_freecad_ai_fixes():
    """Verify that FreeCAD AI fixes are working."""
    
    print("=" * 60)
    print("FreeCAD AI Fix Verification")
    print("=" * 60)
    
    try:
        # Try to import and test the main widget with fixes
        print("Testing FreeCAD AI components...")
        
        # Get the addon directory (assuming this script is in the project root)
        addon_dir = os.path.dirname(os.path.abspath(__file__))
        freecad_ai_dir = os.path.join(addon_dir, 'freecad-ai')
        
        if freecad_ai_dir not in sys.path:
            sys.path.insert(0, freecad_ai_dir)
        
        # Import the main widget
        from gui.main_widget import MCPMainWidget
        
        print("✓ MCPMainWidget imported successfully")
        
        # Create an instance (this will trigger initialization)
        try:
            widget = MCPMainWidget()
            print("✓ MCPMainWidget instance created")
            
            # Check agent manager status
            if hasattr(widget, 'agent_manager'):
                if widget.agent_manager is not None:
                    print("✅ Agent Manager: AVAILABLE")
                    print(f"   Mode: {widget.agent_manager.get_mode()}")
                    print(f"   State: {widget.agent_manager.execution_state}")
                else:
                    print("⚠️  Agent Manager: Instance is None (fallback mode)")
            else:
                print("❌ Agent Manager: Attribute not found")
            
            # Check provider service status  
            if hasattr(widget, 'provider_service'):
                if widget.provider_service is not None:
                    print("✅ Provider Service: AVAILABLE")
                    providers = widget.provider_service.get_all_providers()
                    print(f"   Total providers: {len(providers)}")
                else:
                    print("⚠️  Provider Service: Instance is None (fallback mode)")
            else:
                print("❌ Provider Service: Attribute not found")
            
            # Check tools registry
            if (hasattr(widget, 'agent_manager') and widget.agent_manager is not None):
                if hasattr(widget.agent_manager, 'tool_registry'):
                    if widget.agent_manager.tool_registry is not None:
                        tools = widget.agent_manager.get_available_tools()
                        total_tools = sum(len(methods) for methods in tools.values())
                        print("✅ Tools Registry: AVAILABLE")
                        print(f"   Total tools: {total_tools}")
                        print(f"   Categories: {len(tools)}")
                    else:
                        print("⚠️  Tools Registry: Registry is None")
                else:
                    print("❌ Tools Registry: Registry attribute not found")
            else:
                print("❌ Tools Registry: Agent Manager not available")
                
        except Exception as e:
            print(f"❌ Widget creation failed: {e}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            return False
            
    except Exception as e:
        print(f"❌ Import failed: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False
    
    print("\n" + "=" * 60)
    print("Verification complete!")
    print("=" * 60)
    
    return True

# Run verification if executed directly
if __name__ == "__main__":
    verify_freecad_ai_fixes()
