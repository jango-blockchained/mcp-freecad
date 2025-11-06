"""Context Enricher - Enhances conversation context with FreeCAD state and history"""

from datetime import datetime
from typing import Any, Dict, List, Optional

import FreeCAD
import FreeCADGui


class ContextEnricher:
    """
    Enriches conversation context with current FreeCAD state,
    document information, and interaction history.
    """

    def __init__(self):
        """Initialize the Context Enricher"""
        self.context_history = []
        self.max_history_items = 10
        self.object_cache = {}

        # Context extraction configuration
        self.config = {
            "include_document_info": True,
            "include_selection": True,
            "include_objects": True,
            "include_constraints": True,
            "include_materials": True,
            "include_view_info": True,
            "include_recent_commands": True,
            "max_objects_detail": 50,
            "summarize_large_documents": True,
        }

    def enrich(self, base_context: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Enrich the base context with FreeCAD state information

        Args:
            base_context: Optional base context to enrich

        Returns:
            Enriched context dictionary
        """
        context = base_context.copy() if base_context else {}

        # Add timestamp
        context["timestamp"] = datetime.now().isoformat()
        context["enrichment_version"] = "1.0"

        # Extract various context components
        if self.config["include_document_info"]:
            context["document"] = self._extract_document_info()

        if self.config["include_selection"]:
            context["selection"] = self._extract_selection_info()

        if self.config["include_objects"]:
            context["objects"] = self._extract_objects_info()

        if self.config["include_constraints"]:
            context["constraints"] = self._extract_constraints_info()

        if self.config["include_materials"]:
            context["materials"] = self._extract_materials_info()

        if self.config["include_view_info"]:
            context["view"] = self._extract_view_info()

        if self.config["include_recent_commands"]:
            context["recent_commands"] = self._extract_recent_commands()

        # Add context summary
        context["summary"] = self._generate_context_summary(context)

        # Add to history
        self._add_to_history(context)

        return context

    def _extract_document_info(self) -> Dict[str, Any]:
        """Extract information about the active document"""
        doc_info = {
            "has_active_document": False,
            "name": None,
            "label": None,
            "filename": None,
            "modified": False,
            "object_count": 0,
            "undo_count": 0,
            "redo_count": 0,
        }

        try:
            doc = FreeCAD.ActiveDocument
            if doc:
                doc_info["has_active_document"] = True
                doc_info["name"] = doc.Name
                doc_info["label"] = doc.Label
                doc_info["filename"] = (
                    doc.FileName if hasattr(doc, "FileName") else None
                )
                doc_info["modified"] = (
                    doc.Modified if hasattr(doc, "Modified") else False
                )
                doc_info["object_count"] = len(doc.Objects)
                doc_info["undo_count"] = (
                    doc.UndoCount if hasattr(doc, "UndoCount") else 0
                )
                doc_info["redo_count"] = (
                    doc.RedoCount if hasattr(doc, "RedoCount") else 0
                )

                # Document properties
                doc_info["properties"] = self._extract_properties(doc)

        except Exception as e:
            doc_info["error"] = str(e)

        return doc_info

    def _extract_selection_info(self) -> Dict[str, Any]:
        """Extract information about current selection"""
        selection_info = {
            "count": 0,
            "objects": [],
            "sub_objects": [],
            "has_selection": False,
        }

        try:
            if FreeCADGui:
                selection = FreeCADGui.Selection.getSelection()
                selection_info["count"] = len(selection)
                selection_info["has_selection"] = len(selection) > 0

                for obj in selection[:10]:  # Limit to first 10
                    obj_info = {
                        "name": obj.Name,
                        "label": obj.Label,
                        "type": obj.TypeId,
                        "properties": self._extract_properties(obj, detailed=False),
                    }

                    # Check for shape
                    if hasattr(obj, "Shape"):
                        obj_info["shape_type"] = (
                            obj.Shape.ShapeType if obj.Shape else None
                        )
                        if obj.Shape:
                            obj_info["shape_info"] = {
                                "volume": (
                                    obj.Shape.Volume
                                    if hasattr(obj.Shape, "Volume")
                                    else None
                                ),
                                "area": (
                                    obj.Shape.Area
                                    if hasattr(obj.Shape, "Area")
                                    else None
                                ),
                                "length": (
                                    obj.Shape.Length
                                    if hasattr(obj.Shape, "Length")
                                    else None
                                ),
                                "is_valid": (
                                    obj.Shape.isValid()
                                    if hasattr(obj.Shape, "isValid")
                                    else None
                                ),
                            }

                    selection_info["objects"].append(obj_info)

                # Get sub-object selection
                sel_ex = FreeCADGui.Selection.getSelectionEx()
                for sel in sel_ex:
                    if sel.SubElementNames:
                        selection_info["sub_objects"].append(
                            {
                                "object": sel.ObjectName,
                                "sub_elements": sel.SubElementNames,
                            }
                        )

        except Exception as e:
            selection_info["error"] = str(e)

        return selection_info

    def _extract_objects_info(self) -> Dict[str, Any]:
        """Extract information about document objects"""
        objects_info = {
            "total_count": 0,
            "by_type": {},
            "object_tree": [],
            "details": [],
        }

        try:
            doc = FreeCAD.ActiveDocument
            if not doc:
                return objects_info

            objects_info["total_count"] = len(doc.Objects)

            # Count by type
            for obj in doc.Objects:
                type_id = obj.TypeId
                if type_id not in objects_info["by_type"]:
                    objects_info["by_type"][type_id] = 0
                objects_info["by_type"][type_id] += 1

            # Build object tree (limited)
            root_objects = [
                obj
                for obj in doc.Objects
                if not hasattr(obj, "InList") or not obj.InList
            ]
            for obj in root_objects[:10]:  # Limit root objects
                objects_info["object_tree"].append(
                    self._build_object_tree(obj, max_depth=3)
                )

            # Detailed info for recent/important objects
            if (
                self.config["summarize_large_documents"]
                and len(doc.Objects) > self.config["max_objects_detail"]
            ):
                # Just get the most recent objects
                recent_objects = sorted(
                    doc.Objects,
                    key=lambda x: x.ID if hasattr(x, "ID") else 0,
                    reverse=True,
                )[:10]
            else:
                recent_objects = doc.Objects[: self.config["max_objects_detail"]]

            for obj in recent_objects:
                obj_detail = self._extract_object_detail(obj)
                if obj_detail:
                    objects_info["details"].append(obj_detail)

        except Exception as e:
            objects_info["error"] = str(e)

        return objects_info

    def _extract_object_detail(self, obj) -> Optional[Dict[str, Any]]:
        """Extract detailed information about an object"""
        try:
            detail = {
                "name": obj.Name,
                "label": obj.Label,
                "type": obj.TypeId,
                "id": obj.ID if hasattr(obj, "ID") else None,
                "visibility": obj.Visibility if hasattr(obj, "Visibility") else None,
            }

            # Shape information
            if hasattr(obj, "Shape") and obj.Shape:
                shape = obj.Shape
                detail["shape"] = {
                    "type": shape.ShapeType,
                    "faces": len(shape.Faces) if hasattr(shape, "Faces") else 0,
                    "edges": len(shape.Edges) if hasattr(shape, "Edges") else 0,
                    "vertices": (
                        len(shape.Vertexes) if hasattr(shape, "Vertexes") else 0
                    ),
                    "is_solid": (
                        shape.isClosed() if hasattr(shape, "isClosed") else None
                    ),
                }

            # Placement
            if hasattr(obj, "Placement"):
                placement = obj.Placement
                detail["placement"] = {
                    "position": list(placement.Base),
                    "rotation": {
                        "axis": list(placement.Rotation.Axis),
                        "angle": placement.Rotation.Angle,
                    },
                }

            # Key properties
            detail["properties"] = self._extract_properties(obj, detailed=False)

            return detail

        except (AttributeError, TypeError, RuntimeError) as e:
            # AttributeError: FreeCAD object missing expected attributes
            # TypeError: Invalid type conversion or property access
            # RuntimeError: FreeCAD object in invalid state
            import logging

            logging.getLogger(__name__).debug(f"Failed to extract object detail: {e}")
            return None

    def _build_object_tree(self, obj, current_depth=0, max_depth=3) -> Dict[str, Any]:
        """Build object hierarchy tree"""
        tree = {
            "name": obj.Name,
            "label": obj.Label,
            "type": obj.TypeId,
            "children": [],
        }

        if current_depth < max_depth and hasattr(obj, "OutList"):
            for child in obj.OutList[:5]:  # Limit children
                tree["children"].append(
                    self._build_object_tree(child, current_depth + 1, max_depth)
                )

        return tree

    def _extract_properties(self, obj, detailed: bool = True) -> Dict[str, Any]:
        """Extract object properties"""
        properties = {}

        try:
            # Get property list
            if hasattr(obj, "PropertiesList"):
                prop_list = obj.PropertiesList

                # Filter important properties
                important_props = [
                    "Length",
                    "Width",
                    "Height",
                    "Radius",
                    "Radius1",
                    "Radius2",
                    "Angle",
                    "Angle1",
                    "Angle2",
                    "Angle3",
                    "Base",
                    "Axis",
                    "Center",
                    "Position",
                    "Label",
                    "Expression",
                    "Constrained",
                ]

                for prop_name in prop_list:
                    if not detailed and prop_name not in important_props:
                        continue

                    try:
                        value = getattr(obj, prop_name)

                        # Convert complex types
                        if hasattr(value, "__dict__"):
                            # Skip complex objects in non-detailed mode
                            if not detailed:
                                continue
                            value = str(value)
                        elif hasattr(value, "__iter__") and not isinstance(value, str):
                            value = list(value)

                        properties[prop_name] = value

                    except (AttributeError, TypeError, ValueError):
                        # AttributeError: Property doesn't exist
                        # TypeError: Property value type conversion issue
                        # ValueError: Property value invalid
                        continue

        except (AttributeError, TypeError):
            # AttributeError: Object missing expected attributes
            # TypeError: Invalid type operations
            pass

        return properties

    def _extract_constraints_info(self) -> Dict[str, Any]:
        """Extract constraint information from sketches"""
        constraints_info = {"total_count": 0, "by_type": {}, "sketches": []}

        try:
            doc = FreeCAD.ActiveDocument
            if not doc:
                return constraints_info

            # Find all sketches
            sketches = [
                obj for obj in doc.Objects if obj.TypeId == "Sketcher::SketchObject"
            ]

            for sketch in sketches[:10]:  # Limit sketches
                sketch_info = {
                    "name": sketch.Name,
                    "label": sketch.Label,
                    "constraint_count": (
                        sketch.ConstraintCount
                        if hasattr(sketch, "ConstraintCount")
                        else 0
                    ),
                    "constraints": [],
                }

                # Get constraints
                if hasattr(sketch, "Constraints"):
                    for i, constraint in enumerate(
                        sketch.Constraints[:20]
                    ):  # Limit constraints
                        cons_info = {
                            "index": i,
                            "type": (
                                constraint.Type if hasattr(constraint, "Type") else None
                            ),
                            "value": (
                                constraint.Value
                                if hasattr(constraint, "Value")
                                else None
                            ),
                        }
                        sketch_info["constraints"].append(cons_info)

                        # Count by type
                        cons_type = cons_info["type"]
                        if cons_type:
                            if cons_type not in constraints_info["by_type"]:
                                constraints_info["by_type"][cons_type] = 0
                            constraints_info["by_type"][cons_type] += 1
                            constraints_info["total_count"] += 1

                constraints_info["sketches"].append(sketch_info)

        except Exception as e:
            constraints_info["error"] = str(e)

        return constraints_info

    def _extract_materials_info(self) -> Dict[str, Any]:
        """Extract material information"""
        materials_info = {"assigned_materials": [], "available_materials": []}

        try:
            doc = FreeCAD.ActiveDocument
            if not doc:
                return materials_info

            # Find objects with materials
            for obj in doc.Objects:
                if hasattr(obj, "Material") and obj.Material:
                    mat_info = {"object": obj.Name, "material": str(obj.Material)}
                    materials_info["assigned_materials"].append(mat_info)

        except Exception as e:
            materials_info["error"] = str(e)

        return materials_info

    def _extract_view_info(self) -> Dict[str, Any]:
        """Extract 3D view information"""
        view_info = {"active_view": None, "camera": {}}

        try:
            if FreeCADGui:
                view = (
                    FreeCADGui.ActiveDocument.ActiveView
                    if FreeCADGui.ActiveDocument
                    else None
                )
                if view:
                    view_info["active_view"] = True

                    # Camera info
                    if hasattr(view, "getCameraNode"):
                        camera = view.getCameraNode()
                        if camera:
                            view_info["camera"] = {
                                "type": camera.getTypeId().getName(),
                                "position": (
                                    list(camera.position.getValue())
                                    if hasattr(camera, "position")
                                    else None
                                ),
                                "orientation": (
                                    str(camera.orientation.getValue())
                                    if hasattr(camera, "orientation")
                                    else None
                                ),
                            }

        except Exception as e:
            view_info["error"] = str(e)

        return view_info

    def _extract_recent_commands(self) -> List[str]:
        """Extract recently executed commands"""
        # This is a placeholder - actual implementation would need to track commands
        return []

    def _generate_context_summary(self, context: Dict) -> str:
        """Generate a human-readable summary of the context"""
        summary_parts = []

        # Document summary
        if "document" in context and context["document"]["has_active_document"]:
            doc = context["document"]
            summary_parts.append(
                f"Active document: {doc['label']} with {doc['object_count']} objects"
            )

        # Selection summary
        if "selection" in context and context["selection"]["has_selection"]:
            sel = context["selection"]
            summary_parts.append(f"Selected: {sel['count']} object(s)")

        # Objects summary
        if "objects" in context:
            obj = context["objects"]
            if obj["by_type"]:
                types = list(obj["by_type"].keys())[:3]
                summary_parts.append(f"Main object types: {', '.join(types)}")

        return ". ".join(summary_parts) if summary_parts else "Empty FreeCAD session"

    def _add_to_history(self, context: Dict):
        """Add context to history"""
        self.context_history.append(
            {"timestamp": context["timestamp"], "summary": context.get("summary", "")}
        )

        # Limit history size
        if len(self.context_history) > self.max_history_items:
            self.context_history.pop(0)

    def get_history_summary(self) -> List[Dict]:
        """Get summary of context history"""
        return self.context_history.copy()

    def clear_history(self):
        """Clear context history"""
        self.context_history.clear()
        self.object_cache.clear()

    def update_config(self, config: Dict):
        """Update enricher configuration"""
        self.config.update(config)
