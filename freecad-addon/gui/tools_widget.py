"""Tools Widget - GUI for tool management"""

from PySide2 import QtWidgets


class ToolsWidget(QtWidgets.QWidget):
    """Widget for tool management."""
    
    def __init__(self, parent=None):
        super(ToolsWidget, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel("Tool Management - Implementation in progress")
        layout.addWidget(label)