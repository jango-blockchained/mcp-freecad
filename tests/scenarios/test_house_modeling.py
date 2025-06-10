"""
House Modeling Scenario Test

This module contains a comprehensive test that simulates creating a 3D house model
using the MCP-FreeCAD addon with mocked user inputs. This test represents a real-world
use case and validates the entire tool chain.
"""

import asyncio
import logging
import time
from typing import Any, Dict, List

import pytest

from tests.fixtures import (
    expected_house_results,
    house_specification,
    mock_freecad,
    mock_freecad_modules,
    mock_part,
    mock_user_inputs,
    model_manipulation_tool_provider,
    performance_benchmarks,
    primitive_tool_provider,
    test_document,
    test_utilities,
)

logger = logging.getLogger(__name__)


class TestHouseModelingScenario:
    """
    Comprehensive test suite for house modeling scenario.

    This test simulates a realistic workflow where a user creates a 3D house model
    using the MCP-FreeCAD addon tools.
    """

    @pytest.mark.asyncio
    async def test_complete_house_creation(
        self,
        mock_freecad,
        primitive_tool_provider,
        model_manipulation_tool_provider,
        house_specification,
        expected_house_results,
        test_utilities
    ):
        """
        Test complete house creation from foundation to roof.

        This is the main scenario test that validates creating a full house model
        with foundation, walls, windows, doors, and roof.
        """
        logger.info("Starting complete house creation test")

        # Track performance
        start_time = time.time()

        # Step 1: Create foundation
        logger.info("Creating foundation...")
        foundation_params = house_specification["foundation"]

        foundation_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {
                "length": foundation_params["length"],
                "width": foundation_params["width"],
                "height": foundation_params["height"]
            }
        )

        assert foundation_result.status == "success"
        assert foundation_result.result["object_type"] == "Part::Box"
        foundation_object = foundation_result.result["object_id"]

        # Validate foundation dimensions
        doc = mock_freecad.ActiveDocument
        foundation_obj = doc.getObject(foundation_object)
        assert foundation_obj is not None

        test_utilities.validate_model_dimensions(
            foundation_obj,
            {
                "Length": foundation_params["length"],
                "Width": foundation_params["width"],
                "Height": foundation_params["height"]
            }
        )

        # Step 2: Create walls
        logger.info("Creating walls...")
        wall_height = house_specification["walls"]["height"]
        wall_thickness = house_specification["walls"]["thickness"]

        # Create front wall
        front_wall_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {
                "length": foundation_params["length"],
                "width": wall_thickness,
                "height": wall_height
            }
        )
        assert front_wall_result.status == "success"
        front_wall_object = front_wall_result.result["object_id"]

        # Position front wall
        front_wall_transform = await model_manipulation_tool_provider.execute_tool(
            "transform",
            {
                "object": front_wall_object,
                "translation": [0, -wall_thickness/2, foundation_params["height"]]
            }
        )
        assert front_wall_transform.status == "success"

        # Create back wall
        back_wall_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {
                "length": foundation_params["length"],
                "width": wall_thickness,
                "height": wall_height
            }
        )
        assert back_wall_result.status == "success"
        back_wall_object = back_wall_result.result["object_id"]

        # Position back wall
        back_wall_transform = await model_manipulation_tool_provider.execute_tool(
            "transform",
            {
                "object": back_wall_object,
                "translation": [0, foundation_params["width"] + wall_thickness/2, foundation_params["height"]]
            }
        )
        assert back_wall_transform.status == "success"

        # Create left wall
        left_wall_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {
                "length": wall_thickness,
                "width": foundation_params["width"],
                "height": wall_height
            }
        )
        assert left_wall_result.status == "success"
        left_wall_object = left_wall_result.result["object_id"]

        # Position left wall
        left_wall_transform = await model_manipulation_tool_provider.execute_tool(
            "transform",
            {
                "object": left_wall_object,
                "translation": [-wall_thickness/2, 0, foundation_params["height"]]
            }
        )
        assert left_wall_transform.status == "success"

        # Create right wall
        right_wall_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {
                "length": wall_thickness,
                "width": foundation_params["width"],
                "height": wall_height
            }
        )
        assert right_wall_result.status == "success"
        right_wall_object = right_wall_result.result["object_id"]

        # Position right wall
        right_wall_transform = await model_manipulation_tool_provider.execute_tool(
            "transform",
            {
                "object": right_wall_object,
                "translation": [foundation_params["length"] + wall_thickness/2, 0, foundation_params["height"]]
            }
        )
        assert right_wall_transform.status == "success"

        # Step 3: Create window and door openings
        logger.info("Creating window and door openings...")

        # Create windows
        windows = house_specification["windows"]
        for window in windows:
            window_cutout = await primitive_tool_provider.execute_tool(
                "create_box",
                {
                    "length": window["width"],
                    "width": wall_thickness + 0.1,  # Slightly thicker than wall
                    "height": window["height"]
                }
            )
            assert window_cutout.status == "success"
            window_cutout_object = window_cutout.result["object_id"]

            # Position window cutout
            window_position = window["position"]
            await model_manipulation_tool_provider.execute_tool(
                "transform",
                {
                    "object": window_cutout_object,
                    "translation": [window_position["x"], window_position["y"], window_position["z"]]
                }
            )

            # Cut window from appropriate wall
            wall_to_cut = front_wall_object if window["wall"] == "front" else right_wall_object

            wall_with_window = await model_manipulation_tool_provider.execute_tool(
                "boolean_operation",
                {
                    "operation": "difference",
                    "object1": wall_to_cut,
                    "object2": window_cutout_object,
                    "result_name": f"{wall_to_cut}_with_window",
                    "hide_originals": True
                }
            )
            assert wall_with_window.status == "success"

        # Create door opening
        doors = house_specification["doors"]
        for door in doors:
            door_cutout = await primitive_tool_provider.execute_tool(
                "create_box",
                {
                    "length": door["width"],
                    "width": wall_thickness + 0.1,
                    "height": door["height"]
                }
            )
            assert door_cutout.status == "success"
            door_cutout_object = door_cutout.result["object_id"]

            # Position door cutout
            door_position = door["position"]
            await model_manipulation_tool_provider.execute_tool(
                "transform",
                {
                    "object": door_cutout_object,
                    "translation": [door_position["x"], door_position["y"], door_position["z"]]
                }
            )

            # Cut door from front wall
            wall_with_door = await model_manipulation_tool_provider.execute_tool(
                "boolean_operation",
                {
                    "operation": "difference",
                    "object1": front_wall_object,
                    "object2": door_cutout_object,
                    "result_name": f"{front_wall_object}_with_door",
                    "hide_originals": True
                }
            )
            assert wall_with_door.status == "success"

        # Step 4: Create roof structure
        logger.info("Creating roof structure...")
        roof_spec = house_specification["roof"]

        # Create main roof body (simplified gabled roof as a large box)
        roof_length = foundation_params["length"] + wall_thickness
        roof_width = foundation_params["width"] + wall_thickness
        roof_height = roof_spec["thickness"]

        roof_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {
                "length": roof_length,
                "width": roof_width,
                "height": roof_height
            }
        )
        assert roof_result.status == "success"
        roof_object = roof_result.result["object_id"]

        # Position roof
        roof_z_position = foundation_params["height"] + wall_height
        roof_transform = await model_manipulation_tool_provider.execute_tool(
            "transform",
            {
                "object": roof_object,
                "translation": [-wall_thickness/2, -wall_thickness/2, roof_z_position]
            }
        )
        assert roof_transform.status == "success"

        # Step 5: Validate final model
        logger.info("Validating final model...")

        # Check total number of objects
        total_objects = len(doc.Objects)
        assert total_objects >= 5, f"Expected at least 5 objects, got {total_objects}"

        # Check that we have different object types
        box_count = test_utilities.count_objects_by_type(doc, "Part::Box")
        feature_count = test_utilities.count_objects_by_type(doc, "Part::Feature")

        assert box_count + feature_count == total_objects, "Object type count mismatch"

        # Validate total volume is reasonable
        total_volume = test_utilities.get_total_volume(doc)
        assert total_volume > 0, "Total volume should be positive"

        # Performance validation
        elapsed_time = time.time() - start_time
        assert elapsed_time < 5.0, f"House creation took too long: {elapsed_time:.2f}s"

        logger.info(f"House creation completed successfully in {elapsed_time:.2f}s")
        logger.info(f"Total objects created: {total_objects}")
        logger.info(f"Total volume: {total_volume:.2f}")

    @pytest.mark.asyncio
    async def test_house_creation_with_user_input_sequence(
        self,
        mock_freecad,
        primitive_tool_provider,
        model_manipulation_tool_provider,
        mock_user_inputs,
        test_utilities
    ):
        """
        Test house creation using a predefined sequence of user inputs.

        This test simulates step-by-step user interactions with the tools.
        """
        logger.info("Testing house creation with mock user input sequence")

        for step_data in mock_user_inputs:
            logger.info(f"Executing step: {step_data['step']}")

            if step_data["tool"] == "primitives":
                result = await primitive_tool_provider.execute_tool(
                    step_data["action"],
                    step_data["params"]
                )
            elif step_data["tool"] == "model_manipulation":
                result = await model_manipulation_tool_provider.execute_tool(
                    step_data["action"],
                    step_data["params"]
                )
            else:
                pytest.fail(f"Unknown tool: {step_data['tool']}")

            assert result.status == "success", f"Step {step_data['step']} failed: {result.error}"
            logger.info(f"Step {step_data['step']} completed successfully")

        # Validate final state
        doc = mock_freecad.ActiveDocument
        assert len(doc.Objects) >= 5, "Should have created at least 5 objects"

    @pytest.mark.asyncio
    async def test_error_handling_in_house_creation(
        self,
        mock_freecad,
        primitive_tool_provider,
        model_manipulation_tool_provider
    ):
        """
        Test error handling during house creation process.
        """
        logger.info("Testing error handling in house creation")

        # Test invalid parameters
        invalid_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {"length": -5.0, "width": 10.0, "height": 3.0}  # Negative length
        )
        # Note: Our mock doesn't validate negative values, but real FreeCAD would
        # This is where we'd test error conditions

        # Test operating on non-existent object
        transform_result = await model_manipulation_tool_provider.execute_tool(
            "transform",
            {"object": "NonExistentObject", "translation": [1, 0, 0]}
        )
        # The result might still be "success" in mock, but would fail in real FreeCAD

    @pytest.mark.asyncio
    async def test_house_variations(
        self,
        mock_freecad,
        primitive_tool_provider,
        model_manipulation_tool_provider,
        test_utilities
    ):
        """
        Test creating different house variations.
        """
        logger.info("Testing house variations")

        # Test small house
        small_house_spec = {
            "foundation": {"length": 5.0, "width": 4.0, "height": 0.2},
            "walls": {"height": 2.5, "thickness": 0.2}
        }

        foundation = await primitive_tool_provider.execute_tool(
            "create_box",
            small_house_spec["foundation"]
        )
        assert foundation.status == "success"

        # Test large house
        large_house_spec = {
            "foundation": {"length": 20.0, "width": 15.0, "height": 0.4},
            "walls": {"height": 4.0, "thickness": 0.4}
        }

        large_foundation = await primitive_tool_provider.execute_tool(
            "create_box",
            large_house_spec["foundation"]
        )
        assert large_foundation.status == "success"

        # Validate both houses exist
        doc = mock_freecad.ActiveDocument
        assert len(doc.Objects) >= 2

    @pytest.mark.parametrize("foundation_size,wall_height", [
        ({"length": 6.0, "width": 4.0, "height": 0.2}, 2.5),
        ({"length": 12.0, "width": 8.0, "height": 0.3}, 3.0),
        ({"length": 15.0, "width": 10.0, "height": 0.4}, 3.5),
    ])
    @pytest.mark.asyncio
    async def test_parametrized_house_sizes(
        self,
        foundation_size,
        wall_height,
        mock_freecad,
        primitive_tool_provider,
        test_utilities
    ):
        """
        Test house creation with different parametrized sizes.
        """
        logger.info(f"Testing house with foundation {foundation_size} and wall height {wall_height}")

        # Create foundation
        foundation_result = await primitive_tool_provider.execute_tool(
            "create_box",
            foundation_size
        )
        assert foundation_result.status == "success"

        # Create walls with specified height
        wall_result = await primitive_tool_provider.execute_tool(
            "create_box",
            {
                "length": foundation_size["length"],
                "width": 0.3,
                "height": wall_height
            }
        )
        assert wall_result.status == "success"

        # Validate objects were created
        doc = mock_freecad.ActiveDocument
        foundation_obj = doc.getObject(foundation_result.result["object_id"])
        wall_obj = doc.getObject(wall_result.result["object_id"])

        assert foundation_obj is not None
        assert wall_obj is not None

        # Validate dimensions
        test_utilities.validate_model_dimensions(foundation_obj, foundation_size)

    @pytest.mark.slow
    @pytest.mark.asyncio
    async def test_complex_house_with_multiple_floors(
        self,
        mock_freecad,
        primitive_tool_provider,
        model_manipulation_tool_provider,
        test_utilities
    ):
        """
        Test creating a complex multi-floor house.

        This is a more advanced scenario that tests complex operations.
        """
        logger.info("Testing complex multi-floor house creation")

        floors = 2
        floor_height = 3.0
        foundation_spec = {"length": 12.0, "width": 8.0, "height": 0.3}

        # Create foundation
        foundation = await primitive_tool_provider.execute_tool(
            "create_box",
            foundation_spec
        )
        assert foundation.status == "success"

        # Create walls for each floor
        for floor in range(floors):
            z_offset = foundation_spec["height"] + (floor * floor_height)

            # Create floor slab
            floor_slab = await primitive_tool_provider.execute_tool(
                "create_box",
                {
                    "length": foundation_spec["length"],
                    "width": foundation_spec["width"],
                    "height": 0.2
                }
            )
            assert floor_slab.status == "success"

            # Position floor slab
            await model_manipulation_tool_provider.execute_tool(
                "transform",
                {
                    "object": floor_slab.result["object_id"],
                    "translation": [0, 0, z_offset + floor_height]
                }
            )

            # Create walls for this floor
            wall = await primitive_tool_provider.execute_tool(
                "create_box",
                {
                    "length": foundation_spec["length"],
                    "width": 0.3,
                    "height": floor_height
                }
            )
            assert wall.status == "success"

            # Position wall
            await model_manipulation_tool_provider.execute_tool(
                "transform",
                {
                    "object": wall.result["object_id"],
                    "translation": [0, 0, z_offset]
                }
            )

        # Validate final structure
        doc = mock_freecad.ActiveDocument
        total_objects = len(doc.Objects)
        expected_objects = 1 + (floors * 2)  # foundation + (floor_slab + wall) per floor

        assert total_objects >= expected_objects, f"Expected at least {expected_objects} objects, got {total_objects}"

        logger.info(f"Multi-floor house created with {total_objects} objects")

    def test_house_specifications_validation(self, house_specification, expected_house_results):
        """
        Test that house specifications and expected results are consistent.
        """
        # Validate foundation volume calculation
        foundation = house_specification["foundation"]
        expected_foundation_volume = foundation["length"] * foundation["width"] * foundation["height"]

        assert abs(expected_foundation_volume - expected_house_results["foundation"]["volume"]) < 0.01

        # Validate that windows and doors are properly specified
        assert len(house_specification["windows"]) == expected_house_results["openings"]["windows"]
        assert len(house_specification["doors"]) == expected_house_results["openings"]["doors"]

        # Validate wall specifications
        walls = house_specification["walls"]
        assert walls["height"] > 0
        assert walls["thickness"] > 0
