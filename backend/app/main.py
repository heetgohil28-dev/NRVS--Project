from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from contextlib import asynccontextmanager
from app.database.connection import init_db
<<<<<<< HEAD
from app.api import auth, scan
from dotenv import load_dotenv
import logging
import os

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)
=======
from app.api import scan, assets, dashboard, auth
import os, json
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()

ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")


class ConnectionManager:
    def __init__(self):
        self.active: Dict[str, List[WebSocket]] = {}

    async def connect(self, websocket: WebSocket, scan_id: str):
        await websocket.accept()
        self.active.setdefault(scan_id, []).append(websocket)

    def disconnect(self, websocket: WebSocket, scan_id: str):
        if scan_id in self.active:
            self.active[scan_id].remove(websocket)

    async def broadcast(self, scan_id: str, data: dict):
        dead = []
        for ws in self.active.get(scan_id, []):
            try:
                await ws.send_text(json.dumps(data))
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.active[scan_id].remove(ws)


manager = ConnectionManager()
>>>>>>> origin/heet-scan-engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting NRVS — initializing DB...")
    init_db()
    logger.info("DB ready")
    yield
    logger.info("NRVS shutting down")



app = FastAPI(
    title="NRVS — Network & Vulnerability Scanner",
    version="2.0.0",
    docs_url="/api/docs" if os.getenv("ENV", "development") != "production" else None,
    redoc_url="/api/redoc" if os.getenv("ENV", "development") != "production" else None,
    lifespan=lifespan,
)

ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

<<<<<<< HEAD
app.include_router(auth.router, prefix="/api")
app.include_router(scan.router, prefix="/api")
=======
app.include_router(auth.router)
app.include_router(scan.router)
app.include_router(assets.router)
app.include_router(dashboard.router)


@app.websocket("/ws/scan/{scan_id}")
async def websocket_scan(websocket: WebSocket, scan_id: str):
    await manager.connect(websocket, scan_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, scan_id)
>>>>>>> origin/heet-scan-engine


@app.get("/api/health")
def health():
    return {"status": "ok", "service": "NRVS", "version": "2.0.0"}
