from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime, timedelta

from app.database.connection import get_db
from app.database.models import (
    ScanJob, ScanStatus, HostResult,
    Vulnerability, SeverityLevel, Asset
)

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    return {
        "total_scans":     db.query(ScanJob).count(),
        "completed_scans": db.query(ScanJob).filter(
                               ScanJob.status == ScanStatus.COMPLETED).count(),
        "total_hosts":     db.query(HostResult).count(),
        "total_assets":    db.query(Asset).count(),
        "vulnerabilities": {
            "total":    db.query(Vulnerability).count(),
            "critical": db.query(Vulnerability).filter(
                            Vulnerability.severity == SeverityLevel.CRITICAL).count(),
            "high":     db.query(Vulnerability).filter(
                            Vulnerability.severity == SeverityLevel.HIGH).count(),
            "medium":   db.query(Vulnerability).filter(
                            Vulnerability.severity == SeverityLevel.MEDIUM).count(),
            "low":      db.query(Vulnerability).filter(
                            Vulnerability.severity == SeverityLevel.LOW).count(),
        }
    }


@router.get("/recent-scans")
def recent_scans(limit: int = 10, db: Session = Depends(get_db)):
    scans = db.query(ScanJob).order_by(
        ScanJob.created_at.desc()
    ).limit(limit).all()
    return [
        {
            "scan_id":      s.id,
            "targets":      s.targets,
            "profile":      s.scan_profile,
            "status":       s.status,
            "progress":     s.progress,
            "hosts_found":  len(s.hosts),
            "created_at":   s.created_at,
            "completed_at": s.completed_at,
        }
        for s in scans
    ]


@router.get("/top-risky-hosts")
def top_risky_hosts(limit: int = 10, db: Session = Depends(get_db)):
    hosts = db.query(HostResult).order_by(
        HostResult.risk_score.desc()
    ).limit(limit).all()
    return [
        {
            "ip":         h.ip_address,
            "hostname":   h.hostname,
            "os":         h.os_name,
            "risk_score": h.risk_score,
            "grade":      h.security_grade,
            "open_ports": len([p for p in h.ports if p.state == "open"]),
            "vulns":      len(h.vulnerabilities),
        }
        for h in hosts
    ]


@router.get("/severity-breakdown")
def severity_breakdown(db: Session = Depends(get_db)):
    return [
        {"severity": "critical", "count": db.query(Vulnerability).filter(
            Vulnerability.severity == SeverityLevel.CRITICAL).count()},
        {"severity": "high",     "count": db.query(Vulnerability).filter(
            Vulnerability.severity == SeverityLevel.HIGH).count()},
        {"severity": "medium",   "count": db.query(Vulnerability).filter(
            Vulnerability.severity == SeverityLevel.MEDIUM).count()},
        {"severity": "low",      "count": db.query(Vulnerability).filter(
            Vulnerability.severity == SeverityLevel.LOW).count()},
    ]


@router.get("/vuln-trend")
def vuln_trend(days: int = 7, db: Session = Depends(get_db)):
    result = []
    for i in range(days):
        day_start = datetime.utcnow() - timedelta(days=i+1)
        day_end   = datetime.utcnow() - timedelta(days=i)
        count = db.query(Vulnerability).filter(
            Vulnerability.created_at >= day_start,
            Vulnerability.created_at <  day_end
        ).count()
        result.append({
            "date":  day_start.strftime("%Y-%m-%d"),
            "count": count
        })
    return list(reversed(result))


@router.get("/search")
def search(
    q:        Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    profile:  Optional[str] = Query(None),
    status:   Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    results = {"scans": [], "hosts": [], "vulnerabilities": []}

    if q:
        hosts = db.query(HostResult).filter(
            HostResult.ip_address.ilike(f"%{q}%") |
            HostResult.hostname.ilike(f"%{q}%")
        ).limit(20).all()
        results["hosts"] = [
            {"ip": h.ip_address, "hostname": h.hostname,
             "scan_id": h.scan_id, "risk_score": h.risk_score}
            for h in hosts
        ]

        vulns = db.query(Vulnerability).filter(
            Vulnerability.cve_id.ilike(f"%{q}%")
        ).limit(20).all()
        results["vulnerabilities"] = [
            {"cve_id": v.cve_id, "severity": v.severity,
             "cvss": v.cvss_v3_score, "host_id": v.host_id}
            for v in vulns
        ]

    scan_q = db.query(ScanJob)
    if profile:
        scan_q = scan_q.filter(ScanJob.scan_profile == profile)
    if status:
        scan_q = scan_q.filter(ScanJob.status == status)
    results["scans"] = [
        {"scan_id": s.id, "status": s.status,
         "targets": s.targets, "profile": s.scan_profile}
        for s in scan_q.limit(20).all()
    ]
    return results


@router.get("/scan-history")
def scan_history(
    limit:  int = 20,
    offset: int = 0,
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db)
):
    q = db.query(ScanJob)
    if status:
        q = q.filter(ScanJob.status == status)
    total = q.count()
    scans = q.order_by(ScanJob.created_at.desc()).offset(offset).limit(limit).all()
    return {
        "total":  total,
        "offset": offset,
        "limit":  limit,
        "scans": [
            {
                "scan_id":      s.id,
                "targets":      s.targets,
                "profile":      s.scan_profile,
                "status":       s.status,
                "hosts_found":  len(s.hosts),
                "started_at":   s.started_at,
                "completed_at": s.completed_at,
                "duration_sec": (
                    (s.completed_at - s.started_at).seconds
                    if s.completed_at and s.started_at else None
                ),
            }
            for s in scans
        ]
    }


@router.get("/compare/{scan_id_a}/{scan_id_b}")
def compare_scans(
    scan_id_a: int,
    scan_id_b: int,
    db: Session = Depends(get_db)
):
    hosts_a = {h.ip_address: h for h in db.query(HostResult).filter(
        HostResult.scan_id == scan_id_a).all()}
    hosts_b = {h.ip_address: h for h in db.query(HostResult).filter(
        HostResult.scan_id == scan_id_b).all()}

    new_hosts     = [ip for ip in hosts_b if ip not in hosts_a]
    removed_hosts = [ip for ip in hosts_a if ip not in hosts_b]
    common        = [ip for ip in hosts_a if ip in hosts_b]

    risk_changes = []
    for ip in common:
        old = hosts_a[ip].risk_score
        new = hosts_b[ip].risk_score
        if abs(new - old) > 0.5:
            risk_changes.append({
                "ip":        ip,
                "old_score": old,
                "new_score": new,
                "delta":     round(new - old, 2)
            })

    return {
        "scan_a":        scan_id_a,
        "scan_b":        scan_id_b,
        "new_hosts":     new_hosts,
        "removed_hosts": removed_hosts,
        "common_hosts":  len(common),
        "risk_changes":  risk_changes,
        "summary": {
            "hosts_added":   len(new_hosts),
            "hosts_removed": len(removed_hosts),
            "hosts_changed": len(risk_changes),
        }
    }
