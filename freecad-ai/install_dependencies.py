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
    """Install dependencies for FreeCAD FreeCAD AI with enhanced Python 3.13+ support."""
    import os
    import subprocess
    import sys
    import platform

    print("🚀 FreeCAD FreeCAD AI - Enhanced Dependency Installer")
    print("=" * 60)

    # Check Python version and compatibility
    python_version = sys.version_info
    print(f"📍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}")
    print(f"📍 Platform: {platform.system()} {platform.machine()}")

    # Python 3.13+ compatibility warnings
    if python_version >= (3, 13):
        print("⚠️  Python 3.13+ detected - using enhanced compatibility mode")
        print("⚠️  Some packages may require newer versions for compatibility")

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

        # Enhanced dependencies with Python 3.13+ compatibility
        dependencies = [
            {
                "name": "aiohttp",
                "version": ">=3.8.0" if python_version < (3, 13) else ">=3.9.0",
                "description": "Async HTTP client for AI provider communication",
                "critical": True,
            },
            {
                "name": "requests",
                "version": ">=2.28.0" if python_version < (3, 13) else ">=2.31.0",
                "description": "HTTP library for API requests",
                "critical": True,
            },
            {
                "name": "mcp",
                "version": ">=1.0.0",
                "description": "Model Context Protocol library for Claude Desktop integration",
                "critical": False,
            },
        ]

        print(f"\n📦 Installing {len(dependencies)} dependencies with enhanced compatibility...")
        print("-" * 70)

        success_count = 0
        critical_failed = []

        for dep in dependencies:
            package_name = dep["name"]
            version_spec = dep["version"]
            description = dep["description"]
            is_critical = dep["critical"]

            package_spec = f"{package_name}{version_spec}"

            print(f"\n🔄 Installing {package_name}...")
            print(f"   Description: {description}")
            print(f"   Version: {version_spec}")
            print(f"   Critical: {'Yes' if is_critical else 'No'}")

            # Build pip command with Python 3.13+ enhancements
            cmd = [
                python_exe,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--target",
                vendor_path,
                "--upgrade",
            ]

            # Add Python 3.13+ specific options
            if python_version >= (3, 13):
                cmd.extend(["--use-feature", "2020-resolver"])
                if package_name == "aiohttp":
                    cmd.append("--pre")

            cmd.append(package_spec)

            print(f"   Command: {' '.join(cmd)}")

            try:
                # Run pip installation with extended timeout for Python 3.13+
                timeout = 180 if python_version >= (3, 13) else 120
                result = subprocess.run(
                    cmd, capture_output=True, text=True, timeout=timeout
                )

                if result.returncode == 0:
                    print(f"   ✅ Successfully installed {package_name}")
                    success_count += 1
                else:
                    print(f"   ❌ Failed to install {package_name}")
                    if result.stderr:
                        print(f"   Error: {result.stderr.strip()}")

                    # Try alternative installation for critical packages
                    if is_critical:
                        print(f"   🔄 Trying alternative installation for critical package {package_name}...")

                        alt_cmd = [
                            python_exe,
                            "-m",
                            "pip",
                            "install",
                            "--disable-pip-version-check",
                            "--target",
                            vendor_path,
                            "--no-deps",
                            package_name
                        ]

                        alt_result = subprocess.run(
                            alt_cmd, capture_output=True, text=True, timeout=timeout
                        )

                        if alt_result.returncode == 0:
                            print(f"   ✅ Alternative installation of {package_name} succeeded")
                            success_count += 1
                        else:
                            print(f"   ❌ Alternative installation also failed")
                            critical_failed.append(package_name)
                    else:
                        print(f"   ⚠️ Optional package {package_name} failed - continuing")

            except subprocess.TimeoutExpired:
                print(f"   ❌ Installation of {package_name} timed out")
                if is_critical:
                    critical_failed.append(package_name)
            except Exception as e:
                print(f"   ❌ Error installing {package_name}: {str(e)}")
                if is_critical:
                    critical_failed.append(package_name)

        print("\n" + "=" * 60)

        # Enhanced results reporting
        if success_count == len(dependencies):
            print("🎉 All dependencies installed successfully!")
            print("🔄 Please restart FreeCAD to use the new dependencies.")
        elif critical_failed:
            print(f"❌ Critical dependencies failed to install: {', '.join(critical_failed)}")
            print("💡 The addon may not function properly without these dependencies")
            print("🔄 Please restart FreeCAD and try again, or install manually")
        elif success_count > 0:
            print(f"⚠️ Installed {success_count}/{len(dependencies)} dependencies")
            print("✅ All critical dependencies installed successfully")
            print("🔄 Please restart FreeCAD to use the installed dependencies.")
        else:
            print("❌ No dependencies were installed successfully")
            print("💡 Try installing manually using your system package manager")

        print("\n📋 Installation Summary:")
        for dep in dependencies:
            package_name = dep["name"]
            try:
                __import__(package_name)
                print(f"   ✅ {package_name}: Available")
            except ImportError:
                print(f"   ❌ {package_name}: Not available")

        # Python 3.13+ specific guidance
        if python_version >= (3, 13) and (critical_failed or success_count < len(dependencies)):
            print("\n🐍 Python 3.13+ Troubleshooting:")
            print("   - Some packages may need newer versions for Python 3.13 compatibility")
            print("   - Consider using a virtual environment with compatible package versions")
            print("   - Check package documentation for Python 3.13 support status")

    except Exception as e:
        print(f"❌ Unexpected error: {str(e)}")
        print("💡 Please report this error to the addon developers")
        import traceback
        print(f"📋 Traceback: {traceback.format_exc()}")

# Run the installer
if __name__ == "__main__":
    install_mcp_dependencies()
else:
    # When imported/pasted into console
    install_mcp_dependencies()
