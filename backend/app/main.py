from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.database.connection import init_db
from app.api import scan
import os
from dotenv import load_dotenv

load_dotenv()

@asynccontextmanager
async def lifespan(app: FastAPI):
    print("Starting NRVS — initializing DB...")
    init_db()
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
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scan.router)

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "NRVS", "version": "2.0.0"}
