from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel

from app.database.connection import get_db
from app.database.models import ScanJob, ScanStatus, HostResult
from app.services.nmap_service import scanner
from app.services.parser_service import save_scan_results
from app.services.scoring_service import score_and_grade_host

router = APIRouter(prefix="/api/scan", tags=["Scan Engine"])

class ScanRequest(BaseModel):
    targets: List[str]           # ["192.168.1.1", "10.0.0.0/24"]
    profile: Optional[str] = "standard"
    extra_args: Optional[str] = ""


class ScanResponse(BaseModel):
    scan_id: int
    status: str
    targets: list
    profile: str
    message: str

def run_scan_background(scan_id: int, targets: list, profile: str, extra_args: str, db: Session):
    try:
      
        scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
        scan.status     = ScanStatus.RUNNING
        scan.started_at = datetime.utcnow()
        scan.progress   = 10
        db.commit()

        results  = scanner.scan_targets(targets, profile, extra_args)
        raw_xml  = scanner.get_raw_xml()

        scan.raw_xml  = raw_xml
        scan.progress = 60
        db.commit()

        hosts = save_scan_results(db, scan_id, results)

        scan.progress = 80
        db.commit()

        for host in hosts:
            score_and_grade_host(host, db)

        scan.status       = ScanStatus.COMPLETED
        scan.completed_at = datetime.utcnow()
        scan.progress     = 100
        db.commit()

    except Exception as e:
        scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
        if scan:
            scan.status = ScanStatus.FAILED
            db.commit()
        raise e

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
        message = f"Scan #{scan.id} queued. Use GET /api/scan/{scan.id} to check progress."
    )


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
        raise HTTPException(status_code=400, detail=f"Scan is {scan.status}, not completed yet")

    hosts = db.query(HostResult).filter(HostResult.scan_id == scan_id).all()
    return {
        "scan_id":    scan_id,
        "total_hosts": len(hosts),
        "hosts": [
            {
                "ip":            h.ip_address,
                "hostname":      h.hostname,
                "os":            h.os_name,
                "risk_score":    h.risk_score,
                "grade":         h.security_grade,
                "open_ports":    len([p for p in h.ports if p.state == "open"]),
                "vulns_found":   len(h.vulnerabilities),
            }
            for h in hosts
        ]
    }


@router.get("/")
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
