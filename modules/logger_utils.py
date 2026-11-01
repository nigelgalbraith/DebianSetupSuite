#!/usr/bin/env python3
"""
logger_utils.py

Logging helpers: configure logging, print+log messages, rotate log files, and install logrotate config.
"""

import os
import logging
import shutil
from pathlib import Path
from shutil import copyfile

# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------


def log_and_print(message):
    """Print `message` to stdout and log it at INFO level."""
    print(message)
    logging.info(message)

# ---------------------------------------------------------------------
# SETUP
# ---------------------------------------------------------------------


def setup_logging(log_file, log_dir):
    """
    Configure application-wide logging to `log_file` with timestamped INFO messages.

    Creates `log_dir` if it does not exist.

    Example:
        setup_logging(Path("app.log"), Path("./logs"))
    """
    log_dir.mkdir(parents=True, exist_ok=True)
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

# ---------------------------------------------------------------------
# MAINTENANCE / OUTPUT
# ---------------------------------------------------------------------


def rotate_logs(log_dir: Path, logs_to_keep: int, pattern: str = "*.log") -> None:
    """
    Remove old log files from `log_dir`, keeping only the most recent `logs_to_keep`.

    Files are ordered by modification time. If `logs_to_keep` is zero or negative,
    nothing is deleted. Creates `log_dir` if missing.

    Example:
        rotate_logs(Path("./logs"), logs_to_keep=10)
    """
    try:
        log_dir.mkdir(parents=True, exist_ok=True)
        logs = sorted(
            log_dir.glob(pattern),
            key=lambda f: f.stat().st_mtime if f.exists() else 0,
        )
        if logs_to_keep > 0 and len(logs) > logs_to_keep:
            for old_log in logs[:-logs_to_keep]:
                try:
                    if old_log.is_file() or old_log.is_symlink():
                        old_log.unlink()
                        print(f"Deleted old log: {old_log}")
                    elif old_log.is_dir():
                        shutil.rmtree(old_log, ignore_errors=True)
                        print(f"Deleted old log directory: {old_log}")
                except Exception as e:
                    print(f"[rotate_logs] WARNING: Could not remove {old_log}: {e}")
    except Exception as e:
        print(f"[rotate_logs] WARNING: Rotation failed for {log_dir}: {e}")


def show_logs(log_paths: dict):
    """
    Print the contents of log files defined in a name-to-path mapping.

    Example:
        show_logs({"install": "./logs/install.log", "fw": "./logs/firewall.log"})
    """
    for name, path in log_paths.items():
        log_path = Path(path)
        if log_path.exists():
            print(f"\n=== {name} ({log_path}) ===")
            print(log_path.read_text())
        else:
            print(f"\n--- Log file for '{name}' not found at: {log_path}")

# ---------------------------------------------------------------------
# SYSTEM INTEGRATION
# ---------------------------------------------------------------------


def install_logrotate_config(template_path, target_name, target_dir="/etc/logrotate.d"):
    """Install a logrotate configuration file."""
    dest_path = Path(target_dir) / target_name
    copyfile(template_path, dest_path)
    os.chmod(dest_path, 0o644)
    print(f"[OK]   Logrotate config installed → {dest_path}")
    return True


def remove_logrotate_config(log_name, target_dir="/etc/logrotate.d"):
    """Remove a logrotate configuration file if it exists."""
    path = Path(target_dir) / log_name
    if path.exists():
        path.unlink()
        print(f"[OK]   Logrotate config removed → {path}")
    return True