#!/usr/bin/env python3
"""
FreeCAD MCP Indicator Installation Script
Copies the 'freecad_addon' directory to the FreeCAD Mod directory
"""

import os
import sys
import shutil
import platform

# ANSI color codes for terminal output
class Colors:
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    END = '\033[0m'

def print_info(message):
    print(f"{Colors.BLUE}{Colors.BOLD}[INFO]{Colors.END} {message}")

def print_success(message):
    print(f"{Colors.GREEN}{Colors.BOLD}[SUCCESS]{Colors.END} {message}")

def print_warning(message):
    print(f"{Colors.YELLOW}{Colors.BOLD}[WARNING]{Colors.END} {message}")

def print_error(message):
    print(f"{Colors.RED}{Colors.BOLD}[ERROR]{Colors.END} {message}")

def get_freecad_mod_dir():
    """Find or create the FreeCAD Mod directory based on platform"""
    home_dir = os.path.expanduser("~")
    system = platform.system()

    # Define possible Mod directories based on platform
    if system == "Windows":
        possible_dirs = [
            os.path.join(os.getenv('APPDATA', ''), "FreeCAD", "Mod"),
            os.path.join(home_dir, "AppData", "Roaming", "FreeCAD", "Mod")
        ]
    elif system == "Darwin":  # macOS
        possible_dirs = [
            os.path.join(home_dir, "Library", "Preferences", "FreeCAD", "Mod"),
            os.path.join(home_dir, ".FreeCAD", "Mod")
        ]
    else:  # Linux and others
        possible_dirs = [
            # Modern Linux convention first
            os.path.join(home_dir, ".local", "share", "FreeCAD", "Mod"),
            os.path.join(home_dir, ".FreeCAD", "Mod"),
            os.path.join(home_dir, ".freecad", "Mod"),
            "/usr/share/freecad/Mod",
            "/usr/local/share/freecad/Mod"
        ]

    # Check if any of the directories exist
    for mod_dir in possible_dirs:
        if os.path.isdir(mod_dir):
            print_info(f"Found existing FreeCAD Mod directory: {mod_dir}")
            return mod_dir

    # If no directory found, determine and create the default one
    if system == "Windows":
        default_dir = os.path.join(os.getenv('APPDATA', ''), "FreeCAD", "Mod")
    elif system == "Darwin":
        default_dir = os.path.join(home_dir, "Library", "Preferences", "FreeCAD", "Mod")
    else: # Linux default
        default_dir = os.path.join(home_dir, ".local", "share", "FreeCAD", "Mod")

    print_warning("No existing FreeCAD Mod directory found.")
    print_info(f"Creating default directory: {default_dir}")
    os.makedirs(default_dir, exist_ok=True)
    return default_dir

def confirm(prompt):
    """Ask for confirmation"""
    valid = {"yes": True, "y": True, "no": False, "n": False}

    while True:
        sys.stdout.write(f"{prompt} [y/n] ")
        choice = input().lower()
        if choice in valid:
            return valid[choice]
        print("Please respond with 'y' or 'n'")

def main():
    # Use the actual addon directory name
    target_name = "freecad_addon" # Changed from MCPIndicator

    print_info(f"FreeCAD Addon Installation ({target_name})")
    print_info("==========================================")

    # Determine the script directory and source directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    # Source directory is the parent directory of 'scripts'
    src_dir = os.path.dirname(script_dir)

    # Verify that the source directory looks reasonable
    if not os.path.isdir(os.path.join(src_dir, "MCPIndicator")) or \
       not os.path.isfile(os.path.join(src_dir, "package.xml")):
        print_error(f"Source directory structure seems incorrect at: {src_dir}")
        print_error("Expected to find 'MCPIndicator' subdirectory and 'package.xml'.")
        return 1

    print_info(f"Source directory: {src_dir}")

    # Get the FreeCAD Mod directory
    mod_dir = get_freecad_mod_dir()
    # Target directory is Mod directory + target name
    target_dir = os.path.join(mod_dir, target_name)

    # Check if target directory already exists
    if os.path.isdir(target_dir):
        print_warning(f"Target directory already exists: {target_dir}")
        print_warning("This will overwrite the existing installation.")

        if not confirm("Continue with installation?"):
            print_info("Installation cancelled.")
            return

        print_info("Removing existing installation...")
        shutil.rmtree(target_dir)

    # Copy the entire source directory (excluding scripts and .git)
    print_info(f"Copying addon files from {src_dir} to {target_dir}...")
    shutil.copytree(
        src_dir,
        target_dir,
        ignore=shutil.ignore_patterns('scripts', '.git*', '.github', '__pycache__', '*.pyc'),
        dirs_exist_ok=True # Overwrite behavior handled above by removing target_dir
    )

    # Check if the installation was successful
    pkg_xml_path = os.path.join(target_dir, "package.xml")
    init_gui_path = os.path.join(target_dir, "MCPIndicator", "InitGui.py")
    if os.path.isfile(pkg_xml_path) and os.path.isfile(init_gui_path):
        print_success("Installation completed successfully!")
        print_success(f"Addon installed at: {target_dir}")
        print_info("Please restart FreeCAD to use the MCP Indicator Workbench.")
    else:
        print_error("Installation failed. Check if files were copied correctly.")
        print_error(f"Expected package.xml at: {pkg_xml_path}")
        print_error(f"Expected InitGui.py at: {init_gui_path}")
        return 1

    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print_warning("\nInstallation interrupted by user.")
        sys.exit(1)
    except Exception as e:
        print_error(f"An unexpected error occurred: {e}")
        sys.exit(1)
