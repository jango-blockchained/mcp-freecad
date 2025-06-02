import os
import socket
import time
import json
import FreeCAD
import logging

logger = logging.getLogger("MCPIndicator.StatusChecker")

class StatusChecker:
    """Handles periodic checking of server and connection status."""

    def __init__(self, config_manager, process_manager):
        """Initialize with the config and process manager instances."""
        self.config_manager = config_manager
        self.process_manager = process_manager
        self.connection_timestamp = None
        self.last_status_check_time = 0
        self.last_connection_check_time = 0
        self.connection_details = {}
        self.client_connected = False
        self.connection_error = None

        # Cache status to avoid redundant checks within a single update cycle
        self._cached_fc_status = None
        self._cached_mcp_status = None
        self._cached_client_connected = None

    def check_status(self):
        """
        Check the status of servers and client connection.
        Returns True if any relevant status changed, False otherwise.
        This is the main method called periodically.
        """
        current_time = time.time()
        # Throttle checks to avoid excessive resource usage
        if current_time - self.last_status_check_time < 1.0: # Check overall status every 1 second
            return False # No check performed

        self.last_status_check_time = current_time
        logger.debug("Performing status check...")

        # Clear cache for this cycle
        self._cached_fc_status = None
        self._cached_mcp_status = None
        self._cached_client_connected = None

        # Check individual components
        # Note: These calls will populate the cache
        old_client_connected = self.client_connected
        client_now_connected = self.is_client_connected()

        # Get current server statuses (these methods use cache internally)
        fc_status_changed = self._check_fc_server_status_changed()
        mcp_status_changed = self._check_mcp_server_status_changed()

        client_conn_changed = (old_client_connected != client_now_connected)

        status_changed = client_conn_changed or fc_status_changed or mcp_status_changed

        if status_changed:
             logger.info(f"Status change detected: Client={client_conn_changed}, FC={fc_status_changed}, MCP={mcp_status_changed}")

        # Update details only if client is connected (and maybe throttle this too?)
        if self.client_connected:
            # Throttle detail updates separately? e.g., every 5 seconds
            if current_time - getattr(self, '_last_detail_update', 0) > 5.0:
                 self.update_connection_details() # Fetch version etc. from server
                 self._last_detail_update = current_time

        return status_changed

    # --- Individual Status Getters (using cache) ---

    def is_client_connected(self) -> bool:
        """Check connection to the MCP server (cached)."""
        if self._cached_client_connected is None:
            self._cached_client_connected, self.connection_error = self._perform_connection_check()
            # Update timestamp only if status changes to connected
            if self._cached_client_connected and not self.client_connected:
                self.connection_timestamp = time.time()
            elif not self._cached_client_connected:
                 self.connection_timestamp = None # Reset if disconnected
            # Update the main state variable
            self.client_connected = self._cached_client_connected
        return self._cached_client_connected

    def get_fc_server_status(self) -> dict:
        """Get status of the FreeCAD RPC server (cached)."""
        if self._cached_fc_status is None:
            try:
                # Import only when needed to avoid circular imports
                from rpc_server import rpc_server_thread, rpc_server_instance

                is_running = rpc_server_thread is not None and rpc_server_instance is not None

                self._cached_fc_status = {
                    "running": is_running,
                    "pid": None,  # RPC server runs in a thread, not a separate process
                    "type": "rpc"
                }
            except ImportError:
                # If the module is not available, assume not running
                self._cached_fc_status = {
                    "running": False,
                    "pid": None,
                    "type": "rpc"
                }

            logger.debug(f"Checked FC RPC server status: {self._cached_fc_status}")
        return self._cached_fc_status

    def get_mcp_server_status(self) -> dict:
        """Get status of the MCP server (managed or external) (cached)."""
        if self._cached_mcp_status is None:
            if self.process_manager.is_mcp_server_running(): # Check if managed process is alive
                pid = self.process_manager.mcp_server_process.pid if self.process_manager.mcp_server_process else None
                self._cached_mcp_status = {"status": "running_managed", "pid": pid}
            else:
                # If not managed, check if *any* process is listening on the port
                host = self.config_manager.get_mcp_server_host()
                port = self.config_manager.get_mcp_server_port()
                is_listening, _ = self._is_port_listening(host, port)
                if is_listening:
                    self._cached_mcp_status = {"status": "running_external", "pid": None}
                else:
                    self._cached_mcp_status = {"status": "stopped", "pid": None}
            logger.debug(f"Checked MCP server status: {self._cached_mcp_status}")
        return self._cached_mcp_status

    # --- Internal Check Logic ---

    def _check_fc_server_status_changed(self) -> bool:
        """Checks if the FC server status has changed since last check."""
        # Retrieve previous status if available, otherwise assume initial state (e.g., stopped)
        prev_status = getattr(self, '_last_known_fc_status', {"running": False, "pid": None})
        current_status = self.get_fc_server_status() # Uses cache
        changed = (prev_status != current_status)
        if changed:
             self._last_known_fc_status = current_status
        return changed

    def _check_mcp_server_status_changed(self) -> bool:
        """Checks if the MCP server status has changed since last check."""
        prev_status = getattr(self, '_last_known_mcp_status', {"status": "stopped", "pid": None})
        current_status = self.get_mcp_server_status() # Uses cache
        changed = (prev_status != current_status)
        if changed:
            self._last_known_mcp_status = current_status
        return changed

    def _perform_connection_check(self) -> (bool, str | None):
        """Physically check the socket connection to the MCP server."""
        host = self.config_manager.get_mcp_server_host()
        port = self.config_manager.get_mcp_server_port()
        is_listening, error = self._is_port_listening(host, port)
        logger.debug(f"Connection check to {host}:{port}: listening={is_listening}, error={error}")
        return is_listening, error

    def _is_port_listening(self, host: str, port: int) -> (bool, str | None):
        """Checks if a host/port is actively listening for connections."""
        s = None
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)  # Short timeout for check
            s.connect((host, int(port)))
            # If connect succeeds, something is listening
            return True, None
        except socket.timeout:
            # Timeout likely means firewall or host unreachable, treat as not listening here
            return False, "Connection timed out"
        except ConnectionRefusedError:
            # Explicit refusal means host is reachable, but port is not open
            return False, "Connection refused"
        except socket.gaierror:
             # Hostname resolution error
             return False, "Hostname could not be resolved"
        except ValueError:
             # Port might be invalid if config returns non-integer somehow
             logger.error(f"Invalid port value encountered: {port}")
             return False, "Invalid port number"
        except Exception as e:
            # Other errors
            logger.warning(f"Unexpected error checking port {host}:{port}: {e}")
            return False, str(e)
        finally:
            if s: s.close()

    # --- Detail Fetching (Assumes HTTP endpoint on MCP Server) ---

    def update_connection_details(self):
        """Update details about the MCP server connection via HTTP GET (if available)."""
        # Reset details first
        self.connection_details = {}
        host = self.config_manager.get_mcp_server_host()
        port = self.config_manager.get_mcp_server_port()
        # Assuming MCP server might have simple HTTP endpoints alongside main protocol
        # Construct base URL carefully, ensuring port is valid
        try:
             base_url = f"http://{host}:{int(port)}" # Ensure port is int
        except (ValueError, TypeError):
             logger.error(f"Invalid MCP Server port ({port}) for fetching details.")
             self.connection_details = {"error": "Invalid port for HTTP details"}
             return

        details = {}
        try:
            version_info = self._fetch_server_endpoint(base_url, "version")
            if version_info:
                 details.update(version_info)

            # Fetch connections only if version fetch worked?
            # connections_info = self._fetch_server_endpoint(base_url, "connections")
            # if connections_info:
            #     details["connections"] = connections_info

            self.connection_details = details
            logger.debug(f"Updated connection details: {self.connection_details}")

        except Exception as e:
            logger.warning(f"Could not update connection details from {base_url}: {e}")
            self.connection_details = {"error": f"Failed to fetch details: {e}"}

    def _fetch_server_endpoint(self, base_url: str, endpoint: str) -> dict | None:
        """Helper to fetch JSON data from an HTTP endpoint on the server."""
        try:
            import urllib.request
            import urllib.error
            url = f"{base_url}/{endpoint}"
            logger.debug(f"Fetching details from {url}")
            req = urllib.request.Request(url, headers={'User-Agent': 'MCPIndicator-FreeCAD'})
            with urllib.request.urlopen(req, timeout=1.5) as response:
                if response.code == 200:
                    content = response.read().decode('utf-8')
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError as json_err:
                        logger.warning(f"Invalid JSON from {url}: {json_err}")
                        return {"error": "Invalid JSON response", "raw": content[:100]}
                else:
                    logger.warning(f"Server returned status {response.code} for {url}")
                    return {"error": f"Server status {response.code}"}
        except (urllib.error.URLError, urllib.error.HTTPError, socket.timeout) as url_err:
            # Log specific error types differently if needed
            logger.warning(f"Could not connect to {url}: {url_err}")
            # Don't set general error here, just return None
            return None
        except ImportError:
            logger.error("'urllib' module not found, cannot fetch server details.")
            return {"error": "urllib not available"}
        except Exception as e:
            logger.error(f"Unexpected error fetching {url}: {e}")
            return {"error": str(e)}


    # --- Public Info Accessors ---

    def get_client_details(self) -> dict:
         """Returns cached details fetched from the connected server."""
         # Maybe add peer address if available from socket check? Difficult.
         return self.connection_details

    def get_connection_error(self) -> str | None:
        """Returns the last connection error message, if any."""
        return self.connection_error

    # get_detailed_connection_info can be refactored or removed
    # if the UI manager now uses the specific getters.
    # Keep it for now if dialogs still use it.
    def get_detailed_connection_info(self):
        """Get comprehensive information about connection status and servers."""
        # Get current data
        client_conn = self.get_client_details()
        fc_status = self.get_fc_server_status()
        mcp_status = self.get_mcp_server_status()

        # Calculate connection duration if connected
        connection_duration = None
        if self.connection_timestamp:
            duration_seconds = int(time.time() - self.connection_timestamp)
            hours, remainder = divmod(duration_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)

            if hours > 0:
                connection_duration = f"{hours}h {minutes}m {seconds}s"
            elif minutes > 0:
                connection_duration = f"{minutes}m {seconds}s"
            else:
                connection_duration = f"{seconds}s"

        # Create the detailed info dict
        detail_dict = {
            # Client connection information
            "client_connected": self.client_connected,
            "connection_error": self.connection_error,
            "connection_timestamp": self.connection_timestamp,
            "connection_duration": connection_duration,
            "connection_details": self.connection_details,

            # FreeCAD RPC Server information
            "rpc_server_running": fc_status.get("running"),
            "rpc_server_pid": fc_status.get("pid"),
            "rpc_server_type": fc_status.get("type", "rpc"),
            "rpc_server_port": 9875,  # Default RPC XML port

            # MCP Server information
            "mcp_server_running": mcp_status.get("status") in ["running_managed", "running_external"],
            "mcp_server_managed": mcp_status.get("status") == "running_managed",
            "mcp_server_pid": mcp_status.get("pid"),
            "mcp_server_script": self.config_manager.get_mcp_server_script_path(),
            "mcp_server_host": self.config_manager.get_mcp_server_host(),
            "mcp_server_port": self.config_manager.get_mcp_server_port(),
        }

        return detail_dict
