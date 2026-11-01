#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from pathlib import Path
from modules.archive_utils import (
    download_archive_file,
    install_archive_file,
    check_archive_status,
    handle_cleanup,
)

from modules.system_utils import (
    run_commands,
    chmod_paths,
    chown_paths,
    create_group,
    add_user_to_group,
    protect_folders,
    copy_file_dict,
    group_exists,
    user_not_in_group,
)
from modules.desktop_utils import (
    create_desktop_entry,
    remove_desktop_entry,
    refresh_desktop_database,
)
from modules.display_utils import display_config_doc

# === CONFIG PATHS & KEYS ===
PRIMARY_CONFIG   = "config/AppConfigSettings.json"
JOBS_KEY         = "DOSLoader"
CONFIG_TYPE      = "dosloader"
DEFAULT_CONFIG   = "Default"
CONFIG_DOC       = "doc/DOSLoaderDoc.json"

# === JSON KEYS ===
KEY_NAME           = "Name"
KEY_DOWNLOAD_URL   = "DownloadURL"
KEY_EXTRACT_TO     = "ExtractTo"
KEY_CHECK_PATH     = "CheckPath"
KEY_STRIP_TOP      = "StripTopLevel"
KEY_LAUNCH_CMD     = "LaunchCmd"
KEY_POST_INSTALL   = "PostInstall"
KEY_DOWNLOAD_PATH  = "DownloadPath"
KEY_ICON           = "Icon"
KEY_ICO_FILE       = "IconFile"
KEY_CATEGORY       = "Category"

# === MEMBERSHIP / FOLDER ACCESS ===
KEY_DOS_USERS         = "DosUsers"
KEY_DOS_GROUPS        = "DosGroups"
KEY_CHOWN_USER        = "ChownUser"
KEY_CHOWN_GROUP       = "ChownGroup"
KEY_CHOWN_PATHS       = "ChownPaths"
KEY_CHOWN_RECURSIVE   = "ChownRecursive"
KEY_CHMOD_PATHS       = "ChmodPaths"
KEY_PROTECTED_FOLDERS = "ProtectedFolders"

# === VALIDATION CONFIG ===
VALIDATION_CONFIG = {
    "required_job_fields": {
        KEY_NAME: str,
        KEY_DOWNLOAD_URL: str,
        KEY_EXTRACT_TO: str,
        KEY_CHECK_PATH: str,
        KEY_STRIP_TOP: bool,
        KEY_LAUNCH_CMD: str,
        KEY_CHMOD_PATHS: list,
        KEY_CHOWN_PATHS: list,
        KEY_PROTECTED_FOLDERS: list,
        KEY_ICO_FILE: list,
    },
    "example_config": CONFIG_DOC,
}

# === SECONDARY VALIDATION  ===
SECONDARY_VALIDATION = {
    KEY_CHMOD_PATHS: {
        "required_job_fields": {
            "path": str,
            "mode": str,
            "recursive": bool,
        },
        "allow_empty": True,
    },
    KEY_CHOWN_PATHS: {
        "required_job_fields": {
            "path": str,
        },
        "allow_empty": True,
    },
    KEY_PROTECTED_FOLDERS: {
        "required_job_fields": {
            "path": str,
            "owner": str,
            "group": str,
            "permissions": str,
        },
        "allow_empty": True,
    },
    "example_config": CONFIG_DOC,
}

# === DETECTION CONFIG ===
DETECTION_CONFIG = {
    "primary_config": PRIMARY_CONFIG,
    "config_type": CONFIG_TYPE,
    "jobs_key": JOBS_KEY,
    "default_config": DEFAULT_CONFIG,
    "default_config_note": (
        "No model-specific config was found. Using the 'Default' section instead."
    ),
}

# === LOGGING ===
LOG_PREFIX      = "dosloader"
LOG_DIR         = Path.home() / "logs" / "dosloader"
LOGS_TO_KEEP    = 10
ROTATE_LOG_NAME = f"{LOG_PREFIX}_*.log"

# === USER / LABELS ===
REQUIRED_USER     = "root"
INSTALLED_LABEL   = "INSTALLED"
UNINSTALLED_LABEL = "UNINSTALLED"

# === STATUS CHECK CONFIG ===
STATUS_FN_CONFIG = {
    "fn": check_archive_status,
    "args": [KEY_CHECK_PATH, KEY_EXTRACT_TO],
    "labels": {True: INSTALLED_LABEL, False: UNINSTALLED_LABEL},
}

# === MENU / ACTIONS ===
ACTIONS = {
    "_meta": {"title": "Select an option"},
    f"Install {JOBS_KEY} game": {
        "verb": "installation",
        "filter_status": False,
        "label": INSTALLED_LABEL,
        "prompt": "Proceed with installation? [y/n]: ",
        "execute_state": "INSTALL",
        "post_state": "MENU_SELECTION",
    },
    f"Update {JOBS_KEY} permissions": {
        "verb": "update permissions",
        "filter_status": True,
        "label": INSTALLED_LABEL,
        "prompt": "Update permissions now? [y/n]: ",
        "execute_state": "UPDATE_PERMISSIONS",
        "post_state": "MENU_SELECTION",
    },
    f"Create {JOBS_KEY} game shortcut": {
        "verb": "create shortcut",
        "filter_status": True,
        "label": INSTALLED_LABEL,
        "prompt": "Launch now? [y/n]: ",
        "execute_state": "CREATE_SHORTCUT",
        "post_state": "MENU_SELECTION",
    },
    f"Remove {JOBS_KEY} game shortcut": {
        "verb": "remove shortcut",
        "filter_status": None,
        "label": None,
        "prompt": f"Remove {JOBS_KEY} game shortcut? [y/n]: ",
        "execute_state": "REMOVE_SHORTCUT",
        "post_state": "CONFIG_LOADING",
    },
    "Show config help": {
        "verb": "help",
        "filter_status": None,
        "label": None,
        "prompt": "Show config help now? [y/n]: ",
        "execute_state": "SHOW_CONFIG_DOC",
        "post_state": "MENU_SELECTION",
        "skip_sub_select": True,
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "Cancel": {
        "verb": None,
        "filter_status": None,
        "label": None,
        "prompt": None,
        "execute_state": "FINALIZE",
        "post_state": "FINALIZE",
    },
}

# === SUB MENU ===
SUB_MENU = {
    "title": "Select DOS Game",
    "all_label": "All",
    "cancel_label": "Cancel",
    "cancel_state": "MENU_SELECTION",
}

# === DEPENDENCIES ===
DEPENDENCIES = ["dosbox", "wget", "unzip", "tar", "unrar-free", "p7zip-full"]

# === PLAN TABLE COLUMNS
PLAN_COLUMN_ORDER = [
    KEY_NAME,
    KEY_DOWNLOAD_URL,
    KEY_EXTRACT_TO,
    KEY_CHECK_PATH,
    KEY_STRIP_TOP,
    KEY_LAUNCH_CMD,
]

OPTIONAL_PLAN_COLUMNS = {}

# === PIPELINES ===
PIPELINE_STATES = {
    "INSTALL": {
        "pipeline": {
            download_archive_file: {
                "args": ["job", KEY_DOWNLOAD_URL, KEY_DOWNLOAD_PATH],
                "result": "archive_path",
            },
            install_archive_file: {
                "args": ["archive_path", KEY_EXTRACT_TO, KEY_STRIP_TOP],
                "when": "archive_path",
                "result": "installed",
            },
            handle_cleanup: {
                "args": ["archive_path"],
                "when": "installed",
            },
            run_commands: {
                "args": [KEY_POST_INSTALL],
                "when": "installed",
            },
            create_group: {
                "args": [f"?{KEY_DOS_GROUPS}"],
                "when": "installed",
                "result": "groups_created",
            },
            group_exists: {
                "args": [f"?{KEY_DOS_GROUPS}"],
                "when": "groups_created",
                "result": "group_exists",
            },
            user_not_in_group: {
                "args": [f"?{KEY_DOS_USERS}", f"?{KEY_DOS_GROUPS}"],
                "when": "group_exists",
                "result": "user_needs_group",
            },
            add_user_to_group: {
                "args": [f"?{KEY_DOS_USERS}", f"?{KEY_DOS_GROUPS}"],
                "when": "user_needs_group",
            },
            chown_paths: {
                "args": [
                    f"?{KEY_CHOWN_USER}",
                    KEY_CHOWN_PATHS,
                    f"?{KEY_CHOWN_RECURSIVE}",
                    f"?{KEY_CHOWN_GROUP}",
                ],
                "when": "installed",
                "result": "chown_ok",
            },
            chmod_paths: {
                "args": [KEY_CHMOD_PATHS],
                "when": "installed",
                "result": "chmod_ok",
            },
            protect_folders: {
                "args": [KEY_PROTECTED_FOLDERS],
                "when": "installed",
                "result": "protected_ok",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "installed",
        "post_state": "CONFIG_LOADING",
    },
    "UPDATE_PERMISSIONS": {
        "pipeline": {
            create_group: {
                "args": [f"?{KEY_DOS_GROUPS}"],
                "result": "groups_created",
            },
            group_exists: {
                "args": [f"?{KEY_DOS_GROUPS}"],
                "when": "groups_created",
                "result": "group_exists",
            },
            user_not_in_group: {
                "args": [f"?{KEY_DOS_USERS}", f"?{KEY_DOS_GROUPS}"],
                "when": "group_exists",
                "result": "user_needs_group",
            },
            add_user_to_group: {
                "args": [f"?{KEY_DOS_USERS}", f"?{KEY_DOS_GROUPS}"],
                "when": "user_needs_group",
            },
            chown_paths: {
                "args": [
                    f"?{KEY_CHOWN_USER}",
                    KEY_CHOWN_PATHS,
                    f"?{KEY_CHOWN_RECURSIVE}",
                    f"?{KEY_CHOWN_GROUP}",
                ],
                "result": "chown_ok",
            },
            chmod_paths: {
                "args": [KEY_CHMOD_PATHS],
                "result": "chmod_ok",
            },
            protect_folders: {
                "args": [KEY_PROTECTED_FOLDERS],
                "result": "protected_ok",
            },
        },
        "label": "PERMISSIONS_UPDATED",
        "success_key": "protected_ok",
        "post_state": "CONFIG_LOADING",
    },
    "CREATE_SHORTCUT": {
        "pipeline": {
            copy_file_dict: {
                "args": [KEY_ICO_FILE],
                "result": "icons_copied",
            },
            create_desktop_entry: {
                "args": [
                    KEY_NAME,
                    KEY_LAUNCH_CMD,
                    f"?{KEY_CHOWN_USER}",
                    KEY_ICON,
                    KEY_CATEGORY,
                ],
                "when": "icons_copied",
                "result": "shortcut_created",
            },
            refresh_desktop_database: {
                "args": [],
                "when": "shortcut_created",
                "result": "desktop_cache_refreshed",
            },
        },
        "label": "SHORTCUT",
        "success_key": "shortcut_created",
        "post_state": "CONFIG_LOADING",
    },
    "REMOVE_SHORTCUT": {
        "pipeline": {
            remove_desktop_entry: {
                "args": [KEY_NAME, f"?{KEY_CHOWN_USER}"],
                "result": "shortcut_removed",
            },
            refresh_desktop_database: {
                "args": [],
                "when": "shortcut_removed",
                "result": "desktop_cache_refreshed",
            },
        },
        "label": "SHORTCUT_REMOVED",
        "success_key": "shortcut_removed",
        "post_state": "CONFIG_LOADING",
    },
    "SHOW_CONFIG_DOC": {
        "pipeline": {
            display_config_doc: {
                "args": [CONFIG_DOC],
                "result": "ok",
            },
        },
        "label": "DONE",
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
}
