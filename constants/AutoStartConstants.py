# constants/AutoStartConstants.py

from pathlib import Path

from modules.autostart_utils import (
    check_autostart_status,
    install_autostart,
    remove_autostart,
    run_autostart,
)
from modules.system_utils import (
    copy_script_template,
    copy_files,
    copy_folders,
    remove_file,
    remove_files,
    remove_folders,
)
from modules.display_utils import display_config_doc

# === CONFIG PATHS & KEYS ===
PRIMARY_CONFIG   = "config/AppConfigSettings.json"
JOBS_KEY         = "AutoStart"
CONFIG_TYPE      = "AutoStart"
DEFAULT_CONFIG   = "Default"
CONFIG_DOC       = "doc/AutoStartDoc.json"

# === JSON KEYS ===
KEY_ORDER               = "Order"
KEY_NAME                = "Name"
KEY_USERS               = "Users"
KEY_SCRIPT_SRC          = "ScriptSrc"
KEY_SCRIPT_DEST         = "ScriptDest"
KEY_AUTOSTART_SRC       = "AutoStartSrc"
KEY_AUTOSTART_NAME      = "AutoStartName"
KEY_OPTIONAL_FILES      = "OptionalFiles"
KEY_OPTIONAL_FOLDERS    = "OptionalFolders"

# === VALIDATION CONFIG ===
VALIDATION_CONFIG = {
    "required_job_fields": {
        KEY_USERS: list,
        KEY_SCRIPT_SRC: str,
        KEY_SCRIPT_DEST: str,
        KEY_AUTOSTART_SRC: str,
        KEY_AUTOSTART_NAME: str,
    },
    "example_config": CONFIG_DOC,
}

# === SECONDARY VALIDATION CONFIG ===
SECONDARY_VALIDATION = {}

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
LOG_PREFIX      = "AutoStart"
LOG_DIR         = Path.home() / "logs" / "services"
LOGS_TO_KEEP    = 10
ROTATE_LOG_NAME = f"{LOG_PREFIX}_*.log"

# === USER / LABELS ===
REQUIRED_USER     = "root"
INSTALLED_LABEL   = "ENABLED"
UNINSTALLED_LABEL = "DISABLED"

# === STATUS CHECK CONFIG ===
STATUS_FN_CONFIG = {
    "fn": check_autostart_status,
    "args": ["job", f"meta.{KEY_USERS}", f"meta.{KEY_AUTOSTART_NAME}"],
    "labels": {True: INSTALLED_LABEL, False: UNINSTALLED_LABEL},
}

# === MENU / ACTIONS ===
ACTIONS = {
    "_meta": {"title": "Select an option"},
    f"Install & enable {JOBS_KEY}": {
        "verb": "installation",
        "filter_status": False,
        "label": INSTALLED_LABEL,
        "prompt": "Proceed with installation? [y/n]: ",
        "execute_state": "INSTALL",
        "post_state": "CONFIG_LOADING",
    },
    f"Uninstall {JOBS_KEY}": {
        "verb": "uninstallation",
        "filter_status": True,
        "label": UNINSTALLED_LABEL,
        "prompt": "Proceed with uninstallation? [y/n]: ",
        "execute_state": "UNINSTALL",
        "post_state": "CONFIG_LOADING",
    },
    f"Run {JOBS_KEY}": {
        "verb": "run",
        "filter_status": True,
        "label": "RUN",
        "prompt": "Run selected AutoStart now? [y/n]: ",
        "execute_state": "RUN",
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
        "prompt": None,
        "execute_state": "FINALIZE",
        "post_state": "FINALIZE",
    },
}

SUB_MENU = {
    "title": "Select AutoStart",
    "all_label": "All",
    "cancel_label": "Cancel",
    "cancel_state": "MENU_SELECTION",
}

# === DEPENDENCIES ===
DEPENDENCIES = []

# === TABLE COLUMNS ===
PLAN_COLUMN_ORDER = [
    KEY_ORDER,
    KEY_USERS,
    KEY_SCRIPT_SRC,
    KEY_SCRIPT_DEST,
    KEY_AUTOSTART_SRC,
    KEY_AUTOSTART_NAME,
    KEY_NAME,
]

OPTIONAL_PLAN_COLUMNS = {}

# === PIPELINES ===
PIPELINE_STATES = {
    "INSTALL": {
        "pipeline": {
            copy_script_template: {
                "args": [f"meta.{KEY_SCRIPT_SRC}", f"meta.{KEY_SCRIPT_DEST}"],
                "result": "_",
            },
            "copy_files": {
                "fn": copy_files,
                "args": [f"meta.{KEY_OPTIONAL_FILES}"],
                "when": f"meta.{KEY_OPTIONAL_FILES}",
                "result": "_",
            },
            "copy_folders": {
                "fn": copy_folders,
                "args": [f"meta.{KEY_OPTIONAL_FOLDERS}"],
                "when": f"meta.{KEY_OPTIONAL_FOLDERS}",
                "result": "_",
            },
            install_autostart: {
                "args": [
                    f"meta.{KEY_AUTOSTART_SRC}",
                    f"meta.{KEY_AUTOSTART_NAME}",
                    f"meta.{KEY_USERS}",
                ],
                "result": "ok",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "UNINSTALL": {
        "pipeline": {
            remove_autostart: {
                "args": [
                    f"meta.{KEY_AUTOSTART_NAME}",
                    f"meta.{KEY_USERS}",
                ],
                "result": "_",
            },
            "remove_script_file": {
                "fn": remove_file,
                "args": [f"meta.{KEY_SCRIPT_DEST}"],
                "result": "_",
            },
            "remove_files": {
                "fn": remove_files,
                "args": [f"meta.{KEY_OPTIONAL_FILES}"],
                "when": f"meta.{KEY_OPTIONAL_FILES}",
                "result": "_",
            },
            "remove_folders": {
                "fn": remove_folders,
                "args": [f"meta.{KEY_OPTIONAL_FOLDERS}"],
                "when": f"meta.{KEY_OPTIONAL_FOLDERS}",
                "result": "_",
            },
        },
        "label": UNINSTALLED_LABEL,
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "RUN": {
        "pipeline": {
            run_autostart: {
                "args": [f"meta.{KEY_SCRIPT_DEST}"],
                "result": "ok",
            },
        },
        "label": "RUN",
        "success_key": "ok",
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