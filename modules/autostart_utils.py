#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
autostart_utils.py

Desktop autostart helper functions for installing, removing, and checking
per-user autostart entries.
"""

from pathlib import Path
import os
import pwd
import shutil
import subprocess

# ---------------------------------------------------------------------
# HELPERS / STATUS
# ---------------------------------------------------------------------


def check_autostart_status(
    job_name: str,
    users: list,
    autostart_name: str,
) -> bool:
    """Return True if the autostart entry is installed for all configured users."""
    for user in users:
        try:
            user_info = pwd.getpwnam(user)
            autostart_path = (
                Path(user_info.pw_dir)
                / ".config"
                / "autostart"
                / autostart_name
            )
            if not autostart_path.exists():
                return False
        except KeyError:
            return False
    return True


# ---------------------------------------------------------------------
# AUTOSTART OPERATIONS
# ---------------------------------------------------------------------


def install_autostart(
    src: str | Path,
    autostart_name: str,
    users: list,
) -> bool:
    """Install an autostart entry for all configured users."""
    src_path = Path(src)
    if not src_path.exists():
        print(f"[FAIL] Source file missing → {src_path}")
        return False
    success = True
    for user in users:
        try:
            user_info = pwd.getpwnam(user)
            autostart_dir = (
                Path(user_info.pw_dir)
                / ".config"
                / "autostart"
            )
            autostart_path = autostart_dir / autostart_name
            autostart_dir.mkdir(
                parents=True,
                exist_ok=True,
            )
            shutil.copy2(
                src_path,
                autostart_path,
            )
            os.chown(
                autostart_dir,
                user_info.pw_uid,
                user_info.pw_gid,
            )
            os.chown(
                autostart_path,
                user_info.pw_uid,
                user_info.pw_gid,
            )
            print(
                f"[OK]   AutoStart installed → "
                f"{autostart_path} ({user})"
            )
        except KeyError:
            print(f"[FAIL] User not found → {user}")
            success = False
        except Exception as e:
            print(
                f"[FAIL] AutoStart installation failed → "
                f"{user} ({e})"
            )
            success = False
    return success


def remove_autostart(
    autostart_name: str,
    users: list,
) -> bool:
    """Remove an autostart entry for all configured users."""
    success = True
    for user in users:
        try:
            user_info = pwd.getpwnam(user)
            autostart_path = (
                Path(user_info.pw_dir)
                / ".config"
                / "autostart"
                / autostart_name
            )
            if autostart_path.exists():
                autostart_path.unlink()
                print(
                    f"[OK]   AutoStart removed → "
                    f"{autostart_path} ({user})"
                )
            else:
                print(
                    f"[SKIP] AutoStart not present → "
                    f"{autostart_path} ({user})"
                )
        except KeyError:
            print(f"[FAIL] User not found → {user}")
            success = False
        except Exception as e:
            print(
                f"[FAIL] AutoStart removal failed → "
                f"{user} ({e})"
            )
            success = False
    return success


def run_autostart(script_dest: str) -> bool:
    """Run the installed autostart script as the desktop user."""
    user = os.environ.get("SUDO_USER")
    if not user:
        print("[FAIL] Unable to determine desktop user")
        return False
    try:
        uid = subprocess.run(
            ["id", "-u", user],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        display = os.environ.get("DISPLAY")
        xauthority = os.environ.get("XAUTHORITY")
        env = [
            f"XDG_RUNTIME_DIR=/run/user/{uid}",
            f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus",
        ]
        if display:
            env.append(f"DISPLAY={display}")
        if xauthority:
            env.append(f"XAUTHORITY={xauthority}")
        subprocess.Popen(
            [
                "runuser",
                "-u",
                user,
                "--",
                "env",
                *env,
                "/usr/bin/python3",
                script_dest,
            ]
        )
        print(
            f"[OK]   AutoStart launched → "
            f"{script_dest} ({user})"
        )
        return True
    except Exception as e:
        print(
            f"[FAIL] AutoStart launch failed → "
            f"{script_dest} ({e})"
        )
        return False