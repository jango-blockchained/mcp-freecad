"""
Dependency Manager for FreeCAD MCP Integration

Handles installation and management of Python dependencies within FreeCAD,
supporting different FreeCAD versions and installation types.

Based on FreeCAD documentation and community best practices.
"""

import os
import sys
import subprocess
import importlib.util
from typing import List, Dict, Optional, Tuple, Callable
import FreeCAD


class DependencyManager:
    """Manages Python dependencies for the MCP Integration addon."""

    # Required dependencies for the addon
    REQUIRED_DEPENDENCIES = {
        'aiohttp': {
            'version': '>=3.8.0',
            'description': 'Async HTTP client for AI provider communication',
            'import_name': 'aiohttp'
        },
        'requests': {
            'version': '>=2.28.0',
            'description': 'HTTP library for API requests',
            'import_name': 'requests'
        },
        'mcp': {
            'version': '>=1.0.0',
            'description': 'Model Context Protocol library for Claude Desktop integration',
            'import_name': 'mcp'
        }
    }

    def __init__(self, progress_callback: Optional[Callable[[str], None]] = None):
        """Initialize the dependency manager.

        Args:
            progress_callback: Optional callback for progress updates
        """
        self.progress_callback = progress_callback or self._default_progress
        self.freecad_version = self._detect_freecad_version()
        self.installation_type = self._detect_installation_type()

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
            if os.environ.get('APPIMAGE'):
                return 'appimage'

            # Check if running from Snap
            if os.environ.get('SNAP'):
                return 'snap'

            # Check if Windows portable
            if sys.platform == 'win32' and 'FreeCAD' in sys.executable:
                return 'windows_portable'

            return 'standard'
        except:
            return 'standard'

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
                if hasattr(utils, 'get_python_exe'):
                    return utils.get_python_exe()
            except ImportError:
                pass

            # Fallback methods
            if self.installation_type == 'windows_portable':
                # For Windows portable, Python is usually in the bin directory
                freecad_dir = os.path.dirname(sys.executable)
                python_exe = os.path.join(freecad_dir, 'python.exe')
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
            if hasattr(utils, 'get_pip_target_directory'):
                return utils.get_pip_target_directory()
        except ImportError:
            pass

        # Fallback: use FreeCAD user directory
        try:
            user_dir = FreeCAD.getUserAppDataDir()
            vendor_path = os.path.join(user_dir, 'Mod', 'vendor')
            return vendor_path
        except:
            # Last resort
            return os.path.join(os.path.expanduser('~'), '.freecad', 'vendor')

    def check_dependency(self, package_name: str) -> bool:
        """Check if a dependency is installed and importable.

        Args:
            package_name: Name of the package to check

        Returns:
            True if the package is available, False otherwise
        """
        try:
            import_name = self.REQUIRED_DEPENDENCIES.get(package_name, {}).get('import_name', package_name)
            spec = importlib.util.find_spec(import_name)
            return spec is not None
        except ImportError:
            return False

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

    def install_dependency(self, package_name: str, timeout: int = 120) -> bool:
        """Install a single dependency.

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
        package_spec = f"{package_name}{package_info['version']}"

        self.progress_callback(f"Installing {package_name}...")
        self.progress_callback(f"Description: {package_info['description']}")

        try:
            python_exe = self._get_python_exe()
            vendor_path = self._get_pip_target_directory()

            # Ensure target directory exists
            if not os.path.exists(vendor_path):
                os.makedirs(vendor_path)
                self.progress_callback(f"Created vendor directory: {vendor_path}")

            # Build pip command
            cmd = [
                python_exe,
                "-m",
                "pip",
                "install",
                "--disable-pip-version-check",
                "--target",
                vendor_path,
                package_spec
            ]

            self.progress_callback(f"Running: {' '.join(cmd)}")

            # Run pip installation
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True
            )

            # Stream output
            while True:
                output = process.stdout.readline()
                if output == '' and process.poll() is not None:
                    break
                if output:
                    self.progress_callback(f"pip: {output.strip()}")

            # Get any remaining output
            stdout, stderr = process.communicate(timeout=timeout)

            if stdout:
                for line in stdout.split('\n'):
                    if line.strip():
                        self.progress_callback(f"pip: {line}")

            if stderr:
                for line in stderr.split('\n'):
                    if line.strip():
                        self.progress_callback(f"pip error: {line}")

            # Check return code
            if process.returncode == 0:
                self.progress_callback(f"✅ Successfully installed {package_name}")
                return True
            else:
                self.progress_callback(f"❌ Failed to install {package_name} (exit code: {process.returncode})")
                return False

        except subprocess.TimeoutExpired:
            self.progress_callback(f"❌ Installation of {package_name} timed out after {timeout} seconds")
            return False
        except Exception as e:
            self.progress_callback(f"❌ Error installing {package_name}: {str(e)}")
            return False

    def install_missing_dependencies(self, timeout: int = 120) -> bool:
        """Install all missing dependencies.

        Args:
            timeout: Timeout in seconds for each installation

        Returns:
            True if all installations succeeded, False otherwise
        """
        missing = self.get_missing_dependencies()

        if not missing:
            self.progress_callback("✅ All dependencies are already installed")
            return True

        self.progress_callback(f"Found {len(missing)} missing dependencies: {', '.join(missing)}")

        success_count = 0
        for package_name in missing:
            if self.install_dependency(package_name, timeout):
                success_count += 1

        if success_count == len(missing):
            self.progress_callback(f"✅ Successfully installed all {len(missing)} missing dependencies")
            return True
        else:
            self.progress_callback(f"⚠️ Installed {success_count}/{len(missing)} dependencies")
            return False

    def get_installation_info(self) -> Dict[str, str]:
        """Get information about the current installation.

        Returns:
            Dictionary with installation information
        """
        return {
            'freecad_version': f"{self.freecad_version[0]}.{self.freecad_version[1]}",
            'installation_type': self.installation_type,
            'python_executable': self._get_python_exe(),
            'pip_target_directory': self._get_pip_target_directory(),
            'platform': sys.platform
        }

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
        package_spec = f"{package_name}{package_info['version']}"

        script = f'''
# Install {package_name} for FreeCAD MCP Integration
# {package_info['description']}

def install_{package_name.replace('-', '_')}():
    import subprocess
    import os

    try:
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
                import sys
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

        # Install the package
        cmd = [
            python_exe,
            "-m",
            "pip",
            "install",
            "--disable-pip-version-check",
            "--target",
            vendor_path,
            "{package_spec}"
        ]

        print(f"Installing {package_name}...")
        print(f"Command: {{' '.join(cmd)}}")

        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            print(f"✅ Successfully installed {package_name}")
            print("Please restart FreeCAD to use the new dependency.")
        else:
            print(f"❌ Failed to install {package_name}")
            print(f"Error: {{result.stderr}}")

    except Exception as e:
        print(f"❌ Error: {{str(e)}}")

# Run the installation
install_{package_name.replace('-', '_')}()
'''
        return script


# Convenience functions for easy use
def check_dependencies() -> Dict[str, bool]:
    """Check all required dependencies."""
    manager = DependencyManager()
    return manager.check_all_dependencies()


def install_missing_dependencies(progress_callback: Optional[Callable[[str], None]] = None) -> bool:
    """Install all missing dependencies."""
    manager = DependencyManager(progress_callback)
    return manager.install_missing_dependencies()


def get_aiohttp_install_script() -> str:
    """Get a script to install aiohttp."""
    manager = DependencyManager()
    return manager.create_install_script('aiohttp')
