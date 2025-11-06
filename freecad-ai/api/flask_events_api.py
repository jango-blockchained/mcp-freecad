"""
Flask-based API for FreeCAD AI events endpoint (migration template)
"""

import uuid

from flask import Blueprint, Response, abort, jsonify, request, stream_with_context

events_bp = Blueprint("events", __name__, url_prefix="/events")

# In-memory store of connected clients and their queues (for demo only)
client_queues = {}
client_subscriptions = {}


def get_event_handler(event_type):
    from freecad_ai_workbench import MCPServer

    server = MCPServer()
    return server.event_handlers.get(event_type, [])


def get_auth_manager():
    from freecad_ai_workbench import MCPServer

    server = MCPServer()
    return server.auth_manager


@events_bp.route("/subscribe", methods=["POST"])
def update_subscription():
    data = request.get_json()
    authorization = request.headers.get("Authorization")
    if authorization:
        token = authorization.replace("Bearer ", "")
        if not get_auth_manager().authenticate(token):
            abort(401, description="Invalid authentication token")
        client_id = token
    else:
        abort(401, description="Missing authentication token")
    event_types = data.get("event_types", [])
    if client_id not in client_queues:
        abort(404, description="Client not found or not connected")
    # Remove from all handlers first (demo logic)
    for handlers in get_event_handler("").values():
        for handler in handlers:
            handler.remove_listener(client_id)
    # Add to requested handlers
    for event_type in event_types:
        for handler in get_event_handler(event_type):
            handler.add_listener(client_id)
    client_subscriptions[client_id] = event_types
    return jsonify({"success": True, "message": "Subscription updated successfully"})


@events_bp.route("/<event_type>", methods=["POST"])
def trigger_event(event_type):
    data = request.get_json()
    authorization = request.headers.get("Authorization")
    if authorization:
        token = authorization.replace("Bearer ", "")
        if not get_auth_manager().authenticate(token):
            abort(401, description="Invalid authentication token")
    else:
        abort(401, description="Missing authentication token")
    handlers = get_event_handler(event_type)
    if not handlers:
        return jsonify(
            {
                "success": False,
                "message": f"No handlers registered for event type: {event_type}",
            }
        )
    try:
        for handler in handlers:
            handler.handle_event(event_type, data.get("data", {}))
        return jsonify(
            {"success": True, "message": f"Event {event_type} triggered successfully"}
        )
    except Exception as e:
        abort(500, description=f"Error triggering event: {str(e)}")


@events_bp.route("", methods=["GET"])
def subscribe_events():
    types = request.args.getlist("types")
    authorization = request.headers.get("Authorization")
    if authorization:
        token = authorization.replace("Bearer ", "")
        if not get_auth_manager().authenticate(token):
            abort(401, description="Invalid authentication token")
    else:
        abort(401, description="Missing authentication token")
    client_id = str(uuid.uuid4())
    if types:
        client_subscriptions[client_id] = types
        for event_type in types:
            for handler in get_event_handler(event_type):
                handler.add_listener(client_id)
    else:
        all_event_types = list(get_event_handler("").keys())
        client_subscriptions[client_id] = all_event_types
        for event_type, handlers in get_event_handler("").items():
            for handler in handlers:
                handler.add_listener(client_id)

    def event_stream():
        # Demo: yield dummy events
        yield 'data: {"event": "ping", "data": {}}\n\n'

    return Response(stream_with_context(event_stream()), mimetype="text/event-stream")
