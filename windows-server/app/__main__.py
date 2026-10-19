"""Entry point: ``python -m app [--config config.json]``.

Scans the configured media roots, prints the LAN address to type into the
Roku app, then serves until Ctrl+C.
"""

from __future__ import annotations

import argparse
import logging
import socket
import sys
from pathlib import Path

import uvicorn

from app.config import ConfigError, load_config
from app.database import Catalog
from app.main import create_app
from app.services.scanner import scan


def lan_addresses() -> list[str]:
    addresses: set[str] = set()
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            addresses.add(info[4][0])
    except OSError:
        pass
    try:
        # No packets are sent; this only asks the OS which interface it would route through.
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as probe:
            probe.connect(("10.255.255.255", 1))
            addresses.add(probe.getsockname()[0])
    except OSError:
        pass
    return sorted(a for a in addresses if not a.startswith("127.") and not a.startswith("169.254."))


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Roku LAN Media server")
    parser.add_argument("--config", type=Path, default=Path(__file__).resolve().parent.parent / "config.json")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(levelname)s  %(message)s")
    try:
        config = load_config(args.config)
    except ConfigError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    catalog = Catalog(config.database_path)
    print("Scanning media folders...")
    report = scan(config)
    catalog.replace_all(report.records)
    playable = sum(1 for r in report.records if r.playable)
    print(f"Catalog: {len(report.records)} titles ({playable} direct-play ready)")
    if not report.probed:
        print("WARNING: ffprobe not found - codecs are not verified. Install FFmpeg and add it to PATH.")
    for name in report.missing_roots:
        print(f"WARNING: media root '{name}' was not found")

    print()
    print("Enter one of these in the Roku app:")
    if config.bind_address in ("0.0.0.0", ""):
        hosts = lan_addresses() or ["<this PC's LAN IP>"]
    else:
        hosts = [config.bind_address]
    for host in hosts:
        print(f"    Server IP: {host}    Port: {config.port}")
    print()
    print("Press Ctrl+C to stop the server.")

    uvicorn.run(create_app(config, catalog), host=config.bind_address or "0.0.0.0",
                port=config.port, log_level="warning")
    return 0


if __name__ == "__main__":
    sys.exit(main())
