import logging
from typing import Any, Dict, Optional
from urllib.parse import urlparse

from .base import ResourceProvider

logger = logging.getLogger(__name__)


class ConstraintResourceProvider(ResourceProvider):
    """Resource provider for constraints in CAD models."""

    def __init__(self, freecad_app=None):
        """
        Initialize the constraint resource provider.

        Args:
            freecad_app: Optional FreeCAD application instance. If None, will try to import FreeCAD.
        """
        # self.extractor = CADContextExtractor(freecad_app)  # Not needed for constraint resources
        self.app = freecad_app

        if self.app is None:
            try:
                import FreeCAD

                self.app = FreeCAD
                logger.info("Connected to FreeCAD for constraint data")
            except ImportError:
                logger.warning(
                    "Could not import FreeCAD. Make sure it's installed and in your Python path."
                )
                self.app = None

    async def get_resource(
        self, uri: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve constraint data from the CAD model.

        Args:
            uri: The resource URI in format "cad://constraints/[resource_type]/[object_name]"
            params: Optional parameters for the constraints request

        Returns:
            The constraint data
        """
        logger.info(f"Retrieving constraint resource: {uri}")

        # Parse the URI
        parsed_uri = urlparse(uri)

        if parsed_uri.scheme != "cad":
            raise ValueError(f"Invalid URI scheme: {parsed_uri.scheme}, expected 'cad'")

        path_parts = parsed_uri.path.strip("/").split("/")

        if len(path_parts) < 1 or path_parts[0] != "constraints":
            raise ValueError(
                f"Invalid URI format: {uri}, expected 'cad://constraints/...'"
            )

        # Handle different resource types
        if len(path_parts) == 1:
            # Return summary of all constraints in active document
            return await self._get_all_constraints()

        resource_type = path_parts[1]

        if resource_type == "sketch":
            # Return constraints for a specific sketch
            if len(path_parts) < 3:
                return {"error": "No sketch specified"}
            return await self._get_sketch_constraints(path_parts[2])
        elif resource_type == "assembly":
            # Return assembly constraints
            if len(path_parts) < 3:
                # Return all assembly constraints in the document
                return await self._get_assembly_constraints()
            # Return assembly constraints for a specific object
            return await self._get_object_assembly_constraints(path_parts[2])
        elif resource_type == "types":
            # Return available constraint types
            return await self._get_constraint_types()
        else:
            raise ValueError(f"Unknown resource type: {resource_type}")

    async def _get_all_constraints(self) -> Dict[str, Any]:
        """Get summary of all constraints in the active document."""
        if self.app is None:
            return self._mock_all_constraints()

        try:
            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"error": "No active document"}

            # Collect all sketch constraints
            sketch_constraints = []
            assembly_constraints = []

            # Find all sketch objects
            for obj in doc.Objects:
                if obj.TypeId == "Sketcher::SketchObject":
                    sketch_name = obj.Name
                    constraints_count = (
                        len(obj.Constraints) if hasattr(obj, "Constraints") else 0
                    )

                    sketch_constraints.append(
                        {
                            "sketch_name": sketch_name,
                            "label": obj.Label,
                            "constraints_count": constraints_count,
                        }
                    )

            # Find all assembly constraints (if Assembly workbench is available)
            # This is workbench-specific and would need to be adapted based on which
            # assembly workbench is being used (A2Plus, Assembly4, etc.)
            for obj in doc.Objects:
                if hasattr(obj, "Type") and "Constraint" in obj.Type:
                    if any(asm_type in obj.Type for asm_type in ["Assembly", "A2p"]):
                        assembly_constraints.append(
                            {"name": obj.Name, "label": obj.Label, "type": obj.Type}
                        )

            return {
                "resource_type": "all_constraints",
                "document": doc.Name,
                "sketch_constraints": {
                    "count": len(sketch_constraints),
                    "sketches": sketch_constraints,
                },
                "assembly_constraints": {
                    "count": len(assembly_constraints),
                    "constraints": assembly_constraints,
                },
            }

        except Exception as e:
            logger.error(f"Error getting all constraints: {e}")
            return {"error": f"Error getting all constraints: {str(e)}"}

    def _mock_all_constraints(self) -> Dict[str, Any]:
        """Provide mock constraint data when FreeCAD is not available."""
        return {
            "resource_type": "all_constraints",
            "document": "Document",
            "sketch_constraints": {
                "count": 2,
                "sketches": [
                    {
                        "sketch_name": "Sketch",
                        "label": "Sketch",
                        "constraints_count": 12,
                    },
                    {
                        "sketch_name": "Sketch001",
                        "label": "Sketch001",
                        "constraints_count": 8,
                    },
                ],
            },
            "assembly_constraints": {
                "count": 3,
                "constraints": [
                    {
                        "name": "Constraint001",
                        "label": "FixedConstraint",
                        "type": "Assembly2Constraint",
                    },
                    {
                        "name": "Constraint002",
                        "label": "PlaneConstraint",
                        "type": "Assembly2Constraint",
                    },
                    {
                        "name": "Constraint003",
                        "label": "AxisConstraint",
                        "type": "Assembly2Constraint",
                    },
                ],
            },
            "note": "Mock data (FreeCAD not available)",
        }

    async def _get_sketch_constraints(self, sketch_name: str) -> Dict[str, Any]:
        """Get constraints for a specific sketch."""
        if self.app is None:
            return self._mock_sketch_constraints(sketch_name)

        try:
            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"error": "No active document"}

            # Get the sketch object
            sketch = doc.getObject(sketch_name)
            if not sketch:
                return {"error": f"Sketch not found: {sketch_name}"}

            if sketch.TypeId != "Sketcher::SketchObject":
                return {"error": f"Object is not a sketch: {sketch_name}"}

            # Get constraints
            constraints = []

            if hasattr(sketch, "Constraints"):
                for i, constraint in enumerate(sketch.Constraints):
                    constraint_data = {
                        "index": i,
                        "name": constraint.Name,
                        "type": constraint.Type,
                        "driven": getattr(constraint, "Driven", False),
                    }

                    # Add type-specific properties
                    if constraint.Type == "Distance":
                        constraint_data["value"] = constraint.Value
                        constraint_data["first_pos"] = getattr(constraint, "First", -1)
                        constraint_data["second_pos"] = getattr(
                            constraint, "Second", -1
                        )
                    elif constraint.Type == "Angle":
                        constraint_data["value"] = constraint.Value
                        constraint_data["first_pos"] = getattr(constraint, "First", -1)
                        constraint_data["second_pos"] = getattr(
                            constraint, "Second", -1
                        )
                    elif constraint.Type in ["Horizontal", "Vertical"]:
                        constraint_data["pos"] = getattr(constraint, "First", -1)
                    elif constraint.Type in ["Coincident", "Parallel", "Perpendicular"]:
                        constraint_data["first_pos"] = getattr(constraint, "First", -1)
                        constraint_data["second_pos"] = getattr(
                            constraint, "Second", -1
                        )

                    constraints.append(constraint_data)

            # Get geometry elements in the sketch
            geometry = []

            if hasattr(sketch, "Geometry"):
                for i, geo in enumerate(sketch.Geometry):
                    geo_type = geo.TypeId.split(":")[-1]  # Extract type from TypeId
                    geo_data = {
                        "index": i,
                        "type": geo_type,
                        "construction": geo.Construction,
                    }

                    # Add type-specific properties
                    if geo_type == "LineSegment":
                        geo_data["start"] = [
                            geo.StartPoint.x,
                            geo.StartPoint.y,
                            geo.StartPoint.z,
                        ]
                        geo_data["end"] = [
                            geo.EndPoint.x,
                            geo.EndPoint.y,
                            geo.EndPoint.z,
                        ]
                    elif geo_type == "Circle":
                        geo_data["center"] = [geo.Center.x, geo.Center.y, geo.Center.z]
                        geo_data["radius"] = geo.Radius
                    elif geo_type == "Arc":
                        geo_data["center"] = [geo.Center.x, geo.Center.y, geo.Center.z]
                        geo_data["radius"] = geo.Radius
                        geo_data["start_angle"] = geo.FirstAngle
                        geo_data["end_angle"] = geo.LastAngle

                    geometry.append(geo_data)

            return {
                "resource_type": "sketch_constraints",
                "sketch_name": sketch_name,
                "label": sketch.Label,
                "constraints": {"count": len(constraints), "items": constraints},
                "geometry": {"count": len(geometry), "items": geometry},
            }

        except Exception as e:
            logger.error(f"Error getting sketch constraints: {e}")
            return {"error": f"Error getting sketch constraints: {str(e)}"}

    def _mock_sketch_constraints(self, sketch_name: str) -> Dict[str, Any]:
        """Provide mock sketch constraint data when FreeCAD is not available."""
        return {
            "resource_type": "sketch_constraints",
            "sketch_name": sketch_name,
            "label": sketch_name,
            "constraints": {
                "count": 6,
                "items": [
                    {
                        "index": 0,
                        "name": "Horizontal1",
                        "type": "Horizontal",
                        "driven": False,
                        "pos": 0,
                    },
                    {
                        "index": 1,
                        "name": "Vertical1",
                        "type": "Vertical",
                        "driven": False,
                        "pos": 1,
                    },
                    {
                        "index": 2,
                        "name": "Distance1",
                        "type": "Distance",
                        "driven": False,
                        "value": 10.0,
                        "first_pos": 0,
                        "second_pos": -1,
                    },
                    {
                        "index": 3,
                        "name": "Distance2",
                        "type": "Distance",
                        "driven": False,
                        "value": 20.0,
                        "first_pos": 1,
                        "second_pos": -1,
                    },
                    {
                        "index": 4,
                        "name": "Coincident1",
                        "type": "Coincident",
                        "driven": False,
                        "first_pos": 0,
                        "second_pos": 1,
                    },
                    {
                        "index": 5,
                        "name": "Parallel1",
                        "type": "Parallel",
                        "driven": False,
                        "first_pos": 2,
                        "second_pos": 3,
                    },
                ],
            },
            "geometry": {
                "count": 4,
                "items": [
                    {
                        "index": 0,
                        "type": "LineSegment",
                        "construction": False,
                        "start": [0.0, 0.0, 0.0],
                        "end": [10.0, 0.0, 0.0],
                    },
                    {
                        "index": 1,
                        "type": "LineSegment",
                        "construction": False,
                        "start": [10.0, 0.0, 0.0],
                        "end": [10.0, 20.0, 0.0],
                    },
                    {
                        "index": 2,
                        "type": "LineSegment",
                        "construction": False,
                        "start": [10.0, 20.0, 0.0],
                        "end": [0.0, 20.0, 0.0],
                    },
                    {
                        "index": 3,
                        "type": "LineSegment",
                        "construction": False,
                        "start": [0.0, 20.0, 0.0],
                        "end": [0.0, 0.0, 0.0],
                    },
                ],
            },
            "note": "Mock data (FreeCAD not available)",
        }

    async def _get_assembly_constraints(self) -> Dict[str, Any]:
        """Get all assembly constraints in the active document."""
        if self.app is None:
            return self._mock_assembly_constraints()

        try:
            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"error": "No active document"}

            # Assembly constraints are workbench-specific
            # This implementation is based on common patterns found in Assembly workbenches
            # It would need to be adapted based on which assembly workbench is being used

            constraints = []

            # Look for objects that might be assembly constraints
            for obj in doc.Objects:
                if hasattr(obj, "Type") and "Constraint" in obj.Type:
                    if any(asm_type in obj.Type for asm_type in ["Assembly", "A2p"]):
                        constraint_data = {
                            "name": obj.Name,
                            "label": obj.Label,
                            "type": obj.Type,
                        }

                        # Get linked objects (different workbenches handle this differently)
                        linked_objects = []

                        # A2Plus approach
                        if hasattr(obj, "Object1"):
                            linked_objects.append(obj.Object1)
                        if hasattr(obj, "Object2"):
                            linked_objects.append(obj.Object2)

                        # Assembly4 approach
                        if hasattr(obj, "References"):
                            for ref in obj.References:
                                linked_objects.append(ref[0].Name)

                        constraint_data["linked_objects"] = linked_objects

                        # Get constraint parameters
                        parameters = {}
                        for prop in obj.PropertiesList:
                            if prop not in [
                                "Name",
                                "Label",
                                "Type",
                                "Object1",
                                "Object2",
                                "References",
                            ]:
                                try:
                                    parameters[prop] = getattr(obj, prop)
                                except:
                                    pass

                        constraint_data["parameters"] = parameters

                        constraints.append(constraint_data)

            return {
                "resource_type": "assembly_constraints",
                "document": doc.Name,
                "count": len(constraints),
                "constraints": constraints,
            }

        except Exception as e:
            logger.error(f"Error getting assembly constraints: {e}")
            return {"error": f"Error getting assembly constraints: {str(e)}"}

    def _mock_assembly_constraints(self) -> Dict[str, Any]:
        """Provide mock assembly constraint data when FreeCAD is not available."""
        return {
            "resource_type": "assembly_constraints",
            "document": "Document",
            "count": 3,
            "constraints": [
                {
                    "name": "Constraint001",
                    "label": "FixedConstraint",
                    "type": "Assembly2Constraint",
                    "linked_objects": ["Part001"],
                    "parameters": {"Offset": 0.0},
                },
                {
                    "name": "Constraint002",
                    "label": "PlaneConstraint",
                    "type": "Assembly2Constraint",
                    "linked_objects": ["Part001", "Part002"],
                    "parameters": {
                        "Offset": 0.0,
                        "Plane1": "XY_Plane",
                        "Plane2": "XY_Plane",
                    },
                },
                {
                    "name": "Constraint003",
                    "label": "AxisConstraint",
                    "type": "Assembly2Constraint",
                    "linked_objects": ["Part002", "Part003"],
                    "parameters": {"Offset": 0.0, "Axis1": "X_Axis", "Axis2": "X_Axis"},
                },
            ],
            "note": "Mock data (FreeCAD not available)",
        }

    async def _get_object_assembly_constraints(
        self, object_name: str
    ) -> Dict[str, Any]:
        """Get assembly constraints for a specific object."""
        if self.app is None:
            return self._mock_object_assembly_constraints(object_name)

        try:
            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"error": "No active document"}

            # Get the object
            obj = doc.getObject(object_name)
            if not obj:
                return {"error": f"Object not found: {object_name}"}

            # Find constraints related to this object
            constraints = []

            for doc_obj in doc.Objects:
                if hasattr(doc_obj, "Type") and "Constraint" in doc_obj.Type:
                    if any(
                        asm_type in doc_obj.Type for asm_type in ["Assembly", "A2p"]
                    ):
                        is_related = False

                        # A2Plus approach
                        if hasattr(doc_obj, "Object1") and doc_obj.Object1 == obj.Name:
                            is_related = True
                        if hasattr(doc_obj, "Object2") and doc_obj.Object2 == obj.Name:
                            is_related = True

                        # Assembly4 approach
                        if hasattr(doc_obj, "References"):
                            for ref in doc_obj.References:
                                if ref[0].Name == obj.Name:
                                    is_related = True
                                    break

                        if is_related:
                            constraint_data = {
                                "name": doc_obj.Name,
                                "label": doc_obj.Label,
                                "type": doc_obj.Type,
                            }

                            # Get linked objects
                            linked_objects = []

                            # A2Plus approach
                            if hasattr(doc_obj, "Object1"):
                                linked_objects.append(doc_obj.Object1)
                            if hasattr(doc_obj, "Object2"):
                                linked_objects.append(doc_obj.Object2)

                            # Assembly4 approach
                            if hasattr(doc_obj, "References"):
                                for ref in doc_obj.References:
                                    linked_objects.append(ref[0].Name)

                            constraint_data["linked_objects"] = linked_objects

                            # Get constraint parameters
                            parameters = {}
                            for prop in doc_obj.PropertiesList:
                                if prop not in [
                                    "Name",
                                    "Label",
                                    "Type",
                                    "Object1",
                                    "Object2",
                                    "References",
                                ]:
                                    try:
                                        parameters[prop] = getattr(doc_obj, prop)
                                    except:
                                        pass

                            constraint_data["parameters"] = parameters

                            constraints.append(constraint_data)

            return {
                "resource_type": "object_assembly_constraints",
                "object": object_name,
                "label": obj.Label,
                "count": len(constraints),
                "constraints": constraints,
            }

        except Exception as e:
            logger.error(f"Error getting object assembly constraints: {e}")
            return {"error": f"Error getting object assembly constraints: {str(e)}"}

    def _mock_object_assembly_constraints(self, object_name: str) -> Dict[str, Any]:
        """Provide mock object assembly constraint data when FreeCAD is not available."""
        return {
            "resource_type": "object_assembly_constraints",
            "object": object_name,
            "label": object_name,
            "count": 2,
            "constraints": [
                {
                    "name": "Constraint001",
                    "label": "PlaneConstraint",
                    "type": "Assembly2Constraint",
                    "linked_objects": [object_name, "Part002"],
                    "parameters": {
                        "Offset": 0.0,
                        "Plane1": "XY_Plane",
                        "Plane2": "XY_Plane",
                    },
                },
                {
                    "name": "Constraint002",
                    "label": "AxisConstraint",
                    "type": "Assembly2Constraint",
                    "linked_objects": [object_name, "Part003"],
                    "parameters": {"Offset": 0.0, "Axis1": "X_Axis", "Axis2": "X_Axis"},
                },
            ],
            "note": "Mock data (FreeCAD not available)",
        }

    async def _get_constraint_types(self) -> Dict[str, Any]:
        """Get available constraint types."""
        if self.app is None:
            return self._mock_constraint_types()

        try:
            # This information is largely static and based on FreeCAD's capabilities
            # We'll return a comprehensive list of constraint types for different workbenches

            sketch_constraints = [
                {
                    "name": "Coincident",
                    "description": "Forces two points to be coincident",
                    "workbench": "Sketcher",
                },
                {
                    "name": "Point on Object",
                    "description": "Forces a point to lie on another object",
                    "workbench": "Sketcher",
                },
                {
                    "name": "Horizontal",
                    "description": "Forces a line segment to be horizontal",
                    "workbench": "Sketcher",
                },
                {
                    "name": "Vertical",
                    "description": "Forces a line segment to be vertical",
                    "workbench": "Sketcher",
                },
                {
                    "name": "Parallel",
                    "description": "Forces two line segments to be parallel",
                    "workbench": "Sketcher",
                },
                {
                    "name": "Perpendicular",
                    "description": "Forces two line segments to be perpendicular",
                    "workbench": "Sketcher",
                },
                {
                    "name": "Tangent",
                    "description": "Forces an edge to be tangent to another edge",
                    "workbench": "Sketcher",
                },
                {
                    "name": "Equal",
                    "description": "Forces two parameters to be equal",
                    "workbench": "Sketcher",
                },
                {
                    "name": "Symmetric",
                    "description": "Forces two points to be symmetric with respect to a line",
                    "workbench": "Sketcher",
                },
                {
                    "name": "Distance",
                    "description": "Sets the distance between two elements",
                    "workbench": "Sketcher",
                },
                {
                    "name": "Angle",
                    "description": "Sets the angle between two line segments",
                    "workbench": "Sketcher",
                },
            ]

            assembly_constraints = [
                {
                    "name": "Fixed",
                    "description": "Fixes an object in the assembly",
                    "workbench": "Assembly",
                },
                {
                    "name": "Plane Alignment",
                    "description": "Aligns planes between two objects",
                    "workbench": "Assembly",
                },
                {
                    "name": "Axis Alignment",
                    "description": "Aligns axes between two objects",
                    "workbench": "Assembly",
                },
                {
                    "name": "Point on Point",
                    "description": "Aligns points between two objects",
                    "workbench": "Assembly",
                },
                {
                    "name": "Point on Line",
                    "description": "Places a point on a line",
                    "workbench": "Assembly",
                },
                {
                    "name": "Point on Plane",
                    "description": "Places a point on a plane",
                    "workbench": "Assembly",
                },
            ]

            return {
                "resource_type": "constraint_types",
                "sketch_constraints": sketch_constraints,
                "assembly_constraints": assembly_constraints,
            }

        except Exception as e:
            logger.error(f"Error getting constraint types: {e}")
            return {"error": f"Error getting constraint types: {str(e)}"}

    def _mock_constraint_types(self) -> Dict[str, Any]:
        """Provide mock constraint types when FreeCAD is not available."""
        return {
            "resource_type": "constraint_types",
            "sketch_constraints": [
                {
                    "name": "Coincident",
                    "description": "Forces two points to be coincident",
                    "workbench": "Sketcher",
                },
                {
                    "name": "Point on Object",
                    "description": "Forces a point to lie on another object",
                    "workbench": "Sketcher",
                },
                {
                    "name": "Horizontal",
                    "description": "Forces a line segment to be horizontal",
                    "workbench": "Sketcher",
                },
                {
                    "name": "Vertical",
                    "description": "Forces a line segment to be vertical",
                    "workbench": "Sketcher",
                },
                {
                    "name": "Parallel",
                    "description": "Forces two line segments to be parallel",
                    "workbench": "Sketcher",
                },
                {
                    "name": "Perpendicular",
                    "description": "Forces two line segments to be perpendicular",
                    "workbench": "Sketcher",
                },
            ],
            "assembly_constraints": [
                {
                    "name": "Fixed",
                    "description": "Fixes an object in the assembly",
                    "workbench": "Assembly",
                },
                {
                    "name": "Plane Alignment",
                    "description": "Aligns planes between two objects",
                    "workbench": "Assembly",
                },
                {
                    "name": "Axis Alignment",
                    "description": "Aligns axes between two objects",
                    "workbench": "Assembly",
                },
            ],
            "note": "Mock data (FreeCAD not available)",
        }
