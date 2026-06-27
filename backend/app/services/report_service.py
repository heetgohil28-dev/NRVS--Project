import os
import json
import logging
from datetime import datetime, timezone
from jinja2 import Environment, FileSystemLoader, select_autoescape
from weasyprint import HTML as WeasyHTML
from sqlalchemy.orm import Session
from app.database.models import ScanJob, HostResult, Report, ScanStatus

logger = logging.getLogger(__name__)

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")
REPORTS_DIR   = os.path.join(os.path.dirname(__file__), "..", "..", "reports")

os.makedirs(REPORTS_DIR, exist_ok=True)

jinja_env = Environment(
    loader=FileSystemLoader(TEMPLATES_DIR),
    autoescape=select_autoescape(["html"]),
)


def _get_scan_context(scan_id: int, db: Session) -> dict:
    scan = db.query(ScanJob).filter(ScanJob.id == scan_id).first()
    if not scan:
        raise ValueError(f"Scan {scan_id} not found")
    if scan.status != ScanStatus.COMPLETED:
        raise ValueError(f"Scan {scan_id} is not completed")

    hosts = db.query(HostResult).filter(HostResult.scan_id == scan_id).all()

    total_vulns    = 0
    critical_count = 0
    high_count     = 0
    medium_count   = 0
    low_count      = 0

    host_data = []
    for host in hosts:
        vulns = host.vulnerabilities
        total_vulns    += len(vulns)
        for v in vulns:
            sev = v.severity.value if v.severity else ""
            if sev == "critical":   critical_count += 1
            elif sev == "high":     high_count     += 1
            elif sev == "medium":   medium_count   += 1
            elif sev == "low":      low_count      += 1

        host_data.append({
            "ip":         host.ip_address,
            "hostname":   host.hostname,
            "os":         host.os_name,
            "risk_score": host.risk_score,
            "grade":      host.security_grade,
            "open_ports": [p for p in host.ports if p.state == "open"],
            "vulns":      vulns,
        })

    duration = None
    if scan.started_at and scan.completed_at:
        duration = int((scan.completed_at - scan.started_at).total_seconds())

    return {
        "scan":           scan,
        "hosts":          host_data,
        "generated_at":   datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC"),
        "total_hosts":    len(hosts),
        "total_vulns":    total_vulns,
        "critical_count": critical_count,
        "high_count":     high_count,
        "medium_count":   medium_count,
        "low_count":      low_count,
        "duration_sec":   duration,
    }


def _save_report_record(
    db: Session,
    scan_id: int,
    owner_id: int,
    report_type: str,
    file_path: str,
    context: dict,
) -> Report:
    file_size = os.path.getsize(file_path) if os.path.exists(file_path) else 0
    report = Report(
        scan_id        = scan_id,
        owner_id       = owner_id,
        report_type    = report_type,
        file_path      = file_path,
        file_size      = file_size,
        total_hosts    = context["total_hosts"],
        total_vulns    = context["total_vulns"],
        critical_count = context["critical_count"],
        high_count     = context["high_count"],
        medium_count   = context["medium_count"],
        low_count      = context["low_count"],
    )
    db.add(report)
    db.commit()
    db.refresh(report)
    return report


def generate_html_report(scan_id: int, owner_id: int, db: Session) -> Report:
    context      = _get_scan_context(scan_id, db)
    template     = jinja_env.get_template("report_html.html")
    html_content = template.render(**context)

    filename  = f"scan_{scan_id}_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.html"
    file_path = os.path.join(REPORTS_DIR, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    logger.info("HTML report generated: %s", file_path)
    return _save_report_record(db, scan_id, owner_id, "html", file_path, context)


def generate_pdf_report(scan_id: int, owner_id: int, db: Session) -> Report:
    context      = _get_scan_context(scan_id, db)
    template     = jinja_env.get_template("report_pdf.html")
    html_content = template.render(**context)

    filename  = f"scan_{scan_id}_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.pdf"
    file_path = os.path.join(REPORTS_DIR, filename)

    WeasyHTML(string=html_content, base_url=TEMPLATES_DIR).write_pdf(file_path)

    logger.info("PDF report generated: %s", file_path)
    return _save_report_record(db, scan_id, owner_id, "pdf", file_path, context)


def generate_json_report(scan_id: int, owner_id: int, db: Session) -> Report:
    context = _get_scan_context(scan_id, db)

    json_data = {
        "scan_id":      scan_id,
        "generated_at": context["generated_at"],
        "summary": {
            "total_hosts":    context["total_hosts"],
            "total_vulns":    context["total_vulns"],
            "critical_count": context["critical_count"],
            "high_count":     context["high_count"],
            "medium_count":   context["medium_count"],
            "low_count":      context["low_count"],
            "duration_sec":   context["duration_sec"],
        },
        "hosts": [
            {
                "ip":         h["ip"],
                "hostname":   h["hostname"],
                "os":         h["os"],
                "risk_score": h["risk_score"],
                "grade":      h["grade"],
                "open_ports": [
                    {
                        "port":     p.port_number,
                        "protocol": p.protocol,
                        "service":  p.service_name,
                        "version":  p.service_version,
                    }
                    for p in h["open_ports"]
                ],
                "vulnerabilities": [
                    {
                        "cve_id":            v.cve_id,
                        "severity":          v.severity.value if v.severity else None,
                        "cvss_v3":           v.cvss_v3_score,
                        "description":       v.description,
                        "mitre_tactics":     v.mitre_tactics,
                        "mitre_techniques":  v.mitre_techniques,
                        "exploit_available": v.exploit_available,
                        "recommendation":    v.recommendation,
                    }
                    for v in h["vulns"]
                ],
            }
            for h in context["hosts"]
        ],
    }

    filename  = f"scan_{scan_id}_report_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}.json"
    file_path = os.path.join(REPORTS_DIR, filename)

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(json_data, f, indent=2, default=str)

    logger.info("JSON report generated: %s", file_path)
    return _save_report_record(db, scan_id, owner_id, "json", file_path, context)
