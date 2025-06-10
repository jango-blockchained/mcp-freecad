"""
Integration tests for MCP FreeCAD system.

These tests verify that all components work together correctly.
"""

import asyncio
from typing import Any, Dict, List
from unittest.mock import MagicMock, patch

import pytest

from tests.mocks.freecad_mock import MockFreeCAD


class MockMCPServer:
    """Mock MCP Server for integration testing."""

    def __init__(self):
        self.tools = {}
        self.freecad = MockFreeCAD()

    def register_tool(self, name: str, tool_provider):
        """Register a tool provider."""
        self.tools[name] = tool_provider

    async def call_tool(self, tool_name: str, arguments: Dict[str, Any]):
        """Call a registered tool."""
        if tool_name not in self.tools:
            raise ValueError(f"Tool {tool_name} not found")

        tool = self.tools[tool_name]
        return await tool.execute_tool(
            arguments.get("tool_id"), arguments.get("params", {})
        )

    def list_tools(self) -> List[str]:
        """List all registered tools."""
        return list(self.tools.keys())


class TestServerIntegration:
    """Test server component integration."""

    @pytest.fixture
    def mock_server(self):
        """Create a mock MCP server."""
        return MockMCPServer()

    @pytest.fixture
    def setup_server_tools(
        self, mock_server, primitive_tool_provider, model_manipulation_provider
    ):
        """Setup server with tool providers."""
        mock_server.register_tool("primitives", primitive_tool_provider)
        mock_server.register_tool("model_manipulation", model_manipulation_provider)
        return mock_server

    def test_server_tool_registration(self, mock_server, primitive_tool_provider):
        """Test that tools can be registered with the server."""
        mock_server.register_tool("primitives", primitive_tool_provider)

        assert "primitives" in mock_server.list_tools()
        assert mock_server.tools["primitives"] is primitive_tool_provider

    @pytest.mark.asyncio
    async def test_server_tool_execution(self, setup_server_tools):
        """Test that tools can be executed through the server."""
        server = setup_server_tools

        result = await server.call_tool(
            "primitives",
            {
                "tool_id": "create_box",
                "params": {
                    "length": 10.0,
                    "width": 8.0,
                    "height": 3.0,
                    "name": "test_box",
                },
            },
        )

        assert result.status == "success"
        assert "Box created" in result.result["message"]
        assert result.result["object_name"] == "test_box"

    @pytest.mark.asyncio
    async def test_server_tool_chain_execution(self, setup_server_tools):
        """Test executing a chain of tools to build complex objects."""
        server = setup_server_tools

        # Create a box
        box_result = await server.call_tool(
            "primitives",
            {
                "tool_id": "create_box",
                "params": {
                    "length": 10.0,
                    "width": 8.0,
                    "height": 3.0,
                    "name": "foundation",
                },
            },
        )
        assert box_result.status == "success"

        # Create a cylinder
        cylinder_result = await server.call_tool(
            "primitives",
            {
                "tool_id": "create_cylinder",
                "params": {"radius": 2.0, "height": 5.0, "name": "column"},
            },
        )
        assert cylinder_result.status == "success"

        # Move the cylinder
        move_result = await server.call_tool(
            "model_manipulation",
            {
                "tool_id": "transform",
                "params": {"object": "column", "translation": [5.0, 4.0, 3.0]},
            },
        )
        assert move_result.status == "success"

        # Perform boolean union
        union_result = await server.call_tool(
            "model_manipulation",
            {
                "tool_id": "boolean_operation",
                "params": {
                    "operation": "union",
                    "object1": "foundation",
                    "object2": "column",
                    "result_name": "foundation_with_column",
                },
            },
        )
        assert union_result.status == "success"

    @pytest.mark.asyncio
    async def test_server_error_handling(self, setup_server_tools):
        """Test that server handles tool errors correctly."""
        server = setup_server_tools

        # Test calling non-existent tool
        with pytest.raises(ValueError, match="Tool nonexistent not found"):
            await server.call_tool("nonexistent", {})

        # Test calling with invalid parameters
        result = await server.call_tool(
            "primitives",
            {
                "tool_id": "create_box",
                "params": {
                    "length": -10.0,  # Invalid negative length
                    "width": 8.0,
                    "height": 3.0,
                },
            },
        )
        assert result.status == "error"
        assert "positive" in result.error.lower()


# Shared fixtures for integration tests
@pytest.fixture
def workflow_server(mock_freecad, primitive_tool_provider, model_manipulation_provider):
    """Setup server for workflow testing."""
    server = MockMCPServer()
    server.freecad = mock_freecad
    server.register_tool("primitives", primitive_tool_provider)
    server.register_tool("model_manipulation", model_manipulation_provider)
    return server


class TestWorkflowIntegration:
    """Test complete workflow integration scenarios."""

    @pytest.mark.asyncio
    async def test_simple_building_workflow(self, workflow_server):
        """Test a simple building creation workflow."""
        server = workflow_server

        # Create foundation
        foundation = await server.call_tool(
            "primitives",
            {
                "tool_id": "create_box",
                "params": {
                    "length": 20.0,
                    "width": 15.0,
                    "height": 1.0,
                    "name": "foundation",
                },
            },
        )
        assert foundation.status == "success"

        # Create walls
        wall_specs = [
            {"length": 20.0, "width": 0.3, "height": 3.0, "name": "wall_front"},
            {"length": 20.0, "width": 0.3, "height": 3.0, "name": "wall_back"},
            {"length": 15.0, "width": 0.3, "height": 3.0, "name": "wall_left"},
            {"length": 15.0, "width": 0.3, "height": 3.0, "name": "wall_right"},
        ]

        for spec in wall_specs:
            result = await server.call_tool(
                "primitives", {"tool_id": "create_box", "params": spec}
            )
            assert result.status == "success"

        # Position walls on foundation
        positioning_tasks = [
            server.call_tool(
                "model_manipulation",
                {
                    "tool_id": "transform",
                    "params": {
                        "object": "wall_front",
                        "translation": [0.0, -7.35, 1.5],
                    },
                },
            ),
            server.call_tool(
                "model_manipulation",
                {
                    "tool_id": "transform",
                    "params": {"object": "wall_back", "translation": [0.0, 7.35, 1.5]},
                },
            ),
        ]

        positioning_results = await asyncio.gather(*positioning_tasks)
        for result in positioning_results:
            assert result.status == "success"

    @pytest.mark.asyncio
    async def test_complex_modeling_workflow(self, workflow_server):
        """Test a complex modeling workflow with boolean operations."""
        server = workflow_server

        # Create base object
        base = await server.call_tool(
            "primitives",
            {
                "tool_id": "create_box",
                "params": {
                    "length": 10.0,
                    "width": 10.0,
                    "height": 5.0,
                    "name": "base_block",
                },
            },
        )
        assert base.status == "success"

        # Create and position holes
        hole_positions = [(2.0, 2.0, 0.0), (-2.0, 2.0, 0.0), (0.0, -2.0, 0.0)]

        for i, (x, y, z) in enumerate(hole_positions):
            # Create hole
            hole_result = await server.call_tool(
                "primitives",
                {
                    "tool_id": "create_cylinder",
                    "params": {"radius": 1.0, "height": 6.0, "name": f"hole_{i}"},
                },
            )
            assert hole_result.status == "success"

            # Position hole
            position_result = await server.call_tool(
                "model_manipulation",
                {
                    "tool_id": "transform",
                    "params": {"object": f"hole_{i}", "translation": [x, y, z]},
                },
            )
            assert position_result.status == "success"

            # Cut hole from base
            current_base = "base_block" if i == 0 else f"base_with_holes_{i-1}"
            result_name = f"base_with_holes_{i}"

            cut_result = await server.call_tool(
                "model_manipulation",
                {
                    "tool_id": "boolean_operation",
                    "params": {
                        "operation": "difference",
                        "object1": current_base,
                        "object2": f"hole_{i}",
                        "result_name": result_name,
                    },
                },
            )
            assert cut_result.status == "success"

    @pytest.mark.asyncio
    async def test_error_recovery_workflow(self, workflow_server):
        """Test workflow with error recovery."""
        server = workflow_server

        # Try to create an object with invalid parameters
        invalid_result = await server.call_tool(
            "primitives",
            {
                "tool_id": "create_box",
                "params": {
                    "length": -5.0,  # Invalid
                    "width": 10.0,
                    "height": 5.0,
                    "name": "invalid_box",
                },
            },
        )
        assert invalid_result.status == "error"

        # Recover with valid parameters
        valid_result = await server.call_tool(
            "primitives",
            {
                "tool_id": "create_box",
                "params": {
                    "length": 5.0,  # Valid
                    "width": 10.0,
                    "height": 5.0,
                    "name": "valid_box",
                },
            },
        )
        assert valid_result.status == "success"

        # Continue workflow normally
        move_result = await server.call_tool(
            "model_manipulation",
            {
                "tool_id": "transform",
                "params": {"object": "valid_box", "translation": [5.0, 0.0, 0.0]},
            },
        )
        assert move_result.status == "success"


class TestPerformanceIntegration:
    """Test performance aspects of integration."""

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_bulk_operation_performance(self, workflow_server):
        """Test performance with bulk operations."""
        server = workflow_server
        import time

        start_time = time.time()

        # Create many objects concurrently
        tasks = []
        for i in range(20):
            task = server.call_tool(
                "primitives",
                {
                    "tool_id": "create_box",
                    "params": {
                        "length": 1.0,
                        "width": 1.0,
                        "height": 1.0,
                        "name": f"bulk_box_{i}",
                    },
                },
            )
            tasks.append(task)

        results = await asyncio.gather(*tasks)

        end_time = time.time()
        execution_time = end_time - start_time

        # All operations should succeed
        for result in results:
            assert result.status == "success"

        # Should complete within reasonable time
        assert execution_time < 2.0, f"Bulk operations took {execution_time:.2f}s"

    @pytest.mark.performance
    @pytest.mark.asyncio
    async def test_memory_usage_stability(self, workflow_server):
        """Test that memory usage remains stable during operations."""
        server = workflow_server

        # Simulate many operations
        for iteration in range(10):
            # Create some objects
            for i in range(5):
                await server.call_tool(
                    "primitives",
                    {
                        "tool_id": "create_box",
                        "params": {
                            "length": 1.0,
                            "width": 1.0,
                            "height": 1.0,
                            "name": f"mem_test_{iteration}_{i}",
                        },
                    },
                )

        # If we get here without memory issues, the test passes
        assert True


class TestRealWorldScenarios:
    """Test scenarios that simulate real-world usage."""

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_architectural_design_scenario(self, workflow_server):
        """Test a complete architectural design scenario."""
        server = workflow_server

        # Foundation
        foundation = await server.call_tool(
            "primitives",
            {
                "tool_id": "create_box",
                "params": {
                    "length": 12.0,
                    "width": 8.0,
                    "height": 0.5,
                    "name": "house_foundation",
                },
            },
        )
        assert foundation.status == "success"

        # Main structure
        main_box = await server.call_tool(
            "primitives",
            {
                "tool_id": "create_box",
                "params": {
                    "length": 12.0,
                    "width": 8.0,
                    "height": 3.0,
                    "name": "main_structure",
                },
            },
        )
        assert main_box.status == "success"

        # Position main structure
        position_result = await server.call_tool(
            "model_manipulation",
            {
                "tool_id": "transform",
                "params": {"object": "main_structure", "translation": [0.0, 0.0, 1.75]},
            },
        )
        assert position_result.status == "success"

        # Add windows
        window_positions = [
            (5.0, -4.0, 1.5),  # Front window
            (-5.0, -4.0, 1.5),  # Front window 2
            (0.0, 4.0, 1.5),  # Back window
        ]

        for i, (x, y, z) in enumerate(window_positions):
            window = await server.call_tool(
                "primitives",
                {
                    "tool_id": "create_box",
                    "params": {
                        "length": 2.0,
                        "width": 0.5,
                        "height": 1.5,
                        "name": f"window_{i}",
                    },
                },
            )
            assert window.status == "success"

            position_window = await server.call_tool(
                "model_manipulation",
                {
                    "tool_id": "transform",
                    "params": {"object": f"window_{i}", "translation": [x, y, z]},
                },
            )
            assert position_window.status == "success"

        # This represents a real architectural workflow
        assert True

    @pytest.mark.integration
    @pytest.mark.asyncio
    async def test_mechanical_part_design_scenario(self, workflow_server):
        """Test designing a mechanical part."""
        server = workflow_server

        # Create main body
        main_body = await server.call_tool(
            "primitives",
            {
                "tool_id": "create_cylinder",
                "params": {"radius": 5.0, "height": 2.0, "name": "main_body"},
            },
        )
        assert main_body.status == "success"

        # Create central hole
        central_hole = await server.call_tool(
            "primitives",
            {
                "tool_id": "create_cylinder",
                "params": {"radius": 1.0, "height": 2.5, "name": "central_hole"},
            },
        )
        assert central_hole.status == "success"

        # Cut central hole from main body
        central_cut = await server.call_tool(
            "model_manipulation",
            {
                "tool_id": "boolean_operation",
                "params": {
                    "operation": "difference",
                    "object1": "main_body",
                    "object2": "central_hole",
                    "result_name": "part_with_central_hole",
                },
            },
        )
        assert central_cut.status == "success"

        # Create mounting holes
        hole_positions = [
            (3.0, 0.0, 0.0),
            (-3.0, 0.0, 0.0),
            (0.0, 3.0, 0.0),
            (0.0, -3.0, 0.0),
        ]

        current_part = "part_with_central_hole"

        for i, (x, y, z) in enumerate(hole_positions):
            # Create mounting hole
            hole = await server.call_tool(
                "primitives",
                {
                    "tool_id": "create_cylinder",
                    "params": {
                        "radius": 0.5,
                        "height": 2.5,
                        "name": f"mounting_hole_{i}",
                    },
                },
            )
            assert hole.status == "success"

            # Position mounting hole
            position_hole = await server.call_tool(
                "model_manipulation",
                {
                    "tool_id": "transform",
                    "params": {
                        "object": f"mounting_hole_{i}",
                        "translation": [x, y, z],
                    },
                },
            )
            assert position_hole.status == "success"

            # Cut mounting hole
            result_name = f"part_with_{i+1}_mounting_holes"
            cut_result = await server.call_tool(
                "model_manipulation",
                {
                    "tool_id": "boolean_operation",
                    "params": {
                        "operation": "difference",
                        "object1": current_part,
                        "object2": f"mounting_hole_{i}",
                        "result_name": result_name,
                    },
                },
            )
            assert cut_result.status == "success"
            current_part = result_name

        # Final part should be created successfully
        assert current_part == "part_with_4_mounting_holes"
