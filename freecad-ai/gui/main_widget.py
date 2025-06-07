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
        """Ultra-safe initialization - minimal operations only."""
        try:
            FreeCAD.Console.PrintMessage("FreeCAD AI: Starting safe widget initialization...\n")

            # Initialize parent class with minimal parameters
            super(MCPMainWidget, self).__init__("FreeCAD AI", parent)

            # Initialize all service references to None immediately
            self.provider_service = None
            self.agent_manager = None
            self.status_label = None
            self.tab_widget = None
            self.main_widget = None
            
            # Flags to track initialization state
            self._ui_initialized = False
            self._services_initialized = False
            self._widgets_connected = False
            self._initialization_failed = False

            # Set basic dock properties with maximum safety
            self._setup_basic_dock_properties()

            # Create minimal main widget
            self._create_minimal_widget()

            # Schedule the rest of initialization to happen later
            # This prevents crashes during workbench activation
            if hasattr(QtCore.QTimer, 'singleShot'):
                QtCore.QTimer.singleShot(100, self._delayed_initialization_phase1)
            else:
                # Fallback if QTimer is not available
                self._delayed_initialization_phase1()

            FreeCAD.Console.PrintMessage("FreeCAD AI: Basic widget initialization complete\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"FreeCAD AI: Critical widget initialization error: {e}\n")
            self._initialization_failed = True
            self._create_error_widget(str(e))

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
            print(f"FreeCAD AI: Connecting widgets to services...")
            print(
                f"FreeCAD AI: Provider service available: {self.provider_service is not None}"
            )
            print(
                f"FreeCAD AI: Agent manager available: {self.agent_manager is not None}"
            )

            if not self.provider_service:
                print(
                    "FreeCAD AI: Warning - provider service still None during connection"
                )
                # Try to get it again
                try:
                    from ..ai.provider_integration_service import get_provider_service

                    self.provider_service = get_provider_service()
                    print(
                        f"FreeCAD AI: Retry got provider service: {self.provider_service is not None}"
                    )
                except Exception as e:
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
