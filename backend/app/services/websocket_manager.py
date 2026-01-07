import asyncio
import json
import logging
from typing import Set, Dict, Any
from fastapi import WebSocket, WebSocketDisconnect
from datetime import datetime

logger = logging.getLogger(__name__)

class WebSocketManager:
    def __init__(self):
        self.active_connections: Set[WebSocket] = set()
        self.connection_info: Dict[WebSocket, Dict[str, Any]] = {}
    
    async def connect(self, websocket: WebSocket, client_id: str = None):
        """Accept a new WebSocket connection"""
        await websocket.accept()
        self.active_connections.add(websocket)
        self.connection_info[websocket] = {
            "client_id": client_id or f"client_{len(self.active_connections)}",
            "connected_at": datetime.utcnow(),
            "last_ping": datetime.utcnow()
        }
        logger.info(f"🔌 WebSocket connected: {self.connection_info[websocket]['client_id']} (Total: {len(self.active_connections)})")
        
        # Send welcome message
        await self.send_personal_message(websocket, {
            "type": "connection_established",
            "client_id": self.connection_info[websocket]['client_id'],
            "timestamp": datetime.utcnow().isoformat()
        })
    
    def disconnect(self, websocket: WebSocket):
        """Remove a WebSocket connection"""
        if websocket in self.active_connections:
            client_info = self.connection_info.get(websocket, {})
            self.active_connections.remove(websocket)
            if websocket in self.connection_info:
                del self.connection_info[websocket]
            logger.info(f"🔌 WebSocket disconnected: {client_info.get('client_id', 'unknown')} (Total: {len(self.active_connections)})")
    
    async def send_personal_message(self, websocket: WebSocket, message: Dict[str, Any]):
        """Send a message to a specific WebSocket connection"""
        try:
            await websocket.send_text(json.dumps(message, default=str))
        except Exception as e:
            logger.error(f"Failed to send personal message: {e}")
            self.disconnect(websocket)
    
    async def broadcast(self, message: Dict[str, Any]):
        """Broadcast a message to all connected clients"""
        if not self.active_connections:
            return
        
        message["timestamp"] = datetime.utcnow().isoformat()
        disconnected = set()
        
        for connection in self.active_connections:
            try:
                await connection.send_text(json.dumps(message, default=str))
            except Exception as e:
                logger.error(f"Failed to broadcast to connection: {e}")
                disconnected.add(connection)
        
        # Clean up disconnected connections
        for connection in disconnected:
            self.disconnect(connection)
        
        if disconnected:
            logger.info(f"📡 Broadcast sent to {len(self.active_connections)} clients, removed {len(disconnected)} disconnected")
        else:
            logger.info(f"📡 Broadcast sent to {len(self.active_connections)} clients")
    
    async def send_incident_update(self, incident_data: Dict[str, Any], event_type: str = "updated"):
        """Send incident-specific updates"""
        message = {
            "type": "incident_update",
            "event_type": event_type,
            "incident": incident_data
        }
        await self.broadcast(message)
    
    async def send_metrics_update(self, metrics_data: Dict[str, Any]):
        """Send dashboard metrics updates"""
        message = {
            "type": "metrics_update",
            "metrics": metrics_data
        }
        await self.broadcast(message)
    
    async def send_system_alert(self, alert_type: str, message: str, severity: str = "info"):
        """Send system-wide alerts"""
        alert_message = {
            "type": "system_alert",
            "alert_type": alert_type,
            "message": message,
            "severity": severity
        }
        await self.broadcast(alert_message)
    
    async def handle_client_message(self, websocket: WebSocket, message: str):
        """Handle incoming messages from clients"""
        try:
            data = json.loads(message)
            message_type = data.get("type")
            
            if message_type == "ping":
                # Update last ping time
                if websocket in self.connection_info:
                    self.connection_info[websocket]["last_ping"] = datetime.utcnow()
                
                # Send pong response
                await self.send_personal_message(websocket, {
                    "type": "pong",
                    "timestamp": datetime.utcnow().isoformat()
                })
            
            elif message_type == "subscribe":
                # Handle subscription to specific incident updates
                incident_id = data.get("incident_id")
                if incident_id:
                    # Store subscription info
                    if websocket in self.connection_info:
                        subscriptions = self.connection_info[websocket].get("subscriptions", set())
                        subscriptions.add(incident_id)
                        self.connection_info[websocket]["subscriptions"] = subscriptions
                    
                    await self.send_personal_message(websocket, {
                        "type": "subscription_confirmed",
                        "incident_id": incident_id
                    })
            
            elif message_type == "unsubscribe":
                # Handle unsubscription
                incident_id = data.get("incident_id")
                if incident_id and websocket in self.connection_info:
                    subscriptions = self.connection_info[websocket].get("subscriptions", set())
                    subscriptions.discard(incident_id)
                    self.connection_info[websocket]["subscriptions"] = subscriptions
                    
                    await self.send_personal_message(websocket, {
                        "type": "unsubscription_confirmed",
                        "incident_id": incident_id
                    })
        
        except json.JSONDecodeError:
            logger.error(f"Invalid JSON received from client")
        except Exception as e:
            logger.error(f"Error handling client message: {e}")
    
    async def start_heartbeat(self):
        """Start heartbeat to keep connections alive"""
        while True:
            await asyncio.sleep(30)  # Send heartbeat every 30 seconds
            
            if self.active_connections:
                heartbeat_message = {
                    "type": "heartbeat",
                    "active_connections": len(self.active_connections),
                    "server_time": datetime.utcnow().isoformat()
                }
                await self.broadcast(heartbeat_message)
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """Get statistics about active connections"""
        return {
            "total_connections": len(self.active_connections),
            "connections": [
                {
                    "client_id": info["client_id"],
                    "connected_at": info["connected_at"].isoformat(),
                    "last_ping": info["last_ping"].isoformat(),
                    "subscriptions": list(info.get("subscriptions", set()))
                }
                for info in self.connection_info.values()
            ]
        }

# Global WebSocket manager instance
ws_manager = WebSocketManager()