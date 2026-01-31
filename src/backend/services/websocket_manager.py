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
        pass
        
    def disconnect(self, websocket: WebSocket):
        """Remove WebSocket connection"""
        pass
    
    async def send_personal_message(self, message: dict, websocket: WebSocket):
        """Send message to specific client"""
        pass
    
    async def broadcast(self, message: dict):
        """Broadcast message to all connected clients"""
        pass
    
    async def broadcast_json(self, data: dict):
        """Broadcast JSON data to all clients"""
        pass
    
    async def heartbeat(self, websocket: WebSocket):
        """Send periodic ping to keep connection alive"""
        pass
    
    def get_connection_count(self) -> int:
        """Return number of active connections"""
        return len(self.active_connections)