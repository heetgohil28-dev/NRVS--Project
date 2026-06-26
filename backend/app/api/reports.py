from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional
from pydantic import BaseModel

from app.database.connection import get_db
from app.database.models import Report, ScanJob, ScanStatus, User
from app.api.auth import get_current_user

router = APIRouter(prefix="/reports", tags=["Reports"])


class ReportRequest(BaseModel):
    scan_id:          int
    report_type:      str
    include_evidence: Optional[bool] = True


@router.post("/generate", status_code=202)
def generate_report(
    req:          ReportRequest,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    scan = db.query(ScanJob).filter(
        ScanJob.id       == req.scan_id,
        ScanJob.owner_id == current_user.id
    ).first()
    if not scan:
        raise HTTPException(status_code=404, detail="Scan not found")
    if scan.status != ScanStatus.COMPLETED:
        raise HTTPException(
            status_code=400,
            detail=f"Scan is {scan.status} — must be completed to generate report"
        )
    if req.report_type not in ["pdf", "html", "json"]:
        raise HTTPException(
            status_code=400,
            detail="report_type must be pdf, html, or json"
        )

    report = Report(
        scan_id      = req.scan_id,
        owner_id     = current_user.id,
        report_type  = req.report_type,
        total_hosts  = len(scan.hosts),
        total_vulns  = sum(len(h.vulnerabilities) for h in scan.hosts),
        critical_count = sum(
            1 for h in scan.hosts for v in h.vulnerabilities
            if str(v.severity) == "critical"
        ),
        high_count = sum(
            1 for h in scan.hosts for v in h.vulnerabilities
            if str(v.severity) == "high"
        ),
        medium_count = sum(
            1 for h in scan.hosts for v in h.vulnerabilities
            if str(v.severity) == "medium"
        ),
        low_count = sum(
            1 for h in scan.hosts for v in h.vulnerabilities
            if str(v.severity) == "low"
        ),
    )
    db.add(report)
    db.commit()
    db.refresh(report)

    return {
        "report_id":   report.id,
        "scan_id":     req.scan_id,
        "report_type": req.report_type,
        "status":      "queued",
        "message":     "Report generation queued."
    }


@router.get("/")
def list_reports(
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    reports = db.query(Report).filter(
        Report.owner_id == current_user.id
    ).order_by(Report.created_at.desc()).all()
    return [
        {
            "report_id":   r.id,
            "scan_id":     r.scan_id,
            "report_type": r.report_type,
            "total_hosts": r.total_hosts,
            "total_vulns": r.total_vulns,
            "critical":    r.critical_count,
            "high":        r.high_count,
            "file_path":   r.file_path,
            "created_at":  r.created_at,
        }
        for r in reports
    ]


@router.get("/{report_id}")
def get_report(
    report_id:    int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    report = db.query(Report).filter(
        Report.id       == report_id,
        Report.owner_id == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    return report


@router.delete("/{report_id}")
def delete_report(
    report_id:    int,
    db:           Session = Depends(get_db),
    current_user: User    = Depends(get_current_user)
):
    report = db.query(Report).filter(
        Report.id       == report_id,
        Report.owner_id == current_user.id
    ).first()
    if not report:
        raise HTTPException(status_code=404, detail="Report not found")
    db.delete(report)
    db.commit()
    return {"message": f"Report {report_id} deleted"}
