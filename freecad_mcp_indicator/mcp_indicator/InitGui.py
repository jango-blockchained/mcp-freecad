import os
import FreeCAD
import FreeCADGui
from PySide2 import QtCore, QtGui, QtWidgets

class MCPIndicatorWorkbench(FreeCADGui.Workbench):
    """MCP Connection Indicator Workbench"""
    
    MenuText = "MCP Indicator"
    ToolTip = "Shows MCP connection status"
    Icon = """
/* XPM */
static char * mcp_icon_xpm[] = {
"16 16 3 1",
" 	c None",
".	c #000000",
"+	c #FFFFFF",
"                ",
"     ......     ",
"   ..++++++..   ",
"  .+++++++++++. ",
" .+++++..+++++. ",
".++++.  ..++++. ",
".+++.    .++++. ",
".+++.    .++++. ",
".+++.    .++++. ",
".++++.  ..++++. ",
" .+++++..+++++. ",
"  .+++++++++++. ",
"   ..++++++..   ",
"     ......     ",
"                ",
"                "};
"""
    
    def __init__(self):
        self._indicator = None
        self._timer = None
        
    def Initialize(self):
        """Initialize the workbench"""
        # Create the indicator widget
        self._indicator = QtWidgets.QLabel()
        self._indicator.setFixedSize(16, 16)
        self._update_indicator(False)  # Start as disconnected
        
        # Add indicator to status bar
        mw = FreeCADGui.getMainWindow()
        if mw:
            statusbar = mw.statusBar()
            statusbar.addPermanentWidget(self._indicator)
            
        # Setup timer for periodic connection check
        self._timer = QtCore.QTimer()
        self._timer.timeout.connect(self._check_connection)
        self._timer.start(5000)  # Check every 5 seconds
        
    def Activated(self):
        """Called when workbench is activated"""
        pass
        
    def Deactivated(self):
        """Called when workbench is deactivated"""
        pass
        
    def _update_indicator(self, connected):
        """Update the indicator appearance based on connection status"""
        color = QtGui.QColor("#4CAF50") if connected else QtGui.QColor("#F44336")
        size = self._indicator.size()
        pixmap = QtGui.QPixmap(size)
        pixmap.fill(QtCore.Qt.transparent)
        
        painter = QtGui.QPainter(pixmap)
        painter.setRenderHint(QtGui.QPainter.Antialiasing)
        painter.setBrush(QtGui.QBrush(color))
        painter.setPen(QtCore.Qt.NoPen)
        painter.drawEllipse(2, 2, size.width()-4, size.height()-4)
        painter.end()
        
        self._indicator.setPixmap(pixmap)
        self._indicator.setToolTip("MCP: " + ("Connected" if connected else "Disconnected"))
        
    def _check_connection(self):
        """Check MCP connection status"""
        try:
            # Import the MCP connection manager
            from mcp_freecad.core.connection import FreeCADConnectionManager
            from mcp_freecad.core.recovery import RecoveryConfig
            
            # Create a connection manager instance
            config = RecoveryConfig()
            manager = FreeCADConnectionManager(config)
            
            # Update indicator based on connection status
            self._update_indicator(manager.connected)
            
        except Exception as e:
            FreeCAD.Console.PrintWarning(f"MCP connection check failed: {str(e)}\n")
            self._update_indicator(False)

FreeCADGui.addWorkbench(MCPIndicatorWorkbench()) 