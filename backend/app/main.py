from fastapi import FastAPI, WebSocket, WebSocketDisconnect, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.middleware.httpsredirect import HTTPSRedirectMiddleware
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from contextlib import asynccontextmanager
from app.database.connection import init_db
from app.api import scan, assets, dashboard, auth
import os, json, logging
from dotenv import load_dotenv
from typing import Dict, List

load_dotenv()

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

# ── Rate Limiter ────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address)

# ── WebSocket Manager ───────────────────────────────────────
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

# ── Lifespan ────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting NRVS — initializing DB...")
    init_db()
    logger.info("DB ready")
    yield
    logger.info("NRVS shutting down")

# ── App ─────────────────────────────────────────────────────
app = FastAPI(
    title="NRVS — Network & Vulnerability Scanner",
    version="2.0.0",
    docs_url="/api/docs" if os.getenv("ENV", "development") != "production" else None,
    redoc_url="/api/redoc" if os.getenv("ENV", "development") != "production" else None,
    lifespan=lifespan,
)

# ── Rate limit handler ──────────────────────────────────────
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# ── Env vars ────────────────────────────────────────────────
ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost,127.0.0.1").split(",")

# ── HTTPS redirect in production only ──────────────────────
if os.getenv("ENV") == "production":
    app.add_middleware(HTTPSRedirectMiddleware)

# ── Middlewares ─────────────────────────────────────────────
app.add_middleware(TrustedHostMiddleware, allowed_hosts=ALLOWED_HOSTS)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# ── Routers ─────────────────────────────────────────────────
app.include_router(auth.router)
app.include_router(scan.router)
app.include_router(assets.router)
app.include_router(dashboard.router)

# ── WebSocket with auth ─────────────────────────────────────
@app.websocket("/ws/scan/{scan_id}")
async def websocket_scan(websocket: WebSocket, scan_id: str):
    token = websocket.query_params.get("token")
    if not token:
        await websocket.close(code=1008)
        logger.warning(f"WebSocket rejected — no token for scan_id={scan_id}")
        return
    await manager.connect(websocket, scan_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, scan_id)

# ── Health check ────────────────────────────────────────────
@app.get("/api/health")
def health():
    return {
        "status": "ok",
        "service": "NRVS",
        "version": "2.0.0",
        "env": os.getenv("ENV", "development")
    }
