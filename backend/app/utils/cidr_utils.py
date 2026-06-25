import ipaddress
import re
from typing import List

MAX_SUBNET_PREFIX = 24
MAX_TARGETS = 10


def is_valid_ip(target: str) -> bool:
    try:
        ipaddress.ip_address(target)
        return True
    except ValueError:
        return False


def is_valid_cidr(target: str) -> bool:
    try:
        network = ipaddress.ip_network(target, strict=False)
        if network.prefixlen < MAX_SUBNET_PREFIX:
            raise ValueError(f"Subnet too large — minimum prefix is /{MAX_SUBNET_PREFIX}")
        return True
    except ValueError:
        return False


def is_valid_hostname(target: str) -> bool:
    pattern = r"^(?:[a-zA-Z0-9](?:[a-zA-Z0-9\-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$"
    return bool(re.match(pattern, target)) and len(target) <= 253


def is_private_or_loopback(target: str) -> bool:
    try:
        addr = ipaddress.ip_address(target.split("/")[0])
        return addr.is_private or addr.is_loopback
    except ValueError:
        return False


def validate_targets(targets: List[str]) -> List[str]:
    if not targets:
        raise ValueError("No targets provided")
    if len(targets) > MAX_TARGETS:
        raise ValueError(f"Too many targets — maximum is {MAX_TARGETS}")

    validated = []
    for raw in targets:
        target = raw.strip()
        if not target:
            continue
        if "/" in target:
            if not is_valid_cidr(target):
                raise ValueError(f"Invalid CIDR: {target}")
        elif is_valid_ip(target):
            pass
        elif is_valid_hostname(target):
            pass
        else:
            raise ValueError(f"Invalid target: {target}")
        validated.append(target)

    if not validated:
        raise ValueError("No valid targets after validation")
    return validated


def expand_cidr(cidr: str) -> List[str]:
    network = ipaddress.ip_network(cidr, strict=False)
    return [str(ip) for ip in network.hosts()]


def summarize_targets(targets: List[str]) -> dict:
    ips, cidrs, hostnames = [], [], []
    for t in targets:
        if "/" in t:
            cidrs.append(t)
        elif is_valid_ip(t):
            ips.append(t)
        else:
            hostnames.append(t)
    return {"ips": ips, "cidrs": cidrs, "hostnames": hostnames, "total": len(targets)}
