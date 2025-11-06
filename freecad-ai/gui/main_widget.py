"""Main Widget for FreeCAD AI FreeCAD Addon"""

import functools
import importlib
import traceback

import FreeCAD

# Safe Qt imports with comprehensive fallback to prevent crashes
try:
    # First try to use the Qt compatibility module
    from .qt_compatibility import QtCore, QtWidgets, HAS_QT, QT_VERSION

    if HAS_QT:
        FreeCAD.Console.PrintMessage(
            f"FreeCAD AI: Using Qt compatibility layer ({QT_VERSION})\n"
        )
    else:
        FreeCAD.Console.PrintWarning(
            "FreeCAD AI: Qt compatibility layer using dummy classes\n"
        )
except ImportError:
    # Fallback to original Qt import logic
    try:
        from PySide2 import QtCore, QtWidgets

        HAS_PYSIDE2 = True
        # Fix the QT_VERSION_STR issue if it doesn't exist
        if not hasattr(QtCore, "QT_VERSION_STR"):
            try:
                import PySide2

                QtCore.QT_VERSION_STR = PySide2.__version__
            except (ImportError, AttributeError):
                # ImportError: PySide2 not available
                # AttributeError: Missing version attribute
                QtCore.QT_VERSION_STR = "5.15.0"  # Fallback version
        FreeCAD.Console.PrintMessage("FreeCAD AI: Using PySide2\n")
    except ImportError:
        try:
            from PySide import QtCore
            from PySide import QtGui as QtWidgets

            HAS_PYSIDE2 = False
            FreeCAD.Console.PrintMessage("FreeCAD AI: Using PySide (fallback)\n")
        except ImportError:
            FreeCAD.Console.PrintError(
                "FreeCAD AI: No Qt bindings available - minimal functionality\n"
            )
            HAS_PYSIDE2 = False

            # Create minimal dummy classes to prevent crashes
            class QtWidgets:
                class QDockWidget:
                    def __init__(self, *args, **kwargs):
                        pass

                    def setAllowedAreas(self, *args):
                        pass

                    def setFeatures(self, *args):
                        pass

                    def setWidget(self, widget):
                        pass

                    def setMinimumWidth(self, width):
                        pass

                    def resize(self, width, height):
                        pass

                class QWidget:
                    def __init__(self, *args, **kwargs):
                        pass

                class QVBoxLayout:
                    def __init__(self, *args, **kwargs):
                        pass

                    def addWidget(self, widget):
                        pass

                    def addLayout(self, layout):
                        pass

                    def setSpacing(self, spacing):
                        pass

                    def setContentsMargins(self, *args):
                        pass

                class QHBoxLayout:
                    def __init__(self, *args, **kwargs):
                        pass

                    def addWidget(self, widget):
                        pass

                    def addStretch(self):
                        pass

                class QLabel:
                    def __init__(self, *args, **kwargs):
                        pass

                    def setStyleSheet(self, style):
                        pass

                    def setText(self, text):
                        pass

                class QTabWidget:
                    def __init__(self, *args, **kwargs):
                        pass

                    def setUsesScrollButtons(self, value):
                        pass

                    def setElideMode(self, mode):
                        pass

            class QtCore:
                class Qt:
                    RightDockWidgetArea = None
                    LeftDockWidgetArea = None
                    ElideRight = None

                class QTimer:
                    @staticmethod
                    def singleShot(interval, callback):
                        pass

                class QObject:
                    def __init__(self):
                        pass


def crash_safe_wrapper(operation_name):
    """Decorator to wrap methods with comprehensive crash prevention and logging."""

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                FreeCAD.Console.PrintMessage(
                    f"FreeCAD AI: Starting {operation_name}...\n"
                )
                result = func(*args, **kwargs)
                FreeCAD.Console.PrintMessage(
                    f"FreeCAD AI: {operation_name} completed successfully\n"
                )
                return result
            except Exception as e:
                FreeCAD.Console.PrintError(
                    f"FreeCAD AI: CRASH PREVENTED in {operation_name}: {e}\n"
                )
                FreeCAD.Console.PrintError(
                    f"FreeCAD AI: {operation_name} traceback: {traceback.format_exc()}\n"
                )
                if hasattr(args[0], "status_label") and args[0].status_label:
                    try:
                        args[0].status_label.setText(f"Error in {operation_name}")
                        args[0].status_label.setStyleSheet(
                            "padding: 2px 8px; background-color: #ffcdd2; color: #c62828; border-radius: 10px; font-size: 11px;"
                        )
                    except (AttributeError, RuntimeError):
                        # AttributeError: Missing status_label or setText method
                        # RuntimeError: Widget already destroyed or invalid
                        pass
                return None

        return wrapper

    return decorator


def safe_signal_connect(signal, slot, operation_name="signal connection"):
    """Safely connect Qt signals with comprehensive error handling."""
    try:
        if signal and slot and hasattr(signal, "connect"):
            signal.connect(slot)
            FreeCAD.Console.PrintMessage(f"FreeCAD AI: {operation_name} successful\n")
            return True
        else:
            FreeCAD.Console.PrintWarning(
                f"FreeCAD AI: {operation_name} skipped - invalid signal or slot\n"
            )
            return False
    except Exception as e:
        FreeCAD.Console.PrintError(
            f"FreeCAD AI: CRASH PREVENTED in {operation_name}: {e}\n"
        )
        FreeCAD.Console.PrintError(
            f"FreeCAD AI: {operation_name} traceback: {traceback.format_exc()}\n"
        )
        return False


def safe_widget_operation(operation_func, operation_name, fallback_result=None):
    """Safely execute widget operations with comprehensive error handling."""
    try:
        FreeCAD.Console.PrintMessage(f"FreeCAD AI: Attempting {operation_name}...\n")
        result = operation_func()
        FreeCAD.Console.PrintMessage(f"FreeCAD AI: {operation_name} successful\n")
        return result
    except Exception as e:
        FreeCAD.Console.PrintError(
            f"FreeCAD AI: CRASH PREVENTED in {operation_name}: {e}\n"
        )
        FreeCAD.Console.PrintError(
            f"FreeCAD AI: {operation_name} traceback: {traceback.format_exc()}\n"
        )
        return fallback_result


class MCPMainWidget(QtWidgets.QDockWidget):
    """Main widget for FreeCAD AI addon with crash-safe initialization."""

    @crash_safe_wrapper("widget initialization")
    def __init__(self, parent=None):
        """Ultra-safe initialization - prevents all crashes by avoiding complex operations."""
        try:
            FreeCAD.Console.PrintMessage(
                "FreeCAD AI: Starting ultra-safe widget initialization...\n"
            )
            super(MCPMainWidget, self).__init__("FreeCAD AI", parent)
            self.provider_service = None
            self.agent_manager = None
            self.status_label = None
            self.tab_widget = None
            self.main_widget = None
            self.conversation_widget = None
            self.agents_widget = None
            self.settings_widget = None
            self.tools_widget = None
            self.agent_control_widget = None
            self.unified_connection_widget = None
            self._fully_initialized = False
            self._setup_basic_dock_properties()
            self._create_ultra_minimal_ui()
            # Automatically initialize the full UI (no click required)
            if not self._fully_initialized:
                self._initialize_full_functionality()
            FreeCAD.Console.PrintMessage(
                "FreeCAD AI: Ultra-safe widget created successfully\n"
            )
        except Exception as e:
            FreeCAD.Console.PrintError(
                f"FreeCAD AI: Even ultra-safe initialization failed: {e}\n"
            )
            try:
                self.main_widget = QtWidgets.QWidget()
                self.setWidget(self.main_widget)
            except (RuntimeError, AttributeError):
                # RuntimeError: Qt widget creation failed
                # AttributeError: Missing widget methods
                pass

    @crash_safe_wrapper("dock properties setup")
    def _setup_basic_dock_properties(self):
        """Set up basic dock properties with maximum safety."""
        try:
            if hasattr(QtCore, "Qt") and hasattr(QtCore.Qt, "LeftDockWidgetArea"):
                self.setAllowedAreas(
                    QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
                )
            if hasattr(QtWidgets.QDockWidget, "DockWidgetMovable"):
                self.setFeatures(
                    QtWidgets.QDockWidget.DockWidgetMovable
                    | QtWidgets.QDockWidget.DockWidgetFloatable
                )
        except Exception as e:
            FreeCAD.Console.PrintWarning(
                f"FreeCAD AI: Could not set dock properties: {e}\n"
            )

    @crash_safe_wrapper("ultra-minimal UI creation")
    def _create_ultra_minimal_ui(self):
        """Create the absolute minimal UI - just clickable text."""
        try:
            self.main_widget = QtWidgets.QWidget()
            self.setWidget(self.main_widget)
            layout = QtWidgets.QVBoxLayout(self.main_widget)
            layout.setContentsMargins(10, 10, 10, 10)
            title_label = QtWidgets.QLabel("🤖 FreeCAD AI")
            title_label.setStyleSheet(
                "font-weight: bold; font-size: 16px; margin-bottom: 10px;"
            )
            layout.addWidget(title_label)
            self.status_label = QtWidgets.QLabel(
                "Click here to initialize\n\n"
                "This minimal mode prevents crashes.\n"
                "Full features load on demand."
            )
            self.status_label.setStyleSheet(
                "padding: 15px; "
                "background-color: #e3f2fd; "
                "border: 2px solid #2196f3; "
                "border-radius: 8px; "
                "font-size: 12px; "
            )
            if hasattr(self.status_label, "mousePressEvent"):
                original_mouse_event = self.status_label.mousePressEvent

                def on_click(event):
                    try:
                        self._initialize_full_functionality()
                        if original_mouse_event:
                            original_mouse_event(event)
                    except Exception as e:
                        FreeCAD.Console.PrintWarning(
                            f"FreeCAD AI: Click handler error: {e}\n"
                        )

                self.status_label.mousePressEvent = on_click
            layout.addWidget(self.status_label)
            layout.addStretch()
            FreeCAD.Console.PrintMessage("FreeCAD AI: Ultra-minimal UI created\n")
        except Exception as e:
            FreeCAD.Console.PrintError(
                f"FreeCAD AI: Ultra-minimal UI creation failed: {e}\n"
            )
            self.status_label = None

    @crash_safe_wrapper("full functionality initialization")
    def _initialize_full_functionality(self):
        """Initialize the full widget functionality safely - SIMPLIFIED VERSION."""
        if self._fully_initialized:
            return
        try:
            FreeCAD.Console.PrintMessage(
                "FreeCAD AI: Starting simplified full initialization...\n"
            )
            if hasattr(self, "status_label") and self.status_label:
                self.status_label.setText("Initializing full interface...")
                self.status_label.setStyleSheet(
                    "padding: 15px; background-color: #ffecb3; color: #f57c00; border-radius: 8px; "
                    "font-size: 12px;"
                )
            self._init_services_safe()
            self._setup_full_ui_safe()
            self._connect_services_safe()
            self._fully_initialized = True
            if hasattr(self, "status_label") and self.status_label:
                self.status_label.setText("Ready")
                self.status_label.setStyleSheet(
                    "padding: 2px 8px; background-color: #c8e6c9; color: #2e7d32; border-radius: 10px; font-size: 11px;"
                )
            FreeCAD.Console.PrintMessage(
                "FreeCAD AI: Simplified initialization completed successfully\n"
            )
        except Exception as e:
            FreeCAD.Console.PrintError(
                f"FreeCAD AI: Simplified initialization failed: {e}\n"
            )
            if hasattr(self, "status_label") and self.status_label:
                try:
                    self.status_label.setText("Limited Mode - Click to retry")
                    self.status_label.setStyleSheet(
                        "padding: 15px; background-color: #ffecb3; color: #f57c00; border-radius: 8px; "
                        "font-size: 12px;"
                    )
                except (AttributeError, RuntimeError):
                    # AttributeError: Missing status_label methods
                    # RuntimeError: Widget destroyed or invalid state
                    pass

    @crash_safe_wrapper("services initialization")
    def _init_services_safe(self):
        """Safely initialize services without signal connections."""
        try:
            FreeCAD.Console.PrintMessage(
                "FreeCAD AI: Initializing services safely...\n"
            )
            self._init_agent_manager_safe()
            self._setup_provider_service_safe()
            FreeCAD.Console.PrintMessage("FreeCAD AI: Services initialized\n")
        except Exception as e:
            FreeCAD.Console.PrintWarning(
                f"FreeCAD AI: Service initialization failed: {e}\n"
            )

    @crash_safe_wrapper("full UI setup")
    def _setup_full_ui_safe(self):
        """Setup the full UI interface safely."""
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Setting up full UI safely...\n")
            if self.main_widget:
                old_layout = self.main_widget.layout()
                if old_layout:
                    while old_layout.count():
                        child = old_layout.takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()
                    if (
                        hasattr(QtWidgets, "QApplication")
                        and QtWidgets.QApplication.instance()
                    ):
                        QtWidgets.QApplication.processEvents()
                    old_layout.deleteLater()
                    self.main_widget.setLayout(None)

            # Create main layout
            layout = QtWidgets.QVBoxLayout()
            layout.setSpacing(2)
            layout.setContentsMargins(2, 2, 2, 2)
            self.main_widget.setLayout(layout)

            # Set minimum sizes and styling
            self.main_widget.setMinimumSize(400, 300)
            self.main_widget.setStyleSheet("background: #e0f7fa;")
            self.setMinimumWidth(400)
            self.resize(600, 400)

            # Create header layout
            header_layout = QtWidgets.QHBoxLayout()
            header_label = QtWidgets.QLabel("🤖 FreeCAD AI")
            header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            header_layout.addWidget(header_label)
            header_layout.addStretch()

            self.status_label = QtWidgets.QLabel("Setting up...")
            self.status_label.setStyleSheet(
                "padding: 2px 8px; background-color: #f0f0f0; border-radius: 10px; font-size: 11px;"
            )
            header_layout.addWidget(self.status_label)
            layout.addLayout(header_layout)

            # Create tab widget with explicit sizing
            self.tab_widget = QtWidgets.QTabWidget()
            if hasattr(self.tab_widget, "setUsesScrollButtons"):
                self.tab_widget.setUsesScrollButtons(True)
            if hasattr(self.tab_widget, "setElideMode") and hasattr(
                QtCore.Qt, "ElideRight"
            ):
                self.tab_widget.setElideMode(QtCore.Qt.ElideRight)

            # Set explicit size for tab widget to ensure visibility
            self.tab_widget.setMinimumSize(380, 250)
            self.tab_widget.setSizePolicy(
                QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding
            )

            layout.addWidget(self.tab_widget)

            # Create tabs
            self._create_tabs_ultra_safe()

            # Force immediate update and visibility
            self.main_widget.updateGeometry()
            self.tab_widget.updateGeometry()

            # Ensure widgets are visible
            self.main_widget.show()
            self.tab_widget.show()

            # Process events to ensure layout is applied
            if hasattr(QtWidgets, "QApplication") and QtWidgets.QApplication.instance():
                QtWidgets.QApplication.processEvents()

            FreeCAD.Console.PrintMessage(
                f"FreeCAD AI: Full UI setup complete. DockWidget size: {self.size()}, MainWidget size: {self.main_widget.size()}, TabWidget size: {self.tab_widget.size()}\n"
            )
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Full UI setup failed: {e}\n")
            self._create_fallback_ui()

    @crash_safe_wrapper("tab creation")
    def _create_tabs_ultra_safe(self):
        """Create tabs with maximum safety and error handling."""
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Creating tabs ultra-safely...\n")

            widget_configs = [
                ("providers_widget", "ProvidersWidget", "Providers"),
                ("enhanced_conversation_widget", "EnhancedConversationWidget", "Chat"),
                (
                    "enhanced_agent_control_widget",
                    "EnhancedAgentControlWidget",
                    "Agent",
                ),
                ("tools_widget", "ToolsWidget", "Tools"),
                ("unified_connection_widget", "UnifiedConnectionWidget", "Connections"),
                ("settings_widget", "SettingsWidget", "Settings"),
            ]
            for attr_name, class_name, tab_name in widget_configs:
                try:
                    module_name = "gui." + attr_name
                    if "tools_widget" in attr_name:
                        module_name = "gui.tools_widget_compact"
                        class_name = "ToolsWidget"
                    try:
                        module = importlib.import_module(
                            "." + module_name, package=__package__
                        )
                    except (ImportError, ValueError):
                        module = importlib.import_module(module_name)
                    widget_class = getattr(module, class_name)
                    widget_instance = widget_class()
                    setattr(self, attr_name, widget_instance)
                    self.tab_widget.addTab(widget_instance, tab_name)
                    FreeCAD.Console.PrintMessage(
                        f"FreeCAD AI: Successfully created {tab_name} tab\n"
                    )
                except Exception as e:
                    FreeCAD.Console.PrintWarning(
                        f"FreeCAD AI: Failed to create {tab_name} tab: {e}\n"
                    )
                    placeholder = QtWidgets.QWidget()
                    placeholder_layout = QtWidgets.QVBoxLayout(placeholder)
                    error_label = QtWidgets.QLabel(
                        f"{tab_name}\n\nLoading failed:\n{str(e)[:100]}..."
                    )
                    error_label.setStyleSheet("padding: 10px; color: #666;")
                    placeholder_layout.addWidget(error_label)
                    self.tab_widget.addTab(placeholder, tab_name)
                    setattr(self, attr_name, placeholder)

            FreeCAD.Console.PrintMessage(
                f"FreeCAD AI: Tab creation complete. Tab count: {self.tab_widget.count()}\n"
            )

            # Connect to tab change signal to refresh provider selectors when tabs become active
            if hasattr(self.tab_widget, "currentChanged"):
                safe_signal_connect(
                    self.tab_widget.currentChanged,
                    self._on_tab_changed,
                    "tab change signal connection",
                )

        except Exception as e:
            FreeCAD.Console.PrintError(
                f"FreeCAD AI: Ultra-safe tab creation failed: {e}\n"
            )
            # Create simple fallback tabs
            for name in ["Test", "Chat", "Settings"]:
                try:
                    tab = QtWidgets.QWidget()
                    tab_layout = QtWidgets.QVBoxLayout(tab)
                    tab_layout.addWidget(QtWidgets.QLabel(f"{name} - Error loading"))
                    self.tab_widget.addTab(tab, name)
                except (RuntimeError, AttributeError):
                    # RuntimeError: Qt widget creation/operation failed
                    # AttributeError: Missing widget method
                    pass

    @crash_safe_wrapper("tab change handling")
    def _on_tab_changed(self, index):
        """Handle tab change to refresh provider selectors when needed."""
        try:
            if index < 0 or not hasattr(self, "tab_widget"):
                return

            current_widget = self.tab_widget.widget(index)
            if not current_widget:
                return

            # Check if the current widget has a provider selector that needs refreshing
            if hasattr(current_widget, "provider_selector"):
                safe_widget_operation(
                    lambda: current_widget.provider_selector.refresh_on_show(),
                    "provider selector refresh on tab activation",
                )

            # Also check for provider selectors in sub-widgets
            for child in current_widget.findChildren(QtWidgets.QWidget):
                if hasattr(child, "refresh_on_show"):
                    safe_widget_operation(
                        lambda: child.refresh_on_show(),
                        "provider selector refresh on tab activation (child widget)",
                    )

        except Exception as e:
            FreeCAD.Console.PrintWarning(
                f"FreeCAD AI: Tab change handling error: {e}\n"
            )

    @crash_safe_wrapper("service connections")
    def _connect_services_safe(self):
        """Safely connect services to widgets after everything is initialized."""
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Connecting services safely...\n")

            # Connect provider service to widgets
            if self.provider_service:
                if hasattr(self, "providers_widget") and hasattr(
                    self.providers_widget, "set_provider_service"
                ):
                    safe_widget_operation(
                        lambda: self.providers_widget.set_provider_service(
                            self.provider_service
                        ),
                        "provider service connection to providers widget",
                    )
                if hasattr(self, "conversation_widget") and hasattr(
                    self.conversation_widget, "set_provider_service"
                ):
                    safe_widget_operation(
                        lambda: self.conversation_widget.set_provider_service(
                            self.provider_service
                        ),
                        "provider service connection to conversation widget",
                    )
                if hasattr(self, "agent_control_widget") and hasattr(
                    self.agent_control_widget, "set_provider_service"
                ):
                    safe_widget_operation(
                        lambda: self.agent_control_widget.set_provider_service(
                            self.provider_service
                        ),
                        "provider service connection to agent control widget",
                    )

                # Connect config manager to provider selectors
                if (
                    hasattr(self.provider_service, "config_manager")
                    and self.provider_service.config_manager
                ):
                    config_manager = self.provider_service.config_manager

                    # Connect to conversation widget provider selector
                    if hasattr(self, "conversation_widget") and hasattr(
                        self.conversation_widget, "provider_selector"
                    ):
                        safe_widget_operation(
                            lambda: self.conversation_widget.provider_selector.set_config_manager(
                                config_manager
                            ),
                            "config manager connection to conversation provider selector",
                        )

                    # Connect to agent control widget provider selector
                    if hasattr(self, "agent_control_widget") and hasattr(
                        self.agent_control_widget, "provider_selector"
                    ):
                        safe_widget_operation(
                            lambda: self.agent_control_widget.provider_selector.set_config_manager(
                                config_manager
                            ),
                            "config manager connection to agent provider selector",
                        )

                if hasattr(self.provider_service, "provider_status_changed"):
                    safe_signal_connect(
                        self.provider_service.provider_status_changed,
                        self._on_provider_status_changed,
                        "provider status signal connection",
                    )
                if hasattr(self.provider_service, "providers_updated"):
                    safe_signal_connect(
                        self.provider_service.providers_updated,
                        self._on_providers_updated,
                        "providers updated signal connection",
                    )
                if hasattr(self.provider_service, "initialize_providers_from_config"):
                    safe_widget_operation(
                        lambda: self.provider_service.initialize_providers_from_config(),
                        "provider initialization from config",
                    )
            if self.agent_manager:
                if hasattr(self, "conversation_widget") and hasattr(
                    self.conversation_widget, "set_agent_manager"
                ):
                    safe_widget_operation(
                        lambda: self.conversation_widget.set_agent_manager(
                            self.agent_manager
                        ),
                        "agent manager connection to conversation widget",
                    )
                if hasattr(self, "agent_control_widget") and hasattr(
                    self.agent_control_widget, "set_agent_manager"
                ):
                    safe_widget_operation(
                        lambda: self.agent_control_widget.set_agent_manager(
                            self.agent_manager
                        ),
                        "agent manager connection to agent control widget",
                    )
            FreeCAD.Console.PrintMessage("FreeCAD AI: Service connections complete\n")
        except Exception as e:
            FreeCAD.Console.PrintWarning(
                f"FreeCAD AI: Service connection failed: {e}\n"
            )

    @crash_safe_wrapper("fallback UI creation")
    def _create_fallback_ui(self):
        """Create a minimal fallback UI if normal UI creation fails."""
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Creating fallback UI...\n")
            if self.main_widget:
                old_layout = self.main_widget.layout()
                if old_layout:
                    while old_layout.count():
                        child = old_layout.takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()
                    self.main_widget.setLayout(None)
                    old_layout.deleteLater()
            layout = QtWidgets.QVBoxLayout()
            self.main_widget.setLayout(layout)
            error_label = QtWidgets.QLabel(
                "FreeCAD AI - Limited Mode\n\nSome components failed to load.\nBasic functionality may be available."
            )
            error_label.setStyleSheet(
                "padding: 10px; background-color: #fff3e0; border-radius: 5px;"
            )
            layout.addWidget(error_label)
            if hasattr(self, "status_label") and self.status_label:
                self.status_label.setText("Limited Mode")
                self.status_label.setStyleSheet(
                    "padding: 2px 8px; background-color: #fff3e0; color: #ef6c00; border-radius: 10px; font-size: 11px;"
                )
            FreeCAD.Console.PrintMessage("FreeCAD AI: Fallback UI created\n")
        except Exception as e:
            FreeCAD.Console.PrintError(
                f"FreeCAD AI: Even fallback UI creation failed: {e}\n"
            )

    @crash_safe_wrapper("agent manager initialization")
    def _init_agent_manager_safe(self):
        """Safely initialize the agent manager with comprehensive error handling."""
        try:
            if self.agent_manager is not None:
                FreeCAD.Console.PrintMessage(
                    "FreeCAD AI: Agent manager already initialized\n"
                )
                return
            FreeCAD.Console.PrintMessage(
                "FreeCAD AI: Safe agent manager initialization...\n"
            )

            # Try using the wrapper first
            try:
                from ..core.agent_manager_wrapper import (
                    get_agent_manager,
                    is_agent_manager_available,
                )

                if is_agent_manager_available():
                    self.agent_manager = get_agent_manager()
                    FreeCAD.Console.PrintMessage(
                        "FreeCAD AI: AgentManager initialized via wrapper\n"
                    )
                    return
            except ImportError:
                pass

            # Fallback to original initialization
            agent_manager_imported = False
            try:
                from ..core.agent_manager import AgentManager

                agent_manager_imported = True
                FreeCAD.Console.PrintMessage(
                    "FreeCAD AI: AgentManager imported via relative path\n"
                )
            except ImportError as e:
                FreeCAD.Console.PrintMessage(
                    f"FreeCAD AI: Relative import failed: {e}\n"
                )
            if not agent_manager_imported:
                try:
                    from core.agent_manager import AgentManager

                    agent_manager_imported = True
                    FreeCAD.Console.PrintMessage(
                        "FreeCAD AI: AgentManager imported via direct path\n"
                    )
                except ImportError as e:
                    FreeCAD.Console.PrintMessage(
                        f"FreeCAD AI: Direct import failed: {e}\n"
                    )
            if not agent_manager_imported:
                try:
                    import os
                    import sys

                    parent_dir = os.path.dirname(
                        os.path.dirname(os.path.abspath(__file__))
                    )
                    if parent_dir not in sys.path:
                        sys.path.insert(0, parent_dir)
                    from core.agent_manager import AgentManager

                    agent_manager_imported = True
                    FreeCAD.Console.PrintMessage(
                        "FreeCAD AI: AgentManager imported after adding to sys.path\n"
                    )
                except ImportError as e:
                    FreeCAD.Console.PrintMessage(
                        f"FreeCAD AI: Import with sys.path modification failed: {e}\n"
                    )
            if not agent_manager_imported:
                FreeCAD.Console.PrintWarning(
                    "FreeCAD AI: Could not import AgentManager - proceeding without it\n"
                )
                self.agent_manager = None
                return
            self.agent_manager = AgentManager()
            FreeCAD.Console.PrintMessage(
                "FreeCAD AI: AgentManager instance created successfully\n"
            )
            safe_widget_operation(
                lambda: self.agent_manager.register_callback(
                    "on_mode_change", self._on_agent_mode_changed
                ),
                "agent mode change callback registration",
            )
            safe_widget_operation(
                lambda: self.agent_manager.register_callback(
                    "on_state_change", self._on_agent_state_changed
                ),
                "agent state change callback registration",
            )
            FreeCAD.Console.PrintMessage(
                "FreeCAD AI: Agent Manager safely initialized\n"
            )
        except Exception as e:
            FreeCAD.Console.PrintWarning(
                f"FreeCAD AI: Safe agent manager init failed: {e}\n"
            )
            self.agent_manager = None

    @crash_safe_wrapper("provider service setup")
    def _setup_provider_service_safe(self):
        """Safely setup the provider integration service without immediate signal connections."""
        try:
            if self.provider_service is not None:
                FreeCAD.Console.PrintMessage(
                    "FreeCAD AI: Provider service already initialized\n"
                )
                return
            FreeCAD.Console.PrintMessage("FreeCAD AI: Safe provider service setup...\n")

            # Try using the wrapper first
            try:
                from ..ai.provider_service_wrapper import (
                    get_provider_service,
                    is_provider_service_available,
                )

                if is_provider_service_available():
                    self.provider_service = get_provider_service()
                    FreeCAD.Console.PrintMessage(
                        "FreeCAD AI: Provider service initialized via wrapper\n"
                    )
                    return
            except ImportError:
                pass

            # Fallback to original initialization
            provider_service_imported = False
            try:
                from ..ai.provider_integration_service import get_provider_service

                provider_service_imported = True
                FreeCAD.Console.PrintMessage(
                    "FreeCAD AI: Provider service imported via relative path\n"
                )
            except ImportError as e:
                FreeCAD.Console.PrintMessage(
                    f"FreeCAD AI: Relative import failed: {e}\n"
                )
            if not provider_service_imported:
                try:
                    from ai.provider_integration_service import get_provider_service

                    provider_service_imported = True
                    FreeCAD.Console.PrintMessage(
                        "FreeCAD AI: Provider service imported via direct path\n"
                    )
                except ImportError as e:
                    FreeCAD.Console.PrintMessage(
                        f"FreeCAD AI: Direct import failed: {e}\n"
                    )
            if not provider_service_imported:
                try:
                    import os
                    import sys

                    parent_dir = os.path.dirname(
                        os.path.dirname(os.path.abspath(__file__))
                    )
                    if parent_dir not in sys.path:
                        sys.path.insert(0, parent_dir)
                    from ai.provider_integration_service import get_provider_service

                    provider_service_imported = True
                    FreeCAD.Console.PrintMessage(
                        "FreeCAD AI: Provider service imported after adding to sys.path\n"
                    )
                except ImportError as e:
                    FreeCAD.Console.PrintMessage(
                        f"FreeCAD AI: Import with sys.path modification failed: {e}\n"
                    )
            if not provider_service_imported:
                FreeCAD.Console.PrintWarning(
                    "FreeCAD AI: Could not import provider service - proceeding without it\n"
                )
                self.provider_service = None
                return
            self.provider_service = get_provider_service()
            FreeCAD.Console.PrintMessage(
                f"FreeCAD AI: Provider service created: {self.provider_service is not None}\n"
            )
            if self.provider_service:
                FreeCAD.Console.PrintMessage(
                    "FreeCAD AI: Provider service created successfully - signals will be connected later\n"
                )
            else:
                FreeCAD.Console.PrintWarning("FreeCAD AI: Provider service is None\n")
        except Exception as e:
            FreeCAD.Console.PrintWarning(
                f"FreeCAD AI: Safe provider service setup failed: {e}\n"
            )
            self.provider_service = None

    @crash_safe_wrapper("provider status change handling")
    def _on_provider_status_changed(
        self, provider_name: str, status: str, message: str
    ):
        """Handle provider status changes."""
        if not hasattr(self, "status_label") or self.status_label is None:
            FreeCAD.Console.PrintMessage(
                f"FreeCAD AI: Status change ignored - no status_label: {provider_name} -> {status}\n"
            )
            return
        try:
            if status == "connected":
                self.status_label.setText(f"✅ {provider_name}")
                self.status_label.setStyleSheet(
                    "padding: 2px 8px; background-color: #c8e6c9; color: #2e7d32; border-radius: 10px; font-size: 11px;"
                )
            elif status == "error":
                self.status_label.setText(f"❌ {provider_name}")
                self.status_label.setStyleSheet(
                    "padding: 2px 8px; background-color: #ffcdd2; color: #c62828; border-radius: 10px; font-size: 11px;"
                )
            else:
                self.status_label.setText(f"⚡ {provider_name}")
                self.status_label.setStyleSheet(
                    "padding: 2px 8px; background-color: #fff3e0; color: #ef6c00; border-radius: 10px; font-size: 11px;"
                )
        except Exception as e:
            FreeCAD.Console.PrintError(
                f"FreeCAD AI: Error updating status label: {e}\n"
            )

    @crash_safe_wrapper("providers update handling")
    def _on_providers_updated(self):
        """Handle providers list update."""
        if not hasattr(self, "status_label") or self.status_label is None:
            FreeCAD.Console.PrintMessage(
                "FreeCAD AI: Providers update ignored - no status_label\n"
            )
            return
        try:
            if self.provider_service:
                active_count = len(self.provider_service.get_active_providers())
                total_count = len(self.provider_service.get_all_providers())
                self.status_label.setText(f"{active_count}/{total_count} active")
                if active_count > 0:
                    self.status_label.setStyleSheet(
                        "padding: 2px 8px; background-color: #c8e6c9; color: #2e7d32; border-radius: 10px; font-size: 11px;"
                    )
                else:
                    self.status_label.setStyleSheet(
                        "padding: 2px 8px; background-color: #f0f0f0; color: #666; border-radius: 10px; font-size: 11px;"
                    )
        except Exception as e:
            FreeCAD.Console.PrintError(
                f"FreeCAD AI: Error updating providers status: {e}\n"
            )

    @crash_safe_wrapper("agent mode change handling")
    def _on_agent_mode_changed(self, old_mode, new_mode):
        """Handle agent mode change callback."""
        if not hasattr(self, "status_label") or self.status_label is None:
            FreeCAD.Console.PrintMessage(
                f"FreeCAD AI: Agent mode change ignored - no status_label: {old_mode} -> {new_mode}\n"
            )
            return
        try:
            mode_display = "Chat" if new_mode.value == "chat" else "Agent"
            self.status_label.setText(f"Mode: {mode_display}")
        except Exception as e:
            FreeCAD.Console.PrintError(
                f"FreeCAD AI: Error updating agent mode status: {e}\n"
            )

    @crash_safe_wrapper("agent state change handling")
    def _on_agent_state_changed(self, old_state, new_state):
        """Handle agent state change callback."""
        if not hasattr(self, "status_label") or self.status_label is None:
            FreeCAD.Console.PrintMessage(
                f"FreeCAD AI: Agent state change ignored - no status_label: {old_state} -> {new_state}\n"
            )
            return
        try:
            state_display = {
                "idle": "Ready",
                "planning": "Planning...",
                "executing": "Executing...",
                "paused": "Paused",
                "error": "Error",
                "completed": "Completed",
            }
            status_text = state_display.get(new_state.value, new_state.value)
            mode_text = (
                "Chat" if self.agent_manager.current_mode.value == "chat" else "Agent"
            )
            self.status_label.setText(f"{mode_text}: {status_text}")
            if new_state.value == "executing":
                self.status_label.setStyleSheet(
                    "padding: 2px 8px; background-color: #fff3e0; color: #ef6c00; border-radius: 10px; font-size: 11px;"
                )
            elif new_state.value == "error":
                self.status_label.setStyleSheet(
                    "padding: 2px 8px; background-color: #ffcdd2; color: #c62828; border-radius: 10px; font-size: 11px;"
                )
            elif new_state.value == "completed":
                self.status_label.setStyleSheet(
                    "padding: 2px 8px; background-color: #c8e6c9; color: #2e7d32; border-radius: 10px; font-size: 11px;"
                )
            elif new_state.value == "planning":
                self.status_label.setStyleSheet(
                    "padding: 2px 8px; background-color: #e1f5fe; color: #0277bd; border-radius: 10px; font-size: 11px;"
                )
            else:
                self.status_label.setStyleSheet(
                    "padding: 2px 8px; background-color: #f0f0f0; border-radius: 10px; font-size: 11px;"
                )
        except Exception as e:
            FreeCAD.Console.PrintError(
                f"FreeCAD AI: Error updating agent state status: {e}\n"
            )

    def get_provider_service(self):
        """Get the provider service instance."""
        return self.provider_service

    def get_agent_manager(self):
        """Get the agent manager instance."""
        return self.agent_manager
