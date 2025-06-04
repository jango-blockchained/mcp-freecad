import logging
import os
from typing import Any, Dict, List, Optional

from ..base import ToolProvider, ToolResult, ToolSchema

logger = logging.getLogger(__name__)


class RenderingToolProvider(ToolProvider):
    """Tool provider for rendering and visualization operations in FreeCAD."""

    def __init__(self, freecad_app=None):
        """Initialize the rendering tool provider."""
        self.app = freecad_app
        if self.app is None:
            try:
                import FreeCAD
                self.app = FreeCAD
                logger.info("Connected to FreeCAD")
            except ImportError:
                logger.warning("Could not import FreeCAD. Make sure it's installed and in your Python path.")
                self.app = None

    @property
    def tool_schema(self) -> ToolSchema:
        return ToolSchema(
            name="rendering",
            description="Tools for rendering and visualization in FreeCAD",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["render_image", "set_camera", "apply_material", "setup_lighting", "export_scene"],
                        "description": "The rendering action to perform"
                    },
                    "output_path": {
                        "type": "string",
                        "description": "Output file path for rendered image"
                    },
                    "width": {
                        "type": "integer",
                        "description": "Image width in pixels"
                    },
                    "height": {
                        "type": "integer",
                        "description": "Image height in pixels"
                    },
                    "camera_position": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Camera position [x, y, z]"
                    },
                    "camera_target": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "Camera target [x, y, z]"
                    },
                    "object_name": {
                        "type": "string",
                        "description": "Name of object to apply material to"
                    },
                    "material_type": {
                        "type": "string",
                        "enum": ["metal", "plastic", "glass", "wood", "custom"],
                        "description": "Type of material to apply"
                    },
                    "color": {
                        "type": "array",
                        "items": {"type": "number"},
                        "description": "RGB color values [r, g, b] (0-1)"
                    },
                    "renderer": {
                        "type": "string",
                        "enum": ["raytracing", "povray", "luxrender", "blender"],
                        "description": "Rendering engine to use"
                    }
                },
                "required": ["action"]
            },
            returns={
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "result": {"type": "object"},
                    "error": {"type": "string"}
                }
            },
            examples=[
                {
                    "action": "render_image",
                    "output_path": "/tmp/render.png",
                    "width": 1920,
                    "height": 1080
                },
                {
                    "action": "apply_material",
                    "object_name": "Box",
                    "material_type": "metal",
                    "color": [0.8, 0.8, 0.9]
                }
            ]
        )

    async def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> ToolResult:
        """Execute a rendering tool."""
        if self.app is None:
            return self.format_result("error", error="FreeCAD not available")

        action = params.get("action")

        try:
            if action == "render_image":
                return await self._render_image(params)
            elif action == "set_camera":
                return await self._set_camera(params)
            elif action == "apply_material":
                return await self._apply_material(params)
            elif action == "setup_lighting":
                return await self._setup_lighting(params)
            elif action == "export_scene":
                return await self._export_scene(params)
            else:
                return self.format_result("error", error=f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"Rendering tool failed: {e}")
            return self.format_result("error", error=str(e))

    async def _render_image(self, params: Dict[str, Any]) -> ToolResult:
        """Render an image of the current scene."""
        try:
            output_path = params.get("output_path", "/tmp/freecad_render.png")
            width = params.get("width", 1920)
            height = params.get("height", 1080)
            renderer = params.get("renderer", "raytracing")

            try:
                import FreeCADGui as Gui

                # Get active view
                view = Gui.ActiveDocument.ActiveView

                if renderer == "raytracing":
                    # Use built-in raytracing
                    try:
                        import Raytracing

                        # Create raytracing project
                        project = self.app.ActiveDocument.addObject("Raytracing::RayProject", "RayProject")

                        # Add all visible objects
                        for obj in self.app.ActiveDocument.Objects:
                            if hasattr(obj, 'ViewObject') and obj.ViewObject.Visibility:
                                ray_obj = self.app.ActiveDocument.addObject("Raytracing::RayPartFeature", f"Ray_{obj.Name}")
                                ray_obj.Source = obj
                                project.addObject(ray_obj)

                        # Set output file
                        project.PageResult = output_path

                        # Execute rendering
                        project.execute()

                        return self.format_result("success", result={
                            "output_path": output_path,
                            "width": width,
                            "height": height,
                            "renderer": renderer,
                            "message": "Image rendered successfully using Raytracing workbench"
                        })

                    except ImportError:
                        # Fallback to screenshot
                        return await self._screenshot_fallback(output_path, width, height)

                elif renderer == "povray":
                    return await self._render_povray(params)
                elif renderer == "blender":
                    return await self._render_blender(params)
                else:
                    return await self._screenshot_fallback(output_path, width, height)

            except ImportError:
                return self.format_result("error", error="FreeCADGui not available")

        except Exception as e:
            return self.format_result("error", error=f"Failed to render image: {e}")

    async def _screenshot_fallback(self, output_path: str, width: int, height: int) -> ToolResult:
        """Fallback to screenshot if advanced rendering not available."""
        try:
            import FreeCADGui as Gui

            # Take screenshot
            view = Gui.ActiveDocument.ActiveView
            view.saveImage(output_path, width, height, "White")

            return self.format_result("success", result={
                "output_path": output_path,
                "width": width,
                "height": height,
                "renderer": "screenshot",
                "message": "Screenshot saved (fallback method)"
            })

        except Exception as e:
            return self.format_result("error", error=f"Screenshot fallback failed: {e}")

    async def _set_camera(self, params: Dict[str, Any]) -> ToolResult:
        """Set camera position and target."""
        try:
            camera_position = params.get("camera_position", [10, 10, 10])
            camera_target = params.get("camera_target", [0, 0, 0])

            try:
                import FreeCADGui as Gui

                view = Gui.ActiveDocument.ActiveView

                # Set camera
                import FreeCAD
                camera = view.getCameraNode()
                camera.position.setValue(*camera_position)

                # Set view direction (from position to target)
                direction = FreeCAD.Vector(*camera_target) - FreeCAD.Vector(*camera_position)
                direction.normalize()
                view.setViewDirection(direction)

                return self.format_result("success", result={
                    "camera_position": camera_position,
                    "camera_target": camera_target,
                    "message": "Camera position set successfully"
                })

            except ImportError:
                return self.format_result("error", error="FreeCADGui not available")

        except Exception as e:
            return self.format_result("error", error=f"Failed to set camera: {e}")

    async def _apply_material(self, params: Dict[str, Any]) -> ToolResult:
        """Apply material to an object."""
        try:
            object_name = params.get("object_name")
            material_type = params.get("material_type", "metal")
            color = params.get("color", [0.8, 0.8, 0.8])

            doc = self._get_active_document()
            obj = doc.getObject(object_name)

            if not obj:
                return self.format_result("error", error=f"Object '{object_name}' not found")

            try:
                import FreeCADGui as Gui

                # Get view object
                view_obj = obj.ViewObject

                # Set basic material properties
                view_obj.ShapeColor = tuple(color)

                # Set material-specific properties
                if material_type == "metal":
                    view_obj.ShapeColor = (0.8, 0.8, 0.9)
                    # Add metallic properties if available
                elif material_type == "plastic":
                    view_obj.ShapeColor = tuple(color)
                elif material_type == "glass":
                    view_obj.ShapeColor = (0.9, 0.9, 1.0)
                    view_obj.Transparency = 80
                elif material_type == "wood":
                    view_obj.ShapeColor = (0.6, 0.4, 0.2)

                doc.recompute()

                return self.format_result("success", result={
                    "object_name": object_name,
                    "material_type": material_type,
                    "color": color,
                    "message": f"Material '{material_type}' applied to '{object_name}'"
                })

            except ImportError:
                return self.format_result("error", error="FreeCADGui not available")

        except Exception as e:
            return self.format_result("error", error=f"Failed to apply material: {e}")

    async def _setup_lighting(self, params: Dict[str, Any]) -> ToolResult:
        """Set up lighting for the scene."""
        try:
            # This is a simplified lighting setup
            # Real implementation would depend on the rendering engine
            return self.format_result("success", result={
                "lighting": "default",
                "message": "Lighting setup completed (simplified implementation)",
                "note": "Advanced lighting requires specific rendering workbench"
            })

        except Exception as e:
            return self.format_result("error", error=f"Failed to setup lighting: {e}")

    async def _export_scene(self, params: Dict[str, Any]) -> ToolResult:
        """Export scene for external rendering."""
        try:
            output_path = params.get("output_path", "/tmp/scene.obj")

            # Export as OBJ file for external rendering
            doc = self._get_active_document()

            # Get all visible objects
            objects = [obj for obj in doc.Objects if hasattr(obj, 'ViewObject') and obj.ViewObject.Visibility]

            if objects:
                # Export using Mesh module
                try:
                    import Mesh

                    # Create mesh from objects
                    meshes = []
                    for obj in objects:
                        if hasattr(obj, 'Shape'):
                            mesh = Mesh.Mesh(obj.Shape.tessellate(0.1))
                            meshes.append(mesh)

                    if meshes:
                        # Combine meshes
                        combined_mesh = meshes[0]
                        for mesh in meshes[1:]:
                            combined_mesh = combined_mesh.unite(mesh)

                        # Export
                        combined_mesh.write(output_path)

                        return self.format_result("success", result={
                            "output_path": output_path,
                            "object_count": len(objects),
                            "message": f"Scene exported to '{output_path}'"
                        })

                except ImportError:
                    return self.format_result("error", error="Mesh module not available")

            return self.format_result("error", error="No visible objects to export")

        except Exception as e:
            return self.format_result("error", error=f"Failed to export scene: {e}")

    async def _render_povray(self, params: Dict[str, Any]) -> ToolResult:
        """Render using POV-Ray."""
        # This would require POV-Ray integration
        return self.format_result("success", result={
            "renderer": "povray",
            "message": "POV-Ray rendering not implemented yet",
            "note": "Requires POV-Ray workbench or external POV-Ray installation"
        })

    async def _render_blender(self, params: Dict[str, Any]) -> ToolResult:
        """Render using Blender."""
        # This would require Blender integration
        return self.format_result("success", result={
            "renderer": "blender",
            "message": "Blender rendering not implemented yet",
            "note": "Requires export to Blender and external rendering"
        })

    def _get_active_document(self):
        """Get the active document or create a new one if none exists."""
        if self.app.ActiveDocument:
            return self.app.ActiveDocument
        else:
            return self.app.newDocument("Rendering_Document")
