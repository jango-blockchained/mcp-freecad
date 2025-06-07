"""
API for FreeCAD AI addon.

This module contains API handlers for tools, resources, and events.
"""

import sys
import traceback

# Import API handlers with comprehensive version compatibility handling
API_AVAILABLE = False
available_apis = []

# Version compatibility check for FastAPI/Pydantic
def check_fastapi_pydantic_compatibility():
    """Check if FastAPI and Pydantic versions are compatible with current Python version."""
    try:
        python_version = sys.version_info
        
        # Known compatibility issues with Python 3.13+ and certain FastAPI/Pydantic combinations
        if python_version >= (3, 13):
            try:
                # Try a minimal FastAPI import to test compatibility
                import fastapi
                from pydantic import BaseModel
                
                # Test if we can create a simple model (this often fails with version conflicts)
                class TestModel(BaseModel):
                    test_field: str = "test"
                
                # If we get here, compatibility is likely good
                return True, None
                
            except TypeError as e:
                if "Protocols with non-method members" in str(e):
                    return False, f"FastAPI/Pydantic compatibility issue with Python {python_version.major}.{python_version.minor}: {e}"
                else:
                    return False, f"FastAPI/Pydantic compatibility test failed: {e}"
            except Exception as e:
                return False, f"FastAPI/Pydantic compatibility test failed: {e}"
        else:
            # For Python < 3.13, assume compatibility is likely good
            return True, None
            
    except Exception as e:
        return False, f"Version compatibility check failed: {e}"

# Check compatibility before attempting imports
compatibility_ok, compatibility_error = check_fastapi_pydantic_compatibility()

if not compatibility_ok:
    try:
        import FreeCAD
        FreeCAD.Console.PrintWarning(f"FreeCAD AI: API module disabled due to compatibility issue: {compatibility_error}\n")
        FreeCAD.Console.PrintWarning("FreeCAD AI: Consider updating FastAPI/Pydantic or using a different Python version\n")
    except ImportError:
        print(f"FreeCAD AI: API module disabled due to compatibility issue: {compatibility_error}")
        print("FreeCAD AI: Consider updating FastAPI/Pydantic or using a different Python version")

# Try importing each API individually with enhanced error handling
apis_to_import = [
    ("tools", "create_tool_router"),
    ("resources", "create_resource_router"),
    ("events", "create_event_router"),
]

for module_name, item_name in apis_to_import:
    try:
        # Skip import if we know there are compatibility issues
        if not compatibility_ok:
            try:
                import FreeCAD
                FreeCAD.Console.PrintMessage(f"FreeCAD AI: Skipping {item_name} import due to compatibility issues\n")
            except ImportError:
                print(f"FreeCAD AI: Skipping {item_name} import due to compatibility issues")
            continue
            
        # Attempt the import
        module = __import__(f"api.{module_name}", fromlist=[item_name])
        if hasattr(module, item_name):
            globals()[item_name] = getattr(module, item_name)
            available_apis.append(item_name)
            try:
                import FreeCAD
                FreeCAD.Console.PrintMessage(f"FreeCAD AI: Successfully imported {item_name}\n")
            except ImportError:
                print(f"FreeCAD AI: Successfully imported {item_name}")
        else:
            try:
                import FreeCAD
                FreeCAD.Console.PrintWarning(f"FreeCAD AI: {item_name} not found in {module_name} module\n")
            except ImportError:
                print(f"FreeCAD AI: {item_name} not found in {module_name} module")
                
    except ImportError as e:
        try:
            import FreeCAD
            FreeCAD.Console.PrintWarning(f"FreeCAD AI: Failed to import {item_name}: {e}\n")
        except ImportError:
            print(f"FreeCAD AI: Failed to import {item_name}: {e}")
    except TypeError as e:
        if "Protocols with non-method members" in str(e):
            try:
                import FreeCAD
                FreeCAD.Console.PrintError(f"FreeCAD AI: FastAPI/Pydantic compatibility error importing {item_name}: {e}\n")
                FreeCAD.Console.PrintError("FreeCAD AI: This is a known issue with Python 3.13+ and certain library versions\n")
            except ImportError:
                print(f"FreeCAD AI: FastAPI/Pydantic compatibility error importing {item_name}: {e}")
                print("FreeCAD AI: This is a known issue with Python 3.13+ and certain library versions")
        else:
            try:
                import FreeCAD
                FreeCAD.Console.PrintError(f"FreeCAD AI: Type error importing {item_name}: {e}\n")
            except ImportError:
                print(f"FreeCAD AI: Type error importing {item_name}: {e}")
    except Exception as e:
        try:
            import FreeCAD
            FreeCAD.Console.PrintError(f"FreeCAD AI: Unexpected error importing {item_name}: {e}\n")
            FreeCAD.Console.PrintError(f"FreeCAD AI: {item_name} traceback: {traceback.format_exc()}\n")
        except ImportError:
            print(f"FreeCAD AI: Unexpected error importing {item_name}: {e}")
            print(f"FreeCAD AI: {item_name} traceback: {traceback.format_exc()}")

if available_apis:
    API_AVAILABLE = True
    try:
        import FreeCAD
        FreeCAD.Console.PrintMessage(f"FreeCAD AI: API module partially available with {len(available_apis)} components: {', '.join(available_apis)}\n")
    except ImportError:
        print(f"FreeCAD AI: API module partially available with {len(available_apis)} components: {', '.join(available_apis)}")
else:
    try:
        import FreeCAD
        FreeCAD.Console.PrintWarning("FreeCAD AI: API module completely unavailable - all imports failed\n")
        if compatibility_error:
            FreeCAD.Console.PrintWarning(f"FreeCAD AI: Root cause: {compatibility_error}\n")
    except ImportError:
        print("FreeCAD AI: API module completely unavailable - all imports failed")
        if compatibility_error:
            print(f"FreeCAD AI: Root cause: {compatibility_error}")

__all__ = available_apis + ["API_AVAILABLE"]
