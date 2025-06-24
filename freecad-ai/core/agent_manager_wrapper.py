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
                # Import both the AI Manager and the core Agent Manager
                ai_manager = None
                
                # First, try to import and create AIManager
                try:
                    addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                    ai_dir = os.path.join(addon_dir, "ai")
                    if ai_dir not in sys.path:
                        sys.path.insert(0, ai_dir)
                    from agent_manager import AIManager
                    ai_manager = AIManager()
                    logging.info("AIManager imported and created from ai/agent_manager.py")
                except Exception as e:
                    logging.error(f"Failed to import/create AIManager: {e}")
                    logging.debug(traceback.format_exc())
                
                # Then, try to import and create the core AgentManager
                try:
                    from .agent_manager import AgentManager
                    self.agent_manager = AgentManager()
                    logging.info("Core AgentManager created successfully")
                    
                    # Connect the AI Manager to the core Agent Manager if available
                    if ai_manager and hasattr(self.agent_manager, 'set_ai_provider'):
                        # Use the AI Manager as the AI provider for the core Agent Manager
                        self.agent_manager.set_ai_provider(ai_manager)
                        logging.info("AI Manager connected to core Agent Manager")
                    
                except Exception as e:
                    logging.error(f"Failed to create core AgentManager: {e}")
                    logging.debug(traceback.format_exc())
                    # Fallback to just the AI Manager if core Agent Manager fails
                    if ai_manager:
                        self.agent_manager = ai_manager
                        logging.info("Using AI Manager as fallback")
                    else:
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
