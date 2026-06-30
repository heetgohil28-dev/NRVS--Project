NRVS is an online tool that works like a web search.NRVS is an online tool that can be used akin to a web search.

Automatically discover networks, list services, correlate CVEs and provide risk scores with a comprehensive vulnerability assessment solution with a real-time dashboard displayed using React, and professional reports produced.

For internal approving, defensive security operations and organized security learning. Does NOT carry out exploitation.


What It Does

CapabilityDescriptionHost & Port DiscoveryNmap-powered scanning of single hosts, target lists or CIDR rangesService & Version DetectionIdentifies running services, with version strings for accurate CVE matchingCVE CorrelationMaps detected versions to published vulnerabilities with CVSS scoringRisk ScoringComputes per-asset risk scores from severity distribution and exposure profileHistorical ComparisonDiffs scan results over time, surfaces new findings and resolved issuesScreenshot EvidenceCaptures web service screenshots automatically at scan timeReportingExports HTML, PDF and JSON reports for stakeholder distributionAuthenticationJWT-secured API with hashed password storage


Stack

Frontend — HTML, CSS, and JavaScript.Database — PostgreSQL.
Frontend — Material Design and JQuery
To create a Docker image.To download an image.


Workflow

This process includes login, selecting the target, running a scan, enumerating the services, mapping the CVE, calculating the risk score and then viewing the scan results on the dashboard or export the scan report.

Monitor progress of scan streams in real-time. Results are stored in PostgreSQL so that they can be compared across assessment cycles for historical purposes. Reports are made to be sent to the stakeholders directly.


Use Cases


Internal vulnerability checks and network audits.
Home lab and familiar lab environment.
Educating and awareness building
Finding assets and building reserves.Building up reserves of assets and inventory.
Cybersecurity portfolio demonstration


Disclaimer

NRVS is for systems which you own, or have explicit written permission to assess. Scanning: In the majority of countries scanning is illegal if not agreed upon. The author can take no responsibility for misuse. The user assumes responsibility and is subject to the law and ethical standards in respect of all scanning activities.


Author

Heet Gohil 

Maitrey Suthar
A Cybersecurity Engineering Student involved in Offensive Security and Red Teaming.
LinkedIn · GitHub
