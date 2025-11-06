# freecad-ai/utils/dependency_checker.py
import importlib
import subprocess
import sys
import os

# It's good practice to define requirements in a central place
# For example, read from freecad-ai/requirements.txt
ADDON_REQUIREMENTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "requirements.txt"
)


class DependencyChecker:
    def __init__(self):
        self.required_packages = self._parse_requirements()

    def _parse_requirements(self):
        """Parses the requirements.txt file for the addon."""
        packages = []
        try:
            with open(ADDON_REQUIREMENTS_FILE, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Basic parsing, might need to be more robust for version specifiers, etc.
                        package_name = (
                            line.split(">=")[0].split("==")[0].split("<=")[0].strip()
                        )
                        packages.append(package_name)
        except FileNotFoundError:
            print(f"Error: {ADDON_REQUIREMENTS_FILE} not found.")
        return packages

    def get_missing_dependencies(self):
        """Checks for missing dependencies."""
        missing = []
        for package_spec in self.required_packages:
            try:
                # For packages with hyphens in name, Python import name might use underscores
                import_name = package_spec.replace("-", "_")
                importlib.import_module(import_name)
            except ImportError:
                missing.append(package_spec)
            except (TypeError, AttributeError) as e:
                # Handle Protocol-related errors and other type inspection issues
                if "Protocols" in str(e) or "issubclass" in str(e):
                    # Package is installed but has Protocol/typing issues, skip it
                    continue
                else:
                    # Some other error, treat as missing
                    missing.append(package_spec)
            except Exception as e:
                # Handle any other unexpected errors during import
                print(f"Warning: Unexpected error checking {package_spec}: {e}")
                missing.append(package_spec)
        return missing

    def install_dependencies(
        self, dependencies_to_install: list[str]
    ) -> tuple[list[str], list[str]]:
        """
        Installs a list of dependencies using pip with FreeCAD compatibility.
        Returns a tuple containing two lists: successfully installed packages and failed packages.
        """
        if not dependencies_to_install:
            return [], []

        successfully_installed: list[str] = []
        failed_to_install: list[str] = []

        for package in dependencies_to_install:
            print(f"Installing {package}...")
            installation_success = False

            # Method 1: Try programmatic pip (most FreeCAD-compatible)
            try:
                import pip

                pip_args = ["install", package]

                # Try different pip interfaces
                if hasattr(pip, "main"):
                    # Older pip versions
                    result = pip.main(pip_args)
                    if result == 0:
                        installation_success = True
                        successfully_installed.append(package)
                        print(f"✅ Successfully installed {package} (pip.main)")
                elif hasattr(pip, "_internal"):
                    # Newer pip versions
                    from pip._internal import main as pip_main

                    result = pip_main(pip_args)
                    if result == 0:
                        installation_success = True
                        successfully_installed.append(package)
                        print(f"✅ Successfully installed {package} (pip._internal)")

            except Exception as e:
                print(f"⚠️ Programmatic pip failed for {package}: {e}")

            # Method 2: Try direct pip executable (if programmatic failed)
            if not installation_success:
                try:
                    import shutil

                    pip_executable = shutil.which("pip") or shutil.which("pip3")
                    if pip_executable:
                        pip_command = [pip_executable, "install", package]

                        # Run the command
                        process = subprocess.Popen(
                            pip_command,
                            stdout=subprocess.PIPE,
                            stderr=subprocess.PIPE,
                            text=True,
                            encoding="utf-8",
                        )

                        stdout, stderr = process.communicate()

                        if process.returncode == 0:
                            installation_success = True
                            successfully_installed.append(package)
                            print(f"✅ Successfully installed {package} (direct pip)")
                        else:
                            print(f"⚠️ Direct pip failed for {package}: {stderr}")
                    else:
                        print(f"⚠️ Direct pip executable not found for {package}")

                except Exception as e:
                    print(f"⚠️ Direct pip approach failed for {package}: {e}")

            # Method 3: Try subprocess with python -c (avoid -m flag)
            if not installation_success:
                try:
                    # Build pip install command as Python code to avoid -m flag
                    pip_code = f"import pip; pip.main(['install', '{package}'])"

                    process = subprocess.Popen(
                        [sys.executable, "-c", pip_code],
                        stdout=subprocess.PIPE,
                        stderr=subprocess.PIPE,
                        text=True,
                        encoding="utf-8",
                    )

                    stdout, stderr = process.communicate()

                    if process.returncode == 0:
                        installation_success = True
                        successfully_installed.append(package)
                        print(f"✅ Successfully installed {package} (subprocess)")
                    else:
                        print(f"⚠️ Subprocess approach failed for {package}: {stderr}")

                except Exception as e:
                    print(f"⚠️ Subprocess approach failed for {package}: {e}")

            # If all methods failed
            if not installation_success:
                failed_to_install.append(package)
                print(f"❌ All installation methods failed for {package}")

        return successfully_installed, failed_to_install


if __name__ == "__main__":
    checker = DependencyChecker()
    missing_deps = checker.get_missing_dependencies()

    if missing_deps:
        print(f"Missing dependencies: {missing_deps}")
        current_missing_deps = missing_deps
        success, failure = checker.install_dependencies([current_missing_deps[0]])
        print(f"Successfully installed: {success}")
        print(f"Failed to install: {failure}")
    else:
        print("All dependencies are satisfied!")
