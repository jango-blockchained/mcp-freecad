"""Main Widget for MCP Integration FreeCAD Addon"""

from PySide2 import QtCore, QtGui, QtWidgets


class MCPMainWidget(QtWidgets.QDockWidget):
    """Main widget for MCP Integration addon."""

    def __init__(self, parent=None):
        super(MCPMainWidget, self).__init__("MCP Integration", parent)

        self.setAllowedAreas(QtCore.Qt.LeftDockWidgetArea | QtCore.Qt.RightDockWidgetArea)
        self.setFeatures(QtWidgets.QDockWidget.DockWidgetMovable |
                        QtWidgets.QDockWidget.DockWidgetFloatable)

        self.main_widget = QtWidgets.QWidget()
        self.setWidget(self.main_widget)

        # Initialize provider service
        self.provider_service = None

        self._setup_ui()
        self._setup_provider_service()
        self.resize(400, 600)

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QtWidgets.QVBoxLayout(self.main_widget)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        header_label = QtWidgets.QLabel("MCP Integration")
        header_label.setStyleSheet("font-weight: bold; font-size: 14px; padding: 10px;")
        layout.addWidget(header_label)

        self.tab_widget = QtWidgets.QTabWidget()
        layout.addWidget(self.tab_widget)
        self._create_tabs()

        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0;")
        layout.addWidget(self.status_label)

    def _setup_provider_service(self):
        """Setup the provider integration service."""
        try:
            from ..ai.provider_integration_service import get_provider_service
            self.provider_service = get_provider_service()

            # Connect provider service signals to update status
            self.provider_service.provider_status_changed.connect(self._on_provider_status_changed)
            self.provider_service.providers_updated.connect(self._on_providers_updated)

            # Initialize providers from configuration
            QtCore.QTimer.singleShot(1000, self.provider_service.initialize_providers_from_config)

        except ImportError as e:
            if hasattr(self, 'status_label'):
                self.status_label.setText(f"Warning: Provider service unavailable - {e}")
            print(f"MCP Integration: Provider service unavailable - {e}")

    def _on_provider_status_changed(self, provider_name: str, status: str, message: str):
        """Handle provider status changes."""
        if status == "connected":
            self.status_label.setText(f"Provider {provider_name}: Connected")
            self.status_label.setStyleSheet("padding: 5px; background-color: #c8e6c9; color: #2e7d32;")
        elif status == "error":
            self.status_label.setText(f"Provider {provider_name}: {message}")
            self.status_label.setStyleSheet("padding: 5px; background-color: #ffcdd2; color: #c62828;")
        else:
            self.status_label.setText(f"Provider {provider_name}: {status}")
            self.status_label.setStyleSheet("padding: 5px; background-color: #fff3e0; color: #ef6c00;")

    def _on_providers_updated(self):
        """Handle providers list update."""
        if self.provider_service:
            active_count = len(self.provider_service.get_active_providers())
            total_count = len(self.provider_service.get_all_providers())
            self.status_label.setText(f"Providers: {active_count}/{total_count} active")
            if active_count > 0:
                self.status_label.setStyleSheet("padding: 5px; background-color: #c8e6c9; color: #2e7d32;")
            else:
                self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; color: #666;")

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
            from .tools_widget import ToolsWidget
            from .settings_widget import SettingsWidget
            from .logs_widget import LogsWidget

            # Create widgets with provider service integration
            self.connection_widget = ConnectionWidget()
            self.providers_widget = ProvidersWidget()
            self.conversation_widget = ConversationWidget()
            self.settings_widget = SettingsWidget()
            self.tools_widget = ToolsWidget()

            # Connect widgets to provider service if available
            if self.provider_service:
                self._connect_widgets_to_service()

            self.tab_widget.addTab(self.providers_widget, "Providers")
            self.tab_widget.addTab(self.conversation_widget, "Conversation")
            self.tab_widget.addTab(self.connection_widget, "Connections")
            self.tab_widget.addTab(ServerWidget(), "Servers")
            self.tab_widget.addTab(self.tools_widget, "Tools")
            self.tab_widget.addTab(self.settings_widget, "Settings")
            self.tab_widget.addTab(LogsWidget(), "Logs")

        except ImportError:
            for name in ["Providers", "Conversation", "Connections", "Servers", "Tools", "Settings", "Logs"]:
                tab = QtWidgets.QWidget()
                QtWidgets.QVBoxLayout(tab).addWidget(QtWidgets.QLabel(f"{name} - Loading..."))
                self.tab_widget.addTab(tab, name)

    def _connect_widgets_to_service(self):
        """Connect GUI widgets to the provider service."""
        try:
            # Connect providers widget to manage providers and API keys
            if hasattr(self.providers_widget, 'set_provider_service'):
                self.providers_widget.set_provider_service(self.provider_service)

            # Connect providers widget API key changes to service
            if hasattr(self.providers_widget, 'api_key_changed'):
                self.providers_widget.api_key_changed.connect(self._on_settings_api_key_changed)

            # Connect conversation widget to get provider updates
            if hasattr(self.conversation_widget, 'set_provider_service'):
                self.conversation_widget.set_provider_service(self.provider_service)

            # Connect connection widget to show MCP connection status (no AI provider status)
            if hasattr(self.connection_widget, 'set_provider_service'):
                self.connection_widget.set_provider_service(self.provider_service)

        except Exception as e:
            self.status_label.setText(f"Widget integration warning: {e}")

    def _on_settings_api_key_changed(self, provider_name: str):
        """Handle API key changes from settings widget."""
        if self.provider_service:
            self.provider_service.update_provider_from_settings(provider_name)
