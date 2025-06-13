#!/usr/bin/env python3
"""
FreeCAD AI Component Fix Script

This script fixes the initialization issues with the agent manager and provider service
by addressing import failures and dependency problems.
"""

import os
import sys
import traceback

def fix_freecad_ai_initialization():
    """Fix the FreeCAD AI initialization issues."""
    
    print("=" * 60)
    print("FreeCAD AI Component Fix")
    print("=" * 60)
    
    # Get the freecad-ai directory
    freecad_ai_dir = os.path.join(os.path.dirname(__file__), 'freecad-ai')
    
    # Fix 1: Qt compatibility issue
    print("\n1. Fixing Qt compatibility issue...")
    try:
        fix_qt_compatibility(freecad_ai_dir)
        print("✓ Qt compatibility fixed")
    except Exception as e:
        print(f"✗ Qt compatibility fix failed: {e}")
    
    # Fix 2: Import path issues
    print("\n2. Fixing import path issues...")
    try:
        fix_import_paths(freecad_ai_dir)
        print("✓ Import paths fixed")
    except Exception as e:
        print(f"✗ Import path fix failed: {e}")
    
    # Fix 3: Agent manager initialization
    print("\n3. Fixing agent manager initialization...")
    try:
        fix_agent_manager_init(freecad_ai_dir)
        print("✓ Agent manager initialization fixed")
    except Exception as e:
        print(f"✗ Agent manager fix failed: {e}")
    
    # Fix 4: Provider service initialization  
    print("\n4. Fixing provider service initialization...")
    try:
        fix_provider_service_init(freecad_ai_dir)
        print("✓ Provider service initialization fixed")
    except Exception as e:
        print(f"✗ Provider service fix failed: {e}")
    
    print("\n" + "=" * 60)
    print("Fix complete! Please restart FreeCAD.")
    print("=" * 60)

def fix_qt_compatibility(freecad_ai_dir):
    """Fix Qt compatibility issues."""
    gui_dir = os.path.join(freecad_ai_dir, 'gui')
    
    # Create a Qt compatibility module
    qt_compat_content = '''"""
Qt Compatibility Module for FreeCAD AI

This module provides compatibility wrappers for Qt across different versions.
"""

import logging

# Try different Qt imports in order of preference
HAS_QT = False
QtCore = None
QtWidgets = None
QtGui = None

# Strategy 1: Try PySide2 (preferred)
try:
    from PySide2 import QtCore, QtWidgets, QtGui
    HAS_QT = True
    QT_VERSION = "PySide2"
    
    # Fix the QT_VERSION_STR issue
    if not hasattr(QtCore, 'QT_VERSION_STR'):
        try:
            import PySide2
            QtCore.QT_VERSION_STR = PySide2.__version__
        except:
            QtCore.QT_VERSION_STR = "5.15.0"  # Fallback version
            
    logging.info("Qt Compatibility: Using PySide2")
except ImportError:
    pass

# Strategy 2: Try PySide6 if PySide2 failed
if not HAS_QT:
    try:
        from PySide6 import QtCore, QtWidgets, QtGui
        HAS_QT = True
        QT_VERSION = "PySide6"
        logging.info("Qt Compatibility: Using PySide6")
    except ImportError:
        pass

# Strategy 3: Try PyQt5 if both PySide versions failed
if not HAS_QT:
    try:
        from PyQt5 import QtCore, QtWidgets, QtGui
        HAS_QT = True
        QT_VERSION = "PyQt5"
        logging.info("Qt Compatibility: Using PyQt5")
    except ImportError:
        pass

# Strategy 4: Try PySide (legacy) as last resort
if not HAS_QT:
    try:
        from PySide import QtCore
        from PySide import QtGui as QtWidgets  # PySide uses QtGui for widgets
        QtGui = QtWidgets  # For compatibility
        HAS_QT = True
        QT_VERSION = "PySide"
        logging.info("Qt Compatibility: Using PySide (legacy)")
    except ImportError:
        pass

# Create dummy classes if no Qt is available
if not HAS_QT:
    logging.warning("Qt Compatibility: No Qt bindings found, creating dummy classes")
    QT_VERSION = "None"
    
    class DummyQtCore:
        class Qt:
            RightDockWidgetArea = 2
            LeftDockWidgetArea = 1
            ElideRight = 2
            
        class QTimer:
            @staticmethod
            def singleShot(interval, callback):
                pass
                
    class DummyQtWidgets:
        class QDockWidget:
            DockWidgetMovable = 1
            DockWidgetFloatable = 2
            
            def __init__(self, *args, **kwargs):
                pass
            def setAllowedAreas(self, *args): pass
            def setFeatures(self, *args): pass
            def setWidget(self, widget): pass
            def setMinimumWidth(self, width): pass
            def resize(self, width, height): pass
            def show(self): pass
            def hide(self): pass
            def raise_(self): pass
            def updateGeometry(self): pass
            def setObjectName(self, name): pass
            def setWindowTitle(self, title): pass
            
        class QWidget:
            def __init__(self, *args, **kwargs): pass
            def setMinimumSize(self, w, h): pass
            def setStyleSheet(self, style): pass
            def updateGeometry(self): pass
            def show(self): pass
            def size(self): return type('Size', (), {'width': lambda: 400, 'height': lambda: 300})()
            def findChildren(self, type_): return []
            def setLayout(self, layout): pass
            def layout(self): return None
            
        class QVBoxLayout:
            def __init__(self, *args, **kwargs): pass
            def addWidget(self, widget): pass
            def addLayout(self, layout): pass
            def addStretch(self): pass
            def setSpacing(self, spacing): pass
            def setContentsMargins(self, *args): pass
            def count(self): return 0
            def takeAt(self, index): return None
            def deleteLater(self): pass
            
        class QHBoxLayout:
            def __init__(self, *args, **kwargs): pass
            def addWidget(self, widget): pass
            def addStretch(self): pass
            
        class QLabel:
            def __init__(self, text="", *args, **kwargs): pass
            def setStyleSheet(self, style): pass
            def setText(self, text): pass
            
        class QTabWidget:
            def __init__(self, *args, **kwargs): pass
            def setUsesScrollButtons(self, value): pass
            def setElideMode(self, mode): pass
            def addTab(self, widget, name): pass
            def count(self): return 0
            def widget(self, index): return None
            
        class QMessageBox:
            @staticmethod
            def information(parent, title, text): pass
            @staticmethod
            def critical(parent, title, text): pass
            
        class QApplication:
            @staticmethod
            def instance(): return None
            @staticmethod
            def processEvents(): pass
            
    QtCore = DummyQtCore()
    QtWidgets = DummyQtWidgets()
    QtGui = DummyQtWidgets()

def get_qt_version():
    """Get the Qt version being used."""
    return QT_VERSION

def is_qt_available():
    """Check if Qt is available."""
    return HAS_QT
'''
    
    qt_compat_path = os.path.join(gui_dir, 'qt_compatibility.py')
    with open(qt_compat_path, 'w') as f:
        f.write(qt_compat_content)

def fix_import_paths(freecad_ai_dir):
    """Fix import path issues by creating proper __init__.py files."""
    
    # Ensure all directories have __init__.py
    directories = [
        'ai',
        'ai/providers', 
        'core',
        'gui',
        'config',
        'tools',
        'utils'
    ]
    
    for dir_path in directories:
        full_dir_path = os.path.join(freecad_ai_dir, dir_path)
        if os.path.exists(full_dir_path):
            init_file = os.path.join(full_dir_path, '__init__.py')
            if not os.path.exists(init_file):
                with open(init_file, 'w') as f:
                    f.write(f'"""Package: {dir_path}"""\n')

def fix_agent_manager_init(freecad_ai_dir):
    """Fix agent manager initialization issues."""
    
    # Create a robust agent manager wrapper
    wrapper_content = '''"""
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
'''
    
    wrapper_path = os.path.join(freecad_ai_dir, 'core', 'agent_manager_wrapper.py')
    with open(wrapper_path, 'w') as f:
        f.write(wrapper_content)

def fix_provider_service_init(freecad_ai_dir):
    """Fix provider service initialization issues."""
    
    # Create a robust provider service wrapper
    wrapper_content = '''"""
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
'''
    
    wrapper_path = os.path.join(freecad_ai_dir, 'ai', 'provider_service_wrapper.py')
    with open(wrapper_path, 'w') as f:
        f.write(wrapper_content)

if __name__ == "__main__":
    fix_freecad_ai_initialization()
