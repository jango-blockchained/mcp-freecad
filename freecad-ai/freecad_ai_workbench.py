"""FreeCAD AI Workbench - Main workbench implementation"""

import os
import sys
import traceback
import functools

import FreeCAD
import FreeCADGui

# Ensure the addon directory is in the Python path
addon_dir = os.path.dirname(os.path.abspath(__file__))
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)


def workbench_crash_safe(operation_name):
    """Decorator to wrap workbench methods with comprehensive crash prevention and logging."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                FreeCAD.Console.PrintMessage(f"FreeCAD AI Workbench: Starting {operation_name}...\n")
                result = func(*args, **kwargs)
                FreeCAD.Console.PrintMessage(f"FreeCAD AI Workbench: {operation_name} completed successfully\n")
                return result
            except Exception as e:
                FreeCAD.Console.PrintError(f"FreeCAD AI Workbench: CRASH PREVENTED in {operation_name}: {e}\n")
                FreeCAD.Console.PrintError(f"FreeCAD AI Workbench: {operation_name} traceback: {traceback.format_exc()}\n")
                
                # Try to show error in GUI if possible
                try:
                    if hasattr(FreeCADGui, 'getMainWindow'):
                        main_window = FreeCADGui.getMainWindow()
                        if main_window and hasattr(main_window, 'statusBar'):
                            main_window.statusBar().showMessage(f"FreeCAD AI: Error in {operation_name}", 5000)
                except Exception:
                    pass
                
                # Return None or appropriate fallback
                return None
        return wrapper
    return decorator


def safe_import_with_fallback(import_func, module_name, fallback_value=None):
    """Safely import modules with comprehensive error handling and fallback."""
    try:
        FreeCAD.Console.PrintMessage(f"FreeCAD AI: Attempting to import {module_name}...\n")
        result = import_func()
        FreeCAD.Console.PrintMessage(f"FreeCAD AI: Successfully imported {module_name}\n")
        return result
    except ImportError as e:
        FreeCAD.Console.PrintMessage(f"FreeCAD AI: Import failed for {module_name}: {e}\n")
        return fallback_value
    except Exception as e:
        FreeCAD.Console.PrintError(f"FreeCAD AI: CRASH PREVENTED during {module_name} import: {e}\n")
        FreeCAD.Console.PrintError(f"FreeCAD AI: {module_name} import traceback: {traceback.format_exc()}\n")
        return fallback_value


def safe_gui_operation(operation_func, operation_name, fallback_result=None):
    """Safely execute GUI operations with comprehensive error handling."""
    try:
        FreeCAD.Console.PrintMessage(f"FreeCAD AI: Attempting {operation_name}...\n")
        result = operation_func()
        FreeCAD.Console.PrintMessage(f"FreeCAD AI: {operation_name} successful\n")
        return result
    except Exception as e:
        FreeCAD.Console.PrintError(f"FreeCAD AI: CRASH PREVENTED in {operation_name}: {e}\n")
        FreeCAD.Console.PrintError(f"FreeCAD AI: {operation_name} traceback: {traceback.format_exc()}\n")
        return fallback_result


# Try to import PySide2, fall back gracefully if not available
try:
    from PySide2 import QtCore, QtWidgets

    HAS_PYSIDE2 = True
except ImportError:
    try:
        from PySide import QtCore
        from PySide import QtGui as QtWidgets

        HAS_PYSIDE2 = False
        FreeCAD.Console.PrintWarning("FreeCAD AI: Using PySide instead of PySide2\n")
    except ImportError:
        FreeCAD.Console.PrintError("FreeCAD AI: No Qt bindings available\n")
        HAS_PYSIDE2 = False

# Import tools and AI providers with comprehensive crash prevention
TOOLS_AVAILABLE = False
TOOLS_IMPORT_ERROR = None

try:
    # Strategy 1: Try absolute imports first
    try:
        from tools import (
            PrimitivesTool,
            OperationsTool,
            MeasurementsTool,
            ExportImportTool,
            TOOLS_AVAILABLE as TOOLS_LOADED,
        )
        TOOLS_AVAILABLE = TOOLS_LOADED
        FreeCAD.Console.PrintMessage("FreeCAD AI: Tools imported successfully via absolute imports\n")
    except ImportError as e:
        FreeCAD.Console.PrintMessage(f"FreeCAD AI: Absolute tools import failed: {e}\n")
        TOOLS_IMPORT_ERROR = str(e)

        # Strategy 2: Try importing from the current directory structure
        try:
            sys.path.insert(0, addon_dir)
            from tools import (
                PrimitivesTool,
                OperationsTool,
                MeasurementsTool,
                ExportImportTool,
                TOOLS_AVAILABLE as TOOLS_LOADED,
            )
            TOOLS_AVAILABLE = TOOLS_LOADED
            FreeCAD.Console.PrintMessage("FreeCAD AI: Tools imported successfully via path modification\n")
        except ImportError as e2:
            FreeCAD.Console.PrintMessage(f"FreeCAD AI: Tools import with path modification failed: {e2}\n")
            TOOLS_IMPORT_ERROR = str(e2)

            # Strategy 3: Try importing individual tools with fallbacks
            try:
                # Create minimal fallback tools if individual imports fail
                class FallbackTool:
                    def __init__(self, name):
                        self.name = name
                    def __str__(self):
                        return f"Fallback{self.name}"

                try:
                    from tools import PrimitivesTool
                except ImportError:
                    PrimitivesTool = FallbackTool("PrimitivesTool")

                try:
                    from tools import OperationsTool
                except ImportError:
                    OperationsTool = FallbackTool("OperationsTool")

                try:
                    from tools import MeasurementsTool
                except ImportError:
                    MeasurementsTool = FallbackTool("MeasurementsTool")

                try:
                    from tools import ExportImportTool
                except ImportError:
                    ExportImportTool = FallbackTool("ExportImportTool")

                TOOLS_AVAILABLE = True  # Partial availability with fallbacks
                FreeCAD.Console.PrintMessage("FreeCAD AI: Tools imported with fallbacks\n")

            except Exception as e3:
                FreeCAD.Console.PrintWarning(f"FreeCAD AI: Even fallback tools import failed: {e3}\n")
                TOOLS_AVAILABLE = False
                TOOLS_IMPORT_ERROR = str(e3)

except Exception as e:
    FreeCAD.Console.PrintError(f"FreeCAD AI: Critical tools import error: {e}\n")
    TOOLS_AVAILABLE = False
    TOOLS_IMPORT_ERROR = str(e)

if not TOOLS_AVAILABLE:
    FreeCAD.Console.PrintWarning(f"FreeCAD AI: Tools not available - last error: {TOOLS_IMPORT_ERROR}\n")

# Import advanced tools with graceful degradation
ADVANCED_TOOLS_AVAILABLE = safe_import_with_fallback(
    lambda: __import__('tools.advanced', fromlist=['ADVANCED_TOOLS_AVAILABLE']).ADVANCED_TOOLS_AVAILABLE,
    "advanced tools",
    False
)

# Import resources with graceful degradation
RESOURCES_AVAILABLE = safe_import_with_fallback(
    lambda: __import__('resources', fromlist=['RESOURCES_AVAILABLE']).RESOURCES_AVAILABLE,
    "resources",
    False
)

# Import events with graceful degradation
EVENTS_AVAILABLE = safe_import_with_fallback(
    lambda: __import__('events', fromlist=['EVENTS_AVAILABLE']).EVENTS_AVAILABLE,
    "events",
    False
)

# Import API with enhanced version conflict handling
API_AVAILABLE = False
API_IMPORT_ERROR = None

try:
    # Check for FastAPI/Pydantic compatibility issues before importing
    python_version = sys.version_info
    if python_version >= (3, 13):
        FreeCAD.Console.PrintMessage("FreeCAD AI: Python 3.13+ detected - checking API compatibility...\n")
        
        # Test FastAPI/Pydantic compatibility
        try:
            import fastapi
            from pydantic import BaseModel
            
            # Test basic functionality that often fails with version conflicts
            class TestModel(BaseModel):
                test_field: str = "test"
            
            FreeCAD.Console.PrintMessage("FreeCAD AI: FastAPI/Pydantic compatibility test passed\n")
        except TypeError as e:
            if "Protocols with non-method members" in str(e):
                FreeCAD.Console.PrintWarning(f"FreeCAD AI: FastAPI/Pydantic compatibility issue detected: {e}\n")
                FreeCAD.Console.PrintWarning("FreeCAD AI: API module will be disabled due to version conflicts\n")
                FreeCAD.Console.PrintWarning("FreeCAD AI: Consider updating FastAPI/Pydantic or using Python < 3.13\n")
                API_IMPORT_ERROR = f"FastAPI/Pydantic compatibility issue: {e}"
                raise ImportError(API_IMPORT_ERROR)
            else:
                FreeCAD.Console.PrintWarning(f"FreeCAD AI: FastAPI/Pydantic type error: {e}\n")
                API_IMPORT_ERROR = f"FastAPI/Pydantic type error: {e}"
                raise ImportError(API_IMPORT_ERROR)
        except ImportError as e:
            FreeCAD.Console.PrintMessage(f"FreeCAD AI: FastAPI/Pydantic not available: {e}\n")
            API_IMPORT_ERROR = f"FastAPI/Pydantic not available: {e}"
            raise ImportError(API_IMPORT_ERROR)

    # If compatibility check passed or not needed, try importing API
    from api import API_AVAILABLE as API_LOADED
    API_AVAILABLE = API_LOADED
    
    if API_AVAILABLE:
        FreeCAD.Console.PrintMessage("FreeCAD AI: API loaded successfully\n")
    else:
        FreeCAD.Console.PrintMessage("FreeCAD AI: API module reports unavailable\n")
except ImportError as e:
    FreeCAD.Console.PrintMessage(f"FreeCAD AI: API not available: {e}\n")
    API_AVAILABLE = False
    if not API_IMPORT_ERROR:
        API_IMPORT_ERROR = str(e)
except TypeError as e:
    if "Protocols with non-method members" in str(e):
        FreeCAD.Console.PrintError(f"FreeCAD AI: CRASH PREVENTED - FastAPI/Pydantic compatibility error: {e}\n")
        FreeCAD.Console.PrintError("FreeCAD AI: This is a known issue with Python 3.13+ and certain library versions\n")
        FreeCAD.Console.PrintError("FreeCAD AI: API functionality will be disabled\n")
        FreeCAD.Console.PrintError("FreeCAD AI: Solutions:\n")
        FreeCAD.Console.PrintError("  1. Update FastAPI and Pydantic to latest versions\n")
        FreeCAD.Console.PrintError("  2. Use Python 3.12 or earlier\n")
        FreeCAD.Console.PrintError("  3. Use a virtual environment with compatible versions\n")
    else:
        FreeCAD.Console.PrintError(f"FreeCAD AI: CRASH PREVENTED - API type error: {e}\n")
    API_AVAILABLE = False
    API_IMPORT_ERROR = str(e)
except Exception as e:
    FreeCAD.Console.PrintError(f"FreeCAD AI: CRASH PREVENTED - API import error: {e}\n")
    FreeCAD.Console.PrintError(f"FreeCAD AI: API import traceback: {traceback.format_exc()}\n")
    API_AVAILABLE = False
    API_IMPORT_ERROR = str(e)
    
# Import clients with graceful degradation
CLIENTS_AVAILABLE = safe_import_with_fallback(
    lambda: __import__('clients', fromlist=['CLIENTS_AVAILABLE']).CLIENTS_AVAILABLE,
    "clients",
    False
)

# Import AI providers with comprehensive fallback strategies and dependency management
AI_PROVIDERS_AVAILABLE = False
AI_PROVIDERS_IMPORT_ERROR = None
DEPENDENCY_INSTALL_ATTEMPTED = False

def attempt_dependency_installation():
    """Attempt to install missing dependencies for AI providers."""
    global DEPENDENCY_INSTALL_ATTEMPTED
    
    if DEPENDENCY_INSTALL_ATTEMPTED:
        return False
    
    DEPENDENCY_INSTALL_ATTEMPTED = True
    
    try:
        FreeCAD.Console.PrintMessage("FreeCAD AI: Attempting automatic dependency installation for AI providers...\n")
        
        # Try to use the dependency manager
        from utils.dependency_manager import DependencyManager
        
        def progress_callback(message):
            FreeCAD.Console.PrintMessage(f"FreeCAD AI: {message}\n")
        
        manager = DependencyManager(progress_callback)
        
        # Install critical dependencies (like aiohttp)
        success = manager.install_missing_dependencies(critical_only=True)
        
        if success:
            FreeCAD.Console.PrintMessage("FreeCAD AI: ✅ Dependencies installed - restart FreeCAD to use AI providers\n")
            return True
        else:
            FreeCAD.Console.PrintWarning("FreeCAD AI: ❌ Some dependencies failed to install\n")
            return False
            
    except ImportError as e:
        FreeCAD.Console.PrintMessage(f"FreeCAD AI: Could not import dependency manager: {e}\n")
        return False
    except Exception as e:
        FreeCAD.Console.PrintError(f"FreeCAD AI: Dependency installation failed: {e}\n")
        return False

try:
    # Strategy 1: Try absolute imports first
    try:
        from ai.providers.claude_provider import ClaudeProvider
        from ai.providers.gemini_provider import GeminiProvider
        from ai.providers.openrouter_provider import OpenRouterProvider
        AI_PROVIDERS_AVAILABLE = True
        FreeCAD.Console.PrintMessage("FreeCAD AI: AI providers imported successfully via absolute imports\n")
    except ImportError as e:
        FreeCAD.Console.PrintMessage(f"FreeCAD AI: Absolute AI providers import failed: {e}\n")
        AI_PROVIDERS_IMPORT_ERROR = str(e)

        # Check if it's a missing dependency issue
        if "aiohttp" in str(e):
            FreeCAD.Console.PrintWarning("FreeCAD AI: Missing 'aiohttp' dependency detected\n")
            
            # Attempt automatic installation
            if attempt_dependency_installation():
                FreeCAD.Console.PrintMessage("FreeCAD AI: Dependencies installed - AI providers will be available after restart\n")
            else:
                FreeCAD.Console.PrintWarning("FreeCAD AI: Automatic installation failed\n")
                FreeCAD.Console.PrintMessage("FreeCAD AI: Manual installation guide:\n")
                FreeCAD.Console.PrintMessage("  1. Use the Dependencies tab in FreeCAD AI interface\n")
                FreeCAD.Console.PrintMessage("  2. Or run: pip install aiohttp>=3.8.0\n")
                FreeCAD.Console.PrintMessage("  3. Restart FreeCAD after installation\n")

        # Strategy 2: Try importing from the current directory structure
        try:
            sys.path.insert(0, addon_dir)
            from ai.providers.claude_provider import ClaudeProvider
            from ai.providers.gemini_provider import GeminiProvider
            from ai.providers.openrouter_provider import OpenRouterProvider
            AI_PROVIDERS_AVAILABLE = True
            FreeCAD.Console.PrintMessage("FreeCAD AI: AI providers imported successfully via path modification\n")
        except ImportError as e2:
            FreeCAD.Console.PrintMessage(f"FreeCAD AI: AI providers import with path modification failed: {e2}\n")
            AI_PROVIDERS_IMPORT_ERROR = str(e2)

            # Strategy 3: Try importing individual providers with fallbacks
            try:
                # Create minimal fallback provider if individual imports fail
                class FallbackProvider:
                    def __init__(self, name):
                        self.name = name
                        self.available = False
                    def __str__(self):
                        return f"Fallback{self.name}"

                try:
                    from ai.providers.claude_provider import ClaudeProvider
                except ImportError:
                    ClaudeProvider = FallbackProvider("ClaudeProvider")

                try:
                    from ai.providers.gemini_provider import GeminiProvider
                except ImportError:
                    GeminiProvider = FallbackProvider("GeminiProvider")

                try:
                    from ai.providers.openrouter_provider import OpenRouterProvider
                except ImportError:
                    OpenRouterProvider = FallbackProvider("OpenRouterProvider")

                AI_PROVIDERS_AVAILABLE = True  # Partial availability with fallbacks
                FreeCAD.Console.PrintMessage("FreeCAD AI: AI providers imported with fallbacks\n")

            except Exception as e3:
                FreeCAD.Console.PrintWarning(f"FreeCAD AI: Even fallback AI providers import failed: {e3}\n")
                AI_PROVIDERS_AVAILABLE = False
                AI_PROVIDERS_IMPORT_ERROR = str(e3)

except Exception as e:
    FreeCAD.Console.PrintError(f"FreeCAD AI: Critical AI providers import error: {e}\n")
    AI_PROVIDERS_AVAILABLE = False
    AI_PROVIDERS_IMPORT_ERROR = str(e)

if not AI_PROVIDERS_AVAILABLE:
    FreeCAD.Console.PrintWarning(f"FreeCAD AI: AI providers not available - last error: {AI_PROVIDERS_IMPORT_ERROR}\n")
    
    # Provide specific guidance based on the error
    if AI_PROVIDERS_IMPORT_ERROR and "aiohttp" in AI_PROVIDERS_IMPORT_ERROR:
        FreeCAD.Console.PrintMessage("FreeCAD AI: 💡 To enable AI providers:\n")
        FreeCAD.Console.PrintMessage("  1. Open FreeCAD AI interface and go to Dependencies tab\n")
        FreeCAD.Console.PrintMessage("  2. Click 'Install Missing Dependencies'\n")
        FreeCAD.Console.PrintMessage("  3. Restart FreeCAD\n")
        FreeCAD.Console.PrintMessage("  4. Or manually install: pip install aiohttp>=3.8.0\n")

# Print summary of import status with crash prevention
try:

    # Print comprehensive import status summary with user guidance
    FreeCAD.Console.PrintMessage("=" * 60 + "\n")
    FreeCAD.Console.PrintMessage("FreeCAD AI: COMPONENT STATUS SUMMARY\n")
    FreeCAD.Console.PrintMessage("=" * 60 + "\n")

    # Core components
    FreeCAD.Console.PrintMessage("Core Components:\n")
    FreeCAD.Console.PrintMessage(f"  Qt Bindings: {'✓ Available' if HAS_PYSIDE2 else '✗ Missing'}\n")
    FreeCAD.Console.PrintMessage(f"  Tools: {'✓ Available' if TOOLS_AVAILABLE else '✗ Missing'}\n")

    # Optional components
    FreeCAD.Console.PrintMessage("Optional Components:\n")
    FreeCAD.Console.PrintMessage(f"  Advanced Tools: {'✓ Available' if ADVANCED_TOOLS_AVAILABLE else '✗ Missing'}\n")
    FreeCAD.Console.PrintMessage(f"  Resources: {'✓ Available' if RESOURCES_AVAILABLE else '✗ Missing'}\n")
    FreeCAD.Console.PrintMessage(f"  Events: {'✓ Available' if EVENTS_AVAILABLE else '✗ Missing'}\n")
    FreeCAD.Console.PrintMessage(f"  Clients: {'✓ Available' if CLIENTS_AVAILABLE else '✗ Missing'}\n")

    # API and AI components with detailed status
    api_status = "✓ Available" if API_AVAILABLE else "✗ Disabled"
    if not API_AVAILABLE and API_IMPORT_ERROR:
        if "Protocols with non-method members" in API_IMPORT_ERROR:
            api_status += " (FastAPI/Pydantic compatibility issue)"
        else:
            api_status += f" ({API_IMPORT_ERROR[:50]}...)"

    ai_status = "✓ Available" if AI_PROVIDERS_AVAILABLE else "✗ Missing"
    if not AI_PROVIDERS_AVAILABLE and AI_PROVIDERS_IMPORT_ERROR:
        if "aiohttp" in AI_PROVIDERS_IMPORT_ERROR:
            ai_status += " (missing aiohttp dependency)"
        else:
            ai_status += f" ({AI_PROVIDERS_IMPORT_ERROR[:50]}...)"

    FreeCAD.Console.PrintMessage("Network Components:\n")
    FreeCAD.Console.PrintMessage(f"  API: {api_status}\n")
    FreeCAD.Console.PrintMessage(f"  AI Providers: {ai_status}\n")

    # Overall status assessment
    critical_missing = []
    if not HAS_PYSIDE2:
        critical_missing.append("Qt Bindings")
    if not TOOLS_AVAILABLE:
        critical_missing.append("Tools")

    optional_missing = []
    if not API_AVAILABLE:
        optional_missing.append("API")
    if not AI_PROVIDERS_AVAILABLE:
        optional_missing.append("AI Providers")

    FreeCAD.Console.PrintMessage("\nOverall Status:\n")
    if not critical_missing:
        FreeCAD.Console.PrintMessage("  ✅ Core functionality: Available\n")
    else:
        FreeCAD.Console.PrintMessage(f"  ❌ Core functionality: Missing {', '.join(critical_missing)}\n")

    if not optional_missing:
        FreeCAD.Console.PrintMessage("  ✅ Extended functionality: Fully available\n")
    else:
        FreeCAD.Console.PrintMessage(f"  ⚠️ Extended functionality: Missing {', '.join(optional_missing)}\n")

    # User guidance
    if optional_missing:
        FreeCAD.Console.PrintMessage("\n💡 To enable missing functionality:\n")
        if not API_AVAILABLE and "Protocols with non-method members" in str(API_IMPORT_ERROR):
            FreeCAD.Console.PrintMessage("  • API: Update FastAPI/Pydantic or use Python < 3.13\n")
        if not AI_PROVIDERS_AVAILABLE and "aiohttp" in str(AI_PROVIDERS_IMPORT_ERROR):
            FreeCAD.Console.PrintMessage("  • AI Providers: Install aiohttp dependency\n")
            FreeCAD.Console.PrintMessage("    - Use Dependencies tab in FreeCAD AI interface\n")
            FreeCAD.Console.PrintMessage("    - Or run: pip install aiohttp>=3.8.0\n")
            FreeCAD.Console.PrintMessage("    - Then restart FreeCAD\n")

    FreeCAD.Console.PrintMessage("=" * 60 + "\n")
    
except Exception as e:
    FreeCAD.Console.PrintError(f"FreeCAD AI: Error printing import summary: {e}\n")


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

    @workbench_crash_safe("interface command activation")
    def Activated(self):
        """Activate the interface command with comprehensive error handling."""
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Interface command activated\n")
            
            if not HAS_PYSIDE2:
                FreeCAD.Console.PrintWarning("FreeCAD AI: No Qt bindings available - cannot show interface\n")
                return
            
            # Get main window safely
            try:
                main_window = FreeCADGui.getMainWindow()
                if not main_window:
                    FreeCAD.Console.PrintError("FreeCAD AI: Cannot get main window\n")
                    return
            except Exception as e:
                FreeCAD.Console.PrintError(f"FreeCAD AI: Failed to get main window: {e}\n")
                return
            
            # Find existing dock widget
            dock_widget_found = False
            try:
                for widget in main_window.findChildren(QtWidgets.QDockWidget):
                    if widget.windowTitle() == "FreeCAD AI" or widget.objectName() == "MCPIntegrationDockWidget":
                        widget.show()
                        widget.raise_()
                        widget.activateWindow()
                        dock_widget_found = True
                        FreeCAD.Console.PrintMessage("FreeCAD AI: Existing dock widget activated\n")
                        break
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"FreeCAD AI: Error searching for existing dock widget: {e}\n")
            
            # If no dock widget found, show informative message
            if not dock_widget_found:
                try:
                    QtWidgets.QMessageBox.information(
                        main_window,
                        "FreeCAD AI",
                        "FreeCAD AI interface is loading...\n\n"
                        "If the dock widget doesn't appear, try:\n"
                        "1. Check the View menu for dock widgets\n"
                        "2. Look on the right side of the interface\n"
                        "3. Restart FreeCAD if issues persist",
                    )
                    FreeCAD.Console.PrintMessage("FreeCAD AI: Interface activation message shown\n")
                except Exception as e:
                    FreeCAD.Console.PrintWarning(f"FreeCAD AI: Could not show activation message: {e}\n")
                    
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Command activation failed: {e}\n")
            import traceback
            FreeCAD.Console.PrintError(f"FreeCAD AI: Activation traceback: {traceback.format_exc()}\n")


# Register the command with comprehensive error handling
try:
    if hasattr(FreeCADGui, "addCommand"):
        FreeCADGui.addCommand("MCP_ShowInterface", MCPShowInterfaceCommand())
        FreeCAD.Console.PrintMessage(
            "FreeCAD AI: Command 'MCP_ShowInterface' registered successfully\n"
        )
    else:
        FreeCAD.Console.PrintError("FreeCAD AI: FreeCADGui.addCommand not available\n")
except Exception as e:
    FreeCAD.Console.PrintError(f"FreeCAD AI: Failed to register command: {e}\n")
    import traceback
    FreeCAD.Console.PrintError(f"FreeCAD AI: Command registration traceback: {traceback.format_exc()}\n")


class MCPWorkbench(FreeCADGui.Workbench):
    """FreeCAD AI Workbench"""

    MenuText = "FreeCAD AI"
    ToolTip = "AI-powered CAD assistance integrated directly into FreeCAD"

    @workbench_crash_safe("workbench initialization")
    def __init__(self):
        """Initialize the MCP workbench."""
        try:
            self.__class__.Icon = self._get_icon_path()
            FreeCAD.Console.PrintMessage("FreeCAD AI Workbench: Instance created\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI Workbench: Initialization error: {e}\n")

    @workbench_crash_safe("icon path retrieval")
    def _get_icon_path(self):
        """Get the workbench icon path."""
        try:
            icon_path = os.path.join(
                os.path.dirname(__file__), "resources", "icons", "mcp_workbench.svg"
            )
            if os.path.exists(icon_path):
                return icon_path
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"FreeCAD AI: Icon path error: {e}\n")
        return ""

    @workbench_crash_safe("workbench GUI initialization")
    def Initialize(self):
        """Initialize the workbench GUI components with comprehensive error handling."""
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI Workbench: Starting initialization...\n")

            # Check if we have the required GUI components
            if not hasattr(FreeCADGui, 'getMainWindow'):
                FreeCAD.Console.PrintError("FreeCAD AI Workbench: FreeCADGui.getMainWindow not available\n")
                return

            # Define the toolbar commands using the standard FreeCAD method
            safe_gui_operation(
                lambda: self.appendToolbar("FreeCAD AI", ["MCP_ShowInterface"]),
                "toolbar creation"
            )
            
            # Define menu structure
            safe_gui_operation(
                lambda: self.appendMenu("FreeCAD AI", ["MCP_ShowInterface"]),
                "menu creation"
            )

            # Create dock widget with error handling
            safe_gui_operation(
                lambda: self._create_dock_widget_safe(),
                "dock widget creation"
            )

            FreeCAD.Console.PrintMessage("FreeCAD AI Workbench: Initialization complete\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI Workbench: Initialization failed: {e}\n")
            import traceback
            FreeCAD.Console.PrintError(f"FreeCAD AI Workbench: Initialization traceback: {traceback.format_exc()}\n")

    @workbench_crash_safe("workbench activation")
    def Activated(self):
        """Called when the workbench is activated."""
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI Workbench: Activated\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI Workbench: Activation error: {e}\n")

    @workbench_crash_safe("workbench deactivation")
    def Deactivated(self):
        """Called when the workbench is deactivated."""
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI Workbench: Deactivated\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI Workbench: Deactivation error: {e}\n")

    def GetClassName(self):
        """Return the workbench class name."""
        return "Gui::PythonWorkbench"

    @workbench_crash_safe("dock widget creation")
    def _create_dock_widget_safe(self):
        """Create and show the dock widget with maximum safety and error handling."""
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Starting safe dock widget creation...\n")
            
            if not HAS_PYSIDE2:
                FreeCAD.Console.PrintMessage("FreeCAD AI: Skipping dock widget creation - no Qt bindings\n")
                return

            # Get main window safely
            main_window = safe_gui_operation(
                lambda: FreeCADGui.getMainWindow(),
                "main window retrieval"
            )
            
            if not main_window:
                FreeCAD.Console.PrintError("FreeCAD AI: Cannot get main window for dock widget\n")
                return

            # Check if dock widget already exists
            try:
                for widget in main_window.findChildren(QtWidgets.QDockWidget):
                    if widget.objectName() == "MCPIntegrationDockWidget":
                        FreeCAD.Console.PrintMessage("FreeCAD AI: Dock widget already exists\n")
                        return
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"FreeCAD AI: Error checking existing dock widgets: {e}\n")

            # Import and create the main widget
            try:
                from gui.main_widget import MCPMainWidget
                FreeCAD.Console.PrintMessage("FreeCAD AI: MCPMainWidget imported successfully\n")

                # Create main widget - this is a QDockWidget itself
                dock_widget = safe_gui_operation(
                    lambda: MCPMainWidget(main_window),
                    "main widget creation"
                )
                
                if not dock_widget:
                    FreeCAD.Console.PrintError("FreeCAD AI: Failed to create main widget\n")
                    return

                dock_widget.setObjectName("MCPIntegrationDockWidget")
                dock_widget.setWindowTitle("FreeCAD AI")

                # Add to main window with error handling
                add_success = safe_gui_operation(
                    lambda: main_window.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_widget),
                    "dock widget addition to main window"
                )
                
                if add_success is None:
                    FreeCAD.Console.PrintError("FreeCAD AI: Failed to add dock widget to main window\n")
                    # Try to clean up
                    try:
                        dock_widget.deleteLater()
                    except:
                        pass
                    return

                # Show the dock widget
                safe_gui_operation(
                    lambda: dock_widget.show(),
                    "dock widget display"
                )

            except ImportError as e:
                FreeCAD.Console.PrintError(f"FreeCAD AI: Failed to import MCPMainWidget: {e}\n")
                # Create minimal fallback dock widget
                fallback_success = safe_gui_operation(
                    lambda: self._create_fallback_dock_widget(main_window),
                    "fallback dock widget creation"
                )
                
                if fallback_success:
                    FreeCAD.Console.PrintMessage("FreeCAD AI: Fallback dock widget created\n")
                else:
                    FreeCAD.Console.PrintError("FreeCAD AI: Even fallback dock widget creation failed\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Safe dock widget creation failed: {e}\n")
            import traceback
            FreeCAD.Console.PrintError(f"FreeCAD AI: Safe dock widget traceback: {traceback.format_exc()}\n")

    def _create_fallback_dock_widget(self, main_window):
        """Create a minimal fallback dock widget when main widget fails."""
        try:
            fallback_widget = QtWidgets.QWidget()
            fallback_layout = QtWidgets.QVBoxLayout(fallback_widget)
            fallback_label = QtWidgets.QLabel(
                "FreeCAD AI\n\nMain widget failed to load.\n"
                "Check the console for details.\n\n"
                "Basic functionality may be limited."
            )
            fallback_label.setStyleSheet("padding: 10px; color: #666;")
            fallback_layout.addWidget(fallback_label)
            
            dock_widget = QtWidgets.QDockWidget("FreeCAD AI", main_window)
            dock_widget.setObjectName("MCPIntegrationDockWidget")
            dock_widget.setWidget(fallback_widget)
            
            main_window.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock_widget)
            dock_widget.show()
            
            return True
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Fallback dock widget creation failed: {e}\n")
            return False
