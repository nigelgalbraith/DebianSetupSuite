#!/usr/bin/env python3
"""
package_utils.py

Package management helpers for APT/dpkg plus small checks for installed packages/binaries.
"""

import subprocess
import shutil
from pathlib import Path
from typing import Dict, List, Any, Optional, Union
from shutil import which

# ---------------------------------------------------------------------
# HELPERS / STATUS
# ---------------------------------------------------------------------


def check_package(pkg: str) -> bool:
    """Return True if `pkg` is installed (via dpkg-query), otherwise False."""
    try:
        output = subprocess.check_output(
            ["dpkg-query", "-W", "-f=${Status}", pkg],
            stderr=subprocess.DEVNULL
        )
        return b"install ok installed" in output
    except subprocess.CalledProcessError:
        return False


def check_binary_installed(binary_name: str, symlink_path: Path | None = None) -> bool:
    """
    Return True if a binary exists in PATH or at an optional explicit symlink path.

    Example:
        check_binary_installed("docker")
        check_binary_installed("node", Path("/usr/local/bin/node"))
    """
    if symlink_path and Path(symlink_path).exists():
        return True
    if shutil.which(binary_name):
        return True
    return False


def filter_by_status(package_status: Dict[str, bool], wanted: bool) -> List[str]:
    """Return package names whose installed status matches `wanted`."""
    return [name for name, is_installed in package_status.items() if is_installed is wanted]

# ---------------------------------------------------------------------
# DEPENDENCIES
# ---------------------------------------------------------------------


def ensure_dependencies_installed(dependencies):
    """
    Ensure required executables are installed via APT and return True if all succeed.

    Example:
        ensure_dependencies_installed(["wget", "curl"])
    """
    success = True
    for dep in dependencies:
        if not check_package(dep):
            try:
                subprocess.run(["sudo", "apt", "update", "-y"], check=True)
                subprocess.run(["sudo", "apt", "install", "-y", dep], check=True)
            except subprocess.CalledProcessError:
                success = False
    return success

# ---------------------------------------------------------------------
# APT INSTALL / UNINSTALL
# ---------------------------------------------------------------------


def install_packages(packages: Union[str, List[str]]) -> bool:
    """
    Install one or more APT packages and return True on success.

    Example:
        install_packages(["git", "curl"])
    """
    if not packages:
        return False
    if isinstance(packages, str):
        packages = [packages]
    try:
        subprocess.run(["sudo", "apt", "update", "-y"], check=True)
        subprocess.run(["sudo", "apt", "install", "-y"] + packages, check=True)
        return True
    except subprocess.CalledProcessError:
        return False


def uninstall_packages(packages: Union[str, List[str]]) -> bool:
    """
    Uninstall one or more APT packages and return True on success.

    Example:
        uninstall_packages("git")
    """
    if not packages:
        return False
    if isinstance(packages, str):
        packages = [packages]
    try:
        subprocess.run(["sudo", "apt", "remove", "-y"] + packages, check=True)
        subprocess.run(["sudo", "apt", "autoremove", "-y"], check=True)
        return True
    except subprocess.CalledProcessError:
        return False

# ---------------------------------------------------------------------
# DEB DOWNLOAD / INSTALL
# ---------------------------------------------------------------------


def download_deb_file(pkg: str, url: str, download_dir: str | Path, filename: Optional[str] = None) -> bool:
    """
    Download a .deb file from `url` into `download_dir` and return True on success.

    Example:
        download_deb_file("chrome", url, "/tmp/debs", "google-chrome.deb")
    """
    dl_dir = Path(download_dir)
    dl_dir.mkdir(parents=True, exist_ok=True)
    dest = dl_dir / (filename if filename else f"{pkg}.deb")
    print(f"Downloading {pkg} from {url} → {dest.name}")
    result = subprocess.run(["wget", "-q", "--show-progress", "-O", str(dest), url])
    return result.returncode == 0


def install_deb_file(deb_file, name):
    """
    Install a .deb using dpkg, resolving dependencies via apt-get if needed.

    Example:
        install_deb_file(Path("/tmp/google-chrome.deb"), "Chrome")
    """
    if subprocess.run(["sudo", "dpkg", "-i", str(deb_file)]).returncode != 0:
        subprocess.run(["sudo", "apt-get", "install", "-f", "-y"], check=True)
        if subprocess.run(["sudo", "dpkg", "-i", str(deb_file)]).returncode != 0:
            print(f"Retry install failed for {name}")
            return False
    return True
