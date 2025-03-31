from typing import Dict, List, Any, Optional
import platform
import logging

logger = logging.getLogger(__name__)

class CADContextExtractor:
    """Extracts context information from FreeCAD."""
    
    def __init__(self, freecad_app=None):
        """
        Initialize the CAD context extractor.
        
        Args:
            freecad_app: Optional FreeCAD application instance. If None, will try to import FreeCAD.
        """
        self.app = freecad_app
        if self.app is None:
            try:
                import FreeCAD
                self.app = FreeCAD
                logger.info("Connected to FreeCAD")
            except ImportError:
                logger.warning("Could not import FreeCAD. Make sure it's installed and in your Python path.")
                self.app = None
        
    def extract_full_context(self) -> Dict[str, Any]:
        """Extract comprehensive context from the current FreeCAD state"""
        if self.app is None:
            return {"error": "FreeCAD not available"}
            
        context = {
            "application": self._extract_application_context(),
            "documents": self._extract_documents_context(),
            "active_document": self._extract_active_document_context(),
            "selection": self._extract_selection_context()
        }
        return context
        
    def _extract_application_context(self) -> Dict[str, Any]:
        """Extract information about the FreeCAD application"""
        if self.app is None:
            return {"error": "FreeCAD not available"}
            
        return {
            "version": self.app.Version,
            "build_type": getattr(self.app, "BuildVersionMajor", "Unknown"),
            "operating_system": platform.system(),
            "available_workbenches": list(self.app.getWorkbenches().keys()) if hasattr(self.app, "getWorkbenches") else []
        }
        
    def _extract_documents_context(self) -> List[Dict[str, Any]]:
        """Extract information about all open documents"""
        if self.app is None:
            return [{"error": "FreeCAD not available"}]
            
        docs = []
        for doc_name in self.app.listDocuments():
            doc = self.app.getDocument(doc_name)
            docs.append({
                "name": doc.Name,
                "label": doc.Label,
                "file": doc.FileName if hasattr(doc, "FileName") else None,
                "objects_count": len(doc.Objects),
                "modified": doc.Modified
            })
        return docs
        
    def _extract_active_document_context(self) -> Optional[Dict[str, Any]]:
        """Extract detailed information about the active document"""
        if self.app is None or self.app.ActiveDocument is None:
            return None
            
        doc = self.app.ActiveDocument
        return {
            "name": doc.Name,
            "label": doc.Label,
            "file": doc.FileName if hasattr(doc, "FileName") else None,
            "objects": self._extract_objects_context(doc),
            "object_hierarchy": self._extract_object_hierarchy(doc)
        }
        
    def _extract_objects_context(self, doc) -> List[Dict[str, Any]]:
        """Extract information about all objects in a document"""
        objects = []
        for obj in doc.Objects:
            objects.append({
                "id": obj.Name,
                "label": obj.Label,
                "type": obj.TypeId,
                "visibility": obj.Visibility,
                "properties": self._extract_object_properties(obj)
            })
        return objects
        
    def _extract_object_properties(self, obj) -> Dict[str, Any]:
        """Extract properties of an object"""
        properties = {}
        for prop in obj.PropertiesList:
            try:
                prop_type = obj.getTypeIdOfProperty(prop)
                prop_value = getattr(obj, prop)
                
                # Convert complex types to serializable format
                if hasattr(prop_value, "__dict__"):
                    prop_value = str(prop_value)
                    
                properties[prop] = {
                    "type": prop_type,
                    "value": prop_value
                }
            except Exception as e:
                # Skip properties that can't be serialized
                logger.debug(f"Could not extract property {prop} from {obj.Name}: {e}")
                
        return properties
        
    def _extract_object_hierarchy(self, doc) -> Dict[str, Any]:
        """Extract the hierarchical structure of objects in a document"""
        hierarchy = {}
        
        # Create a dictionary of all objects
        all_objects = {obj.Name: {
            "label": obj.Label,
            "type": obj.TypeId,
            "children": []
        } for obj in doc.Objects}
        
        # Identify parent-child relationships
        for obj in doc.Objects:
            # Check for Group property (used by many container objects)
            if hasattr(obj, "Group") and obj.Group:
                for child in obj.Group:
                    if child.Name in all_objects:
                        all_objects[obj.Name]["children"].append(child.Name)
        
        # Build the root level (objects with no parents)
        root_objects = []
        for obj_name, obj_data in all_objects.items():
            is_child = False
            for other_obj in all_objects.values():
                if obj_name in other_obj["children"]:
                    is_child = True
                    break
                    
            if not is_child:
                root_objects.append(obj_name)
                
        # Build the final hierarchy
        hierarchy = {
            "root": root_objects,
            "objects": all_objects
        }
        
        return hierarchy
        
    def _extract_selection_context(self) -> List[Dict[str, Any]]:
        """Extract information about the current selection"""
        if self.app is None or not hasattr(self.app, "Gui") or not hasattr(self.app.Gui, "Selection"):
            return []
            
        selection = []
        for obj in self.app.Gui.Selection.getSelection():
            selection.append({
                "id": obj.Name,
                "label": obj.Label,
                "type": obj.TypeId,
                "document": obj.Document.Name
            })
        return selection 