"""
Flask-based API for FreeCAD AI resources endpoint (migration template)
"""

from flask import Blueprint, abort, jsonify, request

resources_bp = Blueprint("resources", __name__, url_prefix="/resources")


def get_resource_provider(resource_type):
    try:
        from ..freecad_ai_workbench import MCPServer
    except ImportError:
        from freecad_ai_workbench import MCPServer
    server = MCPServer()
    return server.resources.get(resource_type)


@resources_bp.route("/<resource_id>", methods=["GET"])
def get_resource(resource_id):
    uri = request.args.get("uri")
    params = request.args.get("params")
    provider = get_resource_provider(resource_id)
    if not provider:
        abort(404, description=f"Resource provider not found: {resource_id}")
    try:
        # If URI is not provided, use a default URI based on resource ID
        if not uri:
            if resource_id == "cad_model":
                uri = "cad://model/current"
            elif resource_id == "measurements":
                uri = "cad://measurements"
            elif resource_id == "materials":
                uri = "cad://materials"
            elif resource_id == "constraints":
                uri = "cad://constraints"
            else:
                uri = f"cad://{resource_id}"
        # params is expected as JSON string if present
        if params:
            import json

            params = json.loads(params)
        else:
            params = {}
        result = provider.get_resource(uri, params)
        return jsonify(result), 200
    except Exception as e:
        abort(500, description=f"Error getting resource: {str(e)}")


@resources_bp.route("/measurements/<measurement_type>", methods=["GET"])
def get_measurement(measurement_type):
    object_name = request.args.get("object_name")
    point1 = request.args.get("point1")
    point2 = request.args.get("point2")
    provider = get_resource_provider("measurements")
    if not provider:
        abort(404, description="Measurement provider not found")
    try:
        uri = f"cad://measurements/{measurement_type}"
        if object_name:
            uri += f"/{object_name}"
        params = {}
        if point1 and point2:
            try:
                p1 = [float(x) for x in point1.split(",")]
                p2 = [float(x) for x in point2.split(",")]
                params["points"] = [p1, p2]
            except ValueError:
                abort(400, description="Invalid point format. Expected: x,y,z")
        result = provider.get_resource(uri, params)
        return jsonify(result), 200
    except Exception as e:
        abort(500, description=f"Error getting measurement: {str(e)}")


@resources_bp.route("/materials/<resource_type>", methods=["GET"])
def get_material(resource_type):
    object_name = request.args.get("object_name")
    material_name = request.args.get("material_name")
    provider = get_resource_provider("materials")
    if not provider:
        abort(404, description="Material provider not found")
    try:
        uri = f"cad://materials/{resource_type}"
        if resource_type == "object" and object_name:
            uri += f"/{object_name}"
        elif resource_type == "info" and material_name:
            uri += f"/{material_name}"
        result = provider.get_resource(uri)
        return jsonify(result), 200
    except Exception as e:
        abort(500, description=f"Error getting material information: {str(e)}")


@resources_bp.route("/constraints/<resource_type>", methods=["GET"])
def get_constraint(resource_type):
    object_name = request.args.get("object_name")
    provider = get_resource_provider("constraints")
    if not provider:
        abort(404, description="Constraint provider not found")
    try:
        uri = f"cad://constraints/{resource_type}"
        if object_name:
            uri += f"/{object_name}"
        result = provider.get_resource(uri)
        return jsonify(result), 200
    except Exception as e:
        abort(500, description=f"Error getting constraint information: {str(e)}")
