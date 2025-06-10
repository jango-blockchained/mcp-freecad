#!/usr/bin/env python3
"""
Fixed FreeCAD House Modeling Launcher

This script launches FreeCAD with the house modeling script using the correct command line options.
This is the most reliable method for running the live house test!
"""

import argparse
import subprocess
import sys
from pathlib import Path


def main():
    """Launch FreeCAD with the house modeling script."""
    parser = argparse.ArgumentParser(
        description="Launch FreeCAD with live house modeling script",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
This launcher provides the most reliable way to see the house being built live!

Examples:
  python run_house_macro.py                    # Run in console mode (recommended)
  python run_house_macro.py --gui              # Run with GUI mode
  python run_house_macro.py --console          # Run in console mode only
        """,
    )

    parser.add_argument(
        "--gui",
        action="store_true",
        help="Start FreeCAD with GUI (default: console mode)",
    )

    parser.add_argument(
        "--console", action="store_true", help="Force console mode only"
    )

    parser.add_argument(
        "--delay",
        type=float,
        default=2.0,
        help="Step delay in seconds (edit the script file to change this)",
    )

    args = parser.parse_args()

    # Paths
    project_root = Path(__file__).parent
    freecad_appimage = project_root / "FreeCAD_1.0.0-conda-Linux-x86_64-py311.AppImage"
    script_file = project_root / "house_modeling_script.py"

    # Check files exist
    if not freecad_appimage.exists():
        print(f"❌ FreeCAD AppImage not found: {freecad_appimage}")
        print("Please ensure the FreeCAD AppImage is in the project root directory.")
        return 1

    if not script_file.exists():
        print(f"❌ Script file not found: {script_file}")
        print("Please ensure the house_modeling_script.py file exists.")
        return 1

    print("🏠 Live House Modeling - Fixed FreeCAD Launcher")
    print("=" * 60)
    print(f"🚀 Starting FreeCAD with house modeling script...")
    print(f"📄 Script: {script_file}")
    print(f"⏱️  Step delay: {args.delay}s (edit script to change)")

    # Determine mode
    if args.console:
        mode = "console only"
        console_flag = True
    elif args.gui:
        mode = "GUI mode"
        console_flag = False
    else:
        mode = "console mode (recommended for live output)"
        console_flag = True

    print(f"🎛️  Mode: {mode}")
    print()
    print("What will happen:")
    print("1. FreeCAD will start")
    print("2. The house modeling script will run automatically")
    print("3. You'll see step-by-step progress in the terminal:")
    print("   🏗️  Foundation creation")
    print("   🧱 Wall construction")
    print("   🪟 Window and door openings")
    print("4. Model will be created in FreeCAD")

    if console_flag:
        print("5. Run 'FreeCAD' separately to view the model in GUI")
    else:
        print("5. FreeCAD GUI will show the completed model")

    print()

    if args.delay != 2.0:
        print(
            f"⚠️  Note: To change delay to {args.delay}s, edit STEP_DELAY in {script_file}"
        )
        print()

    try:
        # Build command
        cmd = [str(freecad_appimage)]

        # Add console flag if requested
        if console_flag:
            cmd.append("--console")

        # Add the script file
        cmd.append(str(script_file))

        print(f"🔧 Running command: {' '.join(cmd)}")
        print()
        print("🎬 Starting FreeCAD...")
        print("📺 Watch the terminal output for step-by-step progress!")
        print()

        # Run FreeCAD with the script
        result = subprocess.run(cmd, check=False)

        if result.returncode == 0:
            print("✅ FreeCAD exited successfully!")
            print()
            if console_flag:
                print("🔍 To view the 3D model:")
                print(f"   1. Run: {freecad_appimage}")
                print("   2. Open the 'LiveHouseModel' document")
                print("   3. Switch to 3D view to see your house!")
        else:
            print(f"⚠️  FreeCAD exited with code: {result.returncode}")
            if result.returncode == 1:
                print()
                print("💡 This might be due to Qt/Wayland issues. Try:")
                print("   1. Run with --console flag for text-only mode")
                print("   2. Set QT_QPA_PLATFORM=xcb before running")
                print("   3. Use: QT_QPA_PLATFORM=xcb python run_house_macro.py")

        return result.returncode

    except Exception as e:
        print(f"❌ Failed to start FreeCAD: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
