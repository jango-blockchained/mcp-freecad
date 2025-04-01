import logging
import time
import asyncio
import socket
import json
import os
import sys
import subprocess
from typing import Dict, Any, Optional, Callable, List, Coroutine
from dataclasses import dataclass
from loguru import logger

from .exceptions import ConnectionError

logger = logging.getLogger(__name__)

@dataclass
class RecoveryConfig:
    """Configuration for connection recovery."""
    max_retries: int = 5
    retry_delay: float = 2.0
    backoff_factor: float = 1.5
    max_delay: float = 30.0

class ConnectionRecovery:
    """Handle connection recovery with exponential backoff."""
    
    def __init__(self, config: RecoveryConfig):
        self.config = config
        self.retry_count = 0
        self.current_delay = config.retry_delay
        self.last_error: Optional[Exception] = None
        self.connected = False
        self._connection_callbacks: List[Callable[[bool], None]] = []
        
    def add_connection_callback(self, callback: Callable[[bool], None]) -> None:
        """Add a callback to be called when connection status changes."""
        self._connection_callbacks.append(callback)
        
    def _notify_connection_status(self, connected: bool) -> None:
        """Notify all callbacks of connection status change."""
        for callback in self._connection_callbacks:
            try:
                callback(connected)
            except Exception as e:
                logger.error(f"Error in connection callback: {e}")
                
    async def attempt_recovery(self, operation: Callable) -> Any:
        """
        Attempt to recover from a connection error.
        
        Args:
            operation: The operation to retry
            
        Returns:
            Result of the operation if successful
            
        Raises:
            ConnectionError: If all retry attempts fail
        """
        while self.retry_count < self.config.max_retries:
            try:
                result = await operation()
                self.retry_count = 0
                self.current_delay = self.config.retry_delay
                self.last_error = None
                if not self.connected:
                    self.connected = True
                    self._notify_connection_status(True)
                return result
            except Exception as e:
                self.retry_count += 1
                self.last_error = e
                
                if self.retry_count >= self.config.max_retries:
                    self.connected = False
                    self._notify_connection_status(False)
                    raise ConnectionError(
                        f"Failed to connect after {self.retry_count} attempts",
                        "freecad",
                        {"last_error": str(e)}
                    )
                    
                logger.warning(
                    f"Connection attempt {self.retry_count} failed: {e}. "
                    f"Retrying in {self.current_delay} seconds..."
                )
                
                await asyncio.sleep(self.current_delay)
                self.current_delay = min(
                    self.current_delay * self.config.backoff_factor,
                    self.config.max_delay
                )
                
    def reset(self) -> None:
        """Reset the recovery state."""
        self.retry_count = 0
        self.current_delay = self.config.retry_delay
        self.last_error = None
        
    def get_status(self) -> Dict[str, Any]:
        """Get the current recovery status."""
        return {
            "connected": self.connected,
            "retry_count": self.retry_count,
            "current_delay": self.current_delay,
            "last_error": str(self.last_error) if self.last_error else None,
            "max_retries": self.config.max_retries
        }

class FreeCADClient:
    """Client for communicating with FreeCAD server"""
    
    def __init__(self, host='localhost', port=12345, timeout=10.0):
        """Initialize the client"""
        self.host = host
        self.port = port
        self.timeout = timeout
    
    def send_command(self, command_type, params=None):
        """Send a command to the FreeCAD server"""
        if params is None:
            params = {}
            
        command = {
            "type": command_type,
            "params": params
        }
        
        # Create socket
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.settimeout(self.timeout)
        
        try:
            # Connect to server
            sock.connect((self.host, self.port))
            
            # Send command
            sock.sendall(json.dumps(command).encode())
            
            # Receive response
            response = sock.recv(8192).decode()
            
            # Parse response
            result = json.loads(response)
            
            # Check for errors
            if 'error' in result:
                raise Exception(result['error'])
                
            return result
        except socket.timeout:
            raise Exception(f"Connection timed out after {self.timeout} seconds")
        except ConnectionRefusedError:
            raise Exception(f"Connection refused. Is the FreeCAD server running on {self.host}:{self.port}?")
        except Exception as e:
            raise Exception(f"Error communicating with FreeCAD server: {str(e)}")
        finally:
            sock.close()

class FreeCADConnectionManager:
    """Manage FreeCAD connections with recovery support."""
    
    def __init__(self, config: Dict[str, Any], recovery: ConnectionRecovery):
        self.config = config
        self.recovery = recovery
        self.connection = None
        self._setup_connection_callbacks()
        
    def _setup_connection_callbacks(self) -> None:
        """Setup connection status callbacks."""
        self.recovery.add_connection_callback(self._handle_connection_status)
        
    def _handle_connection_status(self, connected: bool) -> None:
        """Handle connection status changes."""
        if connected:
            logger.info("Successfully connected to FreeCAD")
        else:
            logger.error("Lost connection to FreeCAD")
            
    async def connect(self) -> None:
        """Connect to FreeCAD with recovery support."""
        await self.recovery.attempt_recovery(self._connect_to_freecad)
        
    async def _connect_to_freecad(self) -> None:
        """Internal method to connect to FreeCAD."""
        try:
            import FreeCAD
            self.connection = FreeCAD
            logger.info("Connected to FreeCAD")
        except ImportError as e:
            raise ConnectionError(
                "Failed to import FreeCAD",
                "import",
                {"error": str(e)}
            )
            
    async def disconnect(self) -> None:
        """Disconnect from FreeCAD."""
        self.connection = None
        self.recovery.connected = False
        self.recovery._notify_connection_status(False)
        logger.info("Disconnected from FreeCAD")
        
    @property
    def connected(self) -> bool:
        """Return whether we are currently connected to FreeCAD."""
        return self.connection is not None and self.recovery.connected

    def get_status(self) -> Dict[str, Any]:
        """Get the current connection status."""
        config = self.config
        if isinstance(config, dict):
            config = {
                "max_retries": config.get("max_retries", 5),
                "retry_delay": config.get("retry_delay", 2.0),
                "backoff_factor": config.get("backoff_factor", 1.5),
                "max_delay": config.get("max_delay", 30.0)
            }
        else:
            config = {
                "max_retries": config.max_retries,
                "retry_delay": config.retry_delay,
                "backoff_factor": config.backoff_factor,
                "max_delay": config.max_delay
            }
        
        return {
            "connected": self.connected,
            "recovery_status": self.recovery.get_status(),
            "config": config
        }
        
    async def execute_with_recovery(self, operation: Callable) -> Any:
        """
        Execute an operation with connection recovery.
        
        Args:
            operation: The operation to execute
            
        Returns:
            Result of the operation
            
        Raises:
            ConnectionError: If connection cannot be established
        """
        if not self.connection:
            await self.connect()
            
        return await self.recovery.attempt_recovery(operation) 