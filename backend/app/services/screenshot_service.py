import asyncio
import aiofiles
import aiohttp
import os
from datetime import datetime
from typing import Optional
from pathlib import Path

SCREENSHOT_DIR = Path("app/static/screenshots")
SCREENSHOT_DIR.mkdir(parents=True, exist_ok=True)


async def take_screenshot(
    ip: str,
    port: int,
    protocol: str = "http"
) -> Optional[str]:
    """
    Attempt to capture HTTP banner/response from a web service.
    Returns saved file path or None if failed.
    Uses aiohttp to fetch page — lightweight alternative to browser.
    """
    url = f"{protocol}://{ip}:{port}"
    filename = f"{ip}_{port}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}.txt"
    filepath = SCREENSHOT_DIR / filename

    try:
        timeout = aiohttp.ClientTimeout(total=10)
        async with aiohttp.ClientSession(timeout=timeout) as session:
            async with session.get(url, ssl=False, allow_redirects=True) as resp:
                content_type = resp.headers.get("Content-Type", "")
                status       = resp.status
                headers      = dict(resp.headers)
                body         = await resp.text(errors="replace")

                # Save evidence file
                evidence = (
                    f"URL: {url}\n"
                    f"Status: {status}\n"
                    f"Content-Type: {content_type}\n"
                    f"Headers:\n"
                )
                for k, v in headers.items():
                    evidence += f"  {k}: {v}\n"
                evidence += f"\nBody (first 2000 chars):\n{body[:2000]}"

                async with aiofiles.open(filepath, "w") as f:
                    await f.write(evidence)

                return str(filepath)

    except Exception:
        return None


async def scan_web_ports(
    ip: str,
    open_ports: list
) -> dict:
    """
    Scan common web ports on a host and capture evidence.
    Returns dict of port -> screenshot_path.
    """
    WEB_PORTS = {
        80:   "http",
        443:  "https",
        8080: "http",
        8443: "https",
        8000: "http",
        8888: "http",
        3000: "http",
        5000: "http",
    }

    results = {}
    tasks   = []

    for port in open_ports:
        if port in WEB_PORTS:
            proto = WEB_PORTS[port]
            tasks.append((port, take_screenshot(ip, port, proto)))

    for port, task in tasks:
        path = await task
        if path:
            results[port] = path

    return results


def get_screenshots_for_host(ip: str) -> list:
    """Return all saved screenshot files for a given IP."""
    files = []
    for f in SCREENSHOT_DIR.glob(f"{ip}_*.txt"):
        files.append({
            "file":     str(f),
            "port":     f.stem.split("_")[1],
            "captured": f.stat().st_mtime
        })
    return sorted(files, key=lambda x: x["captured"], reverse=True)


def delete_screenshots_for_host(ip: str) -> int:
    """Delete all screenshots for a given IP. Returns count deleted."""
    count = 0
    for f in SCREENSHOT_DIR.glob(f"{ip}_*.txt"):
        f.unlink()
        count += 1
    return count
