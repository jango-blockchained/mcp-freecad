import logging
from typing import Any, Dict, List, Optional

from .base import ToolProvider, ToolResult, ToolSchema

logger = logging.getLogger(__name__)


class CAMToolProvider(ToolProvider):
    """Tool provider for CAM (Computer Aided Manufacturing) operations in FreeCAD."""

    def __init__(self, freecad_app=None):
        """Initialize the CAM tool provider."""
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
            name="cam",
            description="Tools for CAM (Computer Aided Manufacturing) operations in FreeCAD",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["create_job", "add_tool", "create_operation", "generate_gcode", "simulate"],
                        "description": "The CAM action to perform"
                    },
                    "job_name": {
                        "type": "string",
                        "description": "Name of the CAM job"
                    },
                    "base_object": {
                        "type": "string",
                        "description": "Name of the base object for machining"
                    },
                    "operation_type": {
                        "type": "string",
                        "enum": ["profile", "pocket", "drilling", "adaptive", "surface"],
                        "description": "Type of machining operation"
                    },
                    "tool_diameter": {
                        "type": "number",
                        "description": "Tool diameter in mm"
                    },
                    "spindle_speed": {
                        "type": "number",
                        "description": "Spindle speed in RPM"
                    },
                    "feed_rate": {
                        "type": "number",
                        "description": "Feed rate in mm/min"
                    },
                    "cut_depth": {
                        "type": "number",
                        "description": "Depth of cut in mm"
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
                    "action": "create_job",
                    "job_name": "MyCAMJob",
                    "base_object": "Part001"
                },
                {
                    "action": "add_tool",
                    "job_name": "MyCAMJob",
                    "tool_diameter": 6.0,
                    "spindle_speed": 12000
                }
            ]
        )

    async def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> ToolResult:
        """Execute a CAM tool."""
        if self.app is None:
            return self.format_result("error", error="FreeCAD not available")

        action = params.get("action")

        try:
            if action == "create_job":
                return await self._create_job(params)
            elif action == "add_tool":
                return await self._add_tool(params)
            elif action == "create_operation":
                return await self._create_operation(params)
            elif action == "generate_gcode":
                return await self._generate_gcode(params)
            elif action == "simulate":
                return await self._simulate(params)
            else:
                return self.format_result("error", error=f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"CAM tool failed: {e}")
            return self.format_result("error", error=str(e))

    async def _create_job(self, params: Dict[str, Any]) -> ToolResult:
        """Create a new CAM job."""
        try:
            job_name = params.get("job_name", "CAMJob")
            base_object = params.get("base_object")

            doc = self._get_active_document()

            # Try to import Path workbench
            try:
                import Path
                import PathScripts.PathJob as PathJob

                # Create job
                job = PathJob.Create(job_name)

                # Set base object if provided
                if base_object:
                    base_obj = doc.getObject(base_object)
                    if base_obj:
                        job.Base = base_obj

                doc.recompute()

                return self.format_result("success", result={
                    "job_name": job.Name,
                    "label": job.Label,
                    "base_object": base_object,
                    "message": f"CAM job '{job_name}' created successfully"
                })

            except ImportError:
                return self.format_result("error", error="Path workbench not available. Please install FreeCAD with Path workbench.")

        except Exception as e:
            return self.format_result("error", error=f"Failed to create CAM job: {e}")

    async def _add_tool(self, params: Dict[str, Any]) -> ToolResult:
        """Add a tool to a CAM job."""
        try:
            job_name = params.get("job_name")
            tool_diameter = params.get("tool_diameter", 6.0)
            spindle_speed = params.get("spindle_speed", 12000)
            feed_rate = params.get("feed_rate", 1000)

            doc = self._get_active_document()
            job = doc.getObject(job_name)

            if not job:
                return self.format_result("error", error=f"CAM job '{job_name}' not found")

            try:
                import Path
                import PathScripts.PathToolController as PathToolController

                # Create tool controller
                tc = PathToolController.Create("ToolController")

                # Set tool properties
                tc.Tool.Diameter = tool_diameter
                tc.SpindleSpeed = spindle_speed
                tc.HorizFeed = feed_rate
                tc.VertFeed = feed_rate / 2  # Typically slower for vertical feed

                # Add to job
                job.Tools.append(tc)

                doc.recompute()

                return self.format_result("success", result={
                    "tool_controller": tc.Name,
                    "tool_diameter": tool_diameter,
                    "spindle_speed": spindle_speed,
                    "feed_rate": feed_rate,
                    "message": f"Tool added to job '{job_name}'"
                })

            except ImportError:
                return self.format_result("error", error="Path workbench not available")

        except Exception as e:
            return self.format_result("error", error=f"Failed to add tool: {e}")

    async def _create_operation(self, params: Dict[str, Any]) -> ToolResult:
        """Create a machining operation."""
        try:
            job_name = params.get("job_name")
            operation_type = params.get("operation_type", "profile")
            cut_depth = params.get("cut_depth", 1.0)

            doc = self._get_active_document()
            job = doc.getObject(job_name)

            if not job:
                return self.format_result("error", error=f"CAM job '{job_name}' not found")

            try:
                import Path

                # Create operation based on type
                if operation_type == "profile":
                    import PathScripts.PathProfile as PathProfile
                    op = PathProfile.Create("Profile")
                elif operation_type == "pocket":
                    import PathScripts.PathPocket as PathPocket
                    op = PathPocket.Create("Pocket")
                elif operation_type == "drilling":
                    import PathScripts.PathDrilling as PathDrilling
                    op = PathDrilling.Create("Drilling")
                else:
                    return self.format_result("error", error=f"Unsupported operation type: {operation_type}")

                # Set operation properties
                op.FinalDepth = -cut_depth

                # Add to job
                job.Operations.append(op)

                doc.recompute()

                return self.format_result("success", result={
                    "operation_name": op.Name,
                    "operation_type": operation_type,
                    "cut_depth": cut_depth,
                    "message": f"Operation '{operation_type}' added to job '{job_name}'"
                })

            except ImportError:
                return self.format_result("error", error="Path workbench operations not available")

        except Exception as e:
            return self.format_result("error", error=f"Failed to create operation: {e}")

    async def _generate_gcode(self, params: Dict[str, Any]) -> ToolResult:
        """Generate G-code for a CAM job."""
        try:
            job_name = params.get("job_name")

            doc = self._get_active_document()
            job = doc.getObject(job_name)

            if not job:
                return self.format_result("error", error=f"CAM job '{job_name}' not found")

            try:
                import Path

                # Generate G-code
                gcode_lines = []
                for op in job.Operations:
                    if hasattr(op, 'Path'):
                        for command in op.Path.Commands:
                            gcode_lines.append(command.Name + " " + " ".join([f"{k}{v}" for k, v in command.Parameters.items()]))

                gcode = "\n".join(gcode_lines)

                return self.format_result("success", result={
                    "job_name": job_name,
                    "gcode": gcode,
                    "line_count": len(gcode_lines),
                    "message": f"G-code generated for job '{job_name}'"
                })

            except Exception as e:
                return self.format_result("error", error=f"Failed to generate G-code: {e}")

        except Exception as e:
            return self.format_result("error", error=f"Failed to generate G-code: {e}")

    async def _simulate(self, params: Dict[str, Any]) -> ToolResult:
        """Simulate CAM operations."""
        try:
            job_name = params.get("job_name")

            # This is a simplified simulation
            # Real implementation would use Path simulation tools
            return self.format_result("success", result={
                "job_name": job_name,
                "simulation_status": "completed",
                "message": f"Simulation completed for job '{job_name}' (simplified implementation)",
                "note": "Full simulation requires Path workbench simulation tools"
            })

        except Exception as e:
            return self.format_result("error", error=f"Failed to simulate: {e}")

    def _get_active_document(self):
        """Get the active document or create a new one if none exists."""
        if self.app.ActiveDocument:
            return self.app.ActiveDocument
        else:
            return self.app.newDocument("CAM_Document")
