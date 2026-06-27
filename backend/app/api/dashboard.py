from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import Optional
from datetime import datetime, timedelta, timezone

from app.database.connection import get_db
from app.database.models import (
    ScanJob, ScanStatus, HostResult,
    Vulnerability, SeverityLevel, Asset, User
)
from app.api.auth import get_current_user

router = APIRouter(prefix="/dashboard", tags=["Dashboard"])


def _user_scan_ids(db: Session, user: User):
    scans = db.query(ScanJob.id).filter(ScanJob.owner_id == user.id).subquery()
    return scans


def _user_host_ids(db: Session, user: User):
    scan_ids = db.query(ScanJob.id).filter(ScanJob.owner_id == user.id).subquery()
    hosts = db.query(HostResult.id).filter(HostResult.scan_id.in_(scan_ids)).subquery()
    return hosts


@router.get("/summary")
def summary(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    is_admin = current_user.role == "admin"

    scan_q = db.query(ScanJob) if is_admin else db.query(ScanJob).filter(ScanJob.owner_id == current_user.id)
    scan_ids = [s.id for s in scan_q.with_entities(ScanJob.id).all()]

    host_q = db.query(HostResult) if is_admin else db.query(HostResult).filter(HostResult.scan_id.in_(scan_ids))
    host_ids = [h.id for h in host_q.with_entities(HostResult.id).all()]

    vuln_q = db.query(Vulnerability) if is_admin else db.query(Vulnerability).filter(Vulnerability.host_id.in_(host_ids))

    return {
        "total_scans":     scan_q.count(),
        "completed_scans": scan_q.filter(ScanJob.status == ScanStatus.COMPLETED).count(),
        "total_hosts":     host_q.count(),
        "total_assets":    db.query(Asset).count(),
        "vulnerabilities": {
            "total":    vuln_q.count(),
            "critical": vuln_q.filter(Vulnerability.severity == SeverityLevel.CRITICAL).count(),
            "high":     vuln_q.filter(Vulnerability.severity == SeverityLevel.HIGH).count(),
            "medium":   vuln_q.filter(Vulnerability.severity == SeverityLevel.MEDIUM).count(),
            "low":      vuln_q.filter(Vulnerability.severity == SeverityLevel.LOW).count(),
        }
    }


@router.get("/recent-scans")
def recent_scans(
    limit:        int     = 10,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    query = db.query(ScanJob)
    if current_user.role != "admin":
        query = query.filter(ScanJob.owner_id == current_user.id)

    scans = query.order_by(ScanJob.created_at.desc()).limit(limit).all()
    return [
        {
            "scan_id":      s.id,
            "targets":      s.targets,
            "profile":      s.scan_profile,
            "status":       s.status,
            "progress":     s.progress,
            "hosts_found":  db.query(func.count(HostResult.id)).filter(
                                HostResult.scan_id == s.id).scalar(),
            "created_at":   s.created_at,
            "completed_at": s.completed_at,
        }
        for s in scans
    ]


@router.get("/top-risky-hosts")
def top_risky_hosts(
    limit:        int     = 10,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    query = db.query(HostResult)
    if current_user.role != "admin":
        scan_ids = db.query(ScanJob.id).filter(ScanJob.owner_id == current_user.id).subquery()
        query = query.filter(HostResult.scan_id.in_(scan_ids))

    hosts = query.order_by(HostResult.risk_score.desc()).limit(limit).all()
    return [
        {
            "ip":         h.ip_address,
            "hostname":   h.hostname,
            "os":         h.os_name,
            "risk_score": h.risk_score,
            "grade":      h.security_grade,
            "open_ports": db.query(func.count(HostResult.id)).filter(
                              HostResult.id == h.id).scalar(),
            "vulns":      db.query(func.count(Vulnerability.id)).filter(
                              Vulnerability.host_id == h.id).scalar(),
        }
        for h in hosts
    ]


@router.get("/severity-breakdown")
def severity_breakdown(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    if current_user.role == "admin":
        vuln_q = db.query(Vulnerability)
    else:
        scan_ids = db.query(ScanJob.id).filter(ScanJob.owner_id == current_user.id).subquery()
        host_ids = db.query(HostResult.id).filter(HostResult.scan_id.in_(scan_ids)).subquery()
        vuln_q   = db.query(Vulnerability).filter(Vulnerability.host_id.in_(host_ids))

    return [
        {"severity": "critical", "count": vuln_q.filter(Vulnerability.severity == SeverityLevel.CRITICAL).count()},
        {"severity": "high",     "count": vuln_q.filter(Vulnerability.severity == SeverityLevel.HIGH).count()},
        {"severity": "medium",   "count": vuln_q.filter(Vulnerability.severity == SeverityLevel.MEDIUM).count()},
        {"severity": "low",      "count": vuln_q.filter(Vulnerability.severity == SeverityLevel.LOW).count()},
    ]


@router.get("/vuln-trend")
def vuln_trend(
    days:         int     = 7,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    if current_user.role == "admin":
        vuln_q = db.query(Vulnerability)
    else:
        scan_ids = db.query(ScanJob.id).filter(ScanJob.owner_id == current_user.id).subquery()
        host_ids = db.query(HostResult.id).filter(HostResult.scan_id.in_(scan_ids)).subquery()
        vuln_q   = db.query(Vulnerability).filter(Vulnerability.host_id.in_(host_ids))

    result = []
    for i in range(days):
        day_start = datetime.now(timezone.utc) - timedelta(days=i+1)
        day_end   = datetime.now(timezone.utc) - timedelta(days=i)
        count = vuln_q.filter(
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
    q:            Optional[str] = Query(None, max_length=100),
    severity:     Optional[str] = Query(None),
    profile:      Optional[str] = Query(None),
    status:       Optional[str] = Query(None),
    db:           Session       = Depends(get_db),
    current_user: User          = Depends(get_current_user)
):
    results = {"scans": [], "hosts": [], "vulnerabilities": []}

    scan_q = db.query(ScanJob)
    if current_user.role != "admin":
        scan_q = scan_q.filter(ScanJob.owner_id == current_user.id)

    scan_ids = [s.id for s in scan_q.with_entities(ScanJob.id).all()]
    host_q   = db.query(HostResult).filter(HostResult.scan_id.in_(scan_ids))

    if q:
        results["hosts"] = [
            {"ip": h.ip_address, "hostname": h.hostname,
             "scan_id": h.scan_id, "risk_score": h.risk_score}
            for h in host_q.filter(
                HostResult.ip_address.ilike(f"%{q}%") |
                HostResult.hostname.ilike(f"%{q}%")
            ).limit(20).all()
        ]

        host_ids = [h.id for h in host_q.with_entities(HostResult.id).all()]
        vuln_q   = db.query(Vulnerability).filter(Vulnerability.host_id.in_(host_ids))
        if severity:
            vuln_q = vuln_q.filter(Vulnerability.severity == severity)
        results["vulnerabilities"] = [
            {"cve_id": v.cve_id, "severity": v.severity,
             "cvss": v.cvss_v3_score, "host_id": v.host_id}
            for v in vuln_q.filter(
                Vulnerability.cve_id.ilike(f"%{q}%")
            ).limit(20).all()
        ]

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
    limit:        int           = 20,
    offset:       int           = 0,
    status:       Optional[str] = Query(None),
    db:           Session       = Depends(get_db),
    current_user: User          = Depends(get_current_user)
):
    query = db.query(ScanJob)
    if current_user.role != "admin":
        query = query.filter(ScanJob.owner_id == current_user.id)
    if status:
        query = query.filter(ScanJob.status == status)

    total = query.count()
    scans = query.order_by(ScanJob.created_at.desc()).offset(offset).limit(limit).all()
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
                "hosts_found":  db.query(func.count(HostResult.id)).filter(
                                    HostResult.scan_id == s.id).scalar(),
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
    scan_id_a:    int,
    scan_id_b:    int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    def _check_access(scan_id):
        scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
        if not scan:
            return None
        if current_user.role != "admin" and scan.owner_id != current_user.id:
            return None
        return scan

    if not _check_access(scan_id_a) or not _check_access(scan_id_b):
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Scan not found or access denied")

    hosts_a = {h.ip_address: h for h in db.query(HostResult).filter(
        HostResult.scan_id == scan_id_a).all()}
    hosts_b = {h.ip_address: h for h in db.query(HostResult).filter(
        HostResult.scan_id == scan_id_b).all()}

    all_ips = set(hosts_a) | set(hosts_b)
    return {
        "scan_a": scan_id_a,
        "scan_b": scan_id_b,
        "comparison": [
            {
                "ip":           ip,
                "in_a":         ip in hosts_a,
                "in_b":         ip in hosts_b,
                "risk_a":       hosts_a[ip].risk_score if ip in hosts_a else None,
                "risk_b":       hosts_b[ip].risk_score if ip in hosts_b else None,
                "grade_a":      hosts_a[ip].security_grade if ip in hosts_a else None,
                "grade_b":      hosts_b[ip].security_grade if ip in hosts_b else None,
                "vulns_a":      len(hosts_a[ip].vulnerabilities) if ip in hosts_a else 0,
                "vulns_b":      len(hosts_b[ip].vulnerabilities) if ip in hosts_b else 0,
            }
            for ip in sorted(all_ips)
        ]
    }
