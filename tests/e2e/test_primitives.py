"""
E2E Tests for Primitive Operations

Tests the creation and manipulation of basic primitive shapes.
"""

import os
import pytest
from tests.e2e.test_base import MCPClientTestBase
from tests.e2e.config import TEST_OUTPUT_DIR

class TestPrimitives(MCPClientTestBase):
    """Test primitive shape creation and operations."""

    def test_create_box(self):
        """Test creating a box primitive."""
        # Execute the primitives.create_box tool
        result = self.execute_tool(
            "primitives.create_box",
            length=100,
            width=50,
            height=25,
            name="TestBox"
        )

        # Verify the result
        self.assertTrue(result.get("success", False))
        self.assertEqual(result.get("box_id", ""), "TestBox")

    def test_create_cylinder(self):
        """Test creating a cylinder primitive."""
        # Execute the primitives.create_cylinder tool
        result = self.execute_tool(
            "primitives.create_cylinder",
            radius=25,
            height=100,
            name="TestCylinder"
        )

        # Verify the result
        self.assertTrue(result.get("success", False))
        self.assertEqual(result.get("cylinder_id", ""), "TestCylinder")

    def test_create_sphere(self):
        """Test creating a sphere primitive."""
        # Execute the primitives.create_sphere tool
        result = self.execute_tool(
            "primitives.create_sphere",
            radius=50,
            name="TestSphere"
        )

        # Verify the result
        self.assertTrue(result.get("success", False))
        self.assertEqual(result.get("sphere_id", ""), "TestSphere")

    def test_create_multiple_primitives(self):
        """Test creating multiple primitives in sequence."""
        # Create a box
        box_result = self.execute_tool(
            "primitives.create_box",
            length=100,
            width=50,
            height=25,
            name="MultiBox"
        )
        self.assertTrue(box_result.get("success", False))

        # Create a cylinder
        cylinder_result = self.execute_tool(
            "primitives.create_cylinder",
            radius=25,
            height=100,
            name="MultiCylinder"
        )
        self.assertTrue(cylinder_result.get("success", False))

        # Create a sphere
        sphere_result = self.execute_tool(
            "primitives.create_sphere",
            radius=50,
            name="MultiSphere"
        )
        self.assertTrue(sphere_result.get("success", False))

        # List all objects and ensure our primitives are there
        # This is a hypothetical tool - implement according to your actual API
        list_result = self.execute_tool("freecad.list_objects")
        self.assertTrue(list_result.get("success", False))

        # Verify all our objects are in the list
        objects = list_result.get("objects", [])
        expected_objects = ["MultiBox", "MultiCylinder", "MultiSphere"]
        for obj in expected_objects:
            self.assertIn(obj, objects)

    def test_export_primitive(self):
        """Test creating and exporting a primitive to STL."""
        # Create a box
        box_result = self.execute_tool(
            "primitives.create_box",
            length=100,
            width=50,
            height=25,
            name="ExportBox"
        )
        self.assertTrue(box_result.get("success", False))

        # Export the box to STL
        export_path = os.path.join(TEST_OUTPUT_DIR, "test_export.stl")
        export_result = self.execute_tool(
            "export_import.export_stl",
            filepath=export_path,
            object_id="ExportBox"
        )

        # Verify export success
        self.assertTrue(export_result.get("success", False))

        # Verify file was created
        self.assertTrue(os.path.exists(export_path))

        # Cleanup
        if os.path.exists(export_path):
            os.remove(export_path)


if __name__ == "__main__":
    pytest.main(["-v", "tests/e2e/test_primitives.py"])
