import httpx
import asyncio
import logging
import re
import os
from typing import List, Optional, Dict, Any
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database.models import Vulnerability, HostResult, SeverityLevel
from app.services.scoring_service import get_severity_from_cvss

logger = logging.getLogger(__name__)

NVD_API_BASE    = "https://services.nvd.nist.gov/rest/json/cves/2.0"
NVD_API_KEY     = os.getenv("NVD_API_KEY")
REQUEST_TIMEOUT = 10.0
MAX_RETRIES     = 3
RETRY_DELAY     = 2.0


def _build_headers() -> Dict[str, str]:
    headers = {"Accept": "application/json"}
    if NVD_API_KEY:
        headers["apiKey"] = NVD_API_KEY
    return headers


def _parse_cvss(cve_item: Dict[str, Any]) -> tuple:
    metrics = cve_item.get("metrics", {})
    cvss_v3, cvss_v2, vector = None, None, None

    if "cvssMetricV31" in metrics:
        data    = metrics["cvssMetricV31"][0]["cvssData"]
        cvss_v3 = data.get("baseScore")
        vector  = data.get("vectorString")
    elif "cvssMetricV30" in metrics:
        data    = metrics["cvssMetricV30"][0]["cvssData"]
        cvss_v3 = data.get("baseScore")
        vector  = data.get("vectorString")

    if "cvssMetricV2" in metrics:
        data    = metrics["cvssMetricV2"][0]["cvssData"]
        cvss_v2 = data.get("baseScore")

    return cvss_v3, cvss_v2, vector


def _parse_references(cve_item: Dict[str, Any]) -> List[str]:
    return [
        ref.get("url", "")
        for ref in cve_item.get("references", [])
        if ref.get("url")
    ]


def _parse_cpe(cve_item: Dict[str, Any]) -> List[str]:
    cpes = []
    for config in cve_item.get("configurations", []):
        for node in config.get("nodes", []):
            for match in node.get("cpeMatch", []):
                if match.get("vulnerable"):
                    cpes.append(match.get("criteria", ""))
    return cpes


async def _fetch_cve(cve_id: str) -> Optional[Dict[str, Any]]:
    url     = f"{NVD_API_BASE}?cveId={cve_id}"
    headers = _build_headers()

    for attempt in range(MAX_RETRIES):
        try:
            async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
                response = await client.get(url, headers=headers)
                if response.status_code == 200:
                    data  = response.json()
                    vulns = data.get("vulnerabilities", [])
                    if vulns:
                        return vulns[0].get("cve", {})
                elif response.status_code == 404:
                    logger.warning("CVE not found: %s", cve_id)
                    return None
                elif response.status_code == 429:
                    wait = RETRY_DELAY * (attempt + 1)
                    logger.warning("NVD rate limit hit, waiting %ss", wait)
                    await asyncio.sleep(wait)
                else:
                    logger.error("NVD API error %s for %s", response.status_code, cve_id)
        except httpx.TimeoutException:
            logger.warning("Timeout fetching %s (attempt %s)", cve_id, attempt + 1)
            await asyncio.sleep(RETRY_DELAY)
        except Exception as e:
            logger.error("Error fetching CVE %s: %s", cve_id, str(e))
            break

    return None


async def enrich_cve(cve_id: str) -> Optional[Dict[str, Any]]:
    cve_data = await _fetch_cve(cve_id)
    if not cve_data:
        return None

    cvss_v3, cvss_v2, vector = _parse_cvss(cve_data)
    score = cvss_v3 or cvss_v2 or 0.0

    descriptions = cve_data.get("descriptions", [])
    description  = next(
        (d["value"] for d in descriptions if d.get("lang") == "en"),
        None
    )

    published    = cve_data.get("published")
    published_dt = None
    if published:
        try:
            published_dt = datetime.fromisoformat(published.replace("Z", "+00:00"))
        except ValueError:
            pass

    return {
        "cve_id":         cve_id,
        "cvss_v3_score":  cvss_v3,
        "cvss_v2_score":  cvss_v2,
        "cvss_vector":    vector,
        "severity":       get_severity_from_cvss(score),
        "description":    description,
        "published_date": published_dt,
        "references":     _parse_references(cve_data),
        "affected_cpe":   _parse_cpe(cve_data),
    }


def _extract_cve_ids_from_port(port) -> List[str]:
    cve_ids = []
    if not port.script_output:
        return cve_ids
    for script_name, output in port.script_output.items():
        if isinstance(output, str) and "CVE-" in output:
            found = re.findall(r"CVE-\d{4}-\d{4,7}", output)
            cve_ids.extend(found)
    return list(set(cve_ids))


async def enrich_host_vulnerabilities(
    host: HostResult,
    db: Session,
) -> List[Vulnerability]:
    all_cve_ids = []
    for port in host.ports:
        all_cve_ids.extend(_extract_cve_ids_from_port(port))

    all_cve_ids = list(set(all_cve_ids))
    if not all_cve_ids:
        logger.info("No CVEs found in scan output for host %s", host.ip_address)
        return []

    saved_vulns = []
    for cve_id in all_cve_ids:
        existing = db.query(Vulnerability).filter(
            Vulnerability.host_id == host.id,
            Vulnerability.cve_id  == cve_id,
        ).first()
        if existing:
            continue

        enriched = await enrich_cve(cve_id)
        if not enriched:
            continue

        vuln = Vulnerability(
            host_id        = host.id,
            cve_id         = enriched["cve_id"],
            cvss_v3_score  = enriched["cvss_v3_score"],
            cvss_v2_score  = enriched["cvss_v2_score"],
            cvss_vector    = enriched["cvss_vector"],
            severity       = enriched["severity"],
            description    = enriched["description"],
            published_date = enriched["published_date"],
            references     = enriched["references"],
            affected_cpe   = enriched["affected_cpe"],
        )
        db.add(vuln)
        saved_vulns.append(vuln)
        await asyncio.sleep(0.6)

    if saved_vulns:
        db.commit()
        for v in saved_vulns:
            db.refresh(v)
        logger.info("Saved %s CVEs for host %s", len(saved_vulns), host.ip_address)

    return saved_vulns
