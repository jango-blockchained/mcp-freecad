#!/usr/bin/env python3
"""
Test Document Creation and Shape Operations

This script tests the fix for crash when creating a shape and a new document.
"""

import sys
import os
import importlib.util

# Add project root to path
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def load_module_from_path(name, path):
    """Load a Python module from file path"""
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module

def test_connection_bridge():
    """Test the FreeCAD connection bridge with document creation and shape creation"""
    from src.mcp_freecad.connections.freecad_connection_bridge import FreeCADBridge
    
    # Create bridge instance
    bridge = FreeCADBridge()
    
    # Check if bridge is available
    if not bridge.is_available():
        print("FreeCAD bridge is not available. Skipping test.")
        return
    
    print("Testing FreeCAD connection bridge...")
    
    try:
        # Test without document: create box should make new document
        box_name = bridge.create_box(10, 20, 30)
        print(f"✓ Created box '{box_name}' without explicit document (new document created)")
        
        # Create a document explicitly
        doc_name = bridge.create_document("TestDoc")
        print(f"✓ Created document '{doc_name}'")
        
        # Create box in the document
        box_name = bridge.create_box(5, 5, 5, doc_name)
        print(f"✓ Created box '{box_name}' in document '{doc_name}'")
        
        print("Bridge test successful!")
    except Exception as e:
        print(f"Error testing bridge: {e}")
        import traceback
        traceback.print_exc()

def test_primitives_tool():
    """Test the PrimitivesTool with document creation and shape creation"""
    try:
        # Import FreeCAD
        import FreeCAD
        print("FreeCAD available for direct import")
        
        # Check if there's an active document
        has_active = bool(FreeCAD.ActiveDocument)
        print(f"Has active document: {has_active}")
        
        # Import tools
        from freecad_ai.tools.primitives import PrimitivesTool
        from freecad_ai.tools.advanced_primitives import AdvancedPrimitivesTool
        
        # Create instances
        primitives = PrimitivesTool()
        adv_primitives = AdvancedPrimitivesTool()
        
        # Test primitives
        print("\nTesting PrimitivesTool...")
        box_result = primitives.create_box(10, 20, 30)
        if box_result.get("success", False):
            print(f"✓ Created box: {box_result.get('object_name')}")
        else:
            print(f"✗ Failed to create box: {box_result.get('error')}")
        
        # Test advanced primitives
        print("\nTesting AdvancedPrimitivesTool...")
        tube_result = adv_primitives.create_tube(10, 5, 20)
        if tube_result.get("success", False):
            print(f"✓ Created tube: {tube_result.get('object_name')}")
        else:
            print(f"✗ Failed to create tube: {tube_result.get('error')}")
            
    except ImportError:
        print("FreeCAD not available for direct import. Skipping PrimitivesTool test.")
    except Exception as e:
        print(f"Error testing tools: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("=== Testing Document and Shape Creation ===\n")
    test_connection_bridge()
    print("\n--- Direct Import Tests ---")
    test_primitives_tool()
    print("\n=== Tests Completed ===")
