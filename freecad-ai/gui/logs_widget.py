"""Logs Widget - GUI for viewing logs"""

from PySide2 import QtWidgets


class LogsWidget(QtWidgets.QWidget):
    """Widget for viewing logs."""

    def __init__(self, parent=None):
        super(LogsWidget, self).__init__(parent)
        layout = QtWidgets.QVBoxLayout(self)
        label = QtWidgets.QLabel("Logs Viewer - Implementation in progress")
        layout.addWidget(label)
