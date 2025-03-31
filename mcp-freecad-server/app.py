import uvicorn
from fastapi import FastAPI
import json

app = FastAPI(title="FreeCAD MCP Server")

@app.get("/")
async def root():
    return {"message": "FreeCAD MCP Server is running"}

if __name__ == "__main__":
    uvicorn.run(app, host="localhost", port=8080)