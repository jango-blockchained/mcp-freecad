import logging
from typing import Any, Dict, Optional

try:
    from fastapi import APIRouter, HTTPException

    FASTAPI_AVAILABLE = True
except ImportError:
    # FastAPI not available, create minimal stubs
    FASTAPI_AVAILABLE = False
    APIRouter = None
    HTTPException = Exception

try:
    from ..core.server import MCPServer
except ImportError:
    # Fallback for when module is loaded by FreeCAD
    import os
    import sys

    addon_dir = os.path.dirname(os.path.dirname(__file__))
    if addon_dir not in sys.path:
        sys.path.insert(0, addon_dir)
    from core.server import MCPServer

logger = logging.getLogger(__name__)


def create_resource_router(server: MCPServer):
    """Create a router for resource endpoints."""
    if not FASTAPI_AVAILABLE:
        logger.warning("FastAPI not available, resource router disabled")
        return None

    router = APIRouter(
        prefix="/resources",
        tags=["resources"],
        responses={404: {"description": "Resource not found"}},
    )

    @router.get("/{resource_id}")
    async def get_resource(
        resource_id: str,
        uri: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
    ):
        """Get a resource from the server."""
        logger.info(f"Resource request: {resource_id}, URI: {uri}")

        if resource_id not in server.resources:
            raise HTTPException(
                status_code=404, detail=f"Resource provider not found: {resource_id}"
            )

        resource_provider = server.resources[resource_id]

        try:
            # If URI is not provided, use a default URI based on resource ID
            if not uri:
                if resource_id == "cad_model":
                    uri = "cad://model/current"
                elif resource_id == "measurements":
                    uri = "cad://measurements"
                elif resource_id == "materials":
                    uri = "cad://materials"
                elif resource_id == "constraints":
                    uri = "cad://constraints"
                else:
                    uri = f"cad://{resource_id}"

            # Get the resource
            return await resource_provider.get_resource(uri, params)
        except Exception as e:
            logger.error(f"Error getting resource: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Add endpoint for measurements
    @router.get("/measurements/{measurement_type}")
    async def get_measurement(
        measurement_type: str,
        object_name: Optional[str] = None,
        point1: Optional[str] = None,
        point2: Optional[str] = None,
    ):
        """Get a measurement from the server."""
        logger.info(f"Measurement request: {measurement_type}, Object: {object_name}")

        if "measurements" not in server.resources:
            raise HTTPException(
                status_code=404, detail="Measurement provider not found"
            )

        resource_provider = server.resources["measurements"]

        try:
            # Construct a URI based on measurement type and parameters
            uri = f"cad://measurements/{measurement_type}"

            # Add object to URI path if provided
            if object_name:
                uri += f"/{object_name}"

            # Build params based on provided values
            params = {}
            if point1 and point2:
                # Parse points from string format
                try:
                    p1 = [float(x) for x in point1.split(",")]
                    p2 = [float(x) for x in point2.split(",")]
                    params["points"] = [p1, p2]
                except ValueError:
                    raise HTTPException(
                        status_code=400, detail="Invalid point format. Expected: x,y,z"
                    )

            # Get the resource
            return await resource_provider.get_resource(uri, params)
        except Exception as e:
            logger.error(f"Error getting measurement: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Add endpoint for materials
    @router.get("/materials/{resource_type}")
    async def get_material(
        resource_type: str,
        object_name: Optional[str] = None,
        material_name: Optional[str] = None,
    ):
        """Get material information from the server."""
        logger.info(
            f"Material request: {resource_type}, Object: {object_name}, Material: {material_name}"
        )

        if "materials" not in server.resources:
            raise HTTPException(status_code=404, detail="Material provider not found")

        resource_provider = server.resources["materials"]

        try:
            # Construct a URI based on resource type and parameters
            uri = f"cad://materials/{resource_type}"

            # Add object or material name to URI path if provided
            if resource_type == "object" and object_name:
                uri += f"/{object_name}"
            elif resource_type == "info" and material_name:
                uri += f"/{material_name}"

            # Get the resource
            return await resource_provider.get_resource(uri)
        except Exception as e:
            logger.error(f"Error getting material information: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    # Add endpoint for constraints
    @router.get("/constraints/{resource_type}")
    async def get_constraint(resource_type: str, object_name: Optional[str] = None):
        """Get constraint information from the server."""
        logger.info(f"Constraint request: {resource_type}, Object: {object_name}")

        if "constraints" not in server.resources:
            raise HTTPException(status_code=404, detail="Constraint provider not found")

        resource_provider = server.resources["constraints"]

        try:
            # Construct a URI based on resource type and parameters
            uri = f"cad://constraints/{resource_type}"

            # Add object name to URI path if provided
            if object_name:
                uri += f"/{object_name}"

            # Get the resource
            return await resource_provider.get_resource(uri)
        except Exception as e:
            logger.error(f"Error getting constraint information: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    return router
