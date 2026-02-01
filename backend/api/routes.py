# backend/api/routes.py
from fastapi import APIRouter, HTTPException, WebSocket, WebSocketDisconnect
from pydantic import BaseModel
from services.simulation import SimulationEngine
from services.websocket_manager import ConnectionManager
import asyncio

router = APIRouter()
sim_engine = SimulationEngine()
ws_manager = ConnectionManager()

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
    while sim_engine.running:
        sim_engine.step()
        if sim_engine.should_broadcast() and ws_manager.get_connection_count() > 0:
            state = sim_engine.get_broadcast_state()
            await ws_manager.broadcast(state)
        await asyncio.sleep(1/30)


async def idle_loop():
    while True:
        state = sim_engine.get_broadcast_state()
        await ws_manager.broadcast(state)
        await asyncio.sleep(1)

@router.post("/simulation/start")
async def start_simulation(params: StartParams):
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
    return {"status": "simulation started"}

@router.get("/simulation/state")
async def get_state():
    if not sim_engine.state:
        raise HTTPException(status_code=400, detail="Simulation not running")
    return sim_engine.get_state()

@router.post("/simulation/pause")
async def pause_simulation():
    sim_engine.pause()
    return {"status": "simulation paused"}

@router.post("/simulation/reset")
async def reset_simulation():
    global simulation_task
    sim_engine.reset()
    if simulation_task and not simulation_task.done():
        simulation_task.cancel()
    return {"status": "simulation reset"}

@router.post("/simulation/parameters")
async def update_parameters(params: ParameterUpdate):
    update_dict = {}
    if params.trust_decay is not None:
        update_dict['trust_decay'] = params.trust_decay
    if params.trust_quota is not None:
        update_dict['trust_quota'] = params.trust_quota
    sim_engine.update_parameters(update_dict)
    return {"status": "parameters updated"}

@router.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    global simulation_task
    await ws_manager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_json()
            print("Received WebSocket message >>> ", data)
            if not isinstance(data, dict):
                continue

            cmd_type = data.get("type")

            if cmd_type == "start":
                global simulation_task
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
                simulation_task = asyncio.create_task(simulation_loop())

            elif cmd_type == "pause":
                sim_engine.pause()
                report = sim_engine.state.compile_final_report()
                sim_engine.state.reports = []
                print("FINAL REPORT => " + str(report))
                print("------------------------------")
                await ws_manager.broadcast_json({'type': 'report_final', 'payload': {'final_report': report}})

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
                    update_dict["speedMultiplier"] = payload["speedMultiplier"]
                sim_engine.update_parameters(update_dict)

            elif cmd_type == "add_agent":
                try:
                    payload = data.get("payload", {})
                    sim_engine.add_custom_agent(payload)
                    print(f"ADD_AGENT: {payload}")
                except Exception as e:
                    print(f"Error ADD_AGENT: {e}")

            elif cmd_type == "create_group":
                try:
                    payload = data.get("payload", {})
                    group_id = int(payload.get("groupId", 0))
                    num_agents = int(payload.get("numAgents", 0))
                    config = payload.get("config", None)
                    result = sim_engine.create_group(group_id, num_agents, config)
                    if (not sim_engine.running):
                        sim_engine.start(num_agents, 0, 0)
                        sim_engine.pause()
                        simulation_task = asyncio.create_task(idle_loop())
                    await ws_manager.send_personal_message(
                        {"type": "group_created", "payload": result}, websocket
                    )
                    
                    print(f"CREATE_GROUP {group_id}: {result}")
                except Exception as e:
                    print(f"Error CREATE_GROUP: {e}")
                    await ws_manager.send_personal_message(
                        {"type": "group_created", "payload": {"error": str(e)}}, websocket
                    )

            elif cmd_type == "switch_group":
                try:
                    payload = data.get("payload", {})
                    group_id = int(payload.get("groupId", 0))
                    result = sim_engine.switch_group(group_id)
                    await ws_manager.send_personal_message(
                        {"type": "group_switched", "payload": result}, websocket
                    )
                except Exception as e:
                    print(f"Error SWITCH_GROUP: {e}")

            elif cmd_type == "update_group_config":
                try:
                    payload = data.get("payload", {})
                    group_id = int(payload.get("groupId", 0))
                    config = payload.get("config", {})
                    result = sim_engine.update_group_config(group_id, config)
                    await ws_manager.send_personal_message(
                        {"type": "group_config_updated", "payload": result}, websocket
                    )
                except Exception as e:
                    print(f"Error UPDATE_GROUP_CONFIG: {e}")

    except WebSocketDisconnect:
        ws_manager.disconnect(websocket)
    except Exception as e:
        print(f"WebSocket error: {e}")
        ws_manager.disconnect(websocket)

@router.get("/ws/status")
async def websocket_status():
    return {
        "active_connections": ws_manager.get_connection_count(),
        "simulation_running": sim_engine.running,
        "current_tick": sim_engine.state.tick if sim_engine.state else 0
    }