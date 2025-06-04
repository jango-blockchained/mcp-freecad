"""Enhanced Tool Registration - Example of registering tools with detailed capabilities"""

from ..core.tool_capabilities import (
    get_capability_registry,
    ToolCapability,
    CapabilityType,
    Parameter,
    Requirement,
    RequirementType,
    Example
)


def register_enhanced_primitive_tools():
    """Register primitive tools with enhanced capabilities"""
    registry = get_capability_registry()

    # Register Create Box tool
    registry.register(ToolCapability(
        tool_id="primitives.create_box",
        name="Create Box",
        category=CapabilityType.CREATION,
        description="Create a parametric box/cube primitive shape",
        detailed_description="""
        Creates a parametric box (rectangular prism) in the active FreeCAD document.

        The box is created as a Part::Feature object with full parametric control.
        You can specify dimensions, position, and custom naming. The box maintains
        its parametric properties, allowing for later modification through the
        property editor or programmatically.

        Common uses:
        - Basic building blocks for models
        - Bounding boxes for assemblies
        - Reference geometry
        - Boolean operation inputs
        """,
        parameters=[
            Parameter(
                name="length",
                type="number",
                description="Box length along X axis",
                required=False,
                default=10.0,
                units="mm",
                constraints={"min": 0.001, "max": 100000},
                examples=[10, 50, 100, 200]
            ),
            Parameter(
                name="width",
                type="number",
                description="Box width along Y axis",
                required=False,
                default=10.0,
                units="mm",
                constraints={"min": 0.001, "max": 100000},
                examples=[10, 50, 100, 200]
            ),
            Parameter(
                name="height",
                type="number",
                description="Box height along Z axis",
                required=False,
                default=10.0,
                units="mm",
                constraints={"min": 0.001, "max": 100000},
                examples=[10, 50, 100, 200]
            ),
            Parameter(
                name="position",
                type="vector3",
                description="Center position of the box",
                required=False,
                default=[0, 0, 0],
                units="mm",
                examples=[[0, 0, 0], [100, 50, 0], [-50, -50, 10]]
            ),
            Parameter(
                name="name",
                type="string",
                description="Custom name for the created object",
                required=False,
                default=None,
                constraints={"pattern": r"^[A-Za-z][A-Za-z0-9_]*$"},
                examples=["Box001", "BaseBox", "Container"]
            )
        ],
        requirements=[
            Requirement(
                type=RequirementType.DOCUMENT,
                description="Active document required (will be created if none exists)",
                error_message="No active document available"
            )
        ],
        examples=[
            Example(
                description="Create a simple 10mm cube",
                input_text="create a cube",
                parameters={},
                expected_output="Box created with default 10x10x10mm dimensions",
                explanation="Uses all default parameters to create a standard cube"
            ),
            Example(
                description="Create a box with specific dimensions",
                input_text="create a box 50mm long, 30mm wide, and 20mm high",
                parameters={"length": 50, "width": 30, "height": 20},
                expected_output="Box created with dimensions 50x30x20mm at origin",
                explanation="Extracts three dimensions from natural language"
            ),
            Example(
                description="Create a box at specific position",
                input_text="make a 100x100x50 box at position (200, 100, 0)",
                parameters={
                    "length": 100,
                    "width": 100,
                    "height": 50,
                    "position": [200, 100, 0]
                },
                expected_output="Box created at position (200, 100, 0)",
                explanation="Combines dimension and position parameters"
            ),
            Example(
                description="Create named box",
                input_text="create a box called Foundation with dimensions 200x200x10",
                parameters={
                    "name": "Foundation",
                    "length": 200,
                    "width": 200,
                    "height": 10
                },
                expected_output="Box 'Foundation' created with specified dimensions",
                explanation="Creates box with custom name for easy reference"
            )
        ],
        keywords=[
            # Shape names
            "box", "cube", "rectangular", "prism", "block", "cuboid",
            # Actions
            "create", "make", "build", "add", "generate", "new",
            # Descriptors
            "primitive", "shape", "solid", "3d", "geometry"
        ],
        related_tools=[
            "primitives.create_cylinder",
            "primitives.create_sphere",
            "operations.boolean",
            "operations.transform"
        ],
        produces=["Part::Box", "Part::Feature", "solid", "shape"],
        modifies=["document", "3d_view"]
    ))

    # Register Create Cylinder tool
    registry.register(ToolCapability(
        tool_id="primitives.create_cylinder",
        name="Create Cylinder",
        category=CapabilityType.CREATION,
        description="Create a parametric cylinder primitive shape",
        detailed_description="""
        Creates a parametric cylinder in the active FreeCAD document.

        The cylinder is created as a Part::Feature object with parametric radius
        and height. The cylinder axis is aligned with the Z-axis by default.
        Position parameter moves the base center of the cylinder.

        Common uses:
        - Shafts and pins in mechanical design
        - Holes (when used with boolean difference)
        - Pipes and tubes
        - Cylindrical features
        """,
        parameters=[
            Parameter(
                name="radius",
                type="number",
                description="Cylinder radius",
                required=False,
                default=5.0,
                units="mm",
                constraints={"min": 0.001, "max": 50000},
                examples=[5, 10, 25, 50]
            ),
            Parameter(
                name="height",
                type="number",
                description="Cylinder height along Z axis",
                required=False,
                default=10.0,
                units="mm",
                constraints={"min": 0.001, "max": 100000},
                examples=[10, 20, 50, 100]
            ),
            Parameter(
                name="position",
                type="vector3",
                description="Position of cylinder base center",
                required=False,
                default=[0, 0, 0],
                units="mm",
                examples=[[0, 0, 0], [50, 50, 0]]
            ),
            Parameter(
                name="name",
                type="string",
                description="Custom name for the created object",
                required=False,
                default=None,
                constraints={"pattern": r"^[A-Za-z][A-Za-z0-9_]*$"},
                examples=["Cylinder001", "Shaft", "Pin"]
            )
        ],
        requirements=[
            Requirement(
                type=RequirementType.DOCUMENT,
                description="Active document required",
                error_message="No active document available"
            )
        ],
        examples=[
            Example(
                description="Create a simple cylinder",
                input_text="create a cylinder",
                parameters={},
                expected_output="Cylinder created with default R5mm H10mm",
                explanation="Uses default parameters"
            ),
            Example(
                description="Create cylinder with specific radius",
                input_text="make a cylinder with radius 15mm and height 30mm",
                parameters={"radius": 15, "height": 30},
                expected_output="Cylinder created R15mm H30mm",
                explanation="Extracts radius and height from text"
            ),
            Example(
                description="Create cylinder using diameter",
                input_text="create a pipe with 20mm diameter and 100mm length",
                parameters={"radius": 10, "height": 100},
                expected_output="Cylinder created R10mm H100mm",
                explanation="Converts diameter to radius automatically"
            )
        ],
        keywords=[
            # Shape names
            "cylinder", "pipe", "tube", "rod", "shaft", "barrel",
            # Actions
            "create", "make", "build", "add",
            # Descriptors
            "round", "circular", "cylindrical"
        ],
        related_tools=[
            "primitives.create_cone",
            "primitives.create_box",
            "operations.hollow",
            "operations.pattern_circular"
        ],
        produces=["Part::Cylinder", "Part::Feature", "solid", "shape"],
        modifies=["document", "3d_view"]
    ))

    # Register Create Sphere tool
    registry.register(ToolCapability(
        tool_id="primitives.create_sphere",
        name="Create Sphere",
        category=CapabilityType.CREATION,
        description="Create a parametric sphere primitive shape",
        detailed_description="""
        Creates a parametric sphere in the active FreeCAD document.

        The sphere is created as a Part::Feature object with parametric radius.
        The position parameter specifies the sphere center location.

        Common uses:
        - Ball bearings and spherical joints
        - Dome shapes (when cut)
        - Blend radii for complex shapes
        - Reference geometry
        """,
        parameters=[
            Parameter(
                name="radius",
                type="number",
                description="Sphere radius",
                required=False,
                default=5.0,
                units="mm",
                constraints={"min": 0.001, "max": 50000},
                examples=[5, 10, 25, 50]
            ),
            Parameter(
                name="position",
                type="vector3",
                description="Position of sphere center",
                required=False,
                default=[0, 0, 0],
                units="mm",
                examples=[[0, 0, 0], [50, 50, 50]]
            ),
            Parameter(
                name="name",
                type="string",
                description="Custom name for the created object",
                required=False,
                default=None,
                constraints={"pattern": r"^[A-Za-z][A-Za-z0-9_]*$"},
                examples=["Sphere001", "Ball", "Globe"]
            )
        ],
        requirements=[
            Requirement(
                type=RequirementType.DOCUMENT,
                description="Active document required",
                error_message="No active document available"
            )
        ],
        examples=[
            Example(
                description="Create a simple sphere",
                input_text="create a sphere",
                parameters={},
                expected_output="Sphere created with default R5mm",
                explanation="Uses default radius of 5mm"
            ),
            Example(
                description="Create sphere with specific size",
                input_text="make a ball with 25mm radius",
                parameters={"radius": 25},
                expected_output="Sphere created R25mm at origin",
                explanation="Creates sphere with specified radius"
            ),
            Example(
                description="Create positioned sphere",
                input_text="add a sphere of radius 10 at position (100, 100, 50)",
                parameters={"radius": 10, "position": [100, 100, 50]},
                expected_output="Sphere created at specified position",
                explanation="Combines radius and position parameters"
            )
        ],
        keywords=[
            # Shape names
            "sphere", "ball", "globe", "orb", "spherical",
            # Actions
            "create", "make", "build", "add",
            # Descriptors
            "round", "3d", "primitive"
        ],
        related_tools=[
            "primitives.create_cylinder",
            "primitives.create_torus",
            "operations.cut",
            "operations.shell"
        ],
        produces=["Part::Sphere", "Part::Feature", "solid", "shape"],
        modifies=["document", "3d_view"]
    ))


def register_enhanced_operation_tools():
    """Register operation tools with enhanced capabilities"""
    registry = get_capability_registry()

    # Register Move operation
    registry.register(ToolCapability(
        tool_id="operations.move",
        name="Move Object",
        category=CapabilityType.MODIFICATION,
        description="Move/translate objects in 3D space",
        detailed_description="""
        Moves selected objects or specified objects by a translation vector.

        Can operate on single or multiple objects. The movement can be absolute
        (to a position) or relative (by a vector). Supports moving along specific
        axes or in 3D space.

        Movement modes:
        - Relative: Move by specified distance from current position
        - Absolute: Move to specific coordinates
        - Along axis: Constrain movement to X, Y, or Z axis
        """,
        parameters=[
            Parameter(
                name="vector",
                type="vector3",
                description="Movement vector or target position",
                required=True,
                units="mm",
                examples=[[10, 0, 0], [50, 50, 0], [0, 0, 100]]
            ),
            Parameter(
                name="relative",
                type="boolean",
                description="True for relative movement, False for absolute position",
                required=False,
                default=True,
                examples=[True, False]
            ),
            Parameter(
                name="objects",
                type="array",
                description="List of object names to move (uses selection if not specified)",
                required=False,
                default=None,
                examples=[["Box001"], ["Cylinder001", "Sphere001"]]
            ),
            Parameter(
                name="copy",
                type="boolean",
                description="Create a copy instead of moving original",
                required=False,
                default=False,
                examples=[True, False]
            )
        ],
        requirements=[
            Requirement(
                type=RequirementType.DOCUMENT,
                description="Active document required",
                error_message="No active document"
            ),
            Requirement(
                type=RequirementType.SELECTION,
                description="Objects must be selected or specified",
                error_message="No objects selected or specified"
            )
        ],
        examples=[
            Example(
                description="Move selected object 50mm along X",
                input_text="move 50mm to the right",
                parameters={"vector": [50, 0, 0], "relative": True},
                expected_output="Moved object(s) 50mm along X axis"
            ),
            Example(
                description="Move to absolute position",
                input_text="move the box to position (100, 100, 0)",
                parameters={"vector": [100, 100, 0], "relative": False},
                expected_output="Moved object(s) to position (100, 100, 0)"
            ),
            Example(
                description="Move up by 25mm",
                input_text="move up 25mm",
                parameters={"vector": [0, 0, 25], "relative": True},
                expected_output="Moved object(s) 25mm along Z axis"
            )
        ],
        keywords=[
            "move", "translate", "shift", "position", "place",
            "relocate", "displace", "transfer", "slide"
        ],
        related_tools=[
            "operations.rotate",
            "operations.copy",
            "operations.mirror",
            "operations.align"
        ],
        produces=["transformed_object"],
        modifies=["object_position", "document"]
    ))


def register_all_enhanced_tools():
    """Register all tools with enhanced capabilities"""
    register_enhanced_primitive_tools()
    register_enhanced_operation_tools()

    # Additional tools can be registered here...

    print("Enhanced tool capabilities registered successfully")


# Auto-register when module is imported
if __name__ == "__main__":
    register_all_enhanced_tools()
