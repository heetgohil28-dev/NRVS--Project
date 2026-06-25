from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone

from app.database.connection import get_db
from app.database.models import ScanJob, ScanStatus, HostResult, User
from app.schemas.scan_schemas import ScanRequest, ScanResponse
from app.services.nmap_service import scanner
from app.services.parser_service import save_scan_results
from app.services.scoring_service import score_and_grade_host
from app.utils.security import get_current_user
from app.utils.cidr_utils import validate_targets
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scan", tags=["Scan Engine"])


def run_scan_background(scan_id: int, targets: list, profile: str, db: Session):
    try:
        scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
        scan.status     = ScanStatus.RUNNING
        scan.started_at = datetime.now(timezone.utc)
        scan.progress   = 10
        db.commit()

        results = scanner.scan_targets(targets, profile)
        raw_xml = scanner.get_raw_xml()

        scan.raw_xml  = raw_xml
        scan.progress = 60
        db.commit()

        hosts = save_scan_results(db, scan_id, results)

        scan.progress = 80
        db.commit()

        for host in hosts:
            score_and_grade_host(host, db)

        scan.status       = ScanStatus.COMPLETED
        scan.completed_at = datetime.now(timezone.utc)
        scan.progress     = 100
        db.commit()
        logger.info("Scan #%s completed — %s hosts found", scan_id, len(hosts))

    except Exception as e:
        logger.error("Scan #%s failed: %s", scan_id, str(e))
        scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
        if scan:
            scan.status = ScanStatus.FAILED
            db.commit()


@router.post("/start", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
def start_scan(
    req: ScanRequest,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        validated_targets = validate_targets(req.targets)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    scan = ScanJob(
        owner_id     = current_user.id,
        targets      = validated_targets,
        scan_profile = req.profile,
        status       = ScanStatus.PENDING,
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    background_tasks.add_task(
        run_scan_background,
        scan.id, validated_targets, req.profile, db
    )

    logger.info("Scan #%s queued by user %s", scan.id, current_user.username)
    return ScanResponse(
        scan_id = scan.id,
        status  = "pending",
        targets = validated_targets,
        profile = req.profile,
        message = f"Scan #{scan.id} queued",
    )


@router.get("/list")
def list_scans(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(ScanJob)
    if current_user.role != "admin":
        query = query.filter(ScanJob.owner_id == current_user.id)

    scans = query.order_by(ScanJob.created_at.desc()).limit(50).all()
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
def get_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    if current_user.role != "admin" and scan.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

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
def get_scan_results(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    if current_user.role != "admin" and scan.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if scan.status != ScanStatus.COMPLETED:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Scan is {scan.status}")

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
                ],
            }
            for h in hosts
        ],
    }


@router.delete("/{scan_id}", status_code=status.HTTP_200_OK)
def delete_scan(
    scan_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    if current_user.role != "admin" and scan.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    db.delete(scan)
    db.commit()
    logger.info("Scan #%s deleted by %s", scan_id, current_user.username)
    return {"message": f"Scan #{scan_id} deleted"}
