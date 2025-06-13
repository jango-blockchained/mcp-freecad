"""
Agent Manager Initialization Wrapper

This module provides a robust wrapper for agent manager initialization
that handles import failures gracefully.
"""

import logging
import traceback

class AgentManagerWrapper:
    """Wrapper that provides agent manager functionality with graceful degradation."""
    
    def __init__(self):
        self.agent_manager = None
        self._init_agent_manager()
        
    def _init_agent_manager(self):
        """Initialize the agent manager with comprehensive error handling."""
        try:
            # Try multiple import strategies
            agent_manager_imported = False
            
            # Strategy 1: Relative import
            try:
                from .agent_manager import AgentManager
                agent_manager_imported = True
                logging.info("AgentManager imported via relative path")
            except ImportError as e:
                logging.debug(f"Relative import failed: {e}")
            
            # Strategy 2: Direct import
            if not agent_manager_imported:
                try:
                    from agent_manager import AgentManager
                    agent_manager_imported = True
                    logging.info("AgentManager imported via direct path")
                except ImportError as e:
                    logging.debug(f"Direct import failed: {e}")
            
            # Strategy 3: Absolute import
            if not agent_manager_imported:
                try:
                    import sys
                    import os
                    
                    # Add core directory to path
                    core_dir = os.path.dirname(__file__)
                    if core_dir not in sys.path:
                        sys.path.insert(0, core_dir)
                    
                    from agent_manager import AgentManager
                    agent_manager_imported = True
                    logging.info("AgentManager imported after path modification")
                except ImportError as e:
                    logging.debug(f"Path modification import failed: {e}")
            
            if agent_manager_imported:
                self.agent_manager = AgentManager()
                logging.info("AgentManager instance created successfully")
            else:
                logging.warning("Could not import AgentManager - using fallback")
                self.agent_manager = None
                
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
