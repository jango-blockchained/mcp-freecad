#!/usr/bin/env python3
"""Test script to verify provider service import fix"""

import os
import sys

# Add the freecad-ai directory to path
freecad_ai_path = os.path.join(os.path.dirname(__file__), "freecad-ai")
sys.path.insert(0, freecad_ai_path)


def test_provider_service_import():
    """Test if provider service can be imported successfully"""
    try:
        print("Testing provider service import...")
        from ai.provider_integration_service import get_provider_service

        print("✅ SUCCESS: get_provider_service import successful")

        # Test getting the service instance
        print("Testing service instantiation...")
        service = get_provider_service()
        print(f"✅ SUCCESS: Service instance created: {service is not None}")

        if service:
            print(f"Service type: {type(service).__name__}")

        return True

    except ImportError as e:
        print(f"❌ FAILED: Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        return False


def test_provider_class_import():
    """Test if provider classes can be imported"""
    try:
        print("\nTesting provider class imports...")
        from ai.provider_integration_service import ProviderIntegrationService

        print("✅ SUCCESS: ProviderIntegrationService import successful")

        return True

    except ImportError as e:
        print(f"❌ FAILED: Provider class import error: {e}")
        return False
    except Exception as e:
        print(f"❌ FAILED: Unexpected error: {e}")
        return False


if __name__ == "__main__":
    print("=== Provider Service Import Fix Test ===")

    success1 = test_provider_service_import()
    success2 = test_provider_class_import()

    if success1 and success2:
        print("\n🎉 ALL TESTS PASSED: Provider service import fix successful!")
        exit(0)
    else:
        print("\n💥 TESTS FAILED: Provider service import still has issues")
        exit(1)
