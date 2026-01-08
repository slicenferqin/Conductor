"""WebSocket endpoint handler."""

import json
import logging

from fastapi import WebSocket, WebSocketDisconnect

from .manager import connection_manager

logger = logging.getLogger(__name__)


async def websocket_endpoint(websocket: WebSocket) -> None:
    """Handle WebSocket connections."""
    await connection_manager.connect(websocket)

    try:
        while True:
            # Receive messages from client
            data = await websocket.receive_text()

            try:
                message = json.loads(data)
            except json.JSONDecodeError:
                await websocket.send_json({
                    "type": "error",
                    "payload": {"message": "Invalid JSON"}
                })
                continue

            msg_type = message.get("type")

            # Handle client commands
            if msg_type == "subscribe":
                project_id = message.get("projectId")
                if project_id:
                    await connection_manager.subscribe_to_project(websocket, project_id)
                    await websocket.send_json({
                        "type": "subscribed",
                        "payload": {"projectId": project_id}
                    })
                else:
                    await websocket.send_json({
                        "type": "error",
                        "payload": {"message": "Missing projectId"}
                    })

            elif msg_type == "unsubscribe":
                project_id = message.get("projectId")
                if project_id:
                    await connection_manager.unsubscribe_from_project(websocket, project_id)
                    await websocket.send_json({
                        "type": "unsubscribed",
                        "payload": {"projectId": project_id}
                    })

            elif msg_type == "ping":
                await websocket.send_json({"type": "pong"})

            else:
                await websocket.send_json({
                    "type": "error",
                    "payload": {"message": f"Unknown message type: {msg_type}"}
                })

    except WebSocketDisconnect:
        logger.info("WebSocket client disconnected normally")
        await connection_manager.disconnect(websocket)
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        await connection_manager.disconnect(websocket)
