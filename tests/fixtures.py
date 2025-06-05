"""
Pytest fixtures for MCP-FreeCAD testing.

This module provides common fixtures and utilities for testing the MCP-FreeCAD addon.
"""

import pytest
import sys
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

from .mocks.freecad_mock import MockFreeCAD, MockPart, get_mock_freecad, get_mock_part
from src.mcp_freecad.tools.primitives import PrimitiveToolProvider
from src.mcp_freecad.tools.model_manipulation import ModelManipulationToolProvider


@pytest.fixture
def mock_freecad():
    """Provide a fresh MockFreeCAD instance for each test."""
    return get_mock_freecad()


@pytest.fixture
def mock_part():
    """Provide a MockPart instance for testing."""
    return get_mock_part()


@pytest.fixture
def mock_freecad_modules(mock_freecad, mock_part):
    """Mock FreeCAD and Part modules in sys.modules."""
    with patch.dict(sys.modules, {
        'FreeCAD': mock_freecad,
        'Part': mock_part
    }):
        yield mock_freecad, mock_part


@pytest.fixture
def primitive_tool_provider(mock_freecad):
    """Provide a PrimitiveToolProvider with mocked FreeCAD."""
    return PrimitiveToolProvider(freecad_app=mock_freecad)


@pytest.fixture
def model_manipulation_tool_provider(mock_freecad):
    """Provide a ModelManipulationToolProvider with mocked FreeCAD."""
    return ModelManipulationToolProvider(freecad_app=mock_freecad)


@pytest.fixture
def model_manipulation_provider(model_manipulation_tool_provider):
    """Alias for model_manipulation_tool_provider for backward compatibility."""
    return model_manipulation_tool_provider


@pytest.fixture
def test_document(mock_freecad):
    """Create a test document with the mock FreeCAD."""
    doc = mock_freecad.newDocument("TestDocument")
    return doc


@pytest.fixture
def house_specification():
    """Provide standard house specifications for testing."""
    return {
        "foundation": {
            "length": 10.0,
            "width": 8.0,
            "height": 0.3,
            "material": "concrete"
        },
        "walls": {
            "height": 3.0,
            "thickness": 0.3,
            "material": "brick"
        },
        "roof": {
            "type": "gabled",
            "pitch": 45.0,
            "thickness": 0.2,
            "material": "wood"
        },
        "windows": [
            {
                "id": "front_window_1",
                "width": 1.2,
                "height": 1.5,
                "position": {"x": 2.0, "y": 0.0, "z": 1.0},
                "wall": "front"
            },
            {
                "id": "front_window_2",
                "width": 1.2,
                "height": 1.5,
                "position": {"x": 6.0, "y": 0.0, "z": 1.0},
                "wall": "front"
            },
            {
                "id": "side_window",
                "width": 1.0,
                "height": 1.2,
                "position": {"x": 10.0, "y": 3.0, "z": 1.0},
                "wall": "right"
            }
        ],
        "doors": [
            {
                "id": "front_door",
                "width": 0.9,
                "height": 2.1,
                "position": {"x": 4.5, "y": 0.0, "z": 0.0},
                "wall": "front"
            }
        ]
    }


@pytest.fixture
def expected_house_results():
    """Expected results for house modeling tests."""
    return {
        "foundation": {
            "volume": 24.0,  # 10 * 8 * 0.3
            "area": 164.8,   # Approximate surface area
            "object_type": "Part::Box"
        },
        "wall_volumes": {
            "front": 8.1,    # (10 * 3 * 0.3) - window/door cutouts
            "back": 9.0,     # 10 * 3 * 0.3
            "left": 7.2,     # 8 * 3 * 0.3
            "right": 6.84    # (8 * 3 * 0.3) - window cutout
        },
        "total_wall_volume": 31.14,
        "total_volume": 55.14,  # foundation + walls
        "openings": {
            "windows": 3,
            "doors": 1
        }
    }


@pytest.fixture
def mock_user_inputs():
    """Mock user input sequences for house creation."""
    return [
        {
            "step": "create_foundation",
            "tool": "primitives",
            "action": "create_box",
            "params": {"length": 10.0, "width": 8.0, "height": 0.3}
        },
        {
            "step": "create_front_wall",
            "tool": "primitives",
            "action": "create_box",
            "params": {"length": 10.0, "width": 0.3, "height": 3.0}
        },
        {
            "step": "position_front_wall",
            "tool": "model_manipulation",
            "action": "transform",
            "params": {
                "object": "Box001",
                "translation": [0, -0.15, 0.3]
            }
        },
        {
            "step": "create_back_wall",
            "tool": "primitives",
            "action": "create_box",
            "params": {"length": 10.0, "width": 0.3, "height": 3.0}
        },
        {
            "step": "position_back_wall",
            "tool": "model_manipulation",
            "action": "transform",
            "params": {
                "object": "Box002",
                "translation": [0, 8.15, 0.3]
            }
        },
        {
            "step": "create_left_wall",
            "tool": "primitives",
            "action": "create_box",
            "params": {"length": 0.3, "width": 8.0, "height": 3.0}
        },
        {
            "step": "position_left_wall",
            "tool": "model_manipulation",
            "action": "transform",
            "params": {
                "object": "Box003",
                "translation": [-0.15, 0, 0.3]
            }
        },
        {
            "step": "create_right_wall",
            "tool": "primitives",
            "action": "create_box",
            "params": {"length": 0.3, "width": 8.0, "height": 3.0}
        },
        {
            "step": "position_right_wall",
            "tool": "model_manipulation",
            "action": "transform",
            "params": {
                "object": "Box004",
                "translation": [10.15, 0, 0.3]
            }
        }
    ]


@pytest.fixture
def performance_benchmarks():
    """Performance benchmarks for testing."""
    return {
        "primitive_creation": {
            "max_time_seconds": 0.1,
            "max_memory_mb": 10
        },
        "boolean_operation": {
            "max_time_seconds": 0.5,
            "max_memory_mb": 50
        },
        "house_complete_creation": {
            "max_time_seconds": 5.0,
            "max_memory_mb": 100
        }
    }


class TestUtilities:
    """Utility functions for testing."""

    @staticmethod
    def validate_model_dimensions(obj, expected_dimensions: Dict[str, float], tolerance: float = 0.01):
        """Validate that an object has expected dimensions."""
        for attr, expected_value in expected_dimensions.items():
            if hasattr(obj, attr):
                actual_value = getattr(obj, attr)
                assert abs(actual_value - expected_value) <= tolerance, \
                    f"{attr}: expected {expected_value}, got {actual_value}"

    @staticmethod
    def validate_volume(shape, expected_volume: float, tolerance: float = 0.01):
        """Validate shape volume."""
        if hasattr(shape, 'Volume'):
            actual_volume = shape.Volume
            assert abs(actual_volume - expected_volume) <= tolerance, \
                f"Volume: expected {expected_volume}, got {actual_volume}"

    @staticmethod
    def count_objects_by_type(document, object_type: str) -> int:
        """Count objects of a specific type in a document."""
        return len([obj for obj in document.Objects if obj.TypeId == object_type])

    @staticmethod
    def get_total_volume(document) -> float:
        """Calculate total volume of all objects in document."""
        total_volume = 0.0
        for obj in document.Objects:
            if hasattr(obj, 'Shape') and hasattr(obj.Shape, 'Volume'):
                total_volume += obj.Shape.Volume
        return total_volume


@pytest.fixture
def test_utilities():
    """Provide test utility functions."""
    return TestUtilities()


# Parametrized fixtures for testing multiple scenarios
@pytest.fixture(params=[
    {"length": 10.0, "width": 5.0, "height": 3.0},
    {"length": 20.0, "width": 10.0, "height": 5.0},
    {"length": 1.0, "width": 1.0, "height": 1.0}
])
def box_parameters(request):
    """Parametrized box dimensions for testing."""
    return request.param


@pytest.fixture(params=[
    {"radius": 5.0, "height": 10.0},
    {"radius": 2.5, "height": 5.0},
    {"radius": 1.0, "height": 1.0}
])
def cylinder_parameters(request):
    """Parametrized cylinder dimensions for testing."""
    return request.param


@pytest.fixture(params=["union", "difference", "intersection"])
def boolean_operations(request):
    """Parametrized boolean operations for testing."""
    return request.param
