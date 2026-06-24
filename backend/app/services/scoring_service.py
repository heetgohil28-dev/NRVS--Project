from typing import List
from app.database.models import HostResult, Vulnerability, SeverityLevel


# Weight per severity for composite risk score
SEVERITY_WEIGHTS = {
    SeverityLevel.CRITICAL: 10.0,
    SeverityLevel.HIGH:      7.0,
    SeverityLevel.MEDIUM:    4.0,
    SeverityLevel.LOW:       1.0,
    SeverityLevel.INFO:      0.1,
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
    Composite risk score 0-100 based on vulnerabilities found.
    Formula: sum of (cvss_score * severity_weight) capped at 100.
    """
    if not vulns:
        return 0.0

    total = 0.0
    for v in vulns:
        base_score = v.cvss_v3_score or v.cvss_v2_score or 0.0
        weight     = SEVERITY_WEIGHTS.get(v.severity, 0.0)
        total     += base_score * weight

    # Normalize to 0-100
    score = min(round((total / (len(vulns) * 10 * 10)) * 100, 2), 100.0)
    return score


def assign_security_grade(risk_score: float) -> str:
    for low, high, grade in GRADE_THRESHOLDS:
        if low <= risk_score < high:
            return grade
    return "F"


def get_severity_from_cvss(cvss_score: float) -> SeverityLevel:
    """CVSS v3 severity mapping per NVD standard."""
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
    """Full scoring pipeline for one host. Saves to DB."""
    vulns = host.vulnerabilities
    host.risk_score     = calculate_host_risk_score(vulns)
    host.security_grade = assign_security_grade(host.risk_score)
    db.commit()
    db.refresh(host)
    return host
