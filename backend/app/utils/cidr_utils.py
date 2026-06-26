import ipaddress
from typing import List


def expand_cidr(cidr: str) -> List[str]:
    """
    Expand a CIDR range into individual IP addresses.
    Example: '192.168.1.0/30' -> ['192.168.1.1', '192.168.1.2']
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        # Skip network and broadcast address
        return [str(ip) for ip in network.hosts()]
    except ValueError as e:
        raise ValueError(f"Invalid CIDR notation '{cidr}': {str(e)}")


def is_valid_cidr(cidr: str) -> bool:
    """Check if a string is valid CIDR notation."""
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except ValueError:
        return False


def is_valid_ip(ip: str) -> bool:
    """Check if a string is a valid IP address."""
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_private_ip(ip: str) -> bool:
    """Check if IP is in private range."""
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def parse_targets(targets: List[str]) -> dict:
    """
    Parse a mixed list of IPs, hostnames, and CIDRs.
    Returns dict with categorized targets and expanded IPs.
    Example input:  ['192.168.1.1', '10.0.0.0/24', 'scanme.nmap.org']
    """
    result = {
        "ips":       [],
        "cidrs":     [],
        "hostnames": [],
        "expanded":  [],
        "total":     0,
        "errors":    []
    }

    for target in targets:
        target = target.strip()

        if is_valid_cidr(target) and "/" in target:
            result["cidrs"].append(target)
            try:
                expanded = expand_cidr(target)
                result["expanded"].extend(expanded)
            except ValueError as e:
                result["errors"].append(str(e))

        elif is_valid_ip(target):
            result["ips"].append(target)
            result["expanded"].append(target)

        else:
            # Treat as hostname
            result["hostnames"].append(target)
            result["expanded"].append(target)

    result["total"] = len(result["expanded"])
    return result


def get_cidr_info(cidr: str) -> dict:
    """
    Get detailed info about a CIDR range.
    Useful for showing users what they're about to scan.
    """
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        return {
            "cidr":             str(network),
            "network_address":  str(network.network_address),
            "broadcast":        str(network.broadcast_address),
            "netmask":          str(network.netmask),
            "prefix_length":    network.prefixlen,
            "total_hosts":      network.num_addresses - 2,
            "is_private":       network.is_private,
        }
    except ValueError as e:
        raise ValueError(f"Invalid CIDR: {str(e)}")
