from typing import Dict, Any, List
from app.database.models import HostResult, PortResult
from sqlalchemy.orm import Session


def save_scan_results(
    db: Session,
    scan_id: int,
    raw_results: Dict[str, Any]
) -> List[HostResult]:
    """
    Takes raw nmap results dict and saves
    HostResult + PortResult rows to DB.
    Returns list of saved HostResult objects.
    """
    saved_hosts = []

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
        db.flush()   # get host.id without full commit

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

        db.commit()
        db.refresh(host)
        saved_hosts.append(host)

    return saved_hosts
