#!/usr/bin/env python3
"""
archive_utils.py

Helpers for downloading, extracting, installing, and cleaning up archive files.
"""

from __future__ import annotations
import os
import shutil
import subprocess
import glob
from pathlib import Path
from typing import Optional, Iterable, List
from zipfile import ZipFile

# ---------------------------------------------------------------------
# CONSTANTS
# ---------------------------------------------------------------------

ARCHIVE_EXTENSIONS = (".tar.gz", ".tgz", ".tar.xz", ".tar.bz2", ".zip", ".rar", ".7z")

# ---------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------


def check_archive_status(check_path: str | None, extract_to: str | None) -> bool:
    """Return True if `check_path` exists as a file or `extract_to` exists as a non-empty directory."""
    for path in (check_path, extract_to):
        if not path:
            continue
        p = Path(path).expanduser()
        if p.is_file():
            return True
        if p.is_dir() and any(p.iterdir()):
            return True
    return False


def guess_ext_from_url(url: str) -> str:
    """Return the matching archive extension for a URL, or an empty string if none match."""
    lower = url.lower()
    for ext in ARCHIVE_EXTENSIONS:
        if lower.endswith(ext):
            return ext
    return ""


def _strip_top_level_dir(extract_to: Path) -> None:
    """Flatten a single top-level directory after extraction into `extract_to`."""
    try:
        items = [p for p in Path(extract_to).iterdir()]
        if len(items) != 1 or not items[0].is_dir():
            return
        top = items[0]
        for child in top.iterdir():
            shutil.move(str(child), str(Path(extract_to) / child.name))
        shutil.rmtree(top)
    except Exception as e:
        print(f"[ERROR] StripTopLevel failed for {extract_to}: {e}")

# ---------------------------------------------------------------------
# DOWNLOAD
# ---------------------------------------------------------------------


def download_archive_file(name: str, url: str, download_dir: str | Path) -> Optional[Path]:
    """Download an archive with wget into `download_dir` and return the resulting file path (or None)."""
    try:
        download_dir = Path(download_dir).expanduser().resolve()
        download_dir.mkdir(parents=True, exist_ok=True)
        ext = guess_ext_from_url(url) or ".zip"
        target = download_dir / f"{name}{ext}"
        subprocess.run(["wget", "-O", str(target), url], check=True)
        return target if target.exists() else None
    except Exception as e:
        print(f"Unexpected error downloading {url}: {e}")
        return None

# ---------------------------------------------------------------------
# INSTALL / UNINSTALL
# ---------------------------------------------------------------------


def install_archive_file(archive_path: Path | str, extract_to: Path | str, strip_top_level: bool = False) -> bool:
    """
    Extract an archive into `extract_to` and optionally flatten a single top-level folder.

    Supports tar-based archives (e.g. .tar.gz/.tgz/.tar.xz/.tar.bz2) and .zip files. When
    `strip_top_level=True`, a single extracted top directory is removed and its contents moved up.

    Example:
        install_archive_file("/tmp/tool.tgz", "/opt/tool", strip_top_level=True)
    """
    try:
        archive_path = Path(archive_path).expanduser()
        extract_to = Path(extract_to).expanduser()
        if not archive_path.exists():
            print(f"Error: Archive file {archive_path} does not exist.")
            return False
        extract_to.mkdir(parents=True, exist_ok=True)
        suffix = "".join(archive_path.suffixes).lower()
        print(f"Attempting to extract {archive_path} to {extract_to}")
        if suffix.endswith((".tar.gz", ".tgz", ".tar.xz", ".tar.bz2")):
            subprocess.run(["tar", "-xf", str(archive_path), "-C", str(extract_to)], check=True)
        elif suffix.endswith(".zip"):
            subprocess.run(["unzip", "-o", str(archive_path), "-d", str(extract_to)], check=True)
        elif suffix.endswith(".rar"):
            subprocess.run(["unrar", "x", "-o+", str(archive_path), str(extract_to)], check=True)
        elif suffix.endswith(".7z"):
            subprocess.run(["7z", "x", "-y", str(archive_path), f"-o{extract_to}"], check=True)
        else:
            print(f"Unsupported file type: {suffix}")
            return False
        if strip_top_level:
            _strip_top_level_dir(extract_to)
        print(f"Archive {archive_path} extracted successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error during extraction: {e}")
        return False
    except Exception as e:
        print(f"Unexpected error: {e}")
        return False



def uninstall_archive_install(check_path: Path | str | None, extract_to: Path | str) -> bool:
    """Remove an extracted installation, or its check path for file-based installations."""
    target = Path(extract_to).expanduser()
    check = Path(check_path).expanduser() if check_path else None
    if check and check.is_file() and target.is_dir() and check != target:
        try:
            check.relative_to(target)
        except ValueError:
            target = check
    try:
        if target.is_symlink() or target.is_file():
            target.unlink()
            print(f"[uninstall_archive_install] Removed file: {target}")
            return True
        if target.is_dir():
            shutil.rmtree(target)
            print(f"[uninstall_archive_install] Removed directory: {target}")
            return True
        print(f"[uninstall_archive_install] Target not found: {target}")
        return False
    except OSError as exc:
        print(f"[uninstall_archive_install] ERROR: {exc}")
        return False


# ---------------------------------------------------------------------
# LINKS / CLEANUP
# ---------------------------------------------------------------------


def create_symlink(target: Path | str, link_path: Path | str) -> bool:
    """
    Create or replace a symlink at `link_path` pointing to `target`.

    Example:
        create_symlink("/opt/tool/bin/tool", "/usr/local/bin/tool")
    """
    try:
        target = Path(os.path.expanduser(str(target)))
        link_path = Path(os.path.expanduser(str(link_path)))
        link_path.parent.mkdir(parents=True, exist_ok=True)
        if link_path.exists() or link_path.is_symlink():
            link_path.unlink()
        link_path.symlink_to(target)
        return True
    except Exception:
        return False



def handle_cleanup(archive_path: Path | str, name: str | None = None) -> bool:
    """Delete a temporary archive file or download directory."""
    try:
        path = Path(archive_path).expanduser()
        if name:
            path = path / f"{name}.deb"
        if path.is_dir() and not path.is_symlink():
            shutil.rmtree(path)
        else:
            path.unlink(missing_ok=True)
        print(f"[handle_cleanup] Removed: {path}")
        return True
    except OSError as exc:
        print(f"[handle_cleanup] ERROR: Could not remove {path}: {exc}")
        return False


# ---------------------------------------------------------------------
# ARCHIVE CREATION
# ---------------------------------------------------------------------



def create_zip_archive(zips):
    """Create zip archives from dictionaries or (src, output) tuples."""
    if isinstance(zips, (tuple, dict)):
        zips = [zips]
    if not zips:
        print("[INFO] No zip archives to create.")
        return True
    success = True
    for item in zips:
        if isinstance(item, dict):
            if not item.get("src") or not item.get("output"):
                print(f"[create_zip_archive] ERROR: Missing or empty 'src' or 'output': {item}")
                success = False
                continue
            src, output = item["src"], item["output"]
        else:
            try:
                src, output = item
            except (TypeError, ValueError):
                print(f"[create_zip_archive] ERROR: Expected (src, output) tuple, got: {item}")
                success = False
                continue
        src_path = Path(os.path.expandvars(os.path.expanduser(src)))
        out_path = Path(os.path.expandvars(os.path.expanduser(output)))
        if not src_path.is_dir():
            print(f"[create_zip_archive] ERROR: Source directory not found: {src_path}")
            success = False
            continue
        try:
            with ZipFile(out_path, "w") as zipf:
                for p in src_path.rglob("*"):
                    if p.is_file():
                        zipf.write(p, p.relative_to(src_path))
            print(f"[create_zip_archive] Created: {out_path}")
        except (OSError, ValueError) as e:
            print(f"[create_zip_archive] ERROR: Could not create {out_path}: {e}")
            success = False
    return success


