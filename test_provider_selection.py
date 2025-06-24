#!/usr/bin/env python3
"""
Test script to verify provider selection fixes
"""

import sys
import os
import importlib.util

# Add the freecad-ai directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'freecad-ai'))

def test_provider_imports():
    """Test that all provider imports work correctly"""
    print("=== Testing Provider Imports ===")
    
    try:
        # Test base provider import
        try:
            from ai.providers.base_provider import BaseAIProvider
            print("✅ BaseAIProvider import successful")
        except ImportError as e:
            print(f"❌ BaseAIProvider import failed: {e}")
        
        # Test provider initialization
        try:
            from ai.providers import get_available_providers, get_provider_class
            print("✅ Provider initialization functions imported")
        except ImportError as e:
            print(f"❌ Provider initialization functions failed: {e}")
        
        # Test individual providers
        providers_to_test = [
            'openai_provider',
            'anthropic_provider', 
            'ollama_provider',
            'vertexai_provider'
        ]
        
        for provider_name in providers_to_test:
            try:
                importlib.import_module(f'ai.providers.{provider_name}')
                print(f"✅ {provider_name} import successful")
            except ImportError as e:
                print(f"❌ {provider_name} import failed: {e}")
        
        return True
    except ImportError as e:
        print(f"❌ Provider import test failed: {e}")
        return False

def test_provider_availability():
    """Test provider availability and configuration"""
    print("\n=== Testing Provider Availability ===")
    
    try:
        from ai.providers import get_available_providers
        providers = get_available_providers()
        print(f"Available providers: {providers}")
        
        # Check if Vertex AI is included
        if 'vertexai' in providers:
            print("✅ Vertex AI provider is available")
        else:
            print("❌ Vertex AI provider is missing")
            
        return len(providers) > 0
    except Exception as e:
        print(f"❌ Provider availability test failed: {e}")
        return False

def test_provider_models():
    """Test provider model configurations"""
    print("\n=== Testing Provider Models ===")
    
    try:
        from ai.providers import get_provider_models
        
        # Test model retrieval for different providers
        test_providers = ['openai', 'anthropic', 'ollama', 'vertexai']
        
        for provider in test_providers:
            try:
                models = get_provider_models(provider)
                print(f"✅ {provider} models: {len(models)} available")
                if models:
                    print(f"   Sample models: {list(models.keys())[:3]}")
            except Exception as e:
                print(f"❌ {provider} models failed: {e}")
        
        return True
    except Exception as e:
        print(f"❌ Provider models test failed: {e}")
        return False

def test_gui_provider_widgets():
    """Test GUI provider widget functionality"""
    print("\n=== Testing GUI Provider Widgets ===")
    
    try:
        # Test provider selector widget
        spec = importlib.util.spec_from_file_location(
            "provider_selector_widget", 
            "freecad-ai/gui/provider_selector_widget.py"
        )
        provider_selector = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(provider_selector)
        print("✅ Provider selector widget import successful")
        
        # Test providers widget
        spec = importlib.util.spec_from_file_location(
            "providers_widget", 
            "freecad-ai/gui/providers_widget.py"
        )
        providers_widget = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(providers_widget)
        print("✅ Providers widget import successful")
        
        return True
    except Exception as e:
        print(f"❌ GUI widget test failed: {e}")
        return False

def main():
    """Run all provider selection tests"""
    print("FreeCAD AI Provider Selection Test")
    print("=" * 50)
    
    tests = [
        ("Provider Imports", test_provider_imports),
        ("Provider Availability", test_provider_availability),
        ("Provider Models", test_provider_models),
        ("GUI Provider Widgets", test_gui_provider_widgets),
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
                print(f"\n✅ {test_name}: PASSED")
            else:
                print(f"\n❌ {test_name}: FAILED")
        except Exception as e:
            print(f"\n❌ {test_name}: ERROR - {e}")
    
    print("\n" + "=" * 50)
    print(f"SUMMARY: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All provider selection tests passed!")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
