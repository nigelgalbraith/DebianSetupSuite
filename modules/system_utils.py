#!/usr/bin/env python3
"""
system_utils.py
"""

import os
import re
import socket
import subprocess
import getpass
import datetime
import uuid
import shutil
import pwd
import glob
import stat
import pwd
import grp
from shutil import which
from pathlib import Path
from typing import List, Sequence, Dict, Any, Union, Any, Tuple, Optional

DEFAULT_EXCLUDES = [
    ".git/",
    ".github/",
    ".gitignore",
    ".gitattributes",
    ".gitmodules",
]

class Colors:
    GREEN = "\033[92m"
    BLUE = "\033[94m"
    RED = "\033[91m"
    DIM = "\033[2m"
    RESET = "\033[0m"

  
# ----------------------------------------------------------------------------
# SMALL HELPERS / STATUS
# ----------------------------------------------------------------------------

def check_account(expected_user="standard"):
    """Return True if script is run by the expected user type ("standard" vs "root")."""
    is_root = os.geteuid() == 0
    expected_user = expected_user.lower()
    if expected_user == "standard" and is_root:
        print("Please run this script as a standard (non-root) user.")
        return False
    elif expected_user == "root" and not is_root:
        print("Please run this script as root.")
        return False
    return True


def get_model():
    """Return the system product model name or 'default' if detection fails."""
    try:
        output = subprocess.check_output(["sudo", "dmidecode", "-s", "system-product-name"])
        return output.decode().strip().replace(" ", "")
    except subprocess.CalledProcessError:
        return "default"

def get_host() -> str:
    """Return hostname without spaces."""
    return socket.gethostname().replace(" ", "")


def expand_path(path_str: str) -> Path:
    """Safely expand a path string (supports ~)."""
    return Path(os.path.expanduser(path_str)) if path_str else Path("")


def check_folder_path(path: str) -> bool:
    """Return True if a folder path exists (supports env vars + ~)."""
    return Path(os.path.expandvars(path)).expanduser().exists()


# ----------------------------------------------------------------------------
# USER / GROUP MANAGEMENT
# ----------------------------------------------------------------------------

def create_group(groups) -> bool:
    """Create one or more groups if they don't already exist."""
    if not groups:
        return True
    if isinstance(groups, str):
        groups = [groups]

    ok = True
    for group in groups:
        print(f"[create_group] Ensuring group '{group}' exists...")
        result = subprocess.run(["getent", "group", group], stdout=subprocess.DEVNULL)
        if result.returncode != 0:
            res = subprocess.run(["groupadd", group], check=False)
            if res.returncode == 0:
                print(f"[create_group] Group '{group}' created.")
            else:
                print(f"[create_group] Failed to create '{group}'.")
                ok = False
        else:
            print(f"[create_group] Group '{group}' already exists.")
    return ok


def create_user(username: str) -> bool:
    """Create a system user (nologin) if missing. Return True on success/no-op."""
    import pwd, subprocess
    if not username or not isinstance(username, str):
        print("[create_user] No username provided, skipping.")
        return True
    try:
        pwd.getpwnam(username)
        print(f"[create_user] User '{username}' already exists.")
        return True
    except KeyError:
        print(f"[create_user] User '{username}' not found, creating...")

    try:
        subprocess.run(
            ["useradd", "-r", "-U", "-m", "-s", "/usr/sbin/nologin", username],
            check=True
        )
        print(f"[create_user] User '{username}' created successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[create_user] Failed to create user '{username}': {e}")
        return False


def create_user_login(username: str, groups: list[str] | None = None) -> bool:
    """Create a normal login user (/bin/bash) if missing. Return True on success/no-op."""
    import pwd, subprocess
    if not username or not isinstance(username, str):
        print("[create_user_login] No username provided, skipping.")
        return True
    try:
        pwd.getpwnam(username)
        print(f"[create_user_login] User '{username}' already exists.")
        return True
    except KeyError:
        print(f"[create_user_login] User '{username}' not found, creating...")

    try:
        cmd = ["useradd", "-m", "-s", "/bin/bash", "-U", username]
        subprocess.run(cmd, check=True)
        if groups:
            subprocess.run(["usermod", "-aG", ",".join(groups), username], check=True)
        print(f"[create_user_login] User '{username}' created successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[create_user_login] Failed to create user '{username}': {e}")
        return False


def ensure_user_exists(username: str) -> bool:
    """Ensure a local user exists, creating it if necessary."""
    try:
        subprocess.run(["id", username], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except subprocess.CalledProcessError:
        try:
            subprocess.run(
                ["sudo", "adduser", "--disabled-password", "--gecos", "", username],
                check=True
            )
            return True
        except subprocess.CalledProcessError:
            return False


def remove_user(username: str, remove_home: bool = True) -> bool:
    """Remove a system user. If remove_home=True, remove home/mail too. Return True on success/no-op."""
    import pwd, subprocess
    if not username or not isinstance(username, str):
        print("[remove_user] No username provided, skipping.")
        return True
    try:
        pwd.getpwnam(username)
    except KeyError:
        print(f"[remove_user] User '{username}' does not exist, nothing to do.")
        return True
    try:
        cmd = ["userdel"]
        if remove_home:
            cmd.append("-r")
        cmd.append(username)
        subprocess.run(cmd, check=True)
        print(f"[remove_user] User '{username}' removed successfully.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[remove_user] Failed to remove user '{username}': {e}")
        return False


def kill_user_session(username: str) -> bool:
    """Kill all processes and sessions for a given user."""
    import pwd, subprocess, time
    if not username or not isinstance(username, str):
        print("[kill_user_session] No username provided, skipping.")
        return True
    try:
        pwd.getpwnam(username)
    except KeyError:
        print(f"[kill_user_session] User '{username}' does not exist, nothing to kill.")
        return True
    try:
        subprocess.run(["loginctl", "terminate-user", username], check=False)
        subprocess.run(["pkill", "-u", username], check=False)
        time.sleep(0.5)
        subprocess.run(["pkill", "-KILL", "-u", username], check=False)
        subprocess.run(["loginctl", "disable-linger", username], check=False)
        print(f"[kill_user_session] Killed sessions/processes for '{username}'.")
        return True
    except Exception as e:
        print(f"[kill_user_session] Error killing session for '{username}': {e}")
        return False


def ensure_user_in_group(user: str, group: str) -> bool:
    """Return True if a user is already in a system group."""
    try:
        out = subprocess.run(
            ["id", "-nG", user],
            capture_output=True,
            text=True,
            check=False
        )
        groups = out.stdout.strip().split() if out.returncode == 0 else []
        if group in groups:
            print(f"User '{user}' is already in '{group}'.")
            return True
        else:
            print(f"User '{user}' is NOT in '{group}'.")
            return False
    except Exception as e:
        print(f"Exception while checking user group: {e}")
        return False


def add_user_to_group(users, groups) -> bool:
    """Add one or more users to one or more system groups."""
    if not users or not groups:
        print("[add_user_to_group] No users or groups provided, skipping.")
        return True
    if isinstance(users, str):
        users = [users]
    if isinstance(groups, str):
        groups = [groups]

    ok = True
    for user in users:
        try:
            group_str = ",".join(groups)
            print(f"[add_user_to_group] Adding user '{user}' to group(s): {group_str}...")
            res = subprocess.run(["usermod", "-aG", group_str, user], check=False)
            if res.returncode == 0:
                print(f"[add_user_to_group] User '{user}' added to group(s): {group_str}.")
            else:
                print(f"[add_user_to_group] Failed to add user '{user}' to group(s): {group_str}.")
                ok = False
        except Exception as e:
            print(f"[add_user_to_group] Exception for '{user}': {e}")
            ok = False
    return ok


def add_users_to_group(users: list[str], group: str) -> bool:
    """Add each user in `users` to `group` (idempotent)."""
    if not users or not group:
        print("[add_users_to_group] No users or group")
        return True
    ok = True
    for u in users:
        try:
            add_user_to_group(u, [group])
        except Exception as e:
            print(f"[add_users_to_group] ERROR {u}->{group}: {e}")
            ok = False
    return ok


def configure_group_access(user: str, group: str) -> None:
    """Ensure a user is in a system group, creating the group if needed."""
    grp_exists = subprocess.run(["getent", "group", group], stdout=subprocess.DEVNULL).returncode == 0
    if not grp_exists:
        subprocess.run(["sudo", "groupadd", group], check=True)
    out = subprocess.run(["id", "-nG", user], capture_output=True, text=True, check=True)
    groups = out.stdout.strip().split()
    if group in groups:
        return
    subprocess.run(["sudo", "usermod", "-aG", group, user], check=True)


def create_sudo_user() -> bool:
    """Interactive: create a new user and add them to the sudo group."""
    try:
        username = input("Enter a username to create: ").strip()
        if not username:
            print("No username entered.")
            return False
        result = subprocess.run(["id", username], capture_output=True)
        if result.returncode == 0:
            print(f"User '{username}' already exists.")
            return False
        subprocess.run(["sudo", "adduser", username], check=True)
        subprocess.run(["sudo", "usermod", "-aG", "sudo", username], check=True)
        print(f"User '{username}' created and added to the sudo group.")
        return True
    except subprocess.CalledProcessError as e:
        print(f"ERROR: Failed to create user: {e}")
        return False
    except Exception as e:
        print(f"EXCEPTION: {e}")
        return False


# ----------------------------------------------------------------------------
# TRASH / SAFE REMOVE
# ----------------------------------------------------------------------------

def sudo_remove_path(path: Path | str) -> bool:
    """Move a file or directory to trash using sudo instead of deleting."""
    try:
        path = Path(path).expanduser()
        if not path.exists():
            return False
        trash_root = Path.home() / ".local/share/Trash/plugins"
        trash_root.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        trash_path = trash_root / f"{path.name}_{timestamp}"
        subprocess.run(["sudo", "mv", str(path), str(trash_path)], check=True)
        print(f"[sudo_remove_path] INFO: Moved '{path}' → '{trash_path}'")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[sudo_remove_path] ERROR: {e}")
        return False
    except Exception as e:
        print(f"[sudo_remove_path] EXCEPTION: {e}")
        return False


def move_to_trash(path: str | Path) -> bool:
    """Move a file, directory, or symlink to the user's Trash."""
    try:
        p = Path(os.path.expanduser(str(path)))
        if not p.exists() and not p.is_symlink():
            return True
        try:
            from send2trash import send2trash
            send2trash(str(p))
            return True
        except ImportError:
            pass
        except Exception:
            pass
        try:
            result = subprocess.run(
                ["gio", "trash", str(p)], check=False,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL
            )
            if result.returncode == 0:
                return True
        except Exception:
            pass
        trash_dir = Path.home() / ".local/share/Trash/files"
        trash_dir.mkdir(parents=True, exist_ok=True)
        unique_name = f"{p.name}.{uuid.uuid4().hex}"
        dest = trash_dir / unique_name
        shutil.move(str(p), str(dest))
        return True
    except Exception:
        return False


def remove_paths(paths) -> bool:
    """Move files/folders to the user's trash; supports ~ and globs (*)."""
    if not paths:
        print("[remove_paths] No paths provided, nothing to do.")
        return True
    if isinstance(paths, str):
        paths = [paths]
    if os.geteuid() == 0 and os.environ.get("SUDO_USER"):
        user_home = Path("/home") / os.environ["SUDO_USER"]
    else:
        user_home = Path.home()
    trash_dir = user_home / ".local/share/Trash/files"
    trash_dir.mkdir(parents=True, exist_ok=True)
    print(f"[remove_paths] Trash directory: {trash_dir}")
    all_ok = True
    for p in paths:
        expanded = os.path.expanduser(p)
        matches = glob.glob(expanded)
        if not matches:
            print(f"[remove_paths] No matches for: {p}")
            all_ok = False
            continue
        for match in matches:
            path_obj = Path(match)
            if path_obj.exists():
                try:
                    dest = trash_dir / path_obj.name
                    counter = 1
                    while dest.exists():
                        dest = trash_dir / f"{path_obj.stem}_{counter}{path_obj.suffix}"
                        counter += 1
                    print(f"[remove_paths] Moving {path_obj} -> {dest}")
                    shutil.move(str(path_obj), str(dest))
                    print(f"[remove_paths] Success: {path_obj} moved to trash.")
                except Exception as e:
                    print(f"[remove_paths] ERROR moving {path_obj}: {e}")
                    all_ok = False
            else:
                print(f"[remove_paths] Path does not exist (even after glob): {path_obj}")
                all_ok = False
    print(f"[remove_paths] Completed. all_ok = {all_ok}")
    return all_ok


# ----------------------------------------------------------------------------
# COPY / PERMISSIONS / FILE OPS
# ----------------------------------------------------------------------------


def copy_script_template(src: str | Path, dest: str | Path) -> bool:
    """Copy a file to `dest` and mark it executable; return True on success."""
    try:
        subprocess.run(["cp", str(src), str(dest)], check=True)
        subprocess.run(["chmod", "+x", str(dest)], check=True)
        print(f"[OK]   File copied → {dest}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Copy failed → {src} → {dest} ({e})")
        return False


def copy_file(src: str | Path | None, dest: str | Path | None, optional: bool = False) -> bool:
    """Copy a file to `dest`. If optional=True, skip missing inputs instead of failing."""
    if not src or not dest:
        if optional:
            print("[SKIP] No file to copy (optional).")
            return True
        print("[FAIL] Source or destination missing.")
        return False
    try:
        src_path = Path(src)
        dest_path = Path(dest)
        if not src_path.exists():
            if optional:
                print(f"[SKIP] Optional file not present → {src_path}")
                return True
            print(f"[FAIL] Source file missing → {src_path}")
            return False
        shutil.copy2(src_path, dest_path)
        print(f"[OK]   File copied → {dest_path}")
        return True
    except Exception as e:
        print(f"[FAIL] Copy failed → {src} → {dest} ({e})")
        return False


def copy_files(files) -> bool:
    """Copy a list of configured files."""
    for file in files:
        if not copy_file(
            file.get("Src"),
            file.get("Dest"),
            True,
        ):
            return False
    return True       


def remove_file(path: str | Path | None, optional: bool = False) -> bool:
    """Delete a file or symlink. If optional=True, skip if it doesn't exist."""
    if not path:
        if optional:
            print("[SKIP] No file to remove (optional).")
            return True
        print("[FAIL] No path provided.")
        return False
    try:
        p = Path(path)
        if p.exists() or p.is_symlink():
            p.unlink()
            print(f"[OK]   Removed → {p}")
            return True
        if optional:
            print(f"[SKIP] File not present (optional) → {p}")
            return True
        print(f"[FAIL] File not found → {p}")
        return False
    except Exception as e:
        print(f"[FAIL] Remove failed → {path} ({e})")
        return False


def remove_files(files) -> bool:
    """Remove a list of configured files."""
    for file in files:
        if not remove_file(
            file.get("Dest"),
            True,
        ):
            return False
    return True


def copy_folder(src: str | Path | None, dest: str | Path | None, optional: bool = False) -> bool:
    """Copy a folder to `dest`. If optional=True, skip missing inputs instead of failing."""
    if not src or not dest:
        if optional:
            print("[SKIP] No folder to copy (optional).")
            return True
        print("[FAIL] Source or destination missing.")
        return False
    try:
        src_path = Path(src)
        dest_path = Path(dest)
        if not src_path.exists():
            if optional:
                print(f"[SKIP] Optional folder not present → {src_path}")
                return True
            print(f"[FAIL] Source folder missing → {src_path}")
            return False
        shutil.copytree(
            src_path,
            dest_path,
            dirs_exist_ok=True,
        )
        print(f"[OK]   Folder copied → {dest_path}")
        return True
    except Exception as e:
        print(f"[FAIL] Folder copy failed → {src} → {dest} ({e})")
        return False


def copy_folders(folders) -> bool:
    """Copy a list of configured folders."""
    for folder in folders:
        if not copy_folder(
            folder.get("Src"),
            folder.get("Dest"),
            True,
        ):
            return False
    return True


def remove_folder(path: str | Path | None, optional: bool = False) -> bool:
    """Delete a folder. If optional=True, skip if it doesn't exist."""
    if not path:
        if optional:
            print("[SKIP] No folder to remove (optional).")
            return True
        print("[FAIL] No path provided.")
        return False
    try:
        p = Path(path)
        if p.exists():
            shutil.rmtree(p)
            print(f"[OK]   Removed folder → {p}")
            return True
        if optional:
            print(f"[SKIP] Folder not present (optional) → {p}")
            return True
        print(f"[FAIL] Folder not found → {p}")
        return False
    except Exception as e:
        print(f"[FAIL] Folder remove failed → {path} ({e})")
        return False


def remove_folders(folders) -> bool:
    """Remove a list of configured folders."""
    for folder in folders:
        if not remove_folder(
            folder.get("Dest"),
            True,
        ):
            return False
    return True



def copy_file_dict(mapping: Any) -> bool:
    """Copy multiple files or directories using rsync (expands ~ and $VARS)."""
    results: List[bool] = []
    if isinstance(mapping, dict):
        items: List[Tuple[Any, Any, Optional[str]]] = [(s, d, None) for s, d in mapping.items()]
    elif isinstance(mapping, list):
        items = [(it.get("src"), it.get("dest"), it.get("name")) for it in mapping if isinstance(it, dict)]
    else:
        print(f"{Colors.RED}[ERROR]{Colors.RESET} copy_file_dict: unsupported type {type(mapping).__name__}")
        return False
    if not items:
        print(f"{Colors.BLUE}[INFO]{Colors.RESET} No files to copy.")
        return True
    print(f"{Colors.BLUE}[APPLY]{Colors.RESET} CopyFiles ({len(items)})")
    for src_raw, dest_raw, name in items:
        label = f"{name}: " if name else ""
        try:
            src = os.path.expanduser(os.path.expandvars(str(src_raw)))
            dest = os.path.expanduser(os.path.expandvars(str(dest_raw)))
            if not os.path.exists(src):
                raise FileNotFoundError(f"Source not found: {src}")
            if os.path.isdir(src):
                os.makedirs(dest, exist_ok=True)
                src_arg = src.rstrip(os.sep) + os.sep
                dest_arg = dest.rstrip(os.sep) + os.sep
                cmd = ["rsync", "-a", "--info=NAME", src_arg, dest_arg]
            else:
                Path(dest).parent.mkdir(parents=True, exist_ok=True)
                cmd = ["rsync", "-a", "--info=NAME", src, dest]
            proc = subprocess.run(cmd, text=True, capture_output=True)
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.strip() or f"rsync failed with code {proc.returncode}")
            output = (proc.stdout or "").strip()
            print(f"  - {label}{src_raw} -> {dest_raw}")
            if output:
                print(f"    {Colors.GREEN}Updated:{Colors.RESET} {output}")
            else:
                print(f"    {Colors.DIM}No changes (already up-to-date){Colors.RESET}")
            results.append(True)
        except Exception as e:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Failed to copy {src_raw} → {dest_raw}: {e}")
            results.append(False)
    return all(results)


def copy_folder_dict(mapping: Any, exclude: Optional[List[str]] = None, *, delete_extra: bool = False) -> bool:
    """Copy multiple folders using rsync (expands ~ and $VARS)."""
    results: List[bool] = []
    if isinstance(mapping, dict):
        items = [(s, d, None) for s, d in mapping.items()]
    elif isinstance(mapping, list):
        items = [(it.get("src"), it.get("dest"), it.get("copyName")) for it in mapping if isinstance(it, dict)]
    else:
        print(f"{Colors.RED}[ERROR]{Colors.RESET} copy_folder_dict: unsupported type {type(mapping).__name__}")
        return False
    if not items:
        print(f"{Colors.BLUE}[INFO]{Colors.RESET} No folders to copy.")
        return True
    print(f"{Colors.BLUE}[APPLY]{Colors.RESET} FolderCopies ({len(items)})")
    exclude_patterns: List[str] = DEFAULT_EXCLUDES.copy()
    if exclude:
        for p in exclude:
            if p is None:
                continue
            exclude_patterns.append(str(p))
    for src_raw, dest_raw, name in items:
        label = f"{name}: " if name else ""
        print(f"  - {label}{src_raw} -> {dest_raw}")
        try:
            if not src_raw or not dest_raw:
                raise ValueError("Missing src or dest")
            src = os.path.expanduser(os.path.expandvars(str(src_raw)))
            dest = os.path.expanduser(os.path.expandvars(str(dest_raw)))
            if not os.path.isdir(src):
                raise FileNotFoundError(f"Source folder not found: {src}")
            os.makedirs(dest, exist_ok=True)
            src_arg = src.rstrip(os.sep) + os.sep
            dest_arg = dest.rstrip(os.sep) + os.sep
            cmd = ["rsync", "-a", "--info=NAME"]
            if delete_extra:
                cmd.append("--delete")
            for pattern in exclude_patterns:
                cmd.extend(["--exclude", pattern])
            cmd += [src_arg, dest_arg]
            proc = subprocess.run(cmd, text=True, capture_output=True)
            if proc.returncode != 0:
                raise RuntimeError(proc.stderr.strip() or f"rsync failed with code {proc.returncode}")
            output = (proc.stdout or "").strip()
            if output:
                print(f"    {Colors.GREEN}Changes:{Colors.RESET}")
                for line in output.splitlines():
                    print(f"      {line}")
            else:
                print(f"    {Colors.DIM}No changes (already up-to-date){Colors.RESET}")
            results.append(True)
        except Exception as e:
            print(f"{Colors.RED}[ERROR]{Colors.RESET} Failed to copy {src_raw} → {dest_raw}: {e}")
            results.append(False)
    return all(results)


def sudo_copy_with_chown(src: Path | str, dest: Path | str, owner: str = "plex:plex") -> bool:
    """Copy files or directories with sudo and set ownership."""
    try:
        src = Path(src).expanduser()
        dest = Path(dest).expanduser()
        dest_dir = dest.parent
        subprocess.run(["sudo", "mkdir", "-p", str(dest_dir)], check=True)
        if dest.exists():
            trash_root = Path.home() / ".local/share/Trash/plugins"
            trash_root.mkdir(parents=True, exist_ok=True)
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            trash_name = f"{dest.name}_{timestamp}"
            trash_path = trash_root / trash_name
            subprocess.run(["sudo", "mv", str(dest), str(trash_path)], check=True)
            print(f"[sudo_copy_with_chown] INFO: Moved existing '{dest}' to '{trash_path}'")
        if src.is_dir():
            subprocess.run(["sudo", "cp", "-a", str(src) + "/.", str(dest)], check=True)
        else:
            subprocess.run(["sudo", "cp", "-a", str(src), str(dest)], check=True)
        subprocess.run(["sudo", "chown", "-R", owner, str(dest)], check=False)
        return True
    except subprocess.CalledProcessError as e:
        print(f"[sudo_copy_with_chown] ERROR: {e}")
        return False
    except Exception as e:
        print(f"[sudo_copy_with_chown] EXCEPTION: {e}")
        return False


def fix_permissions(user: str, paths: List[str]) -> bool:
    """Ensure directories exist and are owned by the specified user (recursively)."""
    if not user or not paths:
        print("[fix_permissions] No user or paths provided, skipping.")
        return True
    for p in paths:
        if not p:
            continue
        try:
            if not os.path.exists(p):
                os.makedirs(p, exist_ok=True)
                print(f"[fix_permissions] Created missing directory {p}")
            subprocess.run(["chown", "-R", f"{user}:{user}", p], check=True)
            print(f"[fix_permissions] Set ownership of {p} to {user}:{user}")
        except Exception as e:
            print(f"[fix_permissions] Failed for {p}: {e}")
            return False
    return True


def secure_logs_for_user(path: Path, username: str):
    """Recursively set ownership and secure permissions on logs for a user."""
    try:
        subprocess.run(["chown", "-R", f"{username}:{username}", str(path)], check=True)
        subprocess.run(["find", str(path), "-type", "d", "-exec", "chmod", "700", "{}", "+"], check=True)
        subprocess.run(["find", str(path), "-type", "f", "-exec", "chmod", "600", "{}", "+"], check=True)
    except subprocess.CalledProcessError as e:
        print(f"Error applying permissions: {e}")


def protect_folders(entries: List[Dict[str, Any]]) -> bool:
    """Apply chown + chmod to a list of protected folder entries."""
    if not entries:
        return True
    ok = True
    for entry in entries:
        try:
            path = entry.get("path")
            if not path:
                continue
            owner = entry.get("owner", "root")
            group = entry.get("group", "root")
            perms = entry.get("permissions", "755")
            p = Path(path)
            if not p.exists():
                print(f"[protect_folders] WARNING: {p} missing; skipping")
                ok = False
                continue
            target = f"{owner}:{group}"
            subprocess.run(["chown", target, str(p)], check=True)
            os.chmod(p, int(perms, 8))
            print(f"[protect_folders] chown {target} {p}")
            print(f"[protect_folders] chmod {perms} {p}")
        except Exception as e:
            print(f"[protect_folders] ERROR: {entry.get('path','?')}: {e}")
            ok = False
    return ok


def chmod_paths(entries, recursive: bool = False) -> bool:
    """Apply chmod to paths; supports per-entry 'recursive' for directories."""
    if not entries:
        return True
    ok = True
    for item in entries:
        if isinstance(item, dict):
            path = item.get("path")
            mode = item.get("mode", "644")
            rec = bool(item.get("recursive", recursive))
        else:
            path, mode, rec = item, "644", recursive
        try:
            p = Path(path)
            if not p.exists():
                print(f"[chmod_paths] WARNING: {p} missing; skipping")
                ok = False
                continue
            mode_i = int(mode, 8)
            if rec and p.is_dir():
                for root, dirs, files in os.walk(p):
                    os.chmod(root, mode_i)
                    for d in dirs:
                        os.chmod(Path(root) / d, mode_i)
                    for f in files:
                        os.chmod(Path(root) / f, mode_i)
                print(f"[chmod_paths] chmod -R {mode} {p}")
            else:
                os.chmod(p, mode_i)
                print(f"[chmod_paths] chmod {mode} {p}")
        except Exception as e:
            print(f"[chmod_paths] ERROR: {path}: {e}")
            ok = False
    return ok


def chown_paths(user: str, paths: list[dict], recursive: bool=False, default_group: str|None=None) -> bool:
    """Apply chown to paths; supports per-entry group + per-entry recursion."""
    if not user or not paths:
        return True
    ok = True
    for item in paths:
        p = item.get("path")
        if not p:
            continue
        owner = user
        group = item.get("group", default_group or user)
        rec = item.get("recursive", recursive) and Path(p).is_dir()
        try:
            target = f"{owner}:{group}"
            if rec:
                subprocess.run(["chown", "-R", target, p], check=True)
            else:
                subprocess.run(["chown", target, p], check=True)
            print(f"[chown_paths] chown {target} {p}{' (recursive)' if rec else ''}")
        except Exception as e:
            print(f"[chown_paths] ERROR: {p}: {e}")
            ok = False
    return ok


def make_dirs(dirs: list[str]) -> bool:
    """Ensure all directories in the list exist. Returns True if successful/no-op."""
    try:
        for d in dirs:
            path = os.path.expanduser(os.path.expandvars(d))
            os.makedirs(path, exist_ok=True)
            print(f"[make_dirs] Ensured directory exists: {path}")
        return True
    except Exception as e:
        print(f"[make_dirs] Error creating directories: {e}")
        return False


# ----------------------------------------------------------------------------
# COMMAND / SCRIPT RUNNERS
# ----------------------------------------------------------------------------

def run_commands(post_install_cmds) -> bool:
    """Run post-install shell commands and return True only if all succeed."""
    if isinstance(post_install_cmds, str):
        cmds = [os.path.expanduser(post_install_cmds)]
    elif isinstance(post_install_cmds, list):
        cmds = [os.path.expanduser(c) for c in post_install_cmds if isinstance(c, str)]
    else:
        cmds = []
    all_ok = True
    for cmd in cmds:
        rc = os.system(cmd)
        if rc != 0:
            print(f"PostInstall failed (rc={rc}): {cmd}")
            all_ok = False
    return all_ok


def run_script_dict(scripts: List[Dict[str, Any]]) -> bool:
    """Run script dict entries: {'script': 'path', 'args': [...]} and return True if all succeed."""
    script_runners = {
        ".sh":   ["bash"],
        ".bash": ["bash"],
        ".py":   ["python3"],
    }
    for entry in scripts:
        script = entry.get("script")
        args   = entry.get("args", [])
        if not script:
            raise ValueError("Script entry missing 'script' key")
        script_path = Path(script).expanduser()
        if not script_path.exists():
            raise FileNotFoundError(f"Script not found: {script_path}")
        ext = script_path.suffix.lower()
        if ext in script_runners:
            cmd = script_runners[ext] + [str(script_path)] + list(args)
        else:
            cmd = [str(script_path)] + list(args)
        subprocess.run(cmd, check=True)
    return True


def convert_dict_list_to_str(
    jobs: list[dict[str, Any]],
    from_key: str = "new_line_list",
    to_key: str = "new_line",
    sep: str | None = None,
) -> list[dict[str, Any]]:
    """Join job[from_key] into job[to_key] using job['sep'] or fallback sep; raise if missing."""
    for job in jobs:
        if from_key not in job:
            continue
        parts = job[from_key]
        if not isinstance(parts, list) or not all(isinstance(p, str) for p in parts):
            raise ValueError(f"{from_key} must be a list[str] in PatternJob '{job.get('patternName','?')}'")
        job_sep = job.get("sep", sep)
        if job_sep is None:
            raise ValueError(f"Missing 'sep' in PatternJob '{job.get('patternName','?')}'. Pass it in the JSON.")

        if parts:
            first, *rest = parts
            if " " in first:
                key, first_val = first.split(maxsplit=1)
                joined = job_sep.join([first_val] + rest) if rest or first_val else first_val
                job[to_key] = f"{key} {joined}"
            else:
                job[to_key] = job_sep.join(parts)
        del job[from_key]
    return jobs


# ----------------------------------------------------------------------------
# SYSTEM / DISPLAY / SYSTEMD
# ----------------------------------------------------------------------------

def reload_systemd() -> bool:
    """Reload systemd to apply changes."""
    try:
        subprocess.run(
            ["systemctl", "daemon-reload"],
            check=True,
        )
        print("[OK]   Systemd daemon reloaded")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[FAIL] Systemd daemon reload failed ({e})")
        return False
    except Exception as e:
        print(f"[FAIL] Unexpected systemd reload error ({e})")
        return False


def reload_user_systemd() -> bool:
    """Reload the user systemd daemon for the user who launched DebianLoader with sudo."""
    user = os.environ.get("SUDO_USER")
    if not user:
        print("[FAIL] Unable to determine sudo user")
        return False
    try:
        uid = subprocess.run(
            ["id", "-u", user],
            capture_output=True,
            text=True,
            check=True,
        ).stdout.strip()
        result = subprocess.run(
            [
                "runuser",
                "-u",
                user,
                "--",
                "env",
                f"XDG_RUNTIME_DIR=/run/user/{uid}",
                f"DBUS_SESSION_BUS_ADDRESS=unix:path=/run/user/{uid}/bus",
                "systemctl",
                "--user",
                "daemon-reload",
            ],
            capture_output=True,
            text=True,
            check=False,
        )
        if result.returncode == 0:
            print(f"[OK]   User systemd daemon reloaded → {user}")
            return True
        print(
            f"[FAIL] User systemd daemon reload failed → "
            f"{user} ({result.stderr.strip()})"
        )
        return False
    except Exception as e:
        print(f"[FAIL] User systemd daemon reload failed → {user} ({e})")
        return False


def set_default_display_manager(dm_package: str, dm_service: str) -> bool:
    """Set default display manager + refresh display-manager.service alias and set graphical target."""
    try:
        default_file = Path("/etc/X11/default-display-manager")
        alias_link   = Path("/etc/systemd/system/display-manager.service")
        real_unit    = Path(f"/lib/systemd/system/{dm_service}.service")
        dm_path      = f"/usr/sbin/{dm_package}"
        default_file.parent.mkdir(parents=True, exist_ok=True)
        default_file.write_text(dm_path + "\n")
        print(f"[INFO] Default display manager set to: {dm_path}")
        if not real_unit.exists():
            print(f"[ERROR] Expected unit not found: {real_unit}")
            return False
        try:
            alias_link.unlink(missing_ok=True)
        except Exception:
            pass
        alias_link.symlink_to(real_unit)
        print(f"[INFO] Linked {alias_link} → {real_unit}")
        subprocess.run(["systemctl", "daemon-reload"], check=True)
        subprocess.run(["systemctl", "set-default", "graphical.target"], check=True)
        print("[INFO] Graphical target set as default.")
        return True
    except Exception as e:
        print(f"[ERROR] set_default_display_manager({dm_package}, {dm_service}) failed: {e}")
        return False
