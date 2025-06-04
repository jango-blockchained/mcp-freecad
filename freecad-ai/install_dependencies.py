#!/usr/bin/env python3
"""
FreeCAD FreeCAD AI - Dependency Installer

This script can be run in the FreeCAD Python console to install
missing dependencies for the FreeCAD AI addon.

Usage:
1. Copy this entire script
2. Paste it into the FreeCAD Python console
3. Press Enter to run

Author: jango-blockchained
"""


def install_mcp_dependencies():
    """Install dependencies for FreeCAD FreeCAD AI."""
    import subprocess
    import os
    import sys

    print("🚀 FreeCAD FreeCAD AI - Dependency Installer")
    print("=" * 50)

    try:
        # Try to get the correct Python executable and target directory
        python_exe = None
        vendor_path = None

        # Method 1: FreeCAD 0.22+
        try:
            from freecad.utils import get_python_exe

            python_exe = get_python_exe()
            print("✅ Found Python executable using freecad.utils")
        except ImportError:
            pass

        # Method 2: FreeCAD 0.21 addon manager utilities
        if not python_exe:
            try:
                import addonmanager_utilities as utils

                if hasattr(utils, "get_python_exe"):
                    python_exe = utils.get_python_exe()
                    print("✅ Found Python executable using addonmanager_utilities")
            except ImportError:
                pass

        # Method 3: Fallback to sys.executable
        if not python_exe:
            python_exe = sys.executable
            print("⚠️ Using fallback Python executable")

        print(f"📍 Python executable: {python_exe}")

        # Get target directory
        try:
            import addonmanager_utilities as utils

            if hasattr(utils, "get_pip_target_directory"):
                vendor_path = utils.get_pip_target_directory()
                print("✅ Found target directory using addonmanager_utilities")
        except ImportError:
            pass

        # Fallback target directory
        if not vendor_path:
            try:
                import FreeCAD

                user_dir = FreeCAD.getUserAppDataDir()
                vendor_path = os.path.join(user_dir, "Mod", "vendor")
                print("⚠️ Using fallback target directory")
            except:
                vendor_path = os.path.join(
                    os.path.expanduser("~"), ".freecad", "vendor"
                )
                print("⚠️ Using home directory fallback")

        print(f"📁 Target directory: {vendor_path}")

        # Ensure target directory exists
        if not os.path.exists(vendor_path):
            os.makedirs(vendor_path)
            print(f"📂 Created target directory: {vendor_path}")

        # Dependencies to install
        dependencies = [
            ("aiohttp", ">=3.8.0", "Async HTTP client for AI provider communication"),
            ("requests", ">=2.28.0", "HTTP library for API requests"),
        ]

        print(f"\n📦 Installing {len(dependencies)} dependencies...")
        print("-" * 40)

        success_count = 0

        for package_name, version_spec, description in dependencies:
            package_spec = f"{package_name}{version_spec}"

            print(f"\n🔄 Installing {package_name}...")
            print(f"   Description: {description}")

            # Build pip command
            cmd = [
                python_exe,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--target",
                vendor_path,
                package_spec,
            ]

            print(f"   Command: {' '.join(cmd)}")

            try:
                # Run pip installation
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=120
                )

                if result.returncode == 0:
                    print(f"   ✅ Successfully installed {package_name}")
                    success_count += 1
                else:
                    print(f"   ❌ Failed to install {package_name}")
                    if result.stderr:
                        print(f"   Error: {result.stderr.strip()}")

            except subprocess.TimeoutExpired:
                print(f"   ❌ Installation of {package_name} timed out")
            except Exception as e:
                print(f"   ❌ Error installing {package_name}: {str(e)}")

        print("\n" + "=" * 50)

        if success_count == len(dependencies):
            print("🎉 All dependencies installed successfully!")
            print("🔄 Please restart FreeCAD to use the new dependencies.")
        elif success_count > 0:
            print(f"⚠️ Installed {success_count}/{len(dependencies)} dependencies")
            print("🔄 Please restart FreeCAD to use the installed dependencies.")
        else:
            print("❌ No dependencies were installed successfully")
            print("💡 Try installing manually using your system package manager")

        print("\n📋 Installation Summary:")
        for package_name, _, _ in dependencies:
            try:
                __import__(package_name)
                print(f"   ✅ {package_name}: Available")
            except ImportError:
                print(f"   ❌ {package_name}: Not available")

    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        print("💡 Please report this error to the addon developers")


# Run the installer
if __name__ == "__main__":
    install_mcp_dependencies()
else:
    # When imported/pasted into console
    install_mcp_dependencies()
