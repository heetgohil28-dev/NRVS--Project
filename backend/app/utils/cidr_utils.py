import ipaddress
from typing import List

MAX_PREFIX_LENGTH = 24  # /24 minimum — blocks /8, /16 etc.

def expand_cidr(cidr: str) -> List[str]:
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        if network.prefixlen < MAX_PREFIX_LENGTH:
            raise ValueError(
                f"CIDR /{network.prefixlen} is too large. Minimum allowed is /{MAX_PREFIX_LENGTH}."
            )
        return [str(ip) for ip in network.hosts()]
    except ValueError as e:
        raise ValueError(f"Invalid CIDR notation '{cidr}': {str(e)}")


def is_valid_cidr(cidr: str) -> bool:
    try:
        ipaddress.ip_network(cidr, strict=False)
        return True
    except ValueError:
        return False


def is_valid_ip(ip: str) -> bool:
    try:
        ipaddress.ip_address(ip)
        return True
    except ValueError:
        return False


def is_private_ip(ip: str) -> bool:
    try:
        return ipaddress.ip_address(ip).is_private
    except ValueError:
        return False


def parse_targets(targets: List[str]) -> dict:
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
            result["hostnames"].append(target)
            result["expanded"].append(target)

    result["total"] = len(result["expanded"])
    return result


def get_cidr_info(cidr: str) -> dict:
    try:
        network = ipaddress.ip_network(cidr, strict=False)
        return {
            "cidr":           str(network),
            "network_address": str(network.network_address),
            "broadcast":      str(network.broadcast_address),
            "netmask":        str(network.netmask),
            "prefix_length":  network.prefixlen,
            "total_hosts":    network.num_addresses - 2,
            "is_private":     network.is_private,
        }
    except ValueError as e:
        raise ValueError(f"Invalid CIDR: {str(e)}")
