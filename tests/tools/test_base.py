"""
Unit tests for Base Tool Provider classes.

This module tests the base functionality that all tool providers inherit.
"""

from unittest.mock import MagicMock

import pytest
from pydantic import ValidationError

from src.mcp_freecad.tools.base import ToolParams, ToolProvider, ToolResult, ToolSchema


class MockToolProvider(ToolProvider):
    """Mock implementation of ToolProvider for testing."""

    @property
    def tool_schema(self) -> ToolSchema:
        return ToolSchema(
            name="mock_tool",
            description="A mock tool for testing",
            parameters={
                "type": "object",
                "properties": {
                    "tool_id": {"type": "string"},
                    "params": {"type": "object"},
                },
                "required": ["tool_id"],
            },
            returns={
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "result": {"type": "object"},
                },
            },
            examples=[{"tool_id": "test", "params": {}}],
        )

    async def execute_tool(self, tool_id: str, params: dict) -> ToolResult:
        if tool_id == "success_tool":
            return self.format_result(
                status="success", result={"message": "Tool executed successfully"}
            )
        elif tool_id == "error_tool":
            return self.format_result(status="error", error="Tool execution failed")
        else:
            return self.format_result(status="error", error=f"Unknown tool: {tool_id}")


class TestToolParams:
    """Test the ToolParams model."""

    def test_tool_params_creation(self):
        """Test creating ToolParams with valid data."""
        params = ToolParams(tool_id="test_tool", params={"param1": "value1"})

        assert params.tool_id == "test_tool"
        assert params.params == {"param1": "value1"}

    def test_tool_params_with_defaults(self):
        """Test ToolParams with default params."""
        params = ToolParams(tool_id="test_tool")

        assert params.tool_id == "test_tool"
        assert params.params == {}

    def test_tool_params_validation_error(self):
        """Test ToolParams validation with missing required field."""
        with pytest.raises(ValidationError):
            ToolParams(params={"param1": "value1"})  # Missing tool_id


class TestToolResult:
    """Test the ToolResult model."""

    def test_tool_result_success(self):
        """Test creating a successful ToolResult."""
        result = ToolResult(status="success", result={"data": "test_data"})

        assert result.status == "success"
        assert result.result == {"data": "test_data"}
        assert result.error is None

    def test_tool_result_error(self):
        """Test creating an error ToolResult."""
        result = ToolResult(status="error", error="Something went wrong")

        assert result.status == "error"
        assert result.error == "Something went wrong"
        assert result.result is None

    def test_tool_result_validation_error(self):
        """Test ToolResult validation with missing status."""
        with pytest.raises(ValidationError):
            ToolResult(result={"data": "test"})  # Missing status


class TestToolSchema:
    """Test the ToolSchema model."""

    def test_tool_schema_creation(self):
        """Test creating a ToolSchema."""
        schema = ToolSchema(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object"},
            returns={"type": "object"},
            examples=[{"example": "data"}],
        )

        assert schema.name == "test_tool"
        assert schema.description == "A test tool"
        assert schema.parameters == {"type": "object"}
        assert schema.returns == {"type": "object"}
        assert schema.examples == [{"example": "data"}]

    def test_tool_schema_without_examples(self):
        """Test ToolSchema without examples."""
        schema = ToolSchema(
            name="test_tool",
            description="A test tool",
            parameters={"type": "object"},
            returns={"type": "object"},
        )

        assert schema.examples is None


class TestToolProvider:
    """Test the base ToolProvider class."""

    def test_tool_provider_is_abstract(self):
        """Test that ToolProvider cannot be instantiated directly."""
        with pytest.raises(TypeError):
            ToolProvider()

    def test_mock_tool_provider_creation(self):
        """Test creating a mock tool provider."""
        provider = MockToolProvider()
        assert isinstance(provider, ToolProvider)

    def test_tool_schema_property(self):
        """Test the tool_schema property."""
        provider = MockToolProvider()
        schema = provider.tool_schema

        assert isinstance(schema, ToolSchema)
        assert schema.name == "mock_tool"
        assert schema.description == "A mock tool for testing"
        assert "tool_id" in schema.parameters["properties"]

    @pytest.mark.asyncio
    async def test_execute_tool_success(self):
        """Test successful tool execution."""
        provider = MockToolProvider()

        result = await provider.execute_tool("success_tool", {})

        assert isinstance(result, ToolResult)
        assert result.status == "success"
        assert result.result["message"] == "Tool executed successfully"
        assert result.error is None

    @pytest.mark.asyncio
    async def test_execute_tool_error(self):
        """Test tool execution error."""
        provider = MockToolProvider()

        result = await provider.execute_tool("error_tool", {})

        assert result.status == "error"
        assert result.error == "Tool execution failed"
        assert result.result is None

    @pytest.mark.asyncio
    async def test_execute_tool_unknown(self):
        """Test execution of unknown tool."""
        provider = MockToolProvider()

        result = await provider.execute_tool("unknown_tool", {})

        assert result.status == "error"
        assert "Unknown tool" in result.error

    def test_validate_params_success(self):
        """Test successful parameter validation."""
        provider = MockToolProvider()

        # This should not raise an exception
        provider.validate_params({"tool_id": "test", "params": {}})

    def test_validate_params_error(self):
        """Test parameter validation error."""
        provider = MockToolProvider()

        with pytest.raises(ValueError):
            provider.validate_params({"params": {}})  # Missing tool_id

    def test_format_result_success(self):
        """Test formatting a successful result."""
        provider = MockToolProvider()

        result = provider.format_result(status="success", result={"data": "test"})

        assert isinstance(result, ToolResult)
        assert result.status == "success"
        assert result.result == {"data": "test"}
        assert result.error is None

    def test_format_result_error(self):
        """Test formatting an error result."""
        provider = MockToolProvider()

        result = provider.format_result(status="error", error="Test error")

        assert result.status == "error"
        assert result.error == "Test error"
        assert result.result is None

    def test_format_result_with_both_result_and_error(self):
        """Test formatting result with both result and error."""
        provider = MockToolProvider()

        result = provider.format_result(
            status="warning", result={"data": "partial"}, error="Warning message"
        )

        assert result.status == "warning"
        assert result.result == {"data": "partial"}
        assert result.error == "Warning message"


class TestToolProviderInheritance:
    """Test tool provider inheritance patterns."""

    def test_multiple_tool_providers(self):
        """Test creating multiple different tool providers."""
        provider1 = MockToolProvider()
        provider2 = MockToolProvider()

        # They should be different instances
        assert provider1 is not provider2

        # But have the same schema
        assert provider1.tool_schema.name == provider2.tool_schema.name

    @pytest.mark.asyncio
    async def test_tool_provider_consistency(self):
        """Test that tool providers behave consistently."""
        provider = MockToolProvider()

        # Multiple calls should return consistent results
        result1 = await provider.execute_tool("success_tool", {})
        result2 = await provider.execute_tool("success_tool", {})

        assert result1.status == result2.status
        assert result1.result == result2.result


class TestToolProviderEdgeCases:
    """Test edge cases and error conditions."""

    @pytest.mark.asyncio
    async def test_execute_tool_with_complex_params(self):
        """Test tool execution with complex parameters."""
        provider = MockToolProvider()

        complex_params = {
            "nested": {"array": [1, 2, 3], "object": {"key": "value"}},
            "string": "test",
            "number": 42,
            "boolean": True,
        }

        result = await provider.execute_tool("success_tool", complex_params)
        assert result.status == "success"

    def test_format_result_with_none_values(self):
        """Test formatting result with None values."""
        provider = MockToolProvider()

        result = provider.format_result(status="success", result=None, error=None)

        assert result.status == "success"
        assert result.result is None
        assert result.error is None

    def test_tool_schema_immutability(self):
        """Test that tool schema doesn't change between calls."""
        provider = MockToolProvider()

        schema1 = provider.tool_schema
        schema2 = provider.tool_schema

        assert schema1.name == schema2.name
        assert schema1.description == schema2.description
        assert schema1.parameters == schema2.parameters

    def test_validate_params_with_empty_dict(self):
        """Test parameter validation with empty dictionary."""
        provider = MockToolProvider()

        with pytest.raises(ValueError):
            provider.validate_params({})  # Empty dict missing tool_id

    def test_validate_params_with_none(self):
        """Test parameter validation with None."""
        provider = MockToolProvider()

        with pytest.raises((ValueError, TypeError)):
            provider.validate_params(None)


class TestToolProviderDocumentation:
    """Test that tool providers are properly documented."""

    def test_tool_schema_has_description(self):
        """Test that tool schema includes description."""
        provider = MockToolProvider()
        schema = provider.tool_schema

        assert schema.description is not None
        assert len(schema.description) > 0
        assert isinstance(schema.description, str)

    def test_tool_schema_has_examples(self):
        """Test that tool schema includes examples."""
        provider = MockToolProvider()
        schema = provider.tool_schema

        assert schema.examples is not None
        assert len(schema.examples) > 0
        assert isinstance(schema.examples, list)

    def test_tool_schema_parameters_structure(self):
        """Test that parameters follow expected structure."""
        provider = MockToolProvider()
        schema = provider.tool_schema

        assert "type" in schema.parameters
        assert "properties" in schema.parameters
        assert schema.parameters["type"] == "object"

        properties = schema.parameters["properties"]
        assert "tool_id" in properties
        assert "params" in properties
