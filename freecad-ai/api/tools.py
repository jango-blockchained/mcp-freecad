import logging
import sys
import traceback
from typing import Any, Dict

# Enhanced FastAPI/Pydantic import with version compatibility handling
FASTAPI_AVAILABLE = False
FASTAPI_IMPORT_ERROR = None

def test_fastapi_compatibility():
    """Test if FastAPI and Pydantic can be imported and used together."""
    try:
        # Import FastAPI components
        from fastapi import APIRouter, HTTPException
        from pydantic import BaseModel

        # Test basic functionality that often fails with version conflicts
        class TestModel(BaseModel):
            test_field: str = "test"

        # Test router creation
        test_router = APIRouter()

        # If we get here, imports and basic functionality work
        return True, None, (APIRouter, HTTPException, BaseModel)

    except TypeError as e:
        if "Protocols with non-method members" in str(e):
            return False, f"FastAPI/Pydantic compatibility issue with Python {sys.version_info.major}.{sys.version_info.minor}: {e}", None
        else:
            return False, f"FastAPI/Pydantic type error: {e}", None
    except ImportError as e:
        return False, f"FastAPI/Pydantic import error: {e}", None
    except Exception as e:
        return False, f"FastAPI/Pydantic unexpected error: {e}", None

# Test compatibility and import
compatibility_ok, error_msg, imports = test_fastapi_compatibility()

if compatibility_ok:
    APIRouter, HTTPException, BaseModel = imports
    FASTAPI_AVAILABLE = True
    try:
        import FreeCAD
        FreeCAD.Console.PrintMessage("FreeCAD AI: FastAPI/Pydantic imported successfully for tools module\n")
    except ImportError:
        pass
else:
    FASTAPI_AVAILABLE = False
    FASTAPI_IMPORT_ERROR = error_msg

    # Create minimal stubs to prevent crashes
    APIRouter = None
    HTTPException = Exception
    BaseModel = object

    try:
        import FreeCAD
        FreeCAD.Console.PrintWarning(f"FreeCAD AI: FastAPI not available for tools module: {error_msg}\n")
        FreeCAD.Console.PrintWarning("FreeCAD AI: Tool router will be disabled\n")
    except ImportError:
        print(f"FreeCAD AI: FastAPI not available for tools module: {error_msg}")
        print("FreeCAD AI: Tool router will be disabled")

try:
    from ..core.server import MCPServer
except ImportError:
    # Fallback for when module is loaded by FreeCAD
    import os
    import sys

    addon_dir = os.path.dirname(os.path.dirname(__file__))
    if addon_dir not in sys.path:
        sys.path.insert(0, addon_dir)
    try:
        from core.server import MCPServer
    except ImportError as e:
        try:
            import FreeCAD
            FreeCAD.Console.PrintWarning(f"FreeCAD AI: Could not import MCPServer: {e}\n")
        except ImportError:
            print(f"FreeCAD AI: Could not import MCPServer: {e}")
        # Create a minimal fallback
        class MCPServer:
            def __init__(self):
                self.tools = {}

logger = logging.getLogger(__name__)

# Enhanced model definitions with compatibility checks
if FASTAPI_AVAILABLE and BaseModel != object:
    class ToolRequest(BaseModel):
        parameters: Dict[str, Any] = {}

    class ToolResponse(BaseModel):
        tool_id: str
        status: str
        result: Dict[str, Any]
else:
    # Fallback classes when Pydantic is not available
    class ToolRequest:
        def __init__(self, parameters: Dict[str, Any] = None):
            self.parameters = parameters or {}

    class ToolResponse:
        def __init__(self, tool_id: str, status: str, result: Dict[str, Any]):
            self.tool_id = tool_id
            self.status = status
            self.result = result

def create_tool_router(server: MCPServer):
    """Create a router for tool endpoints with enhanced error handling."""
    if not FASTAPI_AVAILABLE:
        try:
            import FreeCAD
            FreeCAD.Console.PrintWarning("FreeCAD AI: FastAPI not available, tool router disabled\n")
            if FASTAPI_IMPORT_ERROR:
                FreeCAD.Console.PrintWarning(f"FreeCAD AI: Reason: {FASTAPI_IMPORT_ERROR}\n")
        except ImportError:
            print("FreeCAD AI: FastAPI not available, tool router disabled")
            if FASTAPI_IMPORT_ERROR:
                print(f"FreeCAD AI: Reason: {FASTAPI_IMPORT_ERROR}")
        return None

    if not server:
        try:
            import FreeCAD
            FreeCAD.Console.PrintWarning("FreeCAD AI: No server provided, tool router disabled\n")
        except ImportError:
            print("FreeCAD AI: No server provided, tool router disabled")
        return None

    try:
        router = APIRouter(
            prefix="/tools",
            tags=["tools"],
            responses={404: {"description": "Tool not found"}},
        )

        @router.post("/primitives.{tool_id}")
        async def execute_primitive_tool(tool_id: str, tool_request: Dict[str, Any]):
            """Execute a primitive creation tool."""
            logger.info(f"Tool request: primitives.{tool_id}")

            if "primitives" not in server.tools:
                raise HTTPException(
                    status_code=404, detail="Primitive tool provider not found"
                )

            tool_provider = server.tools["primitives"]

            try:
                return await tool_provider.execute_tool(
                    tool_id, tool_request.get("parameters", {})
                )
            except Exception as e:
                logger.error(f"Error executing primitive tool: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @router.post("/model_manipulation.{tool_id}")
        async def execute_model_manipulation_tool(
            tool_id: str, tool_request: Dict[str, Any]
        ):
            """Execute a model manipulation tool."""
            logger.info(f"Tool request: model_manipulation.{tool_id}")

            if "model_manipulation" not in server.tools:
                raise HTTPException(
                    status_code=404, detail="Model manipulation tool provider not found"
                )

            tool_provider = server.tools["model_manipulation"]

            try:
                return await tool_provider.execute_tool(
                    tool_id, tool_request.get("parameters", {})
                )
            except Exception as e:
                logger.error(f"Error executing model manipulation tool: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        @router.post("/measurement.{tool_id}")
        async def execute_measurement_tool(tool_id: str, tool_request: Dict[str, Any]):
            """Execute a measurement tool."""
            logger.info(f"Tool request: measurement.{tool_id}")

            if "measurement" not in server.tools:
                raise HTTPException(
                    status_code=404, detail="Measurement tool provider not found"
                )

            tool_provider = server.tools["measurement"]

            try:
                return await tool_provider.execute_tool(
                    tool_id, tool_request.get("parameters", {})
                )
            except Exception as e:
                logger.error(f"Error executing measurement tool: {e}")
                raise HTTPException(status_code=500, detail=str(e))

        try:
            import FreeCAD
            FreeCAD.Console.PrintMessage("FreeCAD AI: Tool router created successfully\n")
        except ImportError:
            pass

        return router

    except Exception as e:
        try:
            import FreeCAD
            FreeCAD.Console.PrintError(f"FreeCAD AI: Failed to create tool router: {e}\n")
            FreeCAD.Console.PrintError(f"FreeCAD AI: Tool router traceback: {traceback.format_exc()}\n")
        except ImportError:
            print(f"FreeCAD AI: Failed to create tool router: {e}")
            print(f"FreeCAD AI: Tool router traceback: {traceback.format_exc()}")
        return None
