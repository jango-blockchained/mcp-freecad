import datetime
import logging
import os
import tempfile
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..tools.base import ToolProvider

logger = logging.getLogger(__name__)


class CodeGenerationToolProvider(ToolProvider):
    """Tool provider for generating and executing FreeCAD Python scripts."""

    def __init__(self, freecad_app=None):
        """
        Initialize the code generation tool provider.

        Args:
            freecad_app: Optional FreeCAD application instance. If None, will try to import FreeCAD.
        """
        self.app = freecad_app
        self._script_history = []
        self._snippet_library = {}

        # Create a snippets directory if it doesn't exist
        self.snippets_dir = Path.home() / ".freecad" / "mcp" / "snippets"
        self.snippets_dir.mkdir(parents=True, exist_ok=True)

        if self.app is None:
            try:
                import FreeCAD

                self.app = FreeCAD
                logger.info("Connected to FreeCAD for code generation")
            except ImportError:
                logger.warning(
                    "Could not import FreeCAD. Make sure it's installed and in your Python path."
                )
                self.app = None

    async def execute_tool(
        self, tool_id: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute a code generation tool.

        Args:
            tool_id: The ID of the tool to execute
            params: The parameters for the tool

        Returns:
            The result of the tool execution
        """
        logger.info(f"Executing code generation tool: {tool_id}")

        # Handle different tools
        if tool_id == "generate_script":
            return await self._generate_script(params)
        elif tool_id == "execute_script":
            return await self._execute_script(params)
        elif tool_id == "save_snippet":
            return await self._save_snippet(params)
        elif tool_id == "load_snippet":
            return await self._load_snippet(params)
        elif tool_id == "get_script_history":
            return await self._get_script_history(params)
        elif tool_id == "generate_primitive_script":
            return await self._generate_primitive_script(params)
        elif tool_id == "generate_transform_script":
            return await self._generate_transform_script(params)
        elif tool_id == "generate_boolean_script":
            return await self._generate_boolean_script(params)
        else:
            logger.error(f"Unknown tool ID: {tool_id}")
            return {"status": "error", "message": f"Unknown tool ID: {tool_id}"}

    async def _generate_script(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a Python script based on the provided parameters."""
        try:
            # Get script content from parameters
            script_content = params.get("script_content", "")
            description = params.get("description", "Custom FreeCAD script")

            if not script_content:
                return {"status": "error", "message": "No script content provided"}

            # Add documentation header with timestamp
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            header = f"""# FreeCAD Script
# Description: {description}
# Generated: {timestamp}
# MCP-FreeCAD Integration

"""

            # Add imports if not present in script_content
            imports = """import FreeCAD as App
import Part
"""
            if (
                "import FreeCAD" not in script_content
                and "import App" not in script_content
            ):
                script_content = imports + script_content

            # Add document creation if not present
            if (
                "App.newDocument" not in script_content
                and "FreeCAD.newDocument" not in script_content
            ):
                script_content = (
                    script_content
                    + "\n\n# Make sure changes are visible\nApp.ActiveDocument.recompute()\n"
                )

            # Combine header and script content
            full_script = header + script_content

            # Store in history
            self._add_to_history(description, full_script)

            return {
                "status": "success",
                "message": "Script generated successfully",
                "script": full_script,
                "description": description,
            }

        except Exception as e:
            logger.error(f"Error generating script: {e}")
            return {"status": "error", "message": f"Error generating script: {str(e)}"}

    async def _execute_script(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute a Python script in FreeCAD."""
        try:
            # Check if FreeCAD is available
            if self.app is None:
                return {
                    "status": "error",
                    "message": "FreeCAD is not available. Cannot execute script.",
                    "mock": True,
                }

            # Get script content
            script_content = params.get("script", "")
            if not script_content:
                return {"status": "error", "message": "No script provided"}

            # Create a temporary file for the script
            with tempfile.NamedTemporaryFile(
                mode="w", suffix=".py", delete=False
            ) as temp_file:
                temp_file_path = temp_file.name
                temp_file.write(script_content)

            try:
                # Execute the script
                exec_globals = {"FreeCAD": self.app, "App": self.app}

                # Execute using exec() for simple scripts
                exec(script_content, exec_globals)

                # Store in history
                self._add_to_history("Executed script", script_content)

                return {"status": "success", "message": "Script executed successfully"}
            finally:
                # Clean up the temporary file
                try:
                    os.unlink(temp_file_path)
                except Exception:
                    pass

        except Exception as e:
            logger.error(f"Error executing script: {e}")
            return {"status": "error", "message": f"Error executing script: {str(e)}"}

    async def _save_snippet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Save a code snippet to the snippet library."""
        try:
            # Get snippet details
            name = params.get("name", "")
            content = params.get("content", "")
            description = params.get("description", "")
            tags = params.get("tags", [])

            if not name:
                return {"status": "error", "message": "No snippet name provided"}

            if not content:
                return {"status": "error", "message": "No snippet content provided"}

            # Create a unique ID for the snippet
            snippet_id = str(uuid.uuid4())

            # Create snippet metadata
            snippet = {
                "id": snippet_id,
                "name": name,
                "content": content,
                "description": description,
                "tags": tags,
                "created_at": datetime.datetime.now().isoformat(),
            }

            # Save to library in memory
            self._snippet_library[snippet_id] = snippet

            # Save to file for persistence
            file_path = self.snippets_dir / f"{snippet_id}.py"
            with open(file_path, "w") as f:
                f.write(f"# Name: {name}\n")
                f.write(f"# Description: {description}\n")
                f.write(f"# Tags: {', '.join(tags)}\n")
                f.write(f"# Created: {snippet['created_at']}\n\n")
                f.write(content)

            return {
                "status": "success",
                "message": f"Snippet '{name}' saved successfully",
                "snippet_id": snippet_id,
                "snippet": snippet,
            }

        except Exception as e:
            logger.error(f"Error saving snippet: {e}")
            return {"status": "error", "message": f"Error saving snippet: {str(e)}"}

    async def _load_snippet(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Load a code snippet from the snippet library."""
        try:
            # Get snippet ID or name
            snippet_id = params.get("snippet_id", "")
            name = params.get("name", "")

            if not snippet_id and not name:
                # Return all snippets
                snippets = list(self._snippet_library.values())

                # If no snippets in memory, try to load from files
                if not snippets:
                    for file_path in self.snippets_dir.glob("*.py"):
                        try:
                            snippet_id = file_path.stem
                            with open(file_path, "r") as f:
                                content = f.read()

                            # Parse metadata from comments
                            lines = content.split("\n")
                            metadata = {}
                            for line in lines[:4]:  # Check first 4 lines for metadata
                                if line.startswith("# "):
                                    parts = line[2:].split(": ", 1)
                                    if len(parts) == 2:
                                        key, value = parts
                                        metadata[key.lower()] = value

                            # Extract actual code (skip metadata lines)
                            code_content = "\n".join(lines[5:])

                            snippet = {
                                "id": snippet_id,
                                "name": metadata.get("name", "Unnamed Snippet"),
                                "description": metadata.get("description", ""),
                                "tags": [
                                    tag.strip()
                                    for tag in metadata.get("tags", "").split(",")
                                    if tag.strip()
                                ],
                                "created_at": metadata.get(
                                    "created", datetime.datetime.now().isoformat()
                                ),
                                "content": code_content,
                            }

                            self._snippet_library[snippet_id] = snippet
                            snippets.append(snippet)
                        except Exception as e:
                            logger.error(
                                f"Error loading snippet from file {file_path}: {e}"
                            )

                return {
                    "status": "success",
                    "message": "Snippets retrieved successfully",
                    "snippets": snippets,
                }

            # Find the snippet
            if snippet_id and snippet_id in self._snippet_library:
                snippet = self._snippet_library[snippet_id]
            elif name:
                # Search by name
                for s in self._snippet_library.values():
                    if s["name"].lower() == name.lower():
                        snippet = s
                        break
                else:
                    return {
                        "status": "error",
                        "message": f"Snippet with name '{name}' not found",
                    }
            else:
                return {
                    "status": "error",
                    "message": f"Snippet with ID '{snippet_id}' not found",
                }

            return {
                "status": "success",
                "message": f"Snippet '{snippet['name']}' loaded successfully",
                "snippet": snippet,
            }

        except Exception as e:
            logger.error(f"Error loading snippet: {e}")
            return {"status": "error", "message": f"Error loading snippet: {str(e)}"}

    async def _get_script_history(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get the script execution history."""
        try:
            # Get optional limit parameter
            limit = params.get("limit", 0)

            # Return history (limited if specified)
            history = self._script_history
            if limit > 0:
                history = history[-limit:]

            return {
                "status": "success",
                "message": "Script history retrieved successfully",
                "history": history,
            }

        except Exception as e:
            logger.error(f"Error retrieving script history: {e}")
            return {
                "status": "error",
                "message": f"Error retrieving script history: {str(e)}",
            }

    async def _generate_primitive_script(
        self, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a script for creating primitive objects."""
        try:
            # Get primitive type and parameters
            primitive_type = params.get("primitive_type", "")
            if not primitive_type:
                return {"status": "error", "message": "No primitive type specified"}

            # Start building the script
            script = """import FreeCAD as App
import Part

# Create or get the active document
doc = App.activeDocument()
if not doc:
    doc = App.newDocument("Primitives")

"""

            if primitive_type.lower() == "box":
                length = params.get("length", 10.0)
                width = params.get("width", 10.0)
                height = params.get("height", 10.0)
                position = params.get("position", [0.0, 0.0, 0.0])

                script += f"""# Create a box
box = Part.makeBox({length}, {width}, {height}, App.Vector({position[0]}, {position[1]}, {position[2]}))
box_obj = doc.addObject("Part::Feature", "Box")
box_obj.Shape = box
"""

            elif primitive_type.lower() == "cylinder":
                radius = params.get("radius", 5.0)
                height = params.get("height", 10.0)
                position = params.get("position", [0.0, 0.0, 0.0])

                script += f"""# Create a cylinder
cylinder = Part.makeCylinder({radius}, {height}, App.Vector({position[0]}, {position[1]}, {position[2]}))
cylinder_obj = doc.addObject("Part::Feature", "Cylinder")
cylinder_obj.Shape = cylinder
"""

            elif primitive_type.lower() == "sphere":
                radius = params.get("radius", 5.0)
                position = params.get("position", [0.0, 0.0, 0.0])

                script += f"""# Create a sphere
sphere = Part.makeSphere({radius}, App.Vector({position[0]}, {position[1]}, {position[2]}))
sphere_obj = doc.addObject("Part::Feature", "Sphere")
sphere_obj.Shape = sphere
"""

            elif primitive_type.lower() == "cone":
                radius1 = params.get("radius1", 5.0)
                radius2 = params.get("radius2", 0.0)
                height = params.get("height", 10.0)
                position = params.get("position", [0.0, 0.0, 0.0])

                script += f"""# Create a cone
cone = Part.makeCone({radius1}, {radius2}, {height}, App.Vector({position[0]}, {position[1]}, {position[2]}))
cone_obj = doc.addObject("Part::Feature", "Cone")
cone_obj.Shape = cone
"""

            elif primitive_type.lower() == "torus":
                radius1 = params.get("radius1", 10.0)  # Major radius
                radius2 = params.get("radius2", 2.0)  # Minor radius
                position = params.get("position", [0.0, 0.0, 0.0])

                script += f"""# Create a torus
torus = Part.makeTorus({radius1}, {radius2}, App.Vector({position[0]}, {position[1]}, {position[2]}))
torus_obj = doc.addObject("Part::Feature", "Torus")
torus_obj.Shape = torus
"""

            else:
                return {
                    "status": "error",
                    "message": f"Unsupported primitive type: {primitive_type}",
                }

            # Add recompute at the end
            script += """
# Recompute the document
doc.recompute()
App.ActiveDocument = doc
"""

            # Add to history
            description = f"Create {primitive_type} primitive"
            self._add_to_history(description, script)

            return await self._generate_script(
                {"script_content": script, "description": description}
            )

        except Exception as e:
            logger.error(f"Error generating primitive script: {e}")
            return {
                "status": "error",
                "message": f"Error generating primitive script: {str(e)}",
            }

    async def _generate_transform_script(
        self, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a script for transforming objects."""
        try:
            # Get transformation type and parameters
            transform_type = params.get("transform_type", "")
            if not transform_type:
                return {
                    "status": "error",
                    "message": "No transformation type specified",
                }

            # Get object name
            object_name = params.get("object_name", "")
            if not object_name:
                return {"status": "error", "message": "No object name specified"}

            # Start building the script
            script = """import FreeCAD as App
import Part

# Get the active document
doc = App.activeDocument()
if not doc:
    raise Exception("No active document")

"""

            if transform_type.lower() == "translate":
                # Get translation vector
                x = params.get("x", 0.0)
                y = params.get("y", 0.0)
                z = params.get("z", 0.0)

                script += f"""# Get the object
obj = doc.getObject("{object_name}")
if not obj:
    raise Exception("Object not found: {object_name}")

# Create a transformation matrix for translation
mat = App.Matrix()
mat.move(App.Vector({x}, {y}, {z}))

# Apply the transformation to the object's shape
shape = obj.Shape.copy()
shape.transformShape(mat)

# Update the object's shape
obj.Shape = shape
"""

            elif transform_type.lower() == "rotate":
                # Get rotation axis and angle
                axis_x = params.get("axis_x", 0.0)
                axis_y = params.get("axis_y", 0.0)
                axis_z = params.get("axis_z", 1.0)
                angle = params.get("angle", 0.0)

                script += f"""# Get the object
obj = doc.getObject("{object_name}")
if not obj:
    raise Exception("Object not found: {object_name}")

# Create a rotation matrix
mat = App.Matrix()
mat.rotateAxis(App.Vector(0,0,0), App.Vector({axis_x}, {axis_y}, {axis_z}), {angle})

# Apply the transformation to the object's shape
shape = obj.Shape.copy()
shape.transformShape(mat)

# Update the object's shape
obj.Shape = shape
"""

            elif transform_type.lower() == "scale":
                # Get scale factors
                scale_x = params.get("scale_x", 1.0)
                scale_y = params.get("scale_y", 1.0)
                scale_z = params.get("scale_z", 1.0)

                script += f"""# Get the object
obj = doc.getObject("{object_name}")
if not obj:
    raise Exception("Object not found: {object_name}")

# Create a scaling matrix
mat = App.Matrix()
mat.scale({scale_x}, {scale_y}, {scale_z})

# Apply the transformation to the object's shape
shape = obj.Shape.copy()
shape.transformShape(mat)

# Update the object's shape
obj.Shape = shape
"""

            else:
                return {
                    "status": "error",
                    "message": f"Unsupported transformation type: {transform_type}",
                }

            # Add recompute at the end
            script += """
# Recompute the document
doc.recompute()
"""

            # Add to history
            description = f"{transform_type.capitalize()} {object_name}"
            self._add_to_history(description, script)

            return await self._generate_script(
                {"script_content": script, "description": description}
            )

        except Exception as e:
            logger.error(f"Error generating transform script: {e}")
            return {
                "status": "error",
                "message": f"Error generating transform script: {str(e)}",
            }

    async def _generate_boolean_script(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a script for boolean operations between objects."""
        try:
            # Get operation type and parameters
            operation_type = params.get("operation_type", "")
            if not operation_type:
                return {
                    "status": "error",
                    "message": "No boolean operation type specified",
                }

            # Get object names
            object1 = params.get("object1", "")
            object2 = params.get("object2", "")
            if not object1 or not object2:
                return {
                    "status": "error",
                    "message": "Two object names are required for boolean operations",
                }

            # Get result name (optional)
            result_name = params.get("result_name", "BooleanResult")

            # Start building the script
            script = """import FreeCAD as App
import Part

# Get the active document
doc = App.activeDocument()
if not doc:
    raise Exception("No active document")

"""

            if operation_type.lower() in ["union", "fuse"]:
                script += f"""# Get the objects
obj1 = doc.getObject("{object1}")
obj2 = doc.getObject("{object2}")
if not obj1 or not obj2:
    raise Exception("One or both objects not found")

# Perform the boolean union operation
union = obj1.Shape.fuse(obj2.Shape)

# Create a new object with the result
result = doc.addObject("Part::Feature", "{result_name}")
result.Shape = union
"""

            elif operation_type.lower() in ["difference", "cut"]:
                script += f"""# Get the objects
obj1 = doc.getObject("{object1}")
obj2 = doc.getObject("{object2}")
if not obj1 or not obj2:
    raise Exception("One or both objects not found")

# Perform the boolean difference operation
difference = obj1.Shape.cut(obj2.Shape)

# Create a new object with the result
result = doc.addObject("Part::Feature", "{result_name}")
result.Shape = difference
"""

            elif operation_type.lower() in ["intersection", "common"]:
                script += f"""# Get the objects
obj1 = doc.getObject("{object1}")
obj2 = doc.getObject("{object2}")
if not obj1 or not obj2:
    raise Exception("One or both objects not found")

# Perform the boolean intersection operation
intersection = obj1.Shape.common(obj2.Shape)

# Create a new object with the result
result = doc.addObject("Part::Feature", "{result_name}")
result.Shape = intersection
"""

            else:
                return {
                    "status": "error",
                    "message": f"Unsupported boolean operation type: {operation_type}",
                }

            # Add recompute at the end
            script += """
# Make the original objects invisible if requested
# obj1.Visibility = False
# obj2.Visibility = False

# Recompute the document
doc.recompute()
"""

            # Add to history
            description = f"Boolean {operation_type} between {object1} and {object2}"
            self._add_to_history(description, script)

            return await self._generate_script(
                {"script_content": script, "description": description}
            )

        except Exception as e:
            logger.error(f"Error generating boolean operation script: {e}")
            return {
                "status": "error",
                "message": f"Error generating boolean operation script: {str(e)}",
            }

    def _add_to_history(self, description: str, script: str) -> None:
        """Add a script to the history."""
        timestamp = datetime.datetime.now().isoformat()
        entry = {"timestamp": timestamp, "description": description, "script": script}
        self._script_history.append(entry)

        # Limit history size
        if len(self._script_history) > 100:
            self._script_history = self._script_history[-100:]
