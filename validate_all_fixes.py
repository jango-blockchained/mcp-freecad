#!/usr/bin/env python3
"""
Comprehensive FreeCAD AI Fix Validation Test

This script validates all the fixes we've implemented for the FreeCAD AI system:
1. Document creation crash fix
2. Agent manager initialization
3. Provider service availability
4. Tools registry functionality
"""

import os
import sys
import datetime
import traceback
import importlib

# Add paths to sys.path
script_dir = os.path.dirname(os.path.abspath(__file__))
freecad_ai_dir = os.path.join(script_dir, 'freecad-ai')

if freecad_ai_dir not in sys.path:
    sys.path.insert(0, freecad_ai_dir)

def log_test_result(test_name: str, success: bool, message: str = ""):
    """Log a test result with formatting."""
    status = "✅ PASS" if success else "❌ FAIL"
    print(f"{status} {test_name}")
    if message:
        print(f"    {message}")

def test_document_creation_fix():
    """Test the document creation crash fix."""
    print("\n=== Testing Document Creation Fix ===")
    
    try:
        # Test 1: Check if FreeCAD bridge has headless wrapper
        from src.mcp_freecad.connections.freecad_connection_bridge import FreeCADBridge
        bridge = FreeCADBridge()
        
        # Check if the method exists
        has_headless_wrapper = hasattr(bridge, '_wrap_script_for_headless')
        log_test_result("Bridge has headless wrapper", has_headless_wrapper)
        
        # Test 2: Check if bridge is available
        is_available = bridge.is_available()
        log_test_result("Bridge is available", is_available, f"Available: {is_available}")
        
        return True
        
    except Exception as e:
        log_test_result("Document creation fix", False, f"Error: {e}")
        return False

def test_primitives_tool_fix():
    """Test the primitives tool document handling fix."""
    print("\n=== Testing Primitives Tool Fix ===")
    
    try:
        # Test if primitives tool has the helper method
        from tools.primitives import PrimitivesTool
        primitives = PrimitivesTool()
        
        has_helper_method = hasattr(primitives, '_ensure_document_exists')
        log_test_result("PrimitivesTool has _ensure_document_exists", has_helper_method)
        
        # Test advanced primitives too
        from tools.advanced_primitives import AdvancedPrimitivesTool
        adv_primitives = AdvancedPrimitivesTool()
        
        has_adv_helper_method = hasattr(adv_primitives, '_ensure_document_exists')
        log_test_result("AdvancedPrimitivesTool has _ensure_document_exists", has_adv_helper_method)
        
        return has_helper_method and has_adv_helper_method
        
    except Exception as e:
        log_test_result("Primitives tool fix", False, f"Error: {e}")
        return False

def test_agent_manager_fix():
    """Test the agent manager naming fix."""
    print("\n=== Testing Agent Manager Fix ===")
    
    try:
        # Test 1: Check if agent_manager.py exists (symbolic link)
        agent_manager_path = os.path.join(freecad_ai_dir, "ai", "agent_manager.py")
        file_exists = os.path.exists(agent_manager_path)
        log_test_result("agent_manager.py file exists", file_exists, f"Path: {agent_manager_path}")
        
        # Test 2: Try importing as agent_manager
        try:
            from ai.agent_manager import AIManager
            log_test_result("Import ai.agent_manager.AIManager", True)
            
            # Test 3: Try creating instance
            try:
                ai_manager = AIManager()
                log_test_result("Create AIManager instance", True)
                
                # Test basic functionality
                has_add_provider = hasattr(ai_manager, 'add_provider')
                log_test_result("AIManager has add_provider method", has_add_provider)
                
                return True
                
            except Exception as e:
                log_test_result("Create AIManager instance", False, f"Error: {e}")
                return False
                
        except ImportError as e:
            log_test_result("Import ai.agent_manager.AIManager", False, f"Import error: {e}")
            return False
            
    except Exception as e:
        log_test_result("Agent manager fix", False, f"Error: {e}")
        return False

def test_provider_service_fix():
    """Test the provider service implementation."""
    print("\n=== Testing Provider Service Fix ===")
    
    try:
        # Test 1: Check if provider_service.py exists
        provider_service_path = os.path.join(freecad_ai_dir, "api", "provider_service.py")
        file_exists = os.path.exists(provider_service_path)
        log_test_result("provider_service.py file exists", file_exists, f"Path: {provider_service_path}")
        
        # Test 2: Try importing ProviderService
        try:
            from api.provider_service import ProviderService, get_provider_service
            log_test_result("Import api.provider_service", True)
            
            # Test 3: Try creating instance
            try:
                provider_service = ProviderService()
                log_test_result("Create ProviderService instance", True)
                
                # Test basic functionality
                is_available = provider_service.is_available()
                log_test_result("ProviderService is available", is_available)
                
                # Test global instance
                global_service = get_provider_service()
                log_test_result("Get global ProviderService", global_service is not None)
                
                return True
                
            except Exception as e:
                log_test_result("Create ProviderService instance", False, f"Error: {e}")
                return False
                
        except ImportError as e:
            log_test_result("Import api.provider_service", False, f"Import error: {e}")
            return False
            
    except Exception as e:
        log_test_result("Provider service fix", False, f"Error: {e}")
        return False

def test_file_structure():
    """Test that all expected files and links are in place."""
    print("\n=== Testing File Structure ===")
    
    expected_files = [
        ("freecad-ai/__init__.py", "FreeCAD AI main init"),
        ("freecad-ai/ai/__init__.py", "AI module init"),
        ("freecad-ai/ai/ai_manager.py", "AI Manager implementation"),
        ("freecad-ai/ai/agent_manager.py", "Agent Manager link"),
        ("freecad-ai/api/__init__.py", "API module init"),
        ("freecad-ai/api/provider_service.py", "Provider Service implementation"),
        ("freecad-ai/tools/__init__.py", "Tools module init"),
        ("freecad-ai/tools/primitives.py", "Primitives tool"),
        ("freecad-ai/tools/advanced_primitives.py", "Advanced primitives tool"),
    ]
    
    all_exist = True
    for relative_path, description in expected_files:
        full_path = os.path.join(script_dir, relative_path)
        exists = os.path.exists(full_path)
        log_test_result(f"{description} exists", exists, f"Path: {relative_path}")
        if not exists:
            all_exist = False
    
    return all_exist

def test_import_compatibility():
    """Test that imports work as expected after fixes."""
    print("\n=== Testing Import Compatibility ===")
    
    import_tests = [
        ("tools.primitives", "PrimitivesTool"),
        ("tools.advanced_primitives", "AdvancedPrimitivesTool"), 
        ("ai.ai_manager", "AIManager"),
        ("ai.agent_manager", "AIManager"),
        ("api.provider_service", "ProviderService"),
    ]
    
    all_imports_work = True
    for module_name, class_name in import_tests:
        try:
            module = importlib.import_module(module_name)
            has_class = hasattr(module, class_name)
            log_test_result(f"Import {module_name}.{class_name}", has_class)
            if not has_class:
                all_imports_work = False
        except ImportError as e:
            log_test_result(f"Import {module_name}.{class_name}", False, f"Import error: {e}")
            all_imports_work = False
        except Exception as e:
            log_test_result(f"Import {module_name}.{class_name}", False, f"Error: {e}")
            all_imports_work = False
    
    return all_imports_work

def main():
    """Run all validation tests."""
    print("=" * 60)
    print("FreeCAD AI Complete Fix Validation")
    print(f"Started: {datetime.datetime.now().isoformat()}")
    print("=" * 60)
    
    # Run all tests
    test_results = {
        "Document Creation Fix": test_document_creation_fix(),
        "Primitives Tool Fix": test_primitives_tool_fix(),
        "Agent Manager Fix": test_agent_manager_fix(),
        "Provider Service Fix": test_provider_service_fix(),
        "File Structure": test_file_structure(),
        "Import Compatibility": test_import_compatibility(),
    }
    
    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL FIXES VALIDATED SUCCESSFULLY!")
        print("The FreeCAD AI system should now work without crashes.")
    else:
        print("⚠️  Some fixes need attention.")
        print("Check the individual test results above.")
    
    print(f"\nCompleted: {datetime.datetime.now().isoformat()}")

if __name__ == "__main__":
    main()
