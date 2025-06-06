"""
Basic tests for MCP FreeCAD addon tools

This module provides basic unit tests for the tool implementations
to ensure they work correctly.

Author: jango-blockchained
"""

import os
import sys
import unittest

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# Mock FreeCAD modules for testing without FreeCAD
class MockApp:
    ActiveDocument = None
    Vector = lambda x, y, z: type("Vector", (), {"x": x, "y": y, "z": z})()
    Rotation = lambda x, y, z: type("Rotation", (), {"x": x, "y": y, "z": z})()
    Matrix = lambda: type("Matrix", (), {"scale": lambda self, x, y, z: None})()

    @staticmethod
    def newDocument(name):
        return type(
            "Document",
            (),
            {
                "Objects": [],
                "addObject": lambda self, t, n: type(
                    "Object",
                    (),
                    {
                        "Name": n,
                        "Label": n,
                        "Shape": None,
                        "Placement": type(
                            "Placement",
                            (),
                            {
                                "Base": MockApp.Vector(0, 0, 0),
                                "Rotation": MockApp.Rotation(0, 0, 0),
                            },
                        )(),
                    },
                )(),
                "removeObject": lambda self, n: None,
                "getObject": lambda self, n: None,
                "recompute": lambda self: None,
            },
        )()


class MockPart:
    @staticmethod
    def makeBox(l, w, h):
        return type(
            "Shape",
            (),
            {
                "Volume": l * w * h,
                "Area": 2 * (l * w + l * h + w * h),
                "fuse": lambda self, other: self,
                "cut": lambda self, other: self,
                "common": lambda self, other: self,
                "transformGeometry": lambda self, mat: self,
                "exportStep": lambda self, path: None,
                "exportStl": lambda self, path: None,
                "BoundBox": type(
                    "BoundBox",
                    (),
                    {
                        "Center": MockApp.Vector(l / 2, w / 2, h / 2),
                        "XLength": l,
                        "YLength": w,
                        "ZLength": h,
                        "DiagonalLength": (l**2 + w**2 + h**2) ** 0.5,
                    },
                )(),
            },
        )()

    @staticmethod
    def makeCylinder(r, h):
        import math

        return type(
            "Shape",
            (),
            {"Volume": math.pi * r * r * h, "Area": 2 * math.pi * r * (r + h)},
        )()

    @staticmethod
    def makeSphere(r):
        import math

        return type(
            "Shape",
            (),
            {"Volume": (4 / 3) * math.pi * r * r * r, "Area": 4 * math.pi * r * r},
        )()

    @staticmethod
    def makeCompound(shapes):
        return shapes[0] if shapes else None


# Mock modules
sys.modules["FreeCAD"] = MockApp
sys.modules["Part"] = MockPart
sys.modules["Mesh"] = type("Mesh", (), {"Mesh": lambda: None})()

from tools.export_import import ExportImportTool
from tools.measurements import MeasurementsTool
from tools.operations import OperationsTool

# Now import tools after mocking
from tools.primitives import PrimitivesTool


class TestPrimitivesTool(unittest.TestCase):
    """Test cases for primitives tool."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = PrimitivesTool()
        # Create a mock document
        MockApp.ActiveDocument = MockApp.newDocument("Test")

    def test_create_box(self):
        """Test box creation."""
        result = self.tool.create_box(length=10, width=20, height=30)

        self.assertTrue(result["success"])
        self.assertIn("object_name", result)
        self.assertEqual(result["properties"]["volume"], 10 * 20 * 30)

    def test_create_cylinder(self):
        """Test cylinder creation."""
        result = self.tool.create_cylinder(radius=5, height=10)

        self.assertTrue(result["success"])
        self.assertIn("object_name", result)
        # Volume should be approximately pi * r^2 * h
        import math

        expected_volume = math.pi * 5 * 5 * 10
        self.assertAlmostEqual(
            result["properties"]["volume"], expected_volume, places=1
        )

    def test_create_sphere(self):
        """Test sphere creation."""
        result = self.tool.create_sphere(radius=5)

        self.assertTrue(result["success"])
        self.assertIn("object_name", result)

    def test_get_available_primitives(self):
        """Test listing available primitives."""
        result = self.tool.get_available_primitives()

        self.assertIn("primitives", result)
        self.assertIn("box", result["primitives"])
        self.assertIn("cylinder", result["primitives"])
        self.assertIn("sphere", result["primitives"])


class TestOperationsTool(unittest.TestCase):
    """Test cases for operations tool."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = OperationsTool()
        MockApp.ActiveDocument = MockApp.newDocument("Test")

    def test_get_available_operations(self):
        """Test listing available operations."""
        result = self.tool.get_available_operations()

        self.assertIn("operations", result)
        self.assertIn("boolean_union", result["operations"])
        self.assertIn("boolean_cut", result["operations"])
        self.assertIn("move_object", result["operations"])
        self.assertIn("rotate_object", result["operations"])

    def test_validate_objects_no_document(self):
        """Test object validation without active document."""
        MockApp.ActiveDocument = None
        valid, obj1, obj2, error = self.tool._validate_objects("obj1", "obj2")

        self.assertFalse(valid)
        self.assertEqual(error, "No active document")


class TestMeasurementsTool(unittest.TestCase):
    """Test cases for measurements tool."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = MeasurementsTool()
        MockApp.ActiveDocument = MockApp.newDocument("Test")

    def test_measure_distance_with_coords(self):
        """Test distance measurement between coordinates."""
        result = self.tool.measure_distance([0, 0, 0], [3, 4, 0])

        self.assertTrue(result["success"])
        self.assertEqual(result["properties"]["distance"], 5.0)  # 3-4-5 triangle

    def test_measure_bounding_box_no_object(self):
        """Test bounding box measurement with non-existent object."""
        result = self.tool.measure_bounding_box("NonExistent")

        self.assertFalse(result["success"])
        self.assertIn("not found", result["message"])

    def test_get_available_measurements(self):
        """Test listing available measurements."""
        result = self.tool.get_available_measurements()

        self.assertIn("measurements", result)
        self.assertIn("distance", result["measurements"])
        self.assertIn("volume", result["measurements"])
        self.assertIn("area", result["measurements"])


class TestExportImportTool(unittest.TestCase):
    """Test cases for export/import tool."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = ExportImportTool()
        MockApp.ActiveDocument = MockApp.newDocument("Test")

    def test_get_supported_formats(self):
        """Test listing supported formats."""
        result = self.tool.get_supported_formats()

        self.assertIn("export_formats", result)
        self.assertIn("import_formats", result)
        self.assertIn("stl", result["export_formats"])
        self.assertIn("step", result["export_formats"])

    def test_export_no_document(self):
        """Test export without active document."""
        MockApp.ActiveDocument = None
        result = self.tool.export_stl("test.stl")

        self.assertFalse(result["success"])
        self.assertIn("No active document", result["message"])

    def test_export_format_unsupported(self):
        """Test export with unsupported format."""
        result = self.tool.export_format("test.xyz", "xyz")

        self.assertFalse(result["success"])
        self.assertIn("not supported", result["message"])


class TestToolIntegration(unittest.TestCase):
    """Integration tests for tools working together."""

    def setUp(self):
        """Set up test fixtures."""
        self.primitives = PrimitivesTool()
        self.operations = OperationsTool()
        self.measurements = MeasurementsTool()
        MockApp.ActiveDocument = MockApp.newDocument("Test")

    def test_create_and_measure(self):
        """Test creating a primitive and measuring it."""
        # Create a box
        create_result = self.primitives.create_box(10, 10, 10)
        self.assertTrue(create_result["success"])

        # Measure its volume (mocked, but tests the flow)
        # In real FreeCAD, we would measure the created object
        # For now, just verify the tools can be called in sequence
        self.assertIsNotNone(create_result["object_name"])


def run_tests():
    """Run all tests."""
    unittest.main(argv=[""], exit=False, verbosity=2)


if __name__ == "__main__":
    print("Running MCP FreeCAD Addon Tool Tests")
    print("=" * 50)
    run_tests()
    print("\nTests completed!")
