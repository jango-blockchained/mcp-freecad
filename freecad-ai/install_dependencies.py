#!/usr/bin/env python3

"""
FreeCAD AI - Fixed Dependency Installer

This script can be run in the FreeCAD Python console to install
missing dependencies for the FreeCAD AI addon.

Fixed version that works with FreeCAD's embedded Python interpreter
by avoiding the -m flag which is not supported.

Usage:
1. Copy this entire script
2. Paste it into the FreeCAD Python console  
3. Press Enter to run

Author: jango-blockchained
"""


def install_mcp_dependencies():
    """Install dependencies for FreeCAD AI with FreeCAD compatibility."""
    import os
    import platform
    import subprocess
    import sys

    print("🚀 FreeCAD AI - Fixed Dependency Installer")
    print("=" * 60)

    # Check Python version and compatibility
    python_version = sys.version_info
    print(
        f"📍 Python version: {python_version.major}.{python_version.minor}.{python_version.micro}"
    )
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
            except Exception:
                vendor_path = os.path.join(
                    os.path.expanduser("~"), ".freecad", "vendor"
                )
                print("⚠️ Using home directory fallback")

        print(f"📁 Target directory: {vendor_path}")

        # Ensure target directory exists
        if not os.path.exists(vendor_path):
            os.makedirs(vendor_path)

        # Enhanced dependency list with Python 3.13+ support
        dependencies = [
            {
                "name": "aiohttp",
                "version": ">=3.8.0",
                "description": "Async HTTP client/server",
                "critical": True,
            },
            {
                "name": "multidict", 
                "version": ">=6.0.0",
                "description": "Multidict implementation",
                "critical": True,
            },
            {
                "name": "yarl",
                "version": ">=1.7.0", 
                "description": "URL parsing library",
                "critical": True,
            },
            {
                "name": "aiosignal",
                "version": ">=1.2.0",
                "description": "Async signal support",
                "critical": True,
            },
            {
                "name": "requests",
                "version": ">=2.28.0",
                "description": "HTTP library",
                "critical": True,
            },
            {
                "name": "mcp",
                "version": ">=1.1.0",
                "description": "Model Context Protocol", 
                "critical": True,
            },
            {
                "name": "google-cloud-aiplatform",
                "version": "",
                "description": "Google Vertex AI support",
                "critical": False,
            },
        ]

        print(f"\n📦 Installing {len(dependencies)} packages...")
        print("=" * 40)

        success_count = 0
        failed_packages = []

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

            installation_success = False
            
            # Method 1: Try programmatic pip (most FreeCAD-compatible)
            try:
                print("   Trying programmatic pip installation...")
                
                # Import pip and use it programmatically
                import pip
                
                pip_args = [
                    "install",
                    "--disable-pip-version-check", 
                    "--target",
                    vendor_path,
                    "--upgrade",
                    package_spec
                ]
                
                # Add Python 3.13+ specific options
                if python_version >= (3, 13):
                    pip_args.extend(["--use-feature", "2020-resolver"])
                    if package_name in ["aiohttp", "multidict", "yarl", "aiosignal"]:
                        pip_args.append("--pre")
                
                # Try different pip interfaces
                if hasattr(pip, 'main'):
                    # Older pip versions
                    result = pip.main(pip_args)
                    if result == 0:
                        installation_success = True
                        print(f"   ✅ Successfully installed {package_name} (pip.main)")
                elif hasattr(pip, '_internal'):
                    # Newer pip versions  
                    from pip._internal import main as pip_main
                    result = pip_main(pip_args)
                    if result == 0:
                        installation_success = True
                        print(f"   ✅ Successfully installed {package_name} (pip._internal)")
                
            except Exception as e:
                print(f"   ⚠️ Programmatic pip failed: {e}")

            # Method 2: Try direct pip executable (if programmatic failed)
            if not installation_success:
                try:
                    print("   Trying direct pip executable...")
                    import shutil
                    
                    pip_executable = shutil.which("pip") or shutil.which("pip3")
                    if pip_executable:
                        cmd = [
                            pip_executable,
                            "install",
                            "--disable-pip-version-check",
                            "--target", 
                            vendor_path,
                            "--upgrade",
                            package_spec
                        ]
                        
                        # Add Python 3.13+ specific options
                        if python_version >= (3, 13):
                            cmd.extend(["--use-feature", "2020-resolver"])
                            if package_name in ["aiohttp", "multidict", "yarl", "aiosignal"]:
                                cmd.append("--pre")
                        
                        print(f"   Command: {' '.join(cmd)}")
                        
                        timeout = 180 if python_version >= (3, 13) else 120
                        result = subprocess.run(
                            cmd, capture_output=True, text=True, timeout=timeout
                        )
                        
                        if result.returncode == 0:
                            installation_success = True
                            print(f"   ✅ Successfully installed {package_name} (direct pip)")
                        else:
                            print(f"   ⚠️ Direct pip failed: {result.stderr}")
                    else:
                        print("   ⚠️ Direct pip executable not found")
                        
                except Exception as e:
                    print(f"   ⚠️ Direct pip approach failed: {e}")

            # Method 3: Try subprocess with python -c (avoid -m flag)
            if not installation_success:
                try:
                    print("   Trying subprocess with python -c...")
                    
                    # Build pip install command as Python code to avoid -m flag
                    pip_code = f'''
import subprocess
import sys
result = subprocess.run([
    sys.executable, "-c", 
    "import pip; pip.main(['install', '--disable-pip-version-check', '--target', '{vendor_path}', '--upgrade', '{package_spec}'])"
], capture_output=True, text=True)
sys.exit(result.returncode)
'''
                    
                    result = subprocess.run([
                        python_exe, "-c", pip_code
                    ], capture_output=True, text=True, timeout=120)
                    
                    if result.returncode == 0:
                        installation_success = True
                        print(f"   ✅ Successfully installed {package_name} (subprocess)")
                    else:
                        print(f"   ⚠️ Subprocess approach failed: {result.stderr}")
                        
                except Exception as e:
                    print(f"   ⚠️ Subprocess approach failed: {e}")

            # Check installation success
            if installation_success:
                # Verify the installation worked
                try:
                    __import__(package_name)
                    print(f"   ✅ Verified {package_name} is importable")
                    success_count += 1
                except ImportError:
                    print(f"   ⚠️ {package_name} installed but not importable")
                    success_count += 1  # Count as success since it was installed
                    
            else:
                print(f"   ❌ All installation methods failed for {package_name}")
                failed_packages.append(package_name)
                
                if is_critical:
                    print(f"   ⚠️ Critical package {package_name} failed to install")

        # Final summary
        print("\n" + "=" * 60)
        print("📊 INSTALLATION SUMMARY")
        print("=" * 60)
        print(f"✅ Successfully installed: {success_count}/{len(dependencies)} packages")
        
        if failed_packages:
            print(f"❌ Failed packages: {', '.join(failed_packages)}")
            print("\n💡 For failed packages, you can try:")
            print("   1. Manual installation using system pip")
            print("   2. Installing from FreeCAD's package manager")
            print("   3. Using conda/mamba if available")
        else:
            print("🎉 All packages installed successfully!")
            
        print(f"\n📍 Packages installed to: {vendor_path}")
        print("🔄 You may need to restart FreeCAD for changes to take effect.")
        
        return success_count == len(dependencies)

    except Exception as e:
        print(f"\n❌ Installation failed with error: {e}")
        import traceback
        print(f"💥 Full traceback:\n{traceback.format_exc()}")
        return False


# Execute the installation
if __name__ == "__main__":
    print("🚀 Starting FreeCAD AI dependency installation...")
    success = install_mcp_dependencies()
    if success:
        print("\n🎉 Installation completed successfully!")
    else:
        print("\n⚠️ Installation completed with some issues.")
else:
    # When imported/pasted into FreeCAD console
    print("🚀 FreeCAD AI Dependency Installer loaded!")
    print("💡 Run: install_mcp_dependencies()")
