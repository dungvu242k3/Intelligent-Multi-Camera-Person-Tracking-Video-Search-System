import logging
from typing import List
from fastapi import WebSocket

logger = logging.getLogger("gateway.websocket.manager")

class ConnectionManager:
    """Manages active WebSocket connections at the API Gateway level."""

    def __init__(self) -> None:
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        """Accepts a new WebSocket connection and adds it to the active pool."""
        await websocket.accept()
        self.active_connections.append(websocket)
        logger.info(f"New WebSocket connection accepted. Total active: {len(self.active_connections)}")

    def disconnect(self, websocket: WebSocket) -> None:
        """Removes a closed/disconnected WebSocket from the active pool."""
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)
            logger.info(f"WebSocket disconnected. Total active: {len(self.active_connections)}")

    @staticmethod
    async def send_personal_message(message: dict, websocket: WebSocket) -> None:
        """Sends a JSON message to a single specific client connection."""
        try:
            await websocket.send_json(message)
        except Exception as e:
            logger.error(f"Failed to send message to single client: {e}")

    async def broadcast(self, message: dict) -> None:
        """Broadcasts a JSON message to all active WebSocket clients.
        
        Optimized to handle failed/stale connections by cleanly removing them.
        """
        if not self.active_connections:
            return

        logger.debug(f"Broadcasting message to {len(self.active_connections)} clients: {message}")
        stale_connections = []
        
        for connection in self.active_connections:
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.warning(f"Failed to send broadcast message to client. Stale connection: {e}")
                stale_connections.append(connection)

        # Cleanup closed or failed connections from the active pool
        for connection in stale_connections:
            self.disconnect(connection)

# Global manager instance
manager = ConnectionManager()
