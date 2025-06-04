"""
Export/Import Tool

MCP tool for exporting and importing various file formats in FreeCAD,
including STL, STEP, IGES, OBJ, and others.

Author: jango-blockchained
"""

import FreeCAD as App
import Part
import Mesh
import os
from typing import Dict, Any, List, Optional, Union


class ExportImportTool:
    """Tool for exporting and importing various file formats."""

    def __init__(self):
        """Initialize the export/import tool."""
        self.name = "export_import"
        self.description = "Export and import various file formats"

        # Supported formats with their extensions and descriptions
        self.export_formats = {
            "stl": {"ext": ".stl", "desc": "STL mesh format for 3D printing"},
            "step": {"ext": ".step", "desc": "STEP format for CAD exchange"},
            "stp": {"ext": ".stp", "desc": "STEP format (alternative extension)"},
            "iges": {"ext": ".iges", "desc": "IGES format for CAD exchange"},
            "igs": {"ext": ".igs", "desc": "IGES format (alternative extension)"},
            "obj": {"ext": ".obj", "desc": "Wavefront OBJ format"},
            "dae": {"ext": ".dae", "desc": "COLLADA format"},
            "brep": {"ext": ".brep", "desc": "OpenCASCADE native format"},
            "fcstd": {"ext": ".fcstd", "desc": "FreeCAD native format"}
        }

        self.import_formats = {
            "stl": {"ext": ".stl", "desc": "STL mesh format"},
            "step": {"ext": ".step", "desc": "STEP format"},
            "stp": {"ext": ".stp", "desc": "STEP format"},
            "iges": {"ext": ".iges", "desc": "IGES format"},
            "igs": {"ext": ".igs", "desc": "IGES format"},
            "obj": {"ext": ".obj", "desc": "Wavefront OBJ format"},
            "dae": {"ext": ".dae", "desc": "COLLADA format"},
            "brep": {"ext": ".brep", "desc": "OpenCASCADE format"},
            "fcstd": {"ext": ".fcstd", "desc": "FreeCAD native format"}
        }

    def _get_object(self, obj_name: str, doc: Any = None) -> Optional[Any]:
        """Get an object by name from the document.

        Args:
            obj_name: Name of the object to find
            doc: Document to search in (uses ActiveDocument if None)

        Returns:
            The FreeCAD object or None if not found
        """
        if doc is None:
            doc = App.ActiveDocument
        if not doc:
            return None

        return doc.getObject(obj_name)

    def _get_objects_to_export(self, object_names: List[str] = None, doc: Any = None) -> List[Any]:
        """Get objects to export based on names or all objects if none specified.

        Args:
            object_names: List of object names to export (None = all objects)
            doc: Document to export from

        Returns:
            List of FreeCAD objects
        """
        if doc is None:
            doc = App.ActiveDocument
        if not doc:
            return []

        if object_names:
            objects = []
            for name in object_names:
                obj = self._get_object(name, doc)
                if obj and hasattr(obj, 'Shape'):
                    objects.append(obj)
            return objects
        else:
            # Return all objects with shapes
            return [obj for obj in doc.Objects if hasattr(obj, 'Shape') and obj.Shape]

    def _ensure_directory(self, filepath: str) -> bool:
        """Ensure the directory for the filepath exists.

        Args:
            filepath: Path to file

        Returns:
            True if directory exists or was created
        """
        try:
            directory = os.path.dirname(filepath)
            if directory and not os.path.exists(directory):
                os.makedirs(directory)
            return True
        except Exception:
            return False

    def export_stl(self, filepath: str, object_names: List[str] = None,
                   ascii: bool = False, max_deviation: float = 0.1) -> Dict[str, Any]:
        """Export objects to STL format.

        Args:
            filepath: Path for the output STL file
            object_names: List of object names to export (None = all)
            ascii: If True, save as ASCII STL; if False, save as binary
            max_deviation: Maximum deviation for mesh tessellation in mm

        Returns:
            Dictionary with export result
        """
        try:
            doc = App.ActiveDocument
            if not doc:
                return {
                    "success": False,
                    "error": "No active document",
                    "message": "No active document to export from"
                }

            # Get objects to export
            objects = self._get_objects_to_export(object_names, doc)
            if not objects:
                return {
                    "success": False,
                    "error": "No objects",
                    "message": "No valid objects found to export"
                }

            # Ensure directory exists
            if not self._ensure_directory(filepath):
                return {
                    "success": False,
                    "error": "Directory error",
                    "message": f"Could not create directory for {filepath}"
                }

            # Create mesh from shapes
            meshes = []
            for obj in objects:
                if hasattr(obj, 'Shape') and obj.Shape:
                    mesh = Mesh.Mesh()
                    mesh.addFacets(obj.Shape.tessellate(max_deviation))
                    meshes.append(mesh)

            if not meshes:
                return {
                    "success": False,
                    "error": "No meshes",
                    "message": "Could not create meshes from objects"
                }

            # Combine meshes
            combined_mesh = Mesh.Mesh()
            for mesh in meshes:
                combined_mesh.addMesh(mesh)

            # Export to STL
            if ascii:
                combined_mesh.write(filepath, "AST")
            else:
                combined_mesh.write(filepath)

            # Get file size
            file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0

            return {
                "success": True,
                "message": f"Successfully exported {len(objects)} object(s) to STL",
                "filepath": filepath,
                "properties": {
                    "num_objects": len(objects),
                    "format": "ASCII STL" if ascii else "Binary STL",
                    "file_size_bytes": file_size,
                    "file_size_mb": round(file_size / (1024 * 1024), 2),
                    "max_deviation": max_deviation,
                    "facet_count": combined_mesh.CountFacets
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to export STL: {str(e)}"
            }

    def export_step(self, filepath: str, object_names: List[str] = None) -> Dict[str, Any]:
        """Export objects to STEP format.

        Args:
            filepath: Path for the output STEP file
            object_names: List of object names to export (None = all)

        Returns:
            Dictionary with export result
        """
        try:
            doc = App.ActiveDocument
            if not doc:
                return {
                    "success": False,
                    "error": "No active document",
                    "message": "No active document to export from"
                }

            # Get objects to export
            objects = self._get_objects_to_export(object_names, doc)
            if not objects:
                return {
                    "success": False,
                    "error": "No objects",
                    "message": "No valid objects found to export"
                }

            # Ensure directory exists
            if not self._ensure_directory(filepath):
                return {
                    "success": False,
                    "error": "Directory error",
                    "message": f"Could not create directory for {filepath}"
                }

            # Get shapes
            shapes = [obj.Shape for obj in objects if hasattr(obj, 'Shape') and obj.Shape]

            if len(shapes) == 1:
                # Single shape
                shapes[0].exportStep(filepath)
            else:
                # Multiple shapes - create compound
                compound = Part.makeCompound(shapes)
                compound.exportStep(filepath)

            # Get file size
            file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0

            return {
                "success": True,
                "message": f"Successfully exported {len(objects)} object(s) to STEP",
                "filepath": filepath,
                "properties": {
                    "num_objects": len(objects),
                    "format": "STEP AP214",
                    "file_size_bytes": file_size,
                    "file_size_mb": round(file_size / (1024 * 1024), 2)
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to export STEP: {str(e)}"
            }

    def export_iges(self, filepath: str, object_names: List[str] = None) -> Dict[str, Any]:
        """Export objects to IGES format.

        Args:
            filepath: Path for the output IGES file
            object_names: List of object names to export (None = all)

        Returns:
            Dictionary with export result
        """
        try:
            doc = App.ActiveDocument
            if not doc:
                return {
                    "success": False,
                    "error": "No active document",
                    "message": "No active document to export from"
                }

            # Get objects to export
            objects = self._get_objects_to_export(object_names, doc)
            if not objects:
                return {
                    "success": False,
                    "error": "No objects",
                    "message": "No valid objects found to export"
                }

            # Ensure directory exists
            if not self._ensure_directory(filepath):
                return {
                    "success": False,
                    "error": "Directory error",
                    "message": f"Could not create directory for {filepath}"
                }

            # Get shapes
            shapes = [obj.Shape for obj in objects if hasattr(obj, 'Shape') and obj.Shape]

            if len(shapes) == 1:
                # Single shape
                shapes[0].exportIges(filepath)
            else:
                # Multiple shapes - create compound
                compound = Part.makeCompound(shapes)
                compound.exportIges(filepath)

            # Get file size
            file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0

            return {
                "success": True,
                "message": f"Successfully exported {len(objects)} object(s) to IGES",
                "filepath": filepath,
                "properties": {
                    "num_objects": len(objects),
                    "format": "IGES 5.3",
                    "file_size_bytes": file_size,
                    "file_size_mb": round(file_size / (1024 * 1024), 2)
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to export IGES: {str(e)}"
            }

    def export_brep(self, filepath: str, object_names: List[str] = None) -> Dict[str, Any]:
        """Export objects to BREP (OpenCASCADE) format.

        Args:
            filepath: Path for the output BREP file
            object_names: List of object names to export (None = all)

        Returns:
            Dictionary with export result
        """
        try:
            doc = App.ActiveDocument
            if not doc:
                return {
                    "success": False,
                    "error": "No active document",
                    "message": "No active document to export from"
                }

            # Get objects to export
            objects = self._get_objects_to_export(object_names, doc)
            if not objects:
                return {
                    "success": False,
                    "error": "No objects",
                    "message": "No valid objects found to export"
                }

            # Ensure directory exists
            if not self._ensure_directory(filepath):
                return {
                    "success": False,
                    "error": "Directory error",
                    "message": f"Could not create directory for {filepath}"
                }

            # Get shapes
            shapes = [obj.Shape for obj in objects if hasattr(obj, 'Shape') and obj.Shape]

            if len(shapes) == 1:
                # Single shape
                shapes[0].exportBrep(filepath)
            else:
                # Multiple shapes - create compound
                compound = Part.makeCompound(shapes)
                compound.exportBrep(filepath)

            # Get file size
            file_size = os.path.getsize(filepath) if os.path.exists(filepath) else 0

            return {
                "success": True,
                "message": f"Successfully exported {len(objects)} object(s) to BREP",
                "filepath": filepath,
                "properties": {
                    "num_objects": len(objects),
                    "format": "OpenCASCADE BREP",
                    "file_size_bytes": file_size,
                    "file_size_mb": round(file_size / (1024 * 1024), 2)
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to export BREP: {str(e)}"
            }

    def import_stl(self, filepath: str, object_name: str = None) -> Dict[str, Any]:
        """Import STL file into FreeCAD.

        Args:
            filepath: Path to the STL file to import
            object_name: Optional name for the imported object

        Returns:
            Dictionary with import result
        """
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                return {
                    "success": False,
                    "error": "File not found",
                    "message": f"STL file not found: {filepath}"
                }

            # Get or create document
            doc = App.ActiveDocument
            if not doc:
                doc = App.newDocument("Imported")

            # Import STL
            mesh = Mesh.read(filepath)

            # Create mesh object
            name = object_name or os.path.splitext(os.path.basename(filepath))[0]
            mesh_obj = doc.addObject("Mesh::Feature", name)
            mesh_obj.Mesh = mesh
            mesh_obj.Label = name

            # Get mesh properties
            volume = mesh.Volume if hasattr(mesh, 'Volume') else 0
            area = mesh.Area if hasattr(mesh, 'Area') else 0

            # Recompute document
            doc.recompute()

            return {
                "success": True,
                "object_name": mesh_obj.Name,
                "label": mesh_obj.Label,
                "message": f"Successfully imported STL file",
                "filepath": filepath,
                "properties": {
                    "facet_count": mesh.CountFacets,
                    "point_count": mesh.CountPoints,
                    "volume": round(volume, 2),
                    "area": round(area, 2),
                    "file_size_bytes": os.path.getsize(filepath)
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to import STL: {str(e)}"
            }

    def import_step(self, filepath: str, object_name: str = None) -> Dict[str, Any]:
        """Import STEP file into FreeCAD.

        Args:
            filepath: Path to the STEP file to import
            object_name: Optional name for the imported object

        Returns:
            Dictionary with import result
        """
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                return {
                    "success": False,
                    "error": "File not found",
                    "message": f"STEP file not found: {filepath}"
                }

            # Get or create document
            doc = App.ActiveDocument
            if not doc:
                doc = App.newDocument("Imported")

            # Import STEP
            shape = Part.Shape()
            shape.read(filepath)

            # Create object
            name = object_name or os.path.splitext(os.path.basename(filepath))[0]
            obj = doc.addObject("Part::Feature", name)
            obj.Shape = shape
            obj.Label = name

            # Recompute document
            doc.recompute()

            return {
                "success": True,
                "object_name": obj.Name,
                "label": obj.Label,
                "message": f"Successfully imported STEP file",
                "filepath": filepath,
                "properties": {
                    "volume": round(shape.Volume, 2),
                    "area": round(shape.Area, 2),
                    "is_solid": shape.isSolid(),
                    "is_closed": shape.isClosed(),
                    "num_faces": len(shape.Faces),
                    "num_edges": len(shape.Edges),
                    "file_size_bytes": os.path.getsize(filepath)
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to import STEP: {str(e)}"
            }

    def import_iges(self, filepath: str, object_name: str = None) -> Dict[str, Any]:
        """Import IGES file into FreeCAD.

        Args:
            filepath: Path to the IGES file to import
            object_name: Optional name for the imported object

        Returns:
            Dictionary with import result
        """
        try:
            # Check if file exists
            if not os.path.exists(filepath):
                return {
                    "success": False,
                    "error": "File not found",
                    "message": f"IGES file not found: {filepath}"
                }

            # Get or create document
            doc = App.ActiveDocument
            if not doc:
                doc = App.newDocument("Imported")

            # Import IGES
            shape = Part.Shape()
            shape.read(filepath)

            # Create object
            name = object_name or os.path.splitext(os.path.basename(filepath))[0]
            obj = doc.addObject("Part::Feature", name)
            obj.Shape = shape
            obj.Label = name

            # Recompute document
            doc.recompute()

            return {
                "success": True,
                "object_name": obj.Name,
                "label": obj.Label,
                "message": f"Successfully imported IGES file",
                "filepath": filepath,
                "properties": {
                    "volume": round(shape.Volume, 2),
                    "area": round(shape.Area, 2),
                    "is_solid": shape.isSolid(),
                    "is_closed": shape.isClosed(),
                    "num_faces": len(shape.Faces),
                    "num_edges": len(shape.Edges),
                    "file_size_bytes": os.path.getsize(filepath)
                }
            }

        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "message": f"Failed to import IGES: {str(e)}"
            }

    def export_format(self, filepath: str, format: str, object_names: List[str] = None,
                     **kwargs) -> Dict[str, Any]:
        """Export objects to specified format.

        Args:
            filepath: Path for the output file
            format: Export format (stl, step, iges, brep, etc.)
            object_names: List of object names to export (None = all)
            **kwargs: Format-specific options

        Returns:
            Dictionary with export result
        """
        format_lower = format.lower()

        if format_lower in ["stl"]:
            return self.export_stl(filepath, object_names, **kwargs)
        elif format_lower in ["step", "stp"]:
            return self.export_step(filepath, object_names)
        elif format_lower in ["iges", "igs"]:
            return self.export_iges(filepath, object_names)
        elif format_lower in ["brep"]:
            return self.export_brep(filepath, object_names)
        else:
            return {
                "success": False,
                "error": "Unsupported format",
                "message": f"Export format '{format}' is not supported",
                "supported_formats": list(self.export_formats.keys())
            }

    def import_format(self, filepath: str, format: str = None, object_name: str = None) -> Dict[str, Any]:
        """Import file of specified format.

        Args:
            filepath: Path to the file to import
            format: Import format (auto-detected from extension if None)
            object_name: Optional name for the imported object

        Returns:
            Dictionary with import result
        """
        # Auto-detect format from extension if not specified
        if format is None:
            ext = os.path.splitext(filepath)[1].lower()
            format = ext[1:] if ext else ""

        format_lower = format.lower()

        if format_lower in ["stl"]:
            return self.import_stl(filepath, object_name)
        elif format_lower in ["step", "stp"]:
            return self.import_step(filepath, object_name)
        elif format_lower in ["iges", "igs"]:
            return self.import_iges(filepath, object_name)
        else:
            return {
                "success": False,
                "error": "Unsupported format",
                "message": f"Import format '{format}' is not supported",
                "supported_formats": list(self.import_formats.keys())
            }

    def get_supported_formats(self) -> Dict[str, Any]:
        """Get list of supported export/import formats.

        Returns:
            Dictionary with supported formats
        """
        return {
            "export_formats": self.export_formats,
            "import_formats": self.import_formats,
            "info": {
                "recommended_3d_print": "STL",
                "recommended_cad_exchange": "STEP",
                "native_format": "FCStd"
            }
        }
