import nmap
import shutil
import asyncio
from typing import List, Dict, Any
from datetime import datetime, timezone

SCAN_PROFILES = {
    "quick":    "-T4 -F --open",
    "standard": "-T4 -sV -sC -O --open",
    "deep":     "-T4 -sV -sC -O -A -p- --open",
    "stealth":  "-T2 -sS -sV -O --open",
    "vuln":     "-T4 -sV -sC --script=vuln --open",
    "udp":      "-T4 -sU -sV --open",
}

SCAN_TIMEOUTS = {
    "quick":    120,
    "standard": 300,
    "deep":     900,
    "stealth":  600,
    "vuln":     600,
    "udp":      600,
}


def _check_nmap_installed():
    if not shutil.which("nmap"):
        raise RuntimeError(
            "nmap is not installed or not in PATH. "
            "Install it with: sudo apt-get install nmap"
        )


class NmapScanner:

    def __init__(self):
        _check_nmap_installed()
        self.nm = nmap.PortScanner()

    def scan_targets(
        self,
        targets: List[str],
        profile: str = "standard",
        extra_args: str = ""
    ) -> Dict[str, Any]:
        args    = SCAN_PROFILES.get(profile, SCAN_PROFILES["standard"])
        timeout = SCAN_TIMEOUTS.get(profile, 300)

        if extra_args:
            args = f"{args} {extra_args}"

        target_str = " ".join(targets)

        try:
            self.nm.scan(
                hosts=target_str,
                arguments=args,
                timeout=timeout
            )
        except nmap.PortScannerError as e:
            raise RuntimeError(f"Nmap scan failed: {str(e)}")
        except Exception as e:
            raise RuntimeError(f"Unexpected scan error: {str(e)}")

        return self._parse_results()

    def _parse_results(self) -> Dict[str, Any]:
        results = {
            "scan_time": datetime.now(timezone.utc).isoformat(),
            "hosts": []
        }
        for host in self.nm.all_hosts():
            results["hosts"].append(self._extract_host(host))
        return results

    def _extract_host(self, host: str) -> Dict[str, Any]:
        nm = self.nm[host]

        os_name, os_accuracy, os_family = None, None, None
        if "osmatch" in nm and nm["osmatch"]:
            best        = nm["osmatch"][0]
            os_name     = best.get("name")
            os_accuracy = int(best.get("accuracy", 0))
            osclass     = best.get("osclass", [{}])[0]
            os_family   = osclass.get("osfamily")

        ports = []
        for proto in nm.all_protocols():
            for port in nm[proto].keys():
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
        vendor    = None
        if mac and "vendor" in nm:
            vendor = nm["vendor"].get(mac)

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


scanner = NmapScanner()
