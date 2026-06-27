from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime, timezone
from pydantic import BaseModel
import asyncio

from app.database.connection import get_db, SessionLocal
from app.database.models import ScanJob, ScanStatus, HostResult, User
from app.services.nmap_service import scanner
from app.services.parser_service import save_scan_results
from app.services.scoring_service import score_and_grade_host
from app.services.cve_service import enrich_host_vulnerabilities
from app.services.mitre_service import enrich_host_with_mitre
from app.utils.cidr_utils import parse_targets
from app.utils.nmap_args_validator import validate_custom_args
from app.utils.websocket_manager import ws_manager
from app.api.auth import get_current_user
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/scan", tags=["Scan Engine"])


class ScanRequest(BaseModel):
    targets:     List[str]
    profile:     Optional[str] = "standard"
    custom_args: Optional[str] = ""


class ScanResponse(BaseModel):
    scan_id:        int
    status:         str
    targets:        list
    expanded_count: int
    profile:        str
    custom_args:    str
    message:        str


def run_scan_background(scan_id: int, targets: list, profile: str, custom_args: str = ""):
    db = SessionLocal()
    try:
        async def _run():
            try:
                scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
                scan.status     = ScanStatus.RUNNING
                scan.started_at = datetime.now(timezone.utc)
                scan.progress   = 10
                db.commit()
                await ws_manager.broadcast_progress(
                    str(scan_id), 10, "running", "Nmap scan started"
                )

                results = scanner.scan_targets(targets, profile, custom_args)
                raw_xml = scanner.get_raw_xml()

                scan.raw_xml  = raw_xml
                scan.progress = 40
                db.commit()
                await ws_manager.broadcast_progress(
                    str(scan_id), 40, "running",
                    f"Scan complete. Found {len(results['hosts'])} hosts. Parsing..."
                )

                hosts = save_scan_results(db, scan_id, results)

                for h in hosts:
                    await ws_manager.broadcast_host_found(str(scan_id), {
                        "ip":       h.ip_address,
                        "hostname": h.hostname,
                        "os":       h.os_name,
                        "ports":    len(h.ports),
                    })

                scan.progress = 60
                db.commit()
                await ws_manager.broadcast_progress(
                    str(scan_id), 60, "running", "Enriching CVE data..."
                )

                for host in hosts:
                    await enrich_host_vulnerabilities(host, db)

                scan.progress = 80
                db.commit()
                await ws_manager.broadcast_progress(
                    str(scan_id), 80, "running", "Mapping MITRE ATT&CK and scoring..."
                )

                for host in hosts:
                    enrich_host_with_mitre(host.id, db)
                    score_and_grade_host(host, db)

                scan.status       = ScanStatus.COMPLETED
                scan.completed_at = datetime.now(timezone.utc)
                scan.progress     = 100
                db.commit()
                await ws_manager.broadcast_progress(
                    str(scan_id), 100, "completed",
                    f"Done. {len(hosts)} hosts found.",
                    data={"total_hosts": len(hosts)}
                )
                logger.info("Scan #%s completed — %s hosts", scan_id, len(hosts))

            except Exception as e:
                logger.error("Scan #%s failed: %s", scan_id, str(e))
                scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
                if scan:
                    scan.status = ScanStatus.FAILED
                    db.commit()
                await ws_manager.broadcast_error(str(scan_id), str(e))

        asyncio.run(_run())
    finally:
        db.close()


@router.post("/start", response_model=ScanResponse, status_code=status.HTTP_202_ACCEPTED)
def start_scan(
    req:              ScanRequest,
    background_tasks: BackgroundTasks,
    db:               Session = Depends(get_db),
    current_user:     User    = Depends(get_current_user),
):
    try:
        custom_args = validate_custom_args(req.custom_args or "")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))

    parsed = parse_targets(req.targets)
    if parsed["errors"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=parsed["errors"])
    if not parsed["expanded"]:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="No valid targets")

    scan = ScanJob(
        owner_id     = current_user.id,
        targets      = req.targets,
        scan_profile = req.profile,
        status       = ScanStatus.PENDING,
        options      = {"expanded_targets": parsed["expanded"], "custom_args": custom_args},
    )
    db.add(scan)
    db.commit()
    db.refresh(scan)

    background_tasks.add_task(
        run_scan_background,
        scan.id, parsed["expanded"], req.profile, custom_args
    )

    logger.info("Scan #%s queued by %s", scan.id, current_user.username)
    return ScanResponse(
        scan_id        = scan.id,
        status         = "pending",
        targets        = req.targets,
        expanded_count = parsed["total"],
        profile        = req.profile,
        custom_args    = custom_args,
        message        = (
            f"Scan #{scan.id} queued. "
            f"{parsed['total']} hosts to scan. "
            f"WebSocket: ws://localhost:8000/ws/scan/{scan.id}"
        ),
    )


@router.get("/list")
def list_scans(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
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
    scan_id:      int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
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
    scan_id:      int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
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
                "vulnerabilities": [
                    {
                        "cve_id":           v.cve_id,
                        "severity":         v.severity.value if v.severity else None,
                        "cvss_v3":          v.cvss_v3_score,
                        "cvss_v2":          v.cvss_v2_score,
                        "description":      v.description,
                        "mitre_tactics":    v.mitre_tactics,
                        "mitre_techniques": v.mitre_techniques,
                        "exploit_available": v.exploit_available,
                        "recommendation":   v.recommendation,
                    }
                    for v in h.vulnerabilities
                ],
            }
            for h in hosts
        ],
    }


@router.delete("/{scan_id}", status_code=status.HTTP_200_OK)
def delete_scan(
    scan_id:      int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user),
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
