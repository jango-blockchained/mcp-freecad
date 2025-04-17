# freecad_addon/mcp_indicator/path_finder.py
import os
import sys
import inspect
import shutil
import FreeCAD

class PathFinder:
    """Responsible for finding script paths and Python executable."""

    def __init__(self, config_manager):
        """Initialize PathFinder with a ConfigManager instance."""
        self.config = config_manager
        self._determine_initial_paths()

    def _determine_initial_paths(self):
        """Determine initial script paths based on config or defaults."""
        repo_path = self.config.get_repo_path()
        server_path = self.config.get_server_script_path()
        mcp_path = self.config.get_mcp_server_script_path()

        # If repo path is set but script paths are not, auto-set them
        if repo_path and (not server_path or not mcp_path):
            self.update_paths_from_repo()
            # Reload paths from config after update
            server_path = self.config.get_server_script_path()
            mcp_path = self.config.get_mcp_server_script_path()

        # If still not set, try to determine default paths
        if not server_path or not mcp_path:
            try:
                current_file_path = inspect.getfile(inspect.currentframe())
                current_dir = os.path.dirname(current_file_path)
                indicator_root = os.path.dirname(current_dir)
                project_root = os.path.dirname(indicator_root)

                if not server_path:
                    possible_server_paths = [
                        os.path.join(project_root, "freecad_socket_server.py"),
                        os.path.join(os.path.expanduser("~"), "Git", "mcp-freecad", "freecad_socket_server.py"),
                        "/usr/local/bin/freecad_socket_server.py",
                    ]
                    for path in possible_server_paths:
                        if os.path.exists(path):
                            self.config.set_server_script_path(path)
                            server_path = path # Update local variable
                            break

                if not mcp_path:
                    possible_mcp_paths = [
                        # Prioritize the bridge script
                        os.path.join(project_root, "cursor_mcp_bridge.py"),
                        # Add other potential locations for the bridge if needed
                        os.path.join(os.path.expanduser("~"), "Git", "mcp-freecad", "cursor_mcp_bridge.py"),
                    ]
                    for path in possible_mcp_paths:
                        if os.path.exists(path):
                            self.config.set_mcp_server_script_path(path)
                            mcp_path = path # Update local variable
                            break

                # Save determined paths if changed
                self.config.save_settings()

            except Exception as e:
                FreeCAD.Console.PrintError(f"Error determining default script paths: {str(e)}\n")

        # Log final paths
        if self.config.get_server_script_path():
            FreeCAD.Console.PrintMessage(f"Socket Server script path (Legacy): {self.config.get_server_script_path()}\n")
        else:
            FreeCAD.Console.PrintWarning("Socket Server script path not set. Configure in Settings if needed.\n")

        if self.config.get_mcp_server_script_path():
            FreeCAD.Console.PrintMessage(f"MCP Server script path: {self.config.get_mcp_server_script_path()}\n")
        else:
            FreeCAD.Console.PrintWarning("MCP Server script path not set. Controls will be disabled.\n")

    def update_paths_from_repo(self):
        """Update script paths based on the repository path in config."""
        repo_path = self.config.get_repo_path()
        if not repo_path or not os.path.isdir(repo_path):
            FreeCAD.Console.PrintWarning("Repository path not set or invalid, cannot auto-configure paths.\n")
            return False

        # Original paths for comparison
        old_server_path = self.config.get_server_script_path()
        old_mcp_path = self.config.get_mcp_server_script_path()
        paths_changed = False

        # --- Socket Server Path ---
        server_path = os.path.join(repo_path, "freecad_socket_server.py")
        if os.path.exists(server_path):
            self.config.set_server_script_path(server_path)
            if old_server_path != server_path:
                paths_changed = True
                FreeCAD.Console.PrintMessage(f"Auto-configured Socket Server path: {server_path}\n")
        else:
            # Optionally clear the path if it points outside the repo and doesn't exist?
            # Or just leave it as is if the user set it manually?
            pass

        # --- MCP Server Path ---
        # Look for the bridge script first
        mcp_bridge_path = os.path.join(repo_path, "cursor_mcp_bridge.py")

        preferred_mcp_path = None
        if os.path.exists(mcp_bridge_path):
            preferred_mcp_path = mcp_bridge_path
        else:
            # Fallback or warning if bridge not found?
            FreeCAD.Console.PrintWarning(f"cursor_mcp_bridge.py not found in repository root ({repo_path}). MCP server control might not work.\n")
            # Optionally, uncomment below to fall back to the direct server script:
            # mcp_py_path = os.path.join(repo_path, "src", "mcp_freecad", "server", "freecad_mcp_server.py")
            # if os.path.exists(mcp_py_path):
            #     preferred_mcp_path = mcp_py_path
            # else:
            #     self.config.set_mcp_server_script_path("") # Clear path if nothing found
            self.config.set_mcp_server_script_path("") # Clear path if bridge not found
            preferred_mcp_path = "" # Ensure it's cleared locally too

        if preferred_mcp_path:
            self.config.set_mcp_server_script_path(preferred_mcp_path)
            if old_mcp_path != preferred_mcp_path:
                paths_changed = True
                FreeCAD.Console.PrintMessage(f"Auto-configured MCP Server path: {preferred_mcp_path}\n")
        else:
            # Optionally clear the path?
            pass

        if paths_changed:
            self.config.save_settings()
            return True
        else:
            return False

    def get_python_executable(self):
        """Find an appropriate Python executable."""
        python_candidates = []
        repo_path = self.config.get_repo_path()

        # 1. SquashFS Python
        if repo_path and os.path.exists(repo_path):
            squashfs_python = os.path.join(repo_path, "squashfs-root", "usr", "bin", "python")
            if os.path.exists(squashfs_python):
                python_candidates.append(squashfs_python)

        # 2. Virtual Environments in Repo
        if repo_path and os.path.exists(repo_path):
            venv_python = os.path.join(repo_path, ".venv", "bin", "python")
            if os.path.exists(venv_python):
                python_candidates.append(venv_python)
            mcp_venv_python = os.path.join(repo_path, "mcp_venv", "bin", "python")
            if os.path.exists(mcp_venv_python):
                python_candidates.append(mcp_venv_python)

        # 3. System Python
        python_candidates.extend([
            shutil.which("python3"),
            shutil.which("python"),
            "/usr/bin/python3",
        ])

        # 4. FreeCAD embedded Python (Fallback)
        python_candidates.append(sys.executable)

        # Find the first valid executable
        for candidate in python_candidates:
            if candidate and os.path.exists(candidate):
                FreeCAD.Console.PrintMessage(f"Using Python executable: {candidate}\n")
                return candidate

        FreeCAD.Console.PrintError("Could not find a suitable Python executable.\n")
        return None

    def get_mcp_log_file_path(self):
        """Determine the expected path for the MCP server log file."""
        mcp_script_path = self.config.get_mcp_server_script_path()
        if mcp_script_path and os.path.exists(os.path.dirname(mcp_script_path)):
            script_dir = os.path.dirname(mcp_script_path)
            # If using the shell script in 'scripts', the logs are relative to the *server* script dir
            if os.path.basename(script_dir) == 'scripts':
                 # Assume log dir is relative to repo root/src/mcp_freecad/server/
                 repo_root = os.path.dirname(script_dir)
                 log_dir_rel = os.path.join(repo_root, "src", "mcp_freecad", "server", "logs")
                 # Fallback to relative to script dir if above doesn't exist
                 if not os.path.exists(log_dir_rel):
                      log_dir_rel = os.path.join(script_dir, "..", "logs") # Relative to parent of scripts/
                 log_path = os.path.normpath(os.path.join(log_dir_rel, "freecad_mcp_server.log"))
            else:
                 # Assume logs are in a 'logs' subdir relative to the script's location
                 log_path = os.path.normpath(os.path.join(script_dir, "logs", "freecad_mcp_server.log"))
            return log_path
        return None

# Example Usage (Conceptual)
# from config_manager import ConfigManager
# config = ConfigManager()
# path_finder = PathFinder(config)
# python_exec = path_finder.get_python_executable()
# path_finder.update_paths_from_repo()
# mcp_log = path_finder.get_mcp_log_file_path()
