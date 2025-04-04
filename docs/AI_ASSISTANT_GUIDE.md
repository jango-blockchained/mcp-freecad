# AI Assistant Guide to MCP-FreeCAD

This guide provides detailed instructions for AI assistants on how to use the MCP-FreeCAD server to create and manipulate 3D models.

## Overview

The MCP-FreeCAD server provides a bridge between AI assistants and the FreeCAD CAD/CAM software through the Model Context Protocol (MCP). It allows AI assistants to:

1. Create new 3D models using primitive shapes (box, cylinder, sphere, cone)
2. Perform boolean operations (union, subtraction, intersection)
3. Transform objects (move, rotate)
4. Export models in STL format
5. Manage documents and objects

## Installation

To use the MCP-FreeCAD server, users need to have it installed first. Guide the user through one of these installation methods:

### One-Line Installation (Recommended for AI Tools)

```bash
curl -sSL https://raw.githubusercontent.com/user/mcp-freecad/main/mcp-freecad-installer.sh | bash
```

### Manual Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/user/mcp-freecad.git
   cd mcp-freecad
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. Install the package in development mode:
   ```bash
   pip install -e .
   ```

4. Run the server:
   ```bash
   mcp-freecad
   ```

### Prerequisites

- FreeCAD 0.20 or newer installed on the system
- Python 3.8 or newer
- MCP SDK (`pip install mcp`)

## Available Tools

The MCP-FreeCAD server provides the following tools:

### Document Management

1. **freecad.create_document** - Create a new FreeCAD document
2. **freecad.list_documents** - List all open documents
3. **freecad.list_objects** - List all objects in a document

### 3D Primitives

1. **freecad.create_box** - Create a box primitive
2. **freecad.create_cylinder** - Create a cylinder primitive
3. **freecad.create_sphere** - Create a sphere primitive
4. **freecad.create_cone** - Create a cone primitive

### Boolean Operations

1. **freecad.boolean_union** - Create a union of two objects (add)
2. **freecad.boolean_cut** - Cut the second object from the first (subtract)
3. **freecad.boolean_intersection** - Create the intersection of two objects (common volume)

### Transformations

1. **freecad.move_object** - Move an object to a new position
2. **freecad.rotate_object** - Rotate an object

### Export

1. **freecad.export_stl** - Export the model to an STL file

### Smithery Tools (Specialty Tools)

1. **smithery.create_anvil** - Create an anvil model
2. **smithery.create_hammer** - Create a blacksmith hammer model
3. **smithery.create_tongs** - Create blacksmith tongs model
4. **smithery.forge_blade** - Create a forged blade model
5. **smithery.create_horseshoe** - Create a horseshoe model

## Using the Tools - Workflow Guide

When assisting users with FreeCAD model creation, follow this recommended workflow:

### 1. Creating a Document

Always start by creating a document:

```python
await client.call_tool("freecad.create_document", {"name": "MyModel"})
```

### 2. Creating Primitive Shapes

After creating a document, create the necessary primitive shapes:

```python
# Create a box
box_result = await client.call_tool("freecad.create_box", {
    "length": 100,
    "width": 50,
    "height": 30,
    "name": "MyBox",
    "position_x": 0,
    "position_y": 0,
    "position_z": 0
})

# Store the object name for later reference
box_name = box_result.get("object_name")

# Create a cylinder
cylinder_result = await client.call_tool("freecad.create_cylinder", {
    "radius": 20,
    "height": 80,
    "name": "MyCylinder",
    "position_x": 120,
    "position_y": 0,
    "position_z": 0
})

cylinder_name = cylinder_result.get("object_name")
```

### 3. Performing Boolean Operations

Use boolean operations to combine or cut shapes:

```python
# Create a union of two objects
union_result = await client.call_tool("freecad.boolean_union", {
    "object1": box_name,
    "object2": cylinder_name,
    "name": "CombinedShape"
})

# The resulting combined object name
combined_shape_name = union_result.get("object_name")
```

### 4. Transforming Objects

Move or rotate objects as needed:

```python
# Move an object to a new position
await client.call_tool("freecad.move_object", {
    "object_name": combined_shape_name,
    "position_x": 50,
    "position_y": 50,
    "position_z": 0
})

# Rotate an object
await client.call_tool("freecad.rotate_object", {
    "object_name": combined_shape_name,
    "rotation_x": 0,
    "rotation_y": 0,
    "rotation_z": 45  # Rotate 45 degrees around Z axis
})
```

### 5. Exporting the Model

Finally, export the model to an STL file:

```python
await client.call_tool("freecad.export_stl", {
    "file_path": "my_model.stl",
    "object_name": combined_shape_name
})
```

## Example Projects

Here are some complete example projects to demonstrate the capabilities of the MCP-FreeCAD server:

### Example 1: Simple Box with Hole

This example creates a box with a cylindrical hole:

```python
# Create a document
doc_result = await client.call_tool("freecad.create_document", {"name": "BoxWithHole"})

# Create a box
box_result = await client.call_tool("freecad.create_box", {
    "length": 100,
    "width": 50,
    "height": 30,
    "name": "MainBox",
    "position_x": 0,
    "position_y": 0,
    "position_z": 0
})
box_name = box_result.get("object_name")

# Create a cylinder for the hole
cylinder_result = await client.call_tool("freecad.create_cylinder", {
    "radius": 10,
    "height": 100,
    "name": "Hole",
    "position_x": 50,
    "position_y": 25,
    "position_z": -35
})
cylinder_name = cylinder_result.get("object_name")

# Cut the cylinder from the box
cut_result = await client.call_tool("freecad.boolean_cut", {
    "object1": box_name,
    "object2": cylinder_name,
    "name": "BoxWithHole"
})
final_object = cut_result.get("object_name")

# Export the result
await client.call_tool("freecad.export_stl", {
    "file_path": "box_with_hole.stl",
    "object_name": final_object
})
```

### Example 2: Dumbbell Model

This example creates a dumbbell model using cylinders and spheres:

```python
# Create a document
doc_result = await client.call_tool("freecad.create_document", {"name": "Dumbbell"})

# Create the handle
handle_result = await client.call_tool("freecad.create_cylinder", {
    "radius": 10,
    "height": 150,
    "name": "Handle",
    "position_x": 0,
    "position_y": 0,
    "position_z": 0
})
handle_name = handle_result.get("object_name")

# Create the left weight
left_weight_result = await client.call_tool("freecad.create_sphere", {
    "radius": 30,
    "name": "LeftWeight",
    "position_x": -75,
    "position_y": 0,
    "position_z": 0
})
left_weight_name = left_weight_result.get("object_name")

# Create the right weight
right_weight_result = await client.call_tool("freecad.create_sphere", {
    "radius": 30,
    "name": "RightWeight",
    "position_x": 75,
    "position_y": 0,
    "position_z": 0
})
right_weight_name = right_weight_result.get("object_name")

# Combine the handle and left weight
temp_union_result = await client.call_tool("freecad.boolean_union", {
    "object1": handle_name,
    "object2": left_weight_name,
    "name": "TempUnion"
})
temp_union_name = temp_union_result.get("object_name")

# Combine the temporary union with the right weight
final_union_result = await client.call_tool("freecad.boolean_union", {
    "object1": temp_union_name,
    "object2": right_weight_name,
    "name": "Dumbbell"
})
final_object = final_union_result.get("object_name")

# Export the dumbbell
await client.call_tool("freecad.export_stl", {
    "file_path": "dumbbell.stl",
    "object_name": final_object
})
```

## Parametric Design Approach

When assisting users with CAD design, it's best to follow a parametric design approach:

1. **Ask for key dimensions** - Identify the important dimensions first (e.g., length, width, height)
2. **Define relationships** - Establish relationships between different parts
3. **Start with simple primitives** - Build the model using simple shapes first
4. **Use boolean operations** - Combine, cut, or find intersections as needed
5. **Apply transformations** - Position and orient all components
6. **Export the final result** - Generate the STL file for 3D printing or further use

## Troubleshooting

Here are common issues and their solutions:

### Connection Issues

If the MCP server fails to connect to FreeCAD:

1. Check if FreeCAD is installed and accessible in the PATH
2. Try running FreeCAD manually to verify it works
3. Verify the connection method in the config.json file
4. Run the server with `--debug` flag for more detailed logs

### Boolean Operation Failures

Boolean operations may fail if:

1. Objects don't intersect
2. Objects have invalid geometry
3. Object names are incorrect

To troubleshoot:

```python
# Check what objects are available
list_result = await client.call_tool("freecad.list_objects", {})
objects = list_result.get("objects", [])
print("Available objects:", objects)
```

### Export Failures

If export fails:

1. Ensure the directory is writable
2. Use an absolute path for the file
3. Verify the object exists
4. Check if the object has valid geometry

## Best Practices for AI Assistants

When helping users with FreeCAD via MCP:

1. **Confirm prerequisites** - Ensure FreeCAD is installed and the MCP server is running
2. **Start simple** - Begin with basic shapes and operations
3. **Keep track of object names** - Store names of created objects for later reference
4. **Validate each step** - Check that each operation succeeds before proceeding
5. **Use absolute coordinates** - Prefer absolute coordinates for positioning
6. **Document the process** - Explain the design approach to the user
7. **Provide alternative approaches** - Suggest multiple ways to achieve the desired result
8. **Focus on user's domain knowledge** - Adapt to the user's familiarity with CAD concepts

## Frequently Asked Questions

1. **Can I use FreeCAD workbenches via MCP?**  
   Currently only basic Part workbench operations are supported.

2. **How do I save the FreeCAD document?**  
   Currently, exporting to STL is supported. Native FreeCAD saving is planned for future versions.

3. **Can I import existing models?**  
   Not yet. Importing existing models is planned for future versions.

4. **Does MCP-FreeCAD support assemblies?**  
   Simple assemblies can be created using positioning tools, but advanced assembly features are not yet supported.

5. **How can I create custom shapes?**  
   Currently, combining primitives with boolean operations is the main approach. Advanced shape creation will be added in future updates.

## Resources

- [FreeCAD Documentation](https://wiki.freecad.org/)
- [Python FreeCAD API Reference](https://wiki.freecad.org/Power_users_hub)
- [MCP Protocol Specification](https://modelcontextprotocol.io)
- [FreeCAD Scripting Tutorial](https://wiki.freecad.org/Python_scripting_tutorial) 
