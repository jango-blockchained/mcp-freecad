"""Compact Tools Widget - Clean and organized GUI for all FreeCAD tools"""

import os
import sys

# Ensure the addon directory is in the Python path
addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

import logging
from typing import Any, Dict, List, Optional

import FreeCAD
from PySide2 import QtCore, QtGui, QtWidgets


class CompactToolButton(QtWidgets.QPushButton):
    """Ultra-compact tool button with icon."""

    def __init__(self, icon, text, tooltip, parent=None):
        super().__init__(parent)
        self.setText(icon)
        self.setToolTip(f"<b>{text}</b><br>{tooltip}")
        self.setFixedSize(40, 30)  # Even smaller
        self.setStyleSheet(
            """
            QPushButton {
                font-size: 14px;
                border: 1px solid #ddd;
                border-radius: 4px;
                background-color: #fff;
                margin: 1px;
            }
            QPushButton:hover {
                background-color: #e3f2fd;
                border: 1px solid #2196F3;
            }
            QPushButton:pressed {
                background-color: #bbdefb;
            }
        """
        )


class CollapsibleCategory(QtWidgets.QWidget):
    """Collapsible category with header button."""

    def __init__(self, title, icon="", parent=None):
        super().__init__(parent)
        self.is_collapsed = False

        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header button
        self.header_btn = QtWidgets.QPushButton(f"{icon} {title} ▼")
        self.header_btn.setCheckable(True)
        self.header_btn.setChecked(True)
        self.header_btn.setStyleSheet(
            """
            QPushButton {
                text-align: left;
                padding: 5px 10px;
                border: none;
                background-color: #f5f5f5;
                font-weight: bold;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QPushButton:checked {
                background-color: #e3f2fd;
            }
        """
        )
        self.header_btn.clicked.connect(self._toggle_collapse)
        layout.addWidget(self.header_btn)

        # Content widget
        self.content_widget = QtWidgets.QWidget()
        self.content_layout = QtWidgets.QGridLayout(self.content_widget)
        self.content_layout.setContentsMargins(5, 5, 5, 5)
        self.content_layout.setSpacing(2)
        layout.addWidget(self.content_widget)

        self.title = title
        self.icon = icon

    def _toggle_collapse(self):
        """Toggle collapsed state."""
        self.is_collapsed = not self.is_collapsed
        self.content_widget.setVisible(not self.is_collapsed)
        arrow = "▶" if self.is_collapsed else "▼"
        self.header_btn.setText(f"{self.icon} {self.title} {arrow}")

    def add_button(self, button, row, col):
        """Add button to grid."""
        self.content_layout.addWidget(button, row, col)


class ToolsWidget(QtWidgets.QWidget):
    """Ultra-compact tools widget with icons."""

    tool_executed = QtCore.Signal(str, dict, dict)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = logging.getLogger(__name__)
        self.tools = {}
        self.current_tool_dialog = None
        self._setup_tools()
        self._setup_ui()

    def _setup_tools(self):
        """Setup all tool instances."""
        try:
            # Try absolute imports first
            try:
                from tools.advanced_operations import AdvancedOperationsTool
                from tools.advanced_primitives import AdvancedPrimitivesTool
                from tools.export_import import ExportImportTool
                from tools.measurements import MeasurementsTool
                from tools.operations import OperationsTool
                from tools.primitives import PrimitivesTool
                from tools.surface_modification import SurfaceModificationTool
            except ImportError:
                # Try relative imports
                from ..tools.advanced_operations import AdvancedOperationsTool
                from ..tools.advanced_primitives import AdvancedPrimitivesTool
                from ..tools.export_import import ExportImportTool
                from ..tools.measurements import MeasurementsTool
                from ..tools.operations import OperationsTool
                from ..tools.primitives import PrimitivesTool
                from ..tools.surface_modification import SurfaceModificationTool

            self.tools = {
                "primitives": PrimitivesTool(),
                "operations": OperationsTool(),
                "measurements": MeasurementsTool(),
                "export_import": ExportImportTool(),
                "advanced_primitives": AdvancedPrimitivesTool(),
                "advanced_operations": AdvancedOperationsTool(),
                "surface_modification": SurfaceModificationTool(),
            }
            self.logger.info("All tools loaded successfully")
        except ImportError as e:
            self.logger.error(f"Failed to import some tools: {e}")
            # Try to load basic tools only
            try:
                try:
                    from tools.export_import import ExportImportTool
                    from tools.measurements import MeasurementsTool
                    from tools.operations import OperationsTool
                    from tools.primitives import PrimitivesTool
                except ImportError:
                    from ..tools.export_import import ExportImportTool
                    from ..tools.measurements import MeasurementsTool
                    from ..tools.operations import OperationsTool
                    from ..tools.primitives import PrimitivesTool

                self.tools = {
                    "primitives": PrimitivesTool(),
                    "operations": OperationsTool(),
                    "measurements": MeasurementsTool(),
                    "export_import": ExportImportTool(),
                }
                self.logger.warning("Only basic tools loaded")
            except Exception as e2:
                self.tools = {}
                self.logger.error(f"No tools could be loaded: {e2}")

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(2)
        layout.setContentsMargins(2, 2, 2, 2)

        # Minimal header
        header_layout = QtWidgets.QHBoxLayout()
        header_label = QtWidgets.QLabel("🛠️ Tools")
        header_label.setStyleSheet("font-size: 14px; font-weight: bold;")
        header_layout.addWidget(header_label)

        # Search box
        self.search_box = QtWidgets.QLineEdit()
        self.search_box.setPlaceholderText("Search tools...")
        self.search_box.setMaximumWidth(150)
        self.search_box.setStyleSheet(
            """
            QLineEdit {
                padding: 3px 8px;
                border: 1px solid #ddd;
                border-radius: 12px;
                font-size: 11px;
            }
        """
        )
        header_layout.addStretch()
        header_layout.addWidget(self.search_box)

        layout.addLayout(header_layout)

        # Create scroll area
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)
        scroll.setVerticalScrollBarPolicy(QtCore.Qt.ScrollBarAsNeeded)
        scroll.setStyleSheet("QScrollArea { border: none; }")

        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(2)
        scroll_layout.setContentsMargins(0, 0, 0, 0)

        # Tool categories with icons
        self._create_basic_primitives(scroll_layout)
        self._create_basic_operations(scroll_layout)
        self._create_measurements(scroll_layout)
        self._create_import_export(scroll_layout)

        if "advanced_primitives" in self.tools:
            self._create_advanced_primitives(scroll_layout)
        if "advanced_operations" in self.tools:
            self._create_advanced_operations(scroll_layout)
        if "surface_modification" in self.tools:
            self._create_surface_modification(scroll_layout)

        scroll_layout.addStretch()
        scroll.setWidget(scroll_widget)
        layout.addWidget(scroll)

        # Ultra-compact status
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet(
            "padding: 2px 8px; background-color: #f0f0f0; border-radius: 10px; font-size: 10px;"
        )
        layout.addWidget(self.status_label)

    def _create_basic_primitives(self, layout):
        """Create basic primitives section."""
        category = CollapsibleCategory("Basic Shapes", "□")

        tools = [
            ("□", "Box", "Create a box/cube", "create_box"),
            ("○", "Cylinder", "Create a cylinder", "create_cylinder"),
            ("●", "Sphere", "Create a sphere", "create_sphere"),
            ("△", "Cone", "Create a cone", "create_cone"),
            ("◯", "Torus", "Create a torus", "create_torus"),
            ("▬", "Plane", "Create a plane", "create_plane"),
        ]

        def create_handler(method_name):
            return lambda checked: self._execute_tool("primitives", method_name)

        for i, (icon, name, tooltip, method) in enumerate(tools):
            btn = CompactToolButton(icon, name, tooltip)
            btn.clicked.connect(create_handler(method))
            category.add_button(btn, i // 6, i % 6)

        layout.addWidget(category)

    def _create_basic_operations(self, layout):
        """Create basic operations section."""
        category = CollapsibleCategory("Operations", "⚙")

        tools = [
            ("∪", "Union", "Boolean union", "boolean_union"),
            ("−", "Cut", "Boolean cut", "boolean_cut"),
            ("∩", "Intersect", "Boolean intersection", "boolean_intersection"),
            ("→", "Move", "Move object", "move_object"),
            ("↻", "Rotate", "Rotate object", "rotate_object"),
            ("⤢", "Scale", "Scale object", "scale_object"),
            ("⟷", "Mirror", "Mirror object", "mirror_object"),
            ("⋮⋮", "Array", "Create array", "create_array"),
        ]

        def create_handler(method_name):
            return lambda checked: self._execute_tool("operations", method_name)

        for i, (icon, name, tooltip, method) in enumerate(tools):
            btn = CompactToolButton(icon, name, tooltip)
            btn.clicked.connect(create_handler(method))
            category.add_button(btn, i // 6, i % 6)

        layout.addWidget(category)

    def _create_measurements(self, layout):
        """Create measurements section."""
        category = CollapsibleCategory("Measure", "📏")

        tools = [
            ("↔", "Distance", "Measure distance", "measure_distance"),
            ("∠", "Angle", "Measure angle", "measure_angle"),
            ("³", "Volume", "Measure volume", "measure_volume"),
            ("²", "Area", "Measure area", "measure_area"),
            ("━", "Length", "Measure length", "measure_length"),
            ("⌀", "Radius", "Measure radius", "measure_radius"),
            ("▭", "BBox", "Bounding box", "measure_bounding_box"),
            ("⊕", "CoG", "Center of gravity", "measure_center_of_gravity"),
        ]

        def create_handler(method_name):
            return lambda checked: self._execute_tool("measurements", method_name)

        for i, (icon, name, tooltip, method) in enumerate(tools):
            btn = CompactToolButton(icon, name, tooltip)
            btn.clicked.connect(create_handler(method))
            category.add_button(btn, i // 6, i % 6)

        layout.addWidget(category)

    def _create_import_export(self, layout):
        """Create import/export section."""
        category = CollapsibleCategory("Import/Export", "📁")

        tools = [
            ("▼S", "Import STL", "Import STL", "import_stl"),
            ("▲S", "Export STL", "Export STL", "export_stl"),
            ("▼P", "Import STEP", "Import STEP", "import_step"),
            ("▲P", "Export STEP", "Export STEP", "export_step"),
            ("▼I", "Import IGES", "Import IGES", "import_iges"),
            ("▲I", "Export IGES", "Export IGES", "export_iges"),
            ("▼O", "Import OBJ", "Import OBJ", "import_obj"),
            ("▲O", "Export OBJ", "Export OBJ", "export_obj"),
        ]

        def create_handler(method_name):
            return lambda checked: self._execute_tool("export_import", method_name)

        for i, (icon, name, tooltip, method) in enumerate(tools):
            btn = CompactToolButton(icon, name, tooltip)
            btn.clicked.connect(create_handler(method))
            category.add_button(btn, i // 6, i % 6)

        layout.addWidget(category)

    def _create_advanced_primitives(self, layout):
        """Create advanced primitives section."""
        category = CollapsibleCategory("Advanced Shapes", "◈")

        tools = [
            ("◎", "Tube", "Hollow cylinder", "create_tube"),
            ("⬟", "Prism", "N-sided prism", "create_prism"),
            ("◢", "Wedge", "Wedge shape", "create_wedge"),
            ("⬭", "Ellipsoid", "Ellipsoid", "create_ellipsoid"),
            ("∿", "Spring", "Spring/helix", "create_spring"),
            ("⚙", "Gear", "Create gear", "create_gear"),
            ("⟳", "Thread", "Create thread", "create_thread"),
            ("A", "Text", "3D text", "create_text"),
        ]

        def create_handler(method_name):
            return lambda checked: self._execute_tool(
                "advanced_primitives", method_name
            )

        for i, (icon, name, tooltip, method) in enumerate(tools):
            btn = CompactToolButton(icon, name, tooltip)
            btn.clicked.connect(create_handler(method))
            category.add_button(btn, i // 6, i % 6)

        layout.addWidget(category)

    def _create_advanced_operations(self, layout):
        """Create advanced operations section."""
        category = CollapsibleCategory("Advanced Ops", "⚡")

        tools = [
            ("⬆", "Extrude", "Extrude profile", "extrude_profile"),
            ("⟲", "Revolve", "Revolve profile", "revolve_profile"),
            ("⌒", "Loft", "Loft profiles", "loft_profiles"),
            ("⟿", "Sweep", "Sweep along path", "sweep_profile"),
            ("⟳", "Helix", "Create helix", "create_helix"),
            ("⋮⋮", "Pattern", "Create pattern", "create_pattern"),
            ("⊼", "Project", "Project to surface", "project_to_surface"),
            ("⊕", "Wrap", "Wrap to surface", "wrap_to_surface"),
        ]

        def create_handler(method_name):
            return lambda checked: self._execute_tool(
                "advanced_operations", method_name
            )

        for i, (icon, name, tooltip, method) in enumerate(tools):
            btn = CompactToolButton(icon, name, tooltip)
            btn.clicked.connect(create_handler(method))
            category.add_button(btn, i // 6, i % 6)

        layout.addWidget(category)

    def _create_surface_modification(self, layout):
        """Create surface modification section."""
        category = CollapsibleCategory("Surface Mods", "✨")

        tools = [
            ("╭", "Fillet", "Round edges", "fillet_edges"),
            ("╱", "Chamfer", "Chamfer edges", "chamfer_edges"),
            ("◣", "Draft", "Draft angle", "draft_faces"),
            ("⬚", "Shell", "Shell/hollow", "create_thickness"),
            ("⟷", "Offset", "Offset surface", "offset_surface"),
            ("∼", "Blend", "Blend surfaces", "blend_surfaces"),
            ("◫", "Patch", "Create patch", "create_patch"),
            ("≈", "Simplify", "Simplify shape", "simplify_shape"),
        ]

        def create_handler(method_name):
            return lambda checked: self._execute_tool(
                "surface_modification", method_name
            )

        for i, (icon, name, tooltip, method) in enumerate(tools):
            btn = CompactToolButton(icon, name, tooltip)
            btn.clicked.connect(create_handler(method))
            category.add_button(btn, i // 6, i % 6)

        layout.addWidget(category)

    def _execute_tool(self, category, method):
        """Execute a tool with parameter dialog."""
        if category not in self.tools:
            self.status_label.setText(f"❌ {category} not available")
            self.status_label.setStyleSheet(
                "padding: 2px 8px; background-color: #ffcdd2; border-radius: 10px; font-size: 10px;"
            )
            return

        tool = self.tools[category]
        if not hasattr(tool, method):
            self.status_label.setText(f"❌ {method} not found")
            self.status_label.setStyleSheet(
                "padding: 2px 8px; background-color: #ffcdd2; border-radius: 10px; font-size: 10px;"
            )
            return

        # Create parameter dialog
        dialog = ToolParameterDialog(category, method, self)
        if dialog.exec_():
            params = dialog.get_parameters()

            try:
                # Execute the tool
                result = getattr(tool, method)(**params)

                # Update status
                if result.get("success"):
                    self.status_label.setText(f"✅ {result.get('message', 'Success')}")
                    self.status_label.setStyleSheet(
                        "padding: 2px 8px; background-color: #c8e6c9; border-radius: 10px; font-size: 10px;"
                    )
                else:
                    self.status_label.setText(f"❌ {result.get('message', 'Failed')}")
                    self.status_label.setStyleSheet(
                        "padding: 2px 8px; background-color: #ffcdd2; border-radius: 10px; font-size: 10px;"
                    )

                # Emit signal
                self.tool_executed.emit(f"{category}.{method}", params, result)

            except Exception as e:
                self.logger.error(f"Error executing {category}.{method}: {e}")
                self.status_label.setText(f"❌ Error: {str(e)[:30]}...")
                self.status_label.setStyleSheet(
                    "padding: 2px 8px; background-color: #ffcdd2; border-radius: 10px; font-size: 10px;"
                )


class ToolParameterDialog(QtWidgets.QDialog):
    """Compact dialog for tool parameters."""

    # Parameter configurations for all tools
    PARAM_CONFIGS = {
        # Basic Primitives
        "primitives.create_box": [
            ("length", "float", 10.0, "Length", "mm"),
            ("width", "float", 10.0, "Width", "mm"),
            ("height", "float", 10.0, "Height", "mm"),
            ("name", "string", "", "Name (optional)", ""),
        ],
        "primitives.create_cylinder": [
            ("radius", "float", 5.0, "Radius", "mm"),
            ("height", "float", 10.0, "Height", "mm"),
            ("name", "string", "", "Name (optional)", ""),
        ],
        "primitives.create_sphere": [
            ("radius", "float", 5.0, "Radius", "mm"),
            ("name", "string", "", "Name (optional)", ""),
        ],
        "primitives.create_cone": [
            ("radius1", "float", 5.0, "Bottom Radius", "mm"),
            ("radius2", "float", 0.0, "Top Radius", "mm"),
            ("height", "float", 10.0, "Height", "mm"),
            ("name", "string", "", "Name (optional)", ""),
        ],
        "primitives.create_torus": [
            ("radius1", "float", 10.0, "Major Radius", "mm"),
            ("radius2", "float", 2.0, "Minor Radius", "mm"),
            ("name", "string", "", "Name (optional)", ""),
        ],
        "primitives.create_plane": [
            ("length", "float", 10.0, "Length", "mm"),
            ("width", "float", 10.0, "Width", "mm"),
            ("name", "string", "", "Name (optional)", ""),
        ],
        # Basic Operations
        "operations.boolean_union": [
            ("obj1_name", "object", "", "First Object", ""),
            ("obj2_name", "object", "", "Second Object", ""),
            ("keep_originals", "bool", False, "Keep Originals", ""),
        ],
        "operations.boolean_cut": [
            ("obj1_name", "object", "", "Base Object", ""),
            ("obj2_name", "object", "", "Tool Object", ""),
            ("keep_originals", "bool", False, "Keep Originals", ""),
        ],
        "operations.boolean_intersection": [
            ("obj1_name", "object", "", "First Object", ""),
            ("obj2_name", "object", "", "Second Object", ""),
            ("keep_originals", "bool", False, "Keep Originals", ""),
        ],
        "operations.move_object": [
            ("obj_name", "object", "", "Object", ""),
            ("x", "float", 0.0, "X", "mm"),
            ("y", "float", 0.0, "Y", "mm"),
            ("z", "float", 0.0, "Z", "mm"),
            ("relative", "bool", True, "Relative", ""),
        ],
        "operations.rotate_object": [
            ("obj_name", "object", "", "Object", ""),
            ("angle", "float", 90.0, "Angle", "°"),
            ("axis", "choice", "z", "Axis", ["x", "y", "z"]),
            ("center", "point", "", "Center (optional)", ""),
        ],
        "operations.scale_object": [
            ("obj_name", "object", "", "Object", ""),
            ("scale_x", "float", 1.0, "Scale X", ""),
            ("scale_y", "float", 1.0, "Scale Y", ""),
            ("scale_z", "float", 1.0, "Scale Z", ""),
        ],
        # Measurements
        "measurements.measure_distance": [
            ("point1", "point", "", "First Point/Object", ""),
            ("point2", "point", "", "Second Point/Object", ""),
        ],
        "measurements.measure_angle": [
            ("obj1_name", "object", "", "First Object/Edge", ""),
            ("obj2_name", "object", "", "Second Object/Edge", ""),
        ],
        "measurements.measure_volume": [("obj_name", "object", "", "Object", "")],
        "measurements.measure_area": [("obj_name", "object", "", "Object/Face", "")],
        # Import/Export
        "export_import.export_stl": [
            ("filepath", "file_save", "model.stl", "Output File", ""),
            ("object_names", "objects", "", "Objects (empty=all)", ""),
            ("ascii", "bool", False, "ASCII Format", ""),
        ],
        "export_import.import_stl": [
            ("filepath", "file_open", "", "STL File", ""),
            ("object_name", "string", "", "Name (optional)", ""),
        ],
        # Advanced Primitives
        "advanced_primitives.create_tube": [
            ("outer_radius", "float", 10.0, "Outer Radius", "mm"),
            ("inner_radius", "float", 5.0, "Inner Radius", "mm"),
            ("height", "float", 10.0, "Height", "mm"),
            ("name", "string", "", "Name (optional)", ""),
        ],
        "advanced_primitives.create_prism": [
            ("sides", "int", 6, "Number of Sides", ""),
            ("radius", "float", 5.0, "Radius", "mm"),
            ("height", "float", 10.0, "Height", "mm"),
            ("name", "string", "", "Name (optional)", ""),
        ],
        # Advanced Operations
        "advanced_operations.extrude_profile": [
            ("profile_name", "object", "", "Profile Object", ""),
            ("distance", "float", 10.0, "Distance", "mm"),
            ("direction", "vector", "[0,0,1]", "Direction", ""),
            ("name", "string", "", "Name (optional)", ""),
        ],
        "advanced_operations.revolve_profile": [
            ("profile_name", "object", "", "Profile Object", ""),
            ("angle", "float", 360.0, "Angle", "°"),
            ("axis", "vector", "[0,0,1]", "Axis", ""),
            ("name", "string", "", "Name (optional)", ""),
        ],
        # Surface Modification
        "surface_modification.fillet_edges": [
            ("obj_name", "object", "", "Object", ""),
            ("edge_indices", "indices", "", "Edge Indices", ""),
            ("radius", "float", 1.0, "Radius", "mm"),
            ("name", "string", "", "Name (optional)", ""),
        ],
        "surface_modification.chamfer_edges": [
            ("obj_name", "object", "", "Object", ""),
            ("edge_indices", "indices", "", "Edge Indices", ""),
            ("distance", "float", 1.0, "Distance", "mm"),
            ("name", "string", "", "Name (optional)", ""),
        ],
    }

    def __init__(self, category, method, parent=None):
        super().__init__(parent)
        self.category = category
        self.method = method
        self.inputs = {}

        self.setWindowTitle(f"{category}.{method}")
        self.setModal(True)
        self.setMinimumWidth(300)

        self._setup_ui()

    def _setup_ui(self):
        """Setup the parameter dialog UI."""
        layout = QtWidgets.QVBoxLayout(self)

        # Title
        title = QtWidgets.QLabel(self.method.replace("_", " ").title())
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Parameters
        param_key = f"{self.category}.{self.method}"
        if param_key in self.PARAM_CONFIGS:
            form = QtWidgets.QFormLayout()

            for param_name, param_type, default, label, unit in self.PARAM_CONFIGS[
                param_key
            ]:
                widget = self._create_input_widget(
                    param_name, param_type, default, unit
                )
                if widget:
                    form.addRow(f"{label}:", widget)
                    self.inputs[param_name] = widget

            layout.addLayout(form)
        else:
            # Generic message for unconfigured tools
            msg = QtWidgets.QLabel(
                "This tool requires no parameters or is not yet configured."
            )
            msg.setWordWrap(True)
            layout.addWidget(msg)

        # Buttons
        buttons = QtWidgets.QDialogButtonBox(
            QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel
        )
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _create_input_widget(self, name, param_type, default, unit):
        """Create appropriate input widget for parameter type."""
        if param_type == "float":
            widget = QtWidgets.QDoubleSpinBox()
            widget.setRange(-10000, 10000)
            widget.setValue(default)
            widget.setDecimals(2)
            if unit:
                widget.setSuffix(f" {unit}")
            return widget

        elif param_type == "int":
            widget = QtWidgets.QSpinBox()
            widget.setRange(-10000, 10000)
            widget.setValue(default)
            return widget

        elif param_type == "bool":
            widget = QtWidgets.QCheckBox()
            widget.setChecked(default)
            return widget

        elif param_type == "string":
            widget = QtWidgets.QLineEdit()
            widget.setText(default)
            widget.setPlaceholderText("Optional" if not default else "")
            return widget

        elif param_type == "object":
            widget = QtWidgets.QComboBox()
            widget.setEditable(True)
            # Populate with current objects
            if FreeCAD.ActiveDocument:
                for obj in FreeCAD.ActiveDocument.Objects:
                    widget.addItem(obj.Name)
            return widget

        elif param_type == "objects":
            widget = QtWidgets.QLineEdit()
            widget.setPlaceholderText("Obj1,Obj2,... or empty for all")
            return widget

        elif param_type == "point":
            widget = QtWidgets.QLineEdit()
            widget.setPlaceholderText("[x,y,z] or ObjectName")
            return widget

        elif param_type == "vector":
            widget = QtWidgets.QLineEdit()
            widget.setText(str(default))
            widget.setPlaceholderText("[x,y,z]")
            return widget

        elif param_type == "indices":
            widget = QtWidgets.QLineEdit()
            widget.setPlaceholderText("0,1,2,... or empty for all")
            return widget

        elif param_type == "choice":
            widget = QtWidgets.QComboBox()
            if isinstance(unit, list):  # Choices passed in unit field
                widget.addItems(unit)
            widget.setCurrentText(str(default))
            return widget

        elif param_type == "file_save":
            widget = FileSelectWidget(default, True)
            return widget

        elif param_type == "file_open":
            widget = FileSelectWidget(default, False)
            return widget

        return None

    def get_parameters(self):
        """Extract parameters from dialog."""
        params = {}

        for name, widget in self.inputs.items():
            if isinstance(widget, QtWidgets.QDoubleSpinBox):
                params[name] = widget.value()
            elif isinstance(widget, QtWidgets.QSpinBox):
                params[name] = widget.value()
            elif isinstance(widget, QtWidgets.QCheckBox):
                params[name] = widget.isChecked()
            elif isinstance(widget, QtWidgets.QComboBox):
                params[name] = widget.currentText()
            elif isinstance(widget, QtWidgets.QLineEdit):
                text = widget.text().strip()
                if text:
                    # Handle special cases
                    if name == "object_names" and text:
                        params[name] = [s.strip() for s in text.split(",") if s.strip()]
                    elif name == "edge_indices" and text:
                        params[name] = [
                            int(s.strip()) for s in text.split(",") if s.strip()
                        ]
                    elif (
                        name.startswith("point")
                        or name == "direction"
                        or name == "axis"
                    ) and text.startswith("["):
                        try:
                            params[name] = eval(text)
                        except:
                            params[name] = text
                    else:
                        params[name] = text
            elif isinstance(widget, FileSelectWidget):
                params[name] = widget.get_path()

        return params


class FileSelectWidget(QtWidgets.QWidget):
    """Widget for file selection."""

    def __init__(self, default="", save_mode=False, parent=None):
        super().__init__(parent)
        self.save_mode = save_mode

        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.path_edit = QtWidgets.QLineEdit()
        self.path_edit.setText(default)

        self.browse_btn = QtWidgets.QPushButton("...")
        self.browse_btn.setMaximumWidth(30)
        self.browse_btn.clicked.connect(self._browse)

        layout.addWidget(self.path_edit)
        layout.addWidget(self.browse_btn)

    def _browse(self):
        """Open file dialog."""
        if self.save_mode:
            path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self, "Save File", self.path_edit.text()
            )
        else:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(
                self, "Open File", self.path_edit.text()
            )

        if path:
            self.path_edit.setText(path)

    def get_path(self):
        """Get the selected path."""
        return self.path_edit.text()
