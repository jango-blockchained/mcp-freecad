import logging
from typing import Any, Dict, List, Optional

from ..base import ToolProvider, ToolResult, ToolSchema

logger = logging.getLogger(__name__)


class AssemblyToolProvider(ToolProvider):
    """Tool provider for assembly operations in FreeCAD."""

    def __init__(self, freecad_app=None):
        """Initialize the assembly tool provider."""
        self.app = freecad_app
        if self.app is None:
            try:
                import FreeCAD
                self.app = FreeCAD
                logger.info("Connected to FreeCAD")
            except ImportError:
                logger.warning("Could not import FreeCAD. Make sure it's installed and in your Python path.")
                self.app = None

    @property
    def tool_schema(self) -> ToolSchema:
        return ToolSchema(
            name="assembly",
            description="Tools for creating and managing assemblies in FreeCAD",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create_assembly", "add_part", "create_constraint", "list_parts", "move_part"],
                        "description": "The assembly action to perform"
                    },
                    "assembly_name": {
                        "type": "string",
                        "description": "Name of the assembly"
                    },
                    "part_name": {
                        "type": "string",
                        "description": "Name of the part to add or manipulate"
                    },
                    "constraint_type": {
                        "type": "string",
                        "enum": ["coincident", "distance", "angle", "parallel", "perpendicular"],
                        "description": "Type of constraint to create"
                    },
                    "position": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Position coordinates [x, y, z]"
                    },
                    "rotation": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Rotation angles [rx, ry, rz] in degrees"
                    }
                },
                "required": ["action"]
            },
            returns={
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "result": {"type": "object"},
                    "error": {"type": "string"}
                }
            },
            examples=[
                {
                    "action": "create_assembly",
                    "assembly_name": "MyAssembly"
                },
                {
                    "action": "add_part",
                    "assembly_name": "MyAssembly",
                    "part_name": "Part1",
                    "position": [0, 0, 0]
                }
            ]
        )

    async def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> ToolResult:
        """Execute an assembly tool."""
        if self.app is None:
            return self.format_result("error", error="FreeCAD not available")

        action = params.get("action")

        try:
            if action == "create_assembly":
                return await self._create_assembly(params)
            elif action == "add_part":
                return await self._add_part(params)
            elif action == "create_constraint":
                return await self._create_constraint(params)
            elif action == "list_parts":
                return await self._list_parts(params)
            elif action == "move_part":
                return await self._move_part(params)
            else:
                return self.format_result("error", error=f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Assembly tool failed: {e}")
            return self.format_result("error", error=str(e))

    async def _create_assembly(self, params: Dict[str, Any]) -> ToolResult:
        """Create a new assembly."""
        try:
            assembly_name = params.get("assembly_name", "Assembly")
            doc = self._get_active_document()

            # Try to use Assembly4 workbench if available
            try:
                import Assembly4
                assembly = doc.addObject("App::Part", assembly_name)
                assembly.Label = assembly_name

                # Add Assembly4 properties
                assembly.addProperty("App::PropertyString", "AssemblyType", "Assembly")
                assembly.AssemblyType = "Assembly4"

            except ImportError:
                # Fallback to basic Part container
                assembly = doc.addObject("App::Part", assembly_name)
                assembly.Label = assembly_name

            doc.recompute()

            return self.format_result("success", result={
                "assembly_name": assembly.Name,
                "label": assembly.Label,
                "message": f"Assembly '{assembly_name}' created successfully"
            })

        except Exception as e:
            return self.format_result("error", error=f"Failed to create assembly: {e}")

    async def _add_part(self, params: Dict[str, Any]) -> ToolResult:
        """Add a part to an assembly."""
        try:
            assembly_name = params.get("assembly_name")
            part_name = params.get("part_name")
            position = params.get("position", [0, 0, 0])
            rotation = params.get("rotation", [0, 0, 0])

            doc = self._get_active_document()

            # Get assembly
            assembly = doc.getObject(assembly_name)
            if not assembly:
                return self.format_result("error", error=f"Assembly '{assembly_name}' not found")

            # Get part
            part = doc.getObject(part_name)
            if not part:
                return self.format_result("error", error=f"Part '{part_name}' not found")

            # Create link to part in assembly
            link = doc.addObject("App::Link", f"{part_name}_Link")
            link.LinkedObject = part
            link.Label = f"{part.Label} (Link)"

            # Set position and rotation
            import FreeCAD
            placement = FreeCAD.Placement()
            placement.Base = FreeCAD.Vector(*position)
            placement.Rotation = FreeCAD.Rotation(*rotation)
            link.Placement = placement

            # Add to assembly
            assembly.addObject(link)

            doc.recompute()

            return self.format_result("success", result={
                "link_name": link.Name,
                "part_name": part_name,
                "assembly_name": assembly_name,
                "position": position,
                "rotation": rotation,
                "message": f"Part '{part_name}' added to assembly '{assembly_name}'"
            })

        except Exception as e:
            return self.format_result("error", error=f"Failed to add part: {e}")

    async def _create_constraint(self, params: Dict[str, Any]) -> ToolResult:
        """Create a constraint between parts."""
        try:
            constraint_type = params.get("constraint_type", "coincident")

            # This is a simplified constraint creation
            # Real implementation would depend on the assembly workbench used
            return self.format_result("success", result={
                "constraint_type": constraint_type,
                "message": f"Constraint '{constraint_type}' created (simplified implementation)",
                "note": "Full constraint implementation requires specific assembly workbench"
            })

        except Exception as e:
            return self.format_result("error", error=f"Failed to create constraint: {e}")

    async def _list_parts(self, params: Dict[str, Any]) -> ToolResult:
        """List all parts in an assembly."""
        try:
            assembly_name = params.get("assembly_name")
            doc = self._get_active_document()

            assembly = doc.getObject(assembly_name)
            if not assembly:
                return self.format_result("error", error=f"Assembly '{assembly_name}' not found")

            parts = []
            for obj in assembly.Group:
                if hasattr(obj, 'LinkedObject'):
                    parts.append({
                        "name": obj.Name,
                        "label": obj.Label,
                        "linked_object": obj.LinkedObject.Name if obj.LinkedObject else None,
                        "position": [obj.Placement.Base.x, obj.Placement.Base.y, obj.Placement.Base.z],
                        "rotation": [obj.Placement.Rotation.Axis.x, obj.Placement.Rotation.Axis.y, obj.Placement.Rotation.Axis.z, obj.Placement.Rotation.Angle]
                    })
                else:
                    parts.append({
                        "name": obj.Name,
                        "label": obj.Label,
                        "type": obj.TypeId
                    })

            return self.format_result("success", result={
                "assembly_name": assembly_name,
                "parts": parts,
                "part_count": len(parts)
            })

        except Exception as e:
            return self.format_result("error", error=f"Failed to list parts: {e}")

    async def _move_part(self, params: Dict[str, Any]) -> ToolResult:
        """Move a part within an assembly."""
        try:
            part_name = params.get("part_name")
            position = params.get("position", [0, 0, 0])
            rotation = params.get("rotation", [0, 0, 0])

            doc = self._get_active_document()
            part = doc.getObject(part_name)

            if not part:
                return self.format_result("error", error=f"Part '{part_name}' not found")

            # Update placement
            import FreeCAD
            placement = FreeCAD.Placement()
            placement.Base = FreeCAD.Vector(*position)
            placement.Rotation = FreeCAD.Rotation(*rotation)
            part.Placement = placement

            doc.recompute()

            return self.format_result("success", result={
                "part_name": part_name,
                "new_position": position,
                "new_rotation": rotation,
                "message": f"Part '{part_name}' moved successfully"
            })

        except Exception as e:
            return self.format_result("error", error=f"Failed to move part: {e}")

    def _get_active_document(self):
        """Get the active document or create a new one if none exists."""
        if self.app.ActiveDocument:
            return self.app.ActiveDocument
        else:
            return self.app.newDocument("Assembly_Document")
