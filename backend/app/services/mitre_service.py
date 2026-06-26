import httpx
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from app.database.models import Vulnerability, SeverityLevel
import os

logger = logging.getLogger(__name__)

MITRE_ATTACK_URL = "https://raw.githubusercontent.com/mitre/cti/master/enterprise-attack/enterprise-attack.json"
REQUEST_TIMEOUT  = 15.0

KEYWORD_TECHNIQUE_MAP: Dict[str, List[Dict[str, str]]] = {
    "sql injection": [
        {"tactic": "Initial Access",    "technique_id": "T1190", "technique": "Exploit Public-Facing Application"},
    ],
    "xss": [
        {"tactic": "Execution",         "technique_id": "T1059", "technique": "Command and Scripting Interpreter"},
    ],
    "rce": [
        {"tactic": "Execution",         "technique_id": "T1203", "technique": "Exploitation for Client Execution"},
        {"tactic": "Initial Access",    "technique_id": "T1190", "technique": "Exploit Public-Facing Application"},
    ],
    "remote code execution": [
        {"tactic": "Execution",         "technique_id": "T1203", "technique": "Exploitation for Client Execution"},
        {"tactic": "Initial Access",    "technique_id": "T1190", "technique": "Exploit Public-Facing Application"},
    ],
    "buffer overflow": [
        {"tactic": "Privilege Escalation", "technique_id": "T1068", "technique": "Exploitation for Privilege Escalation"},
        {"tactic": "Execution",            "technique_id": "T1203", "technique": "Exploitation for Client Execution"},
    ],
    "privilege escalation": [
        {"tactic": "Privilege Escalation", "technique_id": "T1068", "technique": "Exploitation for Privilege Escalation"},
    ],
    "path traversal": [
        {"tactic": "Discovery",         "technique_id": "T1083", "technique": "File and Directory Discovery"},
    ],
    "directory traversal": [
        {"tactic": "Discovery",         "technique_id": "T1083", "technique": "File and Directory Discovery"},
    ],
    "information disclosure": [
        {"tactic": "Discovery",         "technique_id": "T1082", "technique": "System Information Discovery"},
    ],
    "denial of service": [
        {"tactic": "Impact",            "technique_id": "T1499", "technique": "Endpoint Denial of Service"},
    ],
    "dos": [
        {"tactic": "Impact",            "technique_id": "T1499", "technique": "Endpoint Denial of Service"},
    ],
    "authentication bypass": [
        {"tactic": "Defense Evasion",   "technique_id": "T1556", "technique": "Modify Authentication Process"},
        {"tactic": "Initial Access",    "technique_id": "T1078", "technique": "Valid Accounts"},
    ],
    "command injection": [
        {"tactic": "Execution",         "technique_id": "T1059", "technique": "Command and Scripting Interpreter"},
    ],
    "ssrf": [
        {"tactic": "Discovery",         "technique_id": "T1046", "technique": "Network Service Discovery"},
        {"tactic": "Initial Access",    "technique_id": "T1190", "technique": "Exploit Public-Facing Application"},
    ],
    "xxe": [
        {"tactic": "Initial Access",    "technique_id": "T1190", "technique": "Exploit Public-Facing Application"},
        {"tactic": "Discovery",         "technique_id": "T1083", "technique": "File and Directory Discovery"},
    ],
    "deserialization": [
        {"tactic": "Execution",         "technique_id": "T1203", "technique": "Exploitation for Client Execution"},
    ],
    "open redirect": [
        {"tactic": "Initial Access",    "technique_id": "T1566", "technique": "Phishing"},
    ],
    "weak password": [
        {"tactic": "Credential Access", "technique_id": "T1110", "technique": "Brute Force"},
    ],
    "default credentials": [
        {"tactic": "Initial Access",    "technique_id": "T1078", "technique": "Valid Accounts"},
        {"tactic": "Credential Access", "technique_id": "T1110", "technique": "Brute Force"},
    ],
    "unencrypted": [
        {"tactic": "Collection",        "technique_id": "T1040", "technique": "Network Sniffing"},
    ],
    "cleartext": [
        {"tactic": "Collection",        "technique_id": "T1040", "technique": "Network Sniffing"},
    ],
    "backdoor": [
        {"tactic": "Persistence",       "technique_id": "T1505", "technique": "Server Software Component"},
    ],
    "persistence": [
        {"tactic": "Persistence",       "technique_id": "T1505", "technique": "Server Software Component"},
    ],
    "lateral movement": [
        {"tactic": "Lateral Movement",  "technique_id": "T1021", "technique": "Remote Services"},
    ],
    "smb": [
        {"tactic": "Lateral Movement",  "technique_id": "T1021", "technique": "Remote Services"},
        {"tactic": "Collection",        "technique_id": "T1039", "technique": "Data from Network Shared Drive"},
    ],
    "ftp": [
        {"tactic": "Exfiltration",      "technique_id": "T1048", "technique": "Exfiltration Over Alternative Protocol"},
    ],
    "ssh": [
        {"tactic": "Initial Access",    "technique_id": "T1078", "technique": "Valid Accounts"},
        {"tactic": "Lateral Movement",  "technique_id": "T1021", "technique": "Remote Services"},
    ],
}

SEVERITY_DEFAULT_TACTICS: Dict[SeverityLevel, List[Dict[str, str]]] = {
    SeverityLevel.CRITICAL: [
        {"tactic": "Initial Access",       "technique_id": "T1190", "technique": "Exploit Public-Facing Application"},
        {"tactic": "Execution",            "technique_id": "T1203", "technique": "Exploitation for Client Execution"},
        {"tactic": "Privilege Escalation", "technique_id": "T1068", "technique": "Exploitation for Privilege Escalation"},
    ],
    SeverityLevel.HIGH: [
        {"tactic": "Initial Access",       "technique_id": "T1190", "technique": "Exploit Public-Facing Application"},
        {"tactic": "Execution",            "technique_id": "T1203", "technique": "Exploitation for Client Execution"},
    ],
    SeverityLevel.MEDIUM: [
        {"tactic": "Discovery",            "technique_id": "T1082", "technique": "System Information Discovery"},
    ],
    SeverityLevel.LOW: [
        {"tactic": "Discovery",            "technique_id": "T1082", "technique": "System Information Discovery"},
    ],
    SeverityLevel.INFO: [],
    SeverityLevel.NONE: [],
}


def map_cve_to_mitre(description: Optional[str], severity: Optional[SeverityLevel]) -> Dict[str, List]:
    tactics    = []
    techniques = []
    seen_ids   = set()

    if description:
        desc_lower = description.lower()
        for keyword, mappings in KEYWORD_TECHNIQUE_MAP.items():
            if keyword in desc_lower:
                for m in mappings:
                    if m["technique_id"] not in seen_ids:
                        tactics.append(m["tactic"])
                        techniques.append({
                            "technique_id": m["technique_id"],
                            "technique":    m["technique"],
                            "tactic":       m["tactic"],
                        })
                        seen_ids.add(m["technique_id"])

    if not techniques and severity and severity in SEVERITY_DEFAULT_TACTICS:
        for m in SEVERITY_DEFAULT_TACTICS[severity]:
            if m["technique_id"] not in seen_ids:
                tactics.append(m["tactic"])
                techniques.append({
                    "technique_id": m["technique_id"],
                    "technique":    m["technique"],
                    "tactic":       m["tactic"],
                })
                seen_ids.add(m["technique_id"])

    return {
        "tactics":    list(set(tactics)),
        "techniques": techniques,
    }


def enrich_vulnerability_with_mitre(vuln: Vulnerability, db: Session) -> Vulnerability:
    mapping = map_cve_to_mitre(vuln.description, vuln.severity)
    vuln.mitre_tactics    = mapping["tactics"]
    vuln.mitre_techniques = mapping["techniques"]
    db.commit()
    db.refresh(vuln)
    logger.info(
        "MITRE mapped for %s — tactics: %s",
        vuln.cve_id, mapping["tactics"]
    )
    return vuln


def enrich_host_with_mitre(host_id: int, db: Session) -> int:
    vulns = db.query(Vulnerability).filter(Vulnerability.host_id == host_id).all()
    count = 0
    for vuln in vulns:
        if not vuln.mitre_tactics:
            enrich_vulnerability_with_mitre(vuln, db)
            count += 1
    return count
