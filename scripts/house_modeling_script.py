#!/usr/bin/env python3
"""
Live House Modeling Script for FreeCAD

This script creates a 3D house model step by step with visual delays.
Can be run by FreeCAD using: FreeCAD --console house_modeling_script.py
"""

import os
import sys
import time

# Add some initial output to verify the script is running
print("🏠 Starting Live House Modeling Script...")
print("=" * 60)

try:
    import FreeCAD
    import Part
    print("✅ FreeCAD modules imported successfully!")
except ImportError as e:
    print(f"❌ Failed to import FreeCAD modules: {e}")
    print("This script must be run from within FreeCAD!")
    sys.exit(1)

# Configuration
STEP_DELAY = 2.0  # Seconds between each step
HOUSE_SPEC = {
    "foundation": {
        "length": 10.0,
        "width": 8.0,
        "height": 0.3
    },
    "walls": {
        "height": 3.0,
        "thickness": 0.3
    },
    "windows": [
        {"id": "front_window_1", "width": 1.2, "height": 1.5, "position": {"x": 2.0, "y": 0.0, "z": 1.0}},
        {"id": "front_window_2", "width": 1.2, "height": 1.5, "position": {"x": 6.0, "y": 0.0, "z": 1.0}}
    ],
    "doors": [
        {"id": "front_door", "width": 0.9, "height": 2.1, "position": {"x": 4.5, "y": 0.0, "z": 0.0}}
    ]
}

def log_step(message):
    """Log a step with emoji and formatting."""
    print(f"\n{'='*50}")
    print(f"{message}")
    print(f"{'='*50}")

def wait_step():
    """Wait between steps for visualization."""
    time.sleep(STEP_DELAY)

def setup_document():
    """Set up the FreeCAD document and view."""
    log_step("🏠 Setting up FreeCAD Document")

    # Create new document
    doc = FreeCAD.newDocument("LiveHouseModel")
    FreeCAD.setActiveDocument(doc.Name)

    print(f"✅ Document created: {doc.Name}")
    wait_step()

    return doc

def create_foundation(doc, foundation_spec):
    """Create the house foundation."""
    log_step("🏗️  Creating Foundation")

    # Create foundation box
    foundation = doc.addObject("Part::Box", "Foundation")
    foundation.Length = foundation_spec["length"]
    foundation.Width = foundation_spec["width"]
    foundation.Height = foundation_spec["height"]

    doc.recompute()

    print(f"✅ Foundation created: {foundation.Name}")
    print(f"   Dimensions: {foundation.Length} × {foundation.Width} × {foundation.Height} mm")
    wait_step()

    return foundation

def create_wall(doc, wall_name, wall_params, translation):
    """Create and position a single wall."""
    log_step(f"🧱 Creating {wall_name.title()}")

    # Create wall box
    wall = doc.addObject("Part::Box", wall_name.replace(' ', '_').title())
    wall.Length = wall_params["length"]
    wall.Width = wall_params["width"]
    wall.Height = wall_params["height"]

    # Position the wall
    wall.Placement.Base.x = translation[0]
    wall.Placement.Base.y = translation[1]
    wall.Placement.Base.z = translation[2]

    doc.recompute()

    print(f"✅ {wall_name.title()} created: {wall.Name}")
    print(f"   Position: ({translation[0]}, {translation[1]}, {translation[2]})")
    wait_step()

    return wall

def create_walls(doc, foundation_spec, wall_spec):
    """Create all house walls."""
    log_step("🧱 Creating All Walls")

    wall_height = wall_spec["height"]
    wall_thickness = wall_spec["thickness"]
    walls = []

    # Wall configurations
    wall_configs = [
        {
            "name": "front wall",
            "params": {"length": foundation_spec["length"], "width": wall_thickness, "height": wall_height},
            "translation": [0, -wall_thickness/2, foundation_spec["height"]]
        },
        {
            "name": "back wall",
            "params": {"length": foundation_spec["length"], "width": wall_thickness, "height": wall_height},
            "translation": [0, foundation_spec["width"] + wall_thickness/2, foundation_spec["height"]]
        },
        {
            "name": "left wall",
            "params": {"length": wall_thickness, "width": foundation_spec["width"], "height": wall_height},
            "translation": [-wall_thickness/2, 0, foundation_spec["height"]]
        },
        {
            "name": "right wall",
            "params": {"length": wall_thickness, "width": foundation_spec["width"], "height": wall_height},
            "translation": [foundation_spec["length"] + wall_thickness/2, 0, foundation_spec["height"]]
        }
    ]

    # Create each wall
    for wall_config in wall_configs:
        wall = create_wall(
            doc,
            wall_config["name"],
            wall_config["params"],
            wall_config["translation"]
        )
        walls.append(wall)

    print(f"✅ All walls completed: {[w.Name for w in walls]}")
    return walls

def create_opening(doc, opening_name, opening_params, position):
    """Create a window or door opening."""
    log_step(f"🪟 Creating {opening_name.title()}")

    # Create opening box
    opening = doc.addObject("Part::Box", opening_name.replace(' ', '_').title())
    opening.Length = opening_params["length"]
    opening.Width = opening_params["width"]
    opening.Height = opening_params["height"]

    # Position the opening
    opening.Placement.Base.x = position[0]
    opening.Placement.Base.y = position[1]
    opening.Placement.Base.z = position[2]

    doc.recompute()

    print(f"✅ {opening_name.title()} created: {opening.Name}")
    print(f"   Position: ({position[0]}, {position[1]}, {position[2]})")
    wait_step()

    return opening

def create_openings(doc, windows, doors, wall_thickness):
    """Create all window and door openings."""
    log_step("🪟 Creating Windows and Doors")

    openings = []

    # Create windows
    for window in windows:
        opening = create_opening(
            doc,
            f"window {window['id']}",
            {
                "length": window["width"],
                "width": wall_thickness + 0.1,
                "height": window["height"]
            },
            [window["position"]["x"], window["position"]["y"], window["position"]["z"]]
        )
        openings.append(opening)

    # Create doors
    for door in doors:
        opening = create_opening(
            doc,
            f"door {door['id']}",
            {
                "length": door["width"],
                "width": wall_thickness + 0.1,
                "height": door["height"]
            },
            [door["position"]["x"], door["position"]["y"], door["position"]["z"]]
        )
        openings.append(opening)

    print(f"✅ All openings completed: {[o.Name for o in openings]}")
    return openings

def save_document(doc):
    """Save the document to disk."""
    log_step("💾 Saving Document")

    try:
        # Get current working directory
        current_dir = os.getcwd()
        filename = "LiveHouseModel.FCStd"
        filepath = os.path.join(current_dir, filename)

        print(f"📁 Saving to: {filepath}")

        # Save the document
        doc.saveAs(filepath)

        # Verify the file was created
        if os.path.exists(filepath):
            file_size = os.path.getsize(filepath)
            print(f"✅ Document saved successfully!")
            print(f"   File: {filename}")
            print(f"   Size: {file_size} bytes")
            print(f"   Location: {current_dir}")
        else:
            print(f"⚠️  File was not created at expected location")

        # Also try to save in user's Documents if different location
        try:
            home_dir = os.path.expanduser("~")
            alt_filepath = os.path.join(home_dir, "Documents", filename)
            if not os.path.exists(alt_filepath):  # Don't overwrite if exists
                doc.saveAs(alt_filepath)
                if os.path.exists(alt_filepath):
                    print(f"✅ Also saved backup to: {alt_filepath}")
        except Exception as e:
            print(f"📝 Note: Could not save backup copy: {e}")

    except Exception as e:
        print(f"❌ Error saving document: {e}")
        # Try alternative save method
        try:
            print("🔄 Trying alternative save method...")
            doc.save()
            print("✅ Document saved using default method")
        except Exception as e2:
            print(f"❌ Alternative save also failed: {e2}")

def finalize_model(doc):
    """Add final touches to the model."""
    log_step("🎨 Finalizing Model")

    # Count objects
    object_count = len(doc.Objects)

    print(f"✅ Model finalized with {object_count} objects!")
    wait_step()

def main():
    """Main house modeling function."""
    try:
        # Setup
        doc = setup_document()

        # Get specifications
        foundation_spec = HOUSE_SPEC["foundation"]
        wall_spec = HOUSE_SPEC["walls"]
        windows = HOUSE_SPEC["windows"]
        doors = HOUSE_SPEC["doors"]

        # Build the house step by step
        foundation = create_foundation(doc, foundation_spec)
        walls = create_walls(doc, foundation_spec, wall_spec)
        openings = create_openings(doc, windows, doors, wall_spec["thickness"])

        # Finalize
        finalize_model(doc)

        # Save the document
        save_document(doc)

        # Summary
        log_step("🎉 House Modeling Completed Successfully!")
        print(f"📊 Summary:")
        print(f"  - Foundation: {foundation.Name}")
        print(f"  - Walls: {[w.Name for w in walls]}")
        print(f"  - Openings: {[o.Name for o in openings]}")
        print(f"  - Total objects: {len(doc.Objects)}")
        print(f"\n🔍 Model has been saved and is ready for inspection!")
        print(f"You can now:")
        print(f"  - Open the saved file: LiveHouseModel.FCStd")
        print(f"  - Double-click the file to open in FreeCAD GUI")
        print(f"  - Use File -> Open Recent in FreeCAD")
        print(f"  - Export to other formats: STEP, STL, etc.")

        # For console mode, give user time to see the output
        print(f"\n⏳ Script completed successfully!")

    except Exception as e:
        log_step(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

# Run the main function
if __name__ == "__main__":
    main()
