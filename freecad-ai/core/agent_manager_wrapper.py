"""
Agent Manager Initialization Wrapper

This module provides a robust wrapper for agent manager initialization
that handles import failures gracefully.
"""

import logging
import traceback
import sys
import os
import threading

class AgentManagerWrapper:
    """Wrapper that provides agent manager functionality with graceful degradation."""
    
    def __init__(self):
        self.agent_manager = None
        self._init_agent_manager()
        
    def _init_agent_manager(self):
        """Initialize the agent manager with comprehensive error handling and timeout."""
        def target():
            try:
                agent_manager_imported = False
                # Try to import AIManager from ai/ai_manager.py
                try:
                    addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    ai_dir = os.path.join(addon_dir, "ai")
                    if ai_dir not in sys.path:
                        sys.path.insert(0, ai_dir)
                    from ai_manager import AIManager
                    agent_manager_imported = True
                    logging.info("AIManager imported from ai/ai_manager.py")
                except Exception as e:
                    logging.error(f"Failed to import AIManager: {e}")
                    logging.debug(traceback.format_exc())
                if agent_manager_imported:
                    self.agent_manager = AIManager()
                    logging.info("AIManager instance created successfully")
                else:
                    logging.warning("Could not import AIManager - using fallback")
                    self.agent_manager = None
            except Exception as e:
                logging.error(f"Agent manager initialization failed: {e}")
                logging.error(f"Traceback: {traceback.format_exc()}")
                self.agent_manager = None
        thread = threading.Thread(target=target)
        thread.start()
        thread.join(timeout=10)
        if thread.is_alive():
            logging.error("AgentManager initialization timed out!")
            self.agent_manager = None
            # Optionally, kill the thread (not safe in Python, so just warn)
    
    def get_agent_manager(self):
        """Get the agent manager instance."""
        return self.agent_manager
    
    def is_available(self):
        """Check if agent manager is available."""
        return self.agent_manager is not None

# Global instance
_agent_wrapper = None

def get_agent_manager():
    """Get the global agent manager instance."""
    global _agent_wrapper
    if _agent_wrapper is None:
        _agent_wrapper = AgentManagerWrapper()
    return _agent_wrapper.get_agent_manager()

def is_agent_manager_available():
    """Check if agent manager is available."""
    global _agent_wrapper
    if _agent_wrapper is None:
        _agent_wrapper = AgentManagerWrapper()
    return _agent_wrapper.is_available()
