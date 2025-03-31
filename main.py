import uvicorn
from fastapi import FastAPI

app = FastAPI(title="FreeCAD MCP Server")

@app.get("/")
async def root():
    return {"message": "FreeCAD MCP Server is running"}

# Placeholder for future MCP routes
# app.add_api_route("/resources/{resource_id}", handle_resource_request, methods=["GET"])
# app.add_api_route("/tools/{tool_id}", handle_tool_request, methods=["POST"])
# app.add_api_route("/events", handle_events, methods=["GET"])

if __name__ == "__main__":
    # Basic configuration, will be enhanced later
    uvicorn.run(app, host="localhost", port=8080) 