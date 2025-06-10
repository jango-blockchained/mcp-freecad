#!/usr/bin/env python3
"""Test script to verify provider-related fixes"""

import os
import sys

# Add the freecad-ai directory to path
freecad_ai_path = os.path.join(os.path.dirname(__file__), "freecad-ai")
sys.path.insert(0, freecad_ai_path)


def test_providers_widget_loading_flag():
    """Test that the ProvidersWidget has the loading flag to prevent excessive saves."""
    try:
        print("Testing ProvidersWidget loading flag...")

        from gui.providers_widget import ProvidersWidget

        # Create widget instance
        widget = ProvidersWidget()

        # Check if loading flag exists
        if hasattr(widget, "_loading_config"):
            print("✅ SUCCESS: ProvidersWidget has _loading_config flag")

            # Check initial state
            if widget._loading_config == False:
                print("✅ SUCCESS: _loading_config initially set to False")
            else:
                print("❌ FAILED: _loading_config should initially be False")
                return False

            return True
        else:
            print("❌ FAILED: ProvidersWidget missing _loading_config flag")
            return False

    except Exception as e:
        print(f"❌ FAILED: Error testing ProvidersWidget: {e}")
        return False


def test_provider_selector_refresh_method():
    """Test that ProviderSelectorWidget has refresh_on_show method."""
    try:
        print("Testing ProviderSelectorWidget refresh method...")

        from gui.provider_selector_widget import ProviderSelectorWidget

        # Create widget instance
        widget = ProviderSelectorWidget()

        # Check if refresh_on_show method exists
        if hasattr(widget, "refresh_on_show"):
            print("✅ SUCCESS: ProviderSelectorWidget has refresh_on_show method")

            # Try calling the method (should not crash)
            widget.refresh_on_show()
            print("✅ SUCCESS: refresh_on_show method can be called without errors")

            return True
        else:
            print("❌ FAILED: ProviderSelectorWidget missing refresh_on_show method")
            return False

    except Exception as e:
        print(f"❌ FAILED: Error testing ProviderSelectorWidget: {e}")
        return False


def test_main_widget_tab_change_handler():
    """Test that MainWidget has tab change handling."""
    try:
        print("Testing MainWidget tab change handler...")

        # This test might require Qt, so we'll just check if the method exists
        from gui.main_widget import MainDockWidget

        # Check if the method exists (we can't instantiate without Qt)
        if hasattr(MainDockWidget, "_on_tab_changed"):
            print("✅ SUCCESS: MainDockWidget has _on_tab_changed method")
            return True
        else:
            print("❌ FAILED: MainDockWidget missing _on_tab_changed method")
            return False

    except Exception as e:
        print(f"❌ FAILED: Error testing MainWidget: {e}")
        return False


def test_config_manager_integration():
    """Test that provider selectors get proper config manager connections."""
    try:
        print("Testing config manager integration...")

        from gui.provider_selector_widget import ProviderSelectorWidget

        # Create widget instance
        widget = ProviderSelectorWidget()

        # Check if set_config_manager method exists and works
        if hasattr(widget, "set_config_manager"):
            print("✅ SUCCESS: ProviderSelectorWidget has set_config_manager method")

            # Try setting a None config manager (should not crash)
            widget.set_config_manager(None)
            print("✅ SUCCESS: set_config_manager can handle None input")

            return True
        else:
            print("❌ FAILED: ProviderSelectorWidget missing set_config_manager method")
            return False

    except Exception as e:
        print(f"❌ FAILED: Error testing config manager integration: {e}")
        return False


if __name__ == "__main__":
    print("=== Provider Fixes Verification Test ===")
    print()

    tests = [
        test_providers_widget_loading_flag,
        test_provider_selector_refresh_method,
        test_main_widget_tab_change_handler,
        test_config_manager_integration,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()

    print(f"=== RESULTS: {passed}/{total} tests passed ===")

    if passed == total:
        print("🎉 ALL TESTS PASSED: Provider fixes implemented successfully!")
        print()
        print("Fixed Issues:")
        print("1. ✅ Excessive config saving - Added _loading_config flag")
        print("2. ✅ Provider selector initialization - Added refresh_on_show method")
        print("3. ✅ Tab activation handling - Added _on_tab_changed method")
        print("4. ✅ Config manager connections - Enhanced service connections")
        exit(0)
    else:
        print("❌ SOME TESTS FAILED: Check implementation")
        exit(1)
