#!/usr/bin/env python3
"""
FreeCAD MCP Indicator Installation Script
Copies the MCP Indicator Workbench to the FreeCAD Mod directory
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

    # If no directory found, create the default one
    default_dir = os.path.join(home_dir, ".FreeCAD", "Mod")
    if system == "Windows":
        default_dir = os.path.join(os.getenv('APPDATA', ''), "FreeCAD", "Mod")
    elif system == "Darwin":
        default_dir = os.path.join(home_dir, "Library", "Preferences", "FreeCAD", "Mod")

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
    print_info("FreeCAD MCP Indicator Installation")
    print_info("==================================")

    # Determine the script directory and source directory
    script_dir = os.path.dirname(os.path.abspath(__file__))
    src_dir = os.path.dirname(script_dir)
    target_name = "freecad_mcp_indicator"

    print_info(f"Source directory: {src_dir}")

    # Get the FreeCAD Mod directory
    mod_dir = get_freecad_mod_dir()
    target_dir = os.path.join(mod_dir, target_name)

    # Check if target directory already exists
    if os.path.isdir(target_dir):
        print_warning(f"Target directory already exists: {target_dir}")
        print_warning("This will overwrite the existing installation.")

        # Ask for confirmation
        if not confirm("Continue with installation?"):
            print_info("Installation cancelled.")
            return

        # Remove existing directory
        print_info("Removing existing installation...")
        shutil.rmtree(target_dir)

    # Create the target directory
    os.makedirs(target_dir, exist_ok=True)

    # Copy all files from the source to the target directory
    print_info(f"Copying files to {target_dir}...")
    for item in os.listdir(src_dir):
        src_item = os.path.join(src_dir, item)
        dst_item = os.path.join(target_dir, item)

        if os.path.isdir(src_item):
            shutil.copytree(src_item, dst_item, dirs_exist_ok=True)
        else:
            shutil.copy2(src_item, dst_item)

    # Make the script executable (for Unix-based systems)
    install_script = os.path.join(target_dir, "scripts", "install.sh")
    if os.path.isfile(install_script) and platform.system() != "Windows":
        try:
            os.chmod(install_script, 0o755)  # rwxr-xr-x
        except Exception as e:
            print_warning(f"Could not make install.sh executable: {e}")

    # Check if the installation was successful
    if os.path.isdir(os.path.join(target_dir, "mcp_indicator")) and os.path.isfile(os.path.join(target_dir, "package.xml")):
        print_success("Installation completed successfully!")
        print_info("Please restart FreeCAD to use the MCP Indicator Workbench.")
    else:
        print_error("Installation failed. Some files may not have been copied correctly.")
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
