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

        # Enhanced dependencies with Python 3.13+ compatibility and sub-dependencies
        dependencies = [
            {
                "name": "aiohttp",
                "version": ">=3.8.0" if python_version < (3, 13) else ">=3.9.0",
                "description": "Async HTTP client for AI provider communication",
                "critical": True,
            },
            {
                "name": "multidict",
                "version": ">=4.7.0" if python_version < (3, 13) else ">=6.0.0",
                "description": "Multi-dictionary implementation (required by aiohttp)",
                "critical": True,
            },
            {
                "name": "yarl",
                "version": ">=1.6.0" if python_version < (3, 13) else ">=1.9.0",
                "description": "URL parsing library (required by aiohttp)",
                "critical": True,
            },
            {
                "name": "aiosignal",
                "version": ">=1.1.0" if python_version < (3, 13) else ">=1.3.0",
                "description": "Signal handling for asyncio (required by aiohttp)",
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

        print(f"\n📦 Installing {len(dependencies)} dependencies with enhanced sub-dependency support...")
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

            # Build pip command with Python 3.13+ enhancements and sub-dependency support
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
                if package_name in ["aiohttp", "multidict", "yarl", "aiosignal"]:
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

                    # Verify the installation worked
                    try:
                        __import__(package_name)
                        print(f"   ✅ Verified {package_name} is importable")
                        success_count += 1
                    except ImportError:
                        print(f"   ⚠️ {package_name} installed but not importable - may need restart")
                        success_count += 1
                else:
                    print(f"   ❌ Failed to install {package_name}")
                    if result.stderr:
                        print(f"   Error: {result.stderr.strip()}")

                    # Try alternative installation for critical packages
                    if is_critical:
                        print(f"   🔄 Trying alternative installation for critical package {package_name}...")

                        # Try without version constraints but WITH dependencies
                        alt_cmd = [
                            python_exe,
                            "-m",
                            "pip",
                            "install",
                            "--disable-pip-version-check",
                            "--target",
                            vendor_path,
                            package_name
                        ]

                        alt_result = subprocess.run(
                            alt_cmd, capture_output=True, text=True, timeout=timeout
                        )

                        if alt_result.returncode == 0:
                            print(f"   ✅ Alternative installation of {package_name} succeeded")
                            try:
                                __import__(package_name)
                                print(f"   ✅ Verified {package_name} is importable")
                                success_count += 1
                            except ImportError:
                                print(f"   ⚠️ {package_name} installed but not importable - may need restart")
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

        # Enhanced results reporting with sub-dependency verification
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

        print("\n📋 Installation Summary with Sub-dependency Verification:")

        # Verify main dependencies
        main_deps_available = 0
        for dep in dependencies:
            package_name = dep["name"]
            try:
                __import__(package_name)
                print(f"   ✅ {package_name}: Available")
                main_deps_available += 1
            except ImportError:
                print(f"   ❌ {package_name}: Not available")

        # Special verification for aiohttp sub-dependencies
        if main_deps_available > 0:
            print("\n📋 Sub-dependency Verification:")

            # Check if aiohttp is available
            aiohttp_available = False
            try:
                import aiohttp
                aiohttp_available = True
                print("   ✅ aiohttp: Available")
            except ImportError:
                print("   ❌ aiohttp: Not available")

            if aiohttp_available:
                # Check aiohttp sub-dependencies
                sub_deps = ["multidict", "yarl", "aiosignal"]
                sub_deps_ok = 0

                for sub_dep in sub_deps:
                    try:
                        __import__(sub_dep)
                        print(f"   ✅ {sub_dep}: Available")
                        sub_deps_ok += 1
                    except ImportError:
                        print(f"   ❌ {sub_dep}: Missing (aiohttp sub-dependency)")

                if sub_deps_ok == len(sub_deps):
                    print("   🎉 All aiohttp sub-dependencies verified!")
                else:
                    print(f"   ⚠️ {sub_deps_ok}/{len(sub_deps)} aiohttp sub-dependencies available")
                    print("   💡 Missing sub-dependencies may cause AI provider failures")
                    print("   🔧 Try reinstalling aiohttp without --no-deps flag")
            else:
                print("   ⚠️ Cannot verify aiohttp sub-dependencies (aiohttp not available)")

        # Python 3.13+ specific guidance
        if python_version >= (3, 13) and (critical_failed or success_count < len(dependencies)):
            print("\n🐍 Python 3.13+ Troubleshooting:")
            print("   - Some packages may need newer versions for Python 3.13 compatibility")
            print("   - Sub-dependencies are critical for proper functionality")
            print("   - Avoid using --no-deps flag which skips sub-dependencies")
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
