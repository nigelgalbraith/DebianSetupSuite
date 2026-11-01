#!/usr/bin/env python3
"""
camera_utils.py

Small utilities for generating camera playlist/XMLTV files and locating extracted binaries.
"""

from pathlib import Path
import subprocess
import os

from modules.system_utils import expand_path

# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------



def find_extracted_binary(root: Path | str, binary_name: str) -> Path | None:
    """Search an extracted directory for a binary by exact name or case-insensitive prefix."""
    root = Path(expand_path(root))
    for p in root.rglob(binary_name):
        if p.is_file():
            return p
    lower_prefix = binary_name.lower()
    for p in root.rglob("*"):
        if p.is_file() and p.name.lower().startswith(lower_prefix):
            return p
    return None


# ---------------------------------------------------------------------
# FILE GENERATORS
# ---------------------------------------------------------------------


def write_m3u(cameras, m3u_path: Path) -> bool:
    """
    Write an M3U playlist file containing camera stream URLs.

    Each entry is written as an EXTINF line using "Name" and optional "Description",
    followed by the camera "URL".

    Example:
        write_m3u(cameras, Path("/etc/tvheadend/iptv/cameras.m3u"))
    """
    try:
        lines = ["#EXTM3U"]
        for cam in cameras:
            name = cam.get("Name", "Camera")
            desc = cam.get("Description", "")
            url  = cam.get("URL", "")
            if not url:
                continue
            display = f"{name} - {desc}" if desc else name
            lines.append(f"#EXTINF:-1,{display}")
            lines.append(url)
        content = "\n".join(lines) + "\n"
        m3u_path = Path(m3u_path)
        m3u_path.parent.mkdir(parents=True, exist_ok=True)
        if os.geteuid() == 0:
            m3u_path.write_text(content, encoding="utf-8")
        else:
            if str(m3u_path).startswith("/etc/"):
                subprocess.run(
                    ["sudo", "tee", str(m3u_path)],
                    input=content.encode("utf-8"),
                    check=True,
                    capture_output=True
                )
            else:
                m3u_path.write_text(content, encoding="utf-8")
        return True
    except Exception as e:
        print(f"[write_m3u] ERROR: {e}")
        return False


def remove_m3u(m3u_path: Path) -> bool:
    """
    Remove an M3U playlist file (using sudo if it lives under /etc).

    Example:
        remove_m3u(Path("/etc/tvheadend/iptv/cameras.m3u"))
    """
    try:
        m3u_path = Path(m3u_path)
        if not m3u_path.exists():
            print(f"[remove_m3u] File not found: {m3u_path}")
            return False
        if str(m3u_path).startswith("/etc/"):
            subprocess.run(["sudo", "rm", "-f", str(m3u_path)], check=True)
        else:
            m3u_path.unlink()
        return True
    except Exception as e:
        print(f"[remove_m3u] ERROR: {e}")
        return False



def ensure_dummy_xmltv(path: Path | str, cameras: list[dict]) -> bool:
    """Ensure an XMLTV file exists with one channel per camera."""
    try:
        path = Path(expand_path(path))
        path.parent.mkdir(parents=True, exist_ok=True)
        if not path.exists():
            header = '<?xml version="1.0" encoding="UTF-8"?>\n<tv>\n'
            footer = '</tv>\n'
            channels = []
            for i, cam in enumerate(cameras, start=1):
                chan_id = f"cam{i}"
                name = cam.get("Name", f"Camera {i}")
                desc = cam.get("Description", "")
                display = f"{name} - {desc}" if desc else name
                channels.append(
                    f'  <channel id="{chan_id}">\n'
                    f'    <display-name>{display}</display-name>\n'
                    f'  </channel>\n'
                )
            content = header + "".join(channels) + footer
            path.write_text(content, encoding="utf-8")
            print(f"Created dummy XMLTV with {len(cameras)} channels → {path}")
        else:
            print(f"XMLTV already exists at: {path}")
        return True
    except Exception as e:
        print(f"WARNING: Could not create dummy XMLTV file: {e}")
        return False

