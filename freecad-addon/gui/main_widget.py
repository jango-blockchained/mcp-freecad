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
        self._setup_ui()
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

    def _create_tabs(self):
        """Create the tab interface."""
        try:
            from .connection_widget import ConnectionWidget
            from .server_widget import ServerWidget
            from .ai_widget import AIWidget
            from .tools_widget import ToolsWidget
            from .settings_widget import SettingsWidget
            from .logs_widget import LogsWidget
            
            self.tab_widget.addTab(ConnectionWidget(), "Connections")
            self.tab_widget.addTab(ServerWidget(), "Servers")
            self.tab_widget.addTab(AIWidget(), "AI Models")
            self.tab_widget.addTab(ToolsWidget(), "Tools")
            self.tab_widget.addTab(SettingsWidget(), "Settings")
            self.tab_widget.addTab(LogsWidget(), "Logs")
            
        except ImportError:
            for name in ["Connections", "Servers", "AI Models", "Tools", "Settings", "Logs"]:
                tab = QtWidgets.QWidget()
                QtWidgets.QVBoxLayout(tab).addWidget(QtWidgets.QLabel(f"{name} - Loading..."))
                self.tab_widget.addTab(tab, name)