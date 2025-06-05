"""Main Widget for FreeCAD AI FreeCAD Addon"""

from PySide2 import QtCore, QtGui, QtWidgets


class MCPMainWidget(QtWidgets.QDockWidget):
    """Main widget for FreeCAD AI addon."""

    def __init__(self, parent=None):
        super(MCPMainWidget, self).__init__("FreeCAD AI", parent)

        self.setAllowedAreas(
            QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea
        )
        self.setFeatures(
            QtWidgets.QDockWidget.DockWidgetMovable
            | QtWidgets.QDockWidget.DockWidgetFloatable
        )

        self.main_widget = QtWidgets.QWidget()
        self.setWidget(self.main_widget)

        # Initialize provider service
        self.provider_service = None

        # Initialize agent manager
        self.agent_manager = None
        self._init_agent_manager()

        # Setup provider service BEFORE UI
        self._setup_provider_service()

        # Setup UI
        self._setup_ui()

        # Connect widgets to services AFTER provider service is set up
        # Use a delayed connection to ensure provider service is ready
        QtCore.QTimer.singleShot(500, self._connect_widgets_to_service)

        # Set flexible sizing
        self.setMinimumWidth(350)
        self.resize(450, 700)

        # Load persisted mode
        self._load_persisted_mode()

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QtWidgets.QVBoxLayout(self.main_widget)
        layout.setSpacing(2)  # Reduced spacing
        layout.setContentsMargins(2, 2, 2, 2)  # Reduced margins

        # Compact header with inline status
        header_layout = QtWidgets.QHBoxLayout()
        header_label = QtWidgets.QLabel("🤖 FreeCAD AI")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px;")
        header_layout.addWidget(header_label)

        # Add mode selector
        self.mode_label = QtWidgets.QLabel("Mode:")
        self.mode_label.setStyleSheet("font-size: 12px; margin-left: 10px;")
        header_layout.addWidget(self.mode_label)

        self.mode_selector = QtWidgets.QComboBox()
        self.mode_selector.addItems(["💬 Chat", "🤖 Agent"])
        self.mode_selector.setToolTip("Chat: AI provides instructions\nAgent: AI executes autonomously")
        self.mode_selector.setStyleSheet("""
            QComboBox {
                padding: 2px 8px;
                font-size: 12px;
                min-width: 100px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: white;
            }
            QComboBox:hover {
                border-color: #2196F3;
            }
        """)
        self.mode_selector.currentTextChanged.connect(self._on_mode_changed)
        header_layout.addWidget(self.mode_selector)

        header_layout.addStretch()

        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("padding: 2px 8px; background-color: #f0f0f0; border-radius: 10px; font-size: 11px;")
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
                    import sys
                    import os
                    parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    if parent_dir not in sys.path:
                        sys.path.insert(0, parent_dir)
                    from ai.provider_integration_service import get_provider_service
                    provider_service_imported = True
                    print("FreeCAD AI: Provider service imported after adding to sys.path")
                except ImportError as e:
                    print(f"FreeCAD AI: Import with sys.path modification failed: {e}")
            
            if not provider_service_imported:
                raise ImportError("Could not import provider_integration_service after all strategies")

            self.provider_service = get_provider_service()
            print(f"FreeCAD AI: Provider service created: {self.provider_service is not None}")

            if self.provider_service:
                # Connect provider service signals to update status
                self.provider_service.provider_status_changed.connect(
                    self._on_provider_status_changed
                )
                self.provider_service.providers_updated.connect(self._on_providers_updated)
                print("FreeCAD AI: Provider service signals connected")

                # Initialize providers from configuration with multiple attempts
                QtCore.QTimer.singleShot(
                    1000, self.provider_service.initialize_providers_from_config
                )
                # Retry after 3 seconds if first attempt fails
                QtCore.QTimer.singleShot(3000, self._retry_provider_initialization)
                print("FreeCAD AI: Provider service initialization scheduled")
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

    def _on_provider_status_changed(
        self, provider_name: str, status: str, message: str
    ):
        """Handle provider status changes."""
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

    def _on_providers_updated(self):
        """Handle providers list update."""
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
            from .connection_widget import ConnectionWidget
            from .server_widget import ServerWidget
            from .providers_widget import ProvidersWidget
            from .conversation_widget import ConversationWidget
            from .tools_widget_compact import ToolsWidget  # Use compact version
            from .settings_widget import SettingsWidget
            from .agent_control_widget import AgentControlWidget

            # Create widgets
            self.connection_widget = ConnectionWidget()
            self.providers_widget = ProvidersWidget()
            self.conversation_widget = ConversationWidget()
            self.settings_widget = SettingsWidget()
            self.tools_widget = ToolsWidget()  # Use compact tools widget
            self.agent_control_widget = AgentControlWidget()

            # Add tabs in logical order (removed Logs)
            self.tab_widget.addTab(self.providers_widget, "Providers")
            self.tab_widget.addTab(self.conversation_widget, "Chat")
            self.tab_widget.addTab(self.agent_control_widget, "Agent")
            self.tab_widget.addTab(self.tools_widget, "Tools")
            self.tab_widget.addTab(self.connection_widget, "Connections")
            self.tab_widget.addTab(ServerWidget(), "Servers")
            self.tab_widget.addTab(self.settings_widget, "Settings")

        except ImportError:
            for name in [
                "Providers",
                "Chat",
                "Tools",
                "Connections",
                "Servers",
                "Settings",
            ]:
                tab = QtWidgets.QWidget()
                tab_layout = QtWidgets.QVBoxLayout(tab)
                tab_layout.addWidget(QtWidgets.QLabel(f"{name} - Loading..."))
                self.tab_widget.addTab(tab, name)

    def _connect_widgets_to_service(self):
        """Connect GUI widgets to the provider service."""
        try:
            print(f"FreeCAD AI: Connecting widgets to services...")
            print(f"FreeCAD AI: Provider service available: {self.provider_service is not None}")
            print(f"FreeCAD AI: Agent manager available: {self.agent_manager is not None}")

            if not self.provider_service:
                print("FreeCAD AI: Warning - provider service still None during connection")
                # Try to get it again
                try:
                    from ..ai.provider_integration_service import get_provider_service
                    self.provider_service = get_provider_service()
                    print(f"FreeCAD AI: Retry got provider service: {self.provider_service is not None}")
                except Exception as e:
                    print(f"FreeCAD AI: Failed to get provider service on retry: {e}")

            # Connect providers widget to manage providers and API keys
            if hasattr(self.providers_widget, "set_provider_service"):
                self.providers_widget.set_provider_service(self.provider_service)
                print("FreeCAD AI: Provider service connected to providers widget")
            else:
                print("FreeCAD AI: Warning - providers widget has no set_provider_service method")

            # Connect providers widget API key changes to service
            if hasattr(self.providers_widget, "api_key_changed"):
                self.providers_widget.api_key_changed.connect(
                    self._on_settings_api_key_changed
                )

            # Connect conversation widget to get provider updates
            if hasattr(self.conversation_widget, "set_provider_service"):
                self.conversation_widget.set_provider_service(self.provider_service)
                print("FreeCAD AI: Provider service connected to conversation widget")

                # Force refresh the conversation widget's provider list
                if hasattr(self.conversation_widget, "refresh_providers"):
                    self.conversation_widget.refresh_providers()
                    print("FreeCAD AI: Conversation widget providers refreshed")
            else:
                print("FreeCAD AI: Warning - conversation widget has no set_provider_service method")

            # Connect conversation widget to agent manager
            if self.agent_manager and hasattr(self.conversation_widget, "set_agent_manager"):
                self.conversation_widget.set_agent_manager(self.agent_manager)
                print("FreeCAD AI: Agent manager connected to conversation widget")
            elif not self.agent_manager:
                print("FreeCAD AI: Agent manager is None - cannot connect to conversation widget")

            # Connect agent control widget to agent manager
            if self.agent_manager and hasattr(self.agent_control_widget, "set_agent_manager"):
                self.agent_control_widget.set_agent_manager(self.agent_manager)
                print("FreeCAD AI: Agent manager connected to agent control widget")
            elif not self.agent_manager:
                print("FreeCAD AI: Agent manager is None - cannot connect to agent control widget")

            # Connect connection widget to show MCP connection status (no AI provider status)
            if hasattr(self.connection_widget, "set_provider_service"):
                self.connection_widget.set_provider_service(self.provider_service)

            # Schedule a second connection attempt to be sure
            QtCore.QTimer.singleShot(2000, self._final_connection_check)

        except Exception as e:
            self.status_label.setText(f"⚠️ {e}")
            import traceback
            print(f"FreeCAD AI: Error connecting widgets: {e}")
            print(f"FreeCAD AI: Traceback: {traceback.format_exc()}")

    def _final_connection_check(self):
        """Final check to ensure all connections are working."""
        try:
            print("FreeCAD AI: Performing final connection check...")

            # Force provider service to initialize providers if not done yet
            if self.provider_service and hasattr(self.provider_service, "initialize_providers_from_config"):
                self.provider_service.initialize_providers_from_config()
                print("FreeCAD AI: Forced provider service initialization")

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

    def _init_agent_manager(self):
        """Initialize the agent manager."""
        try:
            from ..core.agent_manager import AgentManager, AgentMode
            print("FreeCAD AI: AgentManager import successful")

            self.agent_manager = AgentManager()
            print("FreeCAD AI: AgentManager instance created")

            # Register callbacks
            self.agent_manager.register_callback(
                "on_mode_change",
                self._on_agent_mode_changed
            )
            self.agent_manager.register_callback(
                "on_state_change",
                self._on_agent_state_changed
            )

            print("FreeCAD AI: Agent Manager initialized successfully")
        except ImportError as e:
            print(f"FreeCAD AI: Agent Manager import failed - {e}")
            self.agent_manager = None
        except Exception as e:
            print(f"FreeCAD AI: Agent Manager initialization failed - {e}")
            import traceback
            print(f"FreeCAD AI: Full traceback: {traceback.format_exc()}")
            self.agent_manager = None

    def _on_mode_changed(self, mode_text: str):
        """Handle mode selector change."""
        if not self.agent_manager:
            return

        try:
            from ..core.agent_manager import AgentMode

            if "Chat" in mode_text:
                self.agent_manager.set_mode(AgentMode.CHAT)
                self._update_ui_for_chat_mode()
            elif "Agent" in mode_text:
                self.agent_manager.set_mode(AgentMode.AGENT)
                self._update_ui_for_agent_mode()

            # Save mode preference
            self._save_mode(mode_text)

            # Notify conversation widget of mode change
            if hasattr(self, 'conversation_widget') and hasattr(self.conversation_widget, 'set_agent_mode'):
                self.conversation_widget.set_agent_mode(self.agent_manager.get_mode())

            # Update agent control widget if available
            if hasattr(self, 'agent_control_widget'):
                # Refresh the agent control widget state
                if hasattr(self.agent_control_widget, '_update_ui_from_agent_state'):
                    self.agent_control_widget._update_ui_from_agent_state()

        except Exception as e:
            print(f"FreeCAD AI: Error changing mode - {e}")

    def _on_agent_mode_changed(self, old_mode, new_mode):
        """Handle agent mode change callback."""
        mode_display = "Chat" if new_mode.value == "chat" else "Agent"
        self.status_label.setText(f"Mode: {mode_display}")

        # Update mode selector if it doesn't match
        current_selector = self.mode_selector.currentText()
        if new_mode.value == "chat" and "Chat" not in current_selector:
            self.mode_selector.setCurrentText("💬 Chat")
        elif new_mode.value == "agent" and "Agent" not in current_selector:
            self.mode_selector.setCurrentText("🤖 Agent")

    def _on_agent_state_changed(self, old_state, new_state):
        """Handle agent state change callback."""
        # Update status based on execution state
        state_display = {
            "idle": "Ready",
            "planning": "Planning...",
            "executing": "Executing...",
            "paused": "Paused",
            "error": "Error",
            "completed": "Completed"
        }
        status_text = state_display.get(new_state.value, new_state.value)

        # Show mode and state
        mode_text = "Chat" if self.agent_manager.current_mode.value == "chat" else "Agent"
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

    def _update_ui_for_chat_mode(self):
        """Update UI elements for chat mode."""
        # In chat mode, disable autonomous execution features
        if hasattr(self, 'tools_widget'):
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
        if hasattr(self, 'tools_widget'):
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
                "suggestion": "Check FreeCAD console for initialization errors"
            }

        try:
            status = self.agent_manager.get_status()
            return {
                "connected": True,
                "status": status,
                "mode": status.get("mode", "unknown"),
                "state": status.get("state", "unknown"),
                "available_tools": len(status.get("available_tools", {}))
            }
        except Exception as e:
            return {
                "connected": False,
                "error": f"Agent manager exists but is not functional: {e}",
                "suggestion": "Agent manager may be partially initialized"
            }

    def _load_persisted_mode(self):
        """Load persisted mode from settings."""
        try:
            settings = QtCore.QSettings("FreeCAD", "AI_Agent")
            mode = settings.value("agent_mode", "Chat")

            # Find and set the mode in selector
            for i in range(self.mode_selector.count()):
                if mode in self.mode_selector.itemText(i):
                    self.mode_selector.setCurrentIndex(i)
                    break

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
