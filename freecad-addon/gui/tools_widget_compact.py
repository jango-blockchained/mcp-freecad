"""Compact Tools Widget - Clean and organized GUI for all FreeCAD tools"""

import os
import sys

# Ensure the addon directory is in the Python path
addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

from PySide2 import QtCore, QtGui, QtWidgets
import logging
from typing import Dict, Any, Optional, List
import FreeCAD


class CompactToolButton(QtWidgets.QPushButton):
    """Compact tool button with icon and tooltip."""

    def __init__(self, text, tooltip, icon_text=None, parent=None):
        super().__init__(parent)
        self.setText(icon_text or text[:3].upper())
        self.setToolTip(f"<b>{text}</b><br>{tooltip}")
        self.setFixedSize(60, 40)
        self.setStyleSheet("""
            QPushButton {
                font-size: 11px;
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 4px;
                background-color: #f5f5f5;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
                border: 1px solid #999;
            }
            QPushButton:pressed {
                background-color: #d0d0d0;
            }
        """)


class ToolCategoryWidget(QtWidgets.QGroupBox):
    """Collapsible category widget for tools."""

    def __init__(self, title, parent=None):
        super().__init__(title, parent)
        self.setCheckable(True)
        self.setChecked(True)
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 2px solid #cccccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
        """)


class ToolsWidget(QtWidgets.QWidget):
    """Comprehensive widget for all FreeCAD tool management."""

    tool_executed = QtCore.Signal(str, dict, dict)  # tool_name, parameters, result

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
                from tools.primitives import PrimitivesTool
                from tools.operations import OperationsTool
                from tools.measurements import MeasurementsTool
                from tools.export_import import ExportImportTool
                from tools.advanced_primitives import AdvancedPrimitivesTool
                from tools.advanced_operations import AdvancedOperationsTool
                from tools.surface_modification import SurfaceModificationTool
            except ImportError:
                # Try relative imports
                from ..tools.primitives import PrimitivesTool
                from ..tools.operations import OperationsTool
                from ..tools.measurements import MeasurementsTool
                from ..tools.export_import import ExportImportTool
                from ..tools.advanced_primitives import AdvancedPrimitivesTool
                from ..tools.advanced_operations import AdvancedOperationsTool
                from ..tools.surface_modification import SurfaceModificationTool

            self.tools = {
                "primitives": PrimitivesTool(),
                "operations": OperationsTool(),
                "measurements": MeasurementsTool(),
                "export_import": ExportImportTool(),
                "advanced_primitives": AdvancedPrimitivesTool(),
                "advanced_operations": AdvancedOperationsTool(),
                "surface_modification": SurfaceModificationTool()
            }
            self.logger.info("All tools loaded successfully")
        except ImportError as e:
            self.logger.error(f"Failed to import some tools: {e}")
            # Try to load basic tools only
            try:
                try:
                    from tools.primitives import PrimitivesTool
                    from tools.operations import OperationsTool
                    from tools.measurements import MeasurementsTool
                    from tools.export_import import ExportImportTool
                except ImportError:
                    from ..tools.primitives import PrimitivesTool
                    from ..tools.operations import OperationsTool
                    from ..tools.measurements import MeasurementsTool
                    from ..tools.export_import import ExportImportTool

                self.tools = {
                    "primitives": PrimitivesTool(),
                    "operations": OperationsTool(),
                    "measurements": MeasurementsTool(),
                    "export_import": ExportImportTool()
                }
                self.logger.warning("Only basic tools loaded")
            except Exception as e2:
                self.tools = {}
                self.logger.error(f"No tools could be loaded: {e2}")

    def _setup_ui(self):
        """Setup the user interface."""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setSpacing(5)
        layout.setContentsMargins(5, 5, 5, 5)

        # Header
        header = QtWidgets.QLabel("🛠️ FreeCAD Tools")
        header.setStyleSheet("font-size: 16px; font-weight: bold; margin: 5px;")
        layout.addWidget(header)

        # Create scroll area
        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setHorizontalScrollBarPolicy(QtCore.Qt.ScrollBarAlwaysOff)

        scroll_widget = QtWidgets.QWidget()
        scroll_layout = QtWidgets.QVBoxLayout(scroll_widget)
        scroll_layout.setSpacing(10)

        # Tool categories with all tools
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

        # Status bar
        self.status_label = QtWidgets.QLabel("Ready")
        self.status_label.setStyleSheet("padding: 5px; background-color: #f0f0f0; border-radius: 3px;")
        layout.addWidget(self.status_label)

    def _create_basic_primitives(self, layout):
        """Create basic primitives section."""
        category = ToolCategoryWidget("Basic Primitives")
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(5)

        tools = [
            ("Box", "Create a box/cube", "BOX", "create_box"),
            ("Cylinder", "Create a cylinder", "CYL", "create_cylinder"),
            ("Sphere", "Create a sphere", "SPH", "create_sphere"),
            ("Cone", "Create a cone", "CON", "create_cone"),
            ("Torus", "Create a torus", "TOR", "create_torus"),
            ("Plane", "Create a plane", "PLN", "create_plane")
        ]

        for i, (name, tooltip, icon, method) in enumerate(tools):
            btn = CompactToolButton(name, tooltip, icon)
            btn.clicked.connect(lambda checked, m=method: self._execute_tool("primitives", m))
            grid.addWidget(btn, i // 4, i % 4)

        category.setLayout(grid)
        layout.addWidget(category)

    def _create_basic_operations(self, layout):
        """Create basic operations section."""
        category = ToolCategoryWidget("Basic Operations")
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(5)

        tools = [
            ("Union", "Boolean union of objects", "UNI", "boolean_union"),
            ("Cut", "Boolean cut/subtract", "CUT", "boolean_cut"),
            ("Intersect", "Boolean intersection", "INT", "boolean_intersection"),
            ("Move", "Move/translate object", "MOV", "move_object"),
            ("Rotate", "Rotate object", "ROT", "rotate_object"),
            ("Scale", "Scale object", "SCL", "scale_object"),
            ("Mirror", "Mirror object", "MIR", "mirror_object"),
            ("Array", "Create array of objects", "ARR", "create_array")
        ]

        for i, (name, tooltip, icon, method) in enumerate(tools):
            btn = CompactToolButton(name, tooltip, icon)
            btn.clicked.connect(lambda checked, m=method: self._execute_tool("operations", m))
            grid.addWidget(btn, i // 4, i % 4)

        category.setLayout(grid)
        layout.addWidget(category)

    def _create_measurements(self, layout):
        """Create measurements section."""
        category = ToolCategoryWidget("Measurements")
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(5)

        tools = [
            ("Distance", "Measure distance", "DST", "measure_distance"),
            ("Angle", "Measure angle", "ANG", "measure_angle"),
            ("Volume", "Measure volume", "VOL", "measure_volume"),
            ("Area", "Measure area", "ARA", "measure_area"),
            ("Length", "Measure length", "LEN", "measure_length"),
            ("Radius", "Measure radius", "RAD", "measure_radius"),
            ("BBox", "Bounding box", "BBX", "measure_bounding_box"),
            ("CoG", "Center of gravity", "COG", "measure_center_of_gravity")
        ]

        for i, (name, tooltip, icon, method) in enumerate(tools):
            btn = CompactToolButton(name, tooltip, icon)
            btn.clicked.connect(lambda checked, m=method: self._execute_tool("measurements", m))
            grid.addWidget(btn, i // 4, i % 4)

        category.setLayout(grid)
        layout.addWidget(category)

    def _create_import_export(self, layout):
        """Create import/export section."""
        category = ToolCategoryWidget("Import/Export")
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(5)

        tools = [
            ("Import STL", "Import STL file", "I-STL", "import_stl"),
            ("Export STL", "Export to STL", "E-STL", "export_stl"),
            ("Import STEP", "Import STEP file", "I-STP", "import_step"),
            ("Export STEP", "Export to STEP", "E-STP", "export_step"),
            ("Import IGES", "Import IGES file", "I-IGS", "import_iges"),
            ("Export IGES", "Export to IGES", "E-IGS", "export_iges"),
            ("Import OBJ", "Import OBJ file", "I-OBJ", "import_obj"),
            ("Export OBJ", "Export to OBJ", "E-OBJ", "export_obj")
        ]

        for i, (name, tooltip, icon, method) in enumerate(tools):
            btn = CompactToolButton(name, tooltip, icon)
            btn.clicked.connect(lambda checked, m=method: self._execute_tool("export_import", m))
            grid.addWidget(btn, i // 4, i % 4)

        category.setLayout(grid)
        layout.addWidget(category)

    def _create_advanced_primitives(self, layout):
        """Create advanced primitives section."""
        category = ToolCategoryWidget("Advanced Primitives")
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(5)

        tools = [
            ("Tube", "Create hollow cylinder", "TUB", "create_tube"),
            ("Prism", "Create n-sided prism", "PRS", "create_prism"),
            ("Wedge", "Create wedge shape", "WDG", "create_wedge"),
            ("Ellipsoid", "Create ellipsoid", "ELL", "create_ellipsoid"),
            ("Spring", "Create spring/helix", "SPR", "create_spring"),
            ("Gear", "Create gear", "GER", "create_gear"),
            ("Thread", "Create thread", "THR", "create_thread"),
            ("Text", "Create 3D text", "TXT", "create_text")
        ]

        for i, (name, tooltip, icon, method) in enumerate(tools):
            btn = CompactToolButton(name, tooltip, icon)
            btn.clicked.connect(lambda checked, m=method: self._execute_tool("advanced_primitives", m))
            grid.addWidget(btn, i // 4, i % 4)

        category.setLayout(grid)
        layout.addWidget(category)

    def _create_advanced_operations(self, layout):
        """Create advanced operations section."""
        category = ToolCategoryWidget("Advanced Operations")
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(5)

        tools = [
            ("Extrude", "Extrude profile", "EXT", "extrude_profile"),
            ("Revolve", "Revolve profile", "REV", "revolve_profile"),
            ("Loft", "Loft between profiles", "LFT", "loft_profiles"),
            ("Sweep", "Sweep along path", "SWP", "sweep_profile"),
            ("Helix", "Create helix curve", "HLX", "create_helix"),
            ("Pattern", "Create pattern", "PTN", "create_pattern"),
            ("Project", "Project onto surface", "PRJ", "project_to_surface"),
            ("Wrap", "Wrap onto surface", "WRP", "wrap_to_surface")
        ]

        for i, (name, tooltip, icon, method) in enumerate(tools):
            btn = CompactToolButton(name, tooltip, icon)
            btn.clicked.connect(lambda checked, m=method: self._execute_tool("advanced_operations", m))
            grid.addWidget(btn, i // 4, i % 4)

        category.setLayout(grid)
        layout.addWidget(category)

    def _create_surface_modification(self, layout):
        """Create surface modification section."""
        category = ToolCategoryWidget("Surface Modification")
        grid = QtWidgets.QGridLayout()
        grid.setSpacing(5)

        tools = [
            ("Fillet", "Round edges", "FLT", "fillet_edges"),
            ("Chamfer", "Chamfer edges", "CHM", "chamfer_edges"),
            ("Draft", "Add draft angle", "DFT", "draft_faces"),
            ("Thickness", "Shell/hollow", "THK", "create_thickness"),
            ("Offset", "Offset surface", "OFS", "offset_surface"),
            ("Blend", "Blend surfaces", "BLD", "blend_surfaces"),
            ("Patch", "Create patch", "PCH", "create_patch"),
            ("Simplify", "Simplify shape", "SMP", "simplify_shape")
        ]

        for i, (name, tooltip, icon, method) in enumerate(tools):
            btn = CompactToolButton(name, tooltip, icon)
            btn.clicked.connect(lambda checked, m=method: self._execute_tool("surface_modification", m))
            grid.addWidget(btn, i // 4, i % 4)

        category.setLayout(grid)
        layout.addWidget(category)

    def _execute_tool(self, category, method):
        """Execute a tool with parameter dialog."""
        if category not in self.tools:
            QtWidgets.QMessageBox.warning(self, "Error", f"Tool category '{category}' not available")
            return

        tool = self.tools[category]
        if not hasattr(tool, method):
            QtWidgets.QMessageBox.warning(self, "Error", f"Method '{method}' not found in {category}")
            return

        # Create parameter dialog
        dialog = ToolParameterDialog(category, method, self)
        if dialog.exec_():
            params = dialog.get_parameters()

            try:
                # Execute the tool
                result = getattr(tool, method)(**params)

                # Update status
                if result.get('success'):
                    self.status_label.setText(f"✅ {result.get('message', 'Success')}")
                    self.status_label.setStyleSheet("padding: 5px; background-color: #c8e6c9; border-radius: 3px;")
                else:
                    self.status_label.setText(f"❌ {result.get('message', 'Failed')}")
                    self.status_label.setStyleSheet("padding: 5px; background-color: #ffcdd2; border-radius: 3px;")

                # Emit signal
                self.tool_executed.emit(f"{category}.{method}", params, result)

            except Exception as e:
                self.logger.error(f"Error executing {category}.{method}: {e}")
                self.status_label.setText(f"❌ Error: {str(e)}")
                self.status_label.setStyleSheet("padding: 5px; background-color: #ffcdd2; border-radius: 3px;")


class ToolParameterDialog(QtWidgets.QDialog):
    """Compact dialog for tool parameters."""

    # Parameter configurations for all tools
    PARAM_CONFIGS = {
        # Basic Primitives
        "primitives.create_box": [
            ("length", "float", 10.0, "Length", "mm"),
            ("width", "float", 10.0, "Width", "mm"),
            ("height", "float", 10.0, "Height", "mm"),
            ("name", "string", "", "Name (optional)", "")
        ],
        "primitives.create_cylinder": [
            ("radius", "float", 5.0, "Radius", "mm"),
            ("height", "float", 10.0, "Height", "mm"),
            ("name", "string", "", "Name (optional)", "")
        ],
        "primitives.create_sphere": [
            ("radius", "float", 5.0, "Radius", "mm"),
            ("name", "string", "", "Name (optional)", "")
        ],
        "primitives.create_cone": [
            ("radius1", "float", 5.0, "Bottom Radius", "mm"),
            ("radius2", "float", 0.0, "Top Radius", "mm"),
            ("height", "float", 10.0, "Height", "mm"),
            ("name", "string", "", "Name (optional)", "")
        ],
        "primitives.create_torus": [
            ("radius1", "float", 10.0, "Major Radius", "mm"),
            ("radius2", "float", 2.0, "Minor Radius", "mm"),
            ("name", "string", "", "Name (optional)", "")
        ],
        "primitives.create_plane": [
            ("length", "float", 10.0, "Length", "mm"),
            ("width", "float", 10.0, "Width", "mm"),
            ("name", "string", "", "Name (optional)", "")
        ],

        # Basic Operations
        "operations.boolean_union": [
            ("obj1_name", "object", "", "First Object", ""),
            ("obj2_name", "object", "", "Second Object", ""),
            ("keep_originals", "bool", False, "Keep Originals", "")
        ],
        "operations.boolean_cut": [
            ("obj1_name", "object", "", "Base Object", ""),
            ("obj2_name", "object", "", "Tool Object", ""),
            ("keep_originals", "bool", False, "Keep Originals", "")
        ],
        "operations.boolean_intersection": [
            ("obj1_name", "object", "", "First Object", ""),
            ("obj2_name", "object", "", "Second Object", ""),
            ("keep_originals", "bool", False, "Keep Originals", "")
        ],
        "operations.move_object": [
            ("obj_name", "object", "", "Object", ""),
            ("x", "float", 0.0, "X", "mm"),
            ("y", "float", 0.0, "Y", "mm"),
            ("z", "float", 0.0, "Z", "mm"),
            ("relative", "bool", True, "Relative", "")
        ],
        "operations.rotate_object": [
            ("obj_name", "object", "", "Object", ""),
            ("angle", "float", 90.0, "Angle", "°"),
            ("axis", "choice", "z", "Axis", ["x", "y", "z"]),
            ("center", "point", "", "Center (optional)", "")
        ],
        "operations.scale_object": [
            ("obj_name", "object", "", "Object", ""),
            ("scale_x", "float", 1.0, "Scale X", ""),
            ("scale_y", "float", 1.0, "Scale Y", ""),
            ("scale_z", "float", 1.0, "Scale Z", "")
        ],

        # Measurements
        "measurements.measure_distance": [
            ("point1", "point", "", "First Point/Object", ""),
            ("point2", "point", "", "Second Point/Object", "")
        ],
        "measurements.measure_angle": [
            ("obj1_name", "object", "", "First Object/Edge", ""),
            ("obj2_name", "object", "", "Second Object/Edge", "")
        ],
        "measurements.measure_volume": [
            ("obj_name", "object", "", "Object", "")
        ],
        "measurements.measure_area": [
            ("obj_name", "object", "", "Object/Face", "")
        ],

        # Import/Export
        "export_import.export_stl": [
            ("filepath", "file_save", "model.stl", "Output File", ""),
            ("object_names", "objects", "", "Objects (empty=all)", ""),
            ("ascii", "bool", False, "ASCII Format", "")
        ],
        "export_import.import_stl": [
            ("filepath", "file_open", "", "STL File", ""),
            ("object_name", "string", "", "Name (optional)", "")
        ],

        # Advanced Primitives
        "advanced_primitives.create_tube": [
            ("outer_radius", "float", 10.0, "Outer Radius", "mm"),
            ("inner_radius", "float", 5.0, "Inner Radius", "mm"),
            ("height", "float", 10.0, "Height", "mm"),
            ("name", "string", "", "Name (optional)", "")
        ],
        "advanced_primitives.create_prism": [
            ("sides", "int", 6, "Number of Sides", ""),
            ("radius", "float", 5.0, "Radius", "mm"),
            ("height", "float", 10.0, "Height", "mm"),
            ("name", "string", "", "Name (optional)", "")
        ],

        # Advanced Operations
        "advanced_operations.extrude_profile": [
            ("profile_name", "object", "", "Profile Object", ""),
            ("distance", "float", 10.0, "Distance", "mm"),
            ("direction", "vector", "[0,0,1]", "Direction", ""),
            ("name", "string", "", "Name (optional)", "")
        ],
        "advanced_operations.revolve_profile": [
            ("profile_name", "object", "", "Profile Object", ""),
            ("angle", "float", 360.0, "Angle", "°"),
            ("axis", "vector", "[0,0,1]", "Axis", ""),
            ("name", "string", "", "Name (optional)", "")
        ],

        # Surface Modification
        "surface_modification.fillet_edges": [
            ("obj_name", "object", "", "Object", ""),
            ("edge_indices", "indices", "", "Edge Indices", ""),
            ("radius", "float", 1.0, "Radius", "mm"),
            ("name", "string", "", "Name (optional)", "")
        ],
        "surface_modification.chamfer_edges": [
            ("obj_name", "object", "", "Object", ""),
            ("edge_indices", "indices", "", "Edge Indices", ""),
            ("distance", "float", 1.0, "Distance", "mm"),
            ("name", "string", "", "Name (optional)", "")
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
        title = QtWidgets.QLabel(self.method.replace('_', ' ').title())
        title.setStyleSheet("font-size: 14px; font-weight: bold; margin-bottom: 10px;")
        layout.addWidget(title)

        # Parameters
        param_key = f"{self.category}.{self.method}"
        if param_key in self.PARAM_CONFIGS:
            form = QtWidgets.QFormLayout()

            for param_name, param_type, default, label, unit in self.PARAM_CONFIGS[param_key]:
                widget = self._create_input_widget(param_name, param_type, default, unit)
                if widget:
                    form.addRow(f"{label}:", widget)
                    self.inputs[param_name] = widget

            layout.addLayout(form)
        else:
            # Generic message for unconfigured tools
            msg = QtWidgets.QLabel("This tool requires no parameters or is not yet configured.")
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
                        params[name] = [s.strip() for s in text.split(',') if s.strip()]
                    elif name == "edge_indices" and text:
                        params[name] = [int(s.strip()) for s in text.split(',') if s.strip()]
                    elif (name.startswith("point") or name == "direction" or name == "axis") and text.startswith('['):
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
            path, _ = QtWidgets.QFileDialog.getSaveFileName(self, "Save File", self.path_edit.text())
        else:
            path, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Open File", self.path_edit.text())

        if path:
            self.path_edit.setText(path)

    def get_path(self):
        """Get the selected path."""
        return self.path_edit.text()
