# freecad_addon/mcp_indicator/config_manager.py
import FreeCAD
import os

class ConfigManager:
    """Manages loading, saving, and accessing configuration parameters."""

    def __init__(self):
        """Initialize the ConfigManager and load initial settings."""
        self.params = FreeCAD.ParamGet("User parameter:BaseApp/Preferences/Mod/MCPIndicator")
        self._load_settings()

    def _load_settings(self):
        """Load settings from FreeCAD parameters."""
        self.repo_path = self.params.GetString("RepoPath", "")
        self.server_script_path = self.params.GetString("ServerScriptPath", "")
        self.mcp_server_script_path = self.params.GetString("MCPServerScriptPath", "")
        self.mcp_server_host = self.params.GetString("MCPServerHost", "localhost")
        self.mcp_server_port = self.params.GetInt("MCPServerPort", 8000)
        self.mcp_server_config = self.params.GetString("MCPServerConfig", "")

        # Initial check: If repo path is set but script paths aren't, try to set them
        # This requires access to path finding logic, suggesting a dependency
        # We will handle this inter-dependency later during refactoring.

    def save_settings(self):
        """Save current settings to FreeCAD parameters."""
        self.params.SetString("RepoPath", self.repo_path)
        self.params.SetString("ServerScriptPath", self.server_script_path)
        self.params.SetString("MCPServerScriptPath", self.mcp_server_script_path)
        self.params.SetString("MCPServerHost", self.mcp_server_host)
        self.params.SetInt("MCPServerPort", self.mcp_server_port)
        self.params.SetString("MCPServerConfig", self.mcp_server_config)
        FreeCAD.Console.PrintMessage("MCP settings saved.\n")

    # --- Getters ---
    def get_repo_path(self):
        return self.repo_path

    def get_server_script_path(self):
        return self.server_script_path

    def get_mcp_server_script_path(self):
        return self.mcp_server_script_path

    def get_mcp_server_host(self):
        return self.mcp_server_host

    def get_mcp_server_port(self):
        return self.mcp_server_port

    def get_mcp_server_config(self):
        return self.mcp_server_config

    # --- Setters ---
    def set_repo_path(self, path):
        self.repo_path = path

    def set_server_script_path(self, path):
        self.server_script_path = path

    def set_mcp_server_script_path(self, path):
        self.mcp_server_script_path = path

    def set_mcp_server_host(self, host):
        self.mcp_server_host = host

    def set_mcp_server_port(self, port):
        self.mcp_server_port = port

    def set_mcp_server_config(self, path):
        self.mcp_server_config = path

# Example of how it might be used (in InitGui.py later)
# config = ConfigManager()
# repo_path = config.get_repo_path()
# config.set_mcp_server_port(8001)
# config.save_settings()
