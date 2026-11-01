from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

from modules.system_utils import (
    copy_file_dict,
    copy_folder_dict,
    make_dirs,
    run_commands,
    run_script_dict,
    chmod_paths,
    chown_paths,
    create_group,
    add_user_to_group,
    remove_paths,
    protect_folders,
    group_exists,
    user_not_in_group,
)
from modules.package_utils import (
    check_package, install_packages, 
    uninstall_packages,
)
from modules.display_utils import (
    display_config_doc
)

# === CONFIG PATHS & KEYS ===
PRIMARY_CONFIG   = "config/AppConfigSettings.json"
JOBS_KEY         = "Arcade"
CONFIG_TYPE      = "mame"
DEFAULT_CONFIG   = "Default"
CONFIG_DOC       = "doc/ArcadeDoc.json"

# === JSON KEYS ===
KEY_SETUP_CMDS         = "SetupCmds"
KEY_SETUP_SCRIPTS      = "SetupScripts"
KEY_RESET_CMDS         = "ResetCmds"
KEY_SETTINGS_FILES     = "SettingsFiles"
KEY_SETTINGS_FOLDERS   = "SettingsFolders"
KEY_PACKAGES           = "Packages"
KEY_REMOVE_PATHS       = "RemovePaths"
KEY_SETUP_DIRS         = "SetupDirs"
KEY_RESET_DIRS         = "ResetDirs"
KEY_CHMOD_PATHS        = "ChmodPaths"
KEY_CHOWN_PATHS        = "ChownPaths"
KEY_CHOWN_USER         = "ChownUser"
KEY_CHOWN_GROUP        = "ChownGroup"
KEY_CHOWN_RECURSIVE    = "ChownRecursive"
KEY_PROTECTED_FOLDERS  = "ProtectedFolders"
KEY_SCRIPT             = "script"
KEY_ARGS               = "args"

# Membership (arcade-specific)
KEY_ARCADE_USERS       = "arcadeUsers"
KEY_ARCADE_GROUPS      = "arcadeGroups"

# === SUB-JSON KEYS ===
KEY_COPY_NAME          = "copyName"
KEY_SRC                = "src"
KEY_DEST               = "dest"


# === VALIDATION CONFIG ===
VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        KEY_PACKAGES: list,
        KEY_SETTINGS_FILES: list,
        KEY_SETTINGS_FOLDERS: list,
        KEY_REMOVE_PATHS: list,
        KEY_SETUP_DIRS: list,
        KEY_RESET_DIRS: list,
        KEY_SETUP_CMDS: list,
        KEY_SETUP_SCRIPTS: list,
        KEY_RESET_CMDS: list,
        KEY_CHMOD_PATHS: list,
        KEY_CHOWN_PATHS: list,
    },
    "example_config": CONFIG_DOC,
}

# === SECONDARY VALIDATION ===
SECONDARY_VALIDATION: Dict[str, Any] = {
    KEY_SETTINGS_FILES: {
        "required_job_fields": {
            KEY_COPY_NAME: str,
            KEY_SRC: str,
            KEY_DEST: str,
        },
        "allow_empty": True,
    },
    KEY_SETTINGS_FOLDERS: {
        "required_job_fields": {
            KEY_COPY_NAME: str,
            KEY_SRC: str,
            KEY_DEST: str,
        },
        "allow_empty": True,
    },
    KEY_SETUP_SCRIPTS: {
        "required_job_fields": {
            KEY_SCRIPT: str,
            KEY_ARGS: list,
        },
        "allow_empty": True,
    },
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
DETECTION_CONFIG: Dict[str, Any] = {
    "primary_config": PRIMARY_CONFIG,
    "config_type": CONFIG_TYPE,
    "jobs_key": JOBS_KEY,
    "default_config": DEFAULT_CONFIG,
    "default_config_note": (
        "No model-specific MAME config was found. "
        "Using the 'Default' section instead. "
    ),
}

# === LOGGING ===
LOG_PREFIX      = "mame_setup"
LOG_DIR         = Path.home() / "logs" / "mame"
LOGS_TO_KEEP    = 10
ROTATE_LOG_NAME = f"{LOG_PREFIX}_*.log"

# === USER / LABELS ===
REQUIRED_USER       = "root"
INSTALLED_LABEL     = "INSTALLED"
UNINSTALLED_LABEL   = "UNINSTALLED"
RESET_LABEL         = "Reset"

# === STATUS CHECK CONFIG ===
STATUS_FN_CONFIG = {
    "fn": check_package,
    "args": ["job"],
    "labels": {True: INSTALLED_LABEL, False: UNINSTALLED_LABEL},
}

# === COLUMN ORDER ===
PLAN_COLUMN_ORDER = [
    KEY_PACKAGES,
    KEY_SETTINGS_FILES,
    KEY_SETTINGS_FOLDERS,
    KEY_REMOVE_PATHS,
    KEY_SETUP_DIRS,
    KEY_SETUP_SCRIPTS,
    KEY_SETUP_CMDS,
    KEY_CHMOD_PATHS,
    KEY_CHOWN_PATHS,
    KEY_RESET_DIRS,
    KEY_RESET_CMDS,
]
OPTIONAL_PLAN_COLUMNS = {}

# === ACTIONS ===
ACTIONS: Dict[str, Dict[str, Any]] = {
    "_meta": {"title": f"{JOBS_KEY} Setup"},

    f"Install / Configure {JOBS_KEY}": {
        "verb": "install",
        "filter_status": False,
        "label": UNINSTALLED_LABEL,
        "prompt": f"Install/configure {JOBS_KEY}? [y/n]: ",
        "execute_state": "INSTALL",
        "post_state": "CONFIG_LOADING",
    },
    f"Uninstall {JOBS_KEY}": {
        "verb": "uninstall",
        "filter_status": True,
        "label": INSTALLED_LABEL,
        "prompt": f"Uninstall {JOBS_KEY}? [y/n]: ",
        "execute_state": "UNINSTALL",
        "post_state": "CONFIG_LOADING",
    },
    f"Update {JOBS_KEY} Settings": {
        "verb": "update",
        "filter_status": True,
        "label": INSTALLED_LABEL,
        "prompt": f"Update {JOBS_KEY} settings (copy templates + apply edits)? [y/n]: ",
        "execute_state": "UPDATE_SETTINGS",
        "post_state": "CONFIG_LOADING",
    },
    f"Reset {JOBS_KEY} Only (remove INIs / recreate defaults)": {
        "verb": "reset",
        "filter_status": True,
        "label": RESET_LABEL,
        "prompt": f"Reset {JOBS_KEY} config to defaults? [y/n]: ",
        "execute_state": "RESET",
        "post_state": "CONFIG_LOADING",
    },
    "Show config help": {
        "verb": "help",
        "filter_status": None,
        "label": None,
        "prompt": "Show config help now? [y/n]: ",
        "execute_state": "SHOW_CONFIG_DOC",
        "post_state": "CONFIG_LOADING",
        "skip_sub_select": True,
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "Cancel": {
        "verb": None,
        "filter_status": None,
        "label": None,
        "prompt": "",
        "execute_state": "FINALIZE",
        "post_state": "FINALIZE",
        "skip_sub_select": True,
        "skip_prepare_plan": True,
    },
}

SUB_MENU: Dict[str, str] = {
    "title": "Select MAME Task",
    "all_label": "All",
    "cancel_label": "Cancel",
    "cancel_state": "MENU_SELECTION",
}

# === DEPENDENCIES ===
DEPENDENCIES = []

# === PIPELINES ===
PIPELINE_STATES: Dict[str, Dict[str, Any]] = {
    "INSTALL": {
        "pipeline": {
            install_packages: {
                "args": [KEY_PACKAGES],
                "result": "installed",
            },
            make_dirs: {
                "args": [KEY_SETUP_DIRS],
                "when": "installed",
            },
            run_script_dict: {
                "args": [KEY_SETUP_SCRIPTS],
                "when": "installed",
            },
            run_commands: {
                "args": [KEY_SETUP_CMDS],
                "when": "installed",
                "result": "setup_ok",
            },
            copy_file_dict: {
                "args": [KEY_SETTINGS_FILES],
                "when": "installed",
            },
            copy_folder_dict: {
                "args": [KEY_SETTINGS_FOLDERS],
                "when": "installed",
            },
            create_group: {
                "args": [KEY_ARCADE_GROUPS],
                "when": "installed",
            },
            group_exists: {
                "args": [KEY_ARCADE_GROUPS],
                "when": "installed",
                "result": "group_exists",
            },
            user_not_in_group: {
                "args": [KEY_ARCADE_USERS, KEY_ARCADE_GROUPS],
                "when": "group_exists",
                "result": "user_needs_group",
            },
            add_user_to_group: {
                "args": [KEY_ARCADE_USERS, KEY_ARCADE_GROUPS],
                "when": "user_needs_group",
            },
            chown_paths: {
                "args": [
                    KEY_CHOWN_USER,
                    KEY_CHOWN_PATHS,
                    KEY_CHOWN_RECURSIVE,
                    KEY_CHOWN_GROUP,
                ],
                "when": "installed",
            },
            chmod_paths: {
                "args": [KEY_CHMOD_PATHS],
                "when": "installed",
            },
            protect_folders: {
                "args": [KEY_PROTECTED_FOLDERS],
                "when": "installed",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "setup_ok",
        "post_state": "CONFIG_LOADING",
    },

    "UPDATE_SETTINGS": {
        "pipeline": {
            remove_paths: {
                "args": [KEY_REMOVE_PATHS],
                "result": "removed",
            },
            run_script_dict: {
                "args": [KEY_SETUP_SCRIPTS],
                "when": "removed",
            },
            run_commands: {
                "args": [KEY_SETUP_CMDS],
                "when": "removed",
                "result": "setup_ok",
            },
            copy_file_dict: {
                "args": [KEY_SETTINGS_FILES],
                "when": "removed",
            },
            copy_folder_dict: {
                "args": [KEY_SETTINGS_FOLDERS],
                "when": "removed",
            },
            create_group: {
                "args": [KEY_ARCADE_GROUPS],
                "when": "removed",
            },
            group_exists: {
                "args": [KEY_ARCADE_GROUPS],
                "when": "removed",
                "result": "group_exists",
            },
            user_not_in_group: {
                "args": [KEY_ARCADE_USERS, KEY_ARCADE_GROUPS],
                "when": "group_exists",
                "result": "user_needs_group",
            },
            add_user_to_group: {
                "args": [KEY_ARCADE_USERS, KEY_ARCADE_GROUPS],
                "when": "user_needs_group",
            },
            chown_paths: {
                "args": [
                    KEY_CHOWN_USER,
                    KEY_CHOWN_PATHS,
                    KEY_CHOWN_RECURSIVE,
                    KEY_CHOWN_GROUP,
                ],
                "when": "removed",
            },
            chmod_paths: {
                "args": [KEY_CHMOD_PATHS],
                "when": "removed",
            },
            protect_folders: {
                "args": [KEY_PROTECTED_FOLDERS],
                "when": "removed",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "setup_ok",
        "post_state": "CONFIG_LOADING",
    },

    "RESET": {
        "pipeline": {
            remove_paths: {
                "args": [KEY_REMOVE_PATHS],
                "result": "removed",
            },
            make_dirs: {
                "args": [KEY_RESET_DIRS],
                "when": "removed",
                "result": "dirs_created",
            },
            run_commands: {
                "args": [KEY_RESET_CMDS],
                "when": "dirs_created",
                "result": "reset_ok",
            },
        },
        "label": RESET_LABEL,
        "success_key": "reset_ok",
        "post_state": "CONFIG_LOADING",
    },

    "UNINSTALL": {
        "pipeline": {
            run_commands: {
                "args": [KEY_RESET_CMDS],
                "result": "reset_ok",
            },
            remove_paths: {
                "args": [KEY_REMOVE_PATHS],
                "when": "reset_ok",
                "result": "removed",
            },
            make_dirs: {
                "args": [KEY_RESET_DIRS],
                "when": "removed",
                "result": "cleanup_ok",
            },
            uninstall_packages: {
                "args": [KEY_PACKAGES],
                "when": "cleanup_ok",
                "result": "uninstalled",
            },
        },
        "label": UNINSTALLED_LABEL,
        "success_key": "uninstalled",
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
