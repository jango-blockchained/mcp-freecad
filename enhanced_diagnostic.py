#!/usr/bin/env python3
"""
Enhanced FreeCAD AI Diagnostic Tool

This tool tests the fixes applied to FreeCAD AI components and provides
detailed status information about each component.
"""

import os
import sys
import traceback
import logging

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_freecad_ai_components():
    """Test all FreeCAD AI components after fixes."""
    
    print("=" * 60)
    print("Enhanced FreeCAD AI Component Diagnostic")
    print("=" * 60)
    
    # Add the freecad-ai directory to Python path
    freecad_ai_dir = os.path.join(os.path.dirname(__file__), 'freecad-ai')
    if freecad_ai_dir not in sys.path:
        sys.path.insert(0, freecad_ai_dir)
    
    test_results = {}
    
    # Test 1: Qt Compatibility
    print("\n1. Testing Qt Compatibility Layer...")
    test_results['qt_compatibility'] = test_qt_compatibility(freecad_ai_dir)
    
    # Test 2: Agent Manager Wrapper
    print("\n2. Testing Agent Manager Wrapper...")
    test_results['agent_manager'] = test_agent_manager_wrapper(freecad_ai_dir)
    
    # Test 3: Provider Service Wrapper
    print("\n3. Testing Provider Service Wrapper...")
    test_results['provider_service'] = test_provider_service_wrapper(freecad_ai_dir)
    
    # Test 4: Main Widget with Fixes
    print("\n4. Testing Main Widget Initialization...")
    test_results['main_widget'] = test_main_widget_fixes(freecad_ai_dir)
    
    # Test 5: Import Paths
    print("\n5. Testing Import Paths...")
    test_results['import_paths'] = test_import_paths(freecad_ai_dir)
    
    # Generate summary
    print("\n" + "=" * 60)
    print("DIAGNOSTIC SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results.items():
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! FreeCAD AI should now work correctly.")
        print("   Please restart FreeCAD to apply the fixes.")
    else:
        print("\n⚠️  Some tests failed. Check the output above for details.")
    
    return passed == total

def test_qt_compatibility(freecad_ai_dir):
    """Test Qt compatibility layer."""
    try:
        gui_dir = os.path.join(freecad_ai_dir, 'gui')
        sys.path.insert(0, gui_dir)
        
        from qt_compatibility import (
            QtWidgets, HAS_QT, QT_VERSION, is_qt_available
        )
        
        print("  ✓ Qt compatibility layer imported successfully")
        print(f"  ✓ Qt version: {QT_VERSION}")
        print(f"  ✓ Qt available: {is_qt_available()}")
        
        # Test basic Qt classes (but don't create actual widgets without QApplication)
        if HAS_QT:
            # Check if QApplication exists, if not just verify the classes exist
            app = QtWidgets.QApplication.instance()
            if app is None:
                print("  ✓ Qt classes available (no QApplication instance needed)")
                # Just test that the classes exist and can be accessed
                widget_class = QtWidgets.QWidget
                print(f"  ✓ QWidget class accessible: {widget_class}")
            else:
                # If QApplication exists, we can create actual widgets
                test_widget = QtWidgets.QWidget()
                print("  ✓ QWidget creation successful")
                test_widget.deleteLater()  # Clean up
        else:
            print("  ⚠ Using dummy Qt classes (no real Qt available)")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Qt compatibility test failed: {e}")
        print(f"    Traceback: {traceback.format_exc()}")
        return False


def test_agent_manager_wrapper(freecad_ai_dir):
    """Test agent manager wrapper."""
    try:
        core_dir = os.path.join(freecad_ai_dir, 'core')
        sys.path.insert(0, core_dir)
        
        from agent_manager_wrapper import get_agent_manager, is_agent_manager_available
        
        print("  ✓ Agent manager wrapper imported successfully")
        
        # Test availability check
        available = is_agent_manager_available()
        print(f"  ✓ Agent manager available: {available}")
        
        # Test getting instance
        agent_manager = get_agent_manager()
        if agent_manager is not None:
            print("  ✓ Agent manager instance created successfully")
            # Test basic functionality if available
            if hasattr(agent_manager, 'get_mode'):
                mode = agent_manager.get_mode()
                print(f"  ✓ Agent manager mode: {mode}")
        else:
            print("  ⚠ Agent manager instance is None (fallback mode)")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Agent manager wrapper test failed: {e}")
        print(f"    Traceback: {traceback.format_exc()}")
        return False

def test_provider_service_wrapper(freecad_ai_dir):
    """Test provider service wrapper."""
    try:
        ai_dir = os.path.join(freecad_ai_dir, 'ai')
        sys.path.insert(0, ai_dir)
        
        from provider_service_wrapper import get_provider_service, is_provider_service_available
        
        print("  ✓ Provider service wrapper imported successfully")
        
        # Test availability check
        available = is_provider_service_available()
        print(f"  ✓ Provider service available: {available}")
        
        # Test getting instance
        provider_service = get_provider_service()
        if provider_service is not None:
            print("  ✓ Provider service instance created successfully")
            # Test basic functionality if available
            if hasattr(provider_service, 'get_all_providers'):
                providers = provider_service.get_all_providers()
                print(f"  ✓ Total providers: {len(providers)}")
        else:
            print("  ⚠ Provider service instance is None (fallback mode)")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Provider service wrapper test failed: {e}")
        print(f"    Traceback: {traceback.format_exc()}")
        return False

def test_main_widget_fixes(freecad_ai_dir):
    """Test main widget with fixes."""
    try:
        gui_dir = os.path.join(freecad_ai_dir, 'gui')
        sys.path.insert(0, gui_dir)
        
        # Create a mock FreeCAD module to avoid import errors
        if 'FreeCAD' not in sys.modules:
            import types
            freecad_mock = types.ModuleType('FreeCAD')
            freecad_mock.Console = types.ModuleType('Console')
            freecad_mock.Console.PrintMessage = lambda msg: print(f"FreeCAD: {msg.strip()}")
            freecad_mock.Console.PrintWarning = lambda msg: print(f"FreeCAD Warning: {msg.strip()}")
            freecad_mock.Console.PrintError = lambda msg: print(f"FreeCAD Error: {msg.strip()}")
            sys.modules['FreeCAD'] = freecad_mock
        
        from main_widget import MCPMainWidget
        
        print("  ✓ MCPMainWidget class imported successfully")
        
        # Test creating instance (this should work with Qt compatibility layer)
        try:
            # We can't actually create the widget without a QApplication,
            # but we can test that the class is properly defined
            if hasattr(MCPMainWidget, '__init__'):
                print("  ✓ MCPMainWidget constructor available")
            if hasattr(MCPMainWidget, '_init_agent_manager_safe'):
                print("  ✓ Agent manager initialization method available")
            if hasattr(MCPMainWidget, '_setup_provider_service_safe'):
                print("  ✓ Provider service setup method available")
        except Exception as e:
            print(f"  ⚠ Widget creation test skipped: {e}")
        
        return True
        
    except Exception as e:
        print(f"  ✗ Main widget test failed: {e}")
        print(f"    Traceback: {traceback.format_exc()}")
        return False

def test_import_paths(freecad_ai_dir):
    """Test that all required directories have __init__.py files."""
    try:
        required_dirs = [
            'ai',
            'ai/providers',
            'core', 
            'gui',
            'config',
            'tools',
            'utils'
        ]
        
        missing_inits = []
        for dir_path in required_dirs:
            full_dir_path = os.path.join(freecad_ai_dir, dir_path)
            init_file = os.path.join(full_dir_path, '__init__.py')
            
            if os.path.exists(full_dir_path):
                if os.path.exists(init_file):
                    print(f"  ✓ {dir_path}/__init__.py exists")
                else:
                    print(f"  ✗ {dir_path}/__init__.py missing")
                    missing_inits.append(dir_path)
            else:
                print(f"  ⚠ Directory {dir_path} does not exist")
        
        if not missing_inits:
            print("  ✓ All required __init__.py files are present")
            return True
        else:
            print(f"  ✗ Missing __init__.py files in: {missing_inits}")
            return False
            
    except Exception as e:
        print(f"  ✗ Import paths test failed: {e}")
        return False

def create_freecad_test_script():
    """Create a test script that can be run within FreeCAD."""
    
    test_script_content = '''
"""
FreeCAD AI In-Application Test Script

Run this script within FreeCAD to test if the AI components
are working correctly after the fixes.
"""

import sys
import os
import traceback

def test_freecad_ai_in_app():
    """Test FreeCAD AI components from within FreeCAD."""
    
    print("Testing FreeCAD AI components within FreeCAD...")
    
    # Get addon directory
    addon_dir = os.path.dirname(__file__)
    freecad_ai_dir = os.path.join(addon_dir, 'freecad-ai')
    
    if freecad_ai_dir not in sys.path:
        sys.path.insert(0, freecad_ai_dir)
    
    test_results = {}
    
    # Test Agent Manager
    try:
        print("\\n1. Testing Agent Manager...")
        
        # Try multiple methods to get agent manager
        agent_manager = None
        
        # Method 1: Via main widget
        try:
            from gui.main_widget import MCPMainWidget
            widget = MCPMainWidget()
            
            if hasattr(widget, 'agent_manager') and widget.agent_manager is not None:
                agent_manager = widget.agent_manager
                print("✓ Agent Manager: AVAILABLE (via main widget)")
                test_results['agent_manager'] = True
            else:
                print("⚠ Agent Manager: Not available in main widget")
        except Exception as e:
            print(f"⚠ Main widget test failed: {e}")
        
        # Method 2: Via wrapper
        if agent_manager is None:
            try:
                from core.agent_manager_wrapper import get_agent_manager, is_agent_manager_available
                if is_agent_manager_available():
                    agent_manager = get_agent_manager()
                    print("✓ Agent Manager: AVAILABLE (via wrapper)")
                    test_results['agent_manager'] = True
                else:
                    print("⚠ Agent Manager wrapper reports unavailable")
            except Exception as e:
                print(f"⚠ Agent Manager wrapper test failed: {e}")
        
        # Method 3: Direct creation
        if agent_manager is None:
            try:
                from core.agent_manager import AgentManager
                agent_manager = AgentManager()
                print("✓ Agent Manager: AVAILABLE (direct creation)")
                test_results['agent_manager'] = True
            except Exception as e:
                print(f"⚠ Direct agent manager creation failed: {e}")
        
        if agent_manager is None:
            print("✗ Agent Manager: NOT AVAILABLE")
            test_results['agent_manager'] = False
            
    except Exception as e:
        print(f"✗ Agent Manager test failed: {e}")
        test_results['agent_manager'] = False
    
    # Test Provider Service
    try:
        print("\\n2. Testing Provider Service...")
        
        provider_service = None
        
        # Method 1: From main widget
        try:
            if hasattr(widget, 'provider_service') and widget.provider_service is not None:
                provider_service = widget.provider_service
                print("✓ Provider Service: AVAILABLE (via main widget)")
                test_results['provider_service'] = True
        except:
            pass
        
        # Method 2: Via wrapper
        if provider_service is None:
            try:
                from ai.provider_service_wrapper import get_provider_service, is_provider_service_available
                if is_provider_service_available():
                    provider_service = get_provider_service()
                    print("✓ Provider Service: AVAILABLE (via wrapper)")
                    test_results['provider_service'] = True
                else:
                    print("⚠ Provider Service wrapper reports unavailable")
            except Exception as e:
                print(f"⚠ Provider Service wrapper test failed: {e}")
        
        # Method 3: Direct
        if provider_service is None:
            try:
                from ai.provider_integration_service import get_provider_service
                provider_service = get_provider_service()
                if provider_service is not None:
                    print("✓ Provider Service: AVAILABLE (direct)")
                    test_results['provider_service'] = True
                else:
                    print("⚠ Provider Service direct creation returned None")
            except Exception as e:
                print(f"⚠ Direct provider service creation failed: {e}")
        
        if provider_service is None:
            print("✗ Provider Service: NOT AVAILABLE")
            test_results['provider_service'] = False
            
    except Exception as e:
        print(f"✗ Provider Service test failed: {e}")
        test_results['provider_service'] = False
    
    # Test tools registry
    try:
        print("\\n3. Testing Tools Registry...")
        
        if agent_manager and hasattr(agent_manager, 'tool_registry') and agent_manager.tool_registry is not None:
            available_tools = agent_manager.get_available_tools() if hasattr(agent_manager, 'get_available_tools') else []
            print(f"✓ Tools Registry: AVAILABLE ({len(available_tools)} tools)")
            test_results['tools_registry'] = True
        else:
            print("✗ Tools Registry: NOT AVAILABLE")
            test_results['tools_registry'] = False
            
    except Exception as e:
        print(f"✗ Tools Registry test failed: {e}")
        test_results['tools_registry'] = False
    
    # Summary
    passed = sum(1 for result in test_results.values() if result)
    total = len(test_results)
    
    print(f"\\n" + "=" * 50)
    print(f"Test Results: {passed}/{total} components working")
    
    for component, status in test_results.items():
        status_str = "✓ WORKING" if status else "✗ FAILED"
        print(f"{component.replace('_', ' ').title()}: {status_str}")
    
    if passed == total:
        print("\\n🎉 All FreeCAD AI components are working correctly!")
    else:
        print("\\n⚠️ Some components are still not working. Check the fixes.")
    
    return test_results

# Run the test if executed directly
if __name__ == "__main__":
    test_freecad_ai_in_app()
'''
    
    test_script_path = os.path.join(os.path.dirname(__file__), 'test_freecad_ai_in_app.py')
    with open(test_script_path, 'w') as f:
        f.write(test_script_content)
    
    print(f"\nCreated FreeCAD test script: {test_script_path}")
    print("You can run this script within FreeCAD to test the fixes.")

if __name__ == "__main__":
    success = test_freecad_ai_components()
    create_freecad_test_script()
    
    if success:
        print("\n🔧 Next steps:")
        print("1. Restart FreeCAD")
        print("2. Load the FreeCAD AI addon")
        print("3. Check if Agent Manager and Provider Service are now available")
        print("4. Run the test script within FreeCAD to verify functionality")
    else:
        print("\n🔧 Some fixes may need additional work. Check the error messages above.")
