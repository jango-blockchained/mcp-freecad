"""
E2E Tests for Smithery Tools

Tests the creation of blacksmith tools and objects using the smithery tools.
"""

import os
import pytest
from tests.e2e.test_base import MCPClientTestBase
from tests.e2e.config import TEST_OUTPUT_DIR

class TestSmithery(MCPClientTestBase):
    """Test smithery tool operations."""

    def test_create_anvil(self):
        """Test creating an anvil."""
        # Execute the smithery.create_anvil tool
        result = self.execute_tool(
            "smithery.create_anvil",
            length=350,
            width=100,
            height=150,
            horn_length=150,
            base_height=50,
            name="TestAnvil"
        )

        # Verify the result
        self.assertTrue(result.get("success", False))
        self.assertEqual(result.get("anvil_id", ""), "TestAnvil")

    def test_create_hammer(self):
        """Test creating a blacksmith hammer."""
        # Execute the smithery.create_hammer tool
        result = self.execute_tool(
            "smithery.create_hammer",
            handle_length=350,
            handle_diameter=30,
            head_length=100,
            head_width=40,
            head_height=30,
            name="TestHammer"
        )

        # Verify the result
        self.assertTrue(result.get("success", False))
        self.assertEqual(result.get("hammer_id", ""), "TestHammer")

    def test_create_tongs(self):
        """Test creating blacksmith tongs."""
        # Execute the smithery.create_tongs tool
        result = self.execute_tool(
            "smithery.create_tongs",
            handle_length=300,
            jaw_length=80,
            opening_angle=30,
            thickness=10,
            name="TestTongs"
        )

        # Verify the result
        self.assertTrue(result.get("success", False))
        self.assertEqual(result.get("tongs_id", ""), "TestTongs")

    def test_forge_blade(self):
        """Test creating a forged blade."""
        # Execute the smithery.forge_blade tool
        result = self.execute_tool(
            "smithery.forge_blade",
            blade_length=200,
            blade_width=40,
            blade_thickness=5,
            tang_length=100,
            curvature=10,
            name="TestBlade"
        )

        # Verify the result
        self.assertTrue(result.get("success", False))
        self.assertEqual(result.get("blade_id", ""), "TestBlade")

    def test_create_horseshoe(self):
        """Test creating a horseshoe."""
        # Execute the smithery.create_horseshoe tool
        result = self.execute_tool(
            "smithery.create_horseshoe",
            width=120,
            branch_thickness=10,
            branch_width=20,
            calking_height=15,
            name="TestHorseshoe"
        )

        # Verify the result
        self.assertTrue(result.get("success", False))
        self.assertEqual(result.get("horseshoe_id", ""), "TestHorseshoe")

    def test_create_blacksmith_workshop(self):
        """Test creating a full blacksmith workshop with multiple tools."""
        # Create an anvil
        anvil_result = self.execute_tool(
            "smithery.create_anvil",
            length=350,
            width=100,
            height=150,
            name="WorkshopAnvil"
        )
        self.assertTrue(anvil_result.get("success", False))

        # Create a hammer
        hammer_result = self.execute_tool(
            "smithery.create_hammer",
            handle_length=350,
            head_width=40,
            name="WorkshopHammer"
        )
        self.assertTrue(hammer_result.get("success", False))

        # Create tongs
        tongs_result = self.execute_tool(
            "smithery.create_tongs",
            handle_length=300,
            jaw_length=80,
            name="WorkshopTongs"
        )
        self.assertTrue(tongs_result.get("success", False))

        # Export the workshop to STL
        export_path = os.path.join(TEST_OUTPUT_DIR, "blacksmith_workshop.stl")
        export_result = self.execute_tool(
            "export_import.export_stl",
            filepath=export_path
        )

        # Verify export success
        self.assertTrue(export_result.get("success", False))

        # Verify file was created
        self.assertTrue(os.path.exists(export_path))

        # Cleanup
        if os.path.exists(export_path):
            os.remove(export_path)


if __name__ == "__main__":
    pytest.main(["-v", "tests/e2e/test_smithery.py"])
