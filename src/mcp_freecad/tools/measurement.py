from typing import Dict, Any, Optional, List, Tuple
import logging
import math

from ..tools.base import ToolProvider

logger = logging.getLogger(__name__)

class MeasurementToolProvider(ToolProvider):
    """Tool provider for measuring distances, areas, volumes, and angles in CAD models."""
    
    def __init__(self, freecad_app=None):
        """
        Initialize the measurement tool provider.
        
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
                logger.info("Connected to FreeCAD for measurements")
            except ImportError:
                logger.warning("Could not import FreeCAD. Make sure it's installed and in your Python path.")
                self.app = None
                self.Part = None
        else:
            try:
                import Part
                self.Part = Part
            except ImportError:
                logger.warning("Could not import Part module. Some functionality may be limited.")
                self.Part = None
    
    async def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a measurement tool.
        
        Args:
            tool_id: The ID of the tool to execute
            params: The parameters for the tool
            
        Returns:
            The result of the tool execution
        """
        logger.info(f"Executing measurement tool: {tool_id}")
        
        # Check if FreeCAD is available
        if self.app is None:
            return {
                "status": "error",
                "message": "FreeCAD is not available. Cannot execute measurement tool.",
                "mock": True
            }
        
        # Handle different tools
        if tool_id == "distance":
            return await self._measure_distance(params)
        elif tool_id == "angle":
            return await self._measure_angle(params)
        elif tool_id == "area":
            return await self._measure_area(params)
        elif tool_id == "volume":
            return await self._measure_volume(params)
        elif tool_id == "center_of_mass":
            return await self._measure_center_of_mass(params)
        elif tool_id == "bounding_box":
            return await self._measure_bounding_box(params)
        else:
            logger.error(f"Unknown tool ID: {tool_id}")
            return {
                "status": "error",
                "message": f"Unknown tool ID: {tool_id}"
            }
    
    async def _measure_distance(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Measure the distance between two points, edges, or faces."""
        try:
            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"status": "error", "message": "No active document"}
            
            # Get measurement parameters
            point1 = params.get("point1")
            point2 = params.get("point2")
            object1 = params.get("object1")
            object2 = params.get("object2")
            subobject1 = params.get("subobject1")
            subobject2 = params.get("subobject2")
            
            # Check if we have enough information to perform a measurement
            if point1 and point2:
                # Measure distance between two points
                if isinstance(point1, list) and isinstance(point2, list) and len(point1) == 3 and len(point2) == 3:
                    p1 = self.app.Vector(point1[0], point1[1], point1[2])
                    p2 = self.app.Vector(point2[0], point2[1], point2[2])
                    
                    distance = p1.distanceToPoint(p2)
                    
                    return {
                        "status": "success",
                        "measurement_type": "distance_point_to_point",
                        "distance": distance,
                        "units": "mm",
                        "point1": point1,
                        "point2": point2
                    }
                else:
                    return {"status": "error", "message": "Invalid point format. Expected [x, y, z]"}
            
            elif object1 and object2:
                # Measure distance between two objects or subobjects
                obj1 = doc.getObject(object1)
                obj2 = doc.getObject(object2)
                
                if not obj1:
                    return {"status": "error", "message": f"Object not found: {object1}"}
                if not obj2:
                    return {"status": "error", "message": f"Object not found: {object2}"}
                
                # Check if objects have shapes
                if not hasattr(obj1, "Shape") or not hasattr(obj2, "Shape"):
                    return {"status": "error", "message": "Objects must have shapes for distance measurement"}
                
                # Get shape or subshape for first object
                shape1 = obj1.Shape
                if subobject1:
                    if subobject1.startswith("Edge"):
                        edge_idx = int(subobject1[4:]) - 1
                        if edge_idx < 0 or edge_idx >= len(shape1.Edges):
                            return {"status": "error", "message": f"Invalid edge index: {subobject1}"}
                        shape1 = shape1.Edges[edge_idx]
                    elif subobject1.startswith("Face"):
                        face_idx = int(subobject1[4:]) - 1
                        if face_idx < 0 or face_idx >= len(shape1.Faces):
                            return {"status": "error", "message": f"Invalid face index: {subobject1}"}
                        shape1 = shape1.Faces[face_idx]
                    elif subobject1.startswith("Vertex"):
                        vertex_idx = int(subobject1[6:]) - 1
                        if vertex_idx < 0 or vertex_idx >= len(shape1.Vertexes):
                            return {"status": "error", "message": f"Invalid vertex index: {subobject1}"}
                        shape1 = shape1.Vertexes[vertex_idx]
                
                # Get shape or subshape for second object
                shape2 = obj2.Shape
                if subobject2:
                    if subobject2.startswith("Edge"):
                        edge_idx = int(subobject2[4:]) - 1
                        if edge_idx < 0 or edge_idx >= len(shape2.Edges):
                            return {"status": "error", "message": f"Invalid edge index: {subobject2}"}
                        shape2 = shape2.Edges[edge_idx]
                    elif subobject2.startswith("Face"):
                        face_idx = int(subobject2[4:]) - 1
                        if face_idx < 0 or face_idx >= len(shape2.Faces):
                            return {"status": "error", "message": f"Invalid face index: {subobject2}"}
                        shape2 = shape2.Faces[face_idx]
                    elif subobject2.startswith("Vertex"):
                        vertex_idx = int(subobject2[6:]) - 1
                        if vertex_idx < 0 or vertex_idx >= len(shape2.Vertexes):
                            return {"status": "error", "message": f"Invalid vertex index: {subobject2}"}
                        shape2 = shape2.Vertexes[vertex_idx]
                
                # Calculate distance between shapes
                distance = shape1.distToShape(shape2)[0]
                
                # Determine measurement type
                measurement_type = "distance_object_to_object"
                if subobject1 or subobject2:
                    measurement_type = "distance_subobject_to_subobject"
                
                return {
                    "status": "success",
                    "measurement_type": measurement_type,
                    "distance": distance,
                    "units": "mm",
                    "object1": object1,
                    "object2": object2,
                    "subobject1": subobject1,
                    "subobject2": subobject2
                }
            
            else:
                return {"status": "error", "message": "Insufficient measurement parameters. Need two points or two objects"}
                
        except Exception as e:
            logger.error(f"Error measuring distance: {e}")
            return {"status": "error", "message": f"Error measuring distance: {str(e)}"}
    
    async def _measure_angle(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Measure the angle between two edges, faces, or vectors."""
        try:
            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"status": "error", "message": "No active document"}
            
            # Get measurement parameters
            vector1 = params.get("vector1")
            vector2 = params.get("vector2")
            object1 = params.get("object1")
            object2 = params.get("object2")
            subobject1 = params.get("subobject1")
            subobject2 = params.get("subobject2")
            
            # Check if we have enough information to perform a measurement
            if vector1 and vector2:
                # Measure angle between two vectors
                if isinstance(vector1, list) and isinstance(vector2, list) and len(vector1) == 3 and len(vector2) == 3:
                    v1 = self.app.Vector(vector1[0], vector1[1], vector1[2])
                    v2 = self.app.Vector(vector2[0], vector2[1], vector2[2])
                    
                    # Calculate angle between vectors
                    angle_rad = v1.getAngle(v2)
                    angle_deg = math.degrees(angle_rad)
                    
                    return {
                        "status": "success",
                        "measurement_type": "angle_vector_to_vector",
                        "angle": angle_deg,
                        "angle_radians": angle_rad,
                        "units": "degrees",
                        "vector1": vector1,
                        "vector2": vector2
                    }
                else:
                    return {"status": "error", "message": "Invalid vector format. Expected [x, y, z]"}
            
            elif object1 and object2 and subobject1 and subobject2:
                # Measure angle between two edges or faces
                obj1 = doc.getObject(object1)
                obj2 = doc.getObject(object2)
                
                if not obj1:
                    return {"status": "error", "message": f"Object not found: {object1}"}
                if not obj2:
                    return {"status": "error", "message": f"Object not found: {object2}"}
                
                # Check if objects have shapes
                if not hasattr(obj1, "Shape") or not hasattr(obj2, "Shape"):
                    return {"status": "error", "message": "Objects must have shapes for angle measurement"}
                
                # Get subshape for first object
                shape1 = obj1.Shape
                if subobject1.startswith("Edge"):
                    edge_idx = int(subobject1[4:]) - 1
                    if edge_idx < 0 or edge_idx >= len(shape1.Edges):
                        return {"status": "error", "message": f"Invalid edge index: {subobject1}"}
                    edge1 = shape1.Edges[edge_idx]
                    v1 = edge1.tangentAt(edge1.FirstParameter)
                elif subobject1.startswith("Face"):
                    face_idx = int(subobject1[4:]) - 1
                    if face_idx < 0 or face_idx >= len(shape1.Faces):
                        return {"status": "error", "message": f"Invalid face index: {subobject1}"}
                    face1 = shape1.Faces[face_idx]
                    v1 = face1.normalAt(0, 0)
                else:
                    return {"status": "error", "message": f"Invalid subobject type: {subobject1}. Use Edge or Face"}
                
                # Get subshape for second object
                shape2 = obj2.Shape
                if subobject2.startswith("Edge"):
                    edge_idx = int(subobject2[4:]) - 1
                    if edge_idx < 0 or edge_idx >= len(shape2.Edges):
                        return {"status": "error", "message": f"Invalid edge index: {subobject2}"}
                    edge2 = shape2.Edges[edge_idx]
                    v2 = edge2.tangentAt(edge2.FirstParameter)
                elif subobject2.startswith("Face"):
                    face_idx = int(subobject2[4:]) - 1
                    if face_idx < 0 or face_idx >= len(shape2.Faces):
                        return {"status": "error", "message": f"Invalid face index: {subobject2}"}
                    face2 = shape2.Faces[face_idx]
                    v2 = face2.normalAt(0, 0)
                else:
                    return {"status": "error", "message": f"Invalid subobject type: {subobject2}. Use Edge or Face"}
                
                # Calculate angle between vectors
                angle_rad = v1.getAngle(v2)
                angle_deg = math.degrees(angle_rad)
                
                # Determine measurement type
                if subobject1.startswith("Edge") and subobject2.startswith("Edge"):
                    measurement_type = "angle_edge_to_edge"
                elif subobject1.startswith("Face") and subobject2.startswith("Face"):
                    measurement_type = "angle_face_to_face"
                else:
                    measurement_type = "angle_subobject_to_subobject"
                
                return {
                    "status": "success",
                    "measurement_type": measurement_type,
                    "angle": angle_deg,
                    "angle_radians": angle_rad,
                    "units": "degrees",
                    "object1": object1,
                    "object2": object2,
                    "subobject1": subobject1,
                    "subobject2": subobject2
                }
            
            else:
                return {"status": "error", "message": "Insufficient measurement parameters. Need two vectors or two subobjects"}
                
        except Exception as e:
            logger.error(f"Error measuring angle: {e}")
            return {"status": "error", "message": f"Error measuring angle: {str(e)}"}
    
    async def _measure_area(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Measure the area of a face or object."""
        try:
            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"status": "error", "message": "No active document"}
            
            # Get measurement parameters
            object_name = params.get("object")
            subobject = params.get("subobject")
            
            if not object_name:
                return {"status": "error", "message": "No object specified for area measurement"}
            
            # Get the object
            obj = doc.getObject(object_name)
            if not obj:
                return {"status": "error", "message": f"Object not found: {object_name}"}
            
            # Check if object has a shape
            if not hasattr(obj, "Shape"):
                return {"status": "error", "message": f"Object {object_name} does not have a shape"}
            
            # Measure area
            if subobject:
                # Measure area of a specific face
                if subobject.startswith("Face"):
                    face_idx = int(subobject[4:]) - 1
                    if face_idx < 0 or face_idx >= len(obj.Shape.Faces):
                        return {"status": "error", "message": f"Invalid face index: {subobject}"}
                    
                    face = obj.Shape.Faces[face_idx]
                    area = face.Area
                    
                    return {
                        "status": "success",
                        "measurement_type": "area_face",
                        "area": area,
                        "units": "mm²",
                        "object": object_name,
                        "subobject": subobject
                    }
                else:
                    return {"status": "error", "message": f"Invalid subobject type: {subobject}. Use Face"}
            else:
                # Measure total area of the object
                area = obj.Shape.Area
                
                return {
                    "status": "success",
                    "measurement_type": "area_object",
                    "area": area,
                    "units": "mm²",
                    "object": object_name
                }
                
        except Exception as e:
            logger.error(f"Error measuring area: {e}")
            return {"status": "error", "message": f"Error measuring area: {str(e)}"}
    
    async def _measure_volume(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Measure the volume of an object."""
        try:
            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"status": "error", "message": "No active document"}
            
            # Get measurement parameters
            object_name = params.get("object")
            
            if not object_name:
                return {"status": "error", "message": "No object specified for volume measurement"}
            
            # Get the object
            obj = doc.getObject(object_name)
            if not obj:
                return {"status": "error", "message": f"Object not found: {object_name}"}
            
            # Check if object has a shape
            if not hasattr(obj, "Shape"):
                return {"status": "error", "message": f"Object {object_name} does not have a shape"}
            
            # Check if the shape is a solid
            if len(obj.Shape.Solids) == 0:
                return {"status": "error", "message": f"Object {object_name} is not a solid"}
            
            # Measure volume
            volume = obj.Shape.Volume
            
            return {
                "status": "success",
                "measurement_type": "volume",
                "volume": volume,
                "units": "mm³",
                "object": object_name
            }
                
        except Exception as e:
            logger.error(f"Error measuring volume: {e}")
            return {"status": "error", "message": f"Error measuring volume: {str(e)}"}
    
    async def _measure_center_of_mass(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Measure the center of mass of an object."""
        try:
            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"status": "error", "message": "No active document"}
            
            # Get measurement parameters
            object_name = params.get("object")
            
            if not object_name:
                return {"status": "error", "message": "No object specified for center of mass measurement"}
            
            # Get the object
            obj = doc.getObject(object_name)
            if not obj:
                return {"status": "error", "message": f"Object not found: {object_name}"}
            
            # Check if object has a shape
            if not hasattr(obj, "Shape"):
                return {"status": "error", "message": f"Object {object_name} does not have a shape"}
            
            # Measure center of mass
            center_of_mass = obj.Shape.CenterOfMass
            
            return {
                "status": "success",
                "measurement_type": "center_of_mass",
                "center_of_mass": [center_of_mass.x, center_of_mass.y, center_of_mass.z],
                "units": "mm",
                "object": object_name
            }
                
        except Exception as e:
            logger.error(f"Error measuring center of mass: {e}")
            return {"status": "error", "message": f"Error measuring center of mass: {str(e)}"}
    
    async def _measure_bounding_box(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Measure the bounding box of an object."""
        try:
            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"status": "error", "message": "No active document"}
            
            # Get measurement parameters
            object_name = params.get("object")
            
            if not object_name:
                return {"status": "error", "message": "No object specified for bounding box measurement"}
            
            # Get the object
            obj = doc.getObject(object_name)
            if not obj:
                return {"status": "error", "message": f"Object not found: {object_name}"}
            
            # Check if object has a shape
            if not hasattr(obj, "Shape"):
                return {"status": "error", "message": f"Object {object_name} does not have a shape"}
            
            # Measure bounding box
            bbox = obj.Shape.BoundBox
            
            return {
                "status": "success",
                "measurement_type": "bounding_box",
                "min_corner": [bbox.XMin, bbox.YMin, bbox.ZMin],
                "max_corner": [bbox.XMax, bbox.YMax, bbox.ZMax],
                "size": [bbox.XLength, bbox.YLength, bbox.ZLength],
                "center": [bbox.Center.x, bbox.Center.y, bbox.Center.z],
                "diagonal": bbox.DiagonalLength,
                "units": "mm",
                "object": object_name
            }
                
        except Exception as e:
            logger.error(f"Error measuring bounding box: {e}")
            return {"status": "error", "message": f"Error measuring bounding box: {str(e)}"} 