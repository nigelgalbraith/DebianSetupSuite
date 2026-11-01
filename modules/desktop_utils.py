from __future__ import annotations

import os
import pwd
import shutil
import subprocess
from pathlib import Path


def create_desktop_entry(
    name: str,
    exec_cmd: str,
    user: str = "",
    icon: str = "applications-games",
    category: str = "Game;",
) -> bool:
    """Create a system-wide .desktop application launcher."""
    try:
        print(f"[INFO] Creating system desktop entry for '{name}'")
        applications_dir = Path("/usr/share/applications")
        print(f"[INFO] Applications directory: {applications_dir}")
        applications_dir.mkdir(parents=True, exist_ok=True)
        safe_name = name.replace(" ", "_")
        if category and not category.endswith(";"):
            category += ";"
        desktop_path = applications_dir / f"{safe_name}.desktop"
        if desktop_path.exists():
            print(f"[INFO] Removing existing desktop entry: {desktop_path}")
            desktop_path.unlink()
        print(f"[INFO] Desktop file path: {desktop_path}")
        desktop_content = "\n".join([
            "[Desktop Entry]",
            "Version=1.0",
            "Type=Application",
            f"Name={name}",
            f"Exec={exec_cmd}",
            f"Icon={icon}",
            "Terminal=false",
            f"Categories={category}",
            "StartupNotify=true",
            "",
        ])
        print("[INFO] Writing desktop entry file")
        desktop_path.write_text(desktop_content, encoding="utf-8")
        print("[INFO] Setting root ownership")
        os.chown(desktop_path, 0, 0)
        print("[INFO] Setting launcher permissions")
        os.chmod(desktop_path, 0o644)
        print(f"[OK] Desktop entry created successfully: {desktop_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to create desktop entry '{name}': {e}")
        return False


def remove_desktop_entry(name: str, user: str = "") -> bool:
    """Remove a system-wide .desktop application launcher."""
    try:
        print(f"[INFO] Removing system desktop entry for '{name}'")
        applications_dir = Path("/usr/share/applications")
        safe_name = name.replace(" ", "_")
        desktop_path = applications_dir / f"{safe_name}.desktop"
        print(f"[INFO] Desktop file path: {desktop_path}")
        if not desktop_path.exists():
            print(f"[WARN] Desktop entry does not exist: {desktop_path}")
            return False
        desktop_path.unlink()
        print(f"[OK] Desktop entry removed successfully: {desktop_path}")
        return True
    except Exception as e:
        print(f"[ERROR] Failed to remove desktop entry '{name}': {e}")
        return False



def refresh_desktop_database() -> bool:
    """Refresh desktop launcher/icon caches."""
    commands = [["update-desktop-database", "/usr/share/applications"]]
    if shutil.which("kbuildsycoca6"):
        commands.append(["kbuildsycoca6"])
    elif shutil.which("kbuildsycoca5"):
        commands.append(["kbuildsycoca5"])
    success = True
    for cmd in commands:
        print(f"[INFO] Running: {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, check=False)
            if result.returncode == 0:
                print(f"[OK] Command completed: {cmd[0]}")
            else:
                print(f"[WARNING] {cmd[0]} exited with code {result.returncode}")
                success = False
        except OSError as e:
            print(f"[ERROR] Could not run {cmd[0]}: {e}")
            success = False
    if success:
        print("[OK] Desktop cache refresh complete")
    else:
        print("[WARNING] Desktop cache refresh completed with errors")
    return success
