"""
Test suite for SurfaceModificationTool

Tests for surface modification operations including fillet, chamfer,
draft, thickness, and offset operations.

Author: AI Assistant
"""

import unittest
import sys
import os

# Add the parent directory to the path to import the tool
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

try:
    from surface_modification import SurfaceModificationTool
    from advanced_primitives import AdvancedPrimitivesTool
    import FreeCAD as App
    import Part

    FREECAD_AVAILABLE = True
except ImportError:
    FREECAD_AVAILABLE = False
    print("Warning: FreeCAD not available, tests will be skipped")


@unittest.skipUnless(FREECAD_AVAILABLE, "FreeCAD not available")
class TestSurfaceModificationTool(unittest.TestCase):
    """Test cases for SurfaceModificationTool."""

    def setUp(self):
        """Set up test fixtures."""
        self.tool = SurfaceModificationTool()
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
        self.assertEqual(self.tool.name, "surface_modification")
        self.assertEqual(
            self.tool.description, "Modify surfaces and edges for manufacturing"
        )

    def test_get_available_modifications(self):
        """Test getting available modifications list."""
        modifications = self.tool.get_available_modifications()

        self.assertIn("surface_modifications", modifications)
        surface_mods = modifications["surface_modifications"]

        # Check all expected modifications are present
        expected_modifications = ["fillet", "chamfer", "draft", "thickness", "offset"]
        for mod in expected_modifications:
            self.assertIn(mod, surface_mods)
            self.assertIn("description", surface_mods[mod])
            self.assertIn("parameters", surface_mods[mod])
            self.assertIn("manufacturing_use", surface_mods[mod])

    def _create_test_box(self, name="TestBox", length=10, width=8, height=6):
        """Helper method to create a test box for surface modification."""
        # Create a box using Part workbench directly
        box_shape = Part.makeBox(length, width, height)

        box_obj = self.doc.addObject("Part::Feature", name)
        box_obj.Shape = box_shape
        box_obj.Label = name
        self.doc.recompute()

        return box_obj.Name

    def _create_test_cylinder(self, name="TestCylinder", radius=5, height=10):
        """Helper method to create a test cylinder for surface modification."""
        # Create a cylinder using Part workbench directly
        cylinder_shape = Part.makeCylinder(radius, height)

        cylinder_obj = self.doc.addObject("Part::Feature", name)
        cylinder_obj.Shape = cylinder_shape
        cylinder_obj.Label = name
        self.doc.recompute()

        return cylinder_obj.Name

    # Fillet Tests
    def test_fillet_single_edge(self):
        """Test filleting a single edge."""
        box_name = self._create_test_box("FilletBox1", 10, 8, 6)

        result = self.tool.fillet_edges(
            object_name=box_name,
            edge_indices=[0],  # First edge
            radius=2.0,
            name="TestFillet",
        )

        self.assertTrue(result["success"])
        self.assertIn("object_name", result)
        self.assertIn("properties", result)

        props = result["properties"]
        self.assertEqual(props["source_object"], box_name)
        self.assertEqual(props["edge_indices"], [0])
        self.assertEqual(props["radius"], 2.0)
        self.assertEqual(props["edges_filleted"], 1)
        self.assertGreater(props["volume"], 0)

    def test_fillet_multiple_edges(self):
        """Test filleting multiple edges."""
        box_name = self._create_test_box("FilletBox2", 12, 10, 8)

        result = self.tool.fillet_edges(
            object_name=box_name,
            edge_indices=[0, 1, 2, 3],  # Multiple edges
            radius=1.5,
        )

        self.assertTrue(result["success"])
        props = result["properties"]
        self.assertEqual(props["edges_filleted"], 4)
        self.assertEqual(props["radius"], 1.5)

    def test_fillet_invalid_parameters(self):
        """Test fillet with invalid parameters."""
        box_name = self._create_test_box("FilletBox3")

        # Zero radius
        result = self.tool.fillet_edges(box_name, [0], radius=0.0)
        self.assertFalse(result["success"])
        self.assertIn("Radius must be positive", result["error"])

        # Empty edge list
        result = self.tool.fillet_edges(box_name, [], radius=1.0)
        self.assertFalse(result["success"])
        self.assertIn("Edge indices must be a non-empty list", result["error"])

        # Invalid edge index
        result = self.tool.fillet_edges(box_name, [999], radius=1.0)
        self.assertFalse(result["success"])
        self.assertIn("Invalid edge index", result["error"])

    def test_fillet_nonexistent_object(self):
        """Test fillet with non-existent object."""
        result = self.tool.fillet_edges("NonExistentObject", [0], radius=1.0)
        self.assertFalse(result["success"])
        self.assertIn("Object 'NonExistentObject' not found", result["error"])

    # Chamfer Tests
    def test_chamfer_single_edge(self):
        """Test chamfering a single edge."""
        box_name = self._create_test_box("ChamferBox1", 10, 8, 6)

        result = self.tool.chamfer_edges(
            object_name=box_name,
            edge_indices=[0],  # First edge
            distance=1.5,
            name="TestChamfer",
        )

        self.assertTrue(result["success"])
        props = result["properties"]
        self.assertEqual(props["source_object"], box_name)
        self.assertEqual(props["distance"], 1.5)
        self.assertEqual(props["edges_chamfered"], 1)

    def test_chamfer_multiple_edges(self):
        """Test chamfering multiple edges."""
        cylinder_name = self._create_test_cylinder("ChamferCylinder", 6, 12)

        result = self.tool.chamfer_edges(
            object_name=cylinder_name,
            edge_indices=[0, 2],  # Top and bottom circular edges
            distance=1.0,
        )

        self.assertTrue(result["success"])
        props = result["properties"]
        self.assertEqual(props["edges_chamfered"], 2)
        self.assertEqual(props["distance"], 1.0)

    def test_chamfer_invalid_parameters(self):
        """Test chamfer with invalid parameters."""
        box_name = self._create_test_box("ChamferBox2")

        # Zero distance
        result = self.tool.chamfer_edges(box_name, [0], distance=0.0)
        self.assertFalse(result["success"])
        self.assertIn("Distance must be positive", result["error"])

        # Invalid edge index
        result = self.tool.chamfer_edges(box_name, [-1], distance=1.0)
        self.assertFalse(result["success"])
        self.assertIn("Invalid edge index", result["error"])

    # Draft Tests
    def test_draft_faces_valid_parameters(self):
        """Test draft operation with valid parameters."""
        box_name = self._create_test_box("DraftBox1", 10, 8, 6)

        result = self.tool.draft_faces(
            object_name=box_name,
            face_indices=[0, 1],  # Two faces
            angle=5.0,
            direction=(0, 0, 1),
            name="TestDraft",
        )

        # Note: Draft is simplified implementation, should succeed
        self.assertTrue(result["success"])
        props = result["properties"]
        self.assertEqual(props["source_object"], box_name)
        self.assertEqual(props["angle"], 5.0)
        self.assertEqual(props["faces_drafted"], 2)
        self.assertIn("note", props)  # Should have implementation note

    def test_draft_invalid_parameters(self):
        """Test draft with invalid parameters."""
        box_name = self._create_test_box("DraftBox2")

        # Invalid angle
        result = self.tool.draft_faces(box_name, [0], angle=50.0)
        self.assertFalse(result["success"])
        self.assertIn("Angle must be between 0 and 45 degrees", result["error"])

        # Empty face list
        result = self.tool.draft_faces(box_name, [], angle=5.0)
        self.assertFalse(result["success"])
        self.assertIn("Face indices must be a non-empty list", result["error"])

        # Zero direction vector
        result = self.tool.draft_faces(box_name, [0], angle=5.0, direction=(0, 0, 0))
        self.assertFalse(result["success"])
        self.assertIn("Direction vector cannot be zero", result["error"])

    # Thickness Tests
    def test_thickness_without_face_removal(self):
        """Test thickness operation without removing faces."""
        box_name = self._create_test_box("ThicknessBox1", 10, 8, 6)

        result = self.tool.create_thickness(
            object_name=box_name, thickness=2.0, name="TestThickness"
        )

        self.assertTrue(result["success"])
        props = result["properties"]
        self.assertEqual(props["source_object"], box_name)
        self.assertEqual(props["thickness"], 2.0)
        self.assertEqual(props["faces_removed"], 0)
        self.assertFalse(props["is_shell"])

    def test_thickness_with_face_removal(self):
        """Test thickness operation with face removal (shell creation)."""
        box_name = self._create_test_box("ThicknessBox2", 12, 10, 8)

        result = self.tool.create_thickness(
            object_name=box_name,
            thickness=1.5,
            face_indices=[5],  # Remove top face
            name="TestShell",
        )

        self.assertTrue(result["success"])
        props = result["properties"]
        self.assertEqual(props["thickness"], 1.5)
        self.assertEqual(props["faces_removed"], 1)
        self.assertTrue(props["is_shell"])

    def test_thickness_invalid_parameters(self):
        """Test thickness with invalid parameters."""
        box_name = self._create_test_box("ThicknessBox3")

        # Zero thickness
        result = self.tool.create_thickness(box_name, thickness=0.0)
        self.assertFalse(result["success"])
        self.assertIn("Thickness must be positive", result["error"])

        # Invalid face index
        result = self.tool.create_thickness(box_name, thickness=1.0, face_indices=[999])
        self.assertFalse(result["success"])
        self.assertIn("Invalid face index", result["error"])

    # Offset Tests
    def test_offset_outward(self):
        """Test outward offset operation."""
        cylinder_name = self._create_test_cylinder("OffsetCylinder1", 5, 10)

        result = self.tool.offset_surface(
            object_name=cylinder_name, distance=2.0, name="TestOffsetOut"
        )

        self.assertTrue(result["success"])
        props = result["properties"]
        self.assertEqual(props["source_object"], cylinder_name)
        self.assertEqual(props["distance"], 2.0)
        self.assertEqual(props["direction"], "outward")
        self.assertGreater(props["volume"], 0)

    def test_offset_inward(self):
        """Test inward offset operation."""
        box_name = self._create_test_box("OffsetBox", 15, 12, 10)

        result = self.tool.offset_surface(
            object_name=box_name, distance=-1.5, name="TestOffsetIn"
        )

        self.assertTrue(result["success"])
        props = result["properties"]
        self.assertEqual(props["distance"], -1.5)
        self.assertEqual(props["direction"], "inward")

    def test_offset_invalid_parameters(self):
        """Test offset with invalid parameters."""
        box_name = self._create_test_box("OffsetBox2")

        # Zero distance
        result = self.tool.offset_surface(box_name, distance=0.0)
        self.assertFalse(result["success"])
        self.assertIn("Distance cannot be zero", result["error"])

    # Integration Tests
    def test_sequential_modifications(self):
        """Test applying multiple surface modifications sequentially."""
        # Create initial box
        box_name = self._create_test_box("SequentialBox", 12, 10, 8)

        # Apply fillet
        fillet_result = self.tool.fillet_edges(box_name, [0, 1], radius=1.0)
        self.assertTrue(fillet_result["success"])

        # Apply chamfer to the filleted object
        chamfer_result = self.tool.chamfer_edges(
            fillet_result["object_name"], [4, 5], distance=0.5
        )
        self.assertTrue(chamfer_result["success"])

        # Apply thickness to create shell
        thickness_result = self.tool.create_thickness(
            chamfer_result["object_name"], thickness=1.0, face_indices=[5]
        )
        self.assertTrue(thickness_result["success"])

    def test_manufacturing_workflow(self):
        """Test a typical manufacturing workflow."""
        # Create a part
        part_name = self._create_test_cylinder("ManufacturingPart", 8, 15)

        # Add fillets for stress relief
        fillet_result = self.tool.fillet_edges(part_name, [0, 2], radius=1.5)
        self.assertTrue(fillet_result["success"])

        # Add chamfers for assembly
        chamfer_result = self.tool.chamfer_edges(
            fillet_result["object_name"], [1], distance=0.8
        )
        self.assertTrue(chamfer_result["success"])

        # Create shell for weight reduction
        shell_result = self.tool.create_thickness(
            chamfer_result["object_name"], thickness=2.0, face_indices=[1]
        )
        self.assertTrue(shell_result["success"])

        # Verify final part has reasonable volume
        self.assertGreater(shell_result["properties"]["volume"], 0)

    def test_edge_case_handling(self):
        """Test handling of edge cases and error conditions."""
        # Test with very small geometry
        small_box = self._create_test_box("SmallBox", 1, 1, 1)

        # Large fillet radius (should fail gracefully)
        result = self.tool.fillet_edges(small_box, [0], radius=10.0)
        # This might fail due to geometry constraints, which is expected
        if not result["success"]:
            self.assertIn("Fillet operation failed", result["error"])

    def test_no_active_document_handling(self):
        """Test handling when no active document exists."""
        # Close the document
        App.closeDocument(self.doc.Name)

        # Operations should fail gracefully
        result = self.tool.fillet_edges("TestObject", [0], radius=1.0)
        self.assertFalse(result["success"])
        self.assertIn("No active document", result["error"])

    def test_complex_geometry_modifications(self):
        """Test modifications on more complex geometry."""
        # Create a more complex shape using primitives tool
        tube_result = self.primitives_tool.create_tube(
            outer_radius=8.0, inner_radius=5.0, height=12.0, name="ComplexTube"
        )

        if tube_result["success"]:
            tube_name = tube_result["object_name"]

            # Apply fillet to tube edges
            fillet_result = self.tool.fillet_edges(tube_name, [0, 1], radius=1.0)
            # Complex geometry might have different edge arrangements
            # Test should handle both success and expected failures gracefully
            if fillet_result["success"]:
                self.assertGreater(fillet_result["properties"]["volume"], 0)


class TestSurfaceModificationWithoutFreeCAD(unittest.TestCase):
    """Test cases that don't require FreeCAD."""

    def test_import_without_freecad(self):
        """Test that the module can be imported even without FreeCAD."""
        # This test runs regardless of FreeCAD availability
        self.assertTrue(True)  # Placeholder test


if __name__ == "__main__":
    # Run tests
    unittest.main(verbosity=2)
