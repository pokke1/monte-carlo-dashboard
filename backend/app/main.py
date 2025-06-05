from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import json
from pathlib import Path

from app.websocket import SimulationWebSocket
from app.api.routes import api_router

# Get the frontend directory
BASE_DIR = Path(__file__).resolve().parent.parent.parent
FRONTEND_DIR = BASE_DIR / "frontend"

app = FastAPI(
    title="Monte Carlo Simulation Dashboard",
    description="High-performance Monte Carlo simulations with real-time visualization",
    version="1.0.0"
)

# CORS middleware for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router, prefix="/api/v1")

# WebSocket endpoint
@app.websocket("/ws/simulate")
async def websocket_endpoint(websocket: WebSocket):
    simulation_ws = SimulationWebSocket(websocket)
    await simulation_ws.connect()
    
    try:
        while True:
            data = await websocket.receive_json()
            await simulation_ws.handle_message(data)
    except WebSocketDisconnect:
        await simulation_ws.disconnect()
    except Exception as e:
        print(f"WebSocket error: {e}")
        await simulation_ws.disconnect()

# Serve frontend files
@app.get("/")
async def serve_frontend():
    return FileResponse(FRONTEND_DIR / "index.html")

# Mount static files
app.mount("/css", StaticFiles(directory=FRONTEND_DIR / "css"), name="css")
app.mount("/js", StaticFiles(directory=FRONTEND_DIR / "js"), name="js")
# app.mount("/assets", StaticFiles(directory=FRONTEND_DIR / "assets"), name="assets")

@app.get("/health")
async def health_check():
    return {"status": "healthy", "service": "monte-carlo-dashboard"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)