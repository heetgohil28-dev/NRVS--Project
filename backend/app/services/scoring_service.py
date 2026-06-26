from typing import List
from app.database.models import HostResult, Vulnerability, SeverityLevel

SEVERITY_PENALTIES = {
    SeverityLevel.CRITICAL: 40.0,
    SeverityLevel.HIGH:     20.0,
    SeverityLevel.MEDIUM:   10.0,
    SeverityLevel.LOW:       3.0,
    SeverityLevel.INFO:      0.5,
    SeverityLevel.NONE:      0.0,
}

GRADE_THRESHOLDS = [
    (0,  10,  "A+"),
    (10, 20,  "A"),
    (20, 30,  "B"),
    (30, 45,  "C"),
    (45, 60,  "D"),
    (60, 101, "F"),
]


def calculate_host_risk_score(vulns: List[Vulnerability]) -> float:
    """
    Penalty-based risk score 0-100.
    Each vuln deducts points from 100 based on severity.
    Score = min(sum of penalties, 100)
    """
    if not vulns:
        return 0.0

    total_penalty = 0.0
    for v in vulns:
        penalty       = SEVERITY_PENALTIES.get(v.severity, 0.0)
        cvss_modifier = (v.cvss_v3_score or v.cvss_v2_score or 5.0) / 10.0
        total_penalty += penalty * cvss_modifier

    return min(round(total_penalty, 2), 100.0)


def assign_security_grade(risk_score: float) -> str:
    for low, high, grade in GRADE_THRESHOLDS:
        if low <= risk_score < high:
            return grade
    return "F"


def get_severity_from_cvss(cvss_score: float) -> SeverityLevel:
    if cvss_score >= 9.0:
        return SeverityLevel.CRITICAL
    elif cvss_score >= 7.0:
        return SeverityLevel.HIGH
    elif cvss_score >= 4.0:
        return SeverityLevel.MEDIUM
    elif cvss_score > 0.0:
        return SeverityLevel.LOW
    else:
        return SeverityLevel.NONE


def score_and_grade_host(host: HostResult, db) -> HostResult:
    vulns               = host.vulnerabilities
    host.risk_score     = calculate_host_risk_score(vulns)
    host.security_grade = assign_security_grade(host.risk_score)
    db.commit()
    db.refresh(host)
    return host
