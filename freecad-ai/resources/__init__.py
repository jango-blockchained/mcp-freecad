"""
Resources for FreeCAD AI addon.

This module contains resource providers for materials, constraints, measurements, and CAD models.
"""

# Import resource providers
try:
    from .base import ResourceProvider
    from .cad_model import CADModelResourceProvider
    from .constraint import ConstraintResourceProvider
    from .material import MaterialResourceProvider
    from .measurement import MeasurementResourceProvider

    RESOURCES_AVAILABLE = True

    __all__ = [
        "ResourceProvider",
        "MaterialResourceProvider",
        "ConstraintResourceProvider",
        "MeasurementResourceProvider",
        "CADModelResourceProvider",
        "RESOURCES_AVAILABLE",
    ]

except ImportError as e:
    import FreeCAD

    FreeCAD.Console.PrintWarning(f"FreeCAD AI: Failed to import some resources: {e}\n")
    RESOURCES_AVAILABLE = False
    __all__ = ["RESOURCES_AVAILABLE"]
