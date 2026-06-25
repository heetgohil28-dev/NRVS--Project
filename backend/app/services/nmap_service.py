import nmap
import shutil
from typing import List, Dict, Any
from datetime import datetime, timezone
import logging

logger = logging.getLogger(__name__)

SCAN_PROFILES: Dict[str, str] = {
    "quick":    "-T4 -F --open",
    "standard": "-T4 -sV -sC -O --open",
    "deep":     "-T4 -sV -sC -O -A -p- --open",
    "stealth":  "-T2 -sS -sV -O --open",
    "vuln":     "-T4 -sV -sC --script=vuln --open",
    "udp":      "-T4 -sU -sV --open",
}

SCAN_TIMEOUTS: Dict[str, int] = {
    "quick":    300,
    "standard": 600,
    "deep":     3600,
    "stealth":  1200,
    "vuln":     900,
    "udp":      900,
}


def _check_nmap_installed() -> None:
    if not shutil.which("nmap"):
        raise RuntimeError("Nmap is not installed or not found in PATH")


class NmapScanner:
    def __init__(self):
        _check_nmap_installed()
        self.nm = nmap.PortScanner()

    def scan_targets(
        self,
        targets: List[str],
        profile: str = "standard",
    ) -> Dict[str, Any]:
        if profile not in SCAN_PROFILES:
            raise ValueError(f"Invalid profile '{profile}'. Choose from: {', '.join(SCAN_PROFILES)}")

        args = SCAN_PROFILES[profile]
        timeout = SCAN_TIMEOUTS[profile]
        target_str = " ".join(targets)

        logger.info("Starting nmap scan | profile=%s | targets=%s", profile, target_str)

        try:
            self.nm.scan(
                hosts=target_str,
                arguments=args,
                timeout=timeout,
            )
        except nmap.PortScannerError as e:
            logger.error("Nmap scan failed: %s", str(e))
            raise RuntimeError(f"Nmap scan failed: {str(e)}")
        except Exception as e:
            logger.error("Unexpected scan error: %s", str(e))
            raise RuntimeError(f"Scan error: {str(e)}")

        return self._parse_results()

    def _parse_results(self) -> Dict[str, Any]:
        return {
            "scan_time": datetime.now(timezone.utc).isoformat(),
            "hosts": [self._extract_host(h) for h in self.nm.all_hosts()],
        }

    def _extract_host(self, host: str) -> Dict[str, Any]:
        nm = self.nm[host]

        os_name, os_accuracy, os_family = None, None, None
        if nm.get("osmatch"):
            best       = nm["osmatch"][0]
            os_name    = best.get("name")
            os_accuracy = int(best.get("accuracy", 0))
            osclass    = best.get("osclass", [{}])[0]
            os_family  = osclass.get("osfamily")

        ports = []
        for proto in nm.all_protocols():
            for port in sorted(nm[proto].keys()):
                p = nm[proto][port]
                ports.append({
                    "port_number":        port,
                    "protocol":           proto,
                    "state":              p.get("state"),
                    "service_name":       p.get("name"),
                    "service_product":    p.get("product"),
                    "service_version":    p.get("version"),
                    "service_extra_info": p.get("extrainfo"),
                    "cpe":                p.get("cpe"),
                    "script_output":      p.get("script", {}),
                })

        addresses = nm.get("addresses", {})
        mac       = addresses.get("mac")
        vendor    = nm.get("vendor", {}).get(mac) if mac else None

        return {
            "ip_address":  host,
            "hostname":    nm.hostname() or None,
            "host_state":  nm.state(),
            "mac_address": mac,
            "vendor":      vendor,
            "os_name":     os_name,
            "os_accuracy": os_accuracy,
            "os_family":   os_family,
            "ports":       ports,
        }

    def get_raw_xml(self) -> str:
        return self.nm.get_nmap_last_output()


def get_scanner() -> NmapScanner:
    return NmapScanner()


scanner = get_scanner()
