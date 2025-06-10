#!/usr/bin/env python3
"""Test script to verify OpenRouter async models fix"""

import os
import sys

# Add the freecad-ai directory to path
freecad_ai_path = os.path.join(os.path.dirname(__file__), 'freecad-ai')
sys.path.insert(0, freecad_ai_path)

def test_openrouter_models_sync():
    """Test that OpenRouter get_available_models() is now synchronous"""
    try:
        print("Testing OpenRouter models sync fix...")
        
        # Import the provider
        from ai.providers.openrouter_provider import OpenRouterProvider

        # Create provider instance (with dummy API key for testing)
        provider = OpenRouterProvider(api_key="sk-or-test-key")
        
        # Test sync method
        print("Testing get_available_models()...")
        models = provider.get_available_models()
        
        # Verify it returns a list, not a coroutine
        if isinstance(models, list):
            print(f"✅ SUCCESS: get_available_models() returns list with {len(models)} models")
            print(f"Sample models: {models[:3]}...")
            return True
        else:
            print(f"❌ FAILED: get_available_models() returned {type(models)}, expected list")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Error testing OpenRouter models: {e}")
        return False

def test_openrouter_async_method():
    """Test that async method still exists"""
    try:
        print("\nTesting async method availability...")
        
        from ai.providers.openrouter_provider import OpenRouterProvider
        provider = OpenRouterProvider(api_key="sk-or-test-key")
        
        # Check if async method exists
        if hasattr(provider, 'get_available_models_async'):
            print("✅ SUCCESS: get_available_models_async() method exists")
            return True
        else:
            print("❌ FAILED: get_available_models_async() method missing")
            return False
            
    except Exception as e:
        print(f"❌ FAILED: Error checking async method: {e}")
        return False

def test_ui_compatibility():
    """Test UI compatibility with model list"""
    try:
        print("\nTesting UI compatibility...")
        
        from ai.providers.openrouter_provider import OpenRouterProvider
        provider = OpenRouterProvider(api_key="sk-or-test-key")
        
        models = provider.get_available_models()
        
        # Test that we can iterate (like UI would)
        for i, model in enumerate(models[:3]):
            if not isinstance(model, str):
                print(f"❌ FAILED: Model {i} is {type(model)}, expected str")
                return False
        
        print("✅ SUCCESS: All models are strings, UI compatible")
        return True
        
    except Exception as e:
        print(f"❌ FAILED: UI compatibility test failed: {e}")
        return False

if __name__ == "__main__":
    print("=== OpenRouter Async Models Fix Test ===")
    
    test1 = test_openrouter_models_sync()
    test2 = test_openrouter_async_method()  
    test3 = test_ui_compatibility()
    
    if all([test1, test2, test3]):
        print("\n🎉 ALL TESTS PASSED: OpenRouter async models fix successful!")
        print("✅ Provider UI selection should now work without errors")
        exit(0)
    else:
        print("\n💥 SOME TESTS FAILED: OpenRouter fix needs more work")
        exit(1)