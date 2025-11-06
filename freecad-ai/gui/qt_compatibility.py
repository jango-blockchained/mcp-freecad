"""
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
        except Exception:
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
