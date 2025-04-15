import os
import socket
import time
import json
import FreeCAD
import subprocess
import signal
import platform
import sys
import shlex

class StatusChecker:
    """Handles periodic checking of server and connection status."""

    def __init__(self, config_manager, process_manager):
        """Initialize with the config and process manager instances."""
        self.config = config_manager
        self.process_manager = process_manager
        self.connection_timestamp = None
        self.last_check_time = 0
        self.connection_details = {}
        self.mcp_version = "Unknown"
        self.connected = False
        self.connection_error = None

    def check_status(self):
        """Check the status of the FreeCAD/MCP servers and connection."""
        # Skip rapid rechecks (throttle to prevent UI lag)
        current_time = time.time()
        if current_time - self.last_check_time < 0.5:  # half-second throttle
            return False

        self.last_check_time = current_time

        # Check connection to MCP server
        connection_changed = self.check_connection()

        # Update connection details if connected
        if self.connected:
            self.update_connection_details()

        return connection_changed

    def check_connection(self):
        """Check if we can connect to the MCP server."""
        previous_state = self.connected

        try:
            # Create a socket connection to the MCP server
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(1.0)  # 1 second timeout for connection attempt
            s.connect((self.config.get_mcp_server_host(), self.config.get_mcp_server_port()))
            s.close()

            # Connection succeeded
            self.connected = True
            self.connection_error = None

            # Update connection timestamp if connection newly established
            if not previous_state:
                self.connection_timestamp = time.time()

        except Exception as e:
            # Connection failed
            self.connected = False
            self.connection_error = str(e)

        # Return True if connection state changed
        return previous_state != self.connected

    def update_connection_details(self):
        """Update details about the MCP server connection."""
        try:
            # Try to get server info via HTTP
            import urllib.request
            import urllib.error

            url = f"http://{self.config.get_mcp_server_host()}:{self.config.get_mcp_server_port()}/version"

            try:
                with urllib.request.urlopen(url, timeout=2) as response:
                    if response.code == 200:
                        version_info = response.read().decode('utf-8')
                        try:
                            version_data = json.loads(version_info)
                            self.mcp_version = version_data.get("version", "Unknown")
                            self.connection_details = {
                                "mcp_version": self.mcp_version,
                                "api_version": version_data.get("api_version", "Unknown"),
                                "python_version": version_data.get("python_version", "Unknown"),
                                "uptime": version_data.get("uptime", "Unknown"),
                                "connections": self.get_active_connections()
                            }
                        except json.JSONDecodeError:
                            self.mcp_version = version_info.strip()
                            self.connection_details = {"mcp_version": self.mcp_version}
            except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout):
                # Fall back to minimal info if HTTP request fails
                self.connection_details = {"mcp_version": "Unknown"}

        except Exception as e:
            FreeCAD.Console.PrintWarning(f"Error updating connection details: {str(e)}\n")
            self.connection_details = {"error": str(e)}

    def get_active_connections(self):
        """Get information about active connections to the MCP server."""
        try:
            import urllib.request
            import urllib.error

            url = f"http://{self.config.get_mcp_server_host()}:{self.config.get_mcp_server_port()}/connections"

            try:
                with urllib.request.urlopen(url, timeout=2) as response:
                    if response.code == 200:
                        connections_info = response.read().decode('utf-8')
                        try:
                            return json.loads(connections_info)
                        except json.JSONDecodeError:
                            return {"error": "Invalid JSON response"}
            except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout):
                return {"error": "Could not connect to server"}

        except Exception as e:
            return {"error": str(e)}

        return {"error": "Unknown error getting connections"}

    def get_detailed_connection_info(self):
        """Get detailed connection information as a dictionary."""
        # Get the most up-to-date connection details
        if self.connected:
            self.update_connection_details()

        info = {
            "connected": self.connected,
            "connection_time": self.connection_timestamp,
            "mcp_server_host": self.config.get_mcp_server_host(),
            "mcp_server_port": self.config.get_mcp_server_port(),
            "mcp_version": self.mcp_version,
            "freecad_server_running": self.process_manager.is_freecad_server_running(),
            "mcp_server_running": self.process_manager.is_mcp_server_running(),
            "details": self.connection_details,
            "connection_error": self.connection_error
        }

        # Add timestamps
        if self.connected and self.connection_timestamp:
            duration = time.time() - self.connection_timestamp
            hours, remainder = divmod(duration, 3600)
            minutes, seconds = divmod(remainder, 60)

            if hours > 0:
                info["connection_duration"] = f"{int(hours)}h {int(minutes)}m {int(seconds)}s"
            elif minutes > 0:
                info["connection_duration"] = f"{int(minutes)}m {int(seconds)}s"
            else:
                info["connection_duration"] = f"{int(seconds)}s"

        return info
