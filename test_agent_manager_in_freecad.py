#!/usr/bin/env python3
"""
Test Agent Manager Initialization in FreeCAD

This script should be run within FreeCAD to debug agent manager issues.
"""

def test_agent_manager_init():
    """Test agent manager initialization step by step."""
    
    print("=" * 60)
    print("FreeCAD Agent Manager Initialization Test")
    print("=" * 60)
    
    import os
    import sys
    
    # Get the addon directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    freecad_ai_dir = os.path.join(script_dir, 'freecad-ai')
    
    if freecad_ai_dir not in sys.path:
        sys.path.insert(0, freecad_ai_dir)
    
    print(f"FreeCAD AI directory: {freecad_ai_dir}")
    print(f"Directory exists: {os.path.exists(freecad_ai_dir)}")
    
    # Test 1: Check if FreeCAD is available
    print("\n1. Testing FreeCAD availability...")
    try:
        import FreeCAD
        print("  ✓ FreeCAD module available")
        print(f"  ✓ FreeCAD version: {FreeCAD.Version()}")
    except ImportError:
        print("  ✗ FreeCAD module not available")
        return False
    
    # Test 2: Test core agent manager import
    print("\n2. Testing core agent manager import...")
    try:
        from core.agent_manager import AgentManager
        print("  ✓ AgentManager class imported successfully")
        
        # Try to create an instance
        agent_manager = AgentManager()
        print("  ✓ AgentManager instance created successfully")
        print(f"  ✓ Agent manager type: {type(agent_manager)}")
        
        # Test basic functionality
        if hasattr(agent_manager, 'get_mode'):
            mode = agent_manager.get_mode()
            print(f"  ✓ Agent manager mode: {mode}")
        
    except Exception as e:
        print(f"  ✗ Core agent manager test failed: {e}")
        import traceback
        print(f"    Traceback: {traceback.format_exc()}")
    
    # Test 3: Test AI manager import
    print("\n3. Testing AI manager import...")
    try:
        from ai.agent_manager import AIManager
        print("  ✓ AIManager class imported successfully")
        
        # Try to create an instance
        ai_manager = AIManager()
        print("  ✓ AIManager instance created successfully")
        print(f"  ✓ AI manager type: {type(ai_manager)}")
        
    except Exception as e:
        print(f"  ✗ AI manager test failed: {e}")
        import traceback
        print(f"    Traceback: {traceback.format_exc()}")
    
    # Test 4: Test agent manager wrapper
    print("\n4. Testing agent manager wrapper...")
    try:
        from core.agent_manager_wrapper import get_agent_manager, is_agent_manager_available
        print("  ✓ Agent manager wrapper imported successfully")
        
        available = is_agent_manager_available()
        print(f"  ✓ Agent manager available: {available}")
        
        agent_manager = get_agent_manager()
        if agent_manager is not None:
            print("  ✓ Agent manager instance obtained successfully")
            print(f"  ✓ Agent manager type: {type(agent_manager)}")
        else:
            print("  ⚠ Agent manager instance is None")
        
    except Exception as e:
        print(f"  ✗ Agent manager wrapper test failed: {e}")
        import traceback
        print(f"    Traceback: {traceback.format_exc()}")
    
    # Test 5: Test main widget agent manager initialization
    print("\n5. Testing main widget agent manager initialization...")
    try:
        from gui.main_widget import MCPMainWidget
        print("  ✓ MCPMainWidget imported successfully")
        
        # Create a widget instance
        widget = MCPMainWidget()
        print("  ✓ MCPMainWidget instance created successfully")
        
        # Check agent manager initialization
        if hasattr(widget, 'agent_manager') and widget.agent_manager is not None:
            print("  ✓ Agent manager initialized in main widget")
            print(f"  ✓ Agent manager type: {type(widget.agent_manager)}")
        else:
            print("  ⚠ Agent manager not initialized in main widget")
            print(f"  ⚠ Agent manager value: {getattr(widget, 'agent_manager', 'NOT_SET')}")
        
        # Check provider service initialization
        if hasattr(widget, 'provider_service') and widget.provider_service is not None:
            print("  ✓ Provider service initialized in main widget")
            print(f"  ✓ Provider service type: {type(widget.provider_service)}")
        else:
            print("  ⚠ Provider service not initialized in main widget")
            print(f"  ⚠ Provider service value: {getattr(widget, 'provider_service', 'NOT_SET')}")
        
    except Exception as e:
        print(f"  ✗ Main widget test failed: {e}")
        import traceback
        print(f"    Traceback: {traceback.format_exc()}")
    
    print("\n" + "=" * 60)
    print("Test completed. Check output above for issues.")
    print("=" * 60)

if __name__ == "__main__":
    test_agent_manager_init()
