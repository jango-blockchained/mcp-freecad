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

        self._setup_ui()
        self._setup_provider_service()

        # Set flexible sizing
        self.setMinimumWidth(350)
        self.resize(450, 700)

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
            from ..ai.provider_integration_service import get_provider_service

            self.provider_service = get_provider_service()

            # Connect provider service signals to update status
            self.provider_service.provider_status_changed.connect(
                self._on_provider_status_changed
            )
            self.provider_service.providers_updated.connect(self._on_providers_updated)

            # Initialize providers from configuration with multiple attempts
            QtCore.QTimer.singleShot(
                1000, self.provider_service.initialize_providers_from_config
            )
            # Retry after 3 seconds if first attempt fails
            QtCore.QTimer.singleShot(3000, self._retry_provider_initialization)

        except ImportError as e:
            if hasattr(self, "status_label"):
                self.status_label.setText(f"Warning: {e}")
            print(f"FreeCAD AI: Provider service unavailable - {e}")

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

            # Create widgets with provider service integration
            self.connection_widget = ConnectionWidget()
            self.providers_widget = ProvidersWidget()
            self.conversation_widget = ConversationWidget()
            self.settings_widget = SettingsWidget()
            self.tools_widget = ToolsWidget()  # Use compact tools widget

            # Connect widgets to provider service if available
            if self.provider_service:
                self._connect_widgets_to_service()

            # Add tabs in logical order (removed Logs)
            self.tab_widget.addTab(self.providers_widget, "Providers")
            self.tab_widget.addTab(self.conversation_widget, "Chat")
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
            # Connect providers widget to manage providers and API keys
            if hasattr(self.providers_widget, "set_provider_service"):
                self.providers_widget.set_provider_service(self.provider_service)

            # Connect providers widget API key changes to service
            if hasattr(self.providers_widget, "api_key_changed"):
                self.providers_widget.api_key_changed.connect(
                    self._on_settings_api_key_changed
                )

            # Connect conversation widget to get provider updates
            if hasattr(self.conversation_widget, "set_provider_service"):
                self.conversation_widget.set_provider_service(self.provider_service)

            # Connect connection widget to show MCP connection status (no AI provider status)
            if hasattr(self.connection_widget, "set_provider_service"):
                self.connection_widget.set_provider_service(self.provider_service)

        except Exception as e:
            self.status_label.setText(f"⚠️ {e}")

    def _on_settings_api_key_changed(self, provider_name: str):
        """Handle API key changes from settings widget."""
        if self.provider_service:
            self.provider_service.update_provider_from_settings(provider_name)
