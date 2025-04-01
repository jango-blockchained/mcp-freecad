from mcp_freecad.core.recovery import RecoveryConfig

class FreeCADConnectionManager:
    def __init__(self, config: RecoveryConfig):
        self._config = config
        self._freecad = None
        self._connected = False

    @property
    def connected(self) -> bool:
        """Return whether FreeCAD is currently connected."""
        return self._connected

    async def connect(self) -> None:
        """Connect to FreeCAD."""
        if self._connected:
            return

        try:
            import FreeCAD
            self._freecad = FreeCAD
            self._connected = True
        except ImportError as e:
            self._connected = False
            raise ConnectionError("Failed to import FreeCAD") from e

    async def disconnect(self) -> None:
        """Disconnect from FreeCAD."""
        self._freecad = None
        self._connected = False 