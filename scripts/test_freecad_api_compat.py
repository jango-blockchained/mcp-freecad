#!/usr/bin/env python3
"""
Test FreeCAD AI API compatibility within the addon context
"""

import sys
import os

# Add freecad-ai to path
sys.path.insert(0, '/home/jango/Git/mcp-freecad/freecad-ai')

def test_api_compatibility():
    """Test the API compatibility check function"""
    try:
        from api import check_fastapi_pydantic_compatibility
        
        print("Testing API compatibility check...")
        result, error = check_fastapi_pydantic_compatibility()
        
        print(f"Compatibility result: {result}")
        if error:
            print(f"Error message: {error}")
        else:
            print("No error detected")
            
        return result
        
    except Exception as e:
        print(f"Error testing API compatibility: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_direct_api_import():
    """Test importing API modules directly"""
    try:
        print("\nTesting direct API imports...")
        from api.tools import FASTAPI_AVAILABLE, FASTAPI_IMPORT_ERROR
        
        print(f"FastAPI available in tools: {FASTAPI_AVAILABLE}")
        if FASTAPI_IMPORT_ERROR:
            print(f"FastAPI import error: {FASTAPI_IMPORT_ERROR}")
        
        return FASTAPI_AVAILABLE
        
    except Exception as e:
        print(f"Error testing direct API import: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("=== FreeCAD AI API Compatibility Test ===")
    
    compat_result = test_api_compatibility()
    direct_result = test_direct_api_import()
    
    print(f"\nSummary:")
    print(f"Compatibility check: {'PASS' if compat_result else 'FAIL'}")
    print(f"Direct import test: {'PASS' if direct_result else 'FAIL'}")
    
    if compat_result and direct_result:
        print("✅ API should be working correctly!")
    else:
        print("❌ API has compatibility issues")
