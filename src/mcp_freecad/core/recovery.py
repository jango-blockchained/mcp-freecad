import logging
import time
import asyncio
import socket
import json
import os
import sys
import subprocess
from typing import Dict, Any, Optional, Callable, List, Coroutine

logger = logging.getLogger(__name__)

class ConnectionRecovery:
    """
    Connection recovery mechanism for FreeCAD integration.
    
    This class provides functionality to recover from connection
    losses or errors when communicating with FreeCAD.
    """
    
    def __init__(
        self, 
        max_retries: int = 5, 
        retry_delay: float = 2.0,
        backoff_factor: float = 1.5,
        max_delay: float = 30.0
    ):
        """
        Initialize the connection recovery mechanism.
        
        Args:
            max_retries: Maximum number of retry attempts
            retry_delay: Initial delay between retries in seconds
            backoff_factor: Factor by which to increase delay on each retry
            max_delay: Maximum delay between retries in seconds
        """
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.backoff_factor = backoff_factor
        self.max_delay = max_delay
        logger.info(
            f"Initialized connection recovery (max_retries={max_retries}, " 
            f"retry_delay={retry_delay}s, backoff_factor={backoff_factor})"
        )
        
    async def with_retry(
        self, 
        operation: Callable[[], Coroutine[Any, Any, Any]], 
        operation_name: str = "operation",
        custom_max_retries: Optional[int] = None,
        on_failure: Optional[Callable[[Exception, int], Coroutine[Any, Any, Any]]] = None
    ) -> Any:
        """
        Execute an operation with retry logic.
        
        Args:
            operation: Async function to execute
            operation_name: Name of the operation for logging
            custom_max_retries: Optional override for max retries
            on_failure: Optional callback to execute on final failure
            
        Returns:
            The result of the operation
            
        Raises:
            Exception: The last exception encountered if all retries fail
        """
        retries = 0
        max_retries = custom_max_retries if custom_max_retries is not None else self.max_retries
        last_exception = None
        delay = self.retry_delay
        
        while retries <= max_retries:
            try:
                if retries > 0:
                    logger.info(f"Retry {retries}/{max_retries} for {operation_name}")
                return await operation()
            except Exception as e:
                retries += 1
                last_exception = e
                
                if retries <= max_retries:
                    logger.warning(
                        f"Error in {operation_name} (attempt {retries}/{max_retries}): {e}. "
                        f"Retrying in {delay:.1f}s"
                    )
                    await asyncio.sleep(delay)
                    # Increase delay for next retry with exponential backoff
                    delay = min(delay * self.backoff_factor, self.max_delay)
                else:
                    logger.error(f"Failed {operation_name} after {max_retries} retries: {e}")
                    if on_failure:
                        await on_failure(e, retries)
                    raise e
                    
        # This should not be reached, but just in case
        if last_exception:
            raise last_exception
        
        # This should also not be reached
        return None
    
    def with_retry_sync(
        self, 
        operation: Callable[[], Any], 
        operation_name: str = "operation",
        custom_max_retries: Optional[int] = None,
        on_failure: Optional[Callable[[Exception, int], Any]] = None
    ) -> Any:
        """
        Execute a synchronous operation with retry logic.
        
        Args:
            operation: Function to execute
            operation_name: Name of the operation for logging
            custom_max_retries: Optional override for max retries
            on_failure: Optional callback to execute on final failure
            
        Returns:
            The result of the operation
            
        Raises:
            Exception: The last exception encountered if all retries fail
        """
        retries = 0
        max_retries = custom_max_retries if custom_max_retries is not None else self.max_retries
        last_exception = None
        delay = self.retry_delay
        
        while retries <= max_retries:
            try:
                if retries > 0:
                    logger.info(f"Retry {retries}/{max_retries} for {operation_name}")
                return operation()
            except Exception as e:
                retries += 1
                last_exception = e
                
                if retries <= max_retries:
                    logger.warning(
                        f"Error in {operation_name} (attempt {retries}/{max_retries}): {e}. "
                        f"Retrying in {delay:.1f}s"
                    )
                    time.sleep(delay)
                    # Increase delay for next retry with exponential backoff
                    delay = min(delay * self.backoff_factor, self.max_delay)
                else:
                    logger.error(f"Failed {operation_name} after {max_retries} retries: {e}")
                    if on_failure:
                        on_failure(e, retries)
                    raise e
                    
        # This should not be reached, but just in case
        if last_exception:
            raise last_exception
        
        # This should also not be reached
        return None

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
    """
    Manager for FreeCAD connection with recovery capabilities.
    
    This class manages the connection to FreeCAD and provides
    methods to recover from connection failures.
    """
    
    def __init__(self, config: Dict[str, Any], recovery: Optional[ConnectionRecovery] = None):
        """
        Initialize the FreeCAD connection manager.
        
        Args:
            config: Configuration dictionary with FreeCAD settings
            recovery: Optional recovery mechanism, will create one if not provided
        """
        self.config = config
        self.recovery = recovery or ConnectionRecovery()
        self.client = None
        self.freecad_process = None
        self.connected = False
        self.last_connection_attempt = 0
        self.connection_errors: List[Dict[str, Any]] = []
        self.host = 'localhost'
        self.port = 12345
        if 'freecad' in config and 'server_port' in config['freecad']:
            self.port = config['freecad']['server_port']
        logger.info("Initialized FreeCAD connection manager")
        
    async def connect(self, force: bool = False) -> bool:
        """
        Connect to FreeCAD with retry logic.
        
        Args:
            force: Force reconnection even if already connected
            
        Returns:
            True if connected successfully, False otherwise
        """
        if self.connected and not force:
            return True
            
        self.last_connection_attempt = time.time()
        
        try:
            return await self.recovery.with_retry(
                self._connect_impl,
                "FreeCAD connection",
                on_failure=self._on_connection_failure
            )
        except Exception as e:
            logger.error(f"Failed to connect to FreeCAD: {e}")
            return False
            
    async def _connect_impl(self) -> bool:
        """
        Implementation of FreeCAD connection.
        
        Returns:
            True if connected successfully
        
        Raises:
            Exception: If connection fails
        """
        try:
            # Check if FreeCAD server is already running
            try:
                # Create client
                self.client = FreeCADClient(self.host, self.port)
                # Test connection
                result = self.client.send_command("ping")
                if result.get('pong'):
                    logger.info("Connected to existing FreeCAD server")
                    self.connected = True
                    return True
            except Exception:
                # FreeCAD server not running, start it
                pass
                
            # Start FreeCAD server
            freecad_path = self.config.get('freecad', {}).get('path', '/usr/bin/freecad')
            server_script = os.path.join(os.getcwd(), 'freecad_server.py')
            
            if not os.path.exists(server_script):
                raise Exception(f"FreeCAD server script not found: {server_script}")
                
            if not os.path.exists(freecad_path):
                raise Exception(f"FreeCAD executable not found: {freecad_path}")
                
            # Start FreeCAD process
            logger.info(f"Starting FreeCAD server with: {freecad_path} -c {server_script}")
            self.freecad_process = subprocess.Popen(
                [freecad_path, "-c", server_script, self.host, str(self.port)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            
            # Wait for server to start
            logger.info("Waiting for FreeCAD server to start...")
            await asyncio.sleep(5)
            
            # Connect to server
            self.client = FreeCADClient(self.host, self.port)
            
            # Test connection
            result = self.client.send_command("ping")
            if result.get('pong'):
                logger.info("Connected to FreeCAD server successfully")
                self.connected = True
                return True
            else:
                raise Exception("FreeCAD server did not respond with pong")
        except Exception as e:
            logger.warning(f"Failed to connect to FreeCAD server: {e}")
            self.connected = False
            raise e
            
    async def _on_connection_failure(self, exception: Exception, retries: int) -> None:
        """
        Handle connection failure after all retries.
        
        Args:
            exception: The exception that caused the failure
            retries: Number of retries attempted
        """
        self.connection_errors.append({
            "timestamp": time.time(),
            "error": str(exception),
            "retries": retries
        })
        logger.error(f"FreeCAD connection failed after {retries} retries: {exception}")
        
    async def execute_command(self, command_type: str, params: Dict[str, Any] = None, command_name: str = "command") -> Any:
        """
        Execute a command on the FreeCAD server with connection recovery.
        
        Args:
            command_type: Type of command to execute
            params: Parameters for the command
            command_name: Name of the command for logging
            
        Returns:
            Result of the command
            
        Raises:
            Exception: If the command fails after retries
        """
        if not self.connected:
            await self.connect()
            
        async def _execute_command_impl():
            if not self.client:
                raise Exception("FreeCAD client not initialized")
                
            return self.client.send_command(command_type, params)
            
        return await self.recovery.with_retry(
            _execute_command_impl,
            command_name,
            on_failure=lambda e, r: self._on_command_failure(e, r, command_name)
        )
            
    async def _on_command_failure(self, exception: Exception, retries: int, command_name: str) -> None:
        """
        Handle command failure after all retries.
        
        Args:
            exception: The exception that caused the failure
            retries: Number of retries attempted
            command_name: Name of the command
        """
        logger.error(f"FreeCAD command '{command_name}' failed after {retries} retries: {exception}")
        
        # Try to reconnect if we get connection errors
        if "Connection refused" in str(exception) or "Connection timed out" in str(exception):
            logger.info("Attempting to reconnect to FreeCAD server...")
            try:
                await self.connect(force=True)
            except Exception as e:
                logger.error(f"Failed to reconnect: {e}")
        
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get the current connection status.
        
        Returns:
            Dictionary with connection status information
        """
        return {
            "connected": self.connected,
            "last_attempt": self.last_connection_attempt,
            "errors": len(self.connection_errors),
            "server_running": self.freecad_process is not None and self.freecad_process.poll() is None
        } 