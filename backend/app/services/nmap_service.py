import nmap
import asyncio
from typing import List, Dict, Any
from datetime import datetime

# Scan profiles — each maps to real nmap flags
SCAN_PROFILES = {
    "quick":    "-T4 -F --open",
    "standard": "-T4 -sV -sC -O --open",
    "deep":     "-T4 -sV -sC -O -A -p- --open",
    "stealth":  "-T2 -sS -sV -O --open",
    "vuln":     "-T4 -sV -sC --script=vuln --open",
    "udp":      "-T4 -sU -sV --open",
}


class NmapScanner:

    def __init__(self):
        self.nm = nmap.PortScanner()

    def scan_targets(
        self,
        targets: List[str],
        profile: str = "standard",
        extra_args: str = ""
    ) -> Dict[str, Any]:
        """
        Run nmap scan on one or more targets (IPs, hostnames, CIDRs).
        Returns raw parsed result dict.
        """
        args = SCAN_PROFILES.get(profile, SCAN_PROFILES["standard"])
        if extra_args:
            args = f"{args} {extra_args}"

        target_str = " ".join(targets)

        try:
            self.nm.scan(hosts=target_str, arguments=args)
        except nmap.PortScannerError as e:
            raise RuntimeError(f"Nmap scan failed: {str(e)}")

        return self._parse_results()

    def _parse_results(self) -> Dict[str, Any]:
        results = {
            "scan_time": datetime.utcnow().isoformat(),
            "hosts": []
        }

        for host in self.nm.all_hosts():
            host_data = self._extract_host(host)
            results["hosts"].append(host_data)

        return results

    def _extract_host(self, host: str) -> Dict[str, Any]:
        nm = self.nm[host]

        # ── OS Detection ──────────────────────────────
        os_name, os_accuracy, os_family = None, None, None
        if "osmatch" in nm and nm["osmatch"]:
            best = nm["osmatch"][0]
            os_name     = best.get("name")
            os_accuracy = int(best.get("accuracy", 0))
            osclass     = best.get("osclass", [{}])[0]
            os_family   = osclass.get("osfamily")

        # ── Ports ─────────────────────────────────────
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

        # ── MAC / Vendor ───────────────────────────────
        addresses = nm.get("addresses", {})
        mac       = addresses.get("mac")
        vendor    = None
        if mac and "vendor" in nm:
            vendor = nm["vendor"].get(mac)

        return {
            "ip_address":   host,
            "hostname":     nm.hostname() or None,
            "host_state":   nm.state(),
            "mac_address":  mac,
            "vendor":       vendor,
            "os_name":      os_name,
            "os_accuracy":  os_accuracy,
            "os_family":    os_family,
            "ports":        ports,
        }

    def get_raw_xml(self) -> str:
        return self.nm.get_nmap_last_output()


# Singleton
scanner = NmapScanner()
