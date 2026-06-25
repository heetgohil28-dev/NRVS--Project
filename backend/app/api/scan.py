from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import asyncio

from app.database.connection import get_db
from app.database.models import ScanJob, ScanStatus, HostResult
from app.services.nmap_service import scanner
from app.services.parser_service import save_scan_results
from app.services.scoring_service import score_and_grade_host

router = APIRouter(prefix="/api/scan", tags=["Scan Engine"])


class ScanRequest(BaseModel):
    targets: List[str]
    profile: Optional[str] = "standard"
    extra_args: Optional[str] = ""


class ScanResponse(BaseModel):
    scan_id: int
    status: str
    targets: list
    profile: str
    message: str


def run_scan_background(
    scan_id: int,
    targets: list,
    profile: str,
    extra_args: str,
    db: Session
):
    async def _run():
        from app.main import manager

        try:
            scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
            scan.status     = ScanStatus.RUNNING
            scan.started_at = datetime.utcnow()
            scan.progress   = 10
            db.commit()
            await manager.broadcast(str(scan_id), {
                "scan_id":  scan_id,
                "progress": 10,
                "status":   "running",
                "message":  "Nmap scan started"
            })

            results = scanner.scan_targets(targets, profile, extra_args)
            raw_xml = scanner.get_raw_xml()

            scan.raw_xml  = raw_xml
            scan.progress = 60
            db.commit()
            await manager.broadcast(str(scan_id), {
                "scan_id":  scan_id,
                "progress": 60,
                "status":   "running",
                "message":  f"Scan complete. Parsing {len(results['hosts'])} hosts..."
            })

            hosts = save_scan_results(db, scan_id, results)

            scan.progress = 80
            db.commit()
            await manager.broadcast(str(scan_id), {
                "scan_id":  scan_id,
                "progress": 80,
                "status":   "running",
                "message":  "Scoring hosts..."
            })

            for host in hosts:
                score_and_grade_host(host, db)

            scan.status       = ScanStatus.COMPLETED
            scan.completed_at = datetime.utcnow()
            scan.progress     = 100
            db.commit()
            await manager.broadcast(str(scan_id), {
                "scan_id":  scan_id,
                "progress": 100,
                "status":   "completed",
                "message":  f"Done. {len(hosts)} hosts found."
            })

        except Exception as e:
            scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
            if scan:
                scan.status = ScanStatus.FAILED
                db.commit()
            from app.main import manager as m
            await m.broadcast(str(scan_id), {
                "scan_id":  scan_id,
                "progress": 0,
                "status":   "failed",
                "message":  str(e)
            })

    asyncio.run(_run())


@router.post("/start", response_model=ScanResponse, status_code=202)
def start_scan(
    req: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db)
):
    scan = ScanJob(
        owner_id     = 1,
        targets      = req.targets,
        scan_profile = req.profile,
        status       = ScanStatus.PENDING,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    background_tasks.add_task(
        run_scan_background,
        scan.id, req.targets, req.profile, req.extra_args, db
    )

    return ScanResponse(
        scan_id = scan.id,
        status  = "pending",
        targets = req.targets,
        profile = req.profile,
        message = (
            f"Scan #{scan.id} queued. "
            f"Connect WebSocket: ws://localhost:8000/ws/scan/{scan.id}"
        )
    )


@router.get("/list")
def list_scans(db: Session = Depends(get_db)):
    scans = db.query(ScanJob).order_by(ScanJob.created_at.desc()).limit(50).all()
    return [
        {
            "scan_id":  s.id,
            "status":   s.status,
            "targets":  s.targets,
            "profile":  s.scan_profile,
            "progress": s.progress,
            "created":  s.created_at,
        }
        for s in scans
    ]


@router.get("/{scan_id}")
def get_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    return {
        "scan_id":      scan.id,
        "status":       scan.status,
        "progress":     scan.progress,
        "targets":      scan.targets,
        "profile":      scan.scan_profile,
        "started_at":   scan.started_at,
        "completed_at": scan.completed_at,
    }


@router.get("/{scan_id}/results")
def get_scan_results(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.status != ScanStatus.COMPLETED:
        raise HTTPException(status_code=400, detail=f"Scan is {scan.status}")

    hosts = db.query(HostResult).filter(HostResult.scan_id == scan_id).all()
    return {
        "scan_id":     scan_id,
        "total_hosts": len(hosts),
        "hosts": [
            {
                "ip":         h.ip_address,
                "hostname":   h.hostname,
                "os":         h.os_name,
                "risk_score": h.risk_score,
                "grade":      h.security_grade,
                "open_ports": len([p for p in h.ports if p.state == "open"]),
                "vulns":      len(h.vulnerabilities),
                "ports": [
                    {
                        "port":     p.port_number,
                        "protocol": p.protocol,
                        "state":    p.state,
                        "service":  p.service_name,
                        "version":  p.service_version,
                        "product":  p.service_product,
                        "cpe":      p.cpe,
                    }
                    for p in h.ports
                ]
            }
            for h in hosts
        ]
    }


@router.delete("/{scan_id}")
def delete_scan(scan_id: int, db: Session = Depends(get_db)):
    scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    db.delete(scan)
    db.commit()
    return {"message": f"Scan #{scan_id} deleted"}
