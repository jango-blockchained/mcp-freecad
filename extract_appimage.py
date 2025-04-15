#!/usr/bin/env python3
"""
Extract FreeCAD AppImage

This script extracts a FreeCAD AppImage and updates the configuration to use it.
"""

import os
import subprocess
import json
import argparse
import sys
import shutil

def log(message):
    """Log a message"""
    print(f"[AppImage Extractor] {message}")

def extract_appimage(appimage_path, output_dir=None):
    """Extract an AppImage to a directory"""
    if not os.path.exists(appimage_path):
        log(f"Error: AppImage not found at {appimage_path}")
        return False

    # Default output directory is in the same directory as the AppImage
    if output_dir is None:
        output_dir = os.path.join(os.path.dirname(os.path.abspath(appimage_path)), "squashfs-root")

    # Check if already extracted
    if os.path.exists(output_dir):
        log(f"Note: Output directory already exists: {output_dir}")
        log("Using existing extraction. If you want to re-extract, delete this directory first.")
        return output_dir

    # Extract the AppImage
    log(f"Extracting AppImage: {appimage_path}")
    log(f"Output directory: {output_dir}")

    try:
        # First, make sure the AppImage is executable
        os.chmod(appimage_path, 0o755)

        # Extract the AppImage with --appimage-extract
        cmd = [appimage_path, "--appimage-extract"]
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            log(f"Error extracting AppImage: {result.stderr}")
            return False

        # Sometimes extraction goes to squashfs-root in current directory
        default_extract_dir = os.path.join(os.getcwd(), "squashfs-root")
        if os.path.exists(default_extract_dir) and output_dir != default_extract_dir:
            # Move to the specified output directory
            if os.path.exists(output_dir):
                shutil.rmtree(output_dir)
            shutil.move(default_extract_dir, output_dir)

        log("AppImage extracted successfully")
        return output_dir

    except Exception as e:
        log(f"Error extracting AppImage: {e}")
        return False

def update_config(squashfs_path):
    """Update the config.json to use the extracted AppImage"""
    config_path = "config.json"

    if not os.path.exists(config_path):
        log(f"Error: Config file not found at {config_path}")
        return False

    try:
        # Load the config
        with open(config_path, "r") as f:
            config = json.load(f)

        # Update the FreeCAD configuration
        if "freecad" not in config:
            config["freecad"] = {}

        config["freecad"]["use_apprun"] = True
        config["freecad"]["apprun_path"] = squashfs_path
        config["freecad"]["connection_method"] = "launcher"
        config["freecad"]["use_mock"] = False

        # Save the updated config
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

        log("Config updated successfully")
        return True

    except Exception as e:
        log(f"Error updating config: {e}")
        return False

def test_extracted_freecad(squashfs_path):
    """Test the extracted FreeCAD by running the AppRun script"""
    apprun_path = os.path.join(squashfs_path, "AppRun")

    if not os.path.exists(apprun_path):
        log(f"Error: AppRun not found at {apprun_path}")
        return False

    try:
        # Test running FreeCAD with --version
        cmd = [apprun_path, "--version"]
        log(f"Testing extracted FreeCAD: {' '.join(cmd)}")
        result = subprocess.run(cmd, capture_output=True, text=True)

        if result.returncode != 0:
            log(f"Error testing FreeCAD: {result.stderr}")
            return False

        # Print version info
        log(f"FreeCAD version info: {result.stdout.strip()}")

        # Now test with our launcher
        if os.path.exists("freecad_connection_launcher.py"):
            log("Testing with freecad_connection_launcher.py")
            launcher_cmd = ["python3", "freecad_connection_launcher.py", "--apprun", "--path", squashfs_path]
            launcher_result = subprocess.run(launcher_cmd, capture_output=True, text=True)

            if launcher_result.returncode != 0:
                log(f"Error testing launcher: {launcher_result.stderr}")
                log(launcher_result.stdout)  # Still print stdout for debugging
                return False

            log("Launcher test results:")
            log(launcher_result.stdout)

        return True

    except Exception as e:
        log(f"Error testing FreeCAD: {e}")
        return False

def main():
    """Main function"""
    parser = argparse.ArgumentParser(description="Extract FreeCAD AppImage")
    parser.add_argument("appimage", help="Path to the FreeCAD AppImage")
    parser.add_argument("--output", help="Output directory for extraction")
    parser.add_argument("--skip-test", action="store_true", help="Skip testing the extracted AppImage")
    parser.add_argument("--no-config-update", action="store_true", help="Don't update the config.json")

    args = parser.parse_args()

    # Extract the AppImage
    output_dir = extract_appimage(args.appimage, args.output)

    if not output_dir:
        log("Failed to extract AppImage")
        return 1

    log(f"AppImage extracted to: {output_dir}")

    # Update the config
    if not args.no_config_update:
        if update_config(output_dir):
            log("Configuration updated to use the extracted AppImage")
        else:
            log("Failed to update configuration")

    # Test the extracted FreeCAD
    if not args.skip_test:
        if test_extracted_freecad(output_dir):
            log("FreeCAD test successful")
        else:
            log("FreeCAD test failed, but extraction was completed")

    log("Done.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
