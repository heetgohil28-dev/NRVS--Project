from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from app.database.connection import get_db
from app.database.models import Report, ScanJob, User
from app.services.report_service import (
    generate_html_report,
    generate_pdf_report,
    generate_json_report,
)
from app.utils.security import get_current_user
import os
import logging

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/reports", tags=["Reports"])


def _verify_scan_access(scan_id: int, current_user: User, db: Session) -> ScanJob:
    scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Scan not found")
    if current_user.role != "admin" and scan.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return scan


@router.post("/generate/{scan_id}")
def generate_report(
    scan_id: int,
    report_type: str = "json",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    _verify_scan_access(scan_id, current_user, db)

    if report_type not in ("html", "pdf", "json"):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="report_type must be html, pdf, or json",
        )

    try:
        if report_type == "html":
            report = generate_html_report(scan_id, current_user.id, db)
        elif report_type == "pdf":
            report = generate_pdf_report(scan_id, current_user.id, db)
        else:
            report = generate_json_report(scan_id, current_user.id, db)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        logger.error("Report generation failed: %s", str(e))
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Report generation failed")

    return {
        "report_id":   report.id,
        "scan_id":     scan_id,
        "report_type": report_type,
        "file_size":   report.file_size,
        "created_at":  report.created_at,
    }


@router.get("/download/{report_id}")
def download_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if current_user.role != "admin" and report.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    if not report.file_path or not os.path.exists(report.file_path):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report file not found on disk")

    media_types = {"html": "text/html", "pdf": "application/pdf", "json": "application/json"}
    return FileResponse(
        path=report.file_path,
        media_type=media_types.get(report.report_type, "application/octet-stream"),
        filename=os.path.basename(report.file_path),
    )


@router.get("/list")
def list_reports(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Report)
    if current_user.role != "admin":
        query = query.filter(Report.owner_id == current_user.id)

    reports = query.order_by(Report.created_at.desc()).limit(50).all()
    return [
        {
            "report_id":   r.id,
            "scan_id":     r.scan_id,
            "report_type": r.report_type,
            "file_size":   r.file_size,
            "total_hosts": r.total_hosts,
            "total_vulns": r.total_vulns,
            "created_at":  r.created_at,
        }
        for r in reports
    ]


@router.delete("/{report_id}", status_code=status.HTTP_200_OK)
def delete_report(
    report_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    report = db.query(Report).filter(Report.id == report_id).first()
    if not report:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Report not found")
    if current_user.role != "admin" and report.owner_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")

    if report.file_path and os.path.exists(report.file_path):
        os.remove(report.file_path)

    db.delete(report)
    db.commit()
    logger.info("Report #%s deleted by %s", report_id, current_user.username)
    return {"message": f"Report #{report_id} deleted"}
