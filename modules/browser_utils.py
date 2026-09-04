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