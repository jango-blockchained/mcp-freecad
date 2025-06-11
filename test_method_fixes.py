#!/usr/bin/env python3
"""
Test script to verify the missing methods have been added to enhanced widgets.
This tests for method existence without instantiating the widgets.
"""

import sys
import os
import inspect

# Add the freecad-ai directory to the path
freecad_ai_path = os.path.join(os.path.dirname(__file__), 'freecad-ai')
sys.path.insert(0, freecad_ai_path)

def test_method_exists():
    """Test that the missing methods now exist in the enhanced widgets."""
    print("Testing method existence without GUI instantiation...")
    
    try:
        # Test EnhancedConversationWidget has _toggle_mode
        print("\nTesting EnhancedConversationWidget...")
        from gui.enhanced_conversation_widget import EnhancedConversationWidget
        
        # Check if _toggle_mode method exists
        if hasattr(EnhancedConversationWidget, '_toggle_mode'):
            print("✅ _toggle_mode method found")
        else:
            print("❌ _toggle_mode method NOT found")
            return False
            
        # List all methods to see what we have
        methods = [method for method in dir(EnhancedConversationWidget) 
                  if callable(getattr(EnhancedConversationWidget, method)) and not method.startswith('__')]
        print(f"   Total methods: {len(methods)}")
        
        # Test EnhancedAgentControlWidget has _on_provider_changed
        print("\nTesting EnhancedAgentControlWidget...")
        from gui.enhanced_agent_control_widget import EnhancedAgentControlWidget
        
        # Check if _on_provider_changed method exists
        if hasattr(EnhancedAgentControlWidget, '_on_provider_changed'):
            print("✅ _on_provider_changed method found")
        else:
            print("❌ _on_provider_changed method NOT found")
            return False
            
        # Check other essential methods
        essential_methods = [
            '_toggle_execution',
            '_stop_execution', 
            '_step_execution',
            '_clear_queue',
            '_move_queue_item_up',
            '_move_queue_item_down',
            '_remove_queue_item'
        ]
        
        for method in essential_methods:
            if hasattr(EnhancedAgentControlWidget, method):
                print(f"✅ {method} method found")
            else:
                print(f"❌ {method} method NOT found")
                return False
        
        # List all methods
        agent_methods = [method for method in dir(EnhancedAgentControlWidget) 
                        if callable(getattr(EnhancedAgentControlWidget, method)) and not method.startswith('__')]
        print(f"   Total methods: {len(agent_methods)}")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

def main():
    """Main test function."""
    print("=" * 60)
    print("ENHANCED WIDGET METHOD VERIFICATION TEST")
    print("=" * 60)
    
    success = test_method_exists()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ ALL TESTS PASSED - Missing methods have been added!")
    else:
        print("❌ TESTS FAILED - Some methods are still missing")
    print("=" * 60)
    
    return success

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
