"""FreeCAD AI Workbench - Main workbench implementation"""

import os
import sys
import json
import FreeCAD
import FreeCADGui
import asyncio
import threading
from datetime import datetime

# Ensure the addon directory is in the Python path
addon_dir = os.path.dirname(os.path.abspath(__file__))
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

# Try to import PySide2, fall back gracefully if not available
try:
    from PySide2 import QtWidgets, QtCore, QtGui

    HAS_PYSIDE2 = True
except ImportError:
    try:
        from PySide import QtGui as QtWidgets
        from PySide import QtCore, QtGui

        HAS_PYSIDE2 = False
        FreeCAD.Console.PrintWarning("FreeCAD AI: Using PySide instead of PySide2\n")
    except ImportError:
        FreeCAD.Console.PrintError("FreeCAD AI: No Qt bindings available\n")
        HAS_PYSIDE2 = False

# Import tools and AI providers with better error handling
TOOLS_AVAILABLE = False
try:
    # Try absolute imports first
    from tools.primitives import PrimitivesTool
    from tools.operations import OperationsTool
    from tools.measurements import MeasurementsTool
    from tools.export_import import ExportImportTool

    TOOLS_AVAILABLE = True
except ImportError as e:
    FreeCAD.Console.PrintWarning(
        f"FreeCAD AI: Failed to import tools with absolute imports: {e}\n"
    )
    try:
        # Try importing from the current directory structure
        import tools
        from tools import (
            PrimitivesTool,
            OperationsTool,
            MeasurementsTool,
            ExportImportTool,
        )

        TOOLS_AVAILABLE = True
        FreeCAD.Console.PrintMessage(
            "FreeCAD AI: Successfully imported tools using alternative method\n"
        )
    except ImportError as e2:
        FreeCAD.Console.PrintError(f"FreeCAD AI: Failed to import tools: {e2}\n")
        TOOLS_AVAILABLE = False

# Import advanced tools
ADVANCED_TOOLS_AVAILABLE = False
try:
    from tools.advanced import (
        AssemblyToolProvider,
        CAMToolProvider,
        RenderingToolProvider,
        SmitheryToolProvider,
        ADVANCED_TOOLS_AVAILABLE,
    )

    FreeCAD.Console.PrintMessage("FreeCAD AI: Advanced tools loaded successfully\n")
except ImportError as e:
    FreeCAD.Console.PrintWarning(f"FreeCAD AI: Advanced tools not available: {e}\n")
    ADVANCED_TOOLS_AVAILABLE = False

# Import resources
RESOURCES_AVAILABLE = False
try:
    from resources import (
        MaterialResourceProvider,
        ConstraintResourceProvider,
        MeasurementResourceProvider,
        CADModelResourceProvider,
        RESOURCES_AVAILABLE,
    )

    FreeCAD.Console.PrintMessage("FreeCAD AI: Resources loaded successfully\n")
except ImportError as e:
    FreeCAD.Console.PrintWarning(f"FreeCAD AI: Resources not available: {e}\n")
    RESOURCES_AVAILABLE = False

# Import events
EVENTS_AVAILABLE = False
try:
    from events import (
        DocumentEventHandler,
        CommandEventHandler,
        ErrorEventHandler,
        EVENTS_AVAILABLE,
    )

    FreeCAD.Console.PrintMessage("FreeCAD AI: Event handlers loaded successfully\n")
except ImportError as e:
    FreeCAD.Console.PrintWarning(f"FreeCAD AI: Event handlers not available: {e}\n")
    EVENTS_AVAILABLE = False

# Import API
API_AVAILABLE = False
try:
    from api import create_tool_router, create_resource_router, create_event_router, API_AVAILABLE

    FreeCAD.Console.PrintMessage("FreeCAD AI: API loaded successfully\n")
except ImportError as e:
    FreeCAD.Console.PrintWarning(f"FreeCAD AI: API not available: {e}\n")
    API_AVAILABLE = False

# Import clients
CLIENTS_AVAILABLE = False
try:
    from clients import FreeCADClient, CursorMCPBridge, CLIENTS_AVAILABLE

    FreeCAD.Console.PrintMessage("FreeCAD AI: Clients loaded successfully\n")
except ImportError as e:
    FreeCAD.Console.PrintWarning(f"FreeCAD AI: Clients not available: {e}\n")
    CLIENTS_AVAILABLE = False

# Import AI providers with lazy loading
AI_PROVIDERS_AVAILABLE = False
try:
    # Try absolute imports first
    from ai.providers import (
        get_claude_provider,
        get_gemini_provider,
        get_openrouter_provider,
        get_available_providers,
        get_provider_errors,
        check_dependencies,
    )

    AI_PROVIDERS_AVAILABLE = True
except ImportError as e:
    FreeCAD.Console.PrintWarning(
        f"FreeCAD AI: Failed to import AI providers with absolute imports: {e}\n"
    )
    try:
        # Try importing from the current directory structure
        import ai.providers
        from ai.providers import (
            get_claude_provider,
            get_gemini_provider,
            get_openrouter_provider,
            get_available_providers,
            get_provider_errors,
            check_dependencies,
        )

        AI_PROVIDERS_AVAILABLE = True
        FreeCAD.Console.PrintMessage(
            "FreeCAD AI: Successfully imported AI providers using alternative method\n"
        )
    except ImportError as e2:
        FreeCAD.Console.PrintError(f"FreeCAD AI: Failed to import AI providers: {e2}\n")
        AI_PROVIDERS_AVAILABLE = False


class MCPShowInterfaceCommand:
    """Command to show the MCP interface."""

    def GetResources(self):
        return {
            "Pixmap": "",  # Icon path
            "MenuText": "Show MCP Interface",
            "ToolTip": "Show the FreeCAD AI interface",
        }

    def IsActive(self):
        return True

    def Activated(self):
        FreeCAD.Console.PrintMessage("FreeCAD AI: Interface command activated\n")
        # Show the main interface (this is handled by the dock widget creation)
        if HAS_PYSIDE2:
            main_window = FreeCADGui.getMainWindow()
            # Find the dock widget if it exists
            for widget in main_window.findChildren(QtWidgets.QDockWidget):
                if widget.windowTitle() == "FreeCAD AI":
                    widget.show()
                    widget.raise_()
                    return

            # If not found, show message
            QtWidgets.QMessageBox.information(
                main_window,
                "FreeCAD AI",
                "FreeCAD AI interface is loaded. Look for the dock widget on the right side.",
            )


# Register the command
try:
    if hasattr(FreeCADGui, "addCommand"):
        FreeCADGui.addCommand("MCP_ShowInterface", MCPShowInterfaceCommand())
        FreeCAD.Console.PrintMessage(
            "FreeCAD AI: Command 'MCP_ShowInterface' registered successfully\n"
        )
except Exception as e:
    FreeCAD.Console.PrintError(f"FreeCAD AI: Failed to register command: {e}\n")



class MCPWorkbench(FreeCADGui.Workbench):
    """FreeCAD AI Workbench"""

    MenuText = "FreeCAD AI"
    ToolTip = "AI-powered CAD assistance integrated directly into FreeCAD"

    def __init__(self):
        """Initialize the MCP workbench."""
        self.__class__.Icon = self._get_icon_path()

    def _get_icon_path(self):
        """Get the workbench icon path."""
        try:
            icon_path = os.path.join(
                os.path.dirname(__file__), "resources", "icons", "mcp_workbench.svg"
            )
            if os.path.exists(icon_path):
                return icon_path
        except:
            pass
        return ""

    def Initialize(self):
        """Initialize the workbench GUI components."""
        FreeCAD.Console.PrintMessage("FreeCAD AI Workbench: Initializing...\n")

        try:
            # Create toolbar with available commands
            self._create_toolbar()

            # Create dock widget for the interface
            self._create_dock_widget()

            FreeCAD.Console.PrintMessage(
                "FreeCAD AI Workbench: Initialization complete\n"
            )

        except Exception as e:
            FreeCAD.Console.PrintError(
                f"FreeCAD AI Workbench: Initialization failed: {e}\n"
            )
            import traceback

            FreeCAD.Console.PrintError(
                f"FreeCAD AI Workbench: Traceback: {traceback.format_exc()}\n"
            )

    def Activated(self):
        """Called when the workbench is activated."""
        FreeCAD.Console.PrintMessage("FreeCAD AI Workbench: Activated\n")

    def Deactivated(self):
        """Called when the workbench is deactivated."""
        FreeCAD.Console.PrintMessage("FreeCAD AI Workbench: Deactivated\n")

    def GetClassName(self):
        """Return the workbench class name."""
        return "Gui::PythonWorkbench"

    def _create_toolbar(self):
        """Create the MCP toolbar."""
        try:
            # Create a simple toolbar with basic commands
            toolbar_commands = []

            # Only add commands that are properly registered
            try:
                # Check if the command exists before adding it
                if (
                    hasattr(FreeCADGui, "listCommands")
                    and "MCP_ShowInterface" in FreeCADGui.listCommands()
                ):
                    toolbar_commands.append("MCP_ShowInterface")
            except:
                pass

            # Only create toolbar if we have valid commands and appendToolbar method exists
            if toolbar_commands and hasattr(self, "appendToolbar"):
                self.appendToolbar("FreeCAD AI", toolbar_commands)
                FreeCAD.Console.PrintMessage(
                    f"FreeCAD AI: Toolbar created with {len(toolbar_commands)} commands\n"
                )
            else:
                if not hasattr(self, "appendToolbar"):
                    FreeCAD.Console.PrintMessage(
                        "FreeCAD AI: appendToolbar method not available\n"
                    )
                else:
                    FreeCAD.Console.PrintMessage(
                        "FreeCAD AI: Toolbar creation skipped - no valid commands available\n"
                    )

        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to create toolbar: {e}\n")
            import traceback

            FreeCAD.Console.PrintError(
                f"Toolbar creation traceback: {traceback.format_exc()}\n"
            )

    def _create_dock_widget(self):
        """Create and show the dock widget."""
        try:
            if not HAS_PYSIDE2:
                FreeCAD.Console.PrintMessage(
                    "FreeCAD AI: Skipping dock widget creation - no Qt bindings\n"
                )
                return

            # Import and create the correct main widget with proper initialization
            try:
                from gui.main_widget import MCPMainWidget
                FreeCAD.Console.PrintMessage("FreeCAD AI: Using new MCPMainWidget from gui.main_widget\n")

                # Create main widget - this is a QDockWidget itself
                dock_widget = MCPMainWidget(FreeCADGui.getMainWindow())
                dock_widget.setObjectName("MCPIntegrationDockWidget")

                # Add to main window
                FreeCADGui.getMainWindow().addDockWidget(
                    QtCore.Qt.RightDockWidgetArea, dock_widget
                )
                FreeCAD.Console.PrintMessage(
                    "FreeCAD AI: New main widget dock created successfully with proper provider service\n"
                )

            except ImportError as e:
                FreeCAD.Console.PrintWarning(f"FreeCAD AI: Failed to import new main widget: {e}\n")
                FreeCAD.Console.PrintMessage("FreeCAD AI: Falling back to old main widget\n")

                # Fallback to old widget (but this has the interconnection issues)
                main_widget = MCPMainWidget()
                if main_widget and hasattr(main_widget, "status_bar"):
                    dock_widget = QtWidgets.QDockWidget(
                        "FreeCAD AI", FreeCADGui.getMainWindow()
                    )
                    dock_widget.setObjectName("MCPIntegrationDockWidget")
                    dock_widget.setWidget(main_widget)
                    FreeCADGui.getMainWindow().addDockWidget(
                        QtCore.Qt.RightDockWidgetArea, dock_widget
                    )
                    FreeCAD.Console.PrintWarning(
                        "FreeCAD AI: Old widget created - provider service may not work properly\n"
                    )

        except Exception as e:
            FreeCAD.Console.PrintError(f"Failed to create dock widget: {e}\n")
            import traceback

            FreeCAD.Console.PrintError(
                f"Dock widget creation traceback: {traceback.format_exc()}\n"
            )
