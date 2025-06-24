import json
import FreeCAD

version = getattr(FreeCAD, "Version", "unknown")
if callable(version):
    version = version()
version_info = {
    "version": str(version),
    "success": True
}
print(json.dumps(version_info))
