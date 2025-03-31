import logging
import time
import asyncio
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
        self.app = None
        self.connected = False
        self.last_connection_attempt = 0
        self.connection_errors: List[Dict[str, Any]] = []
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
            # Add FreeCAD Python path to sys.path if provided
            if 'python_path' in self.config.get('freecad', {}):
                import sys
                freecad_python_path = self.config['freecad']['python_path']
                if freecad_python_path not in sys.path:
                    logger.info(f"Adding FreeCAD Python path: {freecad_python_path}")
                    sys.path.append(freecad_python_path)
            
            import FreeCAD
            self.app = FreeCAD
            self.connected = True
            logger.info("Connected to FreeCAD successfully")
            return True
        except ImportError as e:
            logger.warning(f"Could not import FreeCAD: {e}")
            self.connected = False
            raise e
        except Exception as e:
            logger.error(f"Error connecting to FreeCAD: {e}")
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
        
    async def execute_command(self, command: Callable[[], Any], command_name: str = "command") -> Any:
        """
        Execute a FreeCAD command with connection recovery.
        
        Args:
            command: Function that executes a FreeCAD command
            command_name: Name of the command for logging
            
        Returns:
            Result of the command
            
        Raises:
            Exception: If command execution fails after retries
        """
        if not self.connected:
            await self.connect()
            
        try:
            return await self.recovery.with_retry(
                lambda: self._execute_command_impl(command),
                command_name,
                on_failure=lambda e, r: self._on_command_failure(e, r, command_name)
            )
        except Exception as e:
            logger.error(f"Failed to execute {command_name}: {e}")
            raise e
            
    async def _execute_command_impl(self, command: Callable[[], Any]) -> Any:
        """
        Implementation of command execution.
        
        Args:
            command: Function that executes a FreeCAD command
            
        Returns:
            Result of the command
            
        Raises:
            Exception: If command execution fails
        """
        if not self.connected:
            raise RuntimeError("Not connected to FreeCAD")
            
        try:
            return command()
        except Exception as e:
            logger.error(f"Error executing FreeCAD command: {e}")
            # Check if it's a connection issue
            if "connection" in str(e).lower() or "not connected" in str(e).lower():
                self.connected = False
                await self.connect(force=True)
            raise e
            
    async def _on_command_failure(self, exception: Exception, retries: int, command_name: str) -> None:
        """
        Handle command execution failure after all retries.
        
        Args:
            exception: The exception that caused the failure
            retries: Number of retries attempted
            command_name: Name of the command that failed
        """
        logger.error(f"FreeCAD command '{command_name}' failed after {retries} retries: {exception}")
        # If we suspect a connection issue, try to reconnect
        if "connection" in str(exception).lower() or "not connected" in str(exception).lower():
            logger.info("Attempting to reconnect to FreeCAD after command failure")
            self.connected = False
            await self.connect(force=True)
            
    def get_connection_status(self) -> Dict[str, Any]:
        """
        Get the status of the FreeCAD connection.
        
        Returns:
            Dictionary with connection status information
        """
        return {
            "connected": self.connected,
            "last_connection_attempt": self.last_connection_attempt,
            "time_since_last_attempt": time.time() - self.last_connection_attempt if self.last_connection_attempt > 0 else None,
            "connection_errors": self.connection_errors[-5:] if self.connection_errors else []
        } 