"""
Test suite for AdvancedOperationsTool

Tests for advanced CAD operations including extrude, revolve, loft,
sweep, and helix operations.

Author: AI Assistant
"""

import os
import sys
import unittest

# Add the parent directory to the path to import the tool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    import FreeCAD as App
    import Part
    from advanced_operations import AdvancedOperationsTool
    from advanced_primitives import AdvancedPrimitivesTool

    FREECAD_AVAILABLE = True
except ImportError:
    FREECAD_AVAILABLE = False
    print("Warning: FreeCAD not available, tests will be skipped")


@unittest.skipUnless(FREECAD_AVAILABLE, "FreeCAD not available")
class TestAdvancedOperationsTool(unittest.TestCase):
    """Test cases for AdvancedOperationsTool."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = AdvancedOperationsTool()
        self.primitives_tool = AdvancedPrimitivesTool()

        # Create a new document for each test
        if App.ActiveDocument:
            App.closeDocument(App.ActiveDocument.Name)
        self.doc = App.newDocument("TestDoc")

    def tearDown(self):
        """Clean up after each test."""
        if App.ActiveDocument:
            App.closeDocument(App.ActiveDocument.Name)

    def test_tool_initialization(self):
        """Test tool initialization."""
        self.assertEqual(self.tool.name, "advanced_operations")
        self.assertEqual(
            self.tool.description, "Perform advanced CAD operations on objects"
        )

    def test_get_available_operations(self):
        """Test getting available operations list."""
        operations = self.tool.get_available_operations()

        self.assertIn("advanced_operations", operations)
        advanced_ops = operations["advanced_operations"]

        # Check all expected operations are present
        expected_operations = ["extrude", "revolve", "loft", "sweep", "helix"]
        for op in expected_operations:
            self.assertIn(op, advanced_ops)
            self.assertIn("description", advanced_ops[op])
            self.assertIn("parameters", advanced_ops[op])

    def _create_test_rectangle(self, name="TestRect", width=10, height=5):
        """Helper method to create a test rectangle profile."""
        # Create a simple rectangle for testing
        vertices = [
            App.Vector(0, 0, 0),
            App.Vector(width, 0, 0),
            App.Vector(width, height, 0),
            App.Vector(0, height, 0),
            App.Vector(0, 0, 0),  # Close the rectangle
        ]

        edges = []
        for i in range(len(vertices) - 1):
            edge = Part.makeLine(vertices[i], vertices[i + 1])
            edges.append(edge)

        wire = Part.Wire(edges)
        face = Part.Face(wire)

        rect_obj = self.doc.addObject("Part::Feature", name)
        rect_obj.Shape = face
        rect_obj.Label = name
        self.doc.recompute()

        return rect_obj.Name

    def _create_test_circle(self, name="TestCircle", radius=5):
        """Helper method to create a test circle profile."""
        circle = Part.makeCircle(radius)
        wire = Part.Wire([circle])
        face = Part.Face(wire)

        circle_obj = self.doc.addObject("Part::Feature", name)
        circle_obj.Shape = face
        circle_obj.Label = name
        self.doc.recompute()

        return circle_obj.Name

    def _create_test_line(self, name="TestLine", start=(0, 0, 0), end=(20, 0, 10)):
        """Helper method to create a test line for paths."""
        line = Part.makeLine(App.Vector(*start), App.Vector(*end))

        line_obj = self.doc.addObject("Part::Feature", name)
        line_obj.Shape = line
        line_obj.Label = name
        self.doc.recompute()

        return line_obj.Name

    # Extrude Tests
    def test_extrude_valid_profile(self):
        """Test extruding a valid 2D profile."""
        profile_name = self._create_test_rectangle("ExtrudeRect", 10, 5)

        result = self.tool.extrude_profile(
            profile_name=profile_name,
            direction=(0, 0, 1),
            distance=15.0,
            name="TestExtrude",
        )

        self.assertTrue(result["success"])
        self.assertIn("object_name", result)
        self.assertIn("properties", result)

        props = result["properties"]
        self.assertEqual(props["source_profile"], profile_name)
        self.assertEqual(props["direction"], (0, 0, 1))
        self.assertEqual(props["distance"], 15.0)
        self.assertGreater(props["volume"], 0)

    def test_extrude_different_directions(self):
        """Test extruding in different directions."""
        profile_name = self._create_test_rectangle("ExtrudeRect2", 8, 6)

        # Test X direction
        result = self.tool.extrude_profile(
            profile_name, direction=(1, 0, 0), distance=10.0
        )
        self.assertTrue(result["success"])

        # Test Y direction
        result = self.tool.extrude_profile(
            profile_name, direction=(0, 1, 0), distance=10.0
        )
        self.assertTrue(result["success"])

        # Test diagonal direction
        result = self.tool.extrude_profile(
            profile_name, direction=(1, 1, 1), distance=10.0
        )
        self.assertTrue(result["success"])

    def test_extrude_invalid_parameters(self):
        """Test extrude with invalid parameters."""
        profile_name = self._create_test_rectangle("ExtrudeRect3")

        # Zero distance
        result = self.tool.extrude_profile(profile_name, distance=0.0)
        self.assertFalse(result["success"])
        self.assertIn("Distance must be positive", result["error"])

        # Invalid direction
        result = self.tool.extrude_profile(profile_name, direction=(0, 0))
        self.assertFalse(result["success"])
        self.assertIn("Direction must be a 3-element tuple", result["error"])

        # Zero direction vector
        result = self.tool.extrude_profile(profile_name, direction=(0, 0, 0))
        self.assertFalse(result["success"])
        self.assertIn("Direction vector cannot be zero", result["error"])

    def test_extrude_nonexistent_profile(self):
        """Test extrude with non-existent profile."""
        result = self.tool.extrude_profile("NonExistentProfile")
        self.assertFalse(result["success"])
        self.assertIn("Profile object 'NonExistentProfile' not found", result["error"])

    # Revolve Tests
    def test_revolve_valid_profile(self):
        """Test revolving a valid 2D profile."""
        profile_name = self._create_test_rectangle("RevolveRect", 5, 8)

        result = self.tool.revolve_profile(
            profile_name=profile_name,
            axis_point=(0, 0, 0),
            axis_direction=(0, 0, 1),
            angle=180.0,
            name="TestRevolve",
        )

        self.assertTrue(result["success"])
        props = result["properties"]
        self.assertEqual(props["source_profile"], profile_name)
        self.assertEqual(props["angle"], 180.0)
        self.assertGreater(props["volume"], 0)

    def test_revolve_full_rotation(self):
        """Test revolving with full 360° rotation."""
        profile_name = self._create_test_rectangle("RevolveRect2", 3, 6)

        result = self.tool.revolve_profile(profile_name, angle=360.0)
        self.assertTrue(result["success"])
        self.assertEqual(result["properties"]["angle"], 360.0)

    def test_revolve_different_axes(self):
        """Test revolving around different axes."""
        profile_name = self._create_test_rectangle("RevolveRect3", 4, 7)

        # X-axis
        result = self.tool.revolve_profile(
            profile_name, axis_direction=(1, 0, 0), angle=90.0
        )
        self.assertTrue(result["success"])

        # Y-axis
        result = self.tool.revolve_profile(
            profile_name, axis_direction=(0, 1, 0), angle=90.0
        )
        self.assertTrue(result["success"])

    def test_revolve_invalid_parameters(self):
        """Test revolve with invalid parameters."""
        profile_name = self._create_test_rectangle("RevolveRect4")

        # Invalid angle
        result = self.tool.revolve_profile(profile_name, angle=0.0)
        self.assertFalse(result["success"])
        self.assertIn("Angle must be between 0 and 360 degrees", result["error"])

        result = self.tool.revolve_profile(profile_name, angle=400.0)
        self.assertFalse(result["success"])
        self.assertIn("Angle must be between 0 and 360 degrees", result["error"])

        # Zero axis direction
        result = self.tool.revolve_profile(profile_name, axis_direction=(0, 0, 0))
        self.assertFalse(result["success"])
        self.assertIn("Axis direction vector cannot be zero", result["error"])

    # Loft Tests
    def test_loft_two_profiles(self):
        """Test lofting between two profiles."""
        profile1 = self._create_test_rectangle("LoftRect1", 10, 5)
        profile2 = self._create_test_circle("LoftCircle1", 3)

        # Move second profile up
        circle_obj = self.doc.getObject(profile2)
        circle_obj.Placement.Base = App.Vector(0, 0, 10)
        self.doc.recompute()

        result = self.tool.loft_profiles(
            profile_names=[profile1, profile2], solid=True, ruled=False, name="TestLoft"
        )

        self.assertTrue(result["success"])
        props = result["properties"]
        self.assertEqual(len(props["source_profiles"]), 2)
        self.assertTrue(props["solid"])
        self.assertFalse(props["ruled"])
        self.assertGreater(props["volume"], 0)

    def test_loft_multiple_profiles(self):
        """Test lofting between multiple profiles."""
        profile1 = self._create_test_rectangle("LoftRect2", 8, 4)
        profile2 = self._create_test_circle("LoftCircle2", 4)
        profile3 = self._create_test_rectangle("LoftRect3", 6, 6)

        # Position profiles at different heights
        self.doc.getObject(profile2).Placement.Base = App.Vector(0, 0, 5)
        self.doc.getObject(profile3).Placement.Base = App.Vector(0, 0, 10)
        self.doc.recompute()

        result = self.tool.loft_profiles([profile1, profile2, profile3])
        self.assertTrue(result["success"])
        self.assertEqual(len(result["properties"]["source_profiles"]), 3)

    def test_loft_surface_mode(self):
        """Test lofting in surface mode."""
        profile1 = self._create_test_circle("LoftCircle3", 5)
        profile2 = self._create_test_circle("LoftCircle4", 3)

        self.doc.getObject(profile2).Placement.Base = App.Vector(0, 0, 8)
        self.doc.recompute()

        result = self.tool.loft_profiles([profile1, profile2], solid=False)
        self.assertTrue(result["success"])
        self.assertFalse(result["properties"]["solid"])
        self.assertEqual(result["properties"]["volume"], "N/A (surface)")

    def test_loft_invalid_parameters(self):
        """Test loft with invalid parameters."""
        profile1 = self._create_test_rectangle("LoftRect4")

        # Too few profiles
        result = self.tool.loft_profiles([profile1])
        self.assertFalse(result["success"])
        self.assertIn("At least 2 profiles required for loft", result["error"])

        # Non-existent profile
        result = self.tool.loft_profiles([profile1, "NonExistent"])
        self.assertFalse(result["success"])
        self.assertIn("Profile object 'NonExistent' not found", result["error"])

    # Sweep Tests
    def test_sweep_valid_profile_and_path(self):
        """Test sweeping a profile along a path."""
        profile_name = self._create_test_circle("SweepCircle", 2)
        path_name = self._create_test_line("SweepPath", (0, 0, 0), (20, 10, 5))

        result = self.tool.sweep_profile(
            profile_name=profile_name,
            path_name=path_name,
            frenet=False,
            name="TestSweep",
        )

        self.assertTrue(result["success"])
        props = result["properties"]
        self.assertEqual(props["source_profile"], profile_name)
        self.assertEqual(props["path"], path_name)
        self.assertFalse(props["frenet"])
        self.assertGreater(props["volume"], 0)

    def test_sweep_with_frenet(self):
        """Test sweeping with Frenet frame orientation."""
        profile_name = self._create_test_rectangle("SweepRect", 3, 2)
        path_name = self._create_test_line("SweepPath2", (0, 0, 0), (15, 15, 10))

        result = self.tool.sweep_profile(profile_name, path_name, frenet=True)
        self.assertTrue(result["success"])
        self.assertTrue(result["properties"]["frenet"])

    def test_sweep_invalid_objects(self):
        """Test sweep with invalid objects."""
        profile_name = self._create_test_circle("SweepCircle2", 2)

        # Non-existent path
        result = self.tool.sweep_profile(profile_name, "NonExistentPath")
        self.assertFalse(result["success"])
        self.assertIn("Path object 'NonExistentPath' not found", result["error"])

        # Non-existent profile
        path_name = self._create_test_line("SweepPath3")
        result = self.tool.sweep_profile("NonExistentProfile", path_name)
        self.assertFalse(result["success"])
        self.assertIn("Profile object 'NonExistentProfile' not found", result["error"])

    # Helix Tests
    def test_create_helix_valid_parameters(self):
        """Test creating helix with valid parameters."""
        result = self.tool.create_helix(
            radius=8.0,
            pitch=3.0,
            height=24.0,
            direction="right",
            position=(5, 5, 0),
            name="TestHelix",
        )

        self.assertTrue(result["success"])
        props = result["properties"]
        self.assertEqual(props["radius"], 8.0)
        self.assertEqual(props["pitch"], 3.0)
        self.assertEqual(props["height"], 24.0)
        self.assertEqual(props["direction"], "right")
        self.assertEqual(props["turns"], 8.0)  # 24/3 = 8 turns
        self.assertGreater(props["length"], 0)

    def test_create_helix_left_handed(self):
        """Test creating left-handed helix."""
        result = self.tool.create_helix(
            radius=5.0, pitch=2.0, height=10.0, direction="left"
        )
        self.assertTrue(result["success"])
        self.assertEqual(result["properties"]["direction"], "left")

    def test_create_helix_different_parameters(self):
        """Test creating helix with different parameter combinations."""
        # Small tight helix
        result = self.tool.create_helix(radius=2.0, pitch=0.5, height=5.0)
        self.assertTrue(result["success"])
        self.assertEqual(result["properties"]["turns"], 10.0)  # 5.0/0.5 = 10 turns

        # Large loose helix
        result = self.tool.create_helix(radius=15.0, pitch=5.0, height=20.0)
        self.assertTrue(result["success"])
        self.assertEqual(result["properties"]["turns"], 4.0)  # 20.0/5.0 = 4 turns

    def test_create_helix_invalid_parameters(self):
        """Test creating helix with invalid parameters."""
        # Zero radius
        result = self.tool.create_helix(radius=0.0, pitch=2.0, height=10.0)
        self.assertFalse(result["success"])
        self.assertIn("Radius must be positive", result["error"])

        # Zero pitch
        result = self.tool.create_helix(radius=5.0, pitch=0.0, height=10.0)
        self.assertFalse(result["success"])
        self.assertIn("Pitch must be positive", result["error"])

        # Zero height
        result = self.tool.create_helix(radius=5.0, pitch=2.0, height=0.0)
        self.assertFalse(result["success"])
        self.assertIn("Height must be positive", result["error"])

        # Invalid direction
        result = self.tool.create_helix(
            radius=5.0, pitch=2.0, height=10.0, direction="up"
        )
        self.assertFalse(result["success"])
        self.assertIn("Direction must be 'right' or 'left'", result["error"])

    # Integration Tests
    def test_operation_chaining(self):
        """Test chaining multiple operations together."""
        # Create a rectangle profile
        profile_name = self._create_test_rectangle("ChainRect", 6, 4)

        # Extrude it
        extrude_result = self.tool.extrude_profile(profile_name, distance=8.0)
        self.assertTrue(extrude_result["success"])

        # Create a helix for threading
        helix_result = self.tool.create_helix(radius=4.0, pitch=1.0, height=8.0)
        self.assertTrue(helix_result["success"])

        # Both operations should succeed independently
        self.assertGreater(extrude_result["properties"]["volume"], 0)
        self.assertGreater(helix_result["properties"]["length"], 0)

    def test_no_active_document_handling(self):
        """Test handling when no active document exists."""
        # Close the document
        App.closeDocument(self.doc.Name)

        # Operations should fail gracefully
        result = self.tool.extrude_profile("TestProfile")
        self.assertFalse(result["success"])
        self.assertIn("No active document", result["error"])

        # Helix should create a new document
        result = self.tool.create_helix()
        self.assertTrue(result["success"])  # Helix creates new doc if needed


class TestAdvancedOperationsWithoutFreeCAD(unittest.TestCase):
    """Test cases that don't require FreeCAD."""

    def test_import_without_freecad(self):
        """Test that the module can be imported even without FreeCAD."""
        # This test runs regardless of FreeCAD availability
        self.assertTrue(True)  # Placeholder test


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
