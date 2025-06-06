import logging
from typing import Any, Dict

from ..base import ToolProvider, ToolResult, ToolSchema

logger = logging.getLogger(__name__)


class SmitheryToolProvider(ToolProvider):
    """Tool provider for smithery operations in FreeCAD."""

    def __init__(self, freecad_app=None):
        """
        Initialize the smithery tool provider.

        Args:
            freecad_app: Optional FreeCAD application instance. If None, will try to import FreeCAD.
        """
        self.app = freecad_app
        if self.app is None:
            try:
                import FreeCAD
                import Part

                self.app = FreeCAD
                self.Part = Part
                logger.info("Connected to FreeCAD for smithery operations")
            except ImportError:
                logger.warning(
                    "Could not import FreeCAD. Make sure it's installed and in your Python path."
                )
                self.app = None
                self.Part = None

    @property
    def tool_schema(self) -> ToolSchema:
        return ToolSchema(
            name="smithery",
            description="Tools for creating blacksmith and smithery objects in FreeCAD",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": [
                            "create_anvil",
                            "create_hammer",
                            "create_tongs",
                            "forge_blade",
                            "create_horseshoe",
                        ],
                        "description": "The smithery action to perform",
                    },
                    "length": {
                        "type": "number",
                        "description": "Length dimension in mm",
                    },
                    "width": {
                        "type": "number",
                        "description": "Width dimension in mm",
                    },
                    "height": {
                        "type": "number",
                        "description": "Height dimension in mm",
                    },
                    "thickness": {
                        "type": "number",
                        "description": "Thickness in mm",
                    },
                },
                "required": ["action"],
            },
            returns={
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "result": {"type": "object"},
                    "error": {"type": "string"},
                },
            },
            examples=[
                {"action": "create_anvil", "length": 400, "width": 120, "height": 200},
                {
                    "action": "create_hammer",
                    "handle_length": 300,
                    "handle_diameter": 25,
                },
            ],
        )

    async def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> ToolResult:
        """
        Execute a smithery tool.

        Args:
            tool_id: The ID of the tool to execute
            params: Parameters for the tool

        Returns:
            ToolResult containing the execution status and result
        """
        if self.app is None:
            return self.format_result("error", error="FreeCAD not available")

        action = params.get("action", tool_id)

        try:
            if action == "create_anvil":
                return await self._create_anvil(params)
            elif action == "create_hammer":
                return await self._create_hammer(params)
            elif action == "create_tongs":
                return await self._create_tongs(params)
            elif action == "forge_blade":
                return await self._forge_blade(params)
            elif action == "create_horseshoe":
                return await self._create_horseshoe(params)
            else:
                return self.format_result(
                    "error", error=f"Unknown smithery action: {action}"
                )
        except Exception as e:
            logger.error(f"Smithery tool failed: {e}")
            return self.format_result("error", error=str(e))

    async def _create_anvil(self, params: Dict[str, Any]) -> ToolResult:
        """Create an anvil model."""
        # Get parameters with default values
        length = params.get("length", 400.0)  # mm
        width = params.get("width", 120.0)  # mm
        height = params.get("height", 200.0)  # mm
        horn_length = params.get("horn_length", 150.0)  # mm

        # Get or create document
        doc = self._get_active_document()

        try:
            # Create the main body
            body = doc.addObject("Part::Box", "AnvilBody")
            body.Length = length
            body.Width = width
            body.Height = height * 0.7

            # Create the tapered top part
            top = doc.addObject("Part::Box", "AnvilTop")
            top.Length = length * 0.9
            top.Width = width
            top.Height = height * 0.3
            top.Placement.Base = self.app.Vector(
                (length - top.Length) / 2, 0, body.Height
            )

            # Create the horn (cone)
            horn = doc.addObject("Part::Cone", "AnvilHorn")
            horn.Radius1 = width / 3
            horn.Radius2 = width / 6
            horn.Height = horn_length
            # Rotate and position the horn
            horn.Placement.Rotation = self.app.Rotation(self.app.Vector(0, 1, 0), 90)
            horn.Placement.Base = self.app.Vector(
                length, width / 2, body.Height + top.Height / 2
            )

            # Create a fusion
            fusion = doc.addObject("Part::MultiFuse", "Anvil")
            fusion.Shapes = [body, top, horn]

            # Recompute document
            doc.recompute()

            return self.format_result(
                "success",
                result={
                    "object_id": fusion.Name,
                    "object_type": "Anvil",
                    "properties": {
                        "Length": length,
                        "Width": width,
                        "Height": height,
                        "HornLength": horn_length,
                    },
                },
            )
        except Exception as e:
            logger.error(f"Error creating anvil: {str(e)}")
            return self.format_result(
                "error", error=f"Failed to create anvil: {str(e)}"
            )

    async def _create_hammer(self, params: Dict[str, Any]) -> ToolResult:
        """Create a blacksmith hammer model."""
        # Get parameters with default values
        handle_length = params.get("handle_length", 300.0)  # mm
        handle_diameter = params.get("handle_diameter", 25.0)  # mm
        head_length = params.get("head_length", 100.0)  # mm
        head_width = params.get("head_width", 40.0)  # mm
        head_height = params.get("head_height", 30.0)  # mm

        # Get or create document
        doc = self._get_active_document()

        try:
            # Create the handle (cylinder)
            handle = doc.addObject("Part::Cylinder", "HammerHandle")
            handle.Radius = handle_diameter / 2
            handle.Height = handle_length
            # Rotate the handle to horizontal position
            handle.Placement.Rotation = self.app.Rotation(self.app.Vector(0, 1, 0), 90)

            # Create the hammer head
            head = doc.addObject("Part::Box", "HammerHead")
            head.Length = head_length
            head.Width = head_width
            head.Height = head_height
            # Position the head at the end of the handle
            head.Placement.Base = self.app.Vector(
                handle.Height - head.Length / 2,
                -head.Width / 2 + handle.Radius,
                -head.Height / 2 + handle.Radius,
            )

            # Create a fusion
            fusion = doc.addObject("Part::MultiFuse", "Hammer")
            fusion.Shapes = [handle, head]

            # Recompute document
            doc.recompute()

            return self.format_result(
                "success",
                result={
                    "object_id": fusion.Name,
                    "object_type": "Hammer",
                    "properties": {
                        "HandleLength": handle_length,
                        "HandleDiameter": handle_diameter,
                        "HeadLength": head_length,
                        "HeadWidth": head_width,
                        "HeadHeight": head_height,
                    },
                },
            )
        except Exception as e:
            logger.error(f"Error creating hammer: {str(e)}")
            return self.format_result(
                "error", error=f"Failed to create hammer: {str(e)}"
            )

    async def _create_tongs(self, params: Dict[str, Any]) -> ToolResult:
        """Create blacksmith tongs model."""
        # Get parameters with default values
        handle_length = params.get("handle_length", 300.0)  # mm
        jaw_length = params.get("jaw_length", 80.0)  # mm
        thickness = params.get("thickness", 10.0)  # mm
        width = params.get("width", 20.0)  # mm
        opening_angle = params.get("opening_angle", 15.0)  # degrees

        # Get or create document
        doc = self._get_active_document()

        try:
            # Create the first handle
            handle1 = doc.addObject("Part::Box", "Handle1")
            handle1.Length = handle_length
            handle1.Width = width
            handle1.Height = thickness

            # Create the first jaw
            jaw1 = doc.addObject("Part::Box", "Jaw1")
            jaw1.Length = jaw_length
            jaw1.Width = width
            jaw1.Height = thickness
            # Position and rotate the jaw
            jaw1.Placement.Base = self.app.Vector(0, 0, 0)
            jaw1.Placement.Rotation = self.app.Rotation(
                self.app.Vector(0, 0, 1), opening_angle
            )

            # Create the second handle
            handle2 = doc.addObject("Part::Box", "Handle2")
            handle2.Length = handle_length
            handle2.Width = width
            handle2.Height = thickness
            # Position the second handle
            handle2.Placement.Base = self.app.Vector(0, 0, thickness * 2)

            # Create the second jaw
            jaw2 = doc.addObject("Part::Box", "Jaw2")
            jaw2.Length = jaw_length
            jaw2.Width = width
            jaw2.Height = thickness
            # Position and rotate the jaw
            jaw2.Placement.Base = self.app.Vector(0, 0, thickness * 2)
            jaw2.Placement.Rotation = self.app.Rotation(
                self.app.Vector(0, 0, 1), -opening_angle
            )

            # Create a pivot point (cylinder)
            pivot = doc.addObject("Part::Cylinder", "Pivot")
            pivot.Radius = thickness
            pivot.Height = thickness * 3
            pivot.Placement.Base = self.app.Vector(0, width / 2, 0)
            pivot.Placement.Rotation = self.app.Rotation(self.app.Vector(1, 0, 0), 90)

            # Group into a compound object
            tongs = doc.addObject("Part::Compound", "Tongs")
            tongs.Links = [handle1, jaw1, handle2, jaw2, pivot]

            # Recompute document
            doc.recompute()

            return self.format_result(
                "success",
                result={
                    "object_id": tongs.Name,
                    "object_type": "Tongs",
                    "properties": {
                        "HandleLength": handle_length,
                        "JawLength": jaw_length,
                        "Thickness": thickness,
                        "Width": width,
                        "OpeningAngle": opening_angle,
                    },
                },
            )
        except Exception as e:
            logger.error(f"Error creating tongs: {str(e)}")
            return self.format_result(
                "error", error=f"Failed to create tongs: {str(e)}"
            )

    async def _forge_blade(self, params: Dict[str, Any]) -> ToolResult:
        """Create a forged blade model."""
        # Get parameters with default values
        blade_length = params.get("blade_length", 250.0)  # mm
        blade_width = params.get("blade_width", 40.0)  # mm
        thickness = params.get("thickness", 4.0)  # mm
        tang_length = params.get("tang_length", 100.0)  # mm
        tang_width = params.get("tang_width", 15.0)  # mm
        curvature = params.get("curvature", 10.0)  # mm, how much the blade curves

        # Get or create document
        doc = self._get_active_document()

        try:
            if not self.Part:
                return self.format_result("error", error="Part module not available")

            # Create blade as a loft between two wires
            # Base wire (at the guard)
            base_points = [
                self.app.Vector(0, -blade_width / 2, 0),
                self.app.Vector(0, blade_width / 2, 0),
            ]
            base_wire = self.Part.makePolygon(base_points)

            # Tip wire
            tip_points = [
                self.app.Vector(blade_length, -curvature, 0),
                self.app.Vector(blade_length, 0, 0),
            ]
            tip_wire = self.Part.makePolygon(tip_points)

            # Create the blade face by lofting between the two wires
            # This is a simplification - in a real implementation we would use a more complex shape
            # Create a simple blade using a box for now
            blade = doc.addObject("Part::Box", "Blade")
            blade.Length = blade_length
            blade.Width = blade_width
            blade.Height = thickness

            # Create the tang
            tang = doc.addObject("Part::Box", "Tang")
            tang.Length = tang_length
            tang.Width = tang_width
            tang.Height = thickness
            tang.Placement.Base = self.app.Vector(
                -tang_length, (blade_width - tang_width) / 2, 0
            )

            # Create a fusion
            fusion = doc.addObject("Part::MultiFuse", "Blade")
            fusion.Shapes = [blade, tang]

            # Recompute document
            doc.recompute()

            return self.format_result(
                "success",
                result={
                    "object_id": fusion.Name,
                    "object_type": "Blade",
                    "properties": {
                        "BladeLength": blade_length,
                        "BladeWidth": blade_width,
                        "Thickness": thickness,
                        "TangLength": tang_length,
                        "TangWidth": tang_width,
                        "Curvature": curvature,
                    },
                },
            )
        except Exception as e:
            logger.error(f"Error forging blade: {str(e)}")
            return self.format_result("error", error=f"Failed to forge blade: {str(e)}")

    async def _create_horseshoe(self, params: Dict[str, Any]) -> ToolResult:
        """Create a horseshoe model."""
        # Get parameters with default values
        outer_radius = params.get("outer_radius", 60.0)  # mm
        inner_radius = params.get("inner_radius", 40.0)  # mm
        thickness = params.get("thickness", 10.0)  # mm
        opening_angle = params.get("opening_angle", 60.0)  # degrees

        # Get or create document
        doc = self._get_active_document()

        try:
            if not self.Part:
                return self.format_result("error", error="Part module not available")

            # Create the outer circle
            outer_circle = self.Part.makeCircle(outer_radius)

            # Create the inner circle
            inner_circle = self.Part.makeCircle(inner_radius)

            # Create wires from the circles
            outer_wire = self.Part.Wire(outer_circle)
            inner_wire = self.Part.Wire(inner_circle)

            # Create a face from the wires
            face = self.Part.Face([outer_wire, inner_wire])

            # Extrude the face into a solid
            solid = face.extrude(self.app.Vector(0, 0, thickness))

            # Cut a portion of the horseshoe to create the opening
            # This is simplified - actual implementation would use more complex geometry

            # Create a part object
            horseshoe_part = doc.addObject("Part::Feature", "Horseshoe")
            horseshoe_part.Shape = solid

            # Recompute document
            doc.recompute()

            return self.format_result(
                "success",
                result={
                    "object_id": horseshoe_part.Name,
                    "object_type": "Horseshoe",
                    "properties": {
                        "OuterRadius": outer_radius,
                        "InnerRadius": inner_radius,
                        "Thickness": thickness,
                        "OpeningAngle": opening_angle,
                    },
                },
            )
        except Exception as e:
            logger.error(f"Error creating horseshoe: {str(e)}")
            return self.format_result(
                "error", error=f"Failed to create horseshoe: {str(e)}"
            )

    def _get_active_document(self):
        """Get the active document or create a new one if none exists."""
        if self.app.ActiveDocument:
            return self.app.ActiveDocument
        else:
            return self.app.newDocument("Smithery")
