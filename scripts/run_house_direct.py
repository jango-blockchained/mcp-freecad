#!/usr/bin/env python3
"""
Direct FreeCAD House Modeling Runner

This creates a single script that FreeCAD can execute directly,
combining the execution logic with the house modeling code.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path


def create_combined_script():
    """Create a combined script that includes both execution and house modeling logic."""

    # Read the house modeling script
    script_path = Path(__file__).parent / "house_modeling_script.py"

    if not script_path.exists():
        print(f"❌ House modeling script not found: {script_path}")
        return None

    with open(script_path, "r") as f:
        house_script_content = f.read()

    # Create combined script that will execute and then exit
    combined_script = f'''
# Combined FreeCAD House Modeling Script
# Auto-executes the house modeling and then exits

import sys
import os

print("🏠 FreeCAD House Modeling - Direct Execution")
print("=" * 50)

try:
    # Change to the correct directory
    os.chdir(r"{Path(__file__).parent}")

    # Execute the house modeling script content
    exec("""
{house_script_content}
""")

    print("\\n🎉 House modeling completed successfully!")
    print("📄 Document 'LiveHouseModel' has been created.")
    print("💾 Saving document...")

    # Save the document
    if 'doc' in locals():
        doc.save()
        print(f"✅ Document saved!")

except Exception as e:
    print(f"\\n❌ Error during execution: {{e}}")
    import traceback
    traceback.print_exc()

finally:
    print("\\n🔚 Execution complete. Exiting...")
    # Force exit
    import sys
    try:
        if hasattr(sys, 'exit'):
            sys.exit(0)
    except:
        pass
'''

    return combined_script


def main():
    """Main execution function."""
    print("🏠 Live House Modeling - Direct Python Runner")
    print("=" * 50)

    # Check FreeCAD AppImage
    freecad_path = (
        Path(__file__).parent / "FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage"
    )

    if not freecad_path.exists():
        print(f"❌ FreeCAD AppImage not found: {freecad_path}")
        print("Please ensure the FreeCAD AppImage is in the project root directory.")
        return 1

    # Create combined script
    combined_script = create_combined_script()
    if not combined_script:
        return 1

    # Write to temporary file
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as temp_file:
        temp_file.write(combined_script)
        temp_script_path = temp_file.name

    try:
        print(f"🚀 Starting FreeCAD with combined script...")
        print(f"📄 Temporary script: {temp_script_path}")
        print("🎛️  Mode: Console mode with direct execution")
        print()
        print("What will happen:")
        print("1. FreeCAD will start in console mode")
        print("2. The house modeling script will execute automatically")
        print("3. You'll see step-by-step progress")
        print("4. Model will be created and saved")
        print("5. FreeCAD will exit automatically")
        print()

        # Set Qt platform
        env = os.environ.copy()
        env["QT_QPA_PLATFORM"] = "xcb"

        # Prepare command
        cmd = [str(freecad_path), "--console"]

        print(f"🔧 Running: {' '.join(cmd)}")
        print("📺 Watch for step-by-step progress below:")
        print()

        # Run FreeCAD with the script as input
        with open(temp_script_path, "r") as script_file:
            result = subprocess.run(cmd, stdin=script_file, env=env, text=True)

        print()
        if result.returncode == 0:
            print("✅ House modeling completed successfully!")
            print()
            print("🔍 To view the 3D model:")
            print(f"   1. Run: {freecad_path}")
            print("   2. Open the 'LiveHouseModel' document")
            print("   3. Switch to 3D view to see your house!")
        else:
            print(f"⚠️  FreeCAD exited with code: {result.returncode}")

        return result.returncode

    except Exception as e:
        print(f"❌ Failed to run FreeCAD: {e}")
        return 1

    finally:
        # Clean up temporary file
        try:
            os.unlink(temp_script_path)
        except:
            pass


if __name__ == "__main__":
    sys.exit(main())
