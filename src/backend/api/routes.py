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
    sim_engine.start(
        num_agents=params.num_agents,
        trust_decay=params.trust_decay,
        trust_quota=params.trust_quota
    )
    router.logger.info(f"Simulation started with {params.num_agents} agents.")
    return {"status": "simulation started"}

@router.get("/simulation/state")
async def get_state():
    """Get current simulation state"""
    if not sim_engine.state:
        raise HTTPException(status_code=400, detail="Simulation not running")
    return sim_engine.get_state()

@router.post("/simulation/pause")
async def pause_simulation():
    """Pause the simulation"""
    sim_engine.pause()
    return {"status": "simulation paused"}

@router.post("/simulation/reset")
async def reset_simulation():
    """Reset simulation to initial state"""
    sim_engine.reset()
    return {"status": "simulation reset"}

@router.post("/simulation/parameters")
async def update_parameters(params: ParameterUpdate):
    """Update simulation parameters on-the-fly"""
    sim_engine.update_parameters(
        trust_decay=params.trust_decay,
        trust_quota=params.trust_quota,
        add_bad_actors=params.add_bad_actors
    )

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time state updates"""
    await ws_manager.connect(websocket)
    while True:
        try:
            await websocket.receive_json()  # Keep connection alive
            await ws_manager.send_personal_message(sim_engine.get_broadcast_state(), websocket)
        except WebSocketDisconnect:
            ws_manager.disconnect(websocket)
            break

@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "active_connections": ws_manager.get_connection_count(),
        "simulation_running": sim_engine.running,
        "current_tick": sim_engine.state.tick if sim_engine.state else 0
    }