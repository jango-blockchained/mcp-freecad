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
    target_name = "MCPIndicator" # Changed from MCPIndicator

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

    # --- Check and Remove Existing Target --- BEFORE asking mode
    if os.path.lexists(target_dir):
        print_warning(f"Target path exists: {target_dir}")
        if os.path.islink(target_dir):
            print_warning("It is a symbolic link and will be removed.")
            try:
                os.unlink(target_dir)
                print_info("Existing symbolic link removed.")
            except OSError as e:
                print_error(f"Failed to remove existing link: {e}")
                return 1 # Stop if we can't remove it
        elif os.path.isdir(target_dir):
            print_warning("It is a directory and will be removed.")
            try:
                shutil.rmtree(target_dir)
                print_info("Existing directory removed.")
            except OSError as e:
                print_error(f"Failed to remove existing directory: {e}")
                return 1 # Stop if we can't remove it
        else:
             print_warning(f"It is not a directory or link and will be removed: {target_dir}")
             try:
                 os.remove(target_dir)
                 print_info("Existing file removed.")
             except OSError as e:
                 print_error(f"Failed to remove existing file: {e}")
                 return 1 # Stop if we can't remove it
    # -----------------------------------------

    # --- Installation Mode Selection --- NOW after potential removal
    install_mode = ""
    while install_mode not in ["copy", "symlink"]:
        print("\nChoose installation mode:")
        print("  a) Full Copy (Installs a copy of the addon files)")
        print("  b) Symbolic Link (Links to source directory - for development)")
        choice = input("Enter choice (a/b): ").lower()
        if choice in ['a', 'copy']:
            install_mode = "copy"
            print_info("Selected: Full Copy")
        elif choice in ['b', 'symlink']:
            install_mode = "symlink"
            print_info("Selected: Symbolic Link (Development Mode)")
            if platform.system() == "Windows":
                print_warning("Creating symlinks on Windows may require administrator privileges.")
        else:
            print_error("Invalid choice. Please enter 'a' or 'b'.")
    # ---------------------------------

    # Target directory path is already defined above
    # mod_dir = get_freecad_mod_dir()
    # target_dir = os.path.join(mod_dir, target_name)

    # Check if target path already exists (as file, dir, or link)
    # REMOVED Check block from here, moved above mode selection
    # if os.path.lexists(target_dir):
        # ... (removal logic moved)

    # Ensure parent Mod directory exists (might be needed if we just removed target)
    os.makedirs(mod_dir, exist_ok=True)

    # --- Perform Installation Based on Mode ---
    try:
        if install_mode == "copy":
            print_info(f"Performing full copy from {src_dir} to {target_dir}...")
            shutil.copytree(
                src_dir,
                target_dir,
                ignore=shutil.ignore_patterns('scripts', '.git*', '.github', '__pycache__', '*.pyc'),
                # dirs_exist_ok=True # Not needed as we remove the target first
            )
        elif install_mode == "symlink":
            print_info(f"Creating symbolic link from {target_dir} pointing to {src_dir}...")
            os.symlink(src_dir, target_dir, target_is_directory=True) # target_is_directory=True is safer

    except OSError as e:
        print_error(f"Failed to perform installation: {e}")
        if install_mode == "symlink" and platform.system() == "Windows":
            print_error("On Windows, this might be due to insufficient privileges to create symlinks.")
            print_error("Try running this script as an Administrator.")
        return 1
    except Exception as e:
        print_error(f"An unexpected error occurred during installation: {e}")
        return 1
    # -----------------------------------------

    # Check if the installation was successful
    pkg_xml_path = os.path.join(target_dir, "package.xml")
    init_gui_path = os.path.join(target_dir, "MCPIndicator", "InitGui.py")
    if os.path.isfile(pkg_xml_path) and os.path.isfile(init_gui_path):
        print_success("Installation completed successfully!")
        if install_mode == "symlink":
            try:
                link_target = os.path.realpath(target_dir)
                print_success(f"Addon linked at: {target_dir} -> {link_target}")
            except Exception:
                 print_success(f"Addon linked at: {target_dir}") # Fallback if realpath fails
        else:
            print_success(f"Addon copied to: {target_dir}")
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
