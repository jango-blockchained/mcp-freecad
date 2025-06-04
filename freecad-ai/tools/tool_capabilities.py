"""Tool Capabilities Framework - Define and query tool capabilities"""

from typing import Dict, List, Optional, Any, Set, Callable
from dataclasses import dataclass, field
from enum import Enum
import json
import FreeCAD


class CapabilityType(Enum):
    """Types of tool capabilities"""
    CREATION = "creation"
    MODIFICATION = "modification"
    ANALYSIS = "analysis"
    SELECTION = "selection"
    VISUALIZATION = "visualization"
    IMPORT_EXPORT = "import_export"
    UTILITY = "utility"


class RequirementType(Enum):
    """Types of requirements for tools"""
    DOCUMENT = "document"
    SELECTION = "selection"
    WORKBENCH = "workbench"
    OBJECT_TYPE = "object_type"
    PROPERTY = "property"
    PERMISSION = "permission"


@dataclass
class Parameter:
    """Defines a tool parameter"""
    name: str
    type: str
    description: str
    required: bool = True
    default: Optional[Any] = None
    constraints: Optional[Dict[str, Any]] = None
    units: Optional[str] = None
    examples: List[Any] = field(default_factory=list)


@dataclass
class Requirement:
    """Defines a tool requirement"""
    type: RequirementType
    description: str
    validator: Optional[Callable] = None
    error_message: Optional[str] = None


@dataclass
class Example:
    """Defines a usage example"""
    description: str
    input_text: str
    parameters: Dict[str, Any]
    expected_output: Optional[str] = None
    explanation: Optional[str] = None


@dataclass
class ToolCapability:
    """Complete capability definition for a tool"""
    tool_id: str
    name: str
    category: CapabilityType
    description: str
    detailed_description: str
    parameters: List[Parameter]
    requirements: List[Requirement]
    examples: List[Example]
    keywords: List[str]
    related_tools: List[str] = field(default_factory=list)
    produces: List[str] = field(default_factory=list)
    modifies: List[str] = field(default_factory=list)
    version: str = "1.0"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            "tool_id": self.tool_id,
            "name": self.name,
            "category": self.category.value,
            "description": self.description,
            "detailed_description": self.detailed_description,
            "parameters": [
                {
                    "name": p.name,
                    "type": p.type,
                    "description": p.description,
                    "required": p.required,
                    "default": p.default,
                    "constraints": p.constraints,
                    "units": p.units,
                    "examples": p.examples
                }
                for p in self.parameters
            ],
            "requirements": [
                {
                    "type": r.type.value,
                    "description": r.description,
                    "error_message": r.error_message
                }
                for r in self.requirements
            ],
            "examples": [
                {
                    "description": e.description,
                    "input_text": e.input_text,
                    "parameters": e.parameters,
                    "expected_output": e.expected_output,
                    "explanation": e.explanation
                }
                for e in self.examples
            ],
            "keywords": self.keywords,
            "related_tools": self.related_tools,
            "produces": self.produces,
            "modifies": self.modifies,
            "version": self.version
        }


class ToolCapabilityRegistry:
    """Registry for managing tool capabilities"""

    def __init__(self):
        """Initialize the capability registry"""
        self.capabilities: Dict[str, ToolCapability] = {}
        self.capability_index: Dict[CapabilityType, Set[str]] = {
            cap_type: set() for cap_type in CapabilityType
        }
        self.keyword_index: Dict[str, Set[str]] = {}
        self.produces_index: Dict[str, Set[str]] = {}
        self.modifies_index: Dict[str, Set[str]] = {}

        # Register built-in capabilities
        self._register_builtin_capabilities()

    def register(self, capability: ToolCapability):
        """Register a tool capability"""
        self.capabilities[capability.tool_id] = capability

        # Update indices
        self.capability_index[capability.category].add(capability.tool_id)

        # Update keyword index
        for keyword in capability.keywords:
            if keyword not in self.keyword_index:
                self.keyword_index[keyword] = set()
            self.keyword_index[keyword].add(capability.tool_id)

        # Update produces index
        for produces in capability.produces:
            if produces not in self.produces_index:
                self.produces_index[produces] = set()
            self.produces_index[produces].add(capability.tool_id)

        # Update modifies index
        for modifies in capability.modifies:
            if modifies not in self.modifies_index:
                self.modifies_index[modifies] = set()
            self.modifies_index[modifies].add(capability.tool_id)

    def get(self, tool_id: str) -> Optional[ToolCapability]:
        """Get capability by tool ID"""
        return self.capabilities.get(tool_id)

    def query(self,
              category: Optional[CapabilityType] = None,
              keywords: Optional[List[str]] = None,
              produces: Optional[str] = None,
              modifies: Optional[str] = None,
              has_all_keywords: bool = False) -> List[ToolCapability]:
        """
        Query capabilities based on criteria

        Args:
            category: Filter by capability type
            keywords: Filter by keywords
            produces: Filter by what the tool produces
            modifies: Filter by what the tool modifies
            has_all_keywords: If True, must have all keywords; if False, any keyword

        Returns:
            List of matching capabilities
        """
        # Start with all tools
        tool_ids = set(self.capabilities.keys())

        # Filter by category
        if category:
            tool_ids &= self.capability_index.get(category, set())

        # Filter by keywords
        if keywords:
            keyword_tools = set()
            for keyword in keywords:
                if keyword in self.keyword_index:
                    if has_all_keywords and not keyword_tools:
                        keyword_tools = self.keyword_index[keyword].copy()
                    elif has_all_keywords:
                        keyword_tools &= self.keyword_index[keyword]
                    else:
                        keyword_tools |= self.keyword_index[keyword]

            tool_ids &= keyword_tools

        # Filter by produces
        if produces and produces in self.produces_index:
            tool_ids &= self.produces_index[produces]

        # Filter by modifies
        if modifies and modifies in self.modifies_index:
            tool_ids &= self.modifies_index[modifies]

        # Return capabilities
        return [self.capabilities[tool_id] for tool_id in tool_ids]

    def validate_parameters(self, tool_id: str,
                          parameters: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate parameters for a tool

        Returns:
            Tuple of (is_valid, error_messages)
        """
        capability = self.get(tool_id)
        if not capability:
            return False, [f"Unknown tool: {tool_id}"]

        errors = []

        # Check required parameters
        for param in capability.parameters:
            if param.required and param.name not in parameters:
                errors.append(f"Missing required parameter: {param.name}")
                continue

            if param.name in parameters:
                value = parameters[param.name]

                # Type validation
                if not self._validate_type(value, param.type):
                    errors.append(
                        f"Parameter '{param.name}' expects type {param.type}, "
                        f"got {type(value).__name__}"
                    )

                # Constraint validation
                if param.constraints:
                    constraint_errors = self._validate_constraints(
                        param.name, value, param.constraints
                    )
                    errors.extend(constraint_errors)

        return len(errors) == 0, errors

    def check_requirements(self, tool_id: str) -> Tuple[bool, List[str]]:
        """
        Check if tool requirements are met

        Returns:
            Tuple of (requirements_met, error_messages)
        """
        capability = self.get(tool_id)
        if not capability:
            return False, [f"Unknown tool: {tool_id}"]

        errors = []

        for requirement in capability.requirements:
            if requirement.validator:
                # Use custom validator
                if not requirement.validator():
                    errors.append(
                        requirement.error_message or
                        f"Requirement not met: {requirement.description}"
                    )
            else:
                # Use built-in validators
                if not self._check_requirement(requirement):
                    errors.append(
                        requirement.error_message or
                        f"Requirement not met: {requirement.description}"
                    )

        return len(errors) == 0, errors

    def _validate_type(self, value: Any, expected_type: str) -> bool:
        """Validate value type"""
        type_map = {
            "string": str,
            "number": (int, float),
            "integer": int,
            "float": float,
            "boolean": bool,
            "array": list,
            "object": dict
        }

        if expected_type in type_map:
            return isinstance(value, type_map[expected_type])

        # Special types
        if expected_type == "vector3":
            return (isinstance(value, (list, tuple)) and len(value) == 3 and
                   all(isinstance(v, (int, float)) for v in value))

        if expected_type == "color":
            # Accept various color formats
            if isinstance(value, str):
                return value.startswith("#") or value in ["red", "green", "blue", "yellow"]
            if isinstance(value, (list, tuple)):
                return len(value) in [3, 4] and all(0 <= v <= 1 for v in value)

        return True  # Unknown type, allow

    def _validate_constraints(self, name: str, value: Any,
                            constraints: Dict[str, Any]) -> List[str]:
        """Validate parameter constraints"""
        errors = []

        # Min/max constraints
        if "min" in constraints and value < constraints["min"]:
            errors.append(f"{name} must be >= {constraints['min']}")

        if "max" in constraints and value > constraints["max"]:
            errors.append(f"{name} must be <= {constraints['max']}")

        # Enum constraint
        if "enum" in constraints and value not in constraints["enum"]:
            errors.append(f"{name} must be one of: {constraints['enum']}")

        # Pattern constraint (for strings)
        if "pattern" in constraints and isinstance(value, str):
            import re
            if not re.match(constraints["pattern"], value):
                errors.append(f"{name} must match pattern: {constraints['pattern']}")

        # Custom validator
        if "validator" in constraints:
            validator = constraints["validator"]
            if callable(validator) and not validator(value):
                errors.append(f"{name} validation failed")

        return errors

    def _check_requirement(self, requirement: Requirement) -> bool:
        """Check a single requirement"""
        if requirement.type == RequirementType.DOCUMENT:
            return FreeCAD.ActiveDocument is not None

        elif requirement.type == RequirementType.SELECTION:
            import FreeCADGui
            return len(FreeCADGui.Selection.getSelection()) > 0

        elif requirement.type == RequirementType.WORKBENCH:
            # Would need to check active workbench
            return True

        elif requirement.type == RequirementType.OBJECT_TYPE:
            # Would need to check selected object types
            return True

        return True

    def _register_builtin_capabilities(self):
        """Register built-in tool capabilities"""
        # Example: Box creation tool
        self.register(ToolCapability(
            tool_id="primitives.create_box",
            name="Create Box",
            category=CapabilityType.CREATION,
            description="Create a box/cube primitive",
            detailed_description="""
            Creates a parametric box (rectangular prism) in the active document.
            The box can be positioned and sized according to the provided parameters.
            """,
            parameters=[
                Parameter(
                    name="length",
                    type="number",
                    description="Length of the box (X direction)",
                    required=False,
                    default=10.0,
                    units="mm",
                    constraints={"min": 0.1, "max": 10000},
                    examples=[10, 50, 100]
                ),
                Parameter(
                    name="width",
                    type="number",
                    description="Width of the box (Y direction)",
                    required=False,
                    default=10.0,
                    units="mm",
                    constraints={"min": 0.1, "max": 10000},
                    examples=[10, 50, 100]
                ),
                Parameter(
                    name="height",
                    type="number",
                    description="Height of the box (Z direction)",
                    required=False,
                    default=10.0,
                    units="mm",
                    constraints={"min": 0.1, "max": 10000},
                    examples=[10, 50, 100]
                ),
                Parameter(
                    name="position",
                    type="vector3",
                    description="Position of the box center",
                    required=False,
                    default=[0, 0, 0],
                    units="mm",
                    examples=[[0, 0, 0], [100, 50, 0]]
                ),
                Parameter(
                    name="name",
                    type="string",
                    description="Name for the created box",
                    required=False,
                    default="Box",
                    constraints={"pattern": r"^[A-Za-z][A-Za-z0-9_]*$"},
                    examples=["Box", "MyBox", "Container"]
                )
            ],
            requirements=[
                Requirement(
                    type=RequirementType.DOCUMENT,
                    description="Active document required",
                    error_message="Please create or open a document first"
                )
            ],
            examples=[
                Example(
                    description="Create a simple cube",
                    input_text="create a cube",
                    parameters={"length": 10, "width": 10, "height": 10},
                    expected_output="Box created with dimensions 10x10x10mm"
                ),
                Example(
                    description="Create a box with specific dimensions",
                    input_text="create a box 50mm x 30mm x 20mm",
                    parameters={"length": 50, "width": 30, "height": 20},
                    expected_output="Box created with dimensions 50x30x20mm"
                ),
                Example(
                    description="Create a box at specific position",
                    input_text="create a box at position (100, 50, 0)",
                    parameters={
                        "length": 10, "width": 10, "height": 10,
                        "position": [100, 50, 0]
                    },
                    expected_output="Box created at position (100, 50, 0)"
                )
            ],
            keywords=[
                "box", "cube", "rectangular", "prism", "block",
                "create", "make", "build", "primitive"
            ],
            related_tools=["primitives.create_cylinder", "primitives.create_sphere"],
            produces=["Part::Box", "solid", "shape"],
            modifies=["document"]
        ))

        # Add more built-in capabilities as needed...

    def export_capabilities(self, file_path: str):
        """Export all capabilities to JSON file"""
        data = {
            tool_id: cap.to_dict()
            for tool_id, cap in self.capabilities.items()
        }

        with open(file_path, 'w') as f:
            json.dump(data, f, indent=2)

    def import_capabilities(self, file_path: str):
        """Import capabilities from JSON file"""
        with open(file_path, 'r') as f:
            data = json.load(f)

        for tool_id, cap_data in data.items():
            # Reconstruct capability object
            # This is simplified - would need proper deserialization
            pass

    def generate_documentation(self, tool_id: str) -> str:
        """Generate documentation for a tool"""
        capability = self.get(tool_id)
        if not capability:
            return f"No documentation available for {tool_id}"

        doc = f"# {capability.name}\n\n"
        doc += f"**Category:** {capability.category.value}\n\n"
        doc += f"**Description:** {capability.description}\n\n"
        doc += capability.detailed_description.strip() + "\n\n"

        # Parameters
        if capability.parameters:
            doc += "## Parameters\n\n"
            for param in capability.parameters:
                req = "Required" if param.required else "Optional"
                doc += f"- **{param.name}** ({param.type}, {req}): {param.description}\n"
                if param.default is not None:
                    doc += f"  - Default: {param.default}\n"
                if param.units:
                    doc += f"  - Units: {param.units}\n"
                if param.constraints:
                    doc += f"  - Constraints: {param.constraints}\n"
                if param.examples:
                    doc += f"  - Examples: {', '.join(map(str, param.examples))}\n"

        # Requirements
        if capability.requirements:
            doc += "\n## Requirements\n\n"
            for req in capability.requirements:
                doc += f"- {req.description}\n"

        # Examples
        if capability.examples:
            doc += "\n## Examples\n\n"
            for i, example in enumerate(capability.examples, 1):
                doc += f"### Example {i}: {example.description}\n\n"
                doc += f"**Input:** `{example.input_text}`\n\n"
                doc += f"**Parameters:** `{example.parameters}`\n\n"
                if example.expected_output:
                    doc += f"**Expected Output:** {example.expected_output}\n\n"
                if example.explanation:
                    doc += f"**Explanation:** {example.explanation}\n\n"

        # Related tools
        if capability.related_tools:
            doc += f"\n## Related Tools\n\n"
            doc += ", ".join(capability.related_tools) + "\n"

        return doc


# Global registry instance
_capability_registry = None

def get_capability_registry() -> ToolCapabilityRegistry:
    """Get the global capability registry"""
    global _capability_registry
    if _capability_registry is None:
        _capability_registry = ToolCapabilityRegistry()
    return _capability_registry
