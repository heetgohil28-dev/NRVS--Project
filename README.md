# NRVS - Network Recon & Vulnerability Scanner

A full-stack vulnerability assessment platform that automates network discovery, service enumeration, CVE correlation, and risk scoring — with a real-time React dashboard and professional reporting output.

Built for authorized internal assessments, defensive security workflows, and structured security education. Does not perform exploitation.

---

## What It Does

| Capability | Description |
|---|---|
| Host & Port Discovery | Nmap-powered scanning across single hosts, target lists, or CIDR ranges |
| Service & Version Detection | Identifies running services with version strings for accurate CVE matching |
| CVE Correlation | Maps detected versions to published vulnerabilities with CVSS scoring |
| Risk Scoring | Computes per-asset risk scores from severity distribution and exposure profile |
| MITRE ATT&CK Mapping | Connects findings to adversary technique context for prioritization |
| Historical Comparison | Diffs scan results over time — surfaces new findings and resolved issues |
| Screenshot Evidence | Captures web service screenshots automatically at scan time |
| Reporting | Exports HTML, PDF, and JSON reports for stakeholder distribution |
| Real-Time Progress | WebSocket-driven scan updates streamed live to the dashboard |
| Authentication | JWT-secured API with hashed password storage |

---

## Stack

**Backend** — Python, FastAPI, SQLAlchemy, PostgreSQL, python-nmap, WebSockets, JWT  
**Frontend** — React, Tailwind CSS, Chart.js, Axios  
**Infra** — Docker, Docker Compose

---

## Workflow

```
Login → Select Target → Run Scan → Service Enumeration → CVE Mapping → Risk Score → Dashboard → Export Report
```

Scan progress streams in real time. Results persist to PostgreSQL for historical comparison across assessment cycles. Reports are formatted for direct stakeholder distribution.

---

## Use Cases

- Internal vulnerability assessments and network auditing
- Homelab and controlled lab environments
- Security awareness training and education
- Asset discovery and inventory
- Cybersecurity portfolio demonstration

---

## Disclaimer

NRVS is intended only for systems you own or have explicit written authorization to assess. Unauthorized scanning is illegal in most jurisdictions. The authors assume no liability for misuse. Users bear full legal and ethical responsibility for all scanning activity.

---

## Authors

**Champ** — Scan Engine, Asset Inventory, Risk Scoring, WebSocket Manager, Screenshot Service  
**Maitrey Suthar** — Auth, CVE Engine, MITRE Mapping, Reports  

*Cybersecurity Engineering Students | Offensive Security & Red Teaming*

Champ's LinkedIn · Champ's GitHub  
Maitrey's LinkedIn · Maitrey's GitHub
