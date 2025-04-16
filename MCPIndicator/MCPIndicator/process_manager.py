import os
import sys
import subprocess
import signal
import time
import platform
import shlex
import threading
import FreeCAD
import psutil

class ProcessManager:
    """Manages server processes for the MCP Indicator Workbench."""

    def __init__(self, config_manager, path_finder):
        """Initialize the ProcessManager with configuration and path utility."""
        self.config = config_manager
        self.path_finder = path_finder
        self.freecad_server_process = None
        self.mcp_server_process = None

    def is_freecad_server_running(self):
        """Check if the FreeCAD server process is running."""
        if self.freecad_server_process:
            # First, check our spawned process
            try:
                if platform.system() == "Windows":
                    # On Windows, poll() returns None if the process is running
                    return self.freecad_server_process.poll() is None
                else:
                    # On Unix, we can send signal 0 to test if process exists
                    os.kill(self.freecad_server_process.pid, 0)
                    return True
            except (OSError, AttributeError):
                # Process is not running
                self.freecad_server_process = None

        # Next, try to detect server by port
        if platform.system() == "Windows":
            try:
                # Use netstat on Windows
                cmd = ["netstat", "-ano"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                for line in result.stdout.splitlines():
                    if "0.0.0.0:5050" in line or "127.0.0.1:5050" in line:
                        return True
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"Error checking netstat for FreeCAD server: {str(e)}\n")
        else:
            try:
                # Use lsof on Unix-like systems
                cmd = ["lsof", "-i", ":5050"]
                result = subprocess.run(cmd, capture_output=True)
                return result.returncode == 0
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"Error checking lsof for FreeCAD server: {str(e)}\n")

        # As a fallback, try a quick socket connection
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect(("localhost", 5050))
            s.close()
            return True
        except:
            return False

    def is_mcp_server_running(self):
        """Check if the MCP server process is running."""
        if self.mcp_server_process:
            # First, check our spawned process
            try:
                if platform.system() == "Windows":
                    # On Windows, poll() returns None if the process is running
                    return self.mcp_server_process.poll() is None
                else:
                    # On Unix, we can send signal 0 to test if process exists
                    os.kill(self.mcp_server_process.pid, 0)
                    return True
            except (OSError, AttributeError):
                # Process is not running
                self.mcp_server_process = None

        # Next, try to detect server by port
        port = self.config.get_mcp_server_port()

        if platform.system() == "Windows":
            try:
                # Use netstat on Windows
                cmd = ["netstat", "-ano"]
                result = subprocess.run(cmd, capture_output=True, text=True)
                for line in result.stdout.splitlines():
                    if f"0.0.0.0:{port}" in line or f"127.0.0.1:{port}" in line:
                        return True
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"Error checking netstat for MCP server: {str(e)}\n")
        else:
            try:
                # Use lsof on Unix-like systems
                cmd = ["lsof", "-i", f":{port}"]
                result = subprocess.run(cmd, capture_output=True)
                return result.returncode == 0
            except Exception as e:
                FreeCAD.Console.PrintWarning(f"Error checking lsof for MCP server: {str(e)}\n")

        # As a fallback, try a quick socket connection
        import socket
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            s.settimeout(0.5)
            s.connect((self.config.get_mcp_server_host(), port))
            s.close()
            return True
        except:
            return False

    def start_freecad_server(self, connect_mode=False):
        """Start the FreeCAD server (legacy socket server)."""
        if self.is_freecad_server_running():
            FreeCAD.Console.PrintMessage("FreeCAD server is already running.\n")
            return True

        server_script_path = self.config.get_server_script_path()
        if not server_script_path or not os.path.exists(server_script_path):
            FreeCAD.Console.PrintError("FreeCAD server script path not set or invalid.\n")
            return False

        # Determine Python executable
        python_exe = self.path_finder.get_python_executable()
        if not python_exe:
            FreeCAD.Console.PrintError("Could not find Python executable.\n")
            return False

        # Prepare command arguments
        cmd = [python_exe, server_script_path]

        # Add --connect flag if needed
        if connect_mode:
            cmd.append("--connect")

        # Run server in background
        try:
            FreeCAD.Console.PrintMessage(f"Starting FreeCAD server: {' '.join(cmd)}\n")

            # Set up process with appropriate flags for the platform
            if platform.system() == "Windows":
                # On Windows, use CREATE_NEW_PROCESS_GROUP to allow Ctrl+C handling separately
                self.freecad_server_process = subprocess.Popen(
                    cmd,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            else:
                # On Unix-like systems, start a new process group
                self.freecad_server_process = subprocess.Popen(
                    cmd,
                    preexec_fn=os.setsid,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

            # Start a thread to monitor the process output
            threading.Thread(
                target=self._monitor_process_output,
                args=(self.freecad_server_process, "FreeCAD Server"),
                daemon=True,
            ).start()

            # Wait briefly to check for immediate failure
            time.sleep(0.5)
            if self.is_freecad_server_running():
                FreeCAD.Console.PrintMessage("FreeCAD server started successfully.\n")
                return True
            else:
                # Check for startup errors
                if self.freecad_server_process:
                    # Process exists but not responding, get output so far
                    stderr_output = self.freecad_server_process.stderr.read(1024)  # Read first 1KB
                    if stderr_output:
                        FreeCAD.Console.PrintError(f"FreeCAD server failed to start:\n{stderr_output}\n")
                    return False
                else:
                    FreeCAD.Console.PrintError("FreeCAD server process failed to start.\n")
                    return False

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error starting FreeCAD server: {str(e)}\n")
            return False

    def stop_freecad_server(self):
        """Stop the FreeCAD server process."""
        if not self.is_freecad_server_running():
            FreeCAD.Console.PrintMessage("FreeCAD server is not running.\n")
            return True

        try:
            # First try gentle shutdown through our stored process
            if self.freecad_server_process:
                FreeCAD.Console.PrintMessage("Stopping FreeCAD server process...\n")
                self._stop_process(self.freecad_server_process)
                self.freecad_server_process = None

            # Check if server is still running and try more forceful methods if needed
            if self.is_freecad_server_running():
                FreeCAD.Console.PrintWarning("FreeCAD server still running, searching for process...\n")
                self._stop_server_by_port(5050, "FreeCAD")

            # Final check
            if self.is_freecad_server_running():
                FreeCAD.Console.PrintError("Failed to stop FreeCAD server completely.\n")
                return False
            else:
                FreeCAD.Console.PrintMessage("FreeCAD server stopped successfully.\n")
                return True

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error stopping FreeCAD server: {str(e)}\n")
            return False

    def restart_freecad_server(self):
        """Restart the FreeCAD server."""
        FreeCAD.Console.PrintMessage("Restarting FreeCAD server...\n")
        self.stop_freecad_server()
        time.sleep(1)  # Wait a moment for ports to be freed
        return self.start_freecad_server()

    def start_mcp_server(self):
        """Start the MCP server process."""
        if self.is_mcp_server_running():
            FreeCAD.Console.PrintMessage("MCP server is already running.\n")
            return True

        mcp_script_path = self.config.get_mcp_server_script_path()
        if not mcp_script_path or not os.path.exists(mcp_script_path):
            FreeCAD.Console.PrintError("MCP server script path not set or invalid.\n")
            return False

        # Prepare environment variables
        env = os.environ.copy()

        # Prepare command based on script type
        is_shell_script = mcp_script_path.endswith(".sh") or mcp_script_path.endswith(".bash")

        if is_shell_script:
            if platform.system() == "Windows":
                FreeCAD.Console.PrintError("Shell scripts not supported on Windows.\n")
                return False

            # Use shell script directly
            cmd = [mcp_script_path]

            # Add config file if specified
            config_path = self.config.get_mcp_server_config()
            if config_path and os.path.exists(config_path):
                cmd.append("--config")
                cmd.append(config_path)

            # Add port if not default
            port = self.config.get_mcp_server_port()
            if port != 8000:
                cmd.append("--port")
                cmd.append(str(port))

        else:
            # It's a Python script, use Python to execute it
            python_exe = self.path_finder.get_python_executable()
            if not python_exe:
                FreeCAD.Console.PrintError("Could not find Python executable.\n")
                return False

            cmd = [python_exe, mcp_script_path]

            # Add always-useful debug
            cmd.append("--debug")

            # Add config file if specified
            config_path = self.config.get_mcp_server_config()
            if config_path and os.path.exists(config_path):
                cmd.append("--config")
                cmd.append(config_path)

            # Add port if not default
            port = self.config.get_mcp_server_port()
            if port != 8000:
                cmd.append("--port")
                cmd.append(str(port))

        # Start the server process
        try:
            FreeCAD.Console.PrintMessage(f"Starting MCP server: {' '.join(cmd)}\n")

            if platform.system() == "Windows":
                self.mcp_server_process = subprocess.Popen(
                    cmd,
                    env=env,
                    creationflags=subprocess.CREATE_NEW_PROCESS_GROUP,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )
            else:
                self.mcp_server_process = subprocess.Popen(
                    cmd,
                    env=env,
                    preexec_fn=os.setsid,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    text=True,
                )

            # Start a thread to monitor the process output
            threading.Thread(
                target=self._monitor_process_output,
                args=(self.mcp_server_process, "MCP Server"),
                daemon=True,
            ).start()

            # Wait briefly to check for immediate failure
            time.sleep(1.0)
            if self.is_mcp_server_running():
                FreeCAD.Console.PrintMessage("MCP server started successfully.\n")
                return True
            else:
                # Check for startup errors
                if self.mcp_server_process:
                    stderr_output = self.mcp_server_process.stderr.read(1024)  # Read first 1KB
                    if stderr_output:
                        FreeCAD.Console.PrintError(f"MCP server failed to start:\n{stderr_output}\n")
                    return False
                else:
                    FreeCAD.Console.PrintError("MCP server process failed to start.\n")
                    return False

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error starting MCP server: {str(e)}\n")
            return False

    def stop_mcp_server(self):
        """Stop the MCP server process."""
        if not self.is_mcp_server_running():
            FreeCAD.Console.PrintMessage("MCP server is not running.\n")
            return True

        try:
            # First try gentle shutdown through our stored process
            if self.mcp_server_process:
                FreeCAD.Console.PrintMessage("Stopping MCP server process...\n")
                self._stop_process(self.mcp_server_process)
                self.mcp_server_process = None

            # Check if server is still running and try more forceful methods if needed
            if self.is_mcp_server_running():
                FreeCAD.Console.PrintWarning("MCP server still running, searching for process...\n")
                self._stop_server_by_port(self.config.get_mcp_server_port(), "MCP")

            # Final check
            if self.is_mcp_server_running():
                FreeCAD.Console.PrintError("Failed to stop MCP server completely.\n")
                return False
            else:
                FreeCAD.Console.PrintMessage("MCP server stopped successfully.\n")
                return True

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error stopping MCP server: {str(e)}\n")
            return False

    def restart_mcp_server(self):
        """Restart the MCP server."""
        FreeCAD.Console.PrintMessage("Restarting MCP server...\n")
        self.stop_mcp_server()
        time.sleep(1)  # Wait a moment for ports to be freed
        return self.start_mcp_server()

    def _stop_process(self, process_or_pid):
        """Stop a process, handling platform-specific details."""
        if not process_or_pid:
            return

        pid = process_or_pid.pid if hasattr(process_or_pid, "pid") else process_or_pid

        try:
            # First try to get a psutil Process object
            if psutil:
                try:
                    p = psutil.Process(pid)
                    # Try to terminate the process and its children
                    for child in p.children(recursive=True):
                        try:
                            child.terminate()
                        except:
                            pass
                    p.terminate()

                    # Wait a bit and check if it's still alive
                    time.sleep(0.5)
                    if p.is_running():
                        # If still running, try to kill it
                        for child in p.children(recursive=True):
                            try:
                                child.kill()
                            except:
                                pass
                        p.kill()
                    return
                except psutil.NoSuchProcess:
                    # Process already gone
                    return
                except Exception as e:
                    FreeCAD.Console.PrintWarning(f"psutil approach failed: {str(e)}\n")
                    # Fall through to OS-specific method

            # OS-specific approaches
            if platform.system() == "Windows":
                # Windows - use taskkill
                try:
                    subprocess.run(["taskkill", "/F", "/T", "/PID", str(pid)], check=False)
                except:
                    pass

                # If it's a subprocess.Popen object, also try its terminate method
                if hasattr(process_or_pid, "terminate"):
                    try:
                        process_or_pid.terminate()
                    except:
                        pass
            else:
                # Unix-like system - send signals
                if hasattr(process_or_pid, "terminate"):
                    # It's a subprocess.Popen object
                    try:
                        # Try SIGTERM first for graceful shutdown
                        process_or_pid.terminate()
                        time.sleep(0.5)

                        # If still running, try SIGKILL
                        if process_or_pid.poll() is None:
                            process_or_pid.kill()
                    except:
                        pass
                else:
                    # Just have the PID
                    try:
                        # Try to send SIGTERM to the process group
                        os.killpg(pid, signal.SIGTERM)
                        time.sleep(0.5)

                        # If still running, try SIGKILL
                        try:
                            os.kill(pid, 0)  # Test if process exists
                            os.killpg(pid, signal.SIGKILL)
                        except OSError:
                            pass  # Process already terminated
                    except:
                        # Fall back to direct signals to the process
                        try:
                            os.kill(pid, signal.SIGTERM)
                            time.sleep(0.5)
                            try:
                                os.kill(pid, 0)  # Test if process exists
                                os.kill(pid, signal.SIGKILL)
                            except OSError:
                                pass  # Process already terminated
                        except:
                            pass

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error stopping process {pid}: {str(e)}\n")

    def _stop_server_by_port(self, port, server_name):
        """Stop a server process identified by its port."""
        try:
            for process in self._find_processes_by_port(port):
                FreeCAD.Console.PrintMessage(f"Found {server_name} server process on port {port}: PID {process['pid']}\n")

                # Try to stop the process
                if self._stop_process(process["pid"]):
                    FreeCAD.Console.PrintMessage(f"Stopped {server_name} server process with PID {process['pid']}\n")
                    # Check if server is still running
                    if server_name == "FreeCAD" and not self.is_freecad_server_running():
                        return True
                    elif server_name == "MCP" and not self.is_mcp_server_running():
                        return True
                else:
                    FreeCAD.Console.PrintWarning(f"Failed to stop {server_name} server process with PID {process['pid']}\n")

            # If we get here, we couldn't stop all processes
            return False

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error finding/stopping {server_name} server: {str(e)}\n")
            return False

    def _find_processes_by_port(self, port):
        """Find processes using a specific port."""
        processes = []

        try:
            # Try using psutil if available (cross-platform)
            import psutil
            for conn in psutil.net_connections(kind='inet'):
                if conn.laddr.port == port:
                    try:
                        proc = psutil.Process(conn.pid)
                        processes.append({
                            'pid': conn.pid,
                            'name': proc.name(),
                            'cmd': ' '.join(proc.cmdline())
                        })
                    except (psutil.NoSuchProcess, psutil.AccessDenied):
                        # Process might have terminated
                        processes.append({'pid': conn.pid, 'name': 'Unknown', 'cmd': 'Unknown'})
            return processes

        except (ImportError, AttributeError):
            # psutil not available or doesn't have this feature, use platform-specific approaches
            pass

        # Platform-specific fallbacks
        if platform.system() == "Windows":
            try:
                # Use netstat on Windows
                output = subprocess.check_output(["netstat", "-ano"], text=True)
                for line in output.splitlines():
                    if f":{port}" in line:
                        parts = line.strip().split()
                        if len(parts) >= 5:
                            pid = int(parts[-1])
                            try:
                                process_info = subprocess.check_output(["tasklist", "/FI", f"PID eq {pid}"], text=True)
                                name = "Unknown"
                                for pline in process_info.splitlines():
                                    if str(pid) in pline:
                                        parts = pline.split()
                                        if len(parts) > 0:
                                            name = parts[0]
                                            break
                                processes.append({'pid': pid, 'name': name, 'cmd': 'Unknown'})
                            except:
                                processes.append({'pid': pid, 'name': 'Unknown', 'cmd': 'Unknown'})
            except:
                pass
        else:
            try:
                # Use lsof on Unix-like systems
                output = subprocess.check_output(["lsof", "-i", f":{port}"], text=True)
                for line in output.splitlines()[1:]:  # Skip header
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        name = parts[0]
                        pid = int(parts[1])
                        processes.append({'pid': pid, 'name': name, 'cmd': 'Unknown'})
            except:
                pass

        return processes

    def _monitor_process_output(self, process, process_name):
        """Monitor and log the output of a subprocess."""
        try:
            while process and process.poll() is None:
                # Read and log stdout
                stdout_line = process.stdout.readline()
                if stdout_line:
                    FreeCAD.Console.PrintMessage(f"{process_name}: {stdout_line.strip()}\n")

                # Read and log stderr
                stderr_line = process.stderr.readline()
                if stderr_line:
                    FreeCAD.Console.PrintError(f"{process_name} Error: {stderr_line.strip()}\n")

                # Avoid busy-waiting if no output
                if not stdout_line and not stderr_line:
                    time.sleep(0.1)

            # Process exited - log any remaining output
            if process:
                remaining_stdout, remaining_stderr = process.communicate()
                if remaining_stdout:
                    for line in remaining_stdout.splitlines():
                        FreeCAD.Console.PrintMessage(f"{process_name}: {line.strip()}\n")
                if remaining_stderr:
                    for line in remaining_stderr.splitlines():
                        FreeCAD.Console.PrintError(f"{process_name} Error: {line.strip()}\n")

            FreeCAD.Console.PrintMessage(f"{process_name} process has terminated.\n")

        except Exception as e:
            FreeCAD.Console.PrintError(f"Error monitoring {process_name} output: {str(e)}\n")
