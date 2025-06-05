"""Tool Capabilities - Define tool capabilities and registry"""

from enum import Enum
from typing import Dict, List, Set, Any, Optional
from dataclasses import dataclass
import FreeCAD


class CapabilityType(Enum):
    """Types of tool capabilities"""
    CREATE_GEOMETRY = "create_geometry"
    MODIFY_GEOMETRY = "modify_geometry"
    ANALYZE_GEOMETRY = "analyze_geometry"
    BOOLEAN_OPERATIONS = "boolean_operations"
    TRANSFORMATIONS = "transformations"
    MEASUREMENTS = "measurements"
    EXPORT_IMPORT = "export_import"
    ADVANCED_MODELING = "advanced_modeling"
    SURFACE_OPERATIONS = "surface_operations"
    ASSEMBLY_OPERATIONS = "assembly_operations"


@dataclass
class ToolCapability:
    """Represents a single tool capability"""
    capability_type: CapabilityType
    name: str
    description: str
    input_types: List[str]
    output_types: List[str]
    parameters: List[str]
    prerequisites: List[str] = None

    def __post_init__(self):
        if self.prerequisites is None:
            self.prerequisites = []


class CapabilityRegistry:
    """Registry for tool capabilities"""

    def __init__(self):
        """Initialize the capability registry"""
        self.capabilities: Dict[str, Dict[str, ToolCapability]] = {}
        self._initialize_default_capabilities()

    def _initialize_default_capabilities(self):
        """Initialize default tool capabilities"""

        # Primitive creation capabilities
        self.register_capability("primitives", "create_box", ToolCapability(
            capability_type=CapabilityType.CREATE_GEOMETRY,
            name="Create Box",
            description="Create a rectangular box/cube",
            input_types=["dimensions"],
            output_types=["solid"],
            parameters=["length", "width", "height", "placement"]
        ))

        self.register_capability("primitives", "create_cylinder", ToolCapability(
            capability_type=CapabilityType.CREATE_GEOMETRY,
            name="Create Cylinder",
            description="Create a cylindrical shape",
            input_types=["dimensions"],
            output_types=["solid"],
            parameters=["radius", "height", "placement"]
        ))

        self.register_capability("primitives", "create_sphere", ToolCapability(
            capability_type=CapabilityType.CREATE_GEOMETRY,
            name="Create Sphere",
            description="Create a spherical shape",
            input_types=["dimensions"],
            output_types=["solid"],
            parameters=["radius", "placement"]
        ))

        self.register_capability("primitives", "create_cone", ToolCapability(
            capability_type=CapabilityType.CREATE_GEOMETRY,
            name="Create Cone",
            description="Create a conical shape",
            input_types=["dimensions"],
            output_types=["solid"],
            parameters=["radius1", "radius2", "height", "placement"]
        ))

        # Boolean operations capabilities
        self.register_capability("operations", "boolean_union", ToolCapability(
            capability_type=CapabilityType.BOOLEAN_OPERATIONS,
            name="Boolean Union",
            description="Combine two or more objects",
            input_types=["solid", "solid"],
            output_types=["solid"],
            parameters=["obj1_name", "obj2_name"],
            prerequisites=["objects_exist"]
        ))

        self.register_capability("operations", "boolean_cut", ToolCapability(
            capability_type=CapabilityType.BOOLEAN_OPERATIONS,
            name="Boolean Cut",
            description="Subtract one object from another",
            input_types=["solid", "solid"],
            output_types=["solid"],
            parameters=["obj1_name", "obj2_name"],
            prerequisites=["objects_exist"]
        ))

        self.register_capability("operations", "boolean_intersection", ToolCapability(
            capability_type=CapabilityType.BOOLEAN_OPERATIONS,
            name="Boolean Intersection",
            description="Find intersection of two objects",
            input_types=["solid", "solid"],
            output_types=["solid"],
            parameters=["obj1_name", "obj2_name"],
            prerequisites=["objects_exist"]
        ))

        # Transformation capabilities
        self.register_capability("operations", "move_object", ToolCapability(
            capability_type=CapabilityType.TRANSFORMATIONS,
            name="Move Object",
            description="Move an object to a new position",
            input_types=["solid"],
            output_types=["solid"],
            parameters=["obj_name", "x", "y", "z"],
            prerequisites=["object_exists"]
        ))

        self.register_capability("operations", "rotate_object", ToolCapability(
            capability_type=CapabilityType.TRANSFORMATIONS,
            name="Rotate Object",
            description="Rotate an object around an axis",
            input_types=["solid"],
            output_types=["solid"],
            parameters=["obj_name", "axis", "angle"],
            prerequisites=["object_exists"]
        ))

        self.register_capability("operations", "scale_object", ToolCapability(
            capability_type=CapabilityType.TRANSFORMATIONS,
            name="Scale Object",
            description="Scale an object by given factors",
            input_types=["solid"],
            output_types=["solid"],
            parameters=["obj_name", "scale_x", "scale_y", "scale_z"],
            prerequisites=["object_exists"]
        ))

        # Measurement capabilities
        self.register_capability("measurements", "measure_volume", ToolCapability(
            capability_type=CapabilityType.MEASUREMENTS,
            name="Measure Volume",
            description="Calculate the volume of an object",
            input_types=["solid"],
            output_types=["number"],
            parameters=["obj_name"],
            prerequisites=["object_exists"]
        ))

        self.register_capability("measurements", "measure_area", ToolCapability(
            capability_type=CapabilityType.MEASUREMENTS,
            name="Measure Surface Area",
            description="Calculate the surface area of an object",
            input_types=["solid"],
            output_types=["number"],
            parameters=["obj_name"],
            prerequisites=["object_exists"]
        ))

        self.register_capability("measurements", "measure_distance", ToolCapability(
            capability_type=CapabilityType.MEASUREMENTS,
            name="Measure Distance",
            description="Measure distance between two points or objects",
            input_types=["point", "point"],
            output_types=["number"],
            parameters=["obj1_name", "obj2_name"]
        ))

        # Export/Import capabilities
        self.register_capability("export_import", "export_step", ToolCapability(
            capability_type=CapabilityType.EXPORT_IMPORT,
            name="Export STEP",
            description="Export objects to STEP format",
            input_types=["solid"],
            output_types=["file"],
            parameters=["filename", "objects"]
        ))

        self.register_capability("export_import", "export_stl", ToolCapability(
            capability_type=CapabilityType.EXPORT_IMPORT,
            name="Export STL",
            description="Export objects to STL format",
            input_types=["solid"],
            output_types=["file"],
            parameters=["filename", "objects"]
        ))

        self.register_capability("export_import", "import_step", ToolCapability(
            capability_type=CapabilityType.EXPORT_IMPORT,
            name="Import STEP",
            description="Import objects from STEP format",
            input_types=["file"],
            output_types=["solid"],
            parameters=["filename"]
        ))

    def register_capability(self, tool_category: str, tool_method: str, capability: ToolCapability):
        """Register a capability for a tool"""
        if tool_category not in self.capabilities:
            self.capabilities[tool_category] = {}

        self.capabilities[tool_category][tool_method] = capability

        FreeCAD.Console.PrintMessage(
            f"Registered capability: {tool_category}.{tool_method} -> {capability.name}\n"
        )

    def get_capability(self, tool_category: str, tool_method: str) -> Optional[ToolCapability]:
        """Get capability for a specific tool"""
        return self.capabilities.get(tool_category, {}).get(tool_method)

    def get_capabilities_by_type(self, capability_type: CapabilityType) -> List[ToolCapability]:
        """Get all capabilities of a specific type"""
        result = []
        for category in self.capabilities.values():
            for capability in category.values():
                if capability.capability_type == capability_type:
                    result.append(capability)
        return result

    def get_capabilities_for_intent(self, intent_type: str) -> List[ToolCapability]:
        """Get capabilities that match an intent type"""
        intent_mapping = {
            "creation": CapabilityType.CREATE_GEOMETRY,
            "modification": CapabilityType.MODIFY_GEOMETRY,
            "analysis": CapabilityType.ANALYZE_GEOMETRY,
            "boolean": CapabilityType.BOOLEAN_OPERATIONS,
            "transformation": CapabilityType.TRANSFORMATIONS,
            "measurement": CapabilityType.MEASUREMENTS,
            "export": CapabilityType.EXPORT_IMPORT,
            "import": CapabilityType.EXPORT_IMPORT
        }

        capability_type = intent_mapping.get(intent_type.lower())
        if capability_type:
            return self.get_capabilities_by_type(capability_type)

        return []

    def find_tools_for_capability(self, capability_type: CapabilityType) -> Dict[str, List[str]]:
        """Find all tools that have a specific capability"""
        result = {}

        for tool_category, capabilities in self.capabilities.items():
            matching_methods = []
            for tool_method, capability in capabilities.items():
                if capability.capability_type == capability_type:
                    matching_methods.append(tool_method)

            if matching_methods:
                result[tool_category] = matching_methods

        return result

    def validate_tool_prerequisites(self, tool_category: str, tool_method: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that tool prerequisites are met"""
        capability = self.get_capability(tool_category, tool_method)
        if not capability:
            return {"valid": False, "reason": "Capability not found"}

        validation = {"valid": True, "missing_prerequisites": []}

        for prerequisite in capability.prerequisites:
            if prerequisite == "object_exists":
                # Check if required object exists in context
                if "obj_name" in capability.parameters:
                    obj_name = context.get("obj_name")
                    if not obj_name or not self._object_exists(obj_name):
                        validation["valid"] = False
                        validation["missing_prerequisites"].append(f"Object '{obj_name}' does not exist")

            elif prerequisite == "objects_exist":
                # Check if multiple objects exist
                for param in ["obj1_name", "obj2_name"]:
                    if param in capability.parameters:
                        obj_name = context.get(param)
                        if not obj_name or not self._object_exists(obj_name):
                            validation["valid"] = False
                            validation["missing_prerequisites"].append(f"Object '{obj_name}' does not exist")

        return validation

    def _object_exists(self, obj_name: str) -> bool:
        """Check if an object exists in the active document"""
        try:
            doc = FreeCAD.ActiveDocument
            if not doc:
                return False

            return any(obj.Name == obj_name for obj in doc.Objects)
        except:
            return False

    def get_all_capabilities(self) -> Dict[str, Dict[str, ToolCapability]]:
        """Get all registered capabilities"""
        return self.capabilities.copy()


# Global capability registry instance
_capability_registry = None


def get_capability_registry() -> CapabilityRegistry:
    """Get the global capability registry instance"""
    global _capability_registry
    if _capability_registry is None:
        _capability_registry = CapabilityRegistry()
    return _capability_registry


def register_tool_capability(tool_category: str, tool_method: str, capability: ToolCapability):
    """Register a tool capability in the global registry"""
    registry = get_capability_registry()
    registry.register_capability(tool_category, tool_method, capability)


def get_tool_capability(tool_category: str, tool_method: str) -> Optional[ToolCapability]:
    """Get capability for a specific tool from global registry"""
    registry = get_capability_registry()
    return registry.get_capability(tool_category, tool_method)
