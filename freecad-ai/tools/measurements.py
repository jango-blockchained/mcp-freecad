"""
Measurements Tool

MCP tool for measuring distances, angles, volumes, areas, and other
geometric properties of FreeCAD objects.

Author: jango-blockchained
"""

import FreeCAD as App
import Part
import math
from typing import Dict, Any, List, Optional, Union, Tuple


class MeasurementsTool:
    """Tool for measuring geometric properties of objects."""

    def __init__(self):
        """Initialize the measurements tool."""
        self.name = "measurements"
        self.description = "Measure distances, angles, volumes, and other properties"

    def _get_object(self, obj_name: str, doc: Any = None) -> Optional[Any]:
        """Get an object by name from the document.

        Args:
            obj_name: Name of the object to find
            doc: Document to search in (uses ActiveDocument if None)

        Returns:
            The FreeCAD object or None if not found
        """
        if doc is None:
            doc = App.ActiveDocument
        if not doc:
            return None

        return doc.getObject(obj_name)

    def _get_point_from_spec(
        self, point_spec: Union[str, List[float], Tuple[float, float, float]]
    ) -> Optional[App.Vector]:
        """Convert various point specifications to FreeCAD Vector.

        Args:
            point_spec: Can be:
                - Object name (uses center of bounding box)
                - List/tuple of [x, y, z] coordinates

        Returns:
            FreeCAD Vector or None if invalid
        """
        if isinstance(point_spec, (list, tuple)) and len(point_spec) == 3:
            return App.Vector(*point_spec)
        elif isinstance(point_spec, str):
            obj = self._get_object(point_spec)
            if obj and hasattr(obj, "Shape") and obj.Shape:
                bbox = obj.Shape.BoundBox
                return bbox.Center
        return None

    def measure_distance(
        self, point1: Union[str, List[float]], point2: Union[str, List[float]]
    ) -> Dict[str, Any]:
        """Measure distance between two points or object centers.

        Args:
            point1: First point - can be object name or [x,y,z] coordinates
            point2: Second point - can be object name or [x,y,z] coordinates

        Returns:
            Dictionary with measurement result
        """
        try:
            doc = App.ActiveDocument
            if not doc:
                return {
                    "success": False,
                    "error": "No active document",
                    "message": "No active document found",
                }

            # Convert point specifications to vectors
            vec1 = self._get_point_from_spec(point1)
            vec2 = self._get_point_from_spec(point2)

            if vec1 is None:
                return {
                    "success": False,
                    "error": "Invalid point1",
                    "message": f"Could not resolve point1: {point1}",
                }

            if vec2 is None:
                return {
                    "success": False,
                    "error": "Invalid point2",
                    "message": f"Could not resolve point2: {point2}",
                }

            # Calculate distance
            # Calculate distance manually for mock compatibility
            distance = (
                (vec2.x - vec1.x) ** 2 + (vec2.y - vec1.y) ** 2 + (vec2.z - vec1.z) ** 2
            ) ** 0.5

            # Calculate component distances
            dx = abs(vec2.x - vec1.x)
            dy = abs(vec2.y - vec1.y)
            dz = abs(vec2.z - vec1.z)

            return {
                "success": True,
                "message": f"Measured distance: {round(distance, 3)} mm",
                "properties": {
                    "distance": round(distance, 3),
                    "dx": round(dx, 3),
                    "dy": round(dy, 3),
                    "dz": round(dz, 3),
                    "point1": (round(vec1.x, 3), round(vec1.y, 3), round(vec1.z, 3)),
                    "point2": (round(vec2.x, 3), round(vec2.y, 3), round(vec2.z, 3)),
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to measure distance: {str(e)}",
            }

    def measure_angle(
        self,
        obj1_name: str,
        obj2_name: str,
        obj3_name: str = None,
        vertex_mode: bool = False,
    ) -> Dict[str, Any]:
        """Measure angle between objects or edges.

        Args:
            obj1_name: First object/edge
            obj2_name: Second object/edge
            obj3_name: Optional third object for 3-point angle
            vertex_mode: If True, use objects as vertices for angle calculation

        Returns:
            Dictionary with measurement result
        """
        try:
            doc = App.ActiveDocument
            if not doc:
                return {
                    "success": False,
                    "error": "No active document",
                    "message": "No active document found",
                }

            if vertex_mode and obj3_name:
                # Three-point angle measurement
                vec1 = self._get_point_from_spec(obj1_name)
                vec2 = self._get_point_from_spec(obj2_name)  # vertex
                vec3 = self._get_point_from_spec(obj3_name)

                if not all([vec1, vec2, vec3]):
                    return {
                        "success": False,
                        "error": "Invalid points",
                        "message": "Could not resolve all three points",
                    }

                # Calculate vectors from vertex
                v1 = vec1 - vec2
                v2 = vec3 - vec2

                # Calculate angle
                dot_product = v1.dot(v2)
                magnitude = v1.Length * v2.Length

                if magnitude == 0:
                    return {
                        "success": False,
                        "error": "Zero length vector",
                        "message": "One or more vectors have zero length",
                    }

                cos_angle = dot_product / magnitude
                # Clamp to avoid numerical errors
                cos_angle = max(-1.0, min(1.0, cos_angle))
                angle_rad = math.acos(cos_angle)
                angle_deg = math.degrees(angle_rad)

                return {
                    "success": True,
                    "message": f"Measured angle: {round(angle_deg, 2)}°",
                    "properties": {
                        "angle_degrees": round(angle_deg, 2),
                        "angle_radians": round(angle_rad, 4),
                        "vertex": (
                            round(vec2.x, 3),
                            round(vec2.y, 3),
                            round(vec2.z, 3),
                        ),
                    },
                }
            else:
                # Edge/face angle measurement (simplified)
                obj1 = self._get_object(obj1_name)
                obj2 = self._get_object(obj2_name)

                if not obj1 or not obj2:
                    return {
                        "success": False,
                        "error": "Objects not found",
                        "message": "One or both objects not found",
                    }

                # For simplicity, measure angle between object orientations
                # In real implementation, this would handle edges/faces properly
                rot1 = obj1.Placement.Rotation
                rot2 = obj2.Placement.Rotation

                # Get Z-axis vectors (forward direction)
                z1 = rot1.multVec(App.Vector(0, 0, 1))
                z2 = rot2.multVec(App.Vector(0, 0, 1))

                # Calculate angle
                dot_product = z1.dot(z2)
                cos_angle = max(-1.0, min(1.0, dot_product))
                angle_rad = math.acos(cos_angle)
                angle_deg = math.degrees(angle_rad)

                return {
                    "success": True,
                    "message": f"Measured angle between orientations: {round(angle_deg, 2)}°",
                    "properties": {
                        "angle_degrees": round(angle_deg, 2),
                        "angle_radians": round(angle_rad, 4),
                        "type": "orientation_angle",
                    },
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to measure angle: {str(e)}",
            }

    def measure_volume(self, obj_name: str) -> Dict[str, Any]:
        """Measure volume of an object.

        Args:
            obj_name: Name of object to measure

        Returns:
            Dictionary with measurement result
        """
        try:
            doc = App.ActiveDocument
            if not doc:
                return {
                    "success": False,
                    "error": "No active document",
                    "message": "No active document found",
                }

            obj = self._get_object(obj_name)
            if not obj:
                return {
                    "success": False,
                    "error": f"Object '{obj_name}' not found",
                    "message": f"Object '{obj_name}' not found in document",
                }

            if not hasattr(obj, "Shape") or not obj.Shape:
                return {
                    "success": False,
                    "error": "No shape",
                    "message": f"Object '{obj_name}' has no valid shape",
                }

            shape = obj.Shape

            # Check if solid
            if not shape.isSolid():
                return {
                    "success": False,
                    "error": "Not a solid",
                    "message": f"Object '{obj_name}' is not a solid and has no volume",
                }

            volume = shape.Volume  # in mm³
            volume_cm3 = volume / 1000
            volume_m3 = volume / 1e9

            # Get mass properties
            mass_props = shape.MatrixOfInertia
            center_of_mass = shape.CenterOfMass

            return {
                "success": True,
                "message": f"Volume of {obj_name}: {round(volume, 2)} mm³",
                "properties": {
                    "volume_mm3": round(volume, 2),
                    "volume_cm3": round(volume_cm3, 5),
                    "volume_m3": round(volume_m3, 9),
                    "center_of_mass": (
                        round(center_of_mass.x, 3),
                        round(center_of_mass.y, 3),
                        round(center_of_mass.z, 3),
                    ),
                    "is_solid": shape.isSolid(),
                    "is_closed": shape.isClosed(),
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to measure volume: {str(e)}",
            }

    def measure_area(self, obj_name: str, face_index: int = None) -> Dict[str, Any]:
        """Measure surface area of an object or specific face.

        Args:
            obj_name: Name of object to measure
            face_index: Optional index of specific face to measure

        Returns:
            Dictionary with measurement result
        """
        try:
            doc = App.ActiveDocument
            if not doc:
                return {
                    "success": False,
                    "error": "No active document",
                    "message": "No active document found",
                }

            obj = self._get_object(obj_name)
            if not obj:
                return {
                    "success": False,
                    "error": f"Object '{obj_name}' not found",
                    "message": f"Object '{obj_name}' not found in document",
                }

            if not hasattr(obj, "Shape") or not obj.Shape:
                return {
                    "success": False,
                    "error": "No shape",
                    "message": f"Object '{obj_name}' has no valid shape",
                }

            shape = obj.Shape

            if face_index is not None:
                # Measure specific face
                if face_index < 0 or face_index >= len(shape.Faces):
                    return {
                        "success": False,
                        "error": "Invalid face index",
                        "message": f"Face index {face_index} is out of range (0-{len(shape.Faces)-1})",
                    }

                face = shape.Faces[face_index]
                area = face.Area

                return {
                    "success": True,
                    "message": f"Area of face {face_index}: {round(area, 2)} mm²",
                    "properties": {
                        "area_mm2": round(area, 2),
                        "area_cm2": round(area / 100, 4),
                        "area_m2": round(area / 1e6, 6),
                        "face_index": face_index,
                        "total_faces": len(shape.Faces),
                        "face_type": face.Surface.__class__.__name__,
                    },
                }
            else:
                # Measure total surface area
                area = shape.Area

                # Get face breakdown
                face_areas = [round(face.Area, 2) for face in shape.Faces]

                return {
                    "success": True,
                    "message": f"Total surface area of {obj_name}: {round(area, 2)} mm²",
                    "properties": {
                        "area_mm2": round(area, 2),
                        "area_cm2": round(area / 100, 4),
                        "area_m2": round(area / 1e6, 6),
                        "num_faces": len(shape.Faces),
                        "face_areas": face_areas,
                        "largest_face_area": max(face_areas) if face_areas else 0,
                        "smallest_face_area": min(face_areas) if face_areas else 0,
                    },
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to measure area: {str(e)}",
            }

    def measure_bounding_box(self, obj_name: str) -> Dict[str, Any]:
        """Measure bounding box dimensions of an object.

        Args:
            obj_name: Name of object to measure

        Returns:
            Dictionary with measurement result
        """
        try:
            doc = App.ActiveDocument
            if not doc:
                return {
                    "success": False,
                    "error": "No active document",
                    "message": "No active document found",
                }

            obj = self._get_object(obj_name)
            if not obj:
                return {
                    "success": False,
                    "error": f"Object '{obj_name}' not found",
                    "message": f"Object '{obj_name}' not found in document",
                }

            if not hasattr(obj, "Shape") or not obj.Shape:
                return {
                    "success": False,
                    "error": "No shape",
                    "message": f"Object '{obj_name}' has no valid shape",
                }

            bbox = obj.Shape.BoundBox

            # Calculate dimensions
            length = bbox.XLength
            width = bbox.YLength
            height = bbox.ZLength
            diagonal = bbox.DiagonalLength

            return {
                "success": True,
                "message": f"Bounding box of {obj_name}: {round(length, 2)} x {round(width, 2)} x {round(height, 2)} mm",
                "properties": {
                    "length": round(length, 3),
                    "width": round(width, 3),
                    "height": round(height, 3),
                    "diagonal": round(diagonal, 3),
                    "min_point": (
                        round(bbox.XMin, 3),
                        round(bbox.YMin, 3),
                        round(bbox.ZMin, 3),
                    ),
                    "max_point": (
                        round(bbox.XMax, 3),
                        round(bbox.YMax, 3),
                        round(bbox.ZMax, 3),
                    ),
                    "center": (
                        round(bbox.Center.x, 3),
                        round(bbox.Center.y, 3),
                        round(bbox.Center.z, 3),
                    ),
                    "volume": round(length * width * height, 2),
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to measure bounding box: {str(e)}",
            }

    def measure_edge_length(
        self, obj_name: str, edge_index: int = None
    ) -> Dict[str, Any]:
        """Measure length of edges in an object.

        Args:
            obj_name: Name of object to measure
            edge_index: Optional index of specific edge to measure

        Returns:
            Dictionary with measurement result
        """
        try:
            doc = App.ActiveDocument
            if not doc:
                return {
                    "success": False,
                    "error": "No active document",
                    "message": "No active document found",
                }

            obj = self._get_object(obj_name)
            if not obj:
                return {
                    "success": False,
                    "error": f"Object '{obj_name}' not found",
                    "message": f"Object '{obj_name}' not found in document",
                }

            if not hasattr(obj, "Shape") or not obj.Shape:
                return {
                    "success": False,
                    "error": "No shape",
                    "message": f"Object '{obj_name}' has no valid shape",
                }

            shape = obj.Shape

            if edge_index is not None:
                # Measure specific edge
                if edge_index < 0 or edge_index >= len(shape.Edges):
                    return {
                        "success": False,
                        "error": "Invalid edge index",
                        "message": f"Edge index {edge_index} is out of range (0-{len(shape.Edges)-1})",
                    }

                edge = shape.Edges[edge_index]
                length = edge.Length

                # Get edge type
                curve = edge.Curve
                edge_type = curve.__class__.__name__

                return {
                    "success": True,
                    "message": f"Length of edge {edge_index}: {round(length, 3)} mm",
                    "properties": {
                        "length": round(length, 3),
                        "edge_index": edge_index,
                        "edge_type": edge_type,
                        "is_closed": edge.isClosed(),
                        "start_point": (
                            round(edge.firstVertex().X, 3),
                            round(edge.firstVertex().Y, 3),
                            round(edge.firstVertex().Z, 3),
                        ),
                        "end_point": (
                            round(edge.lastVertex().X, 3),
                            round(edge.lastVertex().Y, 3),
                            round(edge.lastVertex().Z, 3),
                        ),
                    },
                }
            else:
                # Measure all edges
                edge_lengths = [round(edge.Length, 3) for edge in shape.Edges]
                total_length = sum(edge_lengths)

                return {
                    "success": True,
                    "message": f"Total edge length of {obj_name}: {round(total_length, 3)} mm",
                    "properties": {
                        "total_length": round(total_length, 3),
                        "num_edges": len(shape.Edges),
                        "edge_lengths": edge_lengths,
                        "longest_edge": max(edge_lengths) if edge_lengths else 0,
                        "shortest_edge": min(edge_lengths) if edge_lengths else 0,
                        "average_edge": (
                            round(total_length / len(edge_lengths), 3)
                            if edge_lengths
                            else 0
                        ),
                    },
                }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to measure edge length: {str(e)}",
            }

    def get_available_measurements(self) -> Dict[str, Any]:
        """Get list of available measurement types.

        Returns:
            Dictionary with available measurements and their parameters
        """
        return {
            "measurements": {
                "distance": {
                    "description": "Measure distance between two points or objects",
                    "parameters": ["point1", "point2"],
                },
                "angle": {
                    "description": "Measure angle between objects or three points",
                    "parameters": [
                        "obj1_name",
                        "obj2_name",
                        "obj3_name",
                        "vertex_mode",
                    ],
                },
                "volume": {
                    "description": "Measure volume of a solid object",
                    "parameters": ["obj_name"],
                },
                "area": {
                    "description": "Measure surface area of object or face",
                    "parameters": ["obj_name", "face_index"],
                },
                "bounding_box": {
                    "description": "Measure bounding box dimensions",
                    "parameters": ["obj_name"],
                },
                "edge_length": {
                    "description": "Measure edge lengths",
                    "parameters": ["obj_name", "edge_index"],
                },
            }
        }
