"""Main Widget for FreeCAD AI FreeCAD Addon"""

import FreeCAD

# Safe Qt imports with comprehensive fallback to prevent crashes
try:
    from PySide2 import QtCore, QtWidgets
    HAS_PYSIDE2 = True
    FreeCAD.Console.PrintMessage("FreeCAD AI: Using PySide2\n")
except ImportError:
    try:
        from PySide import QtCore
        from PySide import QtGui as QtWidgets
        HAS_PYSIDE2 = False
        FreeCAD.Console.PrintMessage("FreeCAD AI: Using PySide (fallback)\n")
    except ImportError:
        FreeCAD.Console.PrintError("FreeCAD AI: No Qt bindings available - minimal functionality\n")
        HAS_PYSIDE2 = False
        # Create minimal dummy classes to prevent crashes
        class QtWidgets:
            class QDockWidget:
                def __init__(self, *args, **kwargs): pass
                def setAllowedAreas(self, *args): pass
                def setFeatures(self, *args): pass
                def setWidget(self, widget): pass
                def setMinimumWidth(self, width): pass
                def resize(self, width, height): pass
            class QWidget:
                def __init__(self, *args, **kwargs): pass
            class QVBoxLayout:
                def __init__(self, *args, **kwargs): pass
                def addWidget(self, widget): pass
                def addLayout(self, layout): pass
                def setSpacing(self, spacing): pass
                def setContentsMargins(self, *args): pass
            class QHBoxLayout:
                def __init__(self, *args, **kwargs): pass
                def addWidget(self, widget): pass
                def addStretch(self): pass
            class QLabel:
                def __init__(self, *args, **kwargs): pass
                def setStyleSheet(self, style): pass
                def setText(self, text): pass
            class QTabWidget:
                def __init__(self, *args, **kwargs): pass
                def setUsesScrollButtons(self, value): pass
                def setElideMode(self, mode): pass
        class QtCore:
            class Qt:
                RightDockWidgetArea = None
                LeftDockWidgetArea = None
                ElideRight = None
            class QTimer:
                @staticmethod
                def singleShot(interval, callback): pass
            class QObject:
                def __init__(self): pass


class MCPMainWidget(QtWidgets.QDockWidget):
    """Main widget for FreeCAD AI addon with crash-safe initialization."""

    def __init__(self, parent=None):
        """Nuclear minimal initialization - prevents all PySide2 segfaults.
        
        Creates only static text until user explicitly requests functionality.
        NO timers, NO complex widgets, NO imports until user interaction.
        """
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Nuclear minimal widget initialization...\n")

            # Initialize parent class with minimal parameters
            super(MCPMainWidget, self).__init__("FreeCAD AI", parent)

            # Initialize all service references to None immediately
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
            
            # Flags to track initialization state
            self._fully_initialized = False
            self._initialization_in_progress = False

            # Set basic dock properties with maximum safety
            try:
                if hasattr(QtCore, 'Qt') and hasattr(QtCore.Qt, 'LeftDockWidgetArea'):
                    self.setAllowedAreas(
                        QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
                    )

                if hasattr(QtWidgets.QDockWidget, 'DockWidgetMovable'):
                    self.setFeatures(
                        QtWidgets.QDockWidget.DockWidgetMovable
                        | QtWidgets.QDockWidget.DockWidgetFloatable
                    )
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"FreeCAD AI: Could not set dock properties: {e}\n")

            # Create nuclear minimal UI - just clickable text
            self._create_nuclear_minimal_ui()

            FreeCAD.Console.PrintMessage("FreeCAD AI: Nuclear minimal widget created successfully\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Even nuclear minimal initialization failed: {e}\n")
            # Last resort - do absolutely nothing

    def _create_nuclear_minimal_ui(self):
        """Create the absolute minimal UI - just clickable text."""
        try:
            # Create the most basic widget structure
            self.main_widget = QtWidgets.QWidget()
            self.setWidget(self.main_widget)
            
            # Single layout with one clickable label
            layout = QtWidgets.QVBoxLayout(self.main_widget)
            layout.setContentsMargins(10, 10, 10, 10)
            
            # Title
            title_label = QtWidgets.QLabel("🤖 FreeCAD AI")
            title_label.setStyleSheet("font-weight: bold; font-size: 16px; margin-bottom: 10px;")
            layout.addWidget(title_label)
            
            # Status/instruction label that can be clicked
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
                "cursor: pointer;"
            )
            
            # Make it clickable if possible
            if hasattr(self.status_label, 'mousePressEvent'):
                original_mouse_event = self.status_label.mousePressEvent
                def on_click(event):
                    try:
                        self._on_user_requested_initialization()
                        if original_mouse_event:
                            original_mouse_event(event)
                    except Exception as e:
                        FreeCAD.Console.PrintWarning(f"FreeCAD AI: Click handler error: {e}\n")
                self.status_label.mousePressEvent = on_click
            
            layout.addWidget(self.status_label)
            
            # Add stretch to center content
            layout.addStretch()
            
            FreeCAD.Console.PrintMessage("FreeCAD AI: Nuclear minimal UI created\n")
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Nuclear minimal UI creation failed: {e}\n")
            self.status_label = None

    def _on_user_requested_initialization(self):
        """Initialize full functionality only when user explicitly requests it."""
        if self._initialization_in_progress or self._fully_initialized:
            return
            
        try:
            self._initialization_in_progress = True
            FreeCAD.Console.PrintMessage("FreeCAD AI: User requested full initialization...\n")
            
            if self.status_label:
                self.status_label.setText("Initializing full interface...\nPlease wait...")
                self.status_label.setStyleSheet(
                    "padding: 15px; background-color: #fff3e0; border: 2px solid #ff9800; "
                    "border-radius: 8px; font-size: 12px;"
                )
            
            # Now try the full initialization in a safer context
            self._initialize_full_functionality()
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: User-requested initialization failed: {e}\n")
            if self.status_label:
                self.status_label.setText(f"Initialization failed:\n{str(e)[:50]}...\n\nClick to retry")
                self.status_label.setStyleSheet(
                    "padding: 15px; background-color: #ffebee; border: 2px solid #f44336; "
                    "border-radius: 8px; font-size: 12px; cursor: pointer;"
                )
        finally:
            self._initialization_in_progress = False

    def _initialize_full_functionality(self):
        """Initialize the full widget functionality safely - NUCLEAR MINIMAL VERSION."""
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Starting nuclear minimal initialization...\n")
            
            # Just update the status to show we're active - NO complex UI creation
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.setText("Ready")
                self.status_label.setStyleSheet(
                    "padding: 2px 8px; background-color: #c8e6c9; color: #2e7d32; border-radius: 10px; font-size: 11px;"
                )
            
            # Mark as initialized without doing anything complex
            self._fully_initialized = True
            FreeCAD.Console.PrintMessage("FreeCAD AI: Nuclear minimal initialization completed successfully\n")
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Nuclear minimal initialization failed: {e}\n")
            # Even if this fails, don't raise - just mark as failed
            if hasattr(self, 'status_label') and self.status_label:
                try:
                    self.status_label.setText("Limited Mode")
                    self.status_label.setStyleSheet(
                        "padding: 2px 8px; background-color: #ffecb3; color: #f57c00; border-radius: 10px; font-size: 11px;"
                    )
                except Exception:
                    pass

    def _setup_full_ui(self):
        """Setup the full UI interface."""
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Setting up full UI...\n")
            
            # Clear the minimal UI
            if self.main_widget:
                old_layout = self.main_widget.layout()
                if old_layout:
                    # Clear all widgets from old layout
                    while old_layout.count():
                        child = old_layout.takeAt(0)
                        if child.widget():
                            child.widget().deleteLater()
                    old_layout.deleteLater()
            
            # Create new layout
            layout = QtWidgets.QVBoxLayout(self.main_widget)
            layout.setSpacing(2)
            layout.setContentsMargins(2, 2, 2, 2)

            # Compact header with inline status
            header_layout = QtWidgets.QHBoxLayout()
            header_label = QtWidgets.QLabel("🤖 FreeCAD AI")
            header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            header_layout.addWidget(header_label)

            header_layout.addStretch()

            # Recreate status label
            self.status_label = QtWidgets.QLabel("Ready")
            self.status_label.setStyleSheet(
                "padding: 2px 8px; background-color: #c8e6c9; color: #2e7d32; border-radius: 10px; font-size: 11px;"
            )
            header_layout.addWidget(self.status_label)

            layout.addLayout(header_layout)

            # Create tab widget
            self.tab_widget = QtWidgets.QTabWidget()
            if hasattr(self.tab_widget, 'setUsesScrollButtons'):
                self.tab_widget.setUsesScrollButtons(True)
            if hasattr(self.tab_widget, 'setElideMode') and hasattr(QtCore.Qt, 'ElideRight'):
                self.tab_widget.setElideMode(QtCore.Qt.ElideRight)
            
            layout.addWidget(self.tab_widget)
            
            # Create tabs with nuclear safety
            self._create_tabs_nuclear_safe()

            FreeCAD.Console.PrintMessage("FreeCAD AI: Full UI setup complete\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Full UI setup failed: {e}\n")
            raise

    def _setup_basic_dock_properties(self):
        """Set up basic dock properties with maximum safety."""
        try:
            if hasattr(QtCore, 'Qt') and hasattr(QtCore.Qt, 'LeftDockWidgetArea'):
                self.setAllowedAreas(
                    QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
                )

            if hasattr(QtWidgets.QDockWidget, 'DockWidgetMovable'):
                self.setFeatures(
                    QtWidgets.QDockWidget.DockWidgetMovable
                    | QtWidgets.QDockWidget.DockWidgetFloatable
                )
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"FreeCAD AI: Could not set dock properties: {e}\n")

    def _create_minimal_widget(self):
        """Create the absolute minimum widget to prevent crashes."""
        try:
            self.main_widget = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(self.main_widget)
            
            # Create a simple status label
            self.status_label = QtWidgets.QLabel("Initializing FreeCAD AI...")
            self.status_label.setStyleSheet(
                "padding: 10px; background-color: #f0f0f0; border-radius: 5px; font-size: 12px;"
            )
            layout.addWidget(self.status_label)
            
            self.setWidget(self.main_widget)
            FreeCAD.Console.PrintMessage("FreeCAD AI: Minimal widget created successfully\n")
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Failed to create minimal widget: {e}\n")
            self._create_error_widget(str(e))

    def _create_error_widget(self, error_message):
        """Create a simple error display widget."""
        try:
            self.main_widget = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(self.main_widget)
            
            error_label = QtWidgets.QLabel(f"FreeCAD AI Error:\n{error_message}")
            error_label.setStyleSheet(
                "padding: 10px; background-color: #ffcdd2; color: #c62828; border-radius: 5px;"
            )
            layout.addWidget(error_label)
            
            self.setWidget(self.main_widget)
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Even error widget creation failed: {e}\n")

    def _delayed_initialization_phase1(self):
        """Phase 1 of delayed initialization - agent manager and basic services."""
        if self._initialization_failed:
            return
            
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Starting delayed initialization phase 1...\n")
            self.status_label.setText("Setting up services...")
            
            # Initialize agent manager (safe - no signals)
            self._init_agent_manager_safe()
            
            # Schedule phase 2
            if hasattr(QtCore.QTimer, 'singleShot'):
                QtCore.QTimer.singleShot(200, self._delayed_initialization_phase2)
            else:
                self._delayed_initialization_phase2()
                
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Phase 1 initialization failed: {e}\n")
            self.status_label.setText(f"Init Error Phase 1: {str(e)[:30]}...")

    def _delayed_initialization_phase2(self):
        """Phase 2 of delayed initialization - UI setup."""
        if self._initialization_failed:
            return
            
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Starting delayed initialization phase 2...\n")
            self.status_label.setText("Building interface...")
            
            # Setup UI components
            self._setup_ui_safe()
            self._ui_initialized = True
            
            # Schedule phase 3
            if hasattr(QtCore.QTimer, 'singleShot'):
                QtCore.QTimer.singleShot(300, self._delayed_initialization_phase3)
            else:
                self._delayed_initialization_phase3()
                
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Phase 2 initialization failed: {e}\n")
            self.status_label.setText(f"UI Error: {str(e)[:30]}...")

    def _delayed_initialization_phase3(self):
        """Phase 3 of delayed initialization - provider service setup."""
        if self._initialization_failed:
            return
            
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Starting delayed initialization phase 3...\n")
            self.status_label.setText("Connecting services...")
            
            # Setup provider service (without immediate signal connections)
            self._setup_provider_service_safe()
            self._services_initialized = True
            
            # Schedule phase 4
            if hasattr(QtCore.QTimer, 'singleShot'):
                QtCore.QTimer.singleShot(400, self._delayed_initialization_phase4)
            else:
                self._delayed_initialization_phase4()
                
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Phase 3 initialization failed: {e}\n")
            self.status_label.setText(f"Service Error: {str(e)[:30]}...")

    def _delayed_initialization_phase4(self):
        """Phase 4 of delayed initialization - widget connections and final setup."""
        if self._initialization_failed:
            return
            
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Starting delayed initialization phase 4...\n")
            self.status_label.setText("Finalizing setup...")
            
            # Connect widgets to services
            self._connect_widgets_to_service_safe()
            self._widgets_connected = True
            
            # Initialize providers now that everything is ready
            self._initialize_providers_after_ui()
            
            # Final setup
            self._finalize_initialization()
            
            FreeCAD.Console.PrintMessage("FreeCAD AI: All initialization phases complete\n")
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Phase 4 initialization failed: {e}\n")
            self.status_label.setText(f"Final Error: {str(e)[:30]}...")

    def _finalize_initialization(self):
        """Final setup after all phases complete."""
        try:
            # Set sizing safely
            self.setMinimumWidth(350)
            self.resize(450, 700)
            
            # Load persisted mode
            self._load_persisted_mode()
            
            # Update status to ready
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.setText("Ready")
                self.status_label.setStyleSheet(
                    "padding: 2px 8px; background-color: #c8e6c9; color: #2e7d32; border-radius: 10px; font-size: 11px;"
                )
            
            FreeCAD.Console.PrintMessage("FreeCAD AI: Widget fully initialized and ready\n")
            
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"FreeCAD AI: Finalization warning: {e}\n")

    def _init_agent_manager_safe(self):
        """Safely initialize the agent manager with comprehensive error handling."""
        try:
            if self.agent_manager is not None:
                FreeCAD.Console.PrintMessage("FreeCAD AI: Agent manager already initialized\n")
                return

            FreeCAD.Console.PrintMessage("FreeCAD AI: Safe agent manager initialization...\n")
            
            # Try multiple import strategies for agent manager
            agent_manager_imported = False

            # Strategy 1: Relative import
            try:
                from ..core.agent_manager import AgentManager
                agent_manager_imported = True
                FreeCAD.Console.PrintMessage("FreeCAD AI: AgentManager imported via relative path\n")
            except ImportError as e:
                FreeCAD.Console.PrintMessage(f"FreeCAD AI: Relative import failed: {e}\n")

            # Strategy 2: Direct import
            if not agent_manager_imported:
                try:
                    from core.agent_manager import AgentManager
                    agent_manager_imported = True
                    FreeCAD.Console.PrintMessage("FreeCAD AI: AgentManager imported via direct path\n")
                except ImportError as e:
                    FreeCAD.Console.PrintMessage(f"FreeCAD AI: Direct import failed: {e}\n")

            # Strategy 3: Add parent to path
            if not agent_manager_imported:
                try:
                    import os
                    import sys
                    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if parent_dir not in sys.path:
                        sys.path.insert(0, parent_dir)
                    from core.agent_manager import AgentManager
                    agent_manager_imported = True
                    FreeCAD.Console.PrintMessage("FreeCAD AI: AgentManager imported after adding to sys.path\n")
                except ImportError as e:
                    FreeCAD.Console.PrintMessage(f"FreeCAD AI: Import with sys.path modification failed: {e}\n")

            if not agent_manager_imported:
                FreeCAD.Console.PrintWarning("FreeCAD AI: Could not import AgentManager - proceeding without it\n")
                self.agent_manager = None
                return

            # Create agent manager instance
            self.agent_manager = AgentManager()
            FreeCAD.Console.PrintMessage("FreeCAD AI: AgentManager instance created successfully\n")

            # Register callbacks safely - no signal connections yet
            self.agent_manager.register_callback("on_mode_change", self._on_agent_mode_changed)
            self.agent_manager.register_callback("on_state_change", self._on_agent_state_changed)

            FreeCAD.Console.PrintMessage("FreeCAD AI: Agent Manager safely initialized\n")

        except Exception as e:
            FreeCAD.Console.PrintWarning(f"FreeCAD AI: Safe agent manager init failed: {e}\n")
            self.agent_manager = None

    def _setup_ui_safe(self):
        """Safely setup the user interface with comprehensive error handling."""
        try:
            if self._ui_initialized:
                FreeCAD.Console.PrintMessage("FreeCAD AI: UI already initialized\n")
                return

            FreeCAD.Console.PrintMessage("FreeCAD AI: Safe UI setup...\n")
            
            # Clear the minimal layout and recreate properly
            if self.main_widget:
                # Remove old layout
                old_layout = self.main_widget.layout()
                if old_layout:
                    QtWidgets.QApplication.processEvents()  # Process any pending events
                    old_layout.deleteLater()

            # Create new layout
            layout = QtWidgets.QVBoxLayout(self.main_widget)
            layout.setSpacing(2)
            layout.setContentsMargins(2, 2, 2, 2)

            # Compact header with inline status
            header_layout = QtWidgets.QHBoxLayout()
            header_label = QtWidgets.QLabel("🤖 FreeCAD AI")
            header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
            header_layout.addWidget(header_label)

            header_layout.addStretch()

            # Recreate status label with proper styling
            self.status_label = QtWidgets.QLabel("Setting up...")
            self.status_label.setStyleSheet(
                "padding: 2px 8px; background-color: #f0f0f0; border-radius: 10px; font-size: 11px;"
            )
            header_layout.addWidget(self.status_label)

            layout.addLayout(header_layout)

            # Create tab widget
            self.tab_widget = QtWidgets.QTabWidget()
            if hasattr(self.tab_widget, 'setUsesScrollButtons'):
                self.tab_widget.setUsesScrollButtons(True)
            if hasattr(self.tab_widget, 'setElideMode') and hasattr(QtCore.Qt, 'ElideRight'):
                self.tab_widget.setElideMode(QtCore.Qt.ElideRight)
            
            layout.addWidget(self.tab_widget)
            
            # Create tabs safely
            self._create_tabs_safe()

            FreeCAD.Console.PrintMessage("FreeCAD AI: UI safely setup complete\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Safe UI setup failed: {e}\n")
            # Create fallback UI
            self._create_fallback_ui()

    def _create_tabs_safe(self):
        """Safely create the tab interface with comprehensive error handling."""
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Safe tab creation...\n")
            
            # Try to import tab widgets one by one
            tab_widgets = {}
            
            # Import each widget safely
            widget_imports = [
                ('conversation_widget', 'ConversationWidget', 'Chat'),
                ('providers_widget', 'ProvidersWidget', 'Providers'),
                ('agent_control_widget', 'AgentControlWidget', 'Agent'),
                ('tools_widget_compact', 'ToolsWidget', 'Tools'),
                ('unified_connection_widget', 'UnifiedConnectionWidget', 'Connections'),
                ('settings_widget', 'SettingsWidget', 'Settings'),
            ]
            
            for module_name, class_name, tab_name in widget_imports:
                try:
                    module = __import__(f'gui.{module_name}', fromlist=[class_name])
                    widget_class = getattr(module, class_name)
                    widget_instance = widget_class()
                    tab_widgets[tab_name] = widget_instance
                    
                    # Store widget references
                    setattr(self, module_name.replace('_widget', '').replace('_compact', '') + '_widget', widget_instance)
                    
                    FreeCAD.Console.PrintMessage(f"FreeCAD AI: Successfully created {tab_name} widget\n")
                    
                except Exception as e:
                    FreeCAD.Console.PrintWarning(f"FreeCAD AI: Failed to create {tab_name} widget: {e}\n")
                    # Create placeholder widget
                    placeholder = QtWidgets.QWidget()
                    placeholder_layout = QtWidgets.QVBoxLayout(placeholder)
                    placeholder_layout.addWidget(QtWidgets.QLabel(f"{tab_name} - Loading failed\n{str(e)[:100]}..."))
                    tab_widgets[tab_name] = placeholder

            # Add tabs to tab widget
            tab_order = ['Providers', 'Chat', 'Agent', 'Tools', 'Connections', 'Settings']
            for tab_name in tab_order:
                if tab_name in tab_widgets:
                    self.tab_widget.addTab(tab_widgets[tab_name], tab_name)

            FreeCAD.Console.PrintMessage("FreeCAD AI: Tab creation complete\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Safe tab creation failed: {e}\n")
            # Create minimal tabs
            for name in ['Chat', 'Settings']:
                tab = QtWidgets.QWidget()
                tab_layout = QtWidgets.QVBoxLayout(tab)
                tab_layout.addWidget(QtWidgets.QLabel(f"{name} - Error loading"))
                self.tab_widget.addTab(tab, name)

    def _setup_provider_service_safe(self):
        """Safely setup the provider integration service without immediate signal connections."""
        try:
            if self.provider_service is not None:
                FreeCAD.Console.PrintMessage("FreeCAD AI: Provider service already initialized\n")
                return
                
            FreeCAD.Console.PrintMessage("FreeCAD AI: Safe provider service setup...\n")

            # Try multiple import strategies
            provider_service_imported = False

            # Strategy 1: Relative import
            try:
                from ..ai.provider_integration_service import get_provider_service
                provider_service_imported = True
                FreeCAD.Console.PrintMessage("FreeCAD AI: Provider service imported via relative path\n")
            except ImportError as e:
                FreeCAD.Console.PrintMessage(f"FreeCAD AI: Relative import failed: {e}\n")

            # Strategy 2: Direct import
            if not provider_service_imported:
                try:
                    from ai.provider_integration_service import get_provider_service
                    provider_service_imported = True
                    FreeCAD.Console.PrintMessage("FreeCAD AI: Provider service imported via direct path\n")
                except ImportError as e:
                    FreeCAD.Console.PrintMessage(f"FreeCAD AI: Direct import failed: {e}\n")

            # Strategy 3: Add parent to path and import
            if not provider_service_imported:
                try:
                    import os
                    import sys
                    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if parent_dir not in sys.path:
                        sys.path.insert(0, parent_dir)
                    from ai.provider_integration_service import get_provider_service
                    provider_service_imported = True
                    FreeCAD.Console.PrintMessage("FreeCAD AI: Provider service imported after adding to sys.path\n")
                except ImportError as e:
                    FreeCAD.Console.PrintMessage(f"FreeCAD AI: Import with sys.path modification failed: {e}\n")

            if not provider_service_imported:
                FreeCAD.Console.PrintWarning("FreeCAD AI: Could not import provider service - proceeding without it\n")
                self.provider_service = None
                return

            # Create provider service but don't initialize or connect signals yet
            self.provider_service = get_provider_service()
            FreeCAD.Console.PrintMessage(f"FreeCAD AI: Provider service created: {self.provider_service is not None}\n")

            if self.provider_service:
                FreeCAD.Console.PrintMessage("FreeCAD AI: Provider service created successfully - signals will be connected later\n")
            else:
                FreeCAD.Console.PrintWarning("FreeCAD AI: Provider service is None\n")

        except Exception as e:
            FreeCAD.Console.PrintWarning(f"FreeCAD AI: Safe provider service setup failed: {e}\n")
            self.provider_service = None

    def _create_fallback_ui(self):
        """Create a minimal fallback UI if normal UI creation fails."""
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Creating fallback UI...\n")
            
            # Clear existing layout
            if self.main_widget:
                old_layout = self.main_widget.layout()
                if old_layout:
                    old_layout.deleteLater()

            # Create simple layout
            layout = QtWidgets.QVBoxLayout(self.main_widget)
            
            # Error message
            error_label = QtWidgets.QLabel("FreeCAD AI - Limited Mode\n\nSome components failed to load.\nBasic functionality may be available.")
            error_label.setStyleSheet("padding: 10px; background-color: #fff3e0; border-radius: 5px;")
            layout.addWidget(error_label)
            
            # Update status
            if hasattr(self, 'status_label') and self.status_label:
                self.status_label.setText("Limited Mode")
                self.status_label.setStyleSheet(
                    "padding: 2px 8px; background-color: #fff3e0; color: #ef6c00; border-radius: 10px; font-size: 11px;"
                )

            FreeCAD.Console.PrintMessage("FreeCAD AI: Fallback UI created\n")
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Even fallback UI creation failed: {e}\n")
        """Setup the user interface."""
        layout = QtWidgets.QVBoxLayout(self.main_widget)
        layout.setSpacing(2)  # Reduced spacing
        layout.setContentsMargins(2, 2, 2, 2)  # Reduced margins

        # Compact header with inline status
        header_layout = QtWidgets.QHBoxLayout()
        header_label = QtWidgets.QLabel("🤖 FreeCAD AI")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet(
            "padding: 2px 8px; background-color: #f0f0f0; border-radius: 10px; font-size: 11px;"
        )
        header_layout.addWidget(self.status_label)

        layout.addLayout(header_layout)

        self.tab_widget = QtWidgets.QTabWidget()
        # Make tabs flexible
        self.tab_widget.setUsesScrollButtons(True)
        self.tab_widget.setElideMode(QtCore.Qt.ElideRight)
        layout.addWidget(self.tab_widget)
        self._create_tabs()

    def _setup_provider_service(self):
        """Setup the provider integration service."""
        try:
            print("FreeCAD AI: Setting up provider service...")

            # Try multiple import strategies
            provider_service_imported = False

            # Strategy 1: Relative import
            try:
                from ..ai.provider_integration_service import get_provider_service

                provider_service_imported = True
                print("FreeCAD AI: Provider service imported via relative path")
            except ImportError as e:
                print(f"FreeCAD AI: Relative import failed: {e}")

            # Strategy 2: Direct import if addon is in sys.path
            if not provider_service_imported:
                try:
                    from ai.provider_integration_service import get_provider_service

                    provider_service_imported = True
                    print("FreeCAD AI: Provider service imported via direct path")
                except ImportError as e:
                    print(f"FreeCAD AI: Direct import failed: {e}")

            # Strategy 3: Add parent to path and import
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
                    print(
                        "FreeCAD AI: Provider service imported after adding to sys.path"
                    )
                except ImportError as e:
                    print(f"FreeCAD AI: Import with sys.path modification failed: {e}")

            if not provider_service_imported:
                raise ImportError(
                    "Could not import provider_integration_service after all strategies"
                )

            self.provider_service = get_provider_service()
            print(
                f"FreeCAD AI: Provider service created: {self.provider_service is not None}"
            )

            if self.provider_service:
                # Don't connect signals here - they will be connected later
                # when the UI is fully ready to avoid crashes during workbench activation
                print("FreeCAD AI: Provider service created successfully")
                print("FreeCAD AI: Deferring signal connections until UI is ready")
            else:
                print("FreeCAD AI: Warning - provider service is None")

        except ImportError as e:
            if hasattr(self, "status_label"):
                self.status_label.setText(f"Warning: {e}")
            print(f"FreeCAD AI: Provider service unavailable - {e}")
        except Exception as e:
            print(f"FreeCAD AI: Error setting up provider service - {e}")
            import traceback

            print(f"FreeCAD AI: Traceback: {traceback.format_exc()}")

    def _initialize_providers_after_ui(self):
        """Initialize providers after UI is fully ready to avoid callback crashes."""
        try:
            print("FreeCAD AI: Initializing providers after UI setup...")
            
            if not self.provider_service:
                print("FreeCAD AI: No provider service available for initialization")
                return
                
            # Connect provider service signals to update status - NOW SAFE
            if hasattr(self.provider_service, 'provider_status_changed'):
                self.provider_service.provider_status_changed.connect(
                    self._on_provider_status_changed
                )
                print("FreeCAD AI: Provider status changed signal connected")
                
            if hasattr(self.provider_service, 'providers_updated'):
                self.provider_service.providers_updated.connect(
                    self._on_providers_updated
                )
                print("FreeCAD AI: Providers updated signal connected")

            # Enable signal emission if needed
            if hasattr(self.provider_service, "enable_signals"):
                self.provider_service.enable_signals()
                print("FreeCAD AI: Provider service signals enabled")

            # Now initialize providers - signals are connected and UI exists
            if hasattr(self.provider_service, "initialize_providers_from_config"):
                print("FreeCAD AI: Initializing providers from config...")
                self.provider_service.initialize_providers_from_config()
                print("FreeCAD AI: Provider initialization complete")
            else:
                print("FreeCAD AI: Provider service has no initialize_providers_from_config method")
                
        except Exception as e:
            print(f"FreeCAD AI: Error initializing providers after UI: {e}")
            import traceback
            print(f"FreeCAD AI: Traceback: {traceback.format_exc()}")
            # Update status label to show error if it exists
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"Init Error: {str(e)[:20]}...")
                self.status_label.setStyleSheet(
                    "padding: 2px 8px; background-color: #ffcdd2; color: #c62828; border-radius: 10px; font-size: 11px;"
                )

    def _on_provider_status_changed(
        self, provider_name: str, status: str, message: str
    ):
        """Handle provider status changes."""
        # Robust check - ensure status_label exists and widget is not being destroyed
        if not hasattr(self, "status_label") or self.status_label is None:
            print(f"FreeCAD AI: Status change ignored - no status_label: {provider_name} -> {status}")
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
            print(f"FreeCAD AI: Error updating status label: {e}")

    def _on_providers_updated(self):
        """Handle providers list update."""
        # Robust check - ensure status_label exists and widget is not being destroyed
        if not hasattr(self, "status_label") or self.status_label is None:
            print("FreeCAD AI: Providers update ignored - no status_label")
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
            print(f"FreeCAD AI: Error updating providers status: {e}")

    def _retry_provider_initialization(self):
        """Retry provider initialization if no providers are active."""
        if self.provider_service:
            active_count = len(self.provider_service.get_active_providers())
            if active_count == 0:
                print("Retrying provider initialization...")
                self.provider_service.initialize_providers_from_config()

    def get_provider_service(self):
        """Get the provider service instance."""
        return self.provider_service

    def _create_tabs(self):
        """Create the tab interface."""
        try:
            from .agent_control_widget import AgentControlWidget
            from .conversation_widget import ConversationWidget
            from .providers_widget import ProvidersWidget
            from .settings_widget import SettingsWidget
            from .tools_widget_compact import ToolsWidget  # Use compact version
            from .unified_connection_widget import UnifiedConnectionWidget

            # Create widgets
            self.unified_connection_widget = UnifiedConnectionWidget()
            self.providers_widget = ProvidersWidget()
            self.conversation_widget = ConversationWidget()
            self.settings_widget = SettingsWidget()
            self.tools_widget = ToolsWidget()  # Use compact tools widget
            self.agent_control_widget = AgentControlWidget()

            # Add tabs in logical order (merged Server/Connection)
            self.tab_widget.addTab(self.providers_widget, "Providers")
            self.tab_widget.addTab(self.conversation_widget, "Chat")
            self.tab_widget.addTab(self.agent_control_widget, "Agent")
            self.tab_widget.addTab(self.tools_widget, "Tools")
            self.tab_widget.addTab(self.unified_connection_widget, "Connections")
            self.tab_widget.addTab(self.settings_widget, "Settings")

        except ImportError:
            for name in [
                "Providers",
                "Chat",
                "Tools",
                "Connections",
                "Settings",
            ]:
                tab = QtWidgets.QWidget()
                tab_layout = QtWidgets.QVBoxLayout(tab)
                tab_layout.addWidget(QtWidgets.QLabel(f"{name} - Loading..."))
                self.tab_widget.addTab(tab, name)

    def _connect_widgets_to_service_safe(self):
        """Safely connect widgets to services with error handling."""
        try:
            self._connect_widgets_to_service()
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"FreeCAD AI: Widget connection failed: {e}\n")

    def _connect_widgets_to_service(self):
        """Connect GUI widgets to the provider service."""
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Connecting widgets to services...\n")
            
            # Connect chat functionality
            if hasattr(self, 'send_button') and hasattr(self, 'chat_input'):
                self.send_button.clicked.connect(self._send_chat_message)
                # Connect Ctrl+Enter shortcut for chat input
                if hasattr(QtWidgets, 'QShortcut'):
                    try:
                        from PySide2.QtGui import QKeySequence
                        shortcut = QtWidgets.QShortcut(QKeySequence("Ctrl+Return"), self.chat_input)
                        shortcut.activated.connect(self._send_chat_message)
                    except:
                        pass  # Fallback if shortcut creation fails

            # Connect agent functionality  
            if hasattr(self, 'execute_button') and hasattr(self, 'stop_button'):
                self.execute_button.clicked.connect(self._execute_agent_task)
                self.stop_button.clicked.connect(self._stop_agent_task)

            # Connect mode switching
            if hasattr(self, 'mode_combo'):
                self.mode_combo.currentTextChanged.connect(self._on_mode_changed)

            # Connect provider settings
            if hasattr(self, 'provider_combo'):
                self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
            
            if hasattr(self, 'model_combo'):
                self.model_combo.currentTextChanged.connect(self._on_model_changed)

            if hasattr(self, 'test_connection_button'):
                self.test_connection_button.clicked.connect(self._test_provider_connection)

            if hasattr(self, 'save_settings_button'):
                self.save_settings_button.clicked.connect(self._save_provider_settings)

            # Load saved settings
            self._load_saved_settings()
            
            FreeCAD.Console.PrintMessage("FreeCAD AI: Widget connections completed\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Widget connection failed: {e}\n")

    def _send_chat_message(self):
        """Send a chat message to the AI."""
        try:
            if not hasattr(self, 'chat_input') or not hasattr(self, 'chat_history'):
                return
                
            message = self.chat_input.toPlainText().strip()
            if not message:
                return

            # Add user message to chat history
            self.chat_history.append(f"<b>You:</b> {message}")
            
            # Clear input
            self.chat_input.clear()
            
            # Disable send button while processing
            if hasattr(self, 'send_button'):
                self.send_button.setEnabled(False)
                self.send_button.setText("Sending...")

            # Update status
            self._update_status("Processing message...")

            # Simulate AI response (replace with actual AI call)
            self._simulate_ai_response(message)

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Chat message failed: {e}\n")
            self._update_status("Error sending message")

    def _simulate_ai_response(self, user_message):
        """Simulate AI response (replace with actual AI integration)."""
        try:
            # This is a placeholder - replace with actual AI provider integration
            import time
            
            # Simulate processing delay
            QtCore.QTimer.singleShot(2000, lambda: self._add_ai_response(
                f"I received your message: '{user_message}'. AI integration is being set up."
            ))

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: AI response simulation failed: {e}\n")

    def _add_ai_response(self, response):
        """Add AI response to chat history."""
        try:
            if hasattr(self, 'chat_history'):
                self.chat_history.append(f"<b>AI:</b> {response}")
                
            # Re-enable send button
            if hasattr(self, 'send_button'):
                self.send_button.setEnabled(True)
                self.send_button.setText("Send")

            self._update_status("Ready")

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Adding AI response failed: {e}\n")

    def _execute_agent_task(self):
        """Execute an agent task."""
        try:
            if not hasattr(self, 'task_input') or not hasattr(self, 'agent_results'):
                return
                
            task = self.task_input.toPlainText().strip()
            if not task:
                return

            # Update UI state
            if hasattr(self, 'execute_button'):
                self.execute_button.setEnabled(False)
            if hasattr(self, 'stop_button'):
                self.stop_button.setEnabled(True)

            # Add task to results
            self.agent_results.append(f"<b>Task:</b> {task}")
            self.agent_results.append("<b>Status:</b> Executing...")

            self._update_status("Executing agent task...")

            # Simulate task execution (replace with actual agent integration)
            QtCore.QTimer.singleShot(3000, lambda: self._complete_agent_task(task))

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Agent task execution failed: {e}\n")

    def _complete_agent_task(self, task):
        """Complete an agent task."""
        try:
            if hasattr(self, 'agent_results'):
                self.agent_results.append(f"<b>Result:</b> Task '{task}' completed successfully (simulated)")
                
            # Reset UI state
            if hasattr(self, 'execute_button'):
                self.execute_button.setEnabled(True)
            if hasattr(self, 'stop_button'):
                self.stop_button.setEnabled(False)

            self._update_status("Agent task completed")

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Agent task completion failed: {e}\n")

    def _stop_agent_task(self):
        """Stop the current agent task."""
        try:
            if hasattr(self, 'agent_results'):
                self.agent_results.append("<b>Status:</b> Task stopped by user")
                
            # Reset UI state
            if hasattr(self, 'execute_button'):
                self.execute_button.setEnabled(True)
            if hasattr(self, 'stop_button'):
                self.stop_button.setEnabled(False)

            self._update_status("Task stopped")

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Stop agent task failed: {e}\n")

    def _on_mode_changed(self, mode_text):
        """Handle mode change between Chat and Agent."""
        try:
            FreeCAD.Console.PrintMessage(f"FreeCAD AI: Mode changed to {mode_text}\n")
            # Switch to appropriate tab
            if hasattr(self, 'tab_widget'):
                if "Chat" in mode_text:
                    self.tab_widget.setCurrentIndex(0)  # Chat tab
                elif "Agent" in mode_text:
                    self.tab_widget.setCurrentIndex(1)  # Agent tab

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Mode change failed: {e}\n")

    def _on_provider_changed(self, provider):
        """Handle provider selection change."""
        try:
            FreeCAD.Console.PrintMessage(f"FreeCAD AI: Provider changed to {provider}\n")
            
            # Update model options based on provider
            if hasattr(self, 'model_combo'):
                self.model_combo.clear()
                
                if provider == "OpenAI":
                    self.model_combo.addItems(["gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"])
                elif provider == "Anthropic":
                    self.model_combo.addItems(["claude-3-opus", "claude-3-sonnet", "claude-3-haiku"])
                elif provider == "Google Gemini":
                    self.model_combo.addItems(["gemini-pro", "gemini-pro-vision"])
                elif provider == "Local Ollama":
                    self.model_combo.addItems(["llama2", "codellama", "mistral"])
                else:
                    self.model_combo.addItems(["Default Model"])

            self._update_provider_status()

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Provider change failed: {e}\n")

    def _on_model_changed(self, model):
        """Handle model selection change."""
        try:
            FreeCAD.Console.PrintMessage(f"FreeCAD AI: Model changed to {model}\n")
            self._update_provider_status()

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Model change failed: {e}\n")

    def _test_provider_connection(self):
        """Test connection to the selected AI provider."""
        try:
            if hasattr(self, 'test_connection_button'):
                self.test_connection_button.setText("Testing...")
                self.test_connection_button.setEnabled(False)

            self._update_status("Testing provider connection...")

            # Simulate connection test (replace with actual provider test)
            QtCore.QTimer.singleShot(2000, self._connection_test_complete)

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Connection test failed: {e}\n")

    def _connection_test_complete(self):
        """Complete the connection test."""
        try:
            if hasattr(self, 'test_connection_button'):
                self.test_connection_button.setText("Test Connection")
                self.test_connection_button.setEnabled(True)

            # Simulate successful connection (replace with actual test result)
            self._update_status("Connection test passed")
            self._update_provider_status()

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Connection test completion failed: {e}\n")

    def _save_provider_settings(self):
        """Save provider settings."""
        try:
            settings = QtCore.QSettings("FreeCAD", "AI_Provider")
            
            if hasattr(self, 'provider_combo'):
                settings.setValue("provider", self.provider_combo.currentText())
            if hasattr(self, 'model_combo'):
                settings.setValue("model", self.model_combo.currentText())
            if hasattr(self, 'api_key_input'):
                # Note: In production, use secure storage for API keys
                settings.setValue("api_key", self.api_key_input.text())
            if hasattr(self, 'auto_save_checkbox'):
                settings.setValue("auto_save", self.auto_save_checkbox.isChecked())
            if hasattr(self, 'debug_logging_checkbox'):
                settings.setValue("debug_logging", self.debug_logging_checkbox.isChecked())

            settings.sync()
            self._update_status("Settings saved")
            FreeCAD.Console.PrintMessage("FreeCAD AI: Settings saved successfully\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Save settings failed: {e}\n")

    def _load_saved_settings(self):
        """Load saved provider settings."""
        try:
            settings = QtCore.QSettings("FreeCAD", "AI_Provider")
            
            # Load provider
            if hasattr(self, 'provider_combo'):
                saved_provider = settings.value("provider", "OpenAI")
                index = self.provider_combo.findText(saved_provider)
                if index >= 0:
                    self.provider_combo.setCurrentIndex(index)

            # Load model
            if hasattr(self, 'model_combo'):
                saved_model = settings.value("model", "gpt-4")
                index = self.model_combo.findText(saved_model)
                if index >= 0:
                    self.model_combo.setCurrentIndex(index)

            # Load API key
            if hasattr(self, 'api_key_input'):
                saved_key = settings.value("api_key", "")
                self.api_key_input.setText(saved_key)

            # Load checkboxes
            if hasattr(self, 'auto_save_checkbox'):
                auto_save = settings.value("auto_save", True, type=bool)
                self.auto_save_checkbox.setChecked(auto_save)

            if hasattr(self, 'debug_logging_checkbox'):
                debug_logging = settings.value("debug_logging", False, type=bool)
                self.debug_logging_checkbox.setChecked(debug_logging)

            self._update_provider_status()

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Load settings failed: {e}\n")

    def _update_provider_status(self):
        """Update the provider status display."""
        try:
            if not hasattr(self, 'provider_status'):
                return

            provider = getattr(self, 'provider_combo', None)
            model = getattr(self, 'model_combo', None)
            api_key = getattr(self, 'api_key_input', None)

            if provider and model:
                provider_text = provider.currentText()
                model_text = model.currentText()
                
                if api_key and api_key.text().strip():
                    status_text = f"{provider_text} ({model_text})"
                    self.provider_status.setText(status_text)
                    self.provider_status.setStyleSheet("""
                        QLabel {
                            padding: 3px 8px;
                            background-color: #c8e6c9;
                            color: #2e7d32;
                            border-radius: 10px;
                            font-size: 10px;
                        }
                    """)
                else:
                    self.provider_status.setText("API key required")
                    self.provider_status.setStyleSheet("""
                        QLabel {
                            padding: 3px 8px;
                            background-color: #ffeb3b;
                            color: #f57f17;
                            border-radius: 10px;
                            font-size: 10px;
                        }
                    """)

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Update provider status failed: {e}\n")
            print(f"FreeCAD AI: Failed to get provider service on retry: {e}")

            # Connect providers widget to manage providers and API keys
            if hasattr(self.providers_widget, "set_provider_service"):
                self.providers_widget.set_provider_service(self.provider_service)
                print("FreeCAD AI: Provider service connected to providers widget")
            else:
                print(
                    "FreeCAD AI: Warning - providers widget has no set_provider_service method"
                )

            # Connect providers widget API key changes to service
            if hasattr(self.providers_widget, "api_key_changed"):
                self.providers_widget.api_key_changed.connect(
                    self._on_settings_api_key_changed
                )

            # Connect provider configuration changes to update conversation widget
            if hasattr(self.providers_widget, "provider_configured"):
                self.providers_widget.provider_configured.connect(
                    self._on_provider_configured
                )
                print("FreeCAD AI: Provider configured signal connected")

            # Connect conversation widget to get provider updates
            if hasattr(self.conversation_widget, "set_provider_service"):
                self.conversation_widget.set_provider_service(self.provider_service)
                print("FreeCAD AI: Provider service connected to conversation widget")

                # Force refresh the conversation widget's provider list
                if hasattr(self.conversation_widget, "refresh_providers"):
                    self.conversation_widget.refresh_providers()
                    print("FreeCAD AI: Conversation widget providers refreshed")
            else:
                print(
                    "FreeCAD AI: Warning - conversation widget has no set_provider_service method"
                )

            # Connect conversation widget to agent manager
            if self.agent_manager and hasattr(
                self.conversation_widget, "set_agent_manager"
            ):
                self.conversation_widget.set_agent_manager(self.agent_manager)
                print("FreeCAD AI: Agent manager connected to conversation widget")
            elif not self.agent_manager:
                print(
                    "FreeCAD AI: Agent manager is None - cannot connect to conversation widget"
                )

            # Connect agent control widget to agent manager
            if self.agent_manager and hasattr(
                self.agent_control_widget, "set_agent_manager"
            ):
                self.agent_control_widget.set_agent_manager(self.agent_manager)
                print("FreeCAD AI: Agent manager connected to agent control widget")
            elif not self.agent_manager:
                print(
                    "FreeCAD AI: Agent manager is None - cannot connect to agent control widget"
                )

            # Connect connection widget to show MCP connection status (no AI provider status)
            if hasattr(self.unified_connection_widget, "set_provider_service"):
                self.unified_connection_widget.set_provider_service(
                    self.provider_service
                )

            # Perform final connection check directly
            try:
                self._final_connection_check()
            except Exception as e:
                print(f"FreeCAD AI: Error in final connection check: {e}")

        except Exception as e:
            if hasattr(self, "status_label"):
                self.status_label.setText(f"⚠️ {e}")
            import traceback

            print(f"FreeCAD AI: Error connecting widgets: {e}")
            print(f"FreeCAD AI: Traceback: {traceback.format_exc()}")

    def _final_connection_check(self):
        """Final check to ensure all connections are working."""
        try:
            print("FreeCAD AI: Performing final connection check...")

            # Provider initialization is now handled in _initialize_providers_after_ui()
            # This method just does final UI updates

            # Refresh conversation widget if available
            if hasattr(self.conversation_widget, "refresh_providers"):
                self.conversation_widget.refresh_providers()
                print("FreeCAD AI: Final refresh of conversation widget providers")

        except Exception as e:
            print(f"FreeCAD AI: Error in final connection check: {e}")

    def _on_settings_api_key_changed(self, provider_name: str):
        """Handle API key changes from settings widget."""
        if self.provider_service:
            self.provider_service.update_provider_from_settings(provider_name)

    def _on_provider_configured(self, provider_name: str):
        """Handle provider configuration changes."""
        # Refresh conversation widget when provider is configured
        if hasattr(self.conversation_widget, "refresh_providers"):
            self.conversation_widget.refresh_providers()
            print(
                f"FreeCAD AI: Refreshed conversation widget after {provider_name} configured"
            )

        # Update provider service
        if self.provider_service:
            self.provider_service.update_provider_from_settings(provider_name)

    def _init_agent_manager(self):
        """Initialize the agent manager."""
        try:
            # Try multiple import strategies for agent manager
            agent_manager_imported = False

            # Strategy 1: Relative import
            try:
                from ..core.agent_manager import AgentManager

                agent_manager_imported = True
                print("FreeCAD AI: AgentManager imported via relative path")
            except ImportError as e:
                print(f"FreeCAD AI: Relative import failed: {e}")

            # Strategy 2: Direct import
            if not agent_manager_imported:
                try:
                    from core.agent_manager import AgentManager

                    agent_manager_imported = True
                    print("FreeCAD AI: AgentManager imported via direct path")
                except ImportError as e:
                    print(f"FreeCAD AI: Direct import failed: {e}")

            # Strategy 3: Add parent to path
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
                    print("FreeCAD AI: AgentManager imported after adding to sys.path")
                except ImportError as e:
                    print(f"FreeCAD AI: Import with sys.path modification failed: {e}")

            if not agent_manager_imported:
                print(
                    "FreeCAD AI: ERROR - Could not import AgentManager after all strategies"
                )
                self.agent_manager = None
                return

            self.agent_manager = AgentManager()
            print("FreeCAD AI: AgentManager instance created successfully")

            # Register callbacks
            self.agent_manager.register_callback(
                "on_mode_change", self._on_agent_mode_changed
            )
            self.agent_manager.register_callback(
                "on_state_change", self._on_agent_state_changed
            )

            print("FreeCAD AI: Agent Manager initialized and callbacks registered")

        except Exception as e:
            print(f"FreeCAD AI: Agent Manager initialization failed - {e}")
            import traceback

            print(f"FreeCAD AI: Full traceback: {traceback.format_exc()}")
            self.agent_manager = None

    def _on_agent_mode_changed(self, old_mode, new_mode):
        """Handle agent mode change callback."""
        # Robust check - ensure status_label exists and widget is not being destroyed
        if not hasattr(self, "status_label") or self.status_label is None:
            print(f"FreeCAD AI: Agent mode change ignored - no status_label: {old_mode} -> {new_mode}")
            return

        try:
            mode_display = "Chat" if new_mode.value == "chat" else "Agent"
            self.status_label.setText(f"Mode: {mode_display}")
        except Exception as e:
            print(f"FreeCAD AI: Error updating agent mode status: {e}")

    def _on_agent_state_changed(self, old_state, new_state):
        """Handle agent state change callback."""
        # Robust check - ensure status_label exists and widget is not being destroyed
        if not hasattr(self, "status_label") or self.status_label is None:
            print(f"FreeCAD AI: Agent state change ignored - no status_label: {old_state} -> {new_state}")
            return

        try:
            # Update status based on execution state
            state_display = {
                "idle": "Ready",
                "planning": "Planning...",
                "executing": "Executing...",
                "paused": "Paused",
                "error": "Error",
                "completed": "Completed",
            }
            status_text = state_display.get(new_state.value, new_state.value)

            # Show mode and state
            mode_text = (
                "Chat" if self.agent_manager.current_mode.value == "chat" else "Agent"
            )
            self.status_label.setText(f"{mode_text}: {status_text}")

            # Update status color
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
            print(f"FreeCAD AI: Error updating agent state status: {e}")

    def _update_ui_for_chat_mode(self):
        """Update UI elements for chat mode."""
        # In chat mode, disable autonomous execution features
        if hasattr(self, "tools_widget"):
            self.tools_widget.setEnabled(True)  # Manual tool use allowed

        # Update tab visibility or highlighting
        chat_tab_index = self._find_tab_index("Chat")
        if chat_tab_index >= 0:
            self.tab_widget.setTabText(chat_tab_index, "💬 Chat (Active)")

        agent_tab_index = self._find_tab_index("Agent")
        if agent_tab_index >= 0:
            self.tab_widget.setTabText(agent_tab_index, "🤖 Agent")

    def _update_ui_for_agent_mode(self):
        """Update UI elements for agent mode."""
        # In agent mode, enable autonomous execution features
        if hasattr(self, "tools_widget"):
            self.tools_widget.setEnabled(True)  # Tools can be executed by agent

        # Update tab visibility or highlighting
        chat_tab_index = self._find_tab_index("Chat")
        if chat_tab_index >= 0:
            self.tab_widget.setTabText(chat_tab_index, "💬 Chat")

        agent_tab_index = self._find_tab_index("Agent")
        if agent_tab_index >= 0:
            self.tab_widget.setTabText(agent_tab_index, "🤖 Agent (Active)")

    def _find_tab_index(self, tab_name):
        """Find tab index by name."""
        for i in range(self.tab_widget.count()):
            if tab_name in self.tab_widget.tabText(i):
                return i
        return -1

    def get_agent_manager(self):
        """Get the agent manager instance."""
        return self.agent_manager

    def get_agent_manager_status(self):
        """Get the status of the agent manager for debugging."""
        if self.agent_manager is None:
            return {
                "connected": False,
                "error": "Agent manager is None - initialization failed",
                "suggestion": "Check FreeCAD console for initialization errors",
            }

        try:
            status = self.agent_manager.get_status()
            return {
                "connected": True,
                "status": status,
                "mode": status.get("mode", "unknown"),
                "state": status.get("state", "unknown"),
                "available_tools": len(status.get("available_tools", {})),
            }
        except Exception as e:
            return {
                "connected": False,
                "error": f"Agent manager exists but is not functional: {e}",
                "suggestion": "Agent manager may be partially initialized",
            }

    def _load_persisted_mode(self):
        """Load persisted mode from settings."""
        try:
            settings = QtCore.QSettings("FreeCAD", "AI_Agent")
            mode = settings.value("agent_mode", "Chat")

            # Set the agent manager mode directly
            if self.agent_manager:
                from ..core.agent_manager import AgentMode

                if mode == "Agent":
                    self.agent_manager.set_mode(AgentMode.AGENT)
                else:
                    self.agent_manager.set_mode(AgentMode.CHAT)

        except Exception as e:
            print(f"FreeCAD AI: Error loading persisted mode - {e}")

    def _save_mode(self, mode_text: str):
        """Save mode to settings."""
        try:
            settings = QtCore.QSettings("FreeCAD", "AI_Agent")
            # Extract mode name (Chat or Agent)
            mode = "Chat" if "Chat" in mode_text else "Agent"
            settings.setValue("agent_mode", mode)
            settings.sync()
        except Exception as e:
            print(f"FreeCAD AI: Error saving mode - {e}")

    def _create_tabs_nuclear_safe(self):
        """Create full featured tabs safely after nuclear minimal initialization."""
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Creating full feature tabs...\n")
            
            # Create Chat tab with full functionality
            self._create_chat_tab()
            
            # Create Agent tab with full functionality  
            self._create_agent_tab()
            
            # Create Settings tab with provider configuration
            self._create_settings_tab()
            
            # Create About tab
            self._create_about_tab()
            
            FreeCAD.Console.PrintMessage("FreeCAD AI: All tabs created successfully\n")
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Tab creation failed: {e}\n")
            # Create minimal fallback tabs
            self._create_fallback_tabs()

    def _create_chat_tab(self):
        """Create the chat tab with full functionality."""
        try:
            chat_tab = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(chat_tab)
            layout.setSpacing(5)
            layout.setContentsMargins(5, 5, 5, 5)

            # Header with mode selection
            header_layout = QtWidgets.QHBoxLayout()
            mode_label = QtWidgets.QLabel("Mode:")
            mode_label.setStyleSheet("font-weight: bold;")
            header_layout.addWidget(mode_label)

            self.mode_combo = QtWidgets.QComboBox()
            self.mode_combo.addItems(["💬 Chat Mode", "🤖 Agent Mode"])
            self.mode_combo.setStyleSheet("""
                QComboBox {
                    padding: 5px 10px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: white;
                }
            """)
            header_layout.addWidget(self.mode_combo)
            header_layout.addStretch()

            # Provider status
            self.provider_status = QtWidgets.QLabel("No provider configured")
            self.provider_status.setStyleSheet("""
                QLabel {
                    padding: 3px 8px;
                    background-color: #ffeb3b;
                    color: #f57f17;
                    border-radius: 10px;
                    font-size: 10px;
                }
            """)
            header_layout.addWidget(self.provider_status)
            layout.addLayout(header_layout)

            # Chat history area
            self.chat_history = QtWidgets.QTextEdit()
            self.chat_history.setReadOnly(True)
            self.chat_history.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                    background-color: #fafafa;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 12px;
                }
            """)
            self.chat_history.setPlaceholderText("Chat conversation will appear here...")
            layout.addWidget(self.chat_history, 1)

            # Input area
            input_layout = QtWidgets.QHBoxLayout()
            self.chat_input = QtWidgets.QTextEdit()
            self.chat_input.setMaximumHeight(80)
            self.chat_input.setPlaceholderText("Type your message here... (Ctrl+Enter to send)")
            self.chat_input.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    padding: 8px;
                    font-size: 12px;
                }
            """)
            input_layout.addWidget(self.chat_input, 1)

            self.send_button = QtWidgets.QPushButton("Send")
            self.send_button.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
                QPushButton:disabled {
                    background-color: #ccc;
                }
            """)
            input_layout.addWidget(self.send_button)
            layout.addLayout(input_layout)

            self.tab_widget.addTab(chat_tab, "💬 Chat")
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Chat tab creation failed: {e}\n")

    def _create_agent_tab(self):
        """Create the agent tab with task functionality."""
        try:
            agent_tab = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(agent_tab)
            layout.setSpacing(5)
            layout.setContentsMargins(5, 5, 5, 5)

            # Agent header
            header_label = QtWidgets.QLabel("🤖 FreeCAD AI Agent")
            header_label.setStyleSheet("""
                QLabel {
                    font-size: 16px;
                    font-weight: bold;
                    color: #1976D2;
                    padding: 10px 0;
                }
            """)
            header_label.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(header_label)

            # Task input area
            task_label = QtWidgets.QLabel("Task Description:")
            task_label.setStyleSheet("font-weight: bold; margin-top: 10px;")
            layout.addWidget(task_label)

            self.task_input = QtWidgets.QTextEdit()
            self.task_input.setMaximumHeight(100)
            self.task_input.setPlaceholderText("Describe what you want the AI agent to do in FreeCAD...")
            self.task_input.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #ccc;
                    border-radius: 5px;
                    padding: 8px;
                    font-size: 12px;
                }
            """)
            layout.addWidget(self.task_input)

            # Control buttons
            button_layout = QtWidgets.QHBoxLayout()
            
            self.execute_button = QtWidgets.QPushButton("Execute Task")
            self.execute_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            button_layout.addWidget(self.execute_button)

            self.stop_button = QtWidgets.QPushButton("Stop")
            self.stop_button.setStyleSheet("""
                QPushButton {
                    background-color: #f44336;
                    color: white;
                    border: none;
                    padding: 10px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            self.stop_button.setEnabled(False)
            button_layout.addWidget(self.stop_button)
            
            button_layout.addStretch()
            layout.addLayout(button_layout)

            # Task history/results area
            results_label = QtWidgets.QLabel("Task Results:")
            results_label.setStyleSheet("font-weight: bold; margin-top: 20px;")
            layout.addWidget(results_label)

            self.agent_results = QtWidgets.QTextEdit()
            self.agent_results.setReadOnly(True)
            self.agent_results.setPlaceholderText("Agent execution results will appear here...")
            self.agent_results.setStyleSheet("""
                QTextEdit {
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 10px;
                    background-color: #fafafa;
                    font-family: 'Consolas', 'Monaco', monospace;
                    font-size: 11px;
                }
            """)
            layout.addWidget(self.agent_results, 1)

            self.tab_widget.addTab(agent_tab, "🤖 Agent")
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Agent tab creation failed: {e}\n")

    def _create_settings_tab(self):
        """Create the settings tab with provider configuration."""
        try:
            settings_tab = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(settings_tab)
            layout.setSpacing(10)
            layout.setContentsMargins(10, 10, 10, 10)

            # Provider Configuration Section
            provider_group = QtWidgets.QGroupBox("AI Provider Configuration")
            provider_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #ccc;
                    border-radius: 5px;
                    margin-top: 1ex;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
            """)
            provider_layout = QtWidgets.QVBoxLayout(provider_group)

            # Provider selection
            provider_select_layout = QtWidgets.QHBoxLayout()
            provider_label = QtWidgets.QLabel("Provider:")
            provider_select_layout.addWidget(provider_label)

            self.provider_combo = QtWidgets.QComboBox()
            self.provider_combo.addItems([
                "OpenAI", "Anthropic", "Local Ollama", "Google Gemini", "Azure OpenAI"
            ])
            self.provider_combo.setStyleSheet("""
                QComboBox {
                    padding: 5px 10px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: white;
                    min-width: 150px;
                }
            """)
            provider_select_layout.addWidget(self.provider_combo)
            provider_select_layout.addStretch()
            provider_layout.addLayout(provider_select_layout)

            # Model selection
            model_select_layout = QtWidgets.QHBoxLayout()
            model_label = QtWidgets.QLabel("Model:")
            model_select_layout.addWidget(model_label)

            self.model_combo = QtWidgets.QComboBox()
            self.model_combo.addItems([
                "gpt-4", "gpt-3.5-turbo", "claude-3-sonnet", "claude-3-haiku", "gemini-pro"
            ])
            self.model_combo.setStyleSheet("""
                QComboBox {
                    padding: 5px 10px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: white;
                    min-width: 150px;
                }
            """)
            model_select_layout.addWidget(self.model_combo)
            model_select_layout.addStretch()
            provider_layout.addLayout(model_select_layout)

            # API Key input
            api_key_layout = QtWidgets.QHBoxLayout()
            api_key_label = QtWidgets.QLabel("API Key:")
            api_key_layout.addWidget(api_key_label)

            self.api_key_input = QtWidgets.QLineEdit()
            self.api_key_input.setEchoMode(QtWidgets.QLineEdit.Password)
            self.api_key_input.setPlaceholderText("Enter your API key...")
            self.api_key_input.setStyleSheet("""
                QLineEdit {
                    padding: 5px 10px;
                    border: 1px solid #ccc;
                    border-radius: 3px;
                    background-color: white;
                }
            """)
            api_key_layout.addWidget(self.api_key_input)

            self.test_connection_button = QtWidgets.QPushButton("Test Connection")
            self.test_connection_button.setStyleSheet("""
                QPushButton {
                    background-color: #FF9800;
                    color: white;
                    border: none;
                    padding: 5px 15px;
                    border-radius: 3px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #F57C00;
                }
            """)
            api_key_layout.addWidget(self.test_connection_button)
            provider_layout.addLayout(api_key_layout)

            # Save settings button
            save_layout = QtWidgets.QHBoxLayout()
            save_layout.addStretch()
            self.save_settings_button = QtWidgets.QPushButton("Save Settings")
            self.save_settings_button.setStyleSheet("""
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    border: none;
                    padding: 8px 20px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """)
            save_layout.addWidget(self.save_settings_button)
            provider_layout.addLayout(save_layout)

            layout.addWidget(provider_group)

            # General Settings Section
            general_group = QtWidgets.QGroupBox("General Settings")
            general_group.setStyleSheet("""
                QGroupBox {
                    font-weight: bold;
                    border: 2px solid #ccc;
                    border-radius: 5px;
                    margin-top: 1ex;
                    padding-top: 10px;
                }
                QGroupBox::title {
                    subcontrol-origin: margin;
                    left: 10px;
                    padding: 0 5px 0 5px;
                }
            """)
            general_layout = QtWidgets.QVBoxLayout(general_group)

            # Auto-save chat history
            self.auto_save_checkbox = QtWidgets.QCheckBox("Auto-save chat history")
            self.auto_save_checkbox.setChecked(True)
            general_layout.addWidget(self.auto_save_checkbox)

            # Enable debug logging
            self.debug_logging_checkbox = QtWidgets.QCheckBox("Enable debug logging")
            general_layout.addWidget(self.debug_logging_checkbox)

            layout.addWidget(general_group)
            layout.addStretch()

            self.tab_widget.addTab(settings_tab, "⚙️ Settings")
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Settings tab creation failed: {e}\n")

    def _create_about_tab(self):
        """Create the about tab with information."""
        try:
            about_tab = QtWidgets.QWidget()
            layout = QtWidgets.QVBoxLayout(about_tab)
            layout.setSpacing(15)
            layout.setContentsMargins(20, 20, 20, 20)

            # Logo/Title
            title_label = QtWidgets.QLabel("🤖 FreeCAD AI Assistant")
            title_label.setStyleSheet("""
                QLabel {
                    font-size: 24px;
                    font-weight: bold;
                    color: #1976D2;
                    text-align: center;
                }
            """)
            title_label.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(title_label)

            # Version info
            version_label = QtWidgets.QLabel("Version 1.0.0")
            version_label.setStyleSheet("""
                QLabel {
                    font-size: 14px;
                    color: #666;
                    text-align: center;
                }
            """)
            version_label.setAlignment(QtCore.Qt.AlignCenter)
            layout.addWidget(version_label)

            # Description
            desc_text = """
            <p><b>FreeCAD AI Assistant</b> brings powerful AI capabilities directly into FreeCAD.</p>
            <p>Features:</p>
            <ul>
            <li>💬 Chat with AI about your designs</li>
            <li>🤖 AI Agent for automated tasks</li>
            <li>🔌 Multiple AI provider support</li>
            <li>🛠️ FreeCAD integration tools</li>
            </ul>
            <p>Supported Providers: OpenAI, Anthropic, Google Gemini, Local Ollama</p>
            """
            
            desc_label = QtWidgets.QLabel(desc_text)
            desc_label.setStyleSheet("""
                QLabel {
                    font-size: 12px;
                    color: #333;
                    background-color: #f9f9f9;
                    border: 1px solid #ddd;
                    border-radius: 5px;
                    padding: 15px;
                }
            """)
            desc_label.setWordWrap(True)
            layout.addWidget(desc_label)

            # Links
            links_layout = QtWidgets.QHBoxLayout()
            
            github_button = QtWidgets.QPushButton("📁 GitHub Repository")
            github_button.setStyleSheet("""
                QPushButton {
                    background-color: #24292e;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1c2125;
                }
            """)
            links_layout.addWidget(github_button)

            docs_button = QtWidgets.QPushButton("📚 Documentation")
            docs_button.setStyleSheet("""
                QPushButton {
                    background-color: #2196F3;
                    color: white;
                    border: none;
                    padding: 8px 15px;
                    border-radius: 5px;
                    font-weight: bold;
                }
                QPushButton:hover {
                    background-color: #1976D2;
                }
            """)
            links_layout.addWidget(docs_button)
            
            links_layout.addStretch()
            layout.addLayout(links_layout)

            layout.addStretch()

            self.tab_widget.addTab(about_tab, "ℹ️ About")
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: About tab creation failed: {e}\n")

    def _create_fallback_tabs(self):
        """Create minimal fallback tabs if full tab creation fails."""
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Creating fallback tabs...\n")
            
            # Simple fallback tabs
            fallback_tabs = [
                ("Chat", "💬 Chat functionality will be available after proper initialization"),
                ("Settings", "⚙️ Configure AI providers and settings"),
                ("About", "ℹ️ Information about FreeCAD AI Assistant")
            ]
            
            for tab_name, message in fallback_tabs:
                tab = QtWidgets.QWidget()
                layout = QtWidgets.QVBoxLayout(tab)
                layout.setContentsMargins(20, 20, 20, 20)
                
                label = QtWidgets.QLabel(message)
                label.setStyleSheet("""
                    QLabel {
                        font-size: 14px;
                        color: #666;
                        padding: 20px;
                        background-color: #f5f5f5;
                        border: 1px dashed #ccc;
                        border-radius: 8px;
                        text-align: center;
                    }
                """)
                label.setAlignment(QtCore.Qt.AlignCenter)
                label.setWordWrap(True)
                layout.addWidget(label)
                layout.addStretch()
                
                self.tab_widget.addTab(tab, tab_name)
                
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Fallback tab creation failed: {e}\n")
                    
                    # Add tab to widget
            self.tab_widget.addTab(tab, tab_name)
                    
            FreeCAD.Console.PrintMessage(f"FreeCAD AI: Created nuclear safe {tab_name} tab\n")
                    
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"FreeCAD AI: Failed to create basic {tab_name} tab: {e}\n")       
            FreeCAD.Console.PrintMessage("FreeCAD AI: Nuclear safe tab creation complete\n")
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Nuclear safe tab creation failed: {e}\n")
            # Absolute fallback - create single tab
            try:
                fallback_tab = QtWidgets.QWidget()
                fallback_layout = QtWidgets.QVBoxLayout(fallback_tab)
                fallback_label = QtWidgets.QLabel("FreeCAD AI - Safe Mode")
                fallback_layout.addWidget(fallback_label)
                self.tab_widget.addTab(fallback_tab, "AI")
            except Exception:
                pass  # If even this fails, we'll have an empty tab widget

    def _initialize_specific_tab(self, tab_name):
        """Initialize a specific tab when user requests it."""
        try:
            FreeCAD.Console.PrintMessage(f"FreeCAD AI: User requested initialization of {tab_name} tab\n")
            
            # Find the tab
            tab_index = -1
            for i in range(self.tab_widget.count()):
                if self.tab_widget.tabText(i) == tab_name:
                    tab_index = i
                    break
            
            if tab_index == -1:
                FreeCAD.Console.PrintWarning(f"FreeCAD AI: Could not find {tab_name} tab\n")
                return
            
            # Create the actual widget for this tab
            if tab_name == "Chat":
                self._create_chat_tab_safe(tab_index)
            elif tab_name == "Providers":
                self._create_providers_tab_safe(tab_index)
            elif tab_name == "Tools":
                self._create_tools_tab_safe(tab_index)
            elif tab_name == "Settings":
                self._create_settings_tab_safe(tab_index)
            
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Failed to initialize {tab_name} tab: {e}\n")

    def _create_chat_tab_safe(self, tab_index):
        """Safely create the chat tab."""
        try:
            from .conversation_widget import ConversationWidget
            widget = ConversationWidget()
            self.tab_widget.removeTab(tab_index)
            self.tab_widget.insertTab(tab_index, widget, "Chat")
            self.conversation_widget = widget
            FreeCAD.Console.PrintMessage("FreeCAD AI: Chat tab initialized successfully\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Failed to create chat tab: {e}\n")

    def _create_providers_tab_safe(self, tab_index):
        """Safely create the providers tab."""
        try:
            from .providers_widget import ProvidersWidget
            widget = ProvidersWidget()
            self.tab_widget.removeTab(tab_index)
            self.tab_widget.insertTab(tab_index, widget, "Providers")
            self.providers_widget = widget
            FreeCAD.Console.PrintMessage("FreeCAD AI: Providers tab initialized successfully\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Failed to create providers tab: {e}\n")

    def _create_tools_tab_safe(self, tab_index):
        """Safely create the tools tab."""
        try:
            from .tools_widget_compact import ToolsWidget
            widget = ToolsWidget()
            self.tab_widget.removeTab(tab_index)
            self.tab_widget.insertTab(tab_index, widget, "Tools")
            self.tools_widget = widget
            FreeCAD.Console.PrintMessage("FreeCAD AI: Tools tab initialized successfully\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Failed to create tools tab: {e}\n")

    def _create_settings_tab_safe(self, tab_index):
        """Safely create the settings tab."""
        try:
            from .settings_widget import SettingsWidget
            widget = SettingsWidget()
            self.tab_widget.removeTab(tab_index)
            self.tab_widget.insertTab(tab_index, widget, "Settings")
            self.settings_widget = widget
            FreeCAD.Console.PrintMessage("FreeCAD AI: Settings tab initialized successfully\n")
        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Failed to create settings tab: {e}\n")