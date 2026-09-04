#!/usr/bin/env python3
"""
browser_utils.py

Generic browser helpers.
"""

from __future__ import annotations

import subprocess
from typing import Dict

# ---------------------------------------------------------------------
# STATE
# ---------------------------------------------------------------------

_BROWSER_PROCESSES: Dict[str, subprocess.Popen] = {}

# ---------------------------------------------------------------------
# BROWSER CONTROL
# ---------------------------------------------------------------------


def open_browser(browser: str, url: str) -> bool:
    """Open a URL in a browser and track the launched process."""
    if not browser or not url:
        print("[ERROR] Browser and URL are required.")
        return False
    try:
        process = subprocess.Popen(
            [browser, url],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        _BROWSER_PROCESSES[browser] = process
        print(f"[OK] Opened {browser}: {url}")
        return True
    except FileNotFoundError:
        print(f"[ERROR] Browser not found: {browser}")
        return False
    except Exception as e:
        print(f"[ERROR] Failed to open browser: {e}")
        return False


def close_browser(browser: str) -> bool:
    """Close the browser process launched by this utility."""
    process = _BROWSER_PROCESSES.get(browser)
    if process is None:
        print(f"[INFO] No tracked {browser} process to close.")
        return True
    if process.poll() is not None:
        _BROWSER_PROCESSES.pop(browser, None)
        print(f"[INFO] Tracked {browser} process is already closed.")
        return True
    try:
        process.terminate()
        process.wait(timeout=10)
        _BROWSER_PROCESSES.pop(browser, None)
        print(f"[OK] Closed {browser}.")
        return True
    except subprocess.TimeoutExpired:
        try:
            process.kill()
            process.wait(timeout=5)
            _BROWSER_PROCESSES.pop(browser, None)
            print(f"[OK] Killed {browser}.")
            return True
        except Exception as e:
            print(f"[ERROR] Failed to kill {browser}: {e}")
            return False
    except Exception as e:
        print(f"[ERROR] Failed to close {browser}: {e}")
        return False

# ---------------------------------------------------------------------
# USER INTERACTION
# ---------------------------------------------------------------------


def wait_for_user(message: str) -> bool:
    """Wait for user confirmation before continuing."""
    try:
        input(message)
        return True
    except (EOFError, KeyboardInterrupt):
        print("\n[INFO] Continue cancelled.")
        return False
