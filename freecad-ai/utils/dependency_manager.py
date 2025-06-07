"""
Dependency Manager for FreeCAD FreeCAD AI

Handles installation and management of Python dependencies within FreeCAD,
supporting different FreeCAD versions and installation types.

Based on FreeCAD documentation and community best practices.
"""

import importlib.util
import os
import subprocess
import sys
import platform
import traceback
from typing import Callable, Dict, List, Optional, Tuple

import FreeCAD


def check_python_compatibility():
    """Check Python version compatibility and return compatibility info."""
    python_version = sys.version_info

    compatibility_info = {
        "version": f"{python_version.major}.{python_version.minor}.{python_version.micro}",
        "major_minor": f"{python_version.major}.{python_version.minor}",
        "is_313_plus": python_version >= (3, 13),
        "is_312_plus": python_version >= (3, 12),
        "is_311_plus": python_version >= (3, 11),
        "platform": platform.system(),
        "architecture": platform.machine(),
    }

    # Known compatibility issues
    compatibility_info["known_issues"] = []

    if python_version >= (3, 13):
        compatibility_info["known_issues"].append(
            "Python 3.13+ may have compatibility issues with older FastAPI/Pydantic versions"
        )
        compatibility_info["known_issues"].append(
            "Some packages may require newer versions for Python 3.13 compatibility"
        )

    return compatibility_info


class DependencyManager:
    """Manages Python dependencies for the FreeCAD AI addon."""

    # Required dependencies for the addon with Python 3.13+ compatibility
    REQUIRED_DEPENDENCIES = {
        "aiohttp": {
            "version": ">=3.8.0",
            "version_313": ">=3.9.0",  # Newer version for Python 3.13+
            "description": "Async HTTP client for AI provider communication",
            "import_name": "aiohttp",
            "critical": True,  # Critical for AI providers
        },
        "multidict": {
            "version": ">=4.7.0",
            "version_313": ">=6.0.0",  # Newer version for Python 3.13+
            "description": "Multi-dictionary implementation (required by aiohttp)",
            "import_name": "multidict",
            "critical": True,  # Critical sub-dependency for aiohttp
        },
        "yarl": {
            "version": ">=1.6.0",
            "version_313": ">=1.9.0",  # Newer version for Python 3.13+
            "description": "URL parsing library (required by aiohttp)",
            "import_name": "yarl",
            "critical": True,  # Critical sub-dependency for aiohttp
        },
        "aiosignal": {
            "version": ">=1.1.0",
            "version_313": ">=1.3.0",  # Newer version for Python 3.13+
            "description": "Signal handling for asyncio (required by aiohttp)",
            "import_name": "aiosignal",
            "critical": True,  # Critical sub-dependency for aiohttp
        },
        "requests": {
            "version": ">=2.28.0",
            "version_313": ">=2.31.0",  # Newer version for Python 3.13+
            "description": "HTTP library for API requests",
            "import_name": "requests",
            "critical": True,  # Critical for basic functionality
        },
        "mcp": {
            "version": ">=1.0.0",
            "version_313": ">=1.0.0",  # Same version for now
            "description": "Model Context Protocol library for Claude Desktop integration",
            "import_name": "mcp",
            "critical": False,  # Optional for enhanced functionality
        },
    }

    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """Initialize the dependency manager.

        Args:
            progress_callback: Optional callback for progress updates
        """
        self.progress_callback = progress_callback or self._default_progress
        self.freecad_version = self._detect_freecad_version()
        self.installation_type = self._detect_installation_type()
        self.python_compatibility = check_python_compatibility()

        # Log compatibility info
        self.progress_callback(f"Python version: {self.python_compatibility['version']}")
        self.progress_callback(f"Platform: {self.python_compatibility['platform']}")

        if self.python_compatibility["known_issues"]:
            for issue in self.python_compatibility["known_issues"]:
                self.progress_callback(f"Compatibility note: {issue}")

    def _default_progress(self, message: str):
        """Default progress callback that prints to FreeCAD console."""
        FreeCAD.Console.PrintMessage(f"Dependency Manager: {message}\n")

    def _detect_freecad_version(self) -> Tuple[int, int]:
        """Detect FreeCAD version."""
        try:
            version_info = FreeCAD.Version()
            major = int(version_info[0])
            minor = int(version_info[1])
            return (major, minor)
        except:
            return (0, 21)  # Default to 0.21 if detection fails

    def _detect_installation_type(self) -> str:
        """Detect FreeCAD installation type."""
        try:
            # Check if running from AppImage
            if os.environ.get("APPIMAGE"):
                return "appimage"

            # Check if running from Snap
            if os.environ.get("SNAP"):
                return "snap"

            # Check if Windows portable
            if sys.platform == "win32" and "FreeCAD" in sys.executable:
                return "windows_portable"

            return "standard"
        except:
            return "standard"

    def _get_python_exe(self) -> str:
        """Get the Python executable path for the current FreeCAD installation."""
        try:
            # Try FreeCAD 0.22+ method first
            if self.freecad_version >= (0, 22):
                try:
                    from freecad.utils import get_python_exe

                    return get_python_exe()
                except ImportError:
                    pass

            # Try addon manager utilities (works for 0.21+)
            try:
                import addonmanager_utilities as utils

                if hasattr(utils, "get_python_exe"):
                    return utils.get_python_exe()
            except ImportError:
                pass

            # Fallback methods
            if self.installation_type == "windows_portable":
                # For Windows portable, Python is usually in the bin directory
                freecad_dir = os.path.dirname(sys.executable)
                python_exe = os.path.join(freecad_dir, "python.exe")
                if os.path.exists(python_exe):
                    return python_exe

            # Last resort - use sys.executable
            return sys.executable

        except Exception as e:
            self.progress_callback(f"Warning: Could not detect Python executable: {e}")
            return sys.executable

    def _get_pip_target_directory(self) -> str:
        """Get the target directory for pip installations."""
        try:
            # Try addon manager utilities first
            import addonmanager_utilities as utils

            if hasattr(utils, "get_pip_target_directory"):
                return utils.get_pip_target_directory()
        except ImportError:
            pass

        # Fallback: use FreeCAD user directory
        try:
            user_dir = FreeCAD.getUserAppDataDir()
            vendor_path = os.path.join(user_dir, "Mod", "vendor")
            return vendor_path
        except:
            # Last resort
            return os.path.join(os.path.expanduser("~"), ".freecad", "vendor")

    def _get_package_version_spec(self, package_name: str) -> str:
        """Get the appropriate version specification for a package based on Python version."""
        if package_name not in self.REQUIRED_DEPENDENCIES:
            return ""

        package_info = self.REQUIRED_DEPENDENCIES[package_name]

        # Use Python 3.13+ specific version if available and applicable
        if self.python_compatibility["is_313_plus"] and "version_313" in package_info:
            return package_info["version_313"]
        else:
            return package_info["version"]

    def check_dependency(self, package_name: str) -> bool:
        """Check if a dependency is installed and importable.

        Args:
            package_name: Name of the package to check

        Returns:
            True if the package is available, False otherwise
        """
        try:
            import_name = self.REQUIRED_DEPENDENCIES.get(package_name, {}).get(
                "import_name", package_name
            )
            spec = importlib.util.find_spec(import_name)
            if spec is not None:
                # Try to actually import it to make sure it works
                try:
                    __import__(import_name)
                    return True
                except Exception as e:
                    self.progress_callback(f"Package {package_name} found but import failed: {e}")
                    return False
            return False

        except ImportError:
            return False
        except Exception as e:
            self.progress_callback(f"Error checking dependency {package_name}: {e}")
            return False

    def check_sub_dependencies(self, package_name: str) -> Dict[str, bool]:
        """Check sub-dependencies for a specific package.

        Args:
            package_name: Name of the main package to check sub-dependencies for

        Returns:
            Dictionary mapping sub-dependency names to availability status
        """
        sub_deps = {}

        if package_name == "aiohttp":
            # Check critical aiohttp sub-dependencies
            for sub_dep in ["multidict", "yarl", "aiosignal"]:
                sub_deps[sub_dep] = self.check_dependency(sub_dep)

        return sub_deps

    def check_all_dependencies(self) -> Dict[str, bool]:
        """Check all required dependencies.

        Returns:
            Dictionary mapping package names to availability status
        """
        results = {}
        for package_name in self.REQUIRED_DEPENDENCIES:
            results[package_name] = self.check_dependency(package_name)
        return results
    

    def get_missing_dependencies(self) -> List[str]:
        """Get list of missing dependencies.

        Returns:
            List of missing package names
        """
        missing = []
        for package_name, available in self.check_all_dependencies().items():
            if not available:
                missing.append(package_name)
        return missing

    def get_critical_missing_dependencies(self) -> List[str]:
        """Get list of missing critical dependencies.

        Returns:
            List of missing critical package names
        """
        missing = []
        for package_name, available in self.check_all_dependencies().items():
            if not available and self.REQUIRED_DEPENDENCIES[package_name].get("critical", False):
                missing.append(package_name)
        return missing

    def install_dependency(self, package_name: str, timeout: int = 180) -> bool:
        """Install a single dependency with enhanced error handling and Python 3.13+ support.

        Args:
            package_name: Name of the package to install
            timeout: Timeout in seconds for the installation

        Returns:
            True if installation succeeded, False otherwise
        """
        if package_name not in self.REQUIRED_DEPENDENCIES:
            self.progress_callback(f"Unknown dependency: {package_name}")
            return False

        package_info = self.REQUIRED_DEPENDENCIES[package_name]
        version_spec = self._get_package_version_spec(package_name)
        package_spec = f"{package_name}{version_spec}"

        self.progress_callback(f"Installing {package_name} (version: {version_spec})...")
        self.progress_callback(f"Description: {package_info['description']}")

        try:
            python_exe = self._get_python_exe()
            vendor_path = self._get_pip_target_directory()

            # Ensure target directory exists
            if not os.path.exists(vendor_path):
                os.makedirs(vendor_path)
                self.progress_callback(f"Created vendor directory: {vendor_path}")

            # Build pip command with enhanced options for Python 3.13+
            cmd = [
                python_exe,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--target",
                vendor_path,
                "--upgrade",  # Ensure we get the latest compatible version
            ]

            # Add Python 3.13+ specific options
            if self.python_compatibility["is_313_plus"]:
                # For Python 3.13+, we may need to allow pre-releases for some packages
                if package_name in ["aiohttp", "multidict", "yarl", "aiosignal"]:
                    cmd.append("--pre")  # Allow pre-release versions if needed

                # Use newer pip resolver
                cmd.extend(["--use-feature", "2020-resolver"])

            cmd.append(package_spec)

            self.progress_callback(f"Running: {' '.join(cmd)}")

            try:
                result = subprocess.run(
                    cmd,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    check=False  # Don't raise exception on non-zero exit
                )

                # Log output for debugging
                if result.stdout:
                    for line in result.stdout.split("\n"):
                        if line.strip():
                            self.progress_callback(f"pip: {line}")

                if result.stderr:
                    for line in result.stderr.split("\n"):
                        if line.strip():
                            self.progress_callback(f"pip error: {line}")

                # Check return code
                if result.returncode == 0:
                    self.progress_callback(f"✅ Successfully installed {package_name}")

                    # Verify the installation worked including sub-dependencies
                    if self.check_dependency(package_name):
                        self.progress_callback(f"✅ Verified {package_name} is now importable")

                        # For aiohttp, also verify critical sub-dependencies
                        if package_name == "aiohttp":
                            sub_deps_ok = True
                            for sub_dep in ["multidict", "yarl", "aiosignal"]:
                                if not self.check_dependency(sub_dep):
                                    self.progress_callback(f"⚠️ Sub-dependency {sub_dep} not available after {package_name} installation")
                                    sub_deps_ok = False

                            if sub_deps_ok:
                                self.progress_callback(f"✅ All {package_name} sub-dependencies verified")
                            else:
                                self.progress_callback(f"⚠️ Some {package_name} sub-dependencies missing - may need manual installation")

                        return True
                    else:
                        self.progress_callback(f"⚠️ {package_name} installed but not importable - may need restart")
                        return True  # Consider it successful, restart may be needed
                else:
                    self.progress_callback(f"❌ Failed to install {package_name} (exit code: {result.returncode})")

                    # Try alternative installation strategies for critical packages
                    if package_info.get("critical", False):
                        return self._try_alternative_installation(package_name, vendor_path, timeout)

                    return False

            except subprocess.TimeoutExpired:
                self.progress_callback(f"❌ Installation of {package_name} timed out after {timeout} seconds")
                return False

        except Exception as e:
            self.progress_callback(f"❌ Error installing {package_name}: {str(e)}")
            self.progress_callback(f"❌ Traceback: {traceback.format_exc()}")
            return False

    def _try_alternative_installation(self, package_name: str, vendor_path: str, timeout: int) -> bool:
        """Try alternative installation strategies for critical packages."""
        self.progress_callback(f"Trying alternative installation strategies for {package_name}...")

        python_exe = self._get_python_exe()

        # Strategy 1: Install without version constraints but WITH dependencies
        try:
            self.progress_callback(f"Trying {package_name} without version constraints...")
            cmd = [
                python_exe,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--target",
                vendor_path,
                # NOTE: Removed --no-deps to allow sub-dependencies to install
                package_name  # No version specification
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

            if result.returncode == 0:
                self.progress_callback(f"✅ Alternative installation of {package_name} succeeded")
                return True

        except Exception as e:
            self.progress_callback(f"Alternative installation strategy 1 failed: {e}")

        # Strategy 2: Try with --force-reinstall but keep dependencies
        try:
            self.progress_callback(f"Trying {package_name} with force reinstall...")
            version_spec = self._get_package_version_spec(package_name)
            package_spec = f"{package_name}{version_spec}"

            cmd = [
                python_exe,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--target",
                vendor_path,
                "--force-reinstall",
                # NOTE: Removed --no-deps to allow sub-dependencies to install
                package_spec
            ]

            result = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)

            if result.returncode == 0:
                self.progress_callback(f"✅ Force reinstall of {package_name} succeeded")
                return True

        except Exception as e:
            self.progress_callback(f"Alternative installation strategy 2 failed: {e}")

        # Strategy 3: Try installing sub-dependencies individually for aiohttp
        if package_name == "aiohttp":
            try:
                self.progress_callback(f"Trying to install {package_name} sub-dependencies individually...")
                sub_deps = ["multidict", "yarl", "aiosignal"]

                for sub_dep in sub_deps:
                    if not self.check_dependency(sub_dep):
                        self.progress_callback(f"Installing sub-dependency: {sub_dep}")
                        sub_cmd = [
                            python_exe,
                            "-m",
                            "pip",
                            "install",
                            "--disable-pip-version-check",
                            "--target",
                            vendor_path,
                            sub_dep
                        ]

                        sub_result = subprocess.run(sub_cmd, capture_output=True, text=True, timeout=timeout)
                        if sub_result.returncode == 0:
                            self.progress_callback(f"✅ Sub-dependency {sub_dep} installed")
                        else:
                            self.progress_callback(f"⚠️ Sub-dependency {sub_dep} failed to install")

                # Now try installing aiohttp again
                self.progress_callback(f"Retrying {package_name} installation after sub-dependencies...")
                retry_cmd = [
                    python_exe,
                    "-m",
                    "pip",
                    "install",
                    "--disable-pip-version-check",
                    "--target",
                    vendor_path,
                    package_name
                ]

                retry_result = subprocess.run(retry_cmd, capture_output=True, text=True, timeout=timeout)
                if retry_result.returncode == 0:
                    self.progress_callback(f"✅ {package_name} installation succeeded after sub-dependency installation")
                    return True

            except Exception as e:
                self.progress_callback(f"Alternative installation strategy 3 failed: {e}")

        self.progress_callback(f"❌ All alternative installation strategies failed for {package_name}")
        return False

    def install_missing_dependencies(self, timeout: int = 180, critical_only: bool = False) -> bool:
        """Install all missing dependencies with enhanced handling.

        Args:
            timeout: Timeout in seconds for each installation
            critical_only: If True, only install critical dependencies

        Returns:
            True if all installations succeeded, False otherwise
        """
        if critical_only:
            missing = self.get_critical_missing_dependencies()
            self.progress_callback(f"Installing {len(missing)} critical missing dependencies...")
        else:
            missing = self.get_missing_dependencies()
            self.progress_callback(f"Installing {len(missing)} missing dependencies...")

        if not missing:
            self.progress_callback("✅ All required dependencies are already installed")
            return True

        self.progress_callback(f"Missing dependencies: {', '.join(missing)}")

        success_count = 0
        for package_name in missing:
            if self.install_dependency(package_name, timeout):
                success_count += 1

        if success_count == len(missing):
            self.progress_callback(f"✅ Successfully installed all {len(missing)} missing dependencies")
            return True
        else:
            self.progress_callback(f"⚠️ Installed {success_count}/{len(missing)} dependencies")

            # If critical dependencies failed, this is a bigger problem
            failed_critical = []
            for package_name in missing:
                if not self.check_dependency(package_name) and self.REQUIRED_DEPENDENCIES[package_name].get("critical", False):
                    failed_critical.append(package_name)

            if failed_critical:
                self.progress_callback(f"❌ Critical dependencies failed to install: {', '.join(failed_critical)}")
                return False
            else:
                self.progress_callback("✅ All critical dependencies installed successfully")
                return True


    def auto_install_on_first_run(self) -> bool:
        """Automatically install missing dependencies on first run or when critical deps are missing."""
        try:
            self.progress_callback("Checking for missing dependencies...")

            # Check if any critical dependencies are missing
            critical_missing = self.get_critical_missing_dependencies()

            if critical_missing:
                self.progress_callback(f"Critical dependencies missing: {', '.join(critical_missing)}")
                self.progress_callback("Attempting automatic installation...")

                # Special handling for aiohttp and its sub-dependencies
                if "aiohttp" in critical_missing:
                    self.progress_callback("Detected missing aiohttp - checking sub-dependencies...")

                    # Check if sub-dependencies are also missing
                    aiohttp_sub_deps = self.check_sub_dependencies("aiohttp")
                    missing_sub_deps = [dep for dep, available in aiohttp_sub_deps.items() if not available]

                    if missing_sub_deps:
                        self.progress_callback(f"Missing aiohttp sub-dependencies: {', '.join(missing_sub_deps)}")

                        # Install sub-dependencies first
                        for sub_dep in missing_sub_deps:
                            if sub_dep in self.REQUIRED_DEPENDENCIES:
                                self.progress_callback(f"Installing sub-dependency: {sub_dep}")
                                self.install_dependency(sub_dep)

                # Try to install critical dependencies
                if self.install_missing_dependencies(critical_only=True):
                    self.progress_callback("✅ Critical dependencies installed successfully")

                    # Verify sub-dependencies for aiohttp
                    if "aiohttp" in critical_missing and self.check_dependency("aiohttp"):
                        aiohttp_sub_deps = self.check_sub_dependencies("aiohttp")
                        missing_after_install = [dep for dep, available in aiohttp_sub_deps.items() if not available]

                        if missing_after_install:
                            self.progress_callback(f"⚠️ Some aiohttp sub-dependencies still missing: {', '.join(missing_after_install)}")
                            self.progress_callback("Attempting to install missing sub-dependencies...")

                            for sub_dep in missing_after_install:
                                if sub_dep in self.REQUIRED_DEPENDENCIES:
                                    self.install_dependency(sub_dep)
                        else:
                            self.progress_callback("✅ All aiohttp sub-dependencies verified")

                    # Try to install optional dependencies too
                    all_missing = self.get_missing_dependencies()
                    if all_missing:
                        self.progress_callback("Installing remaining optional dependencies...")
                        self.install_missing_dependencies(critical_only=False)

                    return True
                else:
                    self.progress_callback("❌ Failed to install critical dependencies")
                    return False
            else:
                # Check for any missing optional dependencies
                all_missing = self.get_missing_dependencies()
                if all_missing:
                    self.progress_callback(f"Optional dependencies missing: {', '.join(all_missing)}")
                    self.progress_callback("Installing optional dependencies...")
                    return self.install_missing_dependencies(critical_only=False)
                else:
                    self.progress_callback("✅ All dependencies are already installed")

                    # Even if all main dependencies are available, check sub-dependencies
                    if self.check_dependency("aiohttp"):
                        aiohttp_sub_deps = self.check_sub_dependencies("aiohttp")
                        missing_sub_deps = [dep for dep, available in aiohttp_sub_deps.items() if not available]

                        if missing_sub_deps:
                            self.progress_callback(f"⚠️ aiohttp sub-dependencies missing: {', '.join(missing_sub_deps)}")
                            self.progress_callback("Installing missing sub-dependencies...")

                            for sub_dep in missing_sub_deps:
                                if sub_dep in self.REQUIRED_DEPENDENCIES:
                                    self.install_dependency(sub_dep)

                    return True
        except Exception as e:
            self.progress_callback(f"❌ Auto-installation failed: {e}")
            self.progress_callback(f"❌ Traceback: {traceback.format_exc()}")
            return False
    

    def get_installation_info(self) -> Dict[str, str]:
        """Get information about the current installation.

        Returns:
            Dictionary with installation information
        """
        info = {
            "freecad_version": f"{self.freecad_version[0]}.{self.freecad_version[1]}",
            "installation_type": self.installation_type,
            "python_executable": self._get_python_exe(),
            "pip_target_directory": self._get_pip_target_directory(),
            "platform": sys.platform,
        }

        # Add Python compatibility info
        info.update({
            f"python_{key}": str(value) for key, value in self.python_compatibility.items()
        })

        return info

    def create_install_script(self, package_name: str) -> str:
        """Create a script that can be run in FreeCAD Python console to install a dependency.

        Args:
            package_name: Name of the package to install

        Returns:
            Python script as string
        """
        if package_name not in self.REQUIRED_DEPENDENCIES:
            return f"# Unknown dependency: {package_name}"

        package_info = self.REQUIRED_DEPENDENCIES[package_name]
        version_spec = self._get_package_version_spec(package_name)
        package_spec = f"{package_name}{version_spec}"

        script = f"""
# Install {package_name} for FreeCAD FreeCAD AI
# {package_info['description']}

def install_{package_name.replace('-', '_')}():
    import subprocess
    import os
    import sys

    try:
        # Python version compatibility check
        python_version = sys.version_info
        if python_version >= (3, 13):
            print(f"Python {{python_version.major}}.{{python_version.minor}} detected - using enhanced compatibility mode")

        # Try to get the correct Python executable and target directory
        try:
            # FreeCAD 0.22+
            from freecad.utils import get_python_exe
            python_exe = get_python_exe()
        except ImportError:
            try:
                # FreeCAD 0.21
                import addonmanager_utilities as utils
                python_exe = utils.get_python_exe()
            except ImportError:
                python_exe = sys.executable

        try:
            import addonmanager_utilities as utils
            vendor_path = utils.get_pip_target_directory()
        except ImportError:
            import FreeCAD
            user_dir = FreeCAD.getUserAppDataDir()
            vendor_path = os.path.join(user_dir, 'Mod', 'vendor')

        # Ensure target directory exists
        if not os.path.exists(vendor_path):
            os.makedirs(vendor_path)

        # Install the package with Python 3.13+ compatibility
        cmd = [
            python_exe,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--target",
            vendor_path,
            "--upgrade"
        ]

        # Add Python 3.13+ specific options
        if python_version >= (3, 13):
            cmd.extend(["--use-feature", "2020-resolver"])
            if "{package_name}" in ["aiohttp"]:
                cmd.append("--pre")  # Allow pre-releases if needed

        cmd.append("{package_spec}")

        print(f"Installing {package_name} (version: {version_spec})...")
        print(f"Command: {{' '.join(cmd)}}")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=180)

        if result.returncode == 0:
            print(f"✅ Successfully installed {package_name}")
            print("Please restart FreeCAD to use the new dependency.")
        else:
            print(f"❌ Failed to install {package_name}")
            print(f"Error: {{result.stderr}}")

            # Try alternative installation
            print("Trying alternative installation without version constraints...")
            alt_cmd = [
                python_exe,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--target",
                vendor_path,
                "--no-deps",
                "{package_name}"
            ]

            alt_result = subprocess.run(alt_cmd, capture_output=True, text=True, timeout=180)
            if alt_result.returncode == 0:
                print(f"✅ Alternative installation of {package_name} succeeded")
            else:
                print(f"❌ Alternative installation also failed")

    except Exception as e:
        print(f"❌ Error: {{str(e)}}")

# Run the installation
install_{package_name.replace('-', '_')}()
"""
        return script


# Convenience functions for easy use
def check_dependencies() -> Dict[str, bool]:
    """Check all required dependencies."""
    manager = DependencyManager()
    return manager.check_all_dependencies()


def install_missing_dependencies(
    progress_callback: Optional[Callable[[str], None]] = None,
) -> bool:
    """Install all missing dependencies."""
    manager = DependencyManager(progress_callback)
    return manager.install_missing_dependencies()


def auto_install_dependencies(
    progress_callback: Optional[Callable[[str], None]] = None,
) -> bool:
    """Automatically install missing dependencies on first run."""
    manager = DependencyManager(progress_callback)
    return manager.auto_install_on_first_run()


def get_aiohttp_install_script() -> str:
    """Get a script to install aiohttp."""
    manager = DependencyManager()
    return manager.create_install_script("aiohttp")
