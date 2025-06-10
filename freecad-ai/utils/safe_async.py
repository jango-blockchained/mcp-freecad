"""
Safe async utilities for FreeCAD AI addon.

This module provides utilities for safely handling async operations in synchronous contexts,
particularly when dealing with FreeCAD signal handlers that need to emit async events.
"""

import asyncio
import logging
import threading
from typing import Any, Callable, Coroutine, Optional
import concurrent.futures

logger = logging.getLogger(__name__)


def safe_create_task(coro: Coroutine[Any, Any, Any], task_name: Optional[str] = None) -> bool:
    """
    Safely create an async task, handling cases where no event loop is running.
    
    Args:
        coro: The coroutine to run
        task_name: Optional name for the task (for debugging)
        
    Returns:
        bool: True if task was created successfully, False otherwise
    """
    try:
        # Try to get the current event loop
        loop = asyncio.get_running_loop()
        
        # If we have a loop, create the task normally
        task = loop.create_task(coro)
        if task_name:
            task.set_name(task_name)
        logger.debug(f"Successfully created async task: {task_name or 'unnamed'}")
        return True
        
    except RuntimeError:
        # No event loop is running
        logger.debug(f"No event loop running for task: {task_name or 'unnamed'}")
        
        # Try to run in a thread pool as a fallback
        try:
            # Check if we're in the main thread
            if threading.current_thread() is threading.main_thread():
                logger.debug("In main thread, attempting thread pool execution")
                return _run_in_thread_pool(coro, task_name)
            else:
                logger.debug("Not in main thread, skipping async operation")
                return False
                
        except Exception as e:
            logger.warning(f"Failed to run task {task_name or 'unnamed'} in thread pool: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Unexpected error creating task {task_name or 'unnamed'}: {e}")
        return False


def _run_in_thread_pool(coro: Coroutine[Any, Any, Any], task_name: Optional[str] = None) -> bool:
    """
    Run a coroutine in a thread pool using asyncio.run().
    
    Args:
        coro: The coroutine to run
        task_name: Optional name for the task (for debugging)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        def run_async_in_thread():
            """Run the coroutine in a new event loop."""
            try:
                asyncio.run(coro)
                logger.debug(f"Successfully completed task in thread pool: {task_name or 'unnamed'}")
            except Exception as e:
                logger.error(f"Error running task {task_name or 'unnamed'} in thread pool: {e}")
                
        # Use ThreadPoolExecutor to run the async function
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
            executor.submit(run_async_in_thread)
            # Don't wait for completion - run in background
            logger.debug(f"Submitted task {task_name or 'unnamed'} to thread pool")
            return True
            
    except Exception as e:
        logger.error(f"Failed to submit task {task_name or 'unnamed'} to thread pool: {e}")
        return False


def safe_emit_event(emit_func: Callable, event_type: str, event_data: Any, context: str = "unknown") -> bool:
    """
    Safely emit an event using an async emit function.
    
    Args:
        emit_func: The async emit function (e.g., self.emit_event)
        event_type: Type of event to emit
        event_data: Event data
        context: Context description for logging
        
    Returns:
        bool: True if event was emitted successfully, False otherwise
    """
    try:
        # Create the coroutine
        coro = emit_func(event_type, event_data)
        
        # Use safe_create_task to handle it
        task_name = f"{context}_{event_type}"
        return safe_create_task(coro, task_name)
        
    except Exception as e:
        logger.error(f"Error emitting event {event_type} in context {context}: {e}")
        return False


def check_event_loop_status() -> dict:
    """
    Check the status of the current event loop for debugging.
    
    Returns:
        dict: Information about the event loop status
    """
    status = {
        "has_running_loop": False,
        "is_main_thread": threading.current_thread() is threading.main_thread(),
        "thread_name": threading.current_thread().name,
        "error": None
    }
    
    try:
        loop = asyncio.get_running_loop()
        status["has_running_loop"] = True
        status["loop_running"] = loop.is_running()
        status["loop_closed"] = loop.is_closed()
    except RuntimeError as e:
        status["error"] = str(e)
    except Exception as e:
        status["error"] = f"Unexpected error: {e}"
        
    return status


# Convenience function for FreeCAD signal handlers
def freecad_safe_emit(emit_func: Callable, event_type: str, event_data: Any, signal_name: str = "unknown") -> None:
    """
    Convenience function specifically for FreeCAD signal handlers.
    
    Args:
        emit_func: The async emit function (e.g., self.emit_event)
        event_type: Type of event to emit
        event_data: Event data
        signal_name: Name of the FreeCAD signal that triggered this
    """
    success = safe_emit_event(emit_func, event_type, event_data, f"freecad_signal_{signal_name}")
    
    if not success:
        logger.warning(f"Failed to emit {event_type} event from FreeCAD signal {signal_name}")
        # Log event loop status for debugging
        status = check_event_loop_status()
        logger.debug(f"Event loop status: {status}")
