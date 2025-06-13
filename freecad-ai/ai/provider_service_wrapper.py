"""
Provider Service Initialization Wrapper

This module provides a robust wrapper for provider service initialization
that handles import failures gracefully.
"""

import logging
import traceback

class ProviderServiceWrapper:
    """Wrapper that provides provider service functionality with graceful degradation."""
    
    def __init__(self):
        self.provider_service = None
        self._init_provider_service()
        
    def _init_provider_service(self):
        """Initialize the provider service with comprehensive error handling."""
        try:
            # Try multiple import strategies
            provider_service_imported = False
            
            # Strategy 1: Relative import
            try:
                from .provider_integration_service import get_provider_service
                provider_service_imported = True
                logging.info("Provider service imported via relative path")
            except ImportError as e:
                logging.debug(f"Relative import failed: {e}")
            
            # Strategy 2: Direct import
            if not provider_service_imported:
                try:
                    from provider_integration_service import get_provider_service
                    provider_service_imported = True
                    logging.info("Provider service imported via direct path")
                except ImportError as e:
                    logging.debug(f"Direct import failed: {e}")
            
            # Strategy 3: Absolute import
            if not provider_service_imported:
                try:
                    import sys
                    import os
                    
                    # Add ai directory to path
                    ai_dir = os.path.dirname(__file__)
                    if ai_dir not in sys.path:
                        sys.path.insert(0, ai_dir)
                    
                    from provider_integration_service import get_provider_service
                    provider_service_imported = True
                    logging.info("Provider service imported after path modification")
                except ImportError as e:
                    logging.debug(f"Path modification import failed: {e}")
            
            if provider_service_imported:
                self.provider_service = get_provider_service()
                logging.info("Provider service instance created successfully")
            else:
                logging.warning("Could not import provider service - using fallback")
                self.provider_service = None
                
        except Exception as e:
            logging.error(f"Provider service initialization failed: {e}")
            logging.error(f"Traceback: {traceback.format_exc()}")
            self.provider_service = None
    
    def get_provider_service(self):
        """Get the provider service instance."""
        return self.provider_service
    
    def is_available(self):
        """Check if provider service is available."""
        return self.provider_service is not None

# Global instance
_provider_wrapper = None

def get_provider_service():
    """Get the global provider service instance."""
    global _provider_wrapper
    if _provider_wrapper is None:
        _provider_wrapper = ProviderServiceWrapper()
    return _provider_wrapper.get_provider_service()

def is_provider_service_available():
    """Check if provider service is available."""
    global _provider_wrapper
    if _provider_wrapper is None:
        _provider_wrapper = ProviderServiceWrapper()
    return _provider_wrapper.is_available()
