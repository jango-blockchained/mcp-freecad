import os
import time
from collections import deque

import FreeCAD
import FreeCADGui
from PySide2 import QtCore, QtGui, QtWidgets, QtSvg


class MCPFlowMessage:
    """Represents a message in the MCP flow visualization."""

    def __init__(self, source, destination, message_type, content, timestamp=None):
        self.source = source
        self.destination = destination
        self.message_type = message_type
        self.content = content
        self.timestamp = timestamp or time.time()
        self.id = f"{int(self.timestamp * 1000)}-{hash(content) % 10000}"


class MCPFlowVisualization(QtWidgets.QWidget):
    """A widget that shows the MCP message flow visualization."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("MCP Flow Visualization")
        self.setMinimumSize(800, 600)

        # Message history with max size
        self.message_history = deque(maxlen=50)

        # Components in the flow diagram
        self.components = {
            "ai_assistant": {"name": "AI Assistant", "x": 100, "y": 50},
            "mcp_server": {"name": "MCP Server", "x": 350, "y": 50},
            "freecad_connection": {"name": "FreeCAD Connection", "x": 600, "y": 50},
            "freecad": {"name": "FreeCAD", "x": 600, "y": 200},
        }

        # Connection types
        self.connection_types = {
            "socket": "Socket Connection",
            "bridge": "CLI Bridge",
            "mock": "Mock Connection"
        }

        # Current connection type
        self.current_connection_type = "socket"

        # Set up the UI
        self.setup_ui()

        # Setup timer for animation
        self.animation_timer = QtCore.QTimer(self)
        self.animation_timer.timeout.connect(self.update_animation)
        self.animation_timer.start(50)  # 50ms refresh

        # Animation state
        self.active_messages = []

        # Add some test messages
        self.add_test_messages()

    def setup_ui(self):
        """Set up the user interface."""
        # Main layout
        layout = QtWidgets.QVBoxLayout(self)

        # Toolbar area
        toolbar_layout = QtWidgets.QHBoxLayout()
        layout.addLayout(toolbar_layout)

        # Connection type selector
        self.connection_type_label = QtWidgets.QLabel("Connection Type:")
        toolbar_layout.addWidget(self.connection_type_label)

        self.connection_type_combo = QtWidgets.QComboBox()
        for conn_id, conn_name in self.connection_types.items():
            self.connection_type_combo.addItem(conn_name, conn_id)
        self.connection_type_combo.currentIndexChanged.connect(self.change_connection_type)
        toolbar_layout.addWidget(self.connection_type_combo)

        # Clear button
        self.clear_button = QtWidgets.QPushButton("Clear Messages")
        self.clear_button.clicked.connect(self.clear_messages)
        toolbar_layout.addWidget(self.clear_button)

        toolbar_layout.addStretch()

        # Message display area
        self.flow_view = QtWidgets.QGraphicsView()
        self.flow_scene = QtWidgets.QGraphicsScene()
        self.flow_view.setScene(self.flow_scene)
        self.flow_view.setRenderHint(QtGui.QPainter.Antialiasing)
        layout.addWidget(self.flow_view)

        # Message list at the bottom
        self.message_list = QtWidgets.QTableWidget()
        self.message_list.setColumnCount(5)
        self.message_list.setHorizontalHeaderLabels(["Time", "Source", "Destination", "Type", "Content"])
        self.message_list.horizontalHeader().setSectionResizeMode(4, QtWidgets.QHeaderView.Stretch)
        self.message_list.setSelectionBehavior(QtWidgets.QAbstractItemView.SelectRows)
        self.message_list.setMinimumHeight(200)
        layout.addWidget(self.message_list)

        # Draw initial components
        self.draw_components()

    def draw_components(self):
        """Draw the components on the flow diagram."""
        self.flow_scene.clear()

        # Draw each component
        for comp_id, comp in self.components.items():
            rect = QtWidgets.QGraphicsRectItem(comp["x"], comp["y"], 150, 80)
            rect.setBrush(QtGui.QBrush(QtGui.QColor(240, 240, 240)))
            rect.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0), 2))

            text = QtWidgets.QGraphicsTextItem(comp["name"])
            text.setPos(comp["x"] + 75 - text.boundingRect().width() / 2,
                       comp["y"] + 40 - text.boundingRect().height() / 2)

            self.flow_scene.addItem(rect)
            self.flow_scene.addItem(text)

        # Draw connection lines based on current connection type
        pen = QtGui.QPen(QtGui.QColor(0, 0, 200), 2, QtCore.Qt.DashLine)

        # MCP Server to FreeCAD Connection
        line = QtWidgets.QGraphicsLineItem(
            self.components["mcp_server"]["x"] + 150,
            self.components["mcp_server"]["y"] + 40,
            self.components["freecad_connection"]["x"],
            self.components["freecad_connection"]["y"] + 40
        )
        line.setPen(pen)
        self.flow_scene.addItem(line)

        # FreeCAD Connection to FreeCAD
        conn_line = QtWidgets.QGraphicsLineItem(
            self.components["freecad_connection"]["x"] + 75,
            self.components["freecad_connection"]["y"] + 80,
            self.components["freecad"]["x"] + 75,
            self.components["freecad"]["y"]
        )
        conn_line.setPen(pen)
        self.flow_scene.addItem(conn_line)

        # AI Assistant to MCP Server
        ai_line = QtWidgets.QGraphicsLineItem(
            self.components["ai_assistant"]["x"] + 150,
            self.components["ai_assistant"]["y"] + 40,
            self.components["mcp_server"]["x"],
            self.components["mcp_server"]["y"] + 40
        )
        ai_line.setPen(pen)
        self.flow_scene.addItem(ai_line)

        # Add connection type label
        conn_text = QtWidgets.QGraphicsTextItem(
            f"Connection: {self.connection_types[self.current_connection_type]}"
        )
        conn_text.setPos(
            self.components["freecad_connection"]["x"] + 75 - conn_text.boundingRect().width() / 2,
            self.components["freecad_connection"]["y"] + 100
        )
        conn_text.setDefaultTextColor(QtGui.QColor(0, 100, 200))
        self.flow_scene.addItem(conn_text)

    def change_connection_type(self, index):
        """Change the current connection type."""
        self.current_connection_type = self.connection_type_combo.itemData(index)
        self.draw_components()

    def clear_messages(self):
        """Clear all messages from the visualization."""
        self.message_history.clear()
        self.active_messages.clear()
        self.update_message_list()

    def add_message(self, source, destination, message_type, content):
        """Add a new message to the flow visualization."""
        msg = MCPFlowMessage(source, destination, message_type, content)
        self.message_history.append(msg)

        # Add to active messages for animation
        self.active_messages.append({
            "message": msg,
            "progress": 0.0,  # 0.0 to 1.0 for animation
            "active": True
        })

        # Update the message list
        self.update_message_list()

    def update_message_list(self):
        """Update the message list table."""
        self.message_list.setRowCount(0)  # Clear the table

        # Add messages to the table (newest first)
        for idx, msg in enumerate(reversed(self.message_history)):
            row = self.message_list.rowCount()
            self.message_list.insertRow(row)

            # Format timestamp
            time_str = time.strftime("%H:%M:%S", time.localtime(msg.timestamp))
            ms = int((msg.timestamp - int(msg.timestamp)) * 1000)
            time_str = f"{time_str}.{ms:03d}"

            self.message_list.setItem(row, 0, QtWidgets.QTableWidgetItem(time_str))
            self.message_list.setItem(row, 1, QtWidgets.QTableWidgetItem(msg.source))
            self.message_list.setItem(row, 2, QtWidgets.QTableWidgetItem(msg.destination))
            self.message_list.setItem(row, 3, QtWidgets.QTableWidgetItem(msg.message_type))

            # Trim content if too long
            content = msg.content
            if len(content) > 100:
                content = content[:97] + "..."
            self.message_list.setItem(row, 4, QtWidgets.QTableWidgetItem(content))

    def update_animation(self):
        """Update the animation of the message flow."""
        # Redraw components and flow lines
        self.draw_components()

        # Process active messages
        updated_active_messages = []
        for msg_data in self.active_messages:
            # Update progress
            msg_data["progress"] += 0.02  # Increment by 2% per frame

            # If still active, draw and keep in the list
            if msg_data["progress"] <= 1.0:
                self.draw_message(msg_data["message"], msg_data["progress"])
                updated_active_messages.append(msg_data)

        # Update active messages list
        self.active_messages = updated_active_messages

    def draw_message(self, message, progress):
        """Draw a message at the given progress point along its path."""
        # Get source and destination components
        if message.source in self.components and message.destination in self.components:
            src = self.components[message.source]
            dst = self.components[message.destination]

            # Calculate the position along the path
            start_x = src["x"] + 150 if message.source != "freecad_connection" else src["x"] + 75
            start_y = src["y"] + 40 if message.destination != "freecad" else src["y"] + 80

            end_x = dst["x"] if message.destination != "freecad_connection" else dst["x"] + 75
            end_y = dst["y"] + 40 if message.source != "freecad_connection" else dst["y"]

            pos_x = start_x + (end_x - start_x) * progress
            pos_y = start_y + (end_y - start_y) * progress

            # Draw the message circle
            circle = QtWidgets.QGraphicsEllipseItem(pos_x - 5, pos_y - 5, 10, 10)

            # Set color based on message type
            if message.message_type == "command":
                circle.setBrush(QtGui.QBrush(QtGui.QColor(255, 165, 0)))  # Orange
            elif message.message_type == "response":
                circle.setBrush(QtGui.QBrush(QtGui.QColor(0, 200, 0)))  # Green
            elif message.message_type == "error":
                circle.setBrush(QtGui.QBrush(QtGui.QColor(255, 0, 0)))  # Red
            else:
                circle.setBrush(QtGui.QBrush(QtGui.QColor(100, 100, 255)))  # Blue

            circle.setPen(QtGui.QPen(QtGui.QColor(0, 0, 0), 1))
            self.flow_scene.addItem(circle)

    def add_test_messages(self):
        """Add some test messages for demonstration."""
        self.add_message("ai_assistant", "mcp_server", "command", "list_tools")
        QtCore.QTimer.singleShot(500, lambda: self.add_message(
            "mcp_server", "ai_assistant", "response", '{"tools": ["create_box", "create_cylinder"]}'
        ))
        QtCore.QTimer.singleShot(1500, lambda: self.add_message(
            "ai_assistant", "mcp_server", "command", "execute_tool create_box length=10 width=10 height=10"
        ))
        QtCore.QTimer.singleShot(1700, lambda: self.add_message(
            "mcp_server", "freecad_connection", "command", "create_box(10, 10, 10)"
        ))
        QtCore.QTimer.singleShot(2000, lambda: self.add_message(
            "freecad_connection", "freecad", "command", "exec:create_box(10, 10, 10)"
        ))
        QtCore.QTimer.singleShot(2500, lambda: self.add_message(
            "freecad", "freecad_connection", "response", "Box created successfully"
        ))
        QtCore.QTimer.singleShot(2700, lambda: self.add_message(
            "freecad_connection", "mcp_server", "response", '{"status": "success", "message": "Box created successfully"}'
        ))
        QtCore.QTimer.singleShot(3000, lambda: self.add_message(
            "mcp_server", "ai_assistant", "response", '{"result": "Box created successfully", "object_id": "Box001"}'
        ))


class MCPFlowDialog:
    """Dialog wrapper for the MCP Flow Visualization."""

    def __init__(self):
        self.dialog = None
        self.visualization = None

    def show(self):
        """Show the flow visualization dialog."""
        if self.dialog is None:
            # Create dialog
            self.dialog = QtWidgets.QDialog(FreeCADGui.getMainWindow())
            self.dialog.setWindowTitle("MCP Flow Visualization")
            self.dialog.setMinimumSize(800, 600)

            # Create layout
            layout = QtWidgets.QVBoxLayout(self.dialog)

            # Create visualization widget
            self.visualization = MCPFlowVisualization(self.dialog)
            layout.addWidget(self.visualization)

            # Set up the dialog
            self.dialog.setLayout(layout)

        # Show the dialog
        self.dialog.show()

        return self.dialog

    def add_message(self, source, destination, message_type, content):
        """Add a message to the visualization."""
        if self.visualization:
            self.visualization.add_message(source, destination, message_type, content)


# Global instance for access from other modules
mcp_flow_dialog = MCPFlowDialog()
