from typing import Dict, Any, List
<<<<<<< HEAD
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from app.database.models import HostResult, PortResult, Asset
import logging

logger = logging.getLogger(__name__)
=======
from app.database.models import HostResult, PortResult, Asset
from sqlalchemy.orm import Session
from datetime import datetime
>>>>>>> origin/heet-scan-engine


def save_scan_results(
    db: Session,
    scan_id: int,
    raw_results: Dict[str, Any],
) -> List[HostResult]:
    saved_hosts = []

<<<<<<< HEAD
    try:
        for host_data in raw_results.get("hosts", []):
            host = HostResult(
                scan_id     = scan_id,
                ip_address  = host_data["ip_address"],
                hostname    = host_data.get("hostname"),
                mac_address = host_data.get("mac_address"),
                vendor      = host_data.get("vendor"),
                os_name     = host_data.get("os_name"),
                os_accuracy = host_data.get("os_accuracy"),
                os_family   = host_data.get("os_family"),
                host_state  = host_data.get("host_state", "up"),
=======
    for host_data in raw_results.get("hosts", []):
        host = HostResult(
            scan_id     = scan_id,
            ip_address  = host_data["ip_address"],
            hostname    = host_data.get("hostname"),
            mac_address = host_data.get("mac_address"),
            vendor      = host_data.get("vendor"),
            os_name     = host_data.get("os_name"),
            os_accuracy = host_data.get("os_accuracy"),
            os_family   = host_data.get("os_family"),
            host_state  = host_data.get("host_state", "up"),
        )
        db.add(host)
        db.flush()

        for port_data in host_data.get("ports", []):
            port = PortResult(
                host_id            = host.id,
                port_number        = port_data["port_number"],
                protocol           = port_data["protocol"],
                state              = port_data["state"],
                service_name       = port_data.get("service_name"),
                service_product    = port_data.get("service_product"),
                service_version    = port_data.get("service_version"),
                service_extra_info = port_data.get("service_extra_info"),
                cpe                = port_data.get("cpe"),
                script_output      = port_data.get("script_output"),
>>>>>>> origin/heet-scan-engine
            )
            db.add(host)
            db.flush()

            for port_data in host_data.get("ports", []):
                port = PortResult(
                    host_id            = host.id,
                    port_number        = port_data["port_number"],
                    protocol           = port_data["protocol"],
                    state              = port_data["state"],
                    service_name       = port_data.get("service_name"),
                    service_product    = port_data.get("service_product"),
                    service_version    = port_data.get("service_version"),
                    service_extra_info = port_data.get("service_extra_info"),
                    cpe                = port_data.get("cpe"),
                    script_output      = port_data.get("script_output"),
                )
                db.add(port)

            saved_hosts.append(host)

        db.commit()
<<<<<<< HEAD

        for host in saved_hosts:
            db.refresh(host)
            _upsert_asset(db, host)

    except Exception as e:
        db.rollback()
        logger.error("Failed to save scan results for scan_id=%s: %s", scan_id, str(e))
        raise
=======
        db.refresh(host)

        _upsert_asset(db, host)
        saved_hosts.append(host)
>>>>>>> origin/heet-scan-engine

    return saved_hosts


<<<<<<< HEAD
def _upsert_asset(db: Session, host: HostResult) -> None:
    now = datetime.now(timezone.utc)
    asset = db.query(Asset).filter(Asset.ip_address == host.ip_address).first()
=======
def _upsert_asset(db: Session, host: HostResult):
    asset = db.query(Asset).filter(
        Asset.ip_address == host.ip_address
    ).first()
>>>>>>> origin/heet-scan-engine

    if not asset:
        asset = Asset(
            ip_address = host.ip_address,
            hostname   = host.hostname,
            os_name    = host.os_name,
<<<<<<< HEAD
            first_seen = now,
            last_seen  = now,
=======
            first_seen = datetime.utcnow(),
            last_seen  = datetime.utcnow(),
>>>>>>> origin/heet-scan-engine
        )
        db.add(asset)
    else:
        asset.hostname  = host.hostname or asset.hostname
        asset.os_name   = host.os_name  or asset.os_name
<<<<<<< HEAD
        asset.last_seen = now
=======
        asset.last_seen = datetime.utcnow()
>>>>>>> origin/heet-scan-engine

    asset.last_risk_score = host.risk_score
    db.commit()
