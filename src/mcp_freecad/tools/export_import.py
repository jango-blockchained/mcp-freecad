import logging
import os
import tempfile
from typing import Any, Dict, List, Optional

from ..tools.base import ToolProvider

logger = logging.getLogger(__name__)


class ExportImportToolProvider(ToolProvider):
    """Tool provider for importing and exporting CAD files in various formats."""

    # Supported export formats
    EXPORT_FORMATS = {
        "step": {
            "extension": ".step",
            "description": "STEP (ISO 10303-21) - Standard for Exchange of Product Data",
        },
        "stp": {
            "extension": ".stp",
            "description": "STP (ISO 10303-21) - Alternative extension for STEP",
        },
        "iges": {
            "extension": ".iges",
            "description": "IGES - Initial Graphics Exchange Specification",
        },
        "igs": {
            "extension": ".igs",
            "description": "IGS - Alternative extension for IGES",
        },
        "brep": {
            "extension": ".brep",
            "description": "BREP - Boundary representation file format",
        },
        "stl": {
            "extension": ".stl",
            "description": "STL - Stereolithography format for 3D printing",
        },
        "obj": {"extension": ".obj", "description": "OBJ - Wavefront 3D object file"},
        "dxf": {
            "extension": ".dxf",
            "description": "DXF - AutoCAD Drawing Exchange Format",
        },
        "wrl": {
            "extension": ".wrl",
            "description": "VRML - Virtual Reality Modeling Language",
        },
        "vrml": {
            "extension": ".vrml",
            "description": "VRML - Alternative extension for VRML",
        },
        "fcstd": {
            "extension": ".FCStd",
            "description": "FCStd - Native FreeCAD format",
        },
    }

    # Supported import formats
    IMPORT_FORMATS = {
        "step": {
            "extension": ".step",
            "description": "STEP (ISO 10303-21) - Standard for Exchange of Product Data",
        },
        "stp": {
            "extension": ".stp",
            "description": "STP (ISO 10303-21) - Alternative extension for STEP",
        },
        "iges": {
            "extension": ".iges",
            "description": "IGES - Initial Graphics Exchange Specification",
        },
        "igs": {
            "extension": ".igs",
            "description": "IGS - Alternative extension for IGES",
        },
        "brep": {
            "extension": ".brep",
            "description": "BREP - Boundary representation file format",
        },
        "stl": {
            "extension": ".stl",
            "description": "STL - Stereolithography format for 3D printing",
        },
        "obj": {"extension": ".obj", "description": "OBJ - Wavefront 3D object file"},
        "dxf": {
            "extension": ".dxf",
            "description": "DXF - AutoCAD Drawing Exchange Format",
        },
        "wrl": {
            "extension": ".wrl",
            "description": "VRML - Virtual Reality Modeling Language",
        },
        "fcstd": {
            "extension": ".FCStd",
            "description": "FCStd - Native FreeCAD format",
        },
    }

    def __init__(self, freecad_app=None):
        """
        Initialize the export/import tool provider.

        Args:
            freecad_app: Optional FreeCAD application instance. If None, will try to import FreeCAD.
        """
        self.app = freecad_app

        if self.app is None:
            try:
                import FreeCAD

                self.app = FreeCAD
                logger.info("Connected to FreeCAD for export/import operations")
            except ImportError:
                logger.warning(
                    "Could not import FreeCAD. Make sure it's installed and in your Python path."
                )
                self.app = None

    async def execute_tool(
        self, tool_id: str, params: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Execute an export/import tool.

        Args:
            tool_id: The ID of the tool to execute
            params: The parameters for the tool

        Returns:
            The result of the tool execution
        """
        logger.info(f"Executing export/import tool: {tool_id}")

        # Check if FreeCAD is available
        if self.app is None:
            return {
                "status": "error",
                "message": "FreeCAD is not available. Cannot execute export/import tool.",
                "mock": True,
            }

        # Handle different tools
        if tool_id == "export":
            return await self._export_file(params)
        elif tool_id == "import":
            return await self._import_file(params)
        elif tool_id == "list_formats":
            return await self._list_formats(params)
        elif tool_id == "convert":
            return await self._convert_file(params)
        else:
            logger.error(f"Unknown tool ID: {tool_id}")
            return {"status": "error", "message": f"Unknown tool ID: {tool_id}"}

    async def _export_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Export objects to a file in the specified format."""
        try:
            # Get required parameters
            format_name = params.get("format")
            if not format_name:
                return {"status": "error", "message": "No export format specified"}

            output_path = params.get("output_path")
            if not output_path:
                return {"status": "error", "message": "No output path specified"}

            # Validate the format
            format_name = format_name.lower()
            if format_name not in self.EXPORT_FORMATS:
                return {
                    "status": "error",
                    "message": f"Unsupported export format: {format_name}",
                    "supported_formats": list(self.EXPORT_FORMATS.keys()),
                }

            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"status": "error", "message": "No active document to export"}

            # Get objects to export (optional, if not specified, export all)
            object_names = params.get("objects", [])
            objects = []

            if object_names:
                # Export specific objects
                for name in object_names:
                    obj = doc.getObject(name)
                    if obj:
                        objects.append(obj)
                    else:
                        return {
                            "status": "error",
                            "message": f"Object not found: {name}",
                        }
            else:
                # Export all objects
                objects = doc.Objects

            if not objects:
                return {"status": "error", "message": "No objects to export"}

            # Ensure the output path has the correct extension
            format_info = self.EXPORT_FORMATS[format_name]
            extension = format_info["extension"]

            if not output_path.lower().endswith(extension.lower()):
                output_path += extension

            # Execute the appropriate export function based on format
            if format_name in ["step", "stp"]:
                # Export to STEP format
                import Part

                Part.export(objects, output_path)

            elif format_name in ["iges", "igs"]:
                # Export to IGES format
                import Part

                Part.export(objects, output_path)

            elif format_name == "stl":
                # Export to STL format
                import Mesh

                shapes = [obj.Shape for obj in objects if hasattr(obj, "Shape")]
                if not shapes:
                    return {"status": "error", "message": "No shapes to export to STL"}

                mesh = Mesh.Mesh()
                for shape in shapes:
                    mesh_data = Mesh.Mesh(
                        shape.tessellate(params.get("tessellation", 1.0))
                    )
                    mesh.addMesh(mesh_data)

                mesh.write(output_path)

            elif format_name == "obj":
                # Export to OBJ format
                import Mesh

                shapes = [obj.Shape for obj in objects if hasattr(obj, "Shape")]
                if not shapes:
                    return {"status": "error", "message": "No shapes to export to OBJ"}

                mesh = Mesh.Mesh()
                for shape in shapes:
                    mesh_data = Mesh.Mesh(
                        shape.tessellate(params.get("tessellation", 1.0))
                    )
                    mesh.addMesh(mesh_data)

                mesh.write(output_path)

            elif format_name == "brep":
                # Export to BREP format
                shapes = [obj.Shape for obj in objects if hasattr(obj, "Shape")]
                if not shapes:
                    return {"status": "error", "message": "No shapes to export to BREP"}

                if len(shapes) == 1:
                    # Single shape export
                    shapes[0].exportBrep(output_path)
                else:
                    # Multiple shapes, export as compound
                    import Part

                    compound = Part.Compound(shapes)
                    compound.exportBrep(output_path)

            elif format_name == "fcstd":
                # Save as FreeCAD document
                doc.saveAs(output_path)

            elif format_name in ["dxf", "wrl", "vrml"]:
                # Use the exporter from the importers directory
                exporter_name = "Import" + format_name.upper()
                try:
                    exporter = __import__(exporter_name)
                    exporter.export(objects, output_path)
                except ImportError:
                    return {
                        "status": "error",
                        "message": f"Export module not found: {exporter_name}",
                    }

            return {
                "status": "success",
                "message": f"Objects exported to {format_name.upper()} file: {output_path}",
                "format": format_name,
                "output_path": output_path,
                "object_count": len(objects),
            }

        except Exception as e:
            logger.error(f"Error exporting file: {e}")
            return {"status": "error", "message": f"Error exporting file: {str(e)}"}

    async def _import_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Import a file in the specified format."""
        try:
            # Get required parameters
            file_path = params.get("file_path")
            if not file_path:
                return {"status": "error", "message": "No file path specified"}

            # Determine the format based on file extension if not explicitly specified
            format_name = params.get("format")
            if not format_name:
                _, ext = os.path.splitext(file_path)
                ext = ext.lower()

                # Find matching format
                for fmt, info in self.IMPORT_FORMATS.items():
                    if info["extension"].lower() == ext:
                        format_name = fmt
                        break

                if not format_name:
                    return {
                        "status": "error",
                        "message": f"Unsupported file extension: {ext}",
                        "supported_formats": list(self.IMPORT_FORMATS.keys()),
                    }
            else:
                format_name = format_name.lower()
                if format_name not in self.IMPORT_FORMATS:
                    return {
                        "status": "error",
                        "message": f"Unsupported import format: {format_name}",
                        "supported_formats": list(self.IMPORT_FORMATS.keys()),
                    }

            # Create a new document if none exists or if requested
            doc = self.app.ActiveDocument
            if not doc or params.get("create_new_document", False):
                doc_name = params.get("document_name", "Imported")
                doc = self.app.newDocument(doc_name)

            # Execute the appropriate import function based on format
            objects_before = len(doc.Objects)

            if format_name in ["step", "stp"]:
                # Import STEP file
                import ImportGui

                ImportGui.insert(file_path, doc.Name)

            elif format_name in ["iges", "igs"]:
                # Import IGES file
                import ImportGui

                ImportGui.insert(file_path, doc.Name)

            elif format_name == "stl":
                # Import STL file
                import Mesh

                Mesh.insert(file_path, doc.Name)

            elif format_name == "obj":
                # Import OBJ file
                import Mesh

                Mesh.insert(file_path, doc.Name)

            elif format_name == "brep":
                # Import BREP file
                import Part

                shape = Part.Shape()
                shape.read(file_path)
                Part.show(shape)

            elif format_name == "fcstd":
                # Open FreeCAD document
                self.app.openDocument(file_path)
                # In this case, we need to get the newly opened document
                doc = self.app.getDocument(
                    os.path.splitext(os.path.basename(file_path))[0]
                )

            elif format_name == "dxf":
                # Import DXF file
                import ImportDXF

                ImportDXF.open(file_path, doc.Name)

            # Recompute the document
            doc.recompute()

            # Check what objects were imported
            objects_after = len(doc.Objects)
            new_objects = objects_after - objects_before

            return {
                "status": "success",
                "message": f"File imported from {format_name.upper()} format: {file_path}",
                "format": format_name,
                "file_path": file_path,
                "document": doc.Name,
                "new_objects": new_objects,
            }

        except Exception as e:
            logger.error(f"Error importing file: {e}")
            return {"status": "error", "message": f"Error importing file: {str(e)}"}

    async def _list_formats(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List supported import and export formats."""
        try:
            # Check which type of formats to list
            format_type = params.get("type", "all").lower()

            result = {"status": "success"}

            if format_type in ["export", "all"]:
                result["export_formats"] = self.EXPORT_FORMATS

            if format_type in ["import", "all"]:
                result["import_formats"] = self.IMPORT_FORMATS

            return result

        except Exception as e:
            logger.error(f"Error listing formats: {e}")
            return {"status": "error", "message": f"Error listing formats: {str(e)}"}

    async def _convert_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Convert a file from one format to another."""
        try:
            # Get required parameters
            input_path = params.get("input_path")
            if not input_path:
                return {"status": "error", "message": "No input path specified"}

            output_path = params.get("output_path")
            if not output_path:
                return {"status": "error", "message": "No output path specified"}

            # Determine the input format based on file extension if not explicitly specified
            input_format = params.get("input_format")
            if not input_format:
                _, ext = os.path.splitext(input_path)
                ext = ext.lower()

                # Find matching format
                for fmt, info in self.IMPORT_FORMATS.items():
                    if info["extension"].lower() == ext:
                        input_format = fmt
                        break

                if not input_format:
                    return {
                        "status": "error",
                        "message": f"Unsupported input file extension: {ext}",
                        "supported_formats": list(self.IMPORT_FORMATS.keys()),
                    }
            else:
                input_format = input_format.lower()
                if input_format not in self.IMPORT_FORMATS:
                    return {
                        "status": "error",
                        "message": f"Unsupported input format: {input_format}",
                        "supported_formats": list(self.IMPORT_FORMATS.keys()),
                    }

            # Determine the output format based on file extension if not explicitly specified
            output_format = params.get("output_format")
            if not output_format:
                _, ext = os.path.splitext(output_path)
                ext = ext.lower()

                # Find matching format
                for fmt, info in self.EXPORT_FORMATS.items():
                    if info["extension"].lower() == ext:
                        output_format = fmt
                        break

                if not output_format:
                    return {
                        "status": "error",
                        "message": f"Unsupported output file extension: {ext}",
                        "supported_formats": list(self.EXPORT_FORMATS.keys()),
                    }
            else:
                output_format = output_format.lower()
                if output_format not in self.EXPORT_FORMATS:
                    return {
                        "status": "error",
                        "message": f"Unsupported output format: {output_format}",
                        "supported_formats": list(self.EXPORT_FORMATS.keys()),
                    }

            # Create a temporary document for the conversion
            doc_name = "TempConversion"
            if doc_name in self.app.listDocuments():
                # Close existing document with this name
                self.app.closeDocument(doc_name)

            doc = self.app.newDocument(doc_name)

            # Import the input file
            import_result = await self._import_file(
                {
                    "file_path": input_path,
                    "format": input_format,
                    "document_name": doc_name,
                }
            )

            if import_result["status"] != "success":
                return import_result

            # Export to the output file
            export_result = await self._export_file(
                {"format": output_format, "output_path": output_path}
            )

            # Close the temporary document
            self.app.closeDocument(doc_name)

            if export_result["status"] != "success":
                return export_result

            return {
                "status": "success",
                "message": f"File converted from {input_format.upper()} to {output_format.upper()}",
                "input_format": input_format,
                "input_path": input_path,
                "output_format": output_format,
                "output_path": output_path,
            }

        except Exception as e:
            logger.error(f"Error converting file: {e}")
            return {"status": "error", "message": f"Error converting file: {str(e)}"}
