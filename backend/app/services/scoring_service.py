from typing import List
from app.database.models import HostResult, Vulnerability, SeverityLevel
from sqlalchemy.orm import Session

SEVERITY_WEIGHTS = {
    SeverityLevel.CRITICAL: 40.0,
    SeverityLevel.HIGH:     20.0,
    SeverityLevel.MEDIUM:    8.0,
    SeverityLevel.LOW:       2.0,
    SeverityLevel.INFO:      0.5,
    SeverityLevel.NONE:      0.0,
}

GRADE_THRESHOLDS = [
    (0,   10,  "A+"),
    (10,  20,  "A"),
    (20,  35,  "B"),
    (35,  50,  "C"),
    (50,  70,  "D"),
    (70,  101, "F"),
]


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


def calculate_host_risk_score(vulns: List[Vulnerability]) -> float:
    if not vulns:
        return 0.0

    penalty = 0.0
    for v in vulns:
        cvss = v.cvss_v3_score or v.cvss_v2_score or 0.0
        severity = v.severity or get_severity_from_cvss(cvss)
        weight = SEVERITY_WEIGHTS.get(severity, 0.0)
        exploit_multiplier = 1.5 if v.exploit_available else 1.0
        penalty += (cvss / 10.0) * weight * exploit_multiplier

    return min(round(penalty, 2), 100.0)


def assign_security_grade(risk_score: float) -> str:
    for low, high, grade in GRADE_THRESHOLDS:
        if low <= risk_score < high:
            return grade
    return "F"


def score_and_grade_host(host: HostResult, db: Session) -> HostResult:
    vulns = host.vulnerabilities
    host.risk_score     = calculate_host_risk_score(vulns)
    host.security_grade = assign_security_grade(host.risk_score)
    db.commit()
    db.refresh(host)
    return host
