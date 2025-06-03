import logging
import os
import subprocess
import sys
from typing import Any, Dict, Optional

from .base import ToolProvider, ToolResult, ToolSchema

logger = logging.getLogger(__name__)


class IDEIntegrationToolProvider(ToolProvider):
    """Tool provider for IDE integration and external editor support."""

    @property
    def tool_schema(self) -> ToolSchema:
        return ToolSchema(
            name="ide_integration",
            description="Tools for integrating FreeCAD with external IDEs and editors",
            parameters={
                "type": "object",
                "properties": {
                    "action": {
                        "type": "string",
                        "enum": ["setup_pyzo", "setup_vscode", "setup_atom", "install_stubs", "configure_debugger"],
                        "description": "The IDE integration action to perform"
                    },
                    "ide_path": {
                        "type": "string",
                        "description": "Path to the IDE executable (optional)"
                    },
                    "project_path": {
                        "type": "string",
                        "description": "Path to the project directory"
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
                    "action": "setup_pyzo",
                    "project_path": "/path/to/freecad/project"
                },
                {
                    "action": "install_stubs"
                }
            ]
        )

    async def execute_tool(self, tool_id: str, params: Dict[str, Any]) -> ToolResult:
        """Execute an IDE integration tool."""
        action = params.get("action")

        try:
            if action == "setup_pyzo":
                return await self._setup_pyzo(params)
            elif action == "setup_vscode":
                return await self._setup_vscode(params)
            elif action == "setup_atom":
                return await self._setup_atom(params)
            elif action == "install_stubs":
                return await self._install_stubs(params)
            elif action == "configure_debugger":
                return await self._configure_debugger(params)
            else:
                return self.format_result("error", error=f"Unknown action: {action}")

        except Exception as e:
            logger.error(f"IDE integration tool failed: {e}")
            return self.format_result("error", error=str(e))

    async def _setup_pyzo(self, params: Dict[str, Any]) -> ToolResult:
        """Set up Pyzo IDE for FreeCAD development."""
        try:
            project_path = params.get("project_path", os.getcwd())

            # Create Pyzo configuration
            config = {
                "shell_config": {
                    "name": "freecad",
                    "exe": self._get_freecad_python_path(),
                    "gui": "PySide2",
                    "startup_script": self._create_freecad_startup_script(project_path)
                },
                "setup_instructions": [
                    "1. Install Pyzo from https://pyzo.org",
                    "2. Add new shell configuration in Pyzo (Shell -> Edit shell configurations...)",
                    "3. Use the provided configuration",
                    "4. Set LC_NUMERIC=en_US.UTF-8 in environment if on Linux"
                ]
            }

            return self.format_result("success", result=config)

        except Exception as e:
            return self.format_result("error", error=f"Failed to setup Pyzo: {e}")

    async def _setup_vscode(self, params: Dict[str, Any]) -> ToolResult:
        """Set up VS Code for FreeCAD development."""
        try:
            project_path = params.get("project_path", os.getcwd())

            # Create VS Code configuration
            vscode_config = {
                "settings.json": {
                    "python.defaultInterpreterPath": self._get_freecad_python_path(),
                    "python.analysis.extraPaths": [
                        self._get_freecad_lib_path()
                    ],
                    "python.linting.enabled": True,
                    "python.linting.pylintEnabled": True
                },
                "launch.json": {
                    "version": "0.2.0",
                    "configurations": [
                        {
                            "name": "FreeCAD Debug",
                            "type": "python",
                            "request": "launch",
                            "program": "${workspaceFolder}/debug_freecad.py",
                            "console": "integratedTerminal",
                            "env": {
                                "PYTHONPATH": self._get_freecad_lib_path()
                            }
                        }
                    ]
                },
                "extensions": [
                    "ms-python.python",
                    "ms-python.pylint",
                    "ms-python.debugpy"
                ]
            }

            return self.format_result("success", result=vscode_config)

        except Exception as e:
            return self.format_result("error", error=f"Failed to setup VS Code: {e}")

    async def _install_stubs(self, params: Dict[str, Any]) -> ToolResult:
        """Install FreeCAD Python stubs for better IDE support."""
        try:
            # Try to install freecad-stubs package
            result = subprocess.run([
                sys.executable, "-m", "pip", "install", "freecad-stubs"
            ], capture_output=True, text=True)

            if result.returncode == 0:
                return self.format_result("success", result={
                    "message": "FreeCAD stubs installed successfully",
                    "output": result.stdout
                })
            else:
                return self.format_result("error", error=f"Failed to install stubs: {result.stderr}")

        except Exception as e:
            return self.format_result("error", error=f"Failed to install stubs: {e}")

    def _get_freecad_python_path(self) -> str:
        """Get the path to FreeCAD's Python executable."""
        try:
            import FreeCAD
            return sys.executable
        except ImportError:
            # Fallback paths
            if sys.platform == "win32":
                return "C:/Program Files/FreeCAD/bin/python.exe"
            elif sys.platform == "darwin":
                return "/Applications/FreeCAD.app/Contents/Resources/bin/python"
            else:
                return "/usr/bin/freecad-python3"

    def _create_freecad_startup_script(self, project_path: str) -> str:
        """Create a startup script for FreeCAD in IDEs."""
        script = f"""
import os
import sys

# Add project path
sys.path.insert(0, '{project_path}')

# Import FreeCAD
try:
    import FreeCAD as App
    import FreeCADGui as Gui

    # Show main window if GUI is available
    if hasattr(Gui, 'showMainWindow'):
        Gui.showMainWindow()

    print("FreeCAD loaded successfully")
except ImportError as e:
    print(f"Failed to import FreeCAD: {{e}}")
"""
        return script
