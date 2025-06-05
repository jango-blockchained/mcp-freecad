"""
Unit tests for PrimitiveToolProvider.

This module tests the primitive shape creation functionality in isolation.
"""

import pytest
import asyncio
from unittest.mock import patch, MagicMock

from tests.fixtures import (
    mock_freecad, primitive_tool_provider, test_document,
    box_parameters, cylinder_parameters, test_utilities
)


class TestPrimitiveToolProvider:
    """Test suite for PrimitiveToolProvider."""

    def test_tool_schema(self, primitive_tool_provider):
        """Test that the tool schema is properly defined."""
        schema = primitive_tool_provider.tool_schema

        assert schema.name == "primitives"
        assert schema.description is not None
        assert "properties" in schema.parameters
        assert "tool_id" in schema.parameters["properties"]
        assert "params" in schema.parameters["properties"]

        # Validate tool_id enum values
        tool_ids = schema.parameters["properties"]["tool_id"]["enum"]
        expected_tools = ["create_box", "create_cylinder", "create_sphere", "create_cone"]

        for tool in expected_tools:
            assert tool in tool_ids

    @pytest.mark.asyncio
    async def test_create_box_success(self, primitive_tool_provider, mock_freecad, test_utilities):
        """Test successful box creation."""
        params = {"length": 10.0, "width": 5.0, "height": 3.0}

        result = await primitive_tool_provider.execute_tool("create_box", params)

        assert result.status == "success"
        assert result.result is not None
        assert result.result["object_type"] == "Part::Box"
        assert "object_id" in result.result

        # Validate the created object
        doc = mock_freecad.ActiveDocument
        box_obj = doc.getObject(result.result["object_id"])
        assert box_obj is not None
        assert box_obj.TypeId == "Part::Box"

        # Validate dimensions
        test_utilities.validate_model_dimensions(box_obj, params)

    @pytest.mark.asyncio
    async def test_create_box_with_defaults(self, primitive_tool_provider, mock_freecad):
        """Test box creation with default parameters."""
        result = await primitive_tool_provider.execute_tool("create_box", {})

        assert result.status == "success"

        # Check that defaults were applied
        doc = mock_freecad.ActiveDocument
        box_obj = doc.getObject(result.result["object_id"])
        assert box_obj.Length == 10.0  # Default length
        assert box_obj.Width == 10.0   # Default width
        assert box_obj.Height == 10.0  # Default height

    @pytest.mark.asyncio
    async def test_create_cylinder_success(self, primitive_tool_provider, mock_freecad, test_utilities):
        """Test successful cylinder creation."""
        params = {"radius": 5.0, "height": 10.0}

        result = await primitive_tool_provider.execute_tool("create_cylinder", params)

        assert result.status == "success"
        assert result.result["object_type"] == "Part::Cylinder"

        # Validate the created object
        doc = mock_freecad.ActiveDocument
        cylinder_obj = doc.getObject(result.result["object_id"])
        assert cylinder_obj is not None
        assert cylinder_obj.TypeId == "Part::Cylinder"
        assert cylinder_obj.Radius == params["radius"]
        assert cylinder_obj.Height == params["height"]

    @pytest.mark.asyncio
    async def test_invalid_tool_id(self, primitive_tool_provider):
        """Test handling of invalid tool ID."""
        result = await primitive_tool_provider.execute_tool("invalid_tool", {})

        assert result.status == "error"
        assert "Unknown tool" in result.error

