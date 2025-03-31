import uvicorn
import time
import datetime
import platform
import psutil
from fastapi import FastAPI, Header, HTTPException, Depends
from typing import Optional

app = FastAPI()

# Track server start time
start_time = time.time()

@app.get("/")
async def root():
    return {"message": "MCP-FreeCAD Simple Server"}

@app.get("/health")
async def health():
    return {
        "status": "ok",
        "version": "1.0.0",
        "server_initialized": True,
        "timestamp": datetime.datetime.now().isoformat()
    }

@app.get("/health/detailed")
async def health_detailed():
    # Get system stats
    mem = psutil.virtual_memory()
    disk = psutil.disk_usage('/')
    
    # Get server uptime
    uptime = time.time() - start_time
    
    # Format uptime
    uptime_formatted = str(datetime.timedelta(seconds=int(uptime)))
    
    return {
        "status": "ok",
        "version": "1.0.0",
        "timestamp": datetime.datetime.now().isoformat(),
        "system": {
            "platform": platform.platform(),
            "python_version": platform.python_version(),
            "cpu_count": psutil.cpu_count(),
            "cpu_percent": psutil.cpu_percent(),
            "memory": {
                "total": round(mem.total / (1024 * 1024), 2),  # MB
                "available": round(mem.available / (1024 * 1024), 2),  # MB
                "percent": mem.percent
            },
            "disk": {
                "total": round(disk.total / (1024 * 1024 * 1024), 2),  # GB
                "free": round(disk.free / (1024 * 1024 * 1024), 2),  # GB
                "percent": disk.percent
            }
        },
        "server": {
            "uptime_seconds": uptime,
            "uptime_formatted": uptime_formatted,
            "freecad_status": "mock",
            "initialized": True,
            "event_handlers": ["document_changed", "command_executed", "error"],
            "resource_providers": ["cad_model"],
            "tool_providers": ["primitives"]
        }
    }

def verify_api_key(authorization: Optional[str] = Header(None)):
    """Verify the API key middleware."""
    return True  # Allow all

@app.get("/cache/stats")
async def cache_stats():
    return {
        "size": 0,
        "max_size": 100,
        "default_ttl": 30.0,
        "hit_count": 0,
        "miss_count": 0,
        "hit_rate": 0,
        "keys": []
    }

@app.post("/cache/clear")
async def clear_cache():
    return {"status": "success", "message": "Cache cleared successfully"}

@app.delete("/cache/item/{key}")
async def delete_cache_item(key: str):
    return {"status": "success", "message": f"Cache item '{key}' deleted successfully"}

@app.get("/diagnostics")
async def diagnostics():
    # Get server uptime
    uptime = time.time() - start_time
    uptime_formatted = str(datetime.timedelta(seconds=int(uptime)))
    
    # Get process info
    process = psutil.Process()
    
    return {
        "server": {
            "uptime_seconds": uptime,
            "uptime_formatted": uptime_formatted,
            "start_time": datetime.datetime.fromtimestamp(start_time).isoformat(),
            "current_time": datetime.datetime.now().isoformat(),
            "request_count": 0,
            "error_count": 0,
            "metric_count": 0
        },
        "system": {
            "cpu_percent": process.cpu_percent(),
            "memory_usage": {
                "rss": round(process.memory_info().rss / (1024 * 1024), 2),  # MB
                "vms": round(process.memory_info().vms / (1024 * 1024), 2)   # MB
            },
            "thread_count": process.num_threads()
        },
        "metrics": [],
        "recovery": {
            "retries": {},
            "failures": {}
        },
        "cache": {
            "size": 0,
            "hit_rate": 0
        }
    }

@app.post("/diagnostics/reset")
async def reset_diagnostics():
    return {"status": "success", "message": "Diagnostics reset successfully"}

@app.get("/diagnostics/slow_endpoints")
async def slow_endpoints(limit: int = 10):
    return {"slow_endpoints": []}

@app.get("/diagnostics/errors")
async def error_diagnostics(limit: int = 50):
    return {
        "error_count": 0,
        "error_types": {},
        "recent_errors": []
    }

@app.post("/tools/measurement.distance")
async def measurement_distance(tool_request: dict):
    # Simulated delay
    time.sleep(0.2)
    
    params = tool_request.get("parameters", {})
    object1 = params.get("object1", "Unknown")
    object2 = params.get("object2", "Unknown")
    
    return {
        "status": "success",
        "tool": "measurement.distance",
        "result": {
            "distance": 10.0,
            "unit": "mm",
            "objects": [object1, object2]
        }
    }

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000) 