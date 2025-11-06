#!/usr/bin/env python3
"""
Test Agent Manager Import - Standalone Test

This script tests whether the agent manager can be imported properly
when called from different contexts, similar to how FreeCAD would import it.
"""

import os
import sys
import traceback
import logging

# Setup logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s: %(message)s')

def test_agent_manager_import():
    """Test agent manager import from different contexts."""
    
    print("=" * 60)
    print("Agent Manager Import Test")
    print("=" * 60)
    
    # Add the freecad-ai directory to Python path
    freecad_ai_dir = os.path.join(os.path.dirname(__file__), 'freecad-ai')
    if freecad_ai_dir not in sys.path:
        sys.path.insert(0, freecad_ai_dir)
    
    # Test 1: Direct import of agent manager wrapper
    print("\n1. Testing Agent Manager Wrapper Direct Import...")
    try:
        # Mimic how it would be imported from freecad_ai_workbench.py
        core_dir = os.path.join(freecad_ai_dir, 'core')
        if core_dir not in sys.path:
            sys.path.insert(0, core_dir)
        
        from agent_manager_wrapper import get_agent_manager, is_agent_manager_available
        print("  ✓ Agent manager wrapper imported successfully")
        
        # Test availability
        available = is_agent_manager_available()
        print(f"  ✓ Agent manager available: {available}")
        
        # Try to get instance
        agent_manager = get_agent_manager()
        if agent_manager is not None:
            print("  ✓ Agent manager instance obtained")
            print(f"  ✓ Agent manager type: {type(agent_manager)}")
            
            # Try to access methods
            if hasattr(agent_manager, 'get_mode'):
                print("  ✓ Agent manager has get_mode method")
            if hasattr(agent_manager, 'execution_state'):
                print("  ✓ Agent manager has execution_state attribute")
        else:
            print("  ⚠ Agent manager instance is None")
            
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        print(f"    Traceback: {traceback.format_exc()}")
    
    # Test 2: Direct import of core agent manager
    print("\n2. Testing Core Agent Manager Direct Import...")
    try:
        from core.agent_manager import AgentManager
        print("  ✓ Core AgentManager imported successfully")
        
        # Try to create instance
        agent_manager = AgentManager()
        print("  ✓ Core AgentManager instance created")
        print(f"  ✓ Agent manager type: {type(agent_manager)}")
        
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        print(f"    Traceback: {traceback.format_exc()}")
    
    # Test 3: AI Manager import
    print("\n3. Testing AI Manager Import...")
    try:
        ai_dir = os.path.join(freecad_ai_dir, 'ai')
        if ai_dir not in sys.path:
            sys.path.insert(0, ai_dir)
        
        from agent_manager import AIManager
        print("  ✓ AI Manager imported successfully")
        
        # Try to create instance
        ai_manager = AIManager()
        print("  ✓ AI Manager instance created")
        print(f"  ✓ AI Manager type: {type(ai_manager)}")
        
    except Exception as e:
        print(f"  ✗ Failed: {e}")
        print(f"    Traceback: {traceback.format_exc()}")

if __name__ == "__main__":
    test_agent_manager_import()
