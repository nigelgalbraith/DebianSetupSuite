# constants/FlatpakConstants.py

from pathlib import Path
from modules.flatpak_utils import (
    ensure_flathub,
    check_flatpak_status,
    install_flatpak_app,
    uninstall_flatpak_app,
)
from modules.display_utils import display_config_doc

# === CONFIG PATHS & KEYS ===
PRIMARY_CONFIG   = "config/AppConfigSettings.json"
JOBS_KEY         = "Flatpak"
CONFIG_TYPE      = "flatpak"
DEFAULT_CONFIG   = "Default"
CONFIG_DOC       = "doc/FlatpakDoc.json"

# === JSON KEYS ===
KEY_REMOTE = "remote"

# === VALIDATION CONFIG ===
VALIDATION_CONFIG = {
    "required_job_fields": {
        KEY_REMOTE: str,
    },
    "example_config": CONFIG_DOC, 
}

# === SECONDARY VALIDATION  ===
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
LOG_PREFIX      = "flatpak_install"
LOG_DIR         = Path.home() / "logs" / "flatpak"
LOGS_TO_KEEP    = 10
ROTATE_LOG_NAME = f"{LOG_PREFIX}_*.log"

# === USER / LABELS ===
REQUIRED_USER     = "Standard"
INSTALLED_LABEL   = "INSTALLED"
UNINSTALLED_LABEL = "UNINSTALLED"

# === STATUS CHECK CONFIG ===
STATUS_FN_CONFIG = {
    "fn": check_flatpak_status,
    "args": ["job"], 
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
    "Ensure Flathub remote": {
        "verb": "ensure",
        "filter_status": None,
        "label": "ENSURED",
        "prompt": "Ensure Flathub remote is configured? [y/n]: ",
        "filter_jobs": [],                     
        "skip_sub_select": True,                
        "skip_prepare_plan": True,              
        "execute_state": "ENSURE_FLATHUB",      
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

# === SUB MENU ===
SUB_MENU = {
    "title": "Select Flatpak",
    "all_label": "All",
    "cancel_label": "Cancel",
    "cancel_state": "MENU_SELECTION",
}

# === DEPENDENCIES ===
DEPENDENCIES = ["flatpak"]

# === PLAN TABLE COLUMNS ===
PLAN_COLUMN_ORDER = [KEY_REMOTE]

OPTIONAL_PLAN_COLUMNS = {}


# === PIPELINES ===
PIPELINE_STATES = {
    "INSTALL": {
        "pipeline": {
            ensure_flathub: {
                "args": [],
                "result": "flathub_ready",
            },
            install_flatpak_app: {
                "args": ["job", KEY_REMOTE],
                "when": "flathub_ready",
                "result": "installed",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "installed",
        "post_state": "CONFIG_LOADING",
    },
    "UNINSTALL": {
        "pipeline": {
            uninstall_flatpak_app: {
                "args": ["job"],
                "result": "uninstalled",
            },
        },
        "label": UNINSTALLED_LABEL,
        "success_key": "uninstalled",
        "post_state": "CONFIG_LOADING",
    },
    "ENSURE_FLATHUB": {
        "pipeline": {
            ensure_flathub: {
                "args": [],
                "result": "ok",
            },
        },
        "label": "ENSURED",
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

