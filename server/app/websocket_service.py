from fastapi import WebSocket, WebSocketDisconnect

from repository import Repository
from ws.websocket_manager import WebsocketManager


class WebSocketService:
    def __init__(self, repository: Repository, websocket_manager: WebsocketManager):
        self._repository = repository
        self._manager = websocket_manager
        self._active_connections: dict[str, set[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, session_id: str, ws_type: str) -> None:
        if session_id not in self._active_connections:
            self._active_connections[session_id] = set()
        self._active_connections[session_id].add(websocket)

        async with self._manager.subscribe(channel=f"{ws_type}:{session_id}") as subscriber:
            try:
                async for event in subscriber:
                    # We technically send a json, but it is in string format. Using "send_json" would
                    # result in redundant serialization as it was done so before publishing to redis.
                    await websocket.send_text(event.message)
            except WebSocketDisconnect:
                #TODO: remove user from session?
                self._active_connections[session_id].remove(websocket)
                if not self._active_connections[session_id]:
                    del self._active_connections[session_id]


    async def disconnect(self, session_id: str) -> None:
        if session_id not in self._active_connections:
            return

        for websocket in self._active_connections[session_id]:
            try:
                await websocket.close(code=1001, reason='Session ended.')
            except WebSocketDisconnect as e:
                print(f"WebSocket for session {session_id} already disconnected: {e}")
        del self._active_connections[session_id]