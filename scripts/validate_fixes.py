#!/usr/bin/env python3
"""
Quick validation of the fixes without FreeCAD dependency
"""


def test_provider_service_function_exists():
    """Test that get_provider_service function exists"""
    try:
        # Read the file and check for the function
        with open("freecad-ai/ai/provider_integration_service.py", "r") as f:
            content = f.read()

        if "def get_provider_service():" in content:
            print("✅ get_provider_service() function found")
            return True
        else:
            print("❌ get_provider_service() function not found")
            return False
    except Exception as e:
        print(f"❌ Error checking provider service: {e}")
        return False


def test_openrouter_sync_method():
    """Test that OpenRouter has synchronous get_available_models"""
    try:
        with open("freecad-ai/ai/providers/openrouter_provider.py", "r") as f:
            content = f.read()

        # Check for sync method
        if "def get_available_models(self) -> List[str]:" in content:
            print("✅ OpenRouter synchronous get_available_models() found")
            sync_found = True
        else:
            print("❌ OpenRouter synchronous get_available_models() not found")
            sync_found = False

        # Check for async method too
        if "async def get_available_models_async(self)" in content:
            print("✅ OpenRouter async get_available_models_async() found")
            async_found = True
        else:
            print("❌ OpenRouter async get_available_models_async() not found")
            async_found = False

        return sync_found and async_found
    except Exception as e:
        print(f"❌ Error checking OpenRouter provider: {e}")
        return False


def test_config_cleanup():
    """Test that config duplicates were cleaned up"""
    try:
        import json

        with open("freecad-ai/addon_config.json", "r") as f:
            config = json.load(f)

        providers = config.get("providers", {})

        # Check for problematic duplicates
        issues = []
        if "Anthropic" in providers and "anthropic" in providers:
            issues.append("Anthropic/anthropic still duplicated")
        if "Google" in providers and "google" in providers:
            issues.append("Google/google still duplicated")
        if "OpenRouter" in providers and "openrouter" in providers:
            issues.append("OpenRouter/openrouter still duplicated")

        if issues:
            print("❌ Config issues found:", ", ".join(issues))
            return False
        else:
            print("✅ Config duplicates cleaned up")
            return True

    except Exception as e:
        print(f"❌ Error checking config: {e}")
        return False


if __name__ == "__main__":
    print("=== FreeCAD AI Addon Fix Validation ===")

    test1 = test_provider_service_function_exists()
    test2 = test_openrouter_sync_method()
    test3 = test_config_cleanup()

    if all([test1, test2, test3]):
        print("\n🎉 ALL VALIDATION CHECKS PASSED!")
        print("Both fixes appear to be correctly implemented.")
    else:
        print("\n💥 SOME VALIDATION CHECKS FAILED!")
        print("Fixes may need additional work.")
