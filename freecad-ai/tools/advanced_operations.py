"""
Advanced Operations Tool

MCP tool for performing advanced CAD operations in FreeCAD including
extrude, revolve, loft, sweep, pipe, and helix operations.

Author: jango-blockchained
"""

import math
from typing import Any, Dict, List

import FreeCAD as App
import Part


class AdvancedOperationsTool:
    """Tool for performing advanced CAD operations on objects."""

    def __init__(self):
        """Initialize the advanced operations tool."""
        self.name = "advanced_operations"
        self.description = "Perform advanced CAD operations on objects"

    def extrude_profile(
        self,
        profile_name: str,
        direction: tuple = (0, 0, 1),
        distance: float = 10.0,
        name: str = None,
    ) -> Dict[str, Any]:
        """Extrude a 2D profile to create a 3D solid.

        Args:
            profile_name: Name of the 2D profile object in FreeCAD
            direction: Direction vector for extrusion (x, y, z)
            distance: Extrusion distance in mm
            name: Optional object name

        Returns:
            Dictionary with operation result
        """
        try:
            # Parameter validation
            if distance <= 0:
                return {
                    "success": False,
                    "error": "Distance must be positive",
                    "message": f"Invalid distance: {distance}",
                }

            if len(direction) != 3:
                return {
                    "success": False,
                    "error": "Direction must be a 3-element tuple (x, y, z)",
                    "message": f"Invalid direction: {direction}",
                }

            # Normalize direction vector
            dir_vector = App.Vector(*direction)
            if dir_vector.Length == 0:
                return {
                    "success": False,
                    "error": "Direction vector cannot be zero",
                    "message": f"Invalid direction vector: {direction}",
                }
            dir_vector.normalize()

            # Get active document
            doc = App.ActiveDocument
            if not doc:
                return {
                    "success": False,
                    "error": "No active document",
                    "message": "Please create or open a FreeCAD document",
                }

            # Find the profile object
            profile_obj = doc.getObject(profile_name)
            if not profile_obj:
                return {
                    "success": False,
                    "error": f"Profile object '{profile_name}' not found",
                    "message": f"Available objects: {[obj.Name for obj in doc.Objects]}",
                }

            # Get the shape from the profile
            if hasattr(profile_obj, "Shape"):
                profile_shape = profile_obj.Shape
            else:
                return {
                    "success": False,
                    "error": "Profile object has no Shape attribute",
                    "message": f"Object {profile_name} is not a valid geometric object",
                }

            # Check if profile is 2D (has faces or wires)
            if profile_shape.Faces:
                # Use the first face for extrusion
                face = profile_shape.Faces[0]
                extruded_shape = face.extrude(dir_vector * distance)
            elif profile_shape.Wires:
                # Create face from wire and extrude
                wire = profile_shape.Wires[0]
                try:
                    face = Part.Face(wire)
                    extruded_shape = face.extrude(dir_vector * distance)
                except:
                    return {
                        "success": False,
                        "error": "Cannot create face from wire",
                        "message": "Wire may not be closed or may be invalid",
                    }
            else:
                return {
                    "success": False,
                    "error": "Profile must have faces or closed wires",
                    "message": f"Profile {profile_name} has no extrudable geometry",
                }

            # Create FreeCAD object
            obj_name = name or f"Extrude_{profile_name}_{distance}mm"
            extruded_obj = doc.addObject("Part::Feature", obj_name)
            extruded_obj.Shape = extruded_shape
            extruded_obj.Label = obj_name

            # Recompute document
            doc.recompute()

            # Calculate volume
            volume = extruded_shape.Volume

            return {
                "success": True,
                "object_name": extruded_obj.Name,
                "label": extruded_obj.Label,
                "message": f"Extruded {profile_name} by {distance}mm in direction {direction}",
                "properties": {
                    "source_profile": profile_name,
                    "direction": direction,
                    "distance": distance,
                    "volume": round(volume, 2),
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to extrude profile: {str(e)}",
            }

    def revolve_profile(
        self,
        profile_name: str,
        axis_point: tuple = (0, 0, 0),
        axis_direction: tuple = (0, 0, 1),
        angle: float = 360.0,
        name: str = None,
    ) -> Dict[str, Any]:
        """Revolve a 2D profile around an axis to create a 3D solid.

        Args:
            profile_name: Name of the 2D profile object in FreeCAD
            axis_point: Point on the rotation axis (x, y, z)
            axis_direction: Direction of the rotation axis (x, y, z)
            angle: Rotation angle in degrees (0-360)
            name: Optional object name

        Returns:
            Dictionary with operation result
        """
        try:
            # Parameter validation
            if angle <= 0 or angle > 360:
                return {
                    "success": False,
                    "error": "Angle must be between 0 and 360 degrees",
                    "message": f"Invalid angle: {angle}",
                }

            if len(axis_point) != 3 or len(axis_direction) != 3:
                return {
                    "success": False,
                    "error": "Axis point and direction must be 3-element tuples",
                    "message": f"Invalid axis: point={axis_point}, direction={axis_direction}",
                }

            # Normalize axis direction
            axis_vec = App.Vector(*axis_direction)
            if axis_vec.Length == 0:
                return {
                    "success": False,
                    "error": "Axis direction vector cannot be zero",
                    "message": f"Invalid axis direction: {axis_direction}",
                }
            axis_vec.normalize()

            # Get active document
            doc = App.ActiveDocument
            if not doc:
                return {
                    "success": False,
                    "error": "No active document",
                    "message": "Please create or open a FreeCAD document",
                }

            # Find the profile object
            profile_obj = doc.getObject(profile_name)
            if not profile_obj:
                return {
                    "success": False,
                    "error": f"Profile object '{profile_name}' not found",
                    "message": f"Available objects: {[obj.Name for obj in doc.Objects]}",
                }

            # Get the shape from the profile
            if hasattr(profile_obj, "Shape"):
                profile_shape = profile_obj.Shape
            else:
                return {
                    "success": False,
                    "error": "Profile object has no Shape attribute",
                    "message": f"Object {profile_name} is not a valid geometric object",
                }

            # Check if profile is 2D (has faces or wires)
            if profile_shape.Faces:
                # Use the first face for revolution
                face = profile_shape.Faces[0]
                revolved_shape = face.revolve(
                    App.Vector(*axis_point), axis_vec, math.radians(angle)
                )
            elif profile_shape.Wires:
                # Create face from wire and revolve
                wire = profile_shape.Wires[0]
                try:
                    face = Part.Face(wire)
                    revolved_shape = face.revolve(
                        App.Vector(*axis_point), axis_vec, math.radians(angle)
                    )
                except:
                    return {
                        "success": False,
                        "error": "Cannot create face from wire",
                        "message": "Wire may not be closed or may be invalid",
                    }
            else:
                return {
                    "success": False,
                    "error": "Profile must have faces or closed wires",
                    "message": f"Profile {profile_name} has no revolvable geometry",
                }

            # Create FreeCAD object
            obj_name = name or f"Revolve_{profile_name}_{angle}deg"
            revolved_obj = doc.addObject("Part::Feature", obj_name)
            revolved_obj.Shape = revolved_shape
            revolved_obj.Label = obj_name

            # Recompute document
            doc.recompute()

            # Calculate volume
            volume = revolved_shape.Volume

            return {
                "success": True,
                "object_name": revolved_obj.Name,
                "label": revolved_obj.Label,
                "message": f"Revolved {profile_name} by {angle}° around axis at {axis_point}",
                "properties": {
                    "source_profile": profile_name,
                    "axis_point": axis_point,
                    "axis_direction": axis_direction,
                    "angle": angle,
                    "volume": round(volume, 2),
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to revolve profile: {str(e)}",
            }

    def loft_profiles(
        self,
        profile_names: List[str],
        solid: bool = True,
        ruled: bool = False,
        name: str = None,
    ) -> Dict[str, Any]:
        """Create a loft between multiple 2D profiles.

        Args:
            profile_names: List of profile object names in FreeCAD
            solid: Create solid (True) or surface (False)
            ruled: Use ruled surface (True) or smooth (False)
            name: Optional object name

        Returns:
            Dictionary with operation result
        """
        try:
            # Parameter validation
            if len(profile_names) < 2:
                return {
                    "success": False,
                    "error": "At least 2 profiles required for loft",
                    "message": f"Only {len(profile_names)} profiles provided",
                }

            # Get active document
            doc = App.ActiveDocument
            if not doc:
                return {
                    "success": False,
                    "error": "No active document",
                    "message": "Please create or open a FreeCAD document",
                }

            # Collect profile shapes
            profiles = []
            for profile_name in profile_names:
                profile_obj = doc.getObject(profile_name)
                if not profile_obj:
                    return {
                        "success": False,
                        "error": f"Profile object '{profile_name}' not found",
                        "message": f"Available objects: {[obj.Name for obj in doc.Objects]}",
                    }

                if hasattr(profile_obj, "Shape"):
                    profile_shape = profile_obj.Shape
                else:
                    return {
                        "success": False,
                        "error": f"Profile object '{profile_name}' has no Shape attribute",
                        "message": f"Object {profile_name} is not a valid geometric object",
                    }

                # Get wire or face from profile
                if profile_shape.Wires:
                    profiles.append(profile_shape.Wires[0])
                elif profile_shape.Faces:
                    # Get outer wire from face
                    profiles.append(profile_shape.Faces[0].OuterWire)
                else:
                    return {
                        "success": False,
                        "error": f"Profile '{profile_name}' has no wires or faces",
                        "message": f"Profile {profile_name} has no loftable geometry",
                    }

            # Create loft
            try:
                lofted_shape = Part.makeLoft(profiles, solid, ruled)
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Loft operation failed: {str(e)}",
                    "message": "Profiles may be incompatible or incorrectly positioned",
                }

            # Create FreeCAD object
            obj_name = name or f"Loft_{len(profile_names)}profiles"
            lofted_obj = doc.addObject("Part::Feature", obj_name)
            lofted_obj.Shape = lofted_shape
            lofted_obj.Label = obj_name

            # Recompute document
            doc.recompute()

            # Calculate volume (if solid)
            volume = lofted_shape.Volume if solid else 0

            return {
                "success": True,
                "object_name": lofted_obj.Name,
                "label": lofted_obj.Label,
                "message": f"Created loft from {len(profile_names)} profiles",
                "properties": {
                    "source_profiles": profile_names,
                    "solid": solid,
                    "ruled": ruled,
                    "volume": round(volume, 2) if solid else "N/A (surface)",
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create loft: {str(e)}",
            }

    def sweep_profile(
        self, profile_name: str, path_name: str, frenet: bool = False, name: str = None
    ) -> Dict[str, Any]:
        """Sweep a 2D profile along a 3D path.

        Args:
            profile_name: Name of the 2D profile object in FreeCAD
            path_name: Name of the 3D path object in FreeCAD
            frenet: Use Frenet frame orientation (True) or fixed (False)
            name: Optional object name

        Returns:
            Dictionary with operation result
        """
        try:
            # Get active document
            doc = App.ActiveDocument
            if not doc:
                return {
                    "success": False,
                    "error": "No active document",
                    "message": "Please create or open a FreeCAD document",
                }

            # Find the profile object
            profile_obj = doc.getObject(profile_name)
            if not profile_obj:
                return {
                    "success": False,
                    "error": f"Profile object '{profile_name}' not found",
                    "message": f"Available objects: {[obj.Name for obj in doc.Objects]}",
                }

            # Find the path object
            path_obj = doc.getObject(path_name)
            if not path_obj:
                return {
                    "success": False,
                    "error": f"Path object '{path_name}' not found",
                    "message": f"Available objects: {[obj.Name for obj in doc.Objects]}",
                }

            # Get shapes
            if not hasattr(profile_obj, "Shape") or not hasattr(path_obj, "Shape"):
                return {
                    "success": False,
                    "error": "Profile or path object has no Shape attribute",
                    "message": "Objects must be valid geometric objects",
                }

            profile_shape = profile_obj.Shape
            path_shape = path_obj.Shape

            # Get profile wire or face
            if profile_shape.Wires:
                profile_wire = profile_shape.Wires[0]
            elif profile_shape.Faces:
                profile_wire = profile_shape.Faces[0].OuterWire
            else:
                return {
                    "success": False,
                    "error": "Profile must have wires or faces",
                    "message": f"Profile {profile_name} has no sweepable geometry",
                }

            # Get path wire
            if path_shape.Wires:
                path_wire = path_shape.Wires[0]
            elif path_shape.Edges:
                # Create wire from edges
                path_wire = Part.Wire(path_shape.Edges)
            else:
                return {
                    "success": False,
                    "error": "Path must have wires or edges",
                    "message": f"Path {path_name} has no valid path geometry",
                }

            # Create sweep
            try:
                if frenet:
                    swept_shape = Part.makePipeShell(
                        [profile_wire], path_wire, True, True
                    )
                else:
                    swept_shape = Part.makePipeShell(
                        [profile_wire], path_wire, False, False
                    )
            except Exception as e:
                return {
                    "success": False,
                    "error": f"Sweep operation failed: {str(e)}",
                    "message": "Profile and path may be incompatible",
                }

            # Create FreeCAD object
            obj_name = name or f"Sweep_{profile_name}_along_{path_name}"
            swept_obj = doc.addObject("Part::Feature", obj_name)
            swept_obj.Shape = swept_shape
            swept_obj.Label = obj_name

            # Recompute document
            doc.recompute()

            # Calculate volume
            volume = swept_shape.Volume

            return {
                "success": True,
                "object_name": swept_obj.Name,
                "label": swept_obj.Label,
                "message": f"Swept {profile_name} along {path_name}",
                "properties": {
                    "source_profile": profile_name,
                    "path": path_name,
                    "frenet": frenet,
                    "volume": round(volume, 2),
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create sweep: {str(e)}",
            }

    def create_helix(
        self,
        radius: float = 5.0,
        pitch: float = 2.0,
        height: float = 20.0,
        direction: str = "right",
        position: tuple = (0, 0, 0),
        name: str = None,
    ) -> Dict[str, Any]:
        """Create a helical curve.

        Args:
            radius: Helix radius in mm
            pitch: Distance between turns in mm
            height: Total height of helix in mm
            direction: Helix direction ("right" or "left")
            position: (x, y, z) position tuple
            name: Optional object name

        Returns:
            Dictionary with operation result
        """
        try:
            # Parameter validation
            if radius <= 0:
                return {
                    "success": False,
                    "error": "Radius must be positive",
                    "message": f"Invalid radius: {radius}",
                }

            if pitch <= 0:
                return {
                    "success": False,
                    "error": "Pitch must be positive",
                    "message": f"Invalid pitch: {pitch}",
                }

            if height <= 0:
                return {
                    "success": False,
                    "error": "Height must be positive",
                    "message": f"Invalid height: {height}",
                }

            if direction not in ["right", "left"]:
                return {
                    "success": False,
                    "error": "Direction must be 'right' or 'left'",
                    "message": f"Invalid direction: {direction}",
                }

            # Get or create active document
            doc = App.ActiveDocument
            if not doc:
                doc = App.newDocument("Untitled")

            # Calculate number of turns
            turns = height / pitch

            # Create helix
            # FreeCAD's makeHelix: radius, pitch, height, angle (optional), left_handed (optional)
            left_handed = direction == "left"
            helix_shape = Part.makeHelix(pitch, height, radius, 0, left_handed)

            # Create FreeCAD object
            obj_name = name or f"Helix_R{radius}_P{pitch}_H{height}_{direction}"
            helix_obj = doc.addObject("Part::Feature", obj_name)
            helix_obj.Shape = helix_shape
            helix_obj.Label = obj_name

            # Set position
            if position != (0, 0, 0):
                helix_obj.Placement.Base = App.Vector(*position)

            # Recompute document
            doc.recompute()

            # Calculate length
            length = helix_shape.Length

            return {
                "success": True,
                "object_name": helix_obj.Name,
                "label": helix_obj.Label,
                "message": f"Created {direction}-handed helix R{radius}mm P{pitch}mm H{height}mm at {position}",
                "properties": {
                    "radius": radius,
                    "pitch": pitch,
                    "height": height,
                    "direction": direction,
                    "turns": round(turns, 2),
                    "length": round(length, 2),
                    "position": position,
                },
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to create helix: {str(e)}",
            }

    def get_available_operations(self) -> Dict[str, Any]:
        """Get list of available advanced operations.

        Returns:
            Dictionary with available operations and their parameters
        """
        return {
            "advanced_operations": {
                "extrude": {
                    "description": "Extrude a 2D profile to create a 3D solid",
                    "parameters": ["profile_name", "direction", "distance", "name"],
                },
                "revolve": {
                    "description": "Revolve a 2D profile around an axis",
                    "parameters": [
                        "profile_name",
                        "axis_point",
                        "axis_direction",
                        "angle",
                        "name",
                    ],
                },
                "loft": {
                    "description": "Create a loft between multiple 2D profiles",
                    "parameters": ["profile_names", "solid", "ruled", "name"],
                },
                "sweep": {
                    "description": "Sweep a 2D profile along a 3D path",
                    "parameters": ["profile_name", "path_name", "frenet", "name"],
                },
                "helix": {
                    "description": "Create a helical curve",
                    "parameters": [
                        "radius",
                        "pitch",
                        "height",
                        "direction",
                        "position",
                        "name",
                    ],
                },
            }
        }
