from PySide2.QtCore import QObject, Signal
import socket
import os
import platform
import subprocess
import sys
from typing import Optional, Dict, Literal

try:
    import FreeCAD
except ImportError:
    FreeCAD = None

try:
    import psutil
    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

ConnectionType = Literal["internal", "external", "stopped"]

class ConnectionManager(QObject):
    """
    Manages the FreeCAD RPC server connection, unifying detection and control for all connection types.
    Emits status_changed signal on status change.
    """
    status_changed = Signal(dict)

    def __init__(self, host: str = "localhost", port: int = 9875):
        super().__init__()
        self.host = host
        self.port = port
        self._error: Optional[str] = None
        self._last_status: Optional[dict] = None

    def get_status(self) -> Dict[str, object]:
        status = None
        try:
            from rpc_server import rpc_server_thread, rpc_server_instance
            if rpc_server_thread is not None and rpc_server_instance is not None:
                status = {"type": "internal", "running": True, "error": None}
        except Exception:
            pass
        if status is None:
            s = None
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.settimeout(0.5)
                s.connect((self.host, self.port))
                status = {"type": "external", "running": True, "error": None}
            except Exception as e:
                self._error = str(e)
                status = {"type": "stopped", "running": False, "error": self._error}
            finally:
                if s:
                    s.close()
        if status != self._last_status:
            self.status_changed.emit(status)
            self._last_status = status
        return status

    def start(self) -> bool:
        result = False
        try:
            from MCPIndicator.rpc_server import start_rpc_server
            result = start_rpc_server()
        except Exception as e:
            self._error = str(e)
            if FreeCAD:
                FreeCAD.Console.PrintError(f"Error starting RPC server: {e}\n")
        self.get_status()
        return bool(result)

    def stop(self) -> bool:
        result = False
        try:
            from rpc_server import stop_rpc_server
            result = stop_rpc_server()
        except Exception as e:
            self._error = str(e)
            if FreeCAD:
                FreeCAD.Console.PrintError(f"Error stopping RPC server: {e}\n")
        self.get_status()
        return bool(result)

    def restart(self) -> bool:
        stopped = self.stop()
        started = False
        if stopped:
            started = self.start()
        self.get_status()
        return started

    def get_error(self) -> Optional[str]:
        return self._error

    def is_psutil_available(self) -> bool:
        return PSUTIL_AVAILABLE

    def force_stop(self) -> bool:
        killed = False
        if PSUTIL_AVAILABLE and psutil:
            try:
                for proc in psutil.process_iter(['pid', 'name', 'connections']):
                    for conn in proc.connections(kind='inet'):
                        if conn.laddr.port == self.port and conn.status == psutil.CONN_LISTEN:
                            proc.kill()
                            killed = True
                            break
                    if killed:
                        break
            except Exception as e:
                self._error = str(e)
        self.get_status()
        return killed

class MCPConnectionManager(QObject):
    """
    Manages the MCP server process, supporting managed (internal), external, and stopped states.
    Emits status_changed signal on status change.
    """
    status_changed = Signal(dict)

    def __init__(self, host: str = "localhost", port: int = 8000, script_path: Optional[str] = None):
        super().__init__()
        self.host = host
        self.port = port
        self.script_path = script_path
        self._error: Optional[str] = None
        self._process: Optional[subprocess.Popen] = None
        self._last_status: Optional[dict] = None

    def get_status(self) -> Dict[str, object]:
        status = None
        if self._process and self._process.poll() is None:
            status = {"type": "managed", "running": True, "pid": self._process.pid, "error": None}
        else:
            pid = None
            if PSUTIL_AVAILABLE and psutil:
                try:
                    for conn in psutil.net_connections(kind='inet'):
                        if conn.laddr.port == self.port and conn.status == psutil.CONN_LISTEN:
                            pid = conn.pid
                            break
                    if pid:
                        status = {"type": "external", "running": True, "pid": pid, "error": None}
                except Exception as e:
                    self._error = str(e)
            if status is None:
                s = None
                try:
                    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                    s.settimeout(0.5)
                    s.connect((self.host, self.port))
                    status = {"type": "external", "running": True, "pid": None, "error": None}
                except Exception as e:
                    self._error = str(e)
                    status = {"type": "stopped", "running": False, "pid": None, "error": self._error}
                finally:
                    if s:
                        s.close()
        if status != self._last_status:
            self.status_changed.emit(status)
            self._last_status = status
        return status

    def start(self) -> bool:
        result = False
        if not self.script_path or not os.path.exists(self.script_path):
            self._error = "MCP server script path not set or invalid."
        else:
            try:
                python_exe = self._find_python_executable()
                if python_exe:
                    cmd = [python_exe, self.script_path, "--port", str(self.port)]
                    self._process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
                    result = True
            except Exception as e:
                self._error = str(e)
        self.get_status()
        return result

    def stop(self) -> bool:
        result = False
        if self._process and self._process.poll() is None:
            try:
                self._process.terminate()
                self._process.wait(timeout=2.0)
                result = True
            except Exception as e:
                self._error = str(e)
        elif PSUTIL_AVAILABLE and psutil:
            try:
                for proc in psutil.process_iter(['pid', 'name', 'connections']):
                    for conn in proc.connections(kind='inet'):
                        if conn.laddr.port == self.port and conn.status == psutil.CONN_LISTEN:
                            proc.terminate()
                            result = True
                            break
            except Exception as e:
                self._error = str(e)
        self.get_status()
        return result

    def restart(self) -> bool:
        stopped = self.stop()
        started = False
        if stopped:
            started = self.start()
        self.get_status()
        return started

    def get_error(self) -> Optional[str]:
        return self._error

    def is_psutil_available(self) -> bool:
        return PSUTIL_AVAILABLE

    def _find_python_executable(self) -> Optional[str]:
        if platform.system() == "Windows":
            return sys.executable
        else:
            return os.environ.get("PYTHON_EXECUTABLE", sys.executable)

    def force_stop(self) -> bool:
        killed = False
        if PSUTIL_AVAILABLE and psutil:
            try:
                for proc in psutil.process_iter(['pid', 'name', 'connections']):
                    for conn in proc.connections(kind='inet'):
                        if conn.laddr.port == self.port and conn.status == psutil.CONN_LISTEN:
                            proc.kill()
                            killed = True
                            break
                    if killed:
                        break
            except Exception as e:
                self._error = str(e)
        self.get_status()
        return killed
