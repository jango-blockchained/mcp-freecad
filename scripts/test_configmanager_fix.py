#!/usr/bin/env python3
"""
Test script to verify the ConfigManager attribute fix
"""

import os
import sys

# Add the freecad-ai directory to path
freecad_ai_path = os.path.join(os.path.dirname(__file__), "freecad-ai")
sys.path.insert(0, freecad_ai_path)


def test_config_manager_attributes():
    """Test that ConfigManager has the correct attributes."""
    print("Testing ConfigManager attributes...")

    try:
        from config.config_manager import ConfigManager

        # Create instance
        config_manager = ConfigManager()

        # Check if it has 'config' attribute (correct)
        if hasattr(config_manager, "config"):
            print("✅ SUCCESS: ConfigManager has 'config' attribute")
        else:
            print("❌ FAILED: ConfigManager missing 'config' attribute")
            return False

        # Check if it incorrectly has 'config_data' attribute
        if hasattr(config_manager, "config_data"):
            print("⚠️  WARNING: ConfigManager has 'config_data' attribute (unexpected)")
        else:
            print(
                "✅ SUCCESS: ConfigManager does not have 'config_data' attribute (correct)"
            )

        # Test that config is accessible
        try:
            config_data = config_manager.config
            print(f"✅ SUCCESS: config attribute accessible, type: {type(config_data)}")
            return True
        except Exception as e:
            print(f"❌ FAILED: Error accessing config attribute: {e}")
            return False

    except Exception as e:
        print(f"❌ FAILED: Error importing ConfigManager: {e}")
        return False


def test_provider_integration_service():
    """Test that provider integration service can be imported without errors."""
    print("Testing ProviderIntegrationService import...")

    try:
        from ai.provider_integration_service import ProviderIntegrationService

        # Try to create instance
        service = ProviderIntegrationService()
        print("✅ SUCCESS: ProviderIntegrationService imported and instantiated")

        # Check if config_manager is set up
        if hasattr(service, "config_manager") and service.config_manager:
            print("✅ SUCCESS: ProviderIntegrationService has config_manager")

            # Test accessing config through the service (this was the failing code)
            try:
                providers_config = service.config_manager.config.get("providers", {})
                print(
                    f"✅ SUCCESS: Can access providers config: {len(providers_config)} providers found"
                )
                return True
            except AttributeError as e:
                print(f"❌ FAILED: AttributeError when accessing config: {e}")
                return False
        else:
            print("⚠️  WARNING: ProviderIntegrationService has no config_manager")
            return True  # Still success for import test

    except Exception as e:
        print(f"❌ FAILED: Error with ProviderIntegrationService: {e}")
        return False


def main():
    """Run all tests."""
    print("=" * 60)
    print("TESTING CONFIGMANAGER ATTRIBUTE FIX")
    print("=" * 60)

    test1_passed = test_config_manager_attributes()
    print()
    test2_passed = test_provider_integration_service()
    print()

    print("=" * 60)
    if test1_passed and test2_passed:
        print("🎉 ALL TESTS PASSED! ConfigManager attribute fix is working.")
    else:
        print("❌ SOME TESTS FAILED. Check the output above.")
    print("=" * 60)

    return test1_passed and test2_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
