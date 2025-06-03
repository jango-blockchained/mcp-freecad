"""Tools Widget - GUI for tool management"""

from PySide2 import QtCore, QtGui, QtWidgets
import logging
from typing import Dict, Any, Optional, List


class ToolsWidget(QtWidgets.QWidget):
    """Widget for tool management and execution."""

    tool_executed = QtCore.Signal(str, dict, dict)  # tool_name, parameters, result
    tool_progress = QtCore.Signal(str, int)  # message, percentage

    def __init__(self, parent=None):
        super(ToolsWidget, self).__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.tools = {}
        self._setup_tools()
        self._setup_ui()

    def _setup_tools(self):
        """Setup tool instances."""
        try:
            from ..tools.advanced_primitives import AdvancedPrimitivesTool
            from ..tools.advanced_operations import AdvancedOperationsTool
            from ..tools.surface_modification import SurfaceModificationTool

            self.tools = {
                "advanced_primitives": AdvancedPrimitivesTool(),
                "advanced_operations": AdvancedOperationsTool(),
                "surface_modification": SurfaceModificationTool()
            }
        except ImportError as e:
            self.logger.error(f"Failed to import tools: {e}")
            self.tools = {}

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(10)
        layout.setContentsMargins(10, 10, 10, 10)

        # Create scroll area for tools
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)

        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)

        # Create tool category sections
        self._create_primitives_section(scroll_layout)
        self._create_operations_section(scroll_layout)
        self._create_surface_section(scroll_layout)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Status and progress section
        self._create_status_section(layout)

    def _create_primitives_section(self, layout):
        """Create advanced primitives tools section."""
        group = QtWidgets.QGroupBox("Advanced Primitives")
        group.setCheckable(True)
        group.setChecked(True)
        group_layout = QtWidgets.QVBoxLayout(group)

        # Tube tool
        tube_frame = self._create_tool_frame("Create Tube", self._create_tube_controls(), self._execute_tube)
        group_layout.addWidget(tube_frame)

        # Prism tool
        prism_frame = self._create_tool_frame("Create Prism", self._create_prism_controls(), self._execute_prism)
        group_layout.addWidget(prism_frame)

        # Wedge tool
        wedge_frame = self._create_tool_frame("Create Wedge", self._create_wedge_controls(), self._execute_wedge)
        group_layout.addWidget(wedge_frame)

        # Ellipsoid tool
        ellipsoid_frame = self._create_tool_frame("Create Ellipsoid", self._create_ellipsoid_controls(), self._execute_ellipsoid)
        group_layout.addWidget(ellipsoid_frame)

        layout.addWidget(group)

    def _create_operations_section(self, layout):
        """Create advanced operations tools section."""
        group = QtWidgets.QGroupBox("Advanced Operations")
        group.setCheckable(True)
        group.setChecked(True)
        group_layout = QtWidgets.QVBoxLayout(group)

        # Extrude tool
        extrude_frame = self._create_tool_frame("Extrude Profile", self._create_extrude_controls(), self._execute_extrude)
        group_layout.addWidget(extrude_frame)

        # Revolve tool
        revolve_frame = self._create_tool_frame("Revolve Profile", self._create_revolve_controls(), self._execute_revolve)
        group_layout.addWidget(revolve_frame)

        # Loft tool
        loft_frame = self._create_tool_frame("Loft Profiles", self._create_loft_controls(), self._execute_loft)
        group_layout.addWidget(loft_frame)

        # Sweep tool
        sweep_frame = self._create_tool_frame("Sweep Profile", self._create_sweep_controls(), self._execute_sweep)
        group_layout.addWidget(sweep_frame)

        # Helix tool
        helix_frame = self._create_tool_frame("Create Helix", self._create_helix_controls(), self._execute_helix)
        group_layout.addWidget(helix_frame)

        layout.addWidget(group)

    def _create_surface_section(self, layout):
        """Create surface modification tools section."""
        group = QtWidgets.QGroupBox("Surface Modification")
        group.setCheckable(True)
        group.setChecked(True)
        group_layout = QtWidgets.QVBoxLayout(group)

        # Fillet tool
        fillet_frame = self._create_tool_frame("Fillet Edges", self._create_fillet_controls(), self._execute_fillet)
        group_layout.addWidget(fillet_frame)

        # Chamfer tool
        chamfer_frame = self._create_tool_frame("Chamfer Edges", self._create_chamfer_controls(), self._execute_chamfer)
        group_layout.addWidget(chamfer_frame)

        # Draft tool
        draft_frame = self._create_tool_frame("Draft Faces", self._create_draft_controls(), self._execute_draft)
        group_layout.addWidget(draft_frame)

        # Thickness tool
        thickness_frame = self._create_tool_frame("Create Thickness", self._create_thickness_controls(), self._execute_thickness)
        group_layout.addWidget(thickness_frame)

        # Offset tool
        offset_frame = self._create_tool_frame("Offset Surface", self._create_offset_controls(), self._execute_offset)
        group_layout.addWidget(offset_frame)

        layout.addWidget(group)

    def _create_tool_frame(self, title, controls_widget, execute_callback):
        """Create a collapsible frame for a tool."""
        frame = QtWidgets.QFrame()
        frame.setFrameStyle(QtWidgets.QFrame.StyledPanel)
        frame_layout = QtWidgets.QVBoxLayout(frame)

        # Header with title and execute button
        header_layout = QtWidgets.QHBoxLayout()

        title_label = QtWidgets.QLabel(title)
        title_label.setStyleSheet("font-weight: bold; font-size: 12px;")
        header_layout.addWidget(title_label)

        header_layout.addStretch()

        execute_btn = QtWidgets.QPushButton("Execute")
        execute_btn.setStyleSheet("QPushButton { background-color: #4CAF50; color: white; font-weight: bold; padding: 6px 12px; }")
        execute_btn.clicked.connect(execute_callback)
        header_layout.addWidget(execute_btn)

        frame_layout.addLayout(header_layout)

        # Controls section
        frame_layout.addWidget(controls_widget)

        return frame

    def _create_status_section(self, layout):
        """Create status and progress section."""
        status_group = QtWidgets.QGroupBox("Status")
        status_layout = QtWidgets.QVBoxLayout(status_group)

        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setWordWrap(True)
        status_layout.addWidget(self.status_label)

        self.progress_bar = QtWidgets.QProgressBar()
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)

        layout.addWidget(status_group)

    # Advanced Primitives Controls
    def _create_tube_controls(self):
        """Create controls for tube creation."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        self.tube_outer_radius = QtWidgets.QDoubleSpinBox()
        self.tube_outer_radius.setRange(0.1, 1000.0)
        self.tube_outer_radius.setValue(10.0)
        self.tube_outer_radius.setSuffix(" mm")
        layout.addRow("Outer Radius:", self.tube_outer_radius)

        self.tube_inner_radius = QtWidgets.QDoubleSpinBox()
        self.tube_inner_radius.setRange(0.0, 999.0)
        self.tube_inner_radius.setValue(5.0)
        self.tube_inner_radius.setSuffix(" mm")
        layout.addRow("Inner Radius:", self.tube_inner_radius)

        self.tube_height = QtWidgets.QDoubleSpinBox()
        self.tube_height.setRange(0.1, 1000.0)
        self.tube_height.setValue(10.0)
        self.tube_height.setSuffix(" mm")
        layout.addRow("Height:", self.tube_height)

        self.tube_name = QtWidgets.QLineEdit()
        self.tube_name.setPlaceholderText("Optional object name")
        layout.addRow("Name:", self.tube_name)

        return widget

    def _create_prism_controls(self):
        """Create controls for prism creation."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        self.prism_sides = QtWidgets.QSpinBox()
        self.prism_sides.setRange(3, 20)
        self.prism_sides.setValue(6)
        layout.addRow("Sides:", self.prism_sides)

        self.prism_radius = QtWidgets.QDoubleSpinBox()
        self.prism_radius.setRange(0.1, 1000.0)
        self.prism_radius.setValue(5.0)
        self.prism_radius.setSuffix(" mm")
        layout.addRow("Radius:", self.prism_radius)

        self.prism_height = QtWidgets.QDoubleSpinBox()
        self.prism_height.setRange(0.1, 1000.0)
        self.prism_height.setValue(10.0)
        self.prism_height.setSuffix(" mm")
        layout.addRow("Height:", self.prism_height)

        self.prism_name = QtWidgets.QLineEdit()
        self.prism_name.setPlaceholderText("Optional object name")
        layout.addRow("Name:", self.prism_name)

        return widget

    def _create_wedge_controls(self):
        """Create controls for wedge creation."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        self.wedge_length = QtWidgets.QDoubleSpinBox()
        self.wedge_length.setRange(0.1, 1000.0)
        self.wedge_length.setValue(10.0)
        self.wedge_length.setSuffix(" mm")
        layout.addRow("Length:", self.wedge_length)

        self.wedge_width = QtWidgets.QDoubleSpinBox()
        self.wedge_width.setRange(0.1, 1000.0)
        self.wedge_width.setValue(10.0)
        self.wedge_width.setSuffix(" mm")
        layout.addRow("Width:", self.wedge_width)

        self.wedge_height = QtWidgets.QDoubleSpinBox()
        self.wedge_height.setRange(0.1, 1000.0)
        self.wedge_height.setValue(10.0)
        self.wedge_height.setSuffix(" mm")
        layout.addRow("Height:", self.wedge_height)

        self.wedge_angle = QtWidgets.QDoubleSpinBox()
        self.wedge_angle.setRange(1.0, 89.0)
        self.wedge_angle.setValue(45.0)
        self.wedge_angle.setSuffix("°")
        layout.addRow("Angle:", self.wedge_angle)

        self.wedge_name = QtWidgets.QLineEdit()
        self.wedge_name.setPlaceholderText("Optional object name")
        layout.addRow("Name:", self.wedge_name)

        return widget

    def _create_ellipsoid_controls(self):
        """Create controls for ellipsoid creation."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        self.ellipsoid_radius_x = QtWidgets.QDoubleSpinBox()
        self.ellipsoid_radius_x.setRange(0.1, 1000.0)
        self.ellipsoid_radius_x.setValue(5.0)
        self.ellipsoid_radius_x.setSuffix(" mm")
        layout.addRow("Radius X:", self.ellipsoid_radius_x)

        self.ellipsoid_radius_y = QtWidgets.QDoubleSpinBox()
        self.ellipsoid_radius_y.setRange(0.1, 1000.0)
        self.ellipsoid_radius_y.setValue(3.0)
        self.ellipsoid_radius_y.setSuffix(" mm")
        layout.addRow("Radius Y:", self.ellipsoid_radius_y)

        self.ellipsoid_radius_z = QtWidgets.QDoubleSpinBox()
        self.ellipsoid_radius_z.setRange(0.1, 1000.0)
        self.ellipsoid_radius_z.setValue(4.0)
        self.ellipsoid_radius_z.setSuffix(" mm")
        layout.addRow("Radius Z:", self.ellipsoid_radius_z)

        self.ellipsoid_name = QtWidgets.QLineEdit()
        self.ellipsoid_name.setPlaceholderText("Optional object name")
        layout.addRow("Name:", self.ellipsoid_name)

        return widget

    # Advanced Operations Controls
    def _create_extrude_controls(self):
        """Create controls for extrude operation."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        self.extrude_profile = QtWidgets.QLineEdit()
        self.extrude_profile.setPlaceholderText("Profile object name")
        layout.addRow("Profile:", self.extrude_profile)

        self.extrude_distance = QtWidgets.QDoubleSpinBox()
        self.extrude_distance.setRange(0.1, 1000.0)
        self.extrude_distance.setValue(10.0)
        self.extrude_distance.setSuffix(" mm")
        layout.addRow("Distance:", self.extrude_distance)

        # Direction controls
        dir_widget = QtWidgets.QWidget()
        dir_layout = QtWidgets.QHBoxLayout(dir_widget)
        dir_layout.setContentsMargins(0, 0, 0, 0)

        self.extrude_dir_x = QtWidgets.QDoubleSpinBox()
        self.extrude_dir_x.setRange(-1.0, 1.0)
        self.extrude_dir_x.setValue(0.0)
        self.extrude_dir_x.setSingleStep(0.1)
        dir_layout.addWidget(QtWidgets.QLabel("X:"))
        dir_layout.addWidget(self.extrude_dir_x)

        self.extrude_dir_y = QtWidgets.QDoubleSpinBox()
        self.extrude_dir_y.setRange(-1.0, 1.0)
        self.extrude_dir_y.setValue(0.0)
        self.extrude_dir_y.setSingleStep(0.1)
        dir_layout.addWidget(QtWidgets.QLabel("Y:"))
        dir_layout.addWidget(self.extrude_dir_y)

        self.extrude_dir_z = QtWidgets.QDoubleSpinBox()
        self.extrude_dir_z.setRange(-1.0, 1.0)
        self.extrude_dir_z.setValue(1.0)
        self.extrude_dir_z.setSingleStep(0.1)
        dir_layout.addWidget(QtWidgets.QLabel("Z:"))
        dir_layout.addWidget(self.extrude_dir_z)

        layout.addRow("Direction:", dir_widget)

        self.extrude_name = QtWidgets.QLineEdit()
        self.extrude_name.setPlaceholderText("Optional object name")
        layout.addRow("Name:", self.extrude_name)

        return widget

    def _create_revolve_controls(self):
        """Create controls for revolve operation."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        self.revolve_profile = QtWidgets.QLineEdit()
        self.revolve_profile.setPlaceholderText("Profile object name")
        layout.addRow("Profile:", self.revolve_profile)

        self.revolve_angle = QtWidgets.QDoubleSpinBox()
        self.revolve_angle.setRange(1.0, 360.0)
        self.revolve_angle.setValue(360.0)
        self.revolve_angle.setSuffix("°")
        layout.addRow("Angle:", self.revolve_angle)

        self.revolve_name = QtWidgets.QLineEdit()
        self.revolve_name.setPlaceholderText("Optional object name")
        layout.addRow("Name:", self.revolve_name)

        return widget

    def _create_loft_controls(self):
        """Create controls for loft operation."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        self.loft_profiles = QtWidgets.QTextEdit()
        self.loft_profiles.setMaximumHeight(60)
        self.loft_profiles.setPlaceholderText("Profile names (one per line)")
        layout.addRow("Profiles:", self.loft_profiles)

        self.loft_solid = QtWidgets.QCheckBox("Create solid")
        self.loft_solid.setChecked(True)
        layout.addRow("", self.loft_solid)

        self.loft_ruled = QtWidgets.QCheckBox("Ruled surface")
        layout.addRow("", self.loft_ruled)

        self.loft_name = QtWidgets.QLineEdit()
        self.loft_name.setPlaceholderText("Optional object name")
        layout.addRow("Name:", self.loft_name)

        return widget

    def _create_sweep_controls(self):
        """Create controls for sweep operation."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        self.sweep_profile = QtWidgets.QLineEdit()
        self.sweep_profile.setPlaceholderText("Profile object name")
        layout.addRow("Profile:", self.sweep_profile)

        self.sweep_path = QtWidgets.QLineEdit()
        self.sweep_path.setPlaceholderText("Path object name")
        layout.addRow("Path:", self.sweep_path)

        self.sweep_frenet = QtWidgets.QCheckBox("Use Frenet frame")
        layout.addRow("", self.sweep_frenet)

        self.sweep_name = QtWidgets.QLineEdit()
        self.sweep_name.setPlaceholderText("Optional object name")
        layout.addRow("Name:", self.sweep_name)

        return widget

    def _create_helix_controls(self):
        """Create controls for helix creation."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        self.helix_radius = QtWidgets.QDoubleSpinBox()
        self.helix_radius.setRange(0.1, 1000.0)
        self.helix_radius.setValue(5.0)
        self.helix_radius.setSuffix(" mm")
        layout.addRow("Radius:", self.helix_radius)

        self.helix_pitch = QtWidgets.QDoubleSpinBox()
        self.helix_pitch.setRange(0.1, 100.0)
        self.helix_pitch.setValue(2.0)
        self.helix_pitch.setSuffix(" mm")
        layout.addRow("Pitch:", self.helix_pitch)

        self.helix_height = QtWidgets.QDoubleSpinBox()
        self.helix_height.setRange(0.1, 1000.0)
        self.helix_height.setValue(20.0)
        self.helix_height.setSuffix(" mm")
        layout.addRow("Height:", self.helix_height)

        self.helix_direction = QtWidgets.QComboBox()
        self.helix_direction.addItems(["right", "left"])
        layout.addRow("Direction:", self.helix_direction)

        self.helix_name = QtWidgets.QLineEdit()
        self.helix_name.setPlaceholderText("Optional object name")
        layout.addRow("Name:", self.helix_name)

        return widget

    # Surface Modification Controls
    def _create_fillet_controls(self):
        """Create controls for fillet operation."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        self.fillet_object = QtWidgets.QLineEdit()
        self.fillet_object.setPlaceholderText("Object name")
        layout.addRow("Object:", self.fillet_object)

        self.fillet_edges = QtWidgets.QLineEdit()
        self.fillet_edges.setPlaceholderText("Edge indices (e.g., 0,1,2)")
        layout.addRow("Edge Indices:", self.fillet_edges)

        self.fillet_radius = QtWidgets.QDoubleSpinBox()
        self.fillet_radius.setRange(0.1, 100.0)
        self.fillet_radius.setValue(1.0)
        self.fillet_radius.setSuffix(" mm")
        layout.addRow("Radius:", self.fillet_radius)

        self.fillet_name = QtWidgets.QLineEdit()
        self.fillet_name.setPlaceholderText("Optional object name")
        layout.addRow("Name:", self.fillet_name)

        return widget

    def _create_chamfer_controls(self):
        """Create controls for chamfer operation."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        self.chamfer_object = QtWidgets.QLineEdit()
        self.chamfer_object.setPlaceholderText("Object name")
        layout.addRow("Object:", self.chamfer_object)

        self.chamfer_edges = QtWidgets.QLineEdit()
        self.chamfer_edges.setPlaceholderText("Edge indices (e.g., 0,1,2)")
        layout.addRow("Edge Indices:", self.chamfer_edges)

        self.chamfer_distance = QtWidgets.QDoubleSpinBox()
        self.chamfer_distance.setRange(0.1, 100.0)
        self.chamfer_distance.setValue(1.0)
        self.chamfer_distance.setSuffix(" mm")
        layout.addRow("Distance:", self.chamfer_distance)

        self.chamfer_name = QtWidgets.QLineEdit()
        self.chamfer_name.setPlaceholderText("Optional object name")
        layout.addRow("Name:", self.chamfer_name)

        return widget

    def _create_draft_controls(self):
        """Create controls for draft operation."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        self.draft_object = QtWidgets.QLineEdit()
        self.draft_object.setPlaceholderText("Object name")
        layout.addRow("Object:", self.draft_object)

        self.draft_faces = QtWidgets.QLineEdit()
        self.draft_faces.setPlaceholderText("Face indices (e.g., 0,1,2)")
        layout.addRow("Face Indices:", self.draft_faces)

        self.draft_angle = QtWidgets.QDoubleSpinBox()
        self.draft_angle.setRange(0.1, 45.0)
        self.draft_angle.setValue(5.0)
        self.draft_angle.setSuffix("°")
        layout.addRow("Angle:", self.draft_angle)

        self.draft_name = QtWidgets.QLineEdit()
        self.draft_name.setPlaceholderText("Optional object name")
        layout.addRow("Name:", self.draft_name)

        return widget

    def _create_thickness_controls(self):
        """Create controls for thickness operation."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        self.thickness_object = QtWidgets.QLineEdit()
        self.thickness_object.setPlaceholderText("Object name")
        layout.addRow("Object:", self.thickness_object)

        self.thickness_value = QtWidgets.QDoubleSpinBox()
        self.thickness_value.setRange(0.1, 100.0)
        self.thickness_value.setValue(1.0)
        self.thickness_value.setSuffix(" mm")
        layout.addRow("Thickness:", self.thickness_value)

        self.thickness_faces = QtWidgets.QLineEdit()
        self.thickness_faces.setPlaceholderText("Face indices to remove (optional)")
        layout.addRow("Remove Faces:", self.thickness_faces)

        self.thickness_name = QtWidgets.QLineEdit()
        self.thickness_name.setPlaceholderText("Optional object name")
        layout.addRow("Name:", self.thickness_name)

        return widget

    def _create_offset_controls(self):
        """Create controls for offset operation."""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QFormLayout(widget)

        self.offset_object = QtWidgets.QLineEdit()
        self.offset_object.setPlaceholderText("Object name")
        layout.addRow("Object:", self.offset_object)

        self.offset_distance = QtWidgets.QDoubleSpinBox()
        self.offset_distance.setRange(-100.0, 100.0)
        self.offset_distance.setValue(1.0)
        self.offset_distance.setSuffix(" mm")
        layout.addRow("Distance:", self.offset_distance)

        self.offset_name = QtWidgets.QLineEdit()
        self.offset_name.setPlaceholderText("Optional object name")
        layout.addRow("Name:", self.offset_name)

        return widget

    # Tool execution methods
    def _execute_tool(self, tool_name, method_name, parameters):
        """Execute a tool method with parameters."""
        if tool_name not in self.tools:
            self._show_error(f"Tool {tool_name} not available")
            return

        try:
            self._show_progress(f"Executing {method_name}...", 0)
            tool = self.tools[tool_name]
            method = getattr(tool, method_name)

            result = method(**parameters)

            if result.get("success", False):
                self._show_success(result.get("message", "Operation completed"))
                self.tool_executed.emit(tool_name, parameters, result)
            else:
                self._show_error(result.get("error", "Operation failed"))

            self._hide_progress()

        except Exception as e:
            self._show_error(f"Error executing {method_name}: {str(e)}")
            self._hide_progress()

    def _parse_indices(self, text):
        """Parse comma-separated indices."""
        if not text.strip():
            return []
        try:
            return [int(x.strip()) for x in text.split(',') if x.strip()]
        except ValueError:
            raise ValueError("Invalid indices format. Use comma-separated integers (e.g., 0,1,2)")

    # Advanced Primitives execution methods
    def _execute_tube(self):
        """Execute tube creation."""
        parameters = {
            "outer_radius": self.tube_outer_radius.value(),
            "inner_radius": self.tube_inner_radius.value(),
            "height": self.tube_height.value(),
            "name": self.tube_name.text() or None
        }
        self._execute_tool("advanced_primitives", "create_tube", parameters)

    def _execute_prism(self):
        """Execute prism creation."""
        parameters = {
            "sides": self.prism_sides.value(),
            "radius": self.prism_radius.value(),
            "height": self.prism_height.value(),
            "name": self.prism_name.text() or None
        }
        self._execute_tool("advanced_primitives", "create_prism", parameters)

    def _execute_wedge(self):
        """Execute wedge creation."""
        parameters = {
            "length": self.wedge_length.value(),
            "width": self.wedge_width.value(),
            "height": self.wedge_height.value(),
            "angle": self.wedge_angle.value(),
            "name": self.wedge_name.text() or None
        }
        self._execute_tool("advanced_primitives", "create_wedge", parameters)

    def _execute_ellipsoid(self):
        """Execute ellipsoid creation."""
        parameters = {
            "radius_x": self.ellipsoid_radius_x.value(),
            "radius_y": self.ellipsoid_radius_y.value(),
            "radius_z": self.ellipsoid_radius_z.value(),
            "name": self.ellipsoid_name.text() or None
        }
        self._execute_tool("advanced_primitives", "create_ellipsoid", parameters)

    # Advanced Operations execution methods
    def _execute_extrude(self):
        """Execute extrude operation."""
        if not self.extrude_profile.text():
            self._show_error("Profile name is required")
            return

        parameters = {
            "profile_name": self.extrude_profile.text(),
            "direction": (self.extrude_dir_x.value(), self.extrude_dir_y.value(), self.extrude_dir_z.value()),
            "distance": self.extrude_distance.value(),
            "name": self.extrude_name.text() or None
        }
        self._execute_tool("advanced_operations", "extrude_profile", parameters)

    def _execute_revolve(self):
        """Execute revolve operation."""
        if not self.revolve_profile.text():
            self._show_error("Profile name is required")
            return

        parameters = {
            "profile_name": self.revolve_profile.text(),
            "angle": self.revolve_angle.value(),
            "name": self.revolve_name.text() or None
        }
        self._execute_tool("advanced_operations", "revolve_profile", parameters)

    def _execute_loft(self):
        """Execute loft operation."""
        profiles_text = self.loft_profiles.toPlainText().strip()
        if not profiles_text:
            self._show_error("Profile names are required")
            return

        profile_names = [line.strip() for line in profiles_text.split('\n') if line.strip()]

        parameters = {
            "profile_names": profile_names,
            "solid": self.loft_solid.isChecked(),
            "ruled": self.loft_ruled.isChecked(),
            "name": self.loft_name.text() or None
        }
        self._execute_tool("advanced_operations", "loft_profiles", parameters)

    def _execute_sweep(self):
        """Execute sweep operation."""
        if not self.sweep_profile.text() or not self.sweep_path.text():
            self._show_error("Profile and path names are required")
            return

        parameters = {
            "profile_name": self.sweep_profile.text(),
            "path_name": self.sweep_path.text(),
            "frenet": self.sweep_frenet.isChecked(),
            "name": self.sweep_name.text() or None
        }
        self._execute_tool("advanced_operations", "sweep_profile", parameters)

    def _execute_helix(self):
        """Execute helix creation."""
        parameters = {
            "radius": self.helix_radius.value(),
            "pitch": self.helix_pitch.value(),
            "height": self.helix_height.value(),
            "direction": self.helix_direction.currentText(),
            "name": self.helix_name.text() or None
        }
        self._execute_tool("advanced_operations", "create_helix", parameters)

    # Surface Modification execution methods
    def _execute_fillet(self):
        """Execute fillet operation."""
        if not self.fillet_object.text() or not self.fillet_edges.text():
            self._show_error("Object name and edge indices are required")
            return

        try:
            edge_indices = self._parse_indices(self.fillet_edges.text())
            parameters = {
                "object_name": self.fillet_object.text(),
                "edge_indices": edge_indices,
                "radius": self.fillet_radius.value(),
                "name": self.fillet_name.text() or None
            }
            self._execute_tool("surface_modification", "fillet_edges", parameters)
        except ValueError as e:
            self._show_error(str(e))

    def _execute_chamfer(self):
        """Execute chamfer operation."""
        if not self.chamfer_object.text() or not self.chamfer_edges.text():
            self._show_error("Object name and edge indices are required")
            return

        try:
            edge_indices = self._parse_indices(self.chamfer_edges.text())
            parameters = {
                "object_name": self.chamfer_object.text(),
                "edge_indices": edge_indices,
                "distance": self.chamfer_distance.value(),
                "name": self.chamfer_name.text() or None
            }
            self._execute_tool("surface_modification", "chamfer_edges", parameters)
        except ValueError as e:
            self._show_error(str(e))

    def _execute_draft(self):
        """Execute draft operation."""
        if not self.draft_object.text() or not self.draft_faces.text():
            self._show_error("Object name and face indices are required")
            return

        try:
            face_indices = self._parse_indices(self.draft_faces.text())
            parameters = {
                "object_name": self.draft_object.text(),
                "face_indices": face_indices,
                "angle": self.draft_angle.value(),
                "name": self.draft_name.text() or None
            }
            self._execute_tool("surface_modification", "draft_faces", parameters)
        except ValueError as e:
            self._show_error(str(e))

    def _execute_thickness(self):
        """Execute thickness operation."""
        if not self.thickness_object.text():
            self._show_error("Object name is required")
            return

        try:
            face_indices = None
            if self.thickness_faces.text().strip():
                face_indices = self._parse_indices(self.thickness_faces.text())

            parameters = {
                "object_name": self.thickness_object.text(),
                "thickness": self.thickness_value.value(),
                "face_indices": face_indices,
                "name": self.thickness_name.text() or None
            }
            self._execute_tool("surface_modification", "create_thickness", parameters)
        except ValueError as e:
            self._show_error(str(e))

    def _execute_offset(self):
        """Execute offset operation."""
        if not self.offset_object.text():
            self._show_error("Object name is required")
            return

        parameters = {
            "object_name": self.offset_object.text(),
            "distance": self.offset_distance.value(),
            "name": self.offset_name.text() or None
        }
        self._execute_tool("surface_modification", "offset_surface", parameters)

    # Status and progress methods
    def _show_progress(self, message, percentage):
        """Show progress with message."""
        self.status_label.setText(message)
        self.progress_bar.setValue(percentage)
        self.progress_bar.setVisible(True)
        self.tool_progress.emit(message, percentage)

    def _hide_progress(self):
        """Hide progress bar."""
        self.progress_bar.setVisible(False)

    def _show_success(self, message):
        """Show success message."""
        self.status_label.setText(f"✓ {message}")
        self.status_label.setStyleSheet("color: green;")

    def _show_error(self, message):
        """Show error message."""
        self.status_label.setText(f"✗ {message}")
        self.status_label.setStyleSheet("color: red;")
        QtWidgets.QMessageBox.warning(self, "Tool Error", message)
