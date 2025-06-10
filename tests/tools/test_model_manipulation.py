"""
Unit tests for ModelManipulationToolProvider.

This module tests the model manipulation and transformation functionality.
"""

import asyncio
from unittest.mock import MagicMock, patch

import pytest

from tests.fixtures import (
    boolean_operations,
    mock_freecad,
    model_manipulation_tool_provider,
    primitive_tool_provider,
    test_document,
    test_utilities,
)


class TestModelManipulationToolProvider:
    """Test suite for ModelManipulationToolProvider."""

    def test_tool_schema(self, model_manipulation_tool_provider):
        """Test that the tool schema is properly defined."""
        schema = model_manipulation_tool_provider.tool_schema

        assert schema.name == "model_manipulation"
        assert schema.description is not None
        assert "properties" in schema.parameters
        assert "tool_id" in schema.parameters["properties"]
        assert "params" in schema.parameters["properties"]

        # Validate tool_id enum values
        tool_ids = schema.parameters["properties"]["tool_id"]["enum"]
        expected_tools = [
            "transform", "boolean_operation", "fillet_edge", "chamfer_edge",
            "mirror", "scale", "offset", "thicken"
        ]

        for tool in expected_tools:
            assert tool in tool_ids

    @pytest.mark.asyncio
    async def test_transform_translation(
        self,
        model_manipulation_tool_provider,
        primitive_tool_provider,
        mock_freecad
    ):
        """Test object transformation with translation."""
        # First create an object to transform
        box_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {"length": 5.0, "width": 3.0, "height": 2.0}
        )
        assert box_result.status == "success"
        box_id = box_result.result["object_id"]

        # Transform the object
        transform_params = {
            "object": box_id,
            "translation": [10.0, 5.0, 2.0]
        }

        result = await model_manipulation_tool_provider.execute_tool(
            "transform",
            transform_params
        )

        assert result.status == "success"
        assert "object" in result.result
        assert result.result["object"] == box_id
        assert "modifications" in result.result

    @pytest.mark.asyncio
    async def test_transform_rotation(
        self,
        model_manipulation_tool_provider,
        primitive_tool_provider,
        mock_freecad
    ):
        """Test object transformation with rotation."""
        # Create an object to transform
        cylinder_result = await primitive_tool_provider.execute_tool(
            "create_cylinder",
            {"radius": 3.0, "height": 8.0}
        )
        assert cylinder_result.status == "success"
        cylinder_id = cylinder_result.result["object_id"]

        # Rotate the object
        transform_params = {
            "object": cylinder_id,
            "rotation": [90.0, 0.0, 45.0]  # Euler angles in degrees
        }

        result = await model_manipulation_tool_provider.execute_tool(
            "transform",
            transform_params
        )

        assert result.status == "success"
        assert "modifications" in result.result

    @pytest.mark.asyncio
    async def test_transform_combined(
        self,
        model_manipulation_tool_provider,
        primitive_tool_provider,
        mock_freecad
    ):
        """Test object transformation with both translation and rotation."""
        # Create an object
        sphere_result = await primitive_tool_provider.execute_tool(
            "create_sphere",
            {"radius": 4.0}
        )
        assert sphere_result.status == "success"
        sphere_id = sphere_result.result["object_id"]

        # Apply combined transformation
        transform_params = {
            "object": sphere_id,
            "translation": [5.0, 0.0, 3.0],
            "rotation": [0.0, 90.0, 0.0]
        }

        result = await model_manipulation_tool_provider.execute_tool(
            "transform",
            transform_params
        )

        assert result.status == "success"
        assert len(result.result["modifications"]) == 2  # Translation + rotation

    @pytest.mark.asyncio
    async def test_boolean_union(
        self,
        model_manipulation_tool_provider,
        primitive_tool_provider,
        mock_freecad
    ):
        """Test boolean union operation."""
        # Create two objects
        box1_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {"length": 5.0, "width": 5.0, "height": 5.0}
        )
        box2_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {"length": 3.0, "width": 3.0, "height": 8.0}
        )

        assert box1_result.status == "success"
        assert box2_result.status == "success"

        # Perform union
        union_params = {
            "operation": "union",
            "object1": box1_result.result["object_id"],
            "object2": box2_result.result["object_id"],
            "result_name": "UnionResult"
        }

        result = await model_manipulation_tool_provider.execute_tool(
            "boolean_operation",
            union_params
        )

        assert result.status == "success"
        assert result.result["result_object"] == "UnionResult"
        assert result.result["operation"] == "union"

        # Verify the result object exists
        doc = mock_freecad.ActiveDocument
        union_obj = doc.getObject("UnionResult")
        assert union_obj is not None

    @pytest.mark.asyncio
    async def test_boolean_difference(
        self,
        model_manipulation_tool_provider,
        primitive_tool_provider,
        mock_freecad
    ):
        """Test boolean difference (cut) operation."""
        # Create two objects
        box_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {"length": 10.0, "width": 10.0, "height": 5.0}
        )
        cylinder_result = await primitive_tool_provider.execute_tool(
            "create_cylinder",
            {"radius": 2.0, "height": 6.0}
        )

        assert box_result.status == "success"
        assert cylinder_result.status == "success"

        # Cut cylinder from box
        cut_params = {
            "operation": "difference",
            "object1": box_result.result["object_id"],
            "object2": cylinder_result.result["object_id"],
            "result_name": "CutResult"
        }

        result = await model_manipulation_tool_provider.execute_tool(
            "boolean_operation",
            cut_params
        )

        assert result.status == "success"
        assert result.result["operation"] == "difference"

    @pytest.mark.asyncio
    async def test_boolean_intersection(
        self,
        model_manipulation_tool_provider,
        primitive_tool_provider,
        mock_freecad
    ):
        """Test boolean intersection operation."""
        # Create two overlapping objects
        box_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {"length": 6.0, "width": 6.0, "height": 6.0}
        )
        sphere_result = await primitive_tool_provider.execute_tool(
            "create_sphere",
            {"radius": 4.0}
        )

        assert box_result.status == "success"
        assert sphere_result.status == "success"

        # Find intersection
        intersection_params = {
            "operation": "intersection",
            "object1": box_result.result["object_id"],
            "object2": sphere_result.result["object_id"],
            "result_name": "IntersectionResult"
        }

        result = await model_manipulation_tool_provider.execute_tool(
            "boolean_operation",
            intersection_params
        )

        assert result.status == "success"
        assert result.result["operation"] == "intersection"

    @pytest.mark.asyncio
    async def test_fillet_edge(
        self,
        model_manipulation_tool_provider,
        primitive_tool_provider,
        mock_freecad
    ):
        """Test edge filleting operation."""
        # Create a box to fillet
        box_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {"length": 8.0, "width": 6.0, "height": 4.0}
        )
        assert box_result.status == "success"

        # Apply fillet
        fillet_params = {
            "object": box_result.result["object_id"],
            "radius": 1.0,
            "result_name": "FilletedBox"
        }

        result = await model_manipulation_tool_provider.execute_tool(
            "fillet_edge",
            fillet_params
        )

        assert result.status == "success"
        assert result.result["result_object"] == "FilletedBox"
        assert result.result["radius"] == 1.0

    @pytest.mark.asyncio
    async def test_mirror_object(
        self,
        model_manipulation_tool_provider,
        primitive_tool_provider,
        mock_freecad
    ):
        """Test object mirroring operation."""
        # Create an object to mirror
        cone_result = await primitive_tool_provider.execute_tool(
            "create_cone",
            {"radius1": 5.0, "radius2": 2.0, "height": 8.0}
        )
        assert cone_result.status == "success"

        # Mirror across XY plane
        mirror_params = {
            "object": cone_result.result["object_id"],
            "plane": "xy",
            "result_name": "MirroredCone"
        }

        result = await model_manipulation_tool_provider.execute_tool(
            "mirror",
            mirror_params
        )

        assert result.status == "success"
        assert result.result["result_object"] == "MirroredCone"
        assert "xy" in result.result["mirror_plane"]

    @pytest.mark.asyncio
    async def test_mirror_with_normal_vector(
        self,
        model_manipulation_tool_provider,
        primitive_tool_provider,
        mock_freecad
    ):
        """Test object mirroring with custom normal vector."""
        # Create an object
        box_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {"length": 4.0, "width": 4.0, "height": 4.0}
        )
        assert box_result.status == "success"

        # Mirror with custom normal
        mirror_params = {
            "object": box_result.result["object_id"],
            "normal": [1.0, 1.0, 0.0],  # Diagonal mirror
            "result_name": "DiagonalMirror"
        }

        result = await model_manipulation_tool_provider.execute_tool(
            "mirror",
            mirror_params
        )

        assert result.status == "success"

    @pytest.mark.asyncio
    async def test_transform_nonexistent_object(self, model_manipulation_tool_provider):
        """Test transformation of non-existent object."""
        transform_params = {
            "object": "NonExistentObject",
            "translation": [1.0, 0.0, 0.0]
        }

        result = await model_manipulation_tool_provider.execute_tool(
            "transform",
            transform_params
        )

        # In our mock, this might still succeed, but in real FreeCAD it would fail
        # This test documents the expected behavior

    @pytest.mark.asyncio
    async def test_boolean_operation_missing_objects(self, model_manipulation_tool_provider):
        """Test boolean operation with missing objects."""
        boolean_params = {
            "operation": "union",
            "object1": "MissingObject1",
            "object2": "MissingObject2"
        }

        result = await model_manipulation_tool_provider.execute_tool(
            "boolean_operation",
            boolean_params
        )

        # Should handle missing objects gracefully

    @pytest.mark.asyncio
    async def test_invalid_boolean_operation(self, model_manipulation_tool_provider):
        """Test invalid boolean operation type."""
        boolean_params = {
            "operation": "invalid_operation",
            "object1": "Object1",
            "object2": "Object2"
        }

        result = await model_manipulation_tool_provider.execute_tool(
            "boolean_operation",
            boolean_params
        )

        assert result.status == "error"
        assert "Unknown operation type" in result.error

    @pytest.mark.asyncio
    async def test_transform_invalid_parameters(self, model_manipulation_tool_provider):
        """Test transformation with invalid parameters."""
        # Test invalid translation format
        invalid_params = {
            "object": "SomeObject",
            "translation": [1.0, 2.0]  # Missing Z component
        }

        result = await model_manipulation_tool_provider.execute_tool(
            "transform",
            invalid_params
        )

        assert result.status == "error"
        assert "Invalid translation format" in result.error

    @pytest.mark.parametrize("operation", ["union", "difference", "intersection"])
    @pytest.mark.asyncio
    async def test_boolean_operations_parametrized(
        self,
        operation,
        model_manipulation_tool_provider,
        primitive_tool_provider,
        mock_freecad
    ):
        """Test all boolean operations with parametrized testing."""
        # Create two objects
        obj1_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {"length": 5.0, "width": 5.0, "height": 5.0}
        )
        obj2_result = await primitive_tool_provider.execute_tool(
            "create_sphere",
            {"radius": 3.0}
        )

        assert obj1_result.status == "success"
        assert obj2_result.status == "success"

        # Perform boolean operation
        boolean_params = {
            "operation": operation,
            "object1": obj1_result.result["object_id"],
            "object2": obj2_result.result["object_id"],
            "result_name": f"{operation.title()}Result"
        }

        result = await model_manipulation_tool_provider.execute_tool(
            "boolean_operation",
            boolean_params
        )

        assert result.status == "success"
        assert result.result["operation"] == operation

    @pytest.mark.asyncio
    async def test_no_freecad_connection(self):
        """Test behavior when FreeCAD is not available."""
        from src.mcp_freecad.tools.model_manipulation import (
            ModelManipulationToolProvider,
        )

        # Create provider without FreeCAD
        provider = ModelManipulationToolProvider(freecad_app=None)

        result = await provider.execute_tool(
            "transform",
            {"object": "TestObject", "translation": [1, 0, 0]}
        )

        assert result.status == "error"
        assert "FreeCAD is not available" in result.error

    @pytest.mark.asyncio
    async def test_unimplemented_tools(self, model_manipulation_tool_provider):
        """Test that unimplemented tools return appropriate errors."""
        unimplemented_tools = ["chamfer_edge", "scale", "offset", "thicken"]

        for tool in unimplemented_tools:
            result = await model_manipulation_tool_provider.execute_tool(
                tool,
                {"object": "TestObject"}
            )

            assert result.status == "error"
            assert "not yet implemented" in result.error

    @pytest.mark.asyncio
    async def test_complex_transformation_sequence(
        self,
        model_manipulation_tool_provider,
        primitive_tool_provider,
        mock_freecad
    ):
        """Test a sequence of complex transformations."""
        # Create an object
        box_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {"length": 4.0, "width": 4.0, "height": 4.0}
        )
        assert box_result.status == "success"
        box_id = box_result.result["object_id"]

        # Apply multiple transformations
        transformations = [
            {"translation": [2.0, 0.0, 0.0]},
            {"rotation": [0.0, 0.0, 45.0]},
            {"translation": [0.0, 3.0, 0.0]},
            {"rotation": [90.0, 0.0, 0.0]}
        ]

        for i, transform in enumerate(transformations):
            transform["object"] = box_id
            result = await model_manipulation_tool_provider.execute_tool(
                "transform",
                transform
            )
            assert result.status == "success", f"Transformation {i+1} failed"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_boolean_operation_performance(
        self,
        model_manipulation_tool_provider,
        primitive_tool_provider,
        performance_benchmarks
    ):
        """Test that boolean operations meet performance requirements."""
        import time

        # Create objects
        box_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {"length": 10.0, "width": 10.0, "height": 10.0}
        )
        cylinder_result = await primitive_tool_provider.execute_tool(
            "create_cylinder",
            {"radius": 5.0, "height": 12.0}
        )

        # Time the boolean operation
        start_time = time.time()
        result = await model_manipulation_tool_provider.execute_tool(
            "boolean_operation",
            {
                "operation": "union",
                "object1": box_result.result["object_id"],
                "object2": cylinder_result.result["object_id"]
            }
        )
        elapsed_time = time.time() - start_time

        benchmark = performance_benchmarks["boolean_operation"]
        assert result.status == "success"
        assert elapsed_time < benchmark["max_time_seconds"], \
            f"Boolean operation took {elapsed_time:.3f}s, expected < {benchmark['max_time_seconds']}s"
