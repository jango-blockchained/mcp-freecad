#!/usr/bin/env python3
"""
Test agent manager initialization
"""

import sys
import os

# Add the freecad-ai directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'freecad-ai'))

def test_agent_manager_wrapper():
    """Test the agent manager wrapper initialization"""
    print("=== Testing Agent Manager Wrapper ===")
    
    try:
        # Mock FreeCAD to avoid import errors
        import types
        freecad_mock = types.ModuleType('FreeCAD')
        freecad_mock.Console = types.ModuleType('Console')
        freecad_mock.Console.PrintMessage = lambda x: print(f"FreeCAD: {x}")
        freecad_mock.Console.PrintError = lambda x: print(f"FreeCAD ERROR: {x}")
        freecad_mock.Console.PrintWarning = lambda x: print(f"FreeCAD WARNING: {x}")
        sys.modules['FreeCAD'] = freecad_mock
        
        # Test wrapper import
        from core.agent_manager_wrapper import get_agent_manager, is_agent_manager_available
        print("✅ Agent manager wrapper imported successfully")
        
        # Test availability check
        is_available = is_agent_manager_available()
        print(f"Agent manager available: {is_available}")
        
        # Test getting agent manager
        agent_manager = get_agent_manager()
        if agent_manager:
            print("✅ Agent manager retrieved successfully")
            print(f"Agent manager type: {type(agent_manager)}")
            
            # Test if it has expected methods
            if hasattr(agent_manager, 'get_mode'):
                print("✅ Agent manager has get_mode method")
            else:
                print("❌ Agent manager missing get_mode method")
                
            if hasattr(agent_manager, 'set_mode'):
                print("✅ Agent manager has set_mode method")
            else:
                print("❌ Agent manager missing set_mode method")
                
        else:
            print("❌ Agent manager is None")
            
        return agent_manager is not None
        
    except Exception as e:
        print(f"❌ Agent manager wrapper test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run agent manager tests"""
    print("Agent Manager Initialization Test")
    print("=" * 40)
    
    success = test_agent_manager_wrapper()
    
    print("\n" + "=" * 40)
    if success:
        print("🎉 Agent manager test passed!")
    else:
        print("⚠️  Agent manager test failed!")
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
