#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
service_checks.py
Purpose
-------
Check configured systemd service exit statuses and display the results
as an HTML report.
"""
from __future__ import annotations
import json
import subprocess
import sys
import shutil
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# =====================
# CONSTANTS
# =====================
CONFIG = "/etc/service_checks_config.json"
HTML = "/usr/local/share/service_checks_html/index.html"
REPORT_TITLE = "Service Checks"

# =====================
# DATA MODEL
# =====================
@dataclass
class Check:
    """Hold one systemd service check."""
    key: str
    service: str
    description: str
    status: Dict[str, Dict[str, str]]

# =====================
# LOGGING & CONFIG
# =====================
def log_message(message: str) -> None:
    """Print a timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} : {message}", flush=True)

def load_json(path: Path) -> Dict[str, Any]:
    """Load a JSON object."""
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)

def load_text(path: Path) -> str:
    """Load a text file."""
    return path.read_text(encoding="utf-8")

def parse_checks(cfg: Dict[str, Any]) -> List[Check]:
    """Parse configured systemd service checks."""
    checks = []
    for key, spec in cfg["checks"].items():
        checks.append(
            Check(
                key=key,
                service=spec["service"],
                description=spec["description"],
                status=spec["status"],
            )
        )
    return checks

# =====================
# SYSTEMD
# =====================
def get_service_status(
    service: str,
) -> Tuple[Optional[int], str]:
    """Return the last exit code and run time for a systemd service."""
    result = subprocess.run(
        [
            "systemctl",
            "show",
            service,
            "--property=ExecMainStatus",
            "--property=ExecMainExitTimestamp",
        ],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        return None, "Unknown"
    values = {}
    for line in result.stdout.splitlines():
        key, _, value = line.partition("=")
        values[key] = value
    try:
        exit_code = int(values["ExecMainStatus"])
    except (KeyError, ValueError):
        exit_code = None
    last_run = (
        values.get("ExecMainExitTimestamp")
        or "Unknown"
    )
    return exit_code, last_run

# =====================
# HTML
# =====================
def build_checks_html(
    results: List[Dict[str, str]],
) -> str:
    """Build HTML table rows for check results."""
    rows = []
    for result in results:
        rows.append(
            f"""
            <tr>
                <td>{result["description"]}</td>
                <td class="status {result["class"]}">
                    {result["result"]}
                </td>
                <td>{result["message"]}</td>
                <td>{result["last_run"]}</td>
            </tr>
            """
        )
    return "\n".join(rows)

def build_html_report(
    template: str,
    checks_html: str,
    report_title: str,
) -> str:
    """Build the final HTML report."""
    return (
        template
        .replace("{{TITLE}}", report_title)
        .replace("{{CHECKS}}", checks_html)
    )

def show_html(html: str) -> None:
    """Write and open the generated HTML report."""
    source_dir = Path("/usr/local/share/service_checks_html")
    report_dir = Path.home() / ".cache" / "service_checks"
    index_path = report_dir / "index.html"
    shutil.copytree(
        source_dir,
        report_dir,
        dirs_exist_ok=True,
    )
    index_path.write_text(
        html,
        encoding="utf-8",
    )
    subprocess.Popen(
        ["firefox", index_path.as_uri()]
    )

# =====================
# MAIN
# =====================
def main() -> int:
    """Check configured systemd services and display their status."""
    # Set paths for the configuration and HTML template.
    cfg_path = Path(CONFIG)
    html_path = Path(HTML)
    report_title = REPORT_TITLE
    # Log the files being used.
    log_message(f"Using config: {cfg_path}")
    log_message(f"Using HTML: {html_path}")
    # Load the configuration, HTML template, and configured checks.
    try:
        cfg = load_json(cfg_path)
        html_template = load_text(html_path)
        checks = parse_checks(cfg)
    except Exception as exc:
        # Stop if any required file or configuration cannot be loaded.
        log_message(
            f"[ERROR] Failed to load required files: {exc!r}"
        )
        return 2
    # Process each configured service check.
    results = []
    for check in checks:
        log_message(f"Checking service: {check.service}")
        # Read the service exit status and last run time.
        exit_code, last_run = get_service_status(
            check.service
        )
        # Record an unknown result if the service status cannot be read.
        if exit_code is None:
            results.append({
                "description": check.description,
                "result": "UNKNOWN",
                "class": "unknown",
                "message": "Unable to read service exit status.",
                "last_run": last_run,
            })
            log_message(
                f"UNKNOWN : {check.description} : "
                "Unable to read service exit status."
            )
            continue
        # Match the service exit code to its configured status.
        status = check.status.get(str(exit_code))
        # Record an unknown result if the exit code is not configured.
        if status is None:
            results.append({
                "description": check.description,
                "result": "UNKNOWN",
                "class": "unknown",
                "message": f"Unknown exit status: {exit_code}",
                "last_run": last_run,
            })
            log_message(
                f"UNKNOWN : {check.description} : "
                f"Unknown exit status: {exit_code}"
            )
            continue
        # Record the configured result for the service.
        results.append({
            "description": check.description,
            "result": status["result"],
            "class": status["class"],
            "message": status["description"],
            "last_run": last_run,
        })
        log_message(
            f"{status['result']} : "
            f"{check.description} : "
            f"{status['description']} : "
            f"Last run: {last_run}"
        )
    # Build the HTML table from the collected service results.
    checks_html = build_checks_html(results)
    # Insert the results into the HTML report template.
    html = build_html_report(
        template=html_template,
        checks_html=checks_html,
        report_title=report_title,
    )
    # Display the completed HTML report.
    show_html(html)
    # Log the number of service checks processed.
    log_message(
        f"DONE: {len(results)}/{len(checks)} check(s) processed."
    )
    return 0

if __name__ == "__main__":
    raise SystemExit(main())