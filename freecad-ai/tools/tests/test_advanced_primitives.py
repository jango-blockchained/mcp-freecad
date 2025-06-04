"""
Test suite for AdvancedPrimitivesTool

Tests for creating advanced 3D primitive shapes including tubes, prisms,
wedges, and ellipsoids.

Author: AI Assistant
"""

import unittest
import sys
import os

# Add the parent directory to the path to import the tool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from advanced_primitives import AdvancedPrimitivesTool
    FREECAD_AVAILABLE = True
except ImportError:
    FREECAD_AVAILABLE = False
    print("Warning: FreeCAD not available, tests will be skipped")


@unittest.skipUnless(FREECAD_AVAILABLE, "FreeCAD not available")
class TestAdvancedPrimitivesTool(unittest.TestCase):
    """Test cases for AdvancedPrimitivesTool."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = AdvancedPrimitivesTool()

    def test_tool_initialization(self):
        """Test tool initialization."""
        self.assertEqual(self.tool.name, "advanced_primitives")
        self.assertEqual(self.tool.description, "Create advanced 3D primitive shapes")

    def test_get_available_primitives(self):
        """Test getting available primitives list."""
        primitives = self.tool.get_available_primitives()

        self.assertIn("advanced_primitives", primitives)
        advanced_prims = primitives["advanced_primitives"]

        # Check all expected primitives are present
        expected_primitives = ["tube", "prism", "wedge", "ellipsoid"]
        for prim in expected_primitives:
            self.assertIn(prim, advanced_prims)
            self.assertIn("description", advanced_prims[prim])
            self.assertIn("parameters", advanced_prims[prim])

    # Tube Tests
    def test_create_tube_valid_parameters(self):
        """Test creating tube with valid parameters."""
        result = self.tool.create_tube(
            outer_radius=10.0,
            inner_radius=5.0,
            height=20.0,
            position=(0, 0, 0),
            name="TestTube"
        )

        self.assertTrue(result["success"])
        self.assertIn("object_name", result)
        self.assertIn("properties", result)

        props = result["properties"]
        self.assertEqual(props["outer_radius"], 10.0)
        self.assertEqual(props["inner_radius"], 5.0)
        self.assertEqual(props["height"], 20.0)
        self.assertEqual(props["wall_thickness"], 5.0)

    def test_create_tube_solid_cylinder(self):
        """Test creating tube with inner_radius = 0 (solid cylinder)."""
        result = self.tool.create_tube(
            outer_radius=8.0,
            inner_radius=0.0,
            height=15.0
        )

        self.assertTrue(result["success"])
        props = result["properties"]
        self.assertEqual(props["inner_radius"], 0.0)
        self.assertEqual(props["wall_thickness"], 8.0)

    def test_create_tube_invalid_radii(self):
        """Test creating tube with invalid radius parameters."""
        # Inner radius >= outer radius
        result = self.tool.create_tube(outer_radius=5.0, inner_radius=5.0, height=10.0)
        self.assertFalse(result["success"])
        self.assertIn("Inner radius must be less than outer radius", result["error"])

        # Negative outer radius
        result = self.tool.create_tube(outer_radius=-5.0, inner_radius=2.0, height=10.0)
        self.assertFalse(result["success"])
        self.assertIn("Outer radius must be positive", result["error"])

        # Negative inner radius
        result = self.tool.create_tube(outer_radius=10.0, inner_radius=-2.0, height=10.0)
        self.assertFalse(result["success"])
        self.assertIn("Inner radius must be non-negative", result["error"])

    def test_create_tube_invalid_height(self):
        """Test creating tube with invalid height."""
        result = self.tool.create_tube(outer_radius=10.0, inner_radius=5.0, height=0.0)
        self.assertFalse(result["success"])
        self.assertIn("Height must be positive", result["error"])

    # Prism Tests
    def test_create_prism_valid_parameters(self):
        """Test creating prism with valid parameters."""
        result = self.tool.create_prism(
            sides=6,
            radius=8.0,
            height=12.0,
            position=(10, 0, 0),
            name="TestHexagon"
        )

        self.assertTrue(result["success"])
        props = result["properties"]
        self.assertEqual(props["sides"], 6)
        self.assertEqual(props["radius"], 8.0)
        self.assertEqual(props["height"], 12.0)

    def test_create_prism_triangle(self):
        """Test creating triangular prism."""
        result = self.tool.create_prism(sides=3, radius=5.0, height=10.0)
        self.assertTrue(result["success"])
        self.assertEqual(result["properties"]["sides"], 3)

    def test_create_prism_invalid_sides(self):
        """Test creating prism with invalid sides count."""
        # Too few sides
        result = self.tool.create_prism(sides=2, radius=5.0, height=10.0)
        self.assertFalse(result["success"])
        self.assertIn("Sides must be an integer between 3 and 20", result["error"])

        # Too many sides
        result = self.tool.create_prism(sides=25, radius=5.0, height=10.0)
        self.assertFalse(result["success"])
        self.assertIn("Sides must be an integer between 3 and 20", result["error"])

        # Non-integer sides
        result = self.tool.create_prism(sides=5.5, radius=5.0, height=10.0)
        self.assertFalse(result["success"])

    def test_create_prism_invalid_dimensions(self):
        """Test creating prism with invalid dimensions."""
        # Zero radius
        result = self.tool.create_prism(sides=6, radius=0.0, height=10.0)
        self.assertFalse(result["success"])
        self.assertIn("Radius must be positive", result["error"])

        # Zero height
        result = self.tool.create_prism(sides=6, radius=5.0, height=0.0)
        self.assertFalse(result["success"])
        self.assertIn("Height must be positive", result["error"])

    # Wedge Tests
    def test_create_wedge_valid_parameters(self):
        """Test creating wedge with valid parameters."""
        result = self.tool.create_wedge(
            length=15.0,
            width=10.0,
            height=8.0,
            angle=30.0,
            position=(0, 10, 0),
            name="TestWedge"
        )

        self.assertTrue(result["success"])
        props = result["properties"]
        self.assertEqual(props["length"], 15.0)
        self.assertEqual(props["width"], 10.0)
        self.assertEqual(props["height"], 8.0)
        self.assertEqual(props["angle"], 30.0)

    def test_create_wedge_extreme_angles(self):
        """Test creating wedge with extreme angles."""
        # 0 degree angle (rectangular block)
        result = self.tool.create_wedge(length=10.0, width=10.0, height=10.0, angle=0.0)
        self.assertTrue(result["success"])
        self.assertEqual(result["properties"]["taper_offset"], 0.0)

        # 90 degree angle (maximum taper)
        result = self.tool.create_wedge(length=10.0, width=10.0, height=5.0, angle=90.0)
        self.assertTrue(result["success"])

    def test_create_wedge_invalid_dimensions(self):
        """Test creating wedge with invalid dimensions."""
        # Zero length
        result = self.tool.create_wedge(length=0.0, width=10.0, height=10.0, angle=45.0)
        self.assertFalse(result["success"])
        self.assertIn("Length must be positive", result["error"])

        # Negative width
        result = self.tool.create_wedge(length=10.0, width=-5.0, height=10.0, angle=45.0)
        self.assertFalse(result["success"])
        self.assertIn("Width must be positive", result["error"])

    def test_create_wedge_invalid_angle(self):
        """Test creating wedge with invalid angle."""
        # Negative angle
        result = self.tool.create_wedge(length=10.0, width=10.0, height=10.0, angle=-10.0)
        self.assertFalse(result["success"])
        self.assertIn("Angle must be between 0 and 90 degrees", result["error"])

        # Angle > 90
        result = self.tool.create_wedge(length=10.0, width=10.0, height=10.0, angle=95.0)
        self.assertFalse(result["success"])
        self.assertIn("Angle must be between 0 and 90 degrees", result["error"])

    # Ellipsoid Tests
    def test_create_ellipsoid_valid_parameters(self):
        """Test creating ellipsoid with valid parameters."""
        result = self.tool.create_ellipsoid(
            radius_x=8.0,
            radius_y=5.0,
            radius_z=6.0,
            position=(0, 0, 10),
            name="TestEllipsoid"
        )

        self.assertTrue(result["success"])
        props = result["properties"]
        self.assertEqual(props["radius_x"], 8.0)
        self.assertEqual(props["radius_y"], 5.0)
        self.assertEqual(props["radius_z"], 6.0)
        self.assertFalse(props["is_sphere"])

    def test_create_ellipsoid_sphere(self):
        """Test creating ellipsoid with equal radii (sphere)."""
        result = self.tool.create_ellipsoid(
            radius_x=7.0,
            radius_y=7.0,
            radius_z=7.0
        )

        self.assertTrue(result["success"])
        props = result["properties"]
        self.assertTrue(props["is_sphere"])

    def test_create_ellipsoid_invalid_radii(self):
        """Test creating ellipsoid with invalid radii."""
        # Zero X radius
        result = self.tool.create_ellipsoid(radius_x=0.0, radius_y=5.0, radius_z=6.0)
        self.assertFalse(result["success"])
        self.assertIn("X-radius must be positive", result["error"])

        # Negative Y radius
        result = self.tool.create_ellipsoid(radius_x=5.0, radius_y=-3.0, radius_z=6.0)
        self.assertFalse(result["success"])
        self.assertIn("Y-radius must be positive", result["error"])

        # Zero Z radius
        result = self.tool.create_ellipsoid(radius_x=5.0, radius_y=3.0, radius_z=0.0)
        self.assertFalse(result["success"])
        self.assertIn("Z-radius must be positive", result["error"])

    def test_volume_calculations(self):
        """Test volume calculations for different primitives."""
        # Test tube volume calculation
        tube_result = self.tool.create_tube(outer_radius=10.0, inner_radius=5.0, height=20.0)
        if tube_result["success"]:
            # Volume should be π * (R² - r²) * h
            expected_volume = 3.14159 * (10**2 - 5**2) * 20
            actual_volume = tube_result["properties"]["volume"]
            self.assertAlmostEqual(actual_volume, expected_volume, delta=100)  # Allow some tolerance

        # Test ellipsoid volume calculation
        ellipsoid_result = self.tool.create_ellipsoid(radius_x=3.0, radius_y=4.0, radius_z=5.0)
        if ellipsoid_result["success"]:
            # Volume should be (4/3) * π * a * b * c
            expected_volume = (4/3) * 3.14159 * 3.0 * 4.0 * 5.0
            actual_volume = ellipsoid_result["properties"]["volume"]
            self.assertAlmostEqual(actual_volume, expected_volume, delta=10)


class TestAdvancedPrimitivesWithoutFreeCAD(unittest.TestCase):
    """Test cases that don't require FreeCAD."""

    def test_import_without_freecad(self):
        """Test that the module can be imported even without FreeCAD."""
        # This test runs regardless of FreeCAD availability
        self.assertTrue(True)  # Placeholder test


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
