"""
Mock FreeCAD classes and modules for testing without requiring actual FreeCAD installation.

This module provides mock implementations of FreeCAD's core classes and functions
to enable comprehensive testing of the MCP-FreeCAD addon.
"""

import math
from typing import Dict, List, Optional, Any, Union
from unittest.mock import MagicMock


class MockVector:
    """Mock FreeCAD Vector class."""

    def __init__(self, x: float = 0.0, y: float = 0.0, z: float = 0.0):
        self.x = x
        self.y = y
        self.z = z

    def add(self, other: 'MockVector') -> 'MockVector':
        """Add two vectors."""
        return MockVector(self.x + other.x, self.y + other.y, self.z + other.z)

    def sub(self, other: 'MockVector') -> 'MockVector':
        """Subtract two vectors."""
        return MockVector(self.x - other.x, self.y - other.y, self.z - other.z)

    def normalize(self) -> 'MockVector':
        """Return normalized vector."""
        length = math.sqrt(self.x**2 + self.y**2 + self.z**2)
        if length > 0:
            return MockVector(self.x / length, self.y / length, self.z / length)
        return MockVector(0, 0, 0)

    def __iter__(self):
        """Make vector iterable for unpacking."""
        return iter([self.x, self.y, self.z])

    def __repr__(self):
        return f"Vector({self.x}, {self.y}, {self.z})"


class MockRotation:
    """Mock FreeCAD Rotation class."""

    def __init__(self, axis: MockVector = None, angle: float = 0.0):
        self.axis = axis or MockVector(0, 0, 1)
        self.angle = angle

    def multiply(self, other: 'MockRotation') -> 'MockRotation':
        """Multiply rotations."""
        # Simplified rotation multiplication
        return MockRotation(self.axis, self.angle + other.angle)


class MockPlacement:
    """Mock FreeCAD Placement class."""

    def __init__(self, base: MockVector = None, rotation: MockRotation = None):
        self.Base = base or MockVector(0, 0, 0)
        self.Rotation = rotation or MockRotation()


class MockMatrix:
    """Mock FreeCAD Matrix class."""

    def __init__(self):
        # 4x4 transformation matrix elements
        self.A11 = 1.0
        self.A12 = 0.0
        self.A13 = 0.0
        self.A14 = 0.0
        self.A21 = 0.0
        self.A22 = 1.0
        self.A23 = 0.0
        self.A24 = 0.0
        self.A31 = 0.0
        self.A32 = 0.0
        self.A33 = 1.0
        self.A34 = 0.0
        self.A41 = 0.0
        self.A42 = 0.0
        self.A43 = 0.0
        self.A44 = 1.0

    def unity(self):
        """Set to identity matrix."""
        self.__init__()


class MockShape:
    """Mock FreeCAD Shape class."""

    def __init__(self, shape_type: str = "Solid"):
        self.ShapeType = shape_type
        self.Volume = 1000.0  # Default volume
        self.Area = 600.0     # Default surface area
        self.Edges = [MockEdge() for _ in range(12)]  # Default edges for a box
        self.Faces = [MockFace() for _ in range(6)]   # Default faces for a box
        self.Vertexes = [MockVertex() for _ in range(8)]  # Default vertices for a box

    def fuse(self, other: 'MockShape') -> 'MockShape':
        """Boolean union operation."""
        result = MockShape("Solid")
        result.Volume = self.Volume + other.Volume
        result.Area = self.Area + other.Area * 0.8  # Approximate fusion
        return result

    def cut(self, other: 'MockShape') -> 'MockShape':
        """Boolean difference operation."""
        result = MockShape("Solid")
        result.Volume = max(0, self.Volume - other.Volume)
        result.Area = self.Area + other.Area * 0.5  # Approximate cutting
        return result

    def common(self, other: 'MockShape') -> 'MockShape':
        """Boolean intersection operation."""
        result = MockShape("Solid")
        result.Volume = min(self.Volume, other.Volume) * 0.5  # Approximate intersection
        result.Area = min(self.Area, other.Area) * 0.7
        return result

    def makeFillet(self, radius: float, edges: List['MockEdge']) -> 'MockShape':
        """Create fillet on edges."""
        result = MockShape("Solid")
        result.Volume = self.Volume * 0.95  # Slightly reduced volume
        result.Area = self.Area * 1.05      # Slightly increased area
        return result

    def transformed(self, matrix: MockMatrix) -> 'MockShape':
        """Apply transformation matrix."""
        result = MockShape(self.ShapeType)
        result.Volume = self.Volume
        result.Area = self.Area
        return result


class MockEdge:
    """Mock FreeCAD Edge class."""

    def __init__(self):
        self.Length = 10.0


class MockFace:
    """Mock FreeCAD Face class."""

    def __init__(self):
        self.Area = 100.0


class MockVertex:
    """Mock FreeCAD Vertex class."""

    def __init__(self):
        self.Point = MockVector(0, 0, 0)


class MockObject:
    """Mock FreeCAD Document Object."""

    def __init__(self, name: str, object_type: str = "Part::Feature"):
        self.Name = name
        self.TypeId = object_type
        self.Label = name
        self.Placement = MockPlacement()
        self.Shape = MockShape()
        self._properties = {}

        # Add type-specific properties
        if object_type == "Part::Box":
            self.Length = 10.0
            self.Width = 10.0
            self.Height = 10.0
        elif object_type == "Part::Cylinder":
            self.Radius = 5.0
            self.Height = 10.0
        elif object_type == "Part::Sphere":
            self.Radius = 5.0
        elif object_type == "Part::Cone":
            self.Radius1 = 5.0
            self.Radius2 = 0.0
            self.Height = 10.0

    def __setattr__(self, name, value):
        """Override setattr to track property changes."""
        if hasattr(self, '_properties'):
            self._properties[name] = value
        super().__setattr__(name, value)


class MockDocument:
    """Mock FreeCAD Document."""

    def __init__(self, name: str = "Unnamed"):
        self.Name = name
        self.Label = name
        self.Objects = []
        self._object_counter = 0
        self._objects_by_name = {}

    def addObject(self, object_type: str, name: str = None) -> MockObject:
        """Add an object to the document."""
        if name is None:
            self._object_counter += 1
            name = f"Object{self._object_counter:03d}"

        # Ensure unique name
        original_name = name
        counter = 1
        while name in self._objects_by_name:
            name = f"{original_name}{counter:03d}"
            counter += 1

        obj = MockObject(name, object_type)
        self.Objects.append(obj)
        self._objects_by_name[name] = obj
        return obj

    def getObject(self, name: str) -> Optional[MockObject]:
        """Get an object by name."""
        return self._objects_by_name.get(name)

    def getObjectsByLabel(self, label: str) -> List[MockObject]:
        """Get objects by label."""
        return [obj for obj in self.Objects if obj.Label == label]

    def removeObject(self, name: str) -> bool:
        """Remove an object from the document."""
        if name in self._objects_by_name:
            obj = self._objects_by_name[name]
            self.Objects.remove(obj)
            del self._objects_by_name[name]
            return True
        return False

    def recompute(self) -> None:
        """Recompute the document."""
        # In real FreeCAD, this updates all objects
        # In our mock, we just simulate the operation
        pass

    def saveAs(self, filename: str) -> bool:
        """Save document to file."""
        # Mock implementation
        return True


class MockGui:
    """Mock FreeCAD Gui module."""

    @staticmethod
    def hideObject(obj: MockObject) -> None:
        """Hide an object in the GUI."""
        pass

    @staticmethod
    def showObject(obj: MockObject) -> None:
        """Show an object in the GUI."""
        pass


class MockPart:
    """Mock FreeCAD Part module."""

    @staticmethod
    def makeBox(length: float, width: float, height: float) -> MockShape:
        """Create a box shape."""
        shape = MockShape("Solid")
        shape.Volume = length * width * height
        shape.Area = 2 * (length * width + width * height + height * length)
        return shape

    @staticmethod
    def makeCylinder(radius: float, height: float) -> MockShape:
        """Create a cylinder shape."""
        shape = MockShape("Solid")
        shape.Volume = math.pi * radius**2 * height
        shape.Area = 2 * math.pi * radius * (radius + height)
        return shape

    @staticmethod
    def makeSphere(radius: float) -> MockShape:
        """Create a sphere shape."""
        shape = MockShape("Solid")
        shape.Volume = (4/3) * math.pi * radius**3
        shape.Area = 4 * math.pi * radius**2
        return shape


class MockFreeCAD:
    """Mock FreeCAD application."""

    def __init__(self):
        self.ActiveDocument = None
        self.Documents = {}
        self._doc_counter = 0

        # Add static classes/modules
        self.Vector = MockVector
        self.Rotation = MockRotation
        self.Placement = MockPlacement
        self.Matrix = MockMatrix
        self.Gui = MockGui()

    def newDocument(self, name: str = None) -> MockDocument:
        """Create a new document."""
        if name is None:
            self._doc_counter += 1
            name = f"Unnamed{self._doc_counter}"

        doc = MockDocument(name)
        self.Documents[name] = doc
        self.ActiveDocument = doc
        return doc

    def openDocument(self, filename: str) -> MockDocument:
        """Open a document from file."""
        # Mock implementation - just create a new document
        name = filename.split('/')[-1].split('.')[0]
        return self.newDocument(name)

    def closeDocument(self, name: str) -> None:
        """Close a document."""
        if name in self.Documents:
            del self.Documents[name]
            if self.ActiveDocument and self.ActiveDocument.Name == name:
                self.ActiveDocument = None

    def setActiveDocument(self, name: str) -> None:
        """Set the active document."""
        if name in self.Documents:
            self.ActiveDocument = self.Documents[name]

    def getDocument(self, name: str) -> Optional[MockDocument]:
        """Get a document by name."""
        return self.Documents.get(name)


# Create global mock instances that can be imported
mock_freecad = MockFreeCAD()
mock_part = MockPart()

# Function to get a clean mock instance for testing
def get_mock_freecad() -> MockFreeCAD:
    """Get a fresh MockFreeCAD instance for testing."""
    return MockFreeCAD()


def get_mock_part() -> MockPart:
    """Get a MockPart instance for testing."""
    return MockPart()
