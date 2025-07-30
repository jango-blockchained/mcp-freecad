#!/usr/bin/env python3
"""
Test script to check MCP dependency within FreeCAD environment
"""

def test_mcp_dependency():
    print("Testing MCP dependency in FreeCAD environment...")
    
    import sys
    print(f"Python executable: {sys.executable}")
    print(f"Python version: {sys.version}")
    print(f"Python path (first 3): {sys.path[:3]}")
    
    # Test import using the same method as dependency manager
    import importlib.util
    
    print("\n=== Testing MCP Import ===")
    try:
        spec = importlib.util.find_spec('mcp')
        if spec is not None:
            print(f"✅ MCP spec found: {spec.origin}")
            
            # Try to actually import it
            try:
                import mcp
                print("✅ MCP imported successfully")
                print(f"MCP module file: {getattr(mcp, '__file__', 'No __file__')}")
                print(f"MCP contents (first 10): {[x for x in dir(mcp) if not x.startswith('_')][:10]}")
                return True
            except Exception as e:
                print(f"❌ MCP import failed: {e}")
                return False
        else:
            print("❌ MCP spec not found")
            return False
    except Exception as e:
        print(f"❌ Error checking MCP: {e}")
        return False

def test_other_dependencies():
    print("\n=== Testing Other Dependencies ===")
    deps_to_test = ['aiohttp', 'requests', 'multidict', 'yarl', 'aiosignal']
    
    for dep in deps_to_test:
        try:
            __import__(dep)
            print(f"✅ {dep}: Available")
        except ImportError:
            print(f"❌ {dep}: Missing")
        except Exception as e:
            print(f"⚠️ {dep}: Error - {e}")

def test_dependency_manager():
    print("\n=== Testing Dependency Manager ===")
    try:
        import sys
        import os
        
        # Add the freecad-ai directory to path
        addon_path = os.path.join(os.path.dirname(__file__), 'freecad-ai')
        if addon_path not in sys.path:
            sys.path.insert(0, addon_path)
        
        from utils.dependency_manager import check_dependencies
        
        deps = check_dependencies()
        print("Dependency check results:")
        for dep, available in deps.items():
            status = '✅' if available else '❌'
            print(f"  {status} {dep}: {'Available' if available else 'Missing'}")
            
    except Exception as e:
        print(f"❌ Error testing dependency manager: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    print("="*60)
    print("MCP DEPENDENCY TEST")
    print("="*60)
    
    test_mcp_dependency()
    test_other_dependencies()
    test_dependency_manager()
    
    print("\n" + "="*60)
    print("Test completed")
