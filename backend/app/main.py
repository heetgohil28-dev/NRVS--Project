from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
from app.database.connection import init_db
from app.api import scan, assets, dashboard, reports
from app.utils.websocket_manager import ws_manager
import os, json
from dotenv import load_dotenv

load_dotenv()

ALLOWED_ORIGINS = os.getenv("CORS_ORIGINS", "http://localhost:3000").split(",")


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting NRVS — initializing DB...")
    init_db()
    os.makedirs("app/static/screenshots", exist_ok=True)
    os.makedirs("/tmp/nrvs_reports", exist_ok=True)
    print("DB ready")
    yield
    print("NRVS shutting down")


app = FastAPI(
    title="NRVS — Network & Vulnerability Scanner",
    version="2.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["Authorization", "Content-Type"],
)

# Static files for screenshots
app.mount("/static", StaticFiles(directory="app/static"), name="static")

app.include_router(scan.router)
app.include_router(assets.router)
app.include_router(dashboard.router)
app.include_router(reports.router)


@app.websocket("/ws/scan/{scan_id}")
async def websocket_scan(websocket: WebSocket, scan_id: str):
    await ws_manager.connect(websocket, scan_id)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        ws_manager.disconnect(websocket, scan_id)


@app.get("/api/health")
def health():
    return {
        "status":          "ok",
        "service":         "NRVS",
        "version":         "2.0.0",
        "active_ws_scans": ws_manager.get_active_scans()
    }
