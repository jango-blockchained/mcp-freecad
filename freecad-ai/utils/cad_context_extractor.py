"""
CAD Context Extractor - Extracts current FreeCAD state for AI context

This module provides functionality to extract relevant information from the current
FreeCAD document and workspace to provide context to AI models.
"""

import json
from typing import Any, Dict, List, Optional


class CADContextExtractor:
    """Extracts CAD context information from FreeCAD."""

    def __init__(self):
        """Initialize the CAD context extractor."""
        self.freecad_available = False
        self.freecad = None
        self.freecad_gui = None

        try:
            import FreeCAD

            self.freecad = FreeCAD
            self.freecad_available = True

            try:
                import FreeCADGui

                self.freecad_gui = FreeCADGui
            except ImportError:
                pass

        except ImportError:
            pass

    def get_full_context(self) -> Dict[str, Any]:
        """Get complete CAD context information."""
        if not self.freecad_available:
            return {
                "status": "FreeCAD not available",
                "documents": [],
                "workbench": "Unknown",
                "selection": [],
                "view": {},
            }

        context = {
            "status": "Available",
            "freecad_version": self._get_freecad_version(),
            "documents": self._get_documents_info(),
            "active_document": self._get_active_document_info(),
            "workbench": self._get_current_workbench(),
            "selection": self._get_selection_info(),
            "view": self._get_view_info(),
            "preferences": self._get_relevant_preferences(),
        }

        return context

    def get_compact_context(self) -> str:
        """Get a compact, human-readable context summary."""
        if not self.freecad_available:
            return "FreeCAD is not available in this environment."

        context_parts = []

        # FreeCAD version
        version = self._get_freecad_version()
        if version:
            context_parts.append(f"FreeCAD Version: {version}")

        # Active document
        doc_info = self._get_active_document_info()
        if doc_info and doc_info.get("name"):
            context_parts.append(f"Active Document: {doc_info['name']}")

            objects = doc_info.get("objects", [])
            if objects:
                context_parts.append(f"Objects in document: {len(objects)}")

                # List object types
                object_types = {}
                for obj in objects:
                    obj_type = obj.get("type", "Unknown")
                    object_types[obj_type] = object_types.get(obj_type, 0) + 1

                if object_types:
                    type_summary = ", ".join(
                        [
                            f"{count} {type_name}"
                            for type_name, count in object_types.items()
                        ]
                    )
                    context_parts.append(f"Object types: {type_summary}")
        else:
            context_parts.append("No active document")

        # Current workbench
        workbench = self._get_current_workbench()
        if workbench:
            context_parts.append(f"Current Workbench: {workbench}")

        # Selection
        selection = self._get_selection_info()
        if selection:
            context_parts.append(f"Selected: {len(selection)} object(s)")

        return "\n".join(context_parts) if context_parts else "No CAD context available"

    def _get_freecad_version(self) -> Optional[str]:
        """Get FreeCAD version information."""
        if not self.freecad:
            return None

        try:
            version_info = []
            if hasattr(self.freecad, "Version"):
                version_info.append(f"v{'.'.join(self.freecad.Version()[:3])}")

            if hasattr(self.freecad, "BuildVersionInfo"):
                build_info = self.freecad.BuildVersionInfo()
                if "BuildRevision" in build_info:
                    version_info.append(f"Build {build_info['BuildRevision']}")

            return " ".join(version_info) if version_info else "Unknown"
        except Exception:
            return "Unknown"

    def _get_documents_info(self) -> List[Dict[str, Any]]:
        """Get information about all open documents."""
        if not self.freecad:
            return []

        documents = []
        try:
            for doc in self.freecad.listDocuments().values():
                doc_info = {
                    "name": doc.Name,
                    "label": getattr(doc, "Label", doc.Name),
                    "file_path": getattr(doc, "FileName", ""),
                    "object_count": len(doc.Objects),
                    "modified": getattr(doc, "UndoMode", False),
                }
                documents.append(doc_info)
        except Exception:
            pass

        return documents

    def _get_active_document_info(self) -> Optional[Dict[str, Any]]:
        """Get detailed information about the active document."""
        if not self.freecad:
            return None

        try:
            doc = self.freecad.ActiveDocument
            if not doc:
                return None

            objects_info = []
            for obj in doc.Objects:
                obj_info = {
                    "name": obj.Name,
                    "label": getattr(obj, "Label", obj.Name),
                    "type": obj.TypeId,
                    "visible": (
                        getattr(obj, "Visibility", True)
                        if hasattr(obj, "Visibility")
                        else True
                    ),
                }

                # Add geometry information if available
                if hasattr(obj, "Shape") and obj.Shape:
                    try:
                        shape = obj.Shape
                        obj_info["geometry"] = {
                            "type": (
                                shape.ShapeType
                                if hasattr(shape, "ShapeType")
                                else "Unknown"
                            ),
                            "volume": (
                                round(shape.Volume, 3)
                                if hasattr(shape, "Volume")
                                else None
                            ),
                            "area": (
                                round(shape.Area, 3) if hasattr(shape, "Area") else None
                            ),
                            "length": (
                                round(shape.Length, 3)
                                if hasattr(shape, "Length")
                                else None
                            ),
                        }
                    except Exception:
                        pass

                objects_info.append(obj_info)

            return {
                "name": doc.Name,
                "label": getattr(doc, "Label", doc.Name),
                "file_path": getattr(doc, "FileName", ""),
                "objects": objects_info,
                "object_count": len(objects_info),
            }
        except Exception:
            return None

    def _get_current_workbench(self) -> Optional[str]:
        """Get the current active workbench."""
        if not self.freecad_gui:
            return None

        try:
            workbench = self.freecad_gui.activeWorkbench()
            if workbench:
                return getattr(
                    workbench,
                    "MenuText",
                    getattr(workbench, "__class__", {}).get("__name__", "Unknown"),
                )
        except Exception:
            pass

        return None

    def _get_selection_info(self) -> List[Dict[str, Any]]:
        """Get information about currently selected objects."""
        if not self.freecad_gui:
            return []

        selection_info = []
        try:
            selection = self.freecad_gui.Selection.getSelection()
            for obj in selection:
                obj_info = {
                    "name": obj.Name,
                    "label": getattr(obj, "Label", obj.Name),
                    "type": obj.TypeId,
                }

                # Add shape information if available
                if hasattr(obj, "Shape") and obj.Shape:
                    try:
                        shape = obj.Shape
                        obj_info["shape_type"] = (
                            shape.ShapeType
                            if hasattr(shape, "ShapeType")
                            else "Unknown"
                        )
                    except Exception:
                        pass

                selection_info.append(obj_info)
        except Exception:
            pass

        return selection_info

    def _get_view_info(self) -> Dict[str, Any]:
        """Get current view information."""
        if not self.freecad_gui:
            return {}

        view_info = {}
        try:
            view = (
                self.freecad_gui.ActiveDocument.ActiveView
                if self.freecad_gui.ActiveDocument
                else None
            )
            if view:
                # Get camera information
                camera = view.getCameraNode()
                if camera:
                    view_info["camera_type"] = (
                        "Perspective"
                        if camera.getField("heightAngle")
                        else "Orthographic"
                    )

                # Get view direction
                view_dir = view.getViewDirection()
                if view_dir:
                    view_info["view_direction"] = {
                        "x": round(view_dir.x, 3),
                        "y": round(view_dir.y, 3),
                        "z": round(view_dir.z, 3),
                    }
        except Exception:
            pass

        return view_info

    def _get_relevant_preferences(self) -> Dict[str, Any]:
        """Get relevant FreeCAD preferences."""
        if not self.freecad:
            return {}

        preferences = {}
        try:
            # Get units
            param_get = self.freecad.ParamGet(
                "User parameter:BaseApp/Preferences/Units"
            )
            if param_get:
                unit_system = param_get.GetInt("UserSchema", 0)
                unit_names = {
                    0: "Standard (mm/kg/s)",
                    1: "MKS (m/kg/s)",
                    2: "US customary",
                    3: "Imperial decimal",
                    4: "Building Euro",
                    5: "Building US",
                    6: "Metric small parts",
                    7: "Imperial for FEM",
                }
                preferences["units"] = unit_names.get(
                    unit_system, f"Custom ({unit_system})"
                )

            # Get precision settings
            param_get = self.freecad.ParamGet(
                "User parameter:BaseApp/Preferences/Units"
            )
            if param_get:
                preferences["decimal_places"] = param_get.GetInt("Decimals", 2)

        except Exception:
            pass

        return preferences

    def format_for_ai_prompt(self, include_full_details: bool = False) -> str:
        """Format CAD context for inclusion in AI prompts."""
        if include_full_details:
            context = self.get_full_context()
            return f"Current FreeCAD Context:\n{json.dumps(context, indent=2)}"
        else:
            return f"Current FreeCAD Context:\n{self.get_compact_context()}"


# Global instance
_context_extractor = None


def get_cad_context_extractor() -> CADContextExtractor:
    """Get the global CAD context extractor instance."""
    global _context_extractor
    if _context_extractor is None:
        _context_extractor = CADContextExtractor()
    return _context_extractor
