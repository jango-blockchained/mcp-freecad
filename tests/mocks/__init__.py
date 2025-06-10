"""
Mock modules for testing FreeCAD functionality without requiring actual FreeCAD installation.
"""

from .freecad_mock import MockDocument, MockFreeCAD, MockObject, MockPart

__all__ = ["MockFreeCAD", "MockDocument", "MockObject", "MockPart"]
