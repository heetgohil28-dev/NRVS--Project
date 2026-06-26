from fastapi import WebSocket
from typing import Dict, List
import json
from datetime import datetime, timezone


class WebSocketManager:
    def __init__(self):
        self.active: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, scan_id: str):
        await websocket.accept()
        self.active.setdefault(scan_id, []).append(websocket)
        await self.send(scan_id, {
            "event":     "connected",
            "scan_id":   scan_id,
            "message":   f"Connected to scan {scan_id}",
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def disconnect(self, websocket: WebSocket, scan_id: str):
        if scan_id in self.active:
            try:
                self.active[scan_id].remove(websocket)
            except ValueError:
                pass
            if not self.active[scan_id]:
                del self.active[scan_id]

    async def send(self, scan_id: str, data: dict):
        if scan_id not in self.active:
            return
        dead = []
        for ws in self.active[scan_id]:
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active[scan_id].remove(ws)

    async def broadcast_progress(
        self,
        scan_id:  str,
        progress: int,
        status:   str,
        message:  str,
        data:     dict = None
    ):
        payload = {
            "event":     "progress",
            "scan_id":   scan_id,
            "progress":  progress,
            "status":    status,
            "message":   message,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
        if data:
            payload["data"] = data
        await self.send(scan_id, payload)

    async def broadcast_host_found(self, scan_id: str, host: dict):
        await self.send(scan_id, {
            "event":     "host_found",
            "scan_id":   scan_id,
            "host":      host,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    async def broadcast_error(self, scan_id: str, error: str):
        await self.send(scan_id, {
            "event":     "error",
            "scan_id":   scan_id,
            "message":   error,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })

    def get_active_scans(self) -> List[str]:
        return list(self.active.keys())

    def get_connection_count(self, scan_id: str) -> int:
        return len(self.active.get(scan_id, []))


ws_manager = WebSocketManager()
