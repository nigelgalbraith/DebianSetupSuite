#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
rclone_backup.py

Purpose
-------
Copy configured local folders to rclone remotes using jobs defined in a JSON
configuration file.

The script can be run:

• Manually
• Automatically through a systemd oneshot service and timer

Key Features
------------
• Multiple upload jobs in one JSON config file
• Safe rclone copy mode only
• Manual execution always runs every enabled job
• Scheduled execution honours Immediately / Daily / Weekly / Monthly
• Filename-based dry-run safety
• Explicit --dry-run support
• Per-job exclusion patterns
• Local state records successful live uploads
• Timestamped logging to stdout for systemd capture

Execution Safety
----------------
Live mode is selected only when the script filename is exactly:

    rclone_backup.py

Live mode uses:

    /etc/rclone_backup_config.json

Any other script filename automatically runs in dry-run mode and loads:

    rclone_backup_config-template.json

The --dry-run argument always forces dry-run mode.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional


# =====================
# CONSTANTS
# =====================

SCRIPT_NAME = "rclone_backup.py"
CONFIG_PROD = "/etc/rclone_backup_config.json"
CONFIG_TEST = "rclone_backup_config-template.json"
STATE_DEFAULT = "/var/lib/rclone_backup/state.json"
FREQ_VALUES = {"immediately", "daily", "weekly", "monthly"}
ARG_DESCRIPTION = "Copy configured folders to rclone remotes."


# =====================
# DATA MODEL
# =====================

@dataclass
class Job:
    """Hold one rclone copy job."""
    key: str
    enabled: bool
    source_dir: Path
    remote: str
    remote_folder: str
    upload_frequency: str
    exclude: List[str]


# =====================
# LOGGING & CONFIG
# =====================

def log_message(message: str) -> None:
    """Print a timestamped log message."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} : {message}", flush=True)


def load_json(path: Path) -> Dict[str, Any]:
    """Load and validate a JSON object."""
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a JSON object: {path}")
    return data


def save_json_atomic(path: Path, data: Dict[str, Any]) -> None:
    """Save JSON atomically using a temporary file."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_suffix(path.suffix + ".tmp")
    with tmp_path.open("w", encoding="utf-8") as handle:
        json.dump(data, handle, indent=2, sort_keys=True)
        handle.write("\n")
    tmp_path.replace(path)


def parse_args(description: str) -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(description=description)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show rclone actions without changing the remote",
    )
    parser.add_argument(
        "--scheduled",
        action="store_true",
        help="Run as a scheduled job and enforce upload frequency",
    )
    return parser.parse_args()


# =====================
# FREQUENCY & STATE
# =====================

def parse_state_time(value: Any) -> Optional[datetime]:
    """Parse an ISO timestamp from state data."""
    if not isinstance(value, str) or not value.strip():
        return None
    try:
        return datetime.fromisoformat(value)
    except ValueError:
        return None


def should_run_upload(
    *,
    frequency: str,
    latest_success: Optional[datetime],
    now: datetime,
    manual_trigger: bool,
) -> bool:
    """Return True when an upload should run."""
    if manual_trigger:
        return True
    if frequency == "immediately":
        return True
    if latest_success is None:
        return True
    if frequency == "daily":
        return latest_success.date() != now.date()
    if frequency == "weekly":
        return latest_success.isocalendar()[:2] != now.isocalendar()[:2]
    if frequency == "monthly":
        return (
            latest_success.year,
            latest_success.month,
        ) != (
            now.year,
            now.month,
        )
    return True


# =====================
# RCLONE HELPERS
# =====================

def remote_destination(remote: str, remote_folder: str) -> str:
    """Build an rclone remote destination."""
    folder = remote_folder.strip("/")
    if folder:
        return f"{remote}:{folder}"
    return f"{remote}:"


def build_rclone_command(job: Job, dry_run: bool) -> List[str]:
    """Build the rclone copy command for one job."""
    command = [
        "rclone",
        "copy",
        str(job.source_dir),
        remote_destination(job.remote, job.remote_folder),
        "--verbose",
        "--stats=30s",
        "--create-empty-src-dirs",
    ]
    for pattern in job.exclude:
        command.extend(["--exclude", pattern])
    if dry_run:
        command.append("--dry-run")
    return command


def run_rclone(job: Job, dry_run: bool) -> bool:
    """Run one rclone copy job and return True on success."""
    command = build_rclone_command(job, dry_run)
    log_message(f"Command: {' '.join(command)}")
    proc = subprocess.run(
        command,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        log_message(
            f"[ERROR] rclone failed with return code {proc.returncode}"
        )
        return False
    return True


# =====================
# VALIDATION
# =====================

def parse_jobs(cfg: Dict[str, Any]) -> List[Job]:
    """Validate and parse upload jobs."""
    jobs_cfg = cfg.get("upload_jobs", {})
    if not isinstance(jobs_cfg, dict) or not jobs_cfg:
        raise ValueError(
            "Config must contain a non-empty 'upload_jobs' object."
        )
    jobs: List[Job] = []
    for key, spec in jobs_cfg.items():
        if not isinstance(spec, dict):
            raise ValueError(f"Job '{key}' must be an object.")
        source = spec.get("source_dir")
        remote = spec.get("remote")
        remote_folder = spec.get("remote_folder", "")
        frequency_raw = spec.get("uploadFrequency", "Immediately")
        enabled = spec.get("enabled", True)
        exclude_raw = spec.get("exclude", [])
        if not isinstance(source, str) or not source.strip():
            raise ValueError(
                f"Job '{key}' missing or invalid 'source_dir'."
            )
        if not isinstance(remote, str) or not remote.strip():
            raise ValueError(
                f"Job '{key}' missing or invalid 'remote'."
            )
        if not isinstance(remote_folder, str):
            raise ValueError(
                f"Job '{key}' has invalid 'remote_folder'."
            )
        if not isinstance(enabled, bool):
            raise ValueError(
                f"Job '{key}' field 'enabled' must be true or false."
            )
        frequency = (
            frequency_raw.strip().lower()
            if isinstance(frequency_raw, str)
            else ""
        )
        if frequency not in FREQ_VALUES:
            raise ValueError(
                f"Job '{key}' has invalid uploadFrequency "
                f"'{frequency_raw}'. Allowed: {sorted(FREQ_VALUES)}"
            )
        if not isinstance(exclude_raw, list):
            raise ValueError(
                f"Job '{key}' field 'exclude' must be a list."
            )
        if any(not isinstance(item, str) for item in exclude_raw):
            raise ValueError(
                f"Job '{key}' field 'exclude' must contain strings."
            )
        exclude = [
            item.strip()
            for item in exclude_raw
            if item.strip()
        ]
        jobs.append(
            Job(
                key=key,
                enabled=enabled,
                source_dir=Path(source),
                remote=remote.strip().rstrip(":"),
                remote_folder=remote_folder.strip(),
                upload_frequency=frequency,
                exclude=exclude,
            )
        )
    return jobs


# =====================
# MAIN
# =====================

def main() -> int:
    """Run all configured rclone copy jobs."""
    args = parse_args(ARG_DESCRIPTION)
    script_basename = os.path.basename(sys.argv[0])
    if script_basename == SCRIPT_NAME:
        cfg_path = Path(CONFIG_PROD)
        dry_run = args.dry_run

        if dry_run:
            log_message(
                "Argument '--dry-run' detected — running in DRY-RUN "
                f"with production config '{cfg_path}'."
            )
    else:
        cfg_path = Path(__file__).resolve().parent / CONFIG_TEST
        dry_run = True
        log_message(
            f"Script name '{script_basename}' != '{SCRIPT_NAME}' — "
            f"running in DRY-RUN with test config '{cfg_path}'."
        )
    log_message(f"Using config: {cfg_path}")
    log_message(f"Dry run: {dry_run}")
    log_message(
        "TRIGGER: SCHEDULED"
        if args.scheduled
        else "TRIGGER: MANUAL"
    )
    if shutil.which("rclone") is None:
        log_message("[ERROR] rclone was not found in PATH.")
        return 2
    if not cfg_path.exists():
        log_message(f"[ERROR] Config not found: {cfg_path}")
        return 2
    try:
        cfg = load_json(cfg_path)
        jobs = parse_jobs(cfg)
    except Exception as exc:
        log_message(
            f"[ERROR] Failed to load or parse config: {exc!r}"
        )
        return 2
    state_raw = cfg.get("state_file", STATE_DEFAULT)
    if not isinstance(state_raw, str) or not state_raw.strip():
        log_message(
            "[ERROR] 'state_file' must be a non-empty string."
        )
        return 2
    state_path = Path(state_raw)
    state: Dict[str, Any] = {"jobs": {}}
    if state_path.exists():
        try:
            loaded_state = load_json(state_path)

            if isinstance(loaded_state.get("jobs"), dict):
                state = loaded_state
        except Exception as exc:
            log_message(
                "[WARN] Could not read state file; "
                f"starting fresh: {exc!r}"
            )
    processed = 0
    failed = 0
    manual_trigger = not args.scheduled
    for job in jobs:
        log_message(f"==> Job '{job.key}'")

        if not job.enabled:
            log_message("[SKIP] Job disabled.")
            continue
        destination = remote_destination(
            job.remote,
            job.remote_folder,
        )
        log_message(f"Source: {job.source_dir}")
        log_message(f"Dest:   {destination}")
        if not job.source_dir.exists():
            log_message(
                f"[ERROR] Source does not exist: {job.source_dir}"
            )
            failed += 1
            continue
        if not job.source_dir.is_dir():
            log_message(
                f"[ERROR] Source is not a directory: {job.source_dir}"
            )
            failed += 1
            continue
        job_state = state.setdefault("jobs", {}).get(job.key, {})
        latest = parse_state_time(job_state.get("last_success"))
        now = datetime.now()
        if not should_run_upload(
            frequency=job.upload_frequency,
            latest_success=latest,
            now=now,
            manual_trigger=manual_trigger,
        ):
            latest_text = (
                latest.strftime("%Y-%m-%d %H:%M:%S")
                if latest
                else "None"
            )
            log_message(
                f"[SKIP] Frequency '{job.upload_frequency}' not due. "
                f"Latest successful upload: {latest_text}"
            )
            continue
        try:
            ok = run_rclone(job, dry_run)
        except KeyboardInterrupt:
            log_message("Interrupted by user.")
            return 130
        except Exception as exc:
            log_message(
                f"[ERROR] Job '{job.key}' failed: {exc!r}"
            )
            failed += 1
            continue
        if not ok:
            failed += 1
            continue
        log_message("[OK] rclone copy completed.")
        processed += 1
        if dry_run:
            continue
        state.setdefault("jobs", {})[job.key] = {
            "last_success": datetime.now().isoformat(
                timespec="seconds"
            ),
            "destination": destination,
        }
        try:
            save_json_atomic(state_path, state)
        except Exception as exc:
            log_message(
                f"[ERROR] Failed to save state: {exc!r}"
            )
            failed += 1
    log_message(
        f"DONE: {processed}/{len(jobs)} job(s) processed; "
        f"{failed} failure(s)."
    )
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
