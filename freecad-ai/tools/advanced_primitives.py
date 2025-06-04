"""
Advanced Primitives Tool

MCP tool for creating advanced 3D primitive shapes in FreeCAD including
tubes, prisms, wedges, and ellipsoids.

Author: AI Assistant
"""

import FreeCAD as App
import Part
import math
from typing import Dict, Any, Optional


class AdvancedPrimitivesTool:
    """Tool for creating advanced 3D primitive shapes."""

    def __init__(self):
        """Initialize the advanced primitives tool."""
        self.name = "advanced_primitives"
        self.description = "Create advanced 3D primitive shapes"

    def create_tube(self, outer_radius: float = 10.0, inner_radius: float = 5.0,
                   height: float = 10.0, position: tuple = (0, 0, 0),
                   name: str = None) -> Dict[str, Any]:
        """Create a tube (hollow cylinder) primitive.

        Args:
            outer_radius: Outer radius of the tube in mm
            inner_radius: Inner radius of the tube in mm
            height: Height of the tube in mm
            position: (x, y, z) position tuple
            name: Optional object name

        Returns:
            Dictionary with creation result
        """
        try:
            # Parameter validation
            if outer_radius <= 0:
                return {
                    "success": False,
                    "error": "Outer radius must be positive",
                    "message": f"Invalid outer radius: {outer_radius}"
                }

            if inner_radius < 0:
                return {
                    "success": False,
                    "error": "Inner radius must be non-negative",
                    "message": f"Invalid inner radius: {inner_radius}"
                }

            if inner_radius >= outer_radius:
                return {
                    "success": False,
                    "error": "Inner radius must be less than outer radius",
                    "message": f"Inner radius {inner_radius} >= outer radius {outer_radius}"
                }

            if height <= 0:
                return {
                    "success": False,
                    "error": "Height must be positive",
                    "message": f"Invalid height: {height}"
                }

            # Get or create active document
            doc = App.ActiveDocument
            if not doc:
                doc = App.newDocument("Untitled")

            # Create outer cylinder
            outer_cylinder = Part.makeCylinder(outer_radius, height)

            # Create inner cylinder (if inner_radius > 0)
            if inner_radius > 0:
                inner_cylinder = Part.makeCylinder(inner_radius, height)
                # Create tube by cutting inner from outer
                tube_shape = outer_cylinder.cut(inner_cylinder)
            else:
                # If inner_radius is 0, just use the outer cylinder (solid)
                tube_shape = outer_cylinder

            # Create FreeCAD object
            obj_name = name or f"Tube_OR{outer_radius}_IR{inner_radius}_H{height}"
            tube_obj = doc.addObject("Part::Feature", obj_name)
            tube_obj.Shape = tube_shape
            tube_obj.Label = obj_name

            # Set position
            if position != (0, 0, 0):
                tube_obj.Placement.Base = App.Vector(*position)

            # Recompute document
            doc.recompute()

            # Calculate volume
            volume = tube_shape.Volume

            return {
                "success": True,
                "object_name": tube_obj.Name,
                "label": tube_obj.Label,
                "message": f"Created tube OR{outer_radius}mm IR{inner_radius}mm H{height}mm at position {position}",
                "properties": {
                    "outer_radius": outer_radius,
                    "inner_radius": inner_radius,
                    "height": height,
                    "volume": round(volume, 2),
                    "position": position,
                    "wall_thickness": outer_radius - inner_radius
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create tube: {str(e)}"
            }

    def create_prism(self, sides: int = 6, radius: float = 5.0, height: float = 10.0,
                    position: tuple = (0, 0, 0), name: str = None) -> Dict[str, Any]:
        """Create a regular polygonal prism primitive.

        Args:
            sides: Number of sides for the polygon (3-20)
            radius: Radius of the circumscribed circle in mm
            height: Height of the prism in mm
            position: (x, y, z) position tuple
            name: Optional object name

        Returns:
            Dictionary with creation result
        """
        try:
            # Parameter validation
            if not isinstance(sides, int) or sides < 3 or sides > 20:
                return {
                    "success": False,
                    "error": "Sides must be an integer between 3 and 20",
                    "message": f"Invalid sides count: {sides}"
                }

            if radius <= 0:
                return {
                    "success": False,
                    "error": "Radius must be positive",
                    "message": f"Invalid radius: {radius}"
                }

            if height <= 0:
                return {
                    "success": False,
                    "error": "Height must be positive",
                    "message": f"Invalid height: {height}"
                }

            # Get or create active document
            doc = App.ActiveDocument
            if not doc:
                doc = App.newDocument("Untitled")

            # Create polygon vertices
            vertices = []
            for i in range(sides):
                angle = 2 * math.pi * i / sides
                x = radius * math.cos(angle)
                y = radius * math.sin(angle)
                vertices.append(App.Vector(x, y, 0))

            # Close the polygon by adding the first vertex at the end
            vertices.append(vertices[0])

            # Create wire from vertices
            edges = []
            for i in range(len(vertices) - 1):
                edge = Part.makeLine(vertices[i], vertices[i + 1])
                edges.append(edge)

            wire = Part.Wire(edges)

            # Create face from wire
            face = Part.Face(wire)

            # Extrude face to create prism
            prism_shape = face.extrude(App.Vector(0, 0, height))

            # Create FreeCAD object
            obj_name = name or f"Prism_{sides}sides_R{radius}_H{height}"
            prism_obj = doc.addObject("Part::Feature", obj_name)
            prism_obj.Shape = prism_shape
            prism_obj.Label = obj_name

            # Set position
            if position != (0, 0, 0):
                prism_obj.Placement.Base = App.Vector(*position)

            # Recompute document
            doc.recompute()

            # Calculate properties
            volume = prism_shape.Volume
            base_area = face.Area

            return {
                "success": True,
                "object_name": prism_obj.Name,
                "label": prism_obj.Label,
                "message": f"Created {sides}-sided prism R{radius}mm H{height}mm at position {position}",
                "properties": {
                    "sides": sides,
                    "radius": radius,
                    "height": height,
                    "volume": round(volume, 2),
                    "base_area": round(base_area, 2),
                    "position": position
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create prism: {str(e)}"
            }

    def create_wedge(self, length: float = 10.0, width: float = 10.0, height: float = 10.0,
                    angle: float = 45.0, position: tuple = (0, 0, 0),
                    name: str = None) -> Dict[str, Any]:
        """Create a wedge (tapered block) primitive.

        Args:
            length: Length of the wedge base in mm
            width: Width of the wedge base in mm
            height: Height of the wedge in mm
            angle: Taper angle in degrees (0-90)
            position: (x, y, z) position tuple
            name: Optional object name

        Returns:
            Dictionary with creation result
        """
        try:
            # Parameter validation
            if length <= 0:
                return {
                    "success": False,
                    "error": "Length must be positive",
                    "message": f"Invalid length: {length}"
                }

            if width <= 0:
                return {
                    "success": False,
                    "error": "Width must be positive",
                    "message": f"Invalid width: {width}"
                }

            if height <= 0:
                return {
                    "success": False,
                    "error": "Height must be positive",
                    "message": f"Invalid height: {height}"
                }

            if angle < 0 or angle > 90:
                return {
                    "success": False,
                    "error": "Angle must be between 0 and 90 degrees",
                    "message": f"Invalid angle: {angle}"
                }

            # Get or create active document
            doc = App.ActiveDocument
            if not doc:
                doc = App.newDocument("Untitled")

            # Calculate taper offset
            angle_rad = math.radians(angle)
            taper_offset = height * math.tan(angle_rad)

            # Create wedge vertices
            vertices = [
                App.Vector(0, 0, 0),                    # Bottom front left
                App.Vector(length, 0, 0),               # Bottom front right
                App.Vector(length, width, 0),           # Bottom back right
                App.Vector(0, width, 0),                # Bottom back left
                App.Vector(taper_offset, 0, height),    # Top front left
                App.Vector(length, 0, height),          # Top front right
                App.Vector(length, width, height),      # Top back right
                App.Vector(taper_offset, width, height) # Top back left
            ]

            # Define faces using vertex indices
            faces = [
                [0, 1, 2, 3],       # Bottom face
                [4, 7, 6, 5],       # Top face
                [0, 4, 5, 1],       # Front face
                [2, 6, 7, 3],       # Back face
                [1, 5, 6, 2],       # Right face
                [0, 3, 7, 4]        # Left face (tapered)
            ]

            # Create faces
            face_objects = []
            for face_indices in faces:
                face_vertices = [vertices[i] for i in face_indices]
                # Close the face by adding first vertex at end
                face_vertices.append(face_vertices[0])

                # Create edges
                edges = []
                for i in range(len(face_vertices) - 1):
                    edge = Part.makeLine(face_vertices[i], face_vertices[i + 1])
                    edges.append(edge)

                # Create wire and face
                wire = Part.Wire(edges)
                face = Part.Face(wire)
                face_objects.append(face)

            # Create shell from faces
            shell = Part.Shell(face_objects)

            # Create solid from shell
            wedge_shape = Part.Solid(shell)

            # Create FreeCAD object
            obj_name = name or f"Wedge_L{length}_W{width}_H{height}_A{angle}"
            wedge_obj = doc.addObject("Part::Feature", obj_name)
            wedge_obj.Shape = wedge_shape
            wedge_obj.Label = obj_name

            # Set position
            if position != (0, 0, 0):
                wedge_obj.Placement.Base = App.Vector(*position)

            # Recompute document
            doc.recompute()

            # Calculate volume
            volume = wedge_shape.Volume

            return {
                "success": True,
                "object_name": wedge_obj.Name,
                "label": wedge_obj.Label,
                "message": f"Created wedge L{length}mm W{width}mm H{height}mm A{angle}° at position {position}",
                "properties": {
                    "length": length,
                    "width": width,
                    "height": height,
                    "angle": angle,
                    "volume": round(volume, 2),
                    "taper_offset": round(taper_offset, 2),
                    "position": position
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create wedge: {str(e)}"
            }

    def create_ellipsoid(self, radius_x: float = 5.0, radius_y: float = 3.0,
                        radius_z: float = 4.0, position: tuple = (0, 0, 0),
                        name: str = None) -> Dict[str, Any]:
        """Create an ellipsoid primitive.

        Args:
            radius_x: Radius along X-axis in mm
            radius_y: Radius along Y-axis in mm
            radius_z: Radius along Z-axis in mm
            position: (x, y, z) position tuple
            name: Optional object name

        Returns:
            Dictionary with creation result
        """
        try:
            # Parameter validation
            if radius_x <= 0:
                return {
                    "success": False,
                    "error": "X-radius must be positive",
                    "message": f"Invalid radius_x: {radius_x}"
                }

            if radius_y <= 0:
                return {
                    "success": False,
                    "error": "Y-radius must be positive",
                    "message": f"Invalid radius_y: {radius_y}"
                }

            if radius_z <= 0:
                return {
                    "success": False,
                    "error": "Z-radius must be positive",
                    "message": f"Invalid radius_z: {radius_z}"
                }

            # Get or create active document
            doc = App.ActiveDocument
            if not doc:
                doc = App.newDocument("Untitled")

            # Create unit sphere
            sphere = Part.makeSphere(1.0)

            # Create scaling matrix
            matrix = App.Matrix()
            matrix.scale(radius_x, radius_y, radius_z)

            # Apply scaling to create ellipsoid
            ellipsoid_shape = sphere.transformGeometry(matrix)

            # Create FreeCAD object
            obj_name = name or f"Ellipsoid_RX{radius_x}_RY{radius_y}_RZ{radius_z}"
            ellipsoid_obj = doc.addObject("Part::Feature", obj_name)
            ellipsoid_obj.Shape = ellipsoid_shape
            ellipsoid_obj.Label = obj_name

            # Set position
            if position != (0, 0, 0):
                ellipsoid_obj.Placement.Base = App.Vector(*position)

            # Recompute document
            doc.recompute()

            # Calculate volume (4/3 * π * a * b * c)
            volume = (4/3) * math.pi * radius_x * radius_y * radius_z

            return {
                "success": True,
                "object_name": ellipsoid_obj.Name,
                "label": ellipsoid_obj.Label,
                "message": f"Created ellipsoid RX{radius_x}mm RY{radius_y}mm RZ{radius_z}mm at position {position}",
                "properties": {
                    "radius_x": radius_x,
                    "radius_y": radius_y,
                    "radius_z": radius_z,
                    "volume": round(volume, 2),
                    "position": position,
                    "is_sphere": radius_x == radius_y == radius_z
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create ellipsoid: {str(e)}"
            }

    def get_available_primitives(self) -> Dict[str, Any]:
        """Get list of available advanced primitive types.

        Returns:
            Dictionary with available primitives and their parameters
        """
        return {
            "advanced_primitives": {
                "tube": {
                    "description": "Create a hollow cylinder (tube)",
                    "parameters": ["outer_radius", "inner_radius", "height", "position", "name"]
                },
                "prism": {
                    "description": "Create a regular polygonal prism",
                    "parameters": ["sides", "radius", "height", "position", "name"]
                },
                "wedge": {
                    "description": "Create a tapered block (wedge)",
                    "parameters": ["length", "width", "height", "angle", "position", "name"]
                },
                "ellipsoid": {
                    "description": "Create an ellipsoid (oval sphere)",
                    "parameters": ["radius_x", "radius_y", "radius_z", "position", "name"]
                }
            }
        }
