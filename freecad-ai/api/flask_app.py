"""
Flask-based API for FreeCAD AI unified server entrypoint
"""
import sys
import os
from flask import Flask

# Ensure the current directory is in sys.path for local imports
sys.path.insert(0, os.path.dirname(__file__))

try:
    from .flask_tools_api import tools_bp
    from .flask_resources_api import resources_bp
    from .flask_events_api import events_bp
except ImportError:
    from flask_tools_api import tools_bp
    from flask_resources_api import resources_bp
    from flask_events_api import events_bp

app = Flask(__name__)
app.register_blueprint(tools_bp)
app.register_blueprint(resources_bp)
app.register_blueprint(events_bp)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
