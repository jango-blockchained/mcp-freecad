"""Settings Widget - GUI for addon settings"""

from PySide2 import QtWidgets


class SettingsWidget(QtWidgets.QWidget):
    """Widget for addon settings."""
    
    def __init__(self, parent=None):
        super(SettingsWidget, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel("Settings Management - Implementation in progress")
        layout.addWidget(label)