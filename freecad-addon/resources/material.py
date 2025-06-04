import logging
import os
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse

from .base import ResourceProvider

logger = logging.getLogger(__name__)


class MaterialResourceProvider(ResourceProvider):
    """Resource provider for materials in CAD models."""

    def __init__(self, freecad_app=None):
        """
        Initialize the material resource provider.

        Args:
            freecad_app: Optional FreeCAD application instance. If None, will try to import FreeCAD.
        """
        # self.extractor = CADContextExtractor(freecad_app)  # Not needed for material resources
        self.app = freecad_app
        self._materials_cache = None

        if self.app is None:
            try:
                import FreeCAD

                self.app = FreeCAD
                logger.info("Connected to FreeCAD for material data")
            except ImportError:
                logger.warning(
                    "Could not import FreeCAD. Make sure it's installed and in your Python path."
                )
                self.app = None

    async def get_resource(
        self, uri: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Retrieve material data from the CAD model.

        Args:
            uri: The resource URI in format "cad://materials/[resource_type]/[object_name]"
            params: Optional parameters for the material request

        Returns:
            The material data
        """
        logger.info(f"Retrieving material resource: {uri}")

        # Parse the URI
        parsed_uri = urlparse(uri)

        if parsed_uri.scheme != "cad":
            raise ValueError(f"Invalid URI scheme: {parsed_uri.scheme}, expected 'cad'")

        path_parts = parsed_uri.path.strip("/").split("/")

        if len(path_parts) < 1 or path_parts[0] != "materials":
            raise ValueError(
                f"Invalid URI format: {uri}, expected 'cad://materials/...'"
            )

        # Handle different resource types
        if len(path_parts) == 1:
            # Return list of available materials
            return await self._get_available_materials()

        resource_type = path_parts[1]

        if resource_type == "library":
            # Return materials from the material library
            return await self._get_material_library()
        elif resource_type == "object":
            # Return material assigned to a specific object
            if len(path_parts) < 3:
                return {"error": "No object specified"}
            return await self._get_object_material(path_parts[2])
        elif resource_type == "info":
            # Return detailed information about a specific material
            if len(path_parts) < 3:
                return {"error": "No material specified"}
            return await self._get_material_info(path_parts[2])
        else:
            raise ValueError(f"Unknown resource type: {resource_type}")

    async def _get_available_materials(self) -> Dict[str, Any]:
        """Get list of all available materials."""
        if self.app is None:
            return self._mock_available_materials()

        try:
            # Cache materials if not already done
            if self._materials_cache is None:
                self._materials_cache = self._load_material_library()

            # Create a list of material names and categories
            materials = []
            for material_name, material_data in self._materials_cache.items():
                materials.append(
                    {
                        "name": material_name,
                        "category": material_data.get("category", "Unknown"),
                        "description": material_data.get("description", ""),
                    }
                )

            return {
                "resource_type": "materials",
                "count": len(materials),
                "materials": materials,
            }

        except Exception as e:
            logger.error(f"Error getting available materials: {e}")
            return {"error": f"Error getting available materials: {str(e)}"}

    def _mock_available_materials(self) -> Dict[str, Any]:
        """Provide mock material data when FreeCAD is not available."""
        return {
            "resource_type": "materials",
            "count": 5,
            "materials": [
                {
                    "name": "Steel",
                    "category": "Metal",
                    "description": "Standard steel material",
                },
                {
                    "name": "Aluminum",
                    "category": "Metal",
                    "description": "Standard aluminum alloy",
                },
                {
                    "name": "PLA",
                    "category": "Plastic",
                    "description": "Standard PLA plastic for 3D printing",
                },
                {
                    "name": "Wood",
                    "category": "Natural",
                    "description": "Generic wood material",
                },
                {
                    "name": "Glass",
                    "category": "Ceramic",
                    "description": "Standard glass material",
                },
            ],
            "note": "Mock data (FreeCAD not available)",
        }

    async def _get_material_library(self) -> Dict[str, Any]:
        """Get the full material library structure."""
        if self.app is None:
            return self._mock_material_library()

        try:
            # Cache materials if not already done
            if self._materials_cache is None:
                self._materials_cache = self._load_material_library()

            # Organize materials by category
            categories = {}
            for material_name, material_data in self._materials_cache.items():
                category = material_data.get("category", "Unknown")

                if category not in categories:
                    categories[category] = []

                categories[category].append(
                    {
                        "name": material_name,
                        "description": material_data.get("description", ""),
                    }
                )

            return {
                "resource_type": "material_library",
                "categories": [
                    {"name": category, "materials": materials}
                    for category, materials in categories.items()
                ],
            }

        except Exception as e:
            logger.error(f"Error getting material library: {e}")
            return {"error": f"Error getting material library: {str(e)}"}

    def _mock_material_library(self) -> Dict[str, Any]:
        """Provide mock material library when FreeCAD is not available."""
        return {
            "resource_type": "material_library",
            "categories": [
                {
                    "name": "Metal",
                    "materials": [
                        {"name": "Steel", "description": "Standard steel material"},
                        {"name": "Aluminum", "description": "Standard aluminum alloy"},
                        {"name": "Copper", "description": "Standard copper material"},
                    ],
                },
                {
                    "name": "Plastic",
                    "materials": [
                        {
                            "name": "PLA",
                            "description": "Standard PLA plastic for 3D printing",
                        },
                        {
                            "name": "ABS",
                            "description": "Acrylonitrile Butadiene Styrene plastic",
                        },
                    ],
                },
                {
                    "name": "Natural",
                    "materials": [
                        {"name": "Wood", "description": "Generic wood material"}
                    ],
                },
                {
                    "name": "Ceramic",
                    "materials": [
                        {"name": "Glass", "description": "Standard glass material"}
                    ],
                },
            ],
            "note": "Mock data (FreeCAD not available)",
        }

    async def _get_object_material(self, object_name: str) -> Dict[str, Any]:
        """Get material assigned to a specific object."""
        if self.app is None:
            return self._mock_object_material(object_name)

        try:
            # Get the active document
            doc = self.app.ActiveDocument
            if not doc:
                return {"error": "No active document"}

            # Get the object
            obj = doc.getObject(object_name)

            if not obj:
                return {"error": f"Object not found: {object_name}"}

            # Check if object has material
            material_obj = None

            # In FreeCAD, material can be attached in different ways depending on the workbench
            # This is a simplified approach

            # Check Material property
            if hasattr(obj, "Material") and obj.Material:
                material_obj = obj.Material

            # Check for material group link
            elif hasattr(obj, "MaterialList") and obj.MaterialList:
                material_obj = obj.MaterialList[0] if obj.MaterialList else None

            # If no material found
            if not material_obj:
                return {
                    "resource_type": "object_material",
                    "object": object_name,
                    "has_material": False,
                }

            # Get material properties
            material_props = {}
            if hasattr(material_obj, "Material") and material_obj.Material:
                material_card = material_obj.Material

                for key, value in material_card.items():
                    material_props[key] = value

            return {
                "resource_type": "object_material",
                "object": object_name,
                "has_material": True,
                "material_name": material_obj.Label,
                "properties": material_props,
            }

        except Exception as e:
            logger.error(f"Error getting object material: {e}")
            return {"error": f"Error getting object material: {str(e)}"}

    def _mock_object_material(self, object_name: str) -> Dict[str, Any]:
        """Provide mock object material data when FreeCAD is not available."""
        # Simulate having material for some object names
        has_material = object_name.lower() in ["box001", "cylinder001", "part001"]

        if not has_material:
            return {
                "resource_type": "object_material",
                "object": object_name,
                "has_material": False,
                "note": "Mock data (FreeCAD not available)",
            }

        # Mock material data
        return {
            "resource_type": "object_material",
            "object": object_name,
            "has_material": True,
            "material_name": "Steel",
            "properties": {
                "Density": "7900 kg/m^3",
                "YoungModulus": "210000 MPa",
                "PoissonRatio": "0.3",
                "Color": "0.4, 0.4, 0.4",
                "ThermalConductivity": "50 W/m/K",
                "ThermalExpansionCoefficient": "12 µm/m/K",
            },
            "note": "Mock data (FreeCAD not available)",
        }

    async def _get_material_info(self, material_name: str) -> Dict[str, Any]:
        """Get detailed information about a specific material."""
        if self.app is None:
            return self._mock_material_info(material_name)

        try:
            # Cache materials if not already done
            if self._materials_cache is None:
                self._materials_cache = self._load_material_library()

            # Find the material
            if material_name not in self._materials_cache:
                return {"error": f"Material not found: {material_name}"}

            material_data = self._materials_cache[material_name]

            return {
                "resource_type": "material_info",
                "name": material_name,
                "category": material_data.get("category", "Unknown"),
                "description": material_data.get("description", ""),
                "properties": material_data.get("properties", {}),
            }

        except Exception as e:
            logger.error(f"Error getting material info: {e}")
            return {"error": f"Error getting material info: {str(e)}"}

    def _mock_material_info(self, material_name: str) -> Dict[str, Any]:
        """Provide mock material information when FreeCAD is not available."""
        # Material properties based on name
        if material_name.lower() == "steel":
            return {
                "resource_type": "material_info",
                "name": "Steel",
                "category": "Metal",
                "description": "Standard steel material",
                "properties": {
                    "Density": "7900 kg/m^3",
                    "YoungModulus": "210000 MPa",
                    "PoissonRatio": "0.3",
                    "Color": "0.4, 0.4, 0.4",
                    "ThermalConductivity": "50 W/m/K",
                    "ThermalExpansionCoefficient": "12 µm/m/K",
                },
                "note": "Mock data (FreeCAD not available)",
            }
        elif material_name.lower() == "aluminum":
            return {
                "resource_type": "material_info",
                "name": "Aluminum",
                "category": "Metal",
                "description": "Standard aluminum alloy",
                "properties": {
                    "Density": "2700 kg/m^3",
                    "YoungModulus": "70000 MPa",
                    "PoissonRatio": "0.35",
                    "Color": "0.8, 0.8, 0.8",
                    "ThermalConductivity": "237 W/m/K",
                    "ThermalExpansionCoefficient": "23 µm/m/K",
                },
                "note": "Mock data (FreeCAD not available)",
            }
        elif material_name.lower() == "pla":
            return {
                "resource_type": "material_info",
                "name": "PLA",
                "category": "Plastic",
                "description": "Standard PLA plastic for 3D printing",
                "properties": {
                    "Density": "1240 kg/m^3",
                    "YoungModulus": "3500 MPa",
                    "PoissonRatio": "0.36",
                    "Color": "0.9, 0.9, 0.9",
                    "ThermalConductivity": "0.13 W/m/K",
                    "GlassTransitionTemperature": "60 °C",
                },
                "note": "Mock data (FreeCAD not available)",
            }
        else:
            return {
                "resource_type": "material_info",
                "name": material_name,
                "category": "Unknown",
                "description": "Generic material",
                "properties": {
                    "Density": "1000 kg/m^3",
                    "YoungModulus": "10000 MPa",
                    "PoissonRatio": "0.3",
                    "Color": "0.8, 0.8, 0.8",
                },
                "note": "Mock data (FreeCAD not available)",
            }

    def _load_material_library(self) -> Dict[str, Dict[str, Any]]:
        """Load materials from FreeCAD's material library."""
        materials = {}

        if not self.app:
            return materials

        try:
            # Get the material library paths
            if hasattr(self.app, "getResourceDir"):
                resource_dir = self.app.getResourceDir()
                material_dirs = [
                    os.path.join(resource_dir, "Mod", "Material", "StandardMaterial"),
                    os.path.join(resource_dir, "Mod", "Material", "FluidMaterial"),
                ]

                # Add user material directory if it exists
                user_material_dir = os.path.join(
                    self.app.getUserAppDataDir(), "Material"
                )
                if os.path.exists(user_material_dir):
                    material_dirs.append(user_material_dir)

                # Scan directories for material files
                for material_dir in material_dirs:
                    if os.path.exists(material_dir):
                        for filename in os.listdir(material_dir):
                            if filename.endswith(".FCMat"):
                                material_path = os.path.join(material_dir, filename)
                                material_name = os.path.splitext(filename)[0]

                                # Read and parse the material file
                                material_data = self._parse_material_file(material_path)

                                if material_data:
                                    materials[material_name] = material_data

            return materials

        except Exception as e:
            logger.error(f"Error loading material library: {e}")
            return {}

    def _parse_material_file(self, file_path: str) -> Dict[str, Any]:
        """Parse a FreeCAD material file."""
        material_data = {"properties": {}}

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                category = "Unknown"

                for line in f:
                    line = line.strip()

                    # Skip comments and empty lines
                    if not line or line.startswith(";") or line.startswith("#"):
                        continue

                    # Check for section headers
                    if line.startswith("[") and line.endswith("]"):
                        section = line[1:-1]
                        if section == "FCMat":
                            continue
                        else:
                            category = section
                        continue

                    # Parse key-value pairs
                    if "=" in line:
                        key, value = [x.strip() for x in line.split("=", 1)]

                        if key == "Name":
                            material_data["name"] = value
                        elif key == "Description":
                            material_data["description"] = value
                        elif key == "Father":
                            material_data["parent"] = value
                        else:
                            material_data["properties"][key] = value

                material_data["category"] = category

            return material_data

        except Exception as e:
            logger.error(f"Error parsing material file {file_path}: {e}")
            return {}
