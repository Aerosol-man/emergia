# backend/api/routes.py
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from services.simulation import SimulationEngine
from services.websocket_manager import ConnectionManager

router = APIRouter()
sim_engine = SimulationEngine()
ws_manager = ConnectionManager()

class StartParams(BaseModel):
    num_agents: int
    trust_decay: float
    trust_quota: float

class ParameterUpdate(BaseModel):
    trust_decay: float = None
    trust_quota: float = None
    add_bad_actors: int = None

@router.post("/simulation/start")
async def start_simulation(params: StartParams):
    """Start simulation with given parameters"""
    pass

@router.get("/simulation/state")
async def get_state():
    """Get current simulation state"""
    pass

@router.post("/simulation/pause")
async def pause_simulation():
    """Pause the simulation"""
    pass

@router.post("/simulation/reset")
async def reset_simulation():
    """Reset simulation to initial state"""
    pass

@router.post("/simulation/parameters")
async def update_parameters(params: ParameterUpdate):
    """Update simulation parameters on-the-fly"""
    pass

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time state updates"""
    pass

@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "active_connections": ws_manager.get_connection_count(),
        "simulation_running": sim_engine.running,
        "current_tick": sim_engine.state.tick if sim_engine.state else 0
    }