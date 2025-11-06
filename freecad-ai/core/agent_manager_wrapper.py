"""
Agent Manager Initialization Wrapper

This module provides a robust wrapper for agent manager initialization
that handles import failures gracefully.
"""

import logging
import traceback
import sys
import os

class AgentManagerWrapper:
    """Wrapper that provides agent manager functionality with graceful degradation."""
    
    def __init__(self):
        self.agent_manager = None
        self._init_agent_manager()
        
    def _init_agent_manager(self):
        """Initialize the agent manager with comprehensive error handling."""
        try:
            # Skip threading for simplicity and better debugging
            # Import both the AI Manager and the core Agent Manager
            ai_manager = None
            
            # First, try to import and create AIManager
            try:
                addon_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
                ai_dir = os.path.join(addon_dir, "ai")
                if ai_dir not in sys.path:
                    sys.path.insert(0, ai_dir)
                
                # Try different import strategies for AIManager
                try:
                    from agent_manager import AIManager
                except ImportError:
                    try:
                        from ai.agent_manager import AIManager
                    except ImportError:
                        # Last resort - add the specific path and try again
                        sys.path.insert(0, addon_dir)
                        from ai.agent_manager import AIManager
                
                ai_manager = AIManager()
                logging.info("AIManager imported and created from ai/agent_manager.py")
            except Exception as e:
                logging.error(f"Failed to import/create AIManager: {e}")
                logging.debug(traceback.format_exc())
            
            # Then, try to import and create the core AgentManager
            core_agent_manager = None
            try:
                # Try relative import first
                from .agent_manager import AgentManager
                core_agent_manager = AgentManager()
                logging.info("Core AgentManager created successfully (relative import)")
            except (ImportError, ValueError) as e:
                logging.warning(f"Relative import failed: {e}")
                try:
                    # Try absolute import as fallback
                    from agent_manager import AgentManager
                    core_agent_manager = AgentManager()
                    logging.info("Core AgentManager created successfully (absolute import)")
                except ImportError as e2:
                    logging.error(f"Both relative and absolute imports failed: {e2}")
                    core_agent_manager = None
            
            if core_agent_manager:
                self.agent_manager = core_agent_manager
                logging.info("Core AgentManager set as primary agent manager")
                # Connect the AI Manager to the core Agent Manager if available
                if ai_manager and hasattr(self.agent_manager, 'set_ai_provider'):
                    # Use the AI Manager as the AI provider for the core Agent Manager
                    self.agent_manager.set_ai_provider(ai_manager)
                    logging.info("AI Manager connected to core Agent Manager")
            else:
                # Fallback to just the AI Manager if core Agent Manager fails
                if ai_manager:
                    self.agent_manager = ai_manager
                    logging.info("Using AI Manager as fallback")
                else:
                    self.agent_manager = None
                    logging.error("No agent manager could be created")
                    
        except Exception as e:
            logging.error(f"Agent manager initialization failed: {e}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            self.agent_manager = None
    
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
