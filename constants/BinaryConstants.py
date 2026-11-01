# constants/BinaryConstants.py

from pathlib import Path
from modules.archive_utils import download_archive_file
from modules.display_utils import display_config_doc
from modules.system_utils import run_commands
from modules.binary_utils import install_binary, uninstall_binary, check_binary_status

# === CONFIG PATHS & KEYS ===
PRIMARY_CONFIG   = "config/AppConfigSettings.json"
JOBS_KEY         = "Binary"
CONFIG_TYPE      = "binary"
DEFAULT_CONFIG   = "Default"
CONFIG_DOC       = "doc/BinaryDoc.json"

# === JSON KEYS ===
KEY_DOWNLOAD_URL   = "DownloadURL"
KEY_INSTALL_PATH   = "InstallPath"
KEY_DOWNLOAD_PATH  = "DownloadPath"
KEY_POST_INSTALL   = "PostInstall"
KEY_POST_UNINSTALL = "PostUninstall"

# === VALIDATION CONFIG ===
VALIDATION_CONFIG = {
    "required_job_fields": {
        KEY_DOWNLOAD_URL: str,
        KEY_INSTALL_PATH: str,
        KEY_DOWNLOAD_PATH: str,
    },
    "optional_job_fields": {
        KEY_POST_INSTALL: list,
        KEY_POST_UNINSTALL: list,
    },
    "example_config": CONFIG_DOC,
}

# === SECONDARY VALIDATION ===
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
LOG_PREFIX      = "binary_install"
LOG_DIR         = Path.home() / "logs" / "binary"
LOGS_TO_KEEP    = 10
ROTATE_LOG_NAME = f"{LOG_PREFIX}_*.log"

# === USER / LABELS ===
REQUIRED_USER     = "Standard"
INSTALLED_LABEL   = "INSTALLED"
UNINSTALLED_LABEL = "UNINSTALLED"

# === STATUS CHECK ===
STATUS_FN_CONFIG = {
    "fn": check_binary_status,
    "args": [KEY_INSTALL_PATH],
    "labels": {True: INSTALLED_LABEL, False: UNINSTALLED_LABEL},
}

# === MENU / ACTIONS ===
ACTIONS = {
    "_meta": {"title": "Select an option"},
    f"Install required {JOBS_KEY}": {
        "verb": "installation",
        "filter_status": False,
        "label": INSTALLED_LABEL,
        "prompt": "Proceed with installation? [y/n]: ",
        "execute_state": "INSTALL",
        "post_state": "CONFIG_LOADING",
    },
    f"Uninstall all listed {JOBS_KEY}": {
        "verb": "uninstallation",
        "filter_status": True,
        "label": UNINSTALLED_LABEL,
        "prompt": "Proceed with uninstallation? [y/n]: ",
        "execute_state": "UNINSTALL",
        "post_state": "CONFIG_LOADING",
    },
    "Show config help": {
        "verb": "help",
        "filter_status": None,
        "label": None,
        "prompt": None,
        "execute_state": "SHOW_CONFIG_DOC",
        "post_state": "CONFIG_LOADING",
        "skip_sub_select": True,
        "skip_prepare_plan": True,
        "skip_confirm": True,
    },
    "Cancel": {
        "execute_state": "FINALIZE",
        "post_state": "FINALIZE",
    },
}

SUB_MENU = {
    "title": "Select Binary",
    "all_label": "All",
    "cancel_label": "Cancel",
    "cancel_state": "MENU_SELECTION",
}

# === DEPENDENCIES ===
DEPENDENCIES = ["curl"]

# === TABLE ===
PLAN_COLUMN_ORDER = [
    KEY_DOWNLOAD_URL,
    KEY_INSTALL_PATH,
    KEY_DOWNLOAD_PATH,
]

OPTIONAL_PLAN_COLUMNS = {}


# === PIPELINES ===
PIPELINE_STATES = {
    "INSTALL": {
        "pipeline": {
            download_archive_file: {
                "args": ["job", KEY_DOWNLOAD_URL, KEY_DOWNLOAD_PATH],
                "result": "binary_path",
            },
            install_binary: {
                "args": ["binary_path", KEY_INSTALL_PATH],
                "when": "binary_path",
                "result": "installed",
            },
            run_commands: {
                "args": [KEY_POST_INSTALL],
                "when": "installed",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "installed",
        "post_state": "CONFIG_LOADING",
    },
    "UNINSTALL": {
        "pipeline": {
            uninstall_binary: {
                "args": [KEY_INSTALL_PATH],
                "result": "uninstalled",
            },
            run_commands: {
                "args": [KEY_POST_UNINSTALL],
                "when": "uninstalled",
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
