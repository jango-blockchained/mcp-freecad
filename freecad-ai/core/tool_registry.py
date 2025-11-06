"""Tool Registry - Centralized tool registration and management"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple

import FreeCAD

try:
    import FreeCADGui
except ImportError:
    FreeCADGui = None


@dataclass
class ToolInfo:
    """Information about a registered tool"""

    id: str
    name: str
    category: str
    description: str
    version: str = "1.0.0"
    author: str = "FreeCAD AI"
    parameters: Dict[str, Any] = field(default_factory=dict)
    capabilities: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ToolRegistry:
    """
    Centralized registry for managing FreeCAD tools available to the AI agent.
    Handles tool registration, discovery, metadata, and lifecycle.
    """

    def __init__(self):
        """Initialize the Tool Registry"""
        self.tools = {}  # tool_id -> tool instance
        self.tool_info = {}  # tool_id -> ToolInfo
        self.categories = {}  # category -> list of tool_ids
        self.capabilities_index = {}  # capability -> list of tool_ids

        # Tool loading configuration
        self.config = {
            "auto_discover": True,
            "validate_on_register": True,
            "allow_duplicates": False,
            "log_registration": True,
        }

        # Initialize with built-in tools
        self._register_builtin_tools()

    def _register_builtin_tools(self):
        """Register built-in FreeCAD tools"""
        try:
            # Import and register primitive tools
            pass

            self._register_primitives_tool()

            # Import and register operation tools

            self._register_operations_tool()

            # Import and register measurement tools

            self._register_measurements_tool()

            # Import and register export/import tools

            self._register_export_import_tool()

            FreeCAD.Console.PrintMessage("Tool Registry: Built-in tools registered\n")

        except ImportError as e:
            FreeCAD.Console.PrintError(
                f"Tool Registry: Failed to import built-in tools: {e}\n"
            )

    def _register_primitives_tool(self):
        """Register primitive creation tools"""
        # Box tool
        self.register_tool(
            tool_id="primitives.box",
            tool=self._create_tool_wrapper("box"),
            info=ToolInfo(
                id="primitives.box",
                name="Create Box",
                category="primitives",
                description="Create a box/cube with specified dimensions",
                parameters={
                    "length": {
                        "type": "float",
                        "default": 10.0,
                        "description": "Length of the box",
                    },
                    "width": {
                        "type": "float",
                        "default": 10.0,
                        "description": "Width of the box",
                    },
                    "height": {
                        "type": "float",
                        "default": 10.0,
                        "description": "Height of the box",
                    },
                    "position": {
                        "type": "vector",
                        "default": [0, 0, 0],
                        "description": "Position of the box",
                    },
                },
                capabilities=["create", "3d", "solid", "primitive"],
            ),
        )

        # Cylinder tool
        self.register_tool(
            tool_id="primitives.cylinder",
            tool=self._create_tool_wrapper("cylinder"),
            info=ToolInfo(
                id="primitives.cylinder",
                name="Create Cylinder",
                category="primitives",
                description="Create a cylinder with specified dimensions",
                parameters={
                    "radius": {
                        "type": "float",
                        "default": 5.0,
                        "description": "Radius of the cylinder",
                    },
                    "height": {
                        "type": "float",
                        "default": 10.0,
                        "description": "Height of the cylinder",
                    },
                    "position": {
                        "type": "vector",
                        "default": [0, 0, 0],
                        "description": "Position of the cylinder",
                    },
                },
                capabilities=["create", "3d", "solid", "primitive", "round"],
            ),
        )

        # Sphere tool
        self.register_tool(
            tool_id="primitives.sphere",
            tool=self._create_tool_wrapper("sphere"),
            info=ToolInfo(
                id="primitives.sphere",
                name="Create Sphere",
                category="primitives",
                description="Create a sphere with specified radius",
                parameters={
                    "radius": {
                        "type": "float",
                        "default": 5.0,
                        "description": "Radius of the sphere",
                    },
                    "position": {
                        "type": "vector",
                        "default": [0, 0, 0],
                        "description": "Position of the sphere",
                    },
                },
                capabilities=["create", "3d", "solid", "primitive", "round"],
            ),
        )

        # Cone tool
        self.register_tool(
            tool_id="primitives.cone",
            tool=self._create_tool_wrapper("cone"),
            info=ToolInfo(
                id="primitives.cone",
                name="Create Cone",
                category="primitives",
                description="Create a cone with specified dimensions",
                parameters={
                    "radius1": {
                        "type": "float",
                        "default": 5.0,
                        "description": "Bottom radius",
                    },
                    "radius2": {
                        "type": "float",
                        "default": 0.0,
                        "description": "Top radius",
                    },
                    "height": {
                        "type": "float",
                        "default": 10.0,
                        "description": "Height of the cone",
                    },
                    "position": {
                        "type": "vector",
                        "default": [0, 0, 0],
                        "description": "Position of the cone",
                    },
                },
                capabilities=["create", "3d", "solid", "primitive", "tapered"],
            ),
        )

    def _register_operations_tool(self):
        """Register operation tools"""
        # Move tool
        self.register_tool(
            tool_id="operations.move",
            tool=self._create_tool_wrapper("move"),
            info=ToolInfo(
                id="operations.move",
                name="Move Object",
                category="operations",
                description="Move/translate selected objects",
                parameters={
                    "vector": {
                        "type": "vector",
                        "required": True,
                        "description": "Translation vector [x, y, z]",
                    },
                    "copy": {
                        "type": "bool",
                        "default": False,
                        "description": "Create a copy instead of moving",
                    },
                },
                capabilities=["transform", "position", "translate"],
                dependencies=["selection"],
            ),
        )

        # Rotate tool
        self.register_tool(
            tool_id="operations.rotate",
            tool=self._create_tool_wrapper("rotate"),
            info=ToolInfo(
                id="operations.rotate",
                name="Rotate Object",
                category="operations",
                description="Rotate selected objects",
                parameters={
                    "angle": {
                        "type": "float",
                        "required": True,
                        "description": "Rotation angle in degrees",
                    },
                    "axis": {
                        "type": "vector",
                        "default": [0, 0, 1],
                        "description": "Rotation axis",
                    },
                    "center": {
                        "type": "vector",
                        "default": [0, 0, 0],
                        "description": "Center of rotation",
                    },
                },
                capabilities=["transform", "rotate", "orientation"],
                dependencies=["selection"],
            ),
        )

        # Scale tool
        self.register_tool(
            tool_id="operations.scale",
            tool=self._create_tool_wrapper("scale"),
            info=ToolInfo(
                id="operations.scale",
                name="Scale Object",
                category="operations",
                description="Scale selected objects",
                parameters={
                    "factor": {
                        "type": "float",
                        "default": 1.0,
                        "description": "Scale factor",
                    },
                    "uniform": {
                        "type": "bool",
                        "default": True,
                        "description": "Uniform scaling",
                    },
                },
                capabilities=["transform", "resize", "scale"],
                dependencies=["selection"],
            ),
        )

        # Boolean operations
        self.register_tool(
            tool_id="operations.boolean",
            tool=self._create_tool_wrapper("boolean"),
            info=ToolInfo(
                id="operations.boolean",
                name="Boolean Operation",
                category="operations",
                description="Perform boolean operations on objects",
                parameters={
                    "operation": {
                        "type": "enum",
                        "values": ["union", "difference", "intersection"],
                        "required": True,
                    },
                    "objects": {
                        "type": "list",
                        "description": "List of objects to operate on",
                    },
                },
                capabilities=["boolean", "combine", "subtract", "intersect"],
                dependencies=["selection"],
            ),
        )

    def _register_measurements_tool(self):
        """Register measurement tools"""
        self.register_tool(
            tool_id="measurements.distance",
            tool=self._create_tool_wrapper("measure_distance"),
            info=ToolInfo(
                id="measurements.distance",
                name="Measure Distance",
                category="measurements",
                description="Measure distance between points or objects",
                parameters={
                    "point1": {"type": "vector", "description": "First point"},
                    "point2": {"type": "vector", "description": "Second point"},
                },
                capabilities=["measure", "analyze", "distance"],
            ),
        )

        self.register_tool(
            tool_id="measurements.volume",
            tool=self._create_tool_wrapper("measure_volume"),
            info=ToolInfo(
                id="measurements.volume",
                name="Measure Volume",
                category="measurements",
                description="Calculate volume of selected objects",
                parameters={},
                capabilities=["measure", "analyze", "volume"],
                dependencies=["selection"],
            ),
        )

    def _register_export_import_tool(self):
        """Register export/import tools"""
        self.register_tool(
            tool_id="export.stl",
            tool=self._create_tool_wrapper("export_stl"),
            info=ToolInfo(
                id="export.stl",
                name="Export STL",
                category="export_import",
                description="Export selected objects to STL format",
                parameters={
                    "filename": {
                        "type": "string",
                        "required": True,
                        "description": "Output filename",
                    },
                    "ascii": {
                        "type": "bool",
                        "default": False,
                        "description": "Use ASCII format",
                    },
                },
                capabilities=["export", "stl", "3d_printing"],
                dependencies=["selection"],
            ),
        )

        self.register_tool(
            tool_id="export.step",
            tool=self._create_tool_wrapper("export_step"),
            info=ToolInfo(
                id="export.step",
                name="Export STEP",
                category="export_import",
                description="Export document to STEP format",
                parameters={
                    "filename": {
                        "type": "string",
                        "required": True,
                        "description": "Output filename",
                    }
                },
                capabilities=["export", "step", "cad_exchange"],
            ),
        )

    def _create_tool_wrapper(self, tool_name: str) -> Callable:
        """Create a wrapper function for a tool"""

        def tool_wrapper(**kwargs):
            # This is a placeholder - actual implementation would call the real tool
            return f"Executed {tool_name} with parameters: {kwargs}"

        tool_wrapper.__name__ = tool_name
        return tool_wrapper

    def register_tool(self, tool_id: str, tool: Any, info: ToolInfo) -> bool:
        """
        Register a tool in the registry

        Args:
            tool_id: Unique identifier for the tool
            tool: The tool instance or callable
            info: ToolInfo object with metadata

        Returns:
            True if registration successful, False otherwise
        """
        # Check for duplicates
        if tool_id in self.tools and not self.config["allow_duplicates"]:
            FreeCAD.Console.PrintWarning(
                f"Tool Registry: Tool '{tool_id}' already registered\n"
            )
            return False

        # Validate tool if required
        if self.config["validate_on_register"]:
            if not self._validate_tool(tool, info):
                FreeCAD.Console.PrintError(
                    f"Tool Registry: Tool '{tool_id}' validation failed\n"
                )
                return False

        # Register the tool
        self.tools[tool_id] = tool
        self.tool_info[tool_id] = info

        # Update category index
        if info.category not in self.categories:
            self.categories[info.category] = []
        self.categories[info.category].append(tool_id)

        # Update capabilities index
        for capability in info.capabilities:
            if capability not in self.capabilities_index:
                self.capabilities_index[capability] = []
            self.capabilities_index[capability].append(tool_id)

        if self.config["log_registration"]:
            FreeCAD.Console.PrintMessage(
                f"Tool Registry: Registered '{tool_id}' ({info.name})\n"
            )

        return True

    def _validate_tool(self, tool: Any, info: ToolInfo) -> bool:
        """Validate a tool before registration"""
        # Check if tool is callable
        if not callable(tool) and not hasattr(tool, "execute"):
            return False

        # Validate required fields in info
        if not info.id or not info.name or not info.category:
            return False

        return True

    def unregister_tool(self, tool_id: str) -> bool:
        """Unregister a tool from the registry"""
        if tool_id not in self.tools:
            return False

        # Remove from main registry
        tool = self.tools.pop(tool_id)
        info = self.tool_info.pop(tool_id)

        # Remove from category index
        if info.category in self.categories:
            self.categories[info.category].remove(tool_id)
            if not self.categories[info.category]:
                del self.categories[info.category]

        # Remove from capabilities index
        for capability in info.capabilities:
            if capability in self.capabilities_index:
                self.capabilities_index[capability].remove(tool_id)
                if not self.capabilities_index[capability]:
                    del self.capabilities_index[capability]

        FreeCAD.Console.PrintMessage(f"Tool Registry: Unregistered '{tool_id}'\n")
        return True

    def get_tool(self, tool_id: str) -> Optional[Any]:
        """Get a tool by ID"""
        return self.tools.get(tool_id)

    def get_tool_info(self, tool_id: str) -> Optional[ToolInfo]:
        """Get tool info by ID"""
        return self.tool_info.get(tool_id)

    def get_all_tools(self) -> Dict[str, Any]:
        """Get all registered tools"""
        return self.tools.copy()

    def get_tools_by_category(self, category: str) -> List[Any]:
        """Get all tools in a category"""
        tool_ids = self.categories.get(category, [])
        return [self.tools[tid] for tid in tool_ids if tid in self.tools]

    def get_tools_by_capability(self, capability: str) -> List[Any]:
        """Get all tools with a specific capability"""
        tool_ids = self.capabilities_index.get(capability, [])
        return [self.tools[tid] for tid in tool_ids if tid in self.tools]

    def search_tools(self, query: str) -> List[Tuple[str, ToolInfo]]:
        """Search tools by name or description"""
        results = []
        query_lower = query.lower()

        for tool_id, info in self.tool_info.items():
            if (
                query_lower in info.name.lower()
                or query_lower in info.description.lower()
                or any(query_lower in cap for cap in info.capabilities)
            ):
                results.append((tool_id, info))

        return results

    def get_categories(self) -> List[str]:
        """Get all tool categories"""
        return list(self.categories.keys())

    def get_capabilities(self) -> List[str]:
        """Get all registered capabilities"""
        return list(self.capabilities_index.keys())

    def export_registry(self) -> Dict[str, Any]:
        """Export registry metadata as JSON-serializable dict"""
        registry_data = {
            "tools": {},
            "categories": self.categories,
            "capabilities": list(self.capabilities_index.keys()),
        }

        for tool_id, info in self.tool_info.items():
            registry_data["tools"][tool_id] = {
                "name": info.name,
                "category": info.category,
                "description": info.description,
                "version": info.version,
                "author": info.author,
                "parameters": info.parameters,
                "capabilities": info.capabilities,
                "dependencies": info.dependencies,
                "metadata": info.metadata,
            }

        return registry_data

    def import_tools(self, tools_config: Dict[str, Any]):
        """Import tools from a configuration dictionary"""
        # This would be used to load external tool definitions

    def get_tool_dependencies(self, tool_id: str) -> List[str]:
        """Get dependencies for a tool"""
        info = self.tool_info.get(tool_id)
        return info.dependencies if info else []

    def validate_dependencies(self, tool_id: str) -> Tuple[bool, List[str]]:
        """Check if all dependencies for a tool are satisfied"""
        dependencies = self.get_tool_dependencies(tool_id)
        missing = []

        for dep in dependencies:
            # Check various dependency types
            if (
                dep == "selection"
                and FreeCADGui
                and not FreeCADGui.Selection.getSelection()
            ):
                missing.append("No objects selected")
            elif dep == "active_document" and not FreeCAD.ActiveDocument:
                missing.append("No active document")
            elif dep.startswith("tool:") and dep[5:] not in self.tools:
                missing.append(f"Missing tool: {dep[5:]}")

        return len(missing) == 0, missing
