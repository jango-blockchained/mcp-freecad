# freecad-ai/utils/dependency_checker.py
import importlib
import subprocess
import sys
import os

# It's good practice to define requirements in a central place
# For example, read from freecad-ai/requirements.txt
ADDON_REQUIREMENTS_FILE = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "requirements.txt"
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
                        package_name = line.split(">=")[0].split("==")[0].split("<=")[0].strip()
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

    def install_dependencies(self, dependencies_to_install: list[str]) -> tuple[list[str], list[str]]:
        """
        Installs a list of dependencies using pip.
        Returns a tuple containing two lists: successfully installed packages and failed packages.
        """
        if not dependencies_to_install:
            return [], []

        # Use the Python executable from sys.executable to ensure pip is called for the correct environment.
        pip_command = [sys.executable, "-m", "pip", "install"] + dependencies_to_install
        
        successfully_installed: list[str] = []
        failed_to_install: list[str] = []

        try:
            # Run the command
            # Set encoding for environments where default might not be utf-8
            process = subprocess.Popen(
                pip_command, 
                stdout=subprocess.PIPE, 
                stderr=subprocess.PIPE,
                text=True,  # Decodes stdout/stderr as text
                encoding='utf-8' # Explicitly set encoding
            )
            stdout, stderr = process.communicate()

            if process.returncode == 0:
                # Command was successful.
                # A more robust check would parse stdout to confirm which packages were actually installed or upgraded.
                # For now, we assume all listed dependencies were installed if pip returns 0.
                successfully_installed = list(dependencies_to_install)
                print(f"Pip install command successful for: {', '.join(dependencies_to_install)}")
                if stdout:
                    print(f"Pip stdout:\\n{stdout}")
                # It's possible for pip to succeed but have warnings in stderr
                if stderr:
                    print(f"Pip stderr (warnings):\\n{stderr}")
            else:
                # Command failed
                failed_to_install = list(dependencies_to_install)
                print(f"Pip install command failed for: {', '.join(dependencies_to_install)}")
                if stderr:
                    print(f"Pip stderr:\\n{stderr}")
                if stdout: # Sometimes pip puts error info in stdout too
                    print(f"Pip stdout (errors):\\n{stdout}")
            
            return successfully_installed, failed_to_install

        except FileNotFoundError:
            print("Error: pip command not found (sys.executable or pip module). Ensure Python and pip are correctly installed and in PATH.")
            # If pip itself is not found, all dependencies fail.
            return [], list(dependencies_to_install)
        except subprocess.SubprocessError as e: # More specific exception for subprocess issues
            print(f"A subprocess error occurred during installation: {e}")
            return [], list(dependencies_to_install)
        except Exception as e: # Catch other potential errors
            print(f"An unexpected error occurred during installation: {e}")
            return [], list(dependencies_to_install)

if __name__ == '__main__':
    # Example usage:
    checker = DependencyChecker()
    print("Required packages:", checker.required_packages)
    current_missing_deps = checker.get_missing_dependencies() # Renamed variable
    if current_missing_deps:
        print("Missing dependencies:", current_missing_deps)
        print(f"Attempting to install: {current_missing_deps[0]}")
        # Example: try to install the first missing dependency
        success, failure = checker.install_dependencies([current_missing_deps[0]])
        print("Successfully installed:", success)
        print("Failed to install:", failure)
        
        # Re-check after attempting install
        print("\\nRe-checking dependencies...")
        updated_missing_deps = checker.get_missing_dependencies()
        if updated_missing_deps:
            print("Still missing:", updated_missing_deps)
        else:
            print("All previously missing dependencies are now installed.")
    else:
        print("All dependencies seem to be installed.")
