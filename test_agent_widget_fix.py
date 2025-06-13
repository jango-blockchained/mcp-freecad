#!/usr/bin/env python3
"""Test script to verify the enhanced agent control widget fix."""

import sys
import os

# Add the freecad-ai directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'freecad-ai'))

def test_enhanced_agent_widget():
    """Test that the enhanced agent control widget loads and has all required methods."""
    try:
        # Import the widget
        from gui.enhanced_agent_control_widget import EnhancedAgentControlWidget
        print("✅ SUCCESS: Enhanced agent control widget imported successfully")
        
        # Check if all expected methods exist
        required_methods = [
            '_remove_queue_item',
            '_edit_queue_item', 
            '_set_task_priority',
            '_clear_queue',
            '_move_queue_item_up',
            '_move_queue_item_down',
            '_send_command',
            '_clear_history',
            '_toggle_execution',
            '_stop_execution', 
            '_step_execution',
            '_show_advanced_diagnostics',
            '_show_quick_status',
            '_export_settings'
        ]
        
        missing_methods = []
        for method_name in required_methods:
            if not hasattr(EnhancedAgentControlWidget, method_name):
                missing_methods.append(method_name)
        
        if missing_methods:
            print(f"❌ ERROR: Missing methods: {missing_methods}")
            return False
        else:
            print("✅ SUCCESS: All required methods are present")
        
        # Test method functionality (without GUI)
        import inspect
        remove_method = getattr(EnhancedAgentControlWidget, '_remove_queue_item')
        signature = inspect.signature(remove_method)
        print(f"✅ SUCCESS: _remove_queue_item method signature: {signature}")
        
        return True
        
    except ImportError as e:
        print(f"❌ IMPORT ERROR: {e}")
        return False
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_method_integration():
    """Test that the method is properly integrated with the button."""
    try:
        # Read the file to verify button connection
        widget_file = os.path.join(os.path.dirname(__file__), 'freecad-ai', 'gui', 'enhanced_agent_control_widget.py')
        with open(widget_file, 'r') as f:
            content = f.read()
        
        # Check that the button is connected to the method
        if 'self.remove_item_btn.clicked.connect(self._remove_queue_item)' in content:
            print("✅ SUCCESS: Remove button is properly connected to method")
        else:
            print("❌ ERROR: Remove button connection not found")
            return False
            
        # Check that the method is properly defined
        if 'def _remove_queue_item(self):' in content:
            print("✅ SUCCESS: _remove_queue_item method is properly defined")
        else:
            print("❌ ERROR: _remove_queue_item method definition not found")
            return False
            
        return True
        
    except Exception as e:
        print(f"❌ ERROR checking integration: {e}")
        return False

if __name__ == "__main__":
    print("Testing Enhanced Agent Control Widget Fix...")
    print("=" * 50)
    
    # Run tests
    widget_test = test_enhanced_agent_widget()
    integration_test = test_method_integration()
    
    print("=" * 50)
    if widget_test and integration_test:
        print("🎉 ALL TESTS PASSED: The missing method error has been fixed!")
        sys.exit(0)
    else:
        print("💥 SOME TESTS FAILED: There may still be issues")
        sys.exit(1)
