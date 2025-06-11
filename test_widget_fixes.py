#!/usr/bin/env python3
"""
Test script to verify enhanced widget fixes
Tests both EnhancedConversationWidget and EnhancedAgentControlWidget for missing methods
"""

import sys
import os

# Add the freecad-ai directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'freecad-ai'))

def test_enhanced_conversation_widget():
    """Test EnhancedConversationWidget for missing methods."""
    print("Testing EnhancedConversationWidget...")
    
    try:
        # Import the widget
        from gui.enhanced_conversation_widget import EnhancedConversationWidget
        print("✅ Import successful")
        
        # Check for essential methods
        essential_methods = [
            '_toggle_mode',
            '_on_provider_changed', 
            '_send_message',
            '_clear_conversation',
            '_add_conversation_message',
            '_gather_freecad_context'
        ]
        
        for method_name in essential_methods:
            if hasattr(EnhancedConversationWidget, method_name):
                print(f"✅ Method {method_name} exists")
            else:
                print(f"❌ Method {method_name} MISSING")
                return False
                
        print("✅ All essential methods found in EnhancedConversationWidget")
        return True
        
    except Exception as e:
        print(f"❌ Error testing EnhancedConversationWidget: {e}")
        return False

def test_enhanced_agent_control_widget():
    """Test EnhancedAgentControlWidget for missing methods."""
    print("\nTesting EnhancedAgentControlWidget...")
    
    try:
        # Import the widget
        from gui.enhanced_agent_control_widget import EnhancedAgentControlWidget
        print("✅ Import successful")
        
        # Check for essential methods
        essential_methods = [
            '_on_provider_changed',
            '_on_provider_refresh',
            '_toggle_execution',
            '_stop_execution',
            '_step_execution',
            '_clear_queue',
            '_edit_queue_item',
            'set_agent_manager',
            'set_provider_service'
        ]
        
        for method_name in essential_methods:
            if hasattr(EnhancedAgentControlWidget, method_name):
                print(f"✅ Method {method_name} exists")
            else:
                print(f"❌ Method {method_name} MISSING")
                return False
                
        print("✅ All essential methods found in EnhancedAgentControlWidget")
        return True
        
    except Exception as e:
        print(f"❌ Error testing EnhancedAgentControlWidget: {e}")
        return False

def test_widget_instantiation():
    """Test that widgets can be instantiated without crashing."""
    print("\nTesting widget instantiation...")
    
    try:
        # Set up minimal Qt application for testing
        from PySide2 import QtWidgets
        import sys
        
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication(sys.argv)
        
        # Test EnhancedConversationWidget instantiation
        print("Creating EnhancedConversationWidget...")
        from gui.enhanced_conversation_widget import EnhancedConversationWidget
        conv_widget = EnhancedConversationWidget()
        print("✅ EnhancedConversationWidget created successfully")
        
        # Test EnhancedAgentControlWidget instantiation
        print("Creating EnhancedAgentControlWidget...")
        from gui.enhanced_agent_control_widget import EnhancedAgentControlWidget
        agent_widget = EnhancedAgentControlWidget()
        print("✅ EnhancedAgentControlWidget created successfully")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during widget instantiation: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("WIDGET FIXES VERIFICATION TEST")
    print("=" * 60)
    
    results = []
    
    # Test method existence
    results.append(test_enhanced_conversation_widget())
    results.append(test_enhanced_agent_control_widget())
    
    # Test instantiation
    results.append(test_widget_instantiation())
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    if all(results):
        print("✅ ALL TESTS PASSED - Enhanced widgets should work correctly")
        print("✅ Missing method errors should be resolved")
        return True
    else:
        print("❌ SOME TESTS FAILED - Additional fixes needed")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
