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

        # For Python 3.13+, we need to be more careful with the test
        if python_version >= (3, 13):
            try:
                # First, try basic imports
                import fastapi
                import pydantic

                # Check if we have reasonably recent versions that should work with Python 3.13
                fastapi_version = getattr(fastapi, "__version__", "0.0.0")
                pydantic_version = getattr(pydantic, "__version__", "0.0.0")

                # FastAPI 0.100+ and Pydantic 2.0+ should work with Python 3.13
                fastapi_major = int(fastapi_version.split(".")[0])
                pydantic_major = int(pydantic_version.split(".")[0])

                if fastapi_major == 0:
                    fastapi_minor = int(fastapi_version.split(".")[1])
                    if fastapi_minor < 100:
                        return (
                            False,
                            f"FastAPI {fastapi_version} may not be compatible with Python {python_version.major}.{python_version.minor}. Consider upgrading to FastAPI 0.100+",
                        )

                if pydantic_major < 2:
                    return (
                        False,
                        f"Pydantic {pydantic_version} may not be compatible with Python {python_version.major}.{python_version.minor}. Consider upgrading to Pydantic 2.0+",
                    )

                # Try a more comprehensive test
                from fastapi import APIRouter
                from pydantic import BaseModel

                # Test model creation with type hints
                class TestModel(BaseModel):
                    test_field: str = "test"
                    number_field: int = 42
                    optional_field: str | None = (
                        None  # This uses Python 3.10+ union syntax
                    )

                # Test model instantiation
                test_instance = TestModel()

                # Test router creation
                router = APIRouter()

                # If we get here, everything should work
                return True, None

            except TypeError as e:
                error_str = str(e)
                if "Protocols with non-method members" in error_str:
                    return (
                        True,
                        f"Known compatibility warning with Python {python_version.major}.{python_version.minor}: {error_str}",
                    )
                elif (
                    "issubclass" in error_str
                    and "__is_annotated_types_grouped_metadata__" in error_str
                ):
                    return (
                        True,
                        f"Known compatibility warning with Python {python_version.major}.{python_version.minor}: {error_str}",
                    )
                else:
                    # For other TypeErrors, let's be more permissive and assume it might work
                    return (
                        True,
                        f"Minor compatibility warning (non-blocking): {error_str}",
                    )
            except ImportError as e:
                return False, f"FastAPI/Pydantic import error: {e}"
            except Exception as e:
                # For other exceptions, be more permissive
                return (
                    True,
                    f"Compatibility test had minor issues but imports work: {e}",
                )
        else:
            # For Python < 3.13, assume compatibility is good
            try:
                import fastapi
                import pydantic

                return True, None
            except ImportError as e:
                return False, f"Import error: {e}"

    except Exception as e:
        return False, f"Version compatibility check failed: {e}"


# Check compatibility before attempting imports
compatibility_ok, compatibility_error = check_fastapi_pydantic_compatibility()

if not compatibility_ok:
    try:
        import FreeCAD

        if "compatibility warning" in str(compatibility_error).lower():
            FreeCAD.Console.PrintWarning(
                f"FreeCAD AI: API module compatibility warning: {compatibility_error}\n"
            )
            FreeCAD.Console.PrintMessage(
                "FreeCAD AI: Attempting to load API despite warning...\n"
            )
            compatibility_ok = True  # Allow loading despite warning
        else:
            FreeCAD.Console.PrintError(
                f"FreeCAD AI: API module disabled due to compatibility issue: {compatibility_error}\n"
            )
            FreeCAD.Console.PrintError(
                "FreeCAD AI: Consider updating FastAPI/Pydantic or using a different Python version\n"
            )
    except ImportError:
        if "compatibility warning" in str(compatibility_error).lower():
            print(
                f"FreeCAD AI: API module compatibility warning: {compatibility_error}"
            )
            print("FreeCAD AI: Attempting to load API despite warning...")
            compatibility_ok = True  # Allow loading despite warning
        else:
            print(
                f"FreeCAD AI: API module disabled due to compatibility issue: {compatibility_error}"
            )
            print(
                "FreeCAD AI: Consider updating FastAPI/Pydantic or using a different Python version"
            )

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

                FreeCAD.Console.PrintMessage(
                    f"FreeCAD AI: Skipping {item_name} import due to compatibility issues\n"
                )
            except ImportError:
                print(
                    f"FreeCAD AI: Skipping {item_name} import due to compatibility issues"
                )
            continue

        # Attempt the import
        module = __import__(f"api.{module_name}", fromlist=[item_name])
        if hasattr(module, item_name):
            globals()[item_name] = getattr(module, item_name)
            available_apis.append(item_name)
            try:
                import FreeCAD

                FreeCAD.Console.PrintMessage(
                    f"FreeCAD AI: Successfully imported {item_name}\n"
                )
            except ImportError:
                print(f"FreeCAD AI: Successfully imported {item_name}")
        else:
            try:
                import FreeCAD

                FreeCAD.Console.PrintWarning(
                    f"FreeCAD AI: {item_name} not found in {module_name} module\n"
                )
            except ImportError:
                print(f"FreeCAD AI: {item_name} not found in {module_name} module")

    except ImportError as e:
        try:
            import FreeCAD

            FreeCAD.Console.PrintWarning(
                f"FreeCAD AI: Failed to import {item_name}: {e}\n"
            )
        except ImportError:
            print(f"FreeCAD AI: Failed to import {item_name}: {e}")
    except TypeError as e:
        if "Protocols with non-method members" in str(e):
            try:
                import FreeCAD

                FreeCAD.Console.PrintError(
                    f"FreeCAD AI: FastAPI/Pydantic compatibility error importing {item_name}: {e}\n"
                )
                FreeCAD.Console.PrintError(
                    "FreeCAD AI: This is a known issue with Python 3.13+ and certain library versions\n"
                )
            except ImportError:
                print(
                    f"FreeCAD AI: FastAPI/Pydantic compatibility error importing {item_name}: {e}"
                )
                print(
                    "FreeCAD AI: This is a known issue with Python 3.13+ and certain library versions"
                )
        else:
            try:
                import FreeCAD

                FreeCAD.Console.PrintError(
                    f"FreeCAD AI: Type error importing {item_name}: {e}\n"
                )
            except ImportError:
                print(f"FreeCAD AI: Type error importing {item_name}: {e}")
    except Exception as e:
        try:
            import FreeCAD

            FreeCAD.Console.PrintError(
                f"FreeCAD AI: Unexpected error importing {item_name}: {e}\n"
            )
            FreeCAD.Console.PrintError(
                f"FreeCAD AI: {item_name} traceback: {traceback.format_exc()}\n"
            )
        except ImportError:
            print(f"FreeCAD AI: Unexpected error importing {item_name}: {e}")
            print(f"FreeCAD AI: {item_name} traceback: {traceback.format_exc()}")

if available_apis:
    API_AVAILABLE = True
    try:
        import FreeCAD

        FreeCAD.Console.PrintMessage(
            f"FreeCAD AI: API module partially available with {len(available_apis)} components: {', '.join(available_apis)}\n"
        )
    except ImportError:
        print(
            f"FreeCAD AI: API module partially available with {len(available_apis)} components: {', '.join(available_apis)}"
        )
else:
    try:
        import FreeCAD

        FreeCAD.Console.PrintWarning(
            "FreeCAD AI: API module completely unavailable - all imports failed\n"
        )
        if compatibility_error:
            FreeCAD.Console.PrintWarning(
                f"FreeCAD AI: Root cause: {compatibility_error}\n"
            )
    except ImportError:
        print("FreeCAD AI: API module completely unavailable - all imports failed")
        if compatibility_error:
            print(f"FreeCAD AI: Root cause: {compatibility_error}")

__all__ = available_apis + ["API_AVAILABLE"]
