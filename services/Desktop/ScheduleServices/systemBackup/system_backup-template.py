#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
system_backup.py

Purpose
-------
Run structured rsync backups based on jobs defined in a JSON configuration
file.

This script is intended to run either:

• Manually by an administrator
• Automatically through a systemd service

Each configured job can copy a source directory to a destination directory
while optionally creating an exact mirror, remaining on one filesystem,
excluding configured paths, and enforcing destination folder permissions.


Key Features
------------
• Multiple backup jobs defined in one JSON config file
• Rsync archive mode with ACL, xattr, hard-link, and numeric-ID preservation
• Optional destination mirroring using --delete
• Optional one-filesystem restriction
• Per-job rsync exclusion patterns
• Optional backup destination ownership and permission enforcement
• Safe dry-run mode for testing
• Simple timestamped logging


Execution Safety
----------------
The script determines **live vs dry-run mode** using two checks:

1) Explicit argument

    --dry-run

   This always forces dry-run mode and uses the production config.

2) Script filename check

   If the script filename is exactly:

       system_backup.py

   the script runs in **live mode** and uses:

       /etc/system_backup_config.json

   If executed under any other filename, the script automatically switches
   to **dry-run mode** and uses:

       system_backup_config-template.json


Dry-Run Mode
------------
In dry-run mode:

• Rsync runs with --dry-run
• No files are copied, changed, or deleted
• No groups or user memberships are changed
• No destination ownership or permissions are changed
• All administrative actions are logged with "[DRY-RUN]" messages

This allows safe testing of configuration and logic.


Mirror Behavior
---------------
Jobs may specify:

    "mirror": true

When enabled, rsync uses --delete so files that no longer exist in the source
are removed from the destination.

When disabled, files are copied and updated, but destination-only files are
left untouched.


Configuration
-------------
Configuration is loaded from JSON and must define a top-level object:

    "backup_jobs"

Each job can specify:

• source_dir          – directory to copy
• destination_dir     – destination directory
• mirror              – true to delete destination-only files
• one_file_system     – true to prevent crossing filesystem boundaries
• exclude             – list of rsync exclusion patterns

Optional fields:

• backupGroup         – group to ensure exists for backup access
• backupUsers         – users added to backup group
• protected_folder    – enforce owner/group/permissions on destination

Example job:

{
  "backup_jobs": {
    "debian_system": {
      "source_dir": "/",
      "destination_dir": "/mnt/nigel/backups/System",
      "mirror": true,
      "one_file_system": true,
      "exclude": [
        "/dev/***",
        "/proc/***",
        "/sys/***",
        "/run/***",
        "/tmp/***",
        "/mnt/***",
        "/media/***"
      ],
      "backupGroup": "backup",
      "backupUsers": ["nigel"],
      "protected_folder": {
        "owner": "root",
        "group": "backup",
        "permissions": "2775"
      }
    }
  }
}


Logging
-------
All operations log timestamped messages to stdout.

Logging to files is normally handled by systemd using:

    StandardOutput
    StandardError

This avoids duplicate logging and keeps the script simple.
"""

from __future__ import annotations

import json
import subprocess
import os
import sys
import argparse
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional, List


# =====================
# CONSTANTS
# =====================
SCRIPT_NAME = "system_backup.py"
CONFIG_PROD = "/etc/system_backup_config.json"
CONFIG_TEST = "system_backup_config-template.json"
ARG_DESCRIPTION = "Run structured, per-job rsync backups."


# =====================
# DATA MODELS
# =====================
@dataclass
class Job:
    """Hold one backup job."""
    key: str
    source_dir: Path
    destination_dir: Path
    mirror: bool
    one_file_system: bool
    exclude: List[str]
    backup_group: Optional[str]
    backup_users: List[str]
    protect_owner: Optional[str]
    protect_group: Optional[str]
    protect_perms: Optional[str]


# =====================
# LOGGING & CONFIG
# =====================
def log_message(message: str) -> None:
    """Print a message with timestamp (YYYY-MM-DD HH:MM:SS)."""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"{timestamp} : {message}", flush=True)


def load_json(path: Path) -> Dict[str, Any]:
    """Load JSON file as dict."""
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict):
        raise ValueError(f"Config must be a JSON object: {path}")
    return data


def parse_args(description: str):
    parser = argparse.ArgumentParser(
        description=description
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show actions without executing"
    )
    return parser.parse_args()


# =====================
# FILESYSTEM HELPERS
# =====================
def ensure_backup_group(group: str, users: list[str], dry_run: bool) -> None:
    """Ensure a group exists and required users are members of it."""
    grp_check = subprocess.run(
        ["getent", "group", group],
        capture_output=True,
        text=True
    )
    if grp_check.returncode == 0:
        if dry_run:
            log_message(f"[DRY-RUN] Group already exists: {group}")
    else:
        if dry_run:
            log_message(f"[DRY-RUN] Would create group: {group}")
        else:
            log_message(f"Creating group: {group}")
            proc = subprocess.run(
                ["groupadd", group],
                capture_output=True,
                text=True,
            )
            if proc.returncode != 0:
                log_message(
                    f"[WARN] groupadd {group} failed: "
                    f"{proc.stderr.strip()}"
                )
                return
    for user in sorted({
        u.strip()
        for u in users
        if isinstance(u, str) and u.strip()
    }):
        usr_check = subprocess.run(
            ["id", "-nG", user],
            capture_output=True,
            text=True
        )
        if usr_check.returncode != 0:
            log_message(f"[WARN] User does not exist: {user}")
            continue
        if group in usr_check.stdout.split():
            continue
        if dry_run:
            log_message(
                f"[DRY-RUN] Would add user '{user}' "
                f"to group '{group}'"
            )
            continue
        log_message(f"Adding user '{user}' to group '{group}'")
        proc = subprocess.run(
            ["usermod", "-aG", group, user],
            capture_output=True,
            text=True
        )
        if proc.returncode != 0:
            log_message(
                f"[WARN] usermod failed for {user}: "
                f"{proc.stderr.strip()}"
            )


def apply_folder_protection(
    folder: Path,
    owner: str,
    group: str,
    perms: str,
    dry_run: bool
) -> None:
    """Apply ownership and permissions to a folder."""
    if dry_run:
        log_message(f"[DRY-RUN] Would mkdir -p {folder}")
        log_message(f"[DRY-RUN] Would chown {owner}:{group} {folder}")
        log_message(f"[DRY-RUN] Would chmod {perms} {folder}")
        return
    folder.mkdir(parents=True, exist_ok=True)
    chown = subprocess.run(
        ["chown", f"{owner}:{group}", str(folder)],
        capture_output=True,
        text=True,
    )
    if chown.returncode != 0:
        log_message(
            f"[WARN] chown failed on {folder}: "
            f"{chown.stderr.strip()}"
        )
    chmod = subprocess.run(
        ["chmod", perms, str(folder)],
        capture_output=True,
        text=True,
    )
    if chmod.returncode != 0:
        log_message(
            f"[WARN] chmod failed on {folder}: "
            f"{chmod.stderr.strip()}"
        )
    log_message(f"Protected folder applied: {folder}")


# =====================
# RSYNC HELPERS
# =====================
def rsync_directory(job: Job, dry_run: bool) -> bool:
    """Rsync source_dir to destination_dir."""
    source = str(job.source_dir)
    destination = str(job.destination_dir)
    if source != "/":
        source = source.rstrip("/") + "/"
    destination = destination.rstrip("/") + "/"
    command = [
        "rsync",
        "-aHAX",
        "--numeric-ids",
        "--human-readable",
        "--itemize-changes",
        "--info=progress2",
    ]
    if dry_run:
        command.append("--dry-run")
    if job.mirror:
        command.append("--delete")
    if job.one_file_system:
        command.append("--one-file-system")
    for pattern in job.exclude:
        command.extend(["--exclude", pattern])
    command.extend([
        source,
        destination,
    ])
    if dry_run:
        log_message(
            f"[DRY-RUN] Would rsync '{source}' -> '{destination}'"
        )
    else:
        log_message(f"Rsync '{source}' -> '{destination}'")
    # Allow rsync output to pass directly to systemd.
    proc = subprocess.run(command)
    if proc.returncode != 0:
        log_message(f"[ERROR] rsync failed (rc={proc.returncode})")
        return False
    return True


# =====================
# MAIN
# =====================
def main() -> int:
    """Run rsync backups for all jobs in config."""
    # Decide config + dry-run based on script filename or arguments
    args = parse_args(ARG_DESCRIPTION)
    script_basename = os.path.basename(sys.argv[0])
    if script_basename == SCRIPT_NAME:
        cfg_path = Path(CONFIG_PROD)
        dry_run = args.dry_run
        if dry_run:
            log_message(
                f"Argument '--dry-run' detected — "
                f"running in DRY-RUN with production config '{cfg_path}'."
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
    # Load configuration file
    if not cfg_path.exists():
        log_message(f"[ERROR] Config not found: {cfg_path}")
        return 2
    try:
        cfg = load_json(cfg_path)
    except Exception as e:
        log_message(f"[ERROR] Failed to load config: {e!r}")
        return 2
    # Parse and validate jobs
    try:
        jobs_cfg = cfg.get("backup_jobs", {})
        if not isinstance(jobs_cfg, dict) or not jobs_cfg:
            raise ValueError(
                "Config must contain a non-empty 'backup_jobs' object."
            )
        jobs: List[Job] = []
        for key, spec in jobs_cfg.items():
            if not isinstance(spec, dict):
                raise ValueError(f"Job '{key}' must be an object.")
            src = spec.get("source_dir")
            destination = spec.get("destination_dir")
            if not isinstance(src, str) or not src.strip():
                raise ValueError(
                    f"Job '{key}' missing/invalid 'source_dir'."
                )
            if (
                not isinstance(destination, str)
                or not destination.strip()
            ):
                raise ValueError(
                    f"Job '{key}' missing/invalid 'destination_dir'."
                )
            mirror = spec.get("mirror", False)
            if not isinstance(mirror, bool):
                raise ValueError(
                    f"Job '{key}' has non-boolean 'mirror'."
                )
            one_file_system = spec.get("one_file_system", False)
            if not isinstance(one_file_system, bool):
                raise ValueError(
                    f"Job '{key}' has non-boolean "
                    f"'one_file_system'."
                )
            exclude_raw = spec.get("exclude", [])
            if not isinstance(exclude_raw, list):
                raise ValueError(
                    f"Job '{key}' has non-list 'exclude'."
                )
            exclude = [
                pattern.strip()
                for pattern in exclude_raw
                if isinstance(pattern, str) and pattern.strip()
            ]
            # Backup groups and users
            backup_group_raw = spec.get("backupGroup")
            backup_group = (
                backup_group_raw.strip()
                if isinstance(backup_group_raw, str)
                else None
            )
            backup_group = backup_group if backup_group else None
            backup_users_raw = spec.get("backupUsers", [])
            backup_users: List[str] = []
            if isinstance(backup_users_raw, list):
                backup_users = [
                    user.strip()
                    for user in backup_users_raw
                    if isinstance(user, str) and user.strip()
                ]
            # File protection
            protected = spec.get("protected_folder", {})
            protect_owner = None
            protect_group = None
            protect_perms = None
            if isinstance(protected, dict):
                owner = protected.get("owner")
                group = protected.get("group")
                perms = protected.get("permissions")

                protect_owner = (
                    owner
                    if isinstance(owner, str) and owner.strip()
                    else None
                )
                protect_group = (
                    group
                    if isinstance(group, str) and group.strip()
                    else None
                )
                protect_perms = (
                    perms
                    if isinstance(perms, str) and perms.strip()
                    else None
                )
            jobs.append(
                Job(
                    key=key,
                    source_dir=Path(src),
                    destination_dir=Path(destination),
                    mirror=mirror,
                    one_file_system=one_file_system,
                    exclude=exclude,
                    backup_group=backup_group,
                    backup_users=backup_users,
                    protect_owner=protect_owner,
                    protect_group=protect_group,
                    protect_perms=protect_perms,
                )
            )
    except Exception as e:
        log_message(f"[ERROR] Failed to parse jobs: {e!r}")
        return 2
    # Execute backup jobs
    processed = 0
    for job in jobs:
        try:
            log_message(f"==> Job '{job.key}'")
            log_message(f"Source: {job.source_dir}")
            log_message(f"Dest:   {job.destination_dir}")
            log_message(f"Mirror: {job.mirror}")
            log_message(f"One filesystem: {job.one_file_system}")
            # Ensure backup group + membership
            if job.backup_group:
                ensure_backup_group(
                    job.backup_group,
                    job.backup_users,
                    dry_run
                )
            # Apply folder protection when configured
            if (
                job.protect_owner
                and job.protect_group
                and job.protect_perms
            ):
                apply_folder_protection(
                    job.destination_dir,
                    job.protect_owner,
                    job.protect_group,
                    job.protect_perms,
                    dry_run=dry_run,
                )
                if not dry_run:
                    st = subprocess.run(
                        [
                            "stat",
                            "-c",
                            "%U:%G %a %n",
                            str(job.destination_dir)
                        ],
                        capture_output=True,
                        text=True,
                    )
                    if st.returncode == 0:
                        log_message(
                            f"Protected folder result: "
                            f"{st.stdout.strip()}"
                        )
                    else:
                        log_message(
                            f"[WARN] stat failed on "
                            f"{job.destination_dir}: "
                            f"{st.stderr.strip()}"
                        )
            # Validate source exists
            if not job.source_dir.exists():
                log_message(
                    f"[ERROR] Source does not exist: "
                    f"{job.source_dir}"
                )
                continue
            # Run rsync backup
            ok = rsync_directory(job, dry_run)
            if ok:
                if dry_run:
                    log_message(
                        f"[OK] Dry-run completed: {job.key}"
                    )
                else:
                    log_message(
                        f"[OK] Backup completed: {job.key}"
                    )
                processed += 1
            else:
                log_message("[FAIL] Rsync backup failed.")
        except KeyboardInterrupt:
            log_message("Interrupted by user.")
            return 130
        except Exception as e:
            log_message(
                f"[ERROR] Job '{job.key}' failed: {e!r}"
            )
    # Final summary
    log_message(
        f"DONE: {processed}/{len(jobs)} job(s) processed."
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())