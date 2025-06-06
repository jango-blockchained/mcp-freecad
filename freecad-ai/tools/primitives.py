"""
Primitives Tool

MCP tool for creating basic 3D primitive shapes in FreeCAD including
boxes, cylinders, spheres, cones, and other fundamental shapes.

Author: jango-blockchained
"""

from typing import Any, Dict, Optional

import FreeCAD as App
import Part


class PrimitivesTool:
    """Tool for creating 3D primitive shapes."""

    def __init__(self):
        """Initialize the primitives tool."""
        self.name = "primitives"
        self.description = "Create basic 3D primitive shapes"

    def create_box(
        self,
        length: float = 10.0,
        width: float = 10.0,
        height: float = 10.0,
        position: tuple = (0, 0, 0),
        name: str = None,
    ) -> Dict[str, Any]:
        """Create a box primitive.

        Args:
            length: Box length in mm
            width: Box width in mm
            height: Box height in mm
            position: (x, y, z) position tuple
            name: Optional object name

        Returns:
            Dictionary with creation result
        """
        try:
            # Get or create active document
            doc = App.ActiveDocument
            if not doc:
                doc = App.newDocument("Untitled")

            # Create box
            box = Part.makeBox(length, width, height)

            # Create FreeCAD object
            obj_name = name or f"Box_{length}x{width}x{height}"
            box_obj = doc.addObject("Part::Feature", obj_name)
            box_obj.Shape = box
            box_obj.Label = obj_name

            # Set position
            if position != (0, 0, 0):
                box_obj.Placement.Base = App.Vector(*position)

            # Recompute document
            doc.recompute()

            return {
                "success": True,
                "object_name": box_obj.Name,
                "label": box_obj.Label,
                "message": f"Created box {length}x{width}x{height}mm at position {position}",
                "properties": {
                    "length": length,
                    "width": width,
                    "height": height,
                    "volume": length * width * height,
                    "position": position,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create box: {str(e)}",
            }

    def create_cylinder(
        self,
        radius: float = 5.0,
        height: float = 10.0,
        position: tuple = (0, 0, 0),
        name: str = None,
    ) -> Dict[str, Any]:
        """Create a cylinder primitive.

        Args:
            radius: Cylinder radius in mm
            height: Cylinder height in mm
            position: (x, y, z) position tuple
            name: Optional object name

        Returns:
            Dictionary with creation result
        """
        try:
            # Get or create active document
            doc = App.ActiveDocument
            if not doc:
                doc = App.newDocument("Untitled")

            # Create cylinder
            cylinder = Part.makeCylinder(radius, height)

            # Create FreeCAD object
            obj_name = name or f"Cylinder_R{radius}_H{height}"
            cyl_obj = doc.addObject("Part::Feature", obj_name)
            cyl_obj.Shape = cylinder
            cyl_obj.Label = obj_name

            # Set position
            if position != (0, 0, 0):
                cyl_obj.Placement.Base = App.Vector(*position)

            # Recompute document
            doc.recompute()

            import math

            volume = math.pi * radius * radius * height

            return {
                "success": True,
                "object_name": cyl_obj.Name,
                "label": cyl_obj.Label,
                "message": f"Created cylinder R{radius}mm H{height}mm at position {position}",
                "properties": {
                    "radius": radius,
                    "height": height,
                    "volume": round(volume, 2),
                    "position": position,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create cylinder: {str(e)}",
            }

    def create_sphere(
        self, radius: float = 5.0, position: tuple = (0, 0, 0), name: str = None
    ) -> Dict[str, Any]:
        """Create a sphere primitive.

        Args:
            radius: Sphere radius in mm
            position: (x, y, z) position tuple
            name: Optional object name

        Returns:
            Dictionary with creation result
        """
        try:
            # Get or create active document
            doc = App.ActiveDocument
            if not doc:
                doc = App.newDocument("Untitled")

            # Create sphere
            sphere = Part.makeSphere(radius)

            # Create FreeCAD object
            obj_name = name or f"Sphere_R{radius}"
            sphere_obj = doc.addObject("Part::Feature", obj_name)
            sphere_obj.Shape = sphere
            sphere_obj.Label = obj_name

            # Set position
            if position != (0, 0, 0):
                sphere_obj.Placement.Base = App.Vector(*position)

            # Recompute document
            doc.recompute()

            import math

            volume = (4 / 3) * math.pi * radius * radius * radius

            return {
                "success": True,
                "object_name": sphere_obj.Name,
                "label": sphere_obj.Label,
                "message": f"Created sphere R{radius}mm at position {position}",
                "properties": {
                    "radius": radius,
                    "volume": round(volume, 2),
                    "position": position,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create sphere: {str(e)}",
            }

    def create_cone(
        self,
        radius1: float = 5.0,
        radius2: float = 0.0,
        height: float = 10.0,
        position: tuple = (0, 0, 0),
        name: str = None,
    ) -> Dict[str, Any]:
        """Create a cone primitive.

        Args:
            radius1: Bottom radius in mm
            radius2: Top radius in mm (0 for true cone)
            height: Cone height in mm
            position: (x, y, z) position tuple
            name: Optional object name

        Returns:
            Dictionary with creation result
        """
        try:
            # Get or create active document
            doc = App.ActiveDocument
            if not doc:
                doc = App.newDocument("Untitled")

            # Create cone
            cone = Part.makeCone(radius1, radius2, height)

            # Create FreeCAD object
            obj_name = name or f"Cone_R1{radius1}_R2{radius2}_H{height}"
            cone_obj = doc.addObject("Part::Feature", obj_name)
            cone_obj.Shape = cone
            cone_obj.Label = obj_name

            # Set position
            if position != (0, 0, 0):
                cone_obj.Placement.Base = App.Vector(*position)

            # Recompute document
            doc.recompute()

            import math

            volume = (
                (1 / 3)
                * math.pi
                * height
                * (radius1 * radius1 + radius1 * radius2 + radius2 * radius2)
            )

            return {
                "success": True,
                "object_name": cone_obj.Name,
                "label": cone_obj.Label,
                "message": f"Created cone R1{radius1}mm R2{radius2}mm H{height}mm at position {position}",
                "properties": {
                    "radius1": radius1,
                    "radius2": radius2,
                    "height": height,
                    "volume": round(volume, 2),
                    "position": position,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create cone: {str(e)}",
            }

    def create_torus(
        self,
        radius1: float = 10.0,
        radius2: float = 2.0,
        position: tuple = (0, 0, 0),
        name: str = None,
    ) -> Dict[str, Any]:
        """Create a torus primitive.

        Args:
            radius1: Major radius in mm
            radius2: Minor radius in mm
            position: (x, y, z) position tuple
            name: Optional object name

        Returns:
            Dictionary with creation result
        """
        try:
            # Get or create active document
            doc = App.ActiveDocument
            if not doc:
                doc = App.newDocument("Untitled")

            # Create torus
            torus = Part.makeTorus(radius1, radius2)

            # Create FreeCAD object
            obj_name = name or f"Torus_R1{radius1}_R2{radius2}"
            torus_obj = doc.addObject("Part::Feature", obj_name)
            torus_obj.Shape = torus
            torus_obj.Label = obj_name

            # Set position
            if position != (0, 0, 0):
                torus_obj.Placement.Base = App.Vector(*position)

            # Recompute document
            doc.recompute()

            import math

            volume = 2 * math.pi * math.pi * radius1 * radius2 * radius2

            return {
                "success": True,
                "object_name": torus_obj.Name,
                "label": torus_obj.Label,
                "message": f"Created torus R1{radius1}mm R2{radius2}mm at position {position}",
                "properties": {
                    "major_radius": radius1,
                    "minor_radius": radius2,
                    "volume": round(volume, 2),
                    "position": position,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create torus: {str(e)}",
            }

    def get_available_primitives(self) -> Dict[str, Any]:
        """Get list of available primitive types.

        Returns:
            Dictionary with available primitives and their parameters
        """
        return {
            "primitives": {
                "box": {
                    "description": "Create a rectangular box",
                    "parameters": ["length", "width", "height", "position", "name"],
                },
                "cylinder": {
                    "description": "Create a circular cylinder",
                    "parameters": ["radius", "height", "position", "name"],
                },
                "sphere": {
                    "description": "Create a sphere",
                    "parameters": ["radius", "position", "name"],
                },
                "cone": {
                    "description": "Create a cone or truncated cone",
                    "parameters": ["radius1", "radius2", "height", "position", "name"],
                },
                "torus": {
                    "description": "Create a torus (donut shape)",
                    "parameters": ["radius1", "radius2", "position", "name"],
                },
            }
        }
