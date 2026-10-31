#!/usr/bin/env python3
"""
docker_utils.py

Small wrapper utilities for checking, building, and controlling Docker containers/images.

Also includes helpers for Docker Compose workloads.
"""

import os
import subprocess
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

# ---------------------------------------------------------------------
# INTERNAL HELPERS
# ---------------------------------------------------------------------


def _run(cmd: Sequence[str], *, cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    """Run a command and return the CompletedProcess without raising."""
    return subprocess.run(list(cmd), cwd=str(cwd) if cwd else None, check=False)


def _compose_cmd() -> Tuple[str, ...]:
    """Return the preferred compose command (docker compose vs docker-compose)."""
    try:
        res = _run(["docker", "compose", "version"])
        if res.returncode == 0:
            return ("docker", "compose")
    except Exception:
        pass
    return ("docker-compose",)


def _compose_workdir(compose_file: str, compose_dir: Optional[str]) -> Path:
    """Resolve working directory for compose commands."""
    if compose_dir:
        return Path(compose_dir).expanduser().resolve()
    return Path(compose_file).expanduser().resolve().parent


# ---------------------------------------------------------------------
# IMAGE / CONTAINER CHECKS
# ---------------------------------------------------------------------


def docker_image_doesnt_exist(image_name: str) -> bool:
    """Return True if the Docker image does not exist locally."""
    try:
        result = subprocess.run(
            ["docker", "images", "-q", image_name],
            capture_output=True, text=True, check=False
        )
        missing = (result.returncode == 0 and result.stdout.strip() == "")
        print(f"[CHECK] Image '{image_name}': {'absent' if missing else 'present'}")
        return missing
    except Exception as e:
        print(f"[ERROR] Could not check image '{image_name}': {e}")
        return False


def docker_container_running(name: str) -> bool:
    """Return True if the Docker container `name` is currently running."""
    try:
        result = subprocess.run(
            ["docker", "ps", "-q", "-f", f"name={name}"],
            capture_output=True, text=True, check=False
        )
        running = (result.returncode == 0 and result.stdout.strip() != "")
        print(f"[CHECK] Container '{name}': {'RUNNING' if running else 'not running'}")
        return running
    except Exception as e:
        print(f"[ERROR] Could not check running status for '{name}': {e}")
        return False


def docker_workload_running(job_name: str, meta: dict, compose_key_or_list) -> bool:
    """
    Return True if a docker workload is running.

    The third arg may be:
    - a string key (e.g. "ComposeContainers"), OR
    - the actual list of compose container names (depending on loader arg resolution).
    """
    if isinstance(compose_key_or_list, list):
        compose_containers = compose_key_or_list
    else:
        compose_containers = meta.get(compose_key_or_list) or []
    if isinstance(compose_containers, list) and compose_containers:
        return all(docker_container_running(c) for c in compose_containers)
    return docker_container_running(job_name)



def docker_container_exists(name: str) -> bool:
    """Return True if the Docker container `name` exists (running or stopped)."""
    try:
        result = subprocess.run(
            ["docker", "ps", "-aq", "-f", f"name={name}"],
            capture_output=True, text=True, check=False
        )
        exists = (result.returncode == 0 and result.stdout.strip() != "")
        print(f"[CHECK] Container '{name}': {'exists' if exists else 'missing'}")
        return exists
    except Exception as e:
        print(f"[ERROR] Could not check existence for '{name}': {e}")
        return False


def check_all_containers_running(container_names: List[str]) -> bool:
    """Return True only if every container in container_names is running."""
    if not container_names:
        print("[CHECK] Compose container list is empty; treating as NOT running.")
        return False
    ok = True
    for name in container_names:
        ok = ok and docker_container_running(name)
    return ok


# ---------------------------------------------------------------------
# BUILD / RUN CONTROL (single-container)
# ---------------------------------------------------------------------


def build_docker_container(container_name: str, docker_container_loc: str, image_name: str) -> bool:
    """
    Build a Docker image from a directory containing a Dockerfile.

    Ensures the build directory exists before running `docker build` inside it.

    Example:
        build_docker_container("myapp", "./docker", "myapp:latest")
    """
    try:
        target = Path(docker_container_loc).expanduser().resolve()
        target.mkdir(parents=True, exist_ok=True)
        print(f"[BUILD] {image_name} from {target} (container '{container_name}')")
        result = subprocess.run(
            ["docker", "build", "-t", image_name, "."],
            cwd=target,
            check=False
        )
        if result.returncode == 0:
            print(f"[OK]    Built image: {image_name}")
            return True
        print(f"[FAIL]  Build failed for image: {image_name}")
        return False
    except Exception as e:
        print(f"[ERROR] Build error for '{container_name}': {e}")
        return False


def start_container(container_name: str, port_mapping: str, image_name: str) -> bool:
    """
    Start a Docker container, replacing any stopped container with the same name.

    Example:
        start_container("myapp", "8080:80", "myapp:latest")
    """
    try:
        if docker_container_running(container_name):
            print(f"[OK]    Container '{container_name}' already running.")
            return True
        if docker_container_exists(container_name):
            print(f"[CLEAN] Removing stopped container '{container_name}' before start ...")
            subprocess.run(["docker", "rm", container_name], check=False)
        cmd = ["docker", "run", "-d"]
        if port_mapping:
            cmd += ["-p", port_mapping]
        cmd += ["--name", container_name, image_name]
        print(f"[RUN]   {' '.join(cmd)}")
        res = subprocess.run(cmd, check=False)
        if res.returncode == 0:
            print(f"[OK]    Container '{container_name}' started.")
            return True
        print(f"[FAIL]  Failed to start container '{container_name}'.")
        return False
    except Exception as e:
        print(f"[ERROR] Start error for '{container_name}': {e}")
        return False


def stop_container(container_name: str) -> bool:
    """
    Stop a running Docker container (idempotent).

    Example:
        stop_container("myapp")
    """
    try:
        if docker_container_running(container_name):
            print(f"[STOP]  Stopping '{container_name}' ...")
            res = subprocess.run(["docker", "stop", container_name], check=False)
            if res.returncode == 0:
                print(f"[OK]    Container '{container_name}' stopped.")
                return True
            print(f"[FAIL]  Failed to stop container '{container_name}'.")
            return False
        print(f"[SKIP]  '{container_name}' is not running.")
        return True
    except Exception as e:
        print(f"[ERROR] Stop error for '{container_name}': {e}")
        return False


def remove_container(container_name: str) -> bool:
    """
    Remove a Docker container if it exists (idempotent, forceful).

    Example:
        remove_container("myapp")
    """
    try:
        if docker_container_exists(container_name):
            print(f"[RM]    Removing container '{container_name}' ...")
            res = subprocess.run(
                ["docker", "rm", "-f", container_name],
                check=False
            )
            if res.returncode == 0:
                print(f"[OK]    Container '{container_name}' removed.")
                return True
            print(f"[FAIL]  Failed to remove container '{container_name}'.")
            return False
        print(f"[SKIP]  Container '{container_name}' does not exist.")
        return True
    except Exception as e:
        print(f"[ERROR] Remove error for '{container_name}': {e}")
        return False



def status_container(container_name: str) -> bool:
    """Print the status of a Docker container and return True on success."""
    try:
        if docker_container_running(container_name):
            print(f"[STATUS] '{container_name}': RUNNING")
        elif docker_container_exists(container_name):
            print(f"[STATUS] '{container_name}': STOPPED")
        else:
            print(f"[STATUS] '{container_name}': DOES NOT EXIST")
        return True
    except Exception as e:
        print(f"[ERROR] Status error for '{container_name}': {e}")
        return False


# ---------------------------------------------------------------------
# DOCKER COMPOSE HELPERS
# ---------------------------------------------------------------------


def compose_build(compose_file: str, compose_dir: Optional[str] = None) -> bool:
    """Build images for a compose project."""
    try:
        workdir = _compose_workdir(compose_file, compose_dir)
        cmd = [*_compose_cmd(), "-f", str(Path(compose_file).expanduser()), "build"]
        print(f"[COMPOSE] {' '.join(cmd)}  (cwd={workdir})")
        res = _run(cmd, cwd=workdir)
        return res.returncode == 0
    except Exception as e:
        print(f"[ERROR] Compose build error: {e}")
        return False


def compose_up(compose_file: str, compose_dir: Optional[str] = None) -> bool:
    """Start a compose project in detached mode (no implicit build)."""
    try:
        workdir = _compose_workdir(compose_file, compose_dir)
        cmd = [*_compose_cmd(), "-f", str(Path(compose_file).expanduser()), "up", "-d"]
        print(f"[COMPOSE] {' '.join(cmd)}  (cwd={workdir})")
        res = _run(cmd, cwd=workdir)
        return res.returncode == 0
    except Exception as e:
        print(f"[ERROR] Compose up error: {e}")
        return False


def compose_down(compose_file: str, compose_dir: Optional[str] = None) -> bool:
    """Stop and remove a compose project (containers/networks)."""
    try:
        workdir = _compose_workdir(compose_file, compose_dir)
        cmd = [*_compose_cmd(), "-f", str(Path(compose_file).expanduser()), "down"]
        print(f"[COMPOSE] {' '.join(cmd)}  (cwd={workdir})")
        res = _run(cmd, cwd=workdir)
        return res.returncode == 0
    except Exception as e:
        print(f"[ERROR] Compose down error: {e}")
        return False


def status_compose(project_name: str, container_names: List[str]) -> bool:
    """Print a one-line status for a compose workload; return True if all listed containers are running."""
    try:
        ok = check_all_containers_running(container_names)
        print(f"[STATUS] '{project_name}': {'RUNNING' if ok else 'STOPPED'}")
        if not container_names:
            print("         (no ComposeContainers defined)")
        return True
    except Exception as e:
        print(f"[ERROR] Compose status error for '{project_name}': {e}")
        return False
