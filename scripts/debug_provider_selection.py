#!/usr/bin/env python
"""
Diagnostic script to debug provider selection issues in FreeCAD AI.
This script checks the provider service configuration and connections
to help identify issues with provider and model selection.
"""

import os
import sys
import logging
import traceback

# Configure logging
logging.basicConfig(level=logging.DEBUG, 
                   format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("ProviderDebug")

# Ensure the addon directory is in the Python path
script_dir = os.path.dirname(os.path.abspath(__file__))
addon_dir = os.path.dirname(script_dir)
freecad_ai_dir = os.path.join(addon_dir, 'freecad-ai')
if freecad_ai_dir not in sys.path:
    sys.path.insert(0, freecad_ai_dir)
if addon_dir not in sys.path:
    sys.path.insert(0, addon_dir)

try:
    logger.info("Importing provider integration service...")
    from ai.provider_integration_service import get_provider_service
    
    # Get singleton instance
    provider_service = get_provider_service()
    logger.info("Provider service instance obtained")
    
    # Check service initialization
    logger.info(f"Provider service initialized: {hasattr(provider_service, '_initialized')}")
    logger.info(f"Callbacks enabled: {getattr(provider_service, '_callbacks_enabled', False)}")
    
    # Check config manager
    config_manager = getattr(provider_service, 'config_manager', None)
    logger.info(f"Config manager available: {config_manager is not None}")
    if config_manager:
        logger.info(f"Config file loaded: {getattr(config_manager, 'loaded', False)}")
    
    # Check AI manager
    ai_manager = getattr(provider_service, 'ai_manager', None)
    logger.info(f"AI manager available: {ai_manager is not None}")
    if ai_manager:
        providers = getattr(ai_manager, 'providers', {})
        logger.info(f"Registered providers: {list(providers.keys())}")
    
    # Check provider status tracking
    provider_status = getattr(provider_service, 'provider_status', {})
    logger.info(f"Provider status entries: {len(provider_status)}")
    for provider_name, status in provider_status.items():
        logger.info(f"Provider: {provider_name}, Status: {status.get('status', 'unknown')}")
    
    # Check current provider selection
    current_selection = provider_service.get_current_provider_selection()
    logger.info(f"Current provider selection: {current_selection}")
    
    # Test provider models retrieval
    if current_selection['provider']:
        provider_name = current_selection['provider']
        logger.info(f"Getting models for {provider_name}")
        models = provider_service.get_provider_models(provider_name)
        logger.info(f"Available models: {models}")
        
        # Test model update
        if models and current_selection['model'] in models:
            logger.info(f"Testing model update for {provider_name}")
            success = provider_service.update_provider_model(provider_name, current_selection['model'])
            logger.info(f"Model update success: {success}")
        
    # Check callbacks/signals
    logger.info(f"Provider status changed callbacks: {len(getattr(provider_service, 'provider_status_changed_callbacks', []))}")
    logger.info(f"Provider selection changed callbacks: {len(getattr(provider_service, 'provider_selection_changed_callbacks', []))}")
    logger.info(f"Providers updated callbacks: {len(getattr(provider_service, 'providers_updated_callbacks', []))}")
    
    # Test enabling callbacks
    logger.info("Enabling callbacks...")
    provider_service.enable_signals()
    logger.info(f"Callbacks enabled: {getattr(provider_service, '_callbacks_enabled', False)}")
    
    # Refresh providers to trigger callbacks
    logger.info("Refreshing providers...")
    provider_service.refresh_providers()
    
    logger.info("Provider service diagnostic complete")
    
except Exception as e:
    logger.error(f"Error during provider service diagnostic: {e}")
    logger.error(traceback.format_exc())
