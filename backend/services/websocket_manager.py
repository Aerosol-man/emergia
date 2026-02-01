# backend/services/websocket_manager.py
from fastapi import WebSocket
from typing import List, Dict
import json
import asyncio

class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []
        self.client_data: Dict[WebSocket, dict] = {}
        
    async def connect(self, websocket: WebSocket):
        """Accept and register new WebSocket connection"""
        await websocket.accept()
        self.active_connections.append(websocket)
        self.client_data[websocket] = {}
        print(f"WebSocket connected. Active connections: {len(self.active_connections)}")
        
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
        if websocket in self.client_data:
            del self.client_data[websocket]
        print(f"WebSocket disconnected. Active connections: {len(self.active_connections)}")
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client"""
        print("MSG SENT")
        await websocket.send_json(message)
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        for connection in self.active_connections:
            await self.send_personal_message(message, connection)
    
    async def broadcast_json(self, data: dict):
        """Broadcast JSON data to all clients"""
        await self.broadcast(data)
    
    async def heartbeat(self, websocket: WebSocket):
        """Send periodic ping to keep connection alive"""
        pass
    
    def get_connection_count(self) -> int:
        """Return number of active connections"""
        return len(self.active_connections)