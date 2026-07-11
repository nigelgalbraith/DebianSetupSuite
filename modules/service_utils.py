#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
service_utils.py

Systemd helper functions for installing unit files, enabling/disabling services, and restarts.
"""

from pathlib import Path
import subprocess

# ---------------------------------------------------------------------
# HELPERS / STATUS
# ---------------------------------------------------------------------


def check_service_status(service_name: str) -> bool:
    """Return True if the systemd service is enabled, otherwise False."""
    try:
        result = subprocess.run(
            ["systemctl", "is-enabled", service_name],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            check=False,
            text=True,
        )
        return result.returncode == 0
    except Exception:
        return False


# ---------------------------------------------------------------------
# SYSTEMD OPERATIONS
# ---------------------------------------------------------------------

def create_service(src: str | Path, dest: str | Path) -> bool:
    """Copy and register a systemd service unit file (daemon-reload); return True on success."""
    try:
        subprocess.run(["cp", str(src), str(dest)], check=True)
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def enable_and_start_service(service_name: str) -> bool:
    """Enable and start a systemd service; return True on success."""
    try:
        subprocess.run(["systemctl", "enable", service_name], check=True)
        subprocess.run(["systemctl", "start", service_name], check=True)
        print(f"[OK]   Service enabled & started → {service_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Enable/start failed → {service_name} ({e})")
        return False


def stop_and_disable_service(service_name: str) -> bool:
    """Stop and disable a systemd service; return True on success."""
    try:
        subprocess.run(["systemctl", "stop", service_name], check=True)
        subprocess.run(["systemctl", "disable", service_name], check=True)
        print(f"[OK]   Service stopped & disabled → {service_name}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Stop/disable failed → {service_name} ({e})")
        return False


def restart_service(service_name: str) -> bool:
    """
    Restart (or start if inactive) a systemd service, printing stdout/stderr on failure.

    Example:
        restart_service("ssh")
    """
    print(f"\n[INFO] Attempting to restart service: {service_name}")
    try:
        result = subprocess.run(
            ["systemctl", "restart", service_name],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"[SUCCESS] Service '{service_name}' restarted successfully.")
        if result.stdout.strip():
            print(f"[OUTPUT] {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[WARNING] Failed to restart service '{service_name}'.")
        if e.stderr:
            print(f"[ERROR] {e.stderr.strip()}")
        if e.stdout:
            print(f"[DETAILS] {e.stdout.strip()}")
        return False


def start_service_standard(service: str) -> bool:
    """
    Enable and start a systemd service unconditionally; return True on success.

    If `service` is blank, returns True (no-op).
    """
    if not service:
        return True
    try:
        subprocess.run(["systemctl", "enable", service], check=True)
        subprocess.run(["systemctl", "start", service], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

# ---------------------------------------------------------------------
# PIPELINE / HIGHER-LEVEL HELPERS
# ---------------------------------------------------------------------


def ensure_service_installed(service_name: str, template_path: Path) -> bool:
    """
    Ensure a systemd unit exists; if missing, copy a template, daemon-reload, enable, and start.

    Example:
        ensure_service_installed("myapp", Path("./templates/myapp.service"))
    """
    unit_name = service_name if service_name.endswith(".service") else f"{service_name}.service"
    unit_path = Path("/etc/systemd/system") / unit_name
    if unit_path.exists():
        return True
    if not template_path.exists():
        return False
    try:
        subprocess.run(["cp", str(template_path), str(unit_path)], check=True)
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "enable", unit_name], check=True)
        subprocess.run(["systemctl", "start", unit_name], check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def restart_services_in_order(job_name, meta):
    """
    Restart services in ascending order using each entry's 'Order' field.

    Expects `meta` to be a dict of service configs with keys:
      - ServiceName
      - Order (int, optional; defaults to 0)

    Example:
        restart_services_in_order("Services", {"ssh": {"ServiceName":"ssh","Order":1}})
    """
    import subprocess
    try:
        if not isinstance(meta, dict):
            print(f"[ERROR] Invalid metadata passed for {job_name}")
            return False
        services = sorted(meta.items(), key=lambda item: item[1].get("Order", 0))
        print("\n  ==> Restarting services in defined order")
        for name, svc in services:
            service_name = svc.get("ServiceName")
            if not service_name:
                print(f"[WARN] Skipping {name}: missing ServiceName")
                continue
            try:
                subprocess.run(["systemctl", "restart", service_name], check=True)
                print(f"[OK] Restarted: {service_name}")
            except subprocess.CalledProcessError as e:
                print(f"[ERROR] Failed to restart {service_name}: {e}")
                return False
        return True
    except Exception as e:
        print(f"[FATAL] restart_services_in_order failed: {e}")
        return False
