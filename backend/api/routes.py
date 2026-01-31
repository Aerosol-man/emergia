from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from services.simulation import SimulationEngine
from services.websocket_manager import ConnectionManager
import asyncio

router = APIRouter()
sim_engine = SimulationEngine()
ws_manager = ConnectionManager()

# Background task reference
simulation_task = None

class StartParams(BaseModel):
    num_agents: int
    trust_decay: float
    trust_quota: float

class ParameterUpdate(BaseModel):
    trust_decay: float = None
    trust_quota: float = None
    add_bad_actors: int = None


async def simulation_loop():
    """Background task that runs the simulation at ~30Hz"""
    while sim_engine.running:
        sim_engine.step()
        # Broadcast state to all connected clients
        if sim_engine.should_broadcast() and ws_manager.get_connection_count() > 0:
            state = sim_engine.get_broadcast_state()
            await ws_manager.broadcast(state)
        await asyncio.sleep(1/30)  # ~30 FPS


@router.post("/simulation/start")
async def start_simulation(params: StartParams):
    """Start simulation with given parameters"""
    global simulation_task

    if simulation_task and not simulation_task.done():
        sim_engine.pause()
        simulation_task.cancel()
        try:
            await simulation_task
        except asyncio.CancelledError:
            pass

    sim_engine.start(
        num_agents=params.num_agents,
        trust_decay=params.trust_decay,
        trust_quota=params.trust_quota
    )

    simulation_task = asyncio.create_task(simulation_loop())

    print(f"Simulation started with {params.num_agents} agents.")
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
    global simulation_task
    sim_engine.reset()
    if simulation_task and not simulation_task.done():
        simulation_task.cancel()
    return {"status": "simulation reset"}

@router.post("/simulation/parameters")
async def update_parameters(params: ParameterUpdate):
    """Update simulation parameters on-the-fly"""
    update_dict = {}
    if params.trust_decay is not None:
        update_dict['trust_decay'] = params.trust_decay
    if params.trust_quota is not None:
        update_dict['trust_quota'] = params.trust_quota
    sim_engine.update_parameters(update_dict)
    return {"status": "parameters updated"}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """WebSocket endpoint for real-time state updates"""
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()

            if isinstance(data, dict):
                cmd_type = data.get("type")
                if cmd_type == "start":
                    global simulation_task

                    # Stop any existing simulation
                    if simulation_task and not simulation_task.done():
                        sim_engine.pause()
                        simulation_task.cancel()
                        try:
                            await simulation_task
                        except asyncio.CancelledError:
                            pass

                    params = data.get("payload", {})
                    sim_engine.start(
                        num_agents=params.get("agentCount", 100),
                        trust_decay=params.get("trustDecay", 0.01),
                        trust_quota=params.get("trustQuota", 0.3)
                    )

                    # Start the loop — broadcast directly via ws_manager, no callback needed
                    simulation_task = asyncio.create_task(simulation_loop())
                    print(f"Simulation started with {params.get('agentCount', 100)} agents via WebSocket.")

                elif cmd_type == "pause":
                    sim_engine.pause()

                elif cmd_type == "reset":
                    sim_engine.reset()
                    if simulation_task and not simulation_task.done():
                        simulation_task.cancel()

                elif cmd_type == "update_config":
                    payload = data.get("payload", {})
                    update_dict = {}
                    if "trustDecay" in payload:
                        update_dict["trust_decay"] = payload["trustDecay"]
                    if "trustQuota" in payload:
                        update_dict["trust_quota"] = payload["trustQuota"]
                    if "speedMultiplier" in payload:
                        update_dict["dt"] = 0.016 / payload["speedMultiplier"]
                    sim_engine.update_parameters(update_dict)

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)

@router.get("/ws/status")
async def websocket_status():
    """Get WebSocket connection status"""
    return {
        "active_connections": ws_manager.get_connection_count(),
        "simulation_running": sim_engine.running,
        "current_tick": sim_engine.state.tick if sim_engine.state else 0
    }