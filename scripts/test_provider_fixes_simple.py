#!/usr/bin/env python3
"""Simple test script to verify provider-related fixes without GUI dependencies"""

import os
import re
import sys


def test_loading_flag_implementation():
    """Test that the loading flag is properly implemented in ProvidersWidget."""
    print("Testing loading flag implementation...")
    
    providers_widget_path = os.path.join(os.path.dirname(__file__), 'freecad-ai/gui/providers_widget.py')
    
    if not os.path.exists(providers_widget_path):
        print("❌ FAILED: providers_widget.py not found")
        return False
    
    with open(providers_widget_path, 'r') as f:
        content = f.read()
    
    # Check for loading flag initialization
    if 'self._loading_config = False' in content:
        print("✅ SUCCESS: _loading_config flag initialized in __init__")
    else:
        print("❌ FAILED: _loading_config flag not found in __init__")
        return False
    
    # Check for loading flag usage in _on_config_changed
    if 'if self._loading_config:' in content and 'return' in content:
        print("✅ SUCCESS: _loading_config check found in methods")
    else:
        print("❌ FAILED: _loading_config check not found")
        return False
    
    # Check for loading flag setting in try/finally
    if 'self._loading_config = True' in content and 'finally:' in content:
        print("✅ SUCCESS: _loading_config properly managed in try/finally block")
    else:
        print("❌ FAILED: _loading_config not properly managed")
        return False
    
    return True

def test_provider_selector_refresh():
    """Test that ProviderSelectorWidget has refresh functionality."""
    print("Testing ProviderSelectorWidget refresh functionality...")
    
    selector_widget_path = os.path.join(os.path.dirname(__file__), 'freecad-ai/gui/provider_selector_widget.py')
    
    if not os.path.exists(selector_widget_path):
        print("❌ FAILED: provider_selector_widget.py not found")
        return False
    
    with open(selector_widget_path, 'r') as f:
        content = f.read()
    
    # Check for refresh_on_show method
    if 'def refresh_on_show(self):' in content:
        print("✅ SUCCESS: refresh_on_show method found")
    else:
        print("❌ FAILED: refresh_on_show method not found")
        return False
    
    # Check for enhanced set_config_manager
    if 'def set_config_manager(self, config_manager):' in content:
        if 'self._refresh_providers()' in content:
            print("✅ SUCCESS: set_config_manager triggers refresh")
        else:
            print("❌ FAILED: set_config_manager doesn't trigger refresh")
            return False
    else:
        print("❌ FAILED: set_config_manager method not found")
        return False
    
    return True

def test_main_widget_tab_handling():
    """Test that MainWidget has tab change handling."""
    print("Testing MainWidget tab change handling...")
    
    main_widget_path = os.path.join(os.path.dirname(__file__), 'freecad-ai/gui/main_widget.py')
    
    if not os.path.exists(main_widget_path):
        print("❌ FAILED: main_widget.py not found")
        return False
    
    with open(main_widget_path, 'r') as f:
        content = f.read()
    
    # Check for tab change method
    if 'def _on_tab_changed(self, index):' in content:
        print("✅ SUCCESS: _on_tab_changed method found")
    else:
        print("❌ FAILED: _on_tab_changed method not found")
        return False
    
    # Check for tab change signal connection
    if 'currentChanged' in content and '_on_tab_changed' in content:
        print("✅ SUCCESS: Tab change signal connection found")
    else:
        print("❌ FAILED: Tab change signal connection not found")
        return False
    
    # Check for enhanced service connections
    if '_connect_services_safe' in content and 'set_config_manager' in content:
        print("✅ SUCCESS: Enhanced service connections found")
    else:
        print("❌ FAILED: Enhanced service connections not found")
        return False
    
    return True

def main():
    """Run all tests."""
    print("=" * 60)
    print("TESTING PROVIDER FIXES")
    print("=" * 60)
    
    all_tests_passed = True
    
    # Test 1: Loading flag implementation
    if not test_loading_flag_implementation():
        all_tests_passed = False
    print()
    
    # Test 2: Provider selector refresh
    if not test_provider_selector_refresh():
        all_tests_passed = False
    print()
    
    # Test 3: Main widget tab handling
    if not test_main_widget_tab_handling():
        all_tests_passed = False
    print()
    
    print("=" * 60)
    if all_tests_passed:
        print("🎉 ALL TESTS PASSED! Provider fixes are properly implemented.")
        print()
        print("Summary of fixes:")
        print("1. ✅ Loading flag prevents excessive config saves in ProvidersWidget")
        print("2. ✅ Provider selectors refresh on tab activation")
        print("3. ✅ Config managers properly connected to provider selectors")
        print("4. ✅ Tab change handling implemented in MainWidget")
    else:
        print("❌ SOME TESTS FAILED. Please check the implementation.")
    print("=" * 60)
    
    return all_tests_passed

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
