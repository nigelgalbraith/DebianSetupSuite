# constants/NetworkConstants.py

from pathlib import Path
from pathlib import Path
from modules.network_utils import (
    bring_up_connection,
    ensure_static_connection,  
    ensure_dhcp_connection,     
    is_connected,               
)
from modules.display_utils import display_config_doc

# === CONFIG PATHS & KEYS ===
PRIMARY_CONFIG   = "config/AppConfigSettings.json"
JOBS_KEY         = "Networks"
CONFIG_TYPE      = "network"
DEFAULT_CONFIG   = "Default"
CONFIG_DOC       = "doc/NetworkDoc.json"

# === JSON KEYS ===
KEY_CONN_NAME  = "ConnectionName"
KEY_INTERFACE  = "Interface"
KEY_ADDRESS    = "Address"
KEY_GATEWAY    = "Gateway"
KEY_DNS        = "DNS"

# === VALIDATION CONFIG ===
VALIDATION_CONFIG = {
    "required_job_fields": {
        KEY_CONN_NAME: str,
        KEY_INTERFACE: str,
        KEY_ADDRESS: str,
        KEY_GATEWAY: str,
        KEY_DNS: str,
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
LOG_PREFIX      = "net_install"
LOG_DIR         = Path.home() / "logs" / "net"
LOGS_TO_KEEP    = 10
ROTATE_LOG_NAME = f"{LOG_PREFIX}_*.log"

# === USER / LABELS ===
REQUIRED_USER       = "root"
INSTALLED_LABEL     = "APPLIED"
UNINSTALLED_LABEL   = "NOT_APPLIED"

# === STATUS CHECK CONFIG ===
STATUS_FN_CONFIG = {
    "fn": is_connected,
    "args": ["job"],
    "labels": {True: INSTALLED_LABEL, False: UNINSTALLED_LABEL},
}

# === MENU / ACTIONS ===
ACTIONS = {
    "_meta": {"title": "Select network mode"},
    f"Apply static {JOBS_KEY}": {
        "verb": "apply static",
        "filter_status": None,
        "label": INSTALLED_LABEL,
        "prompt": "\nApply static settings now? [y/n]: ",
        "execute_state": "INSTALL",
        "post_state": "CONFIG_LOADING",
    },
    f"Apply DHCP {JOBS_KEY}": {
        "verb": "apply dhcp",
        "filter_status": None,
        "label": UNINSTALLED_LABEL,
        "prompt": "\nApply DHCP settings now? [y/n]: ",
        "execute_state": "UNINSTALL",
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

# Sub-select menu
SUB_MENU = {
    "title": "Select Network",
    "all_label": "All",
    "cancel_label": "Cancel",
    "cancel_state": "MENU_SELECTION",
}

# === DEPENDENCIES ===
DEPENDENCIES = ["network-manager"]

# === PLAN COLUMN DISPLAYS ===
PLAN_COLUMNS_STATIC = [
    KEY_CONN_NAME,
    KEY_INTERFACE,
    KEY_ADDRESS,
    KEY_GATEWAY,
    KEY_DNS,
]

PLAN_COLUMNS_DHCP = [
    KEY_CONN_NAME,
    KEY_INTERFACE,
]

PLAN_COLUMN_ORDER = PLAN_COLUMNS_STATIC

OPTIONAL_PLAN_COLUMNS = {
    "Apply static Networks": PLAN_COLUMNS_STATIC,
    "Apply DHCP Networks": PLAN_COLUMNS_DHCP,
}


# === PIPELINES ===
PIPELINE_STATES = {
    "INSTALL": {
        "pipeline": {
            ensure_static_connection: {
                "args": ["meta", "job"],
                "result": "applied",
            },
            bring_up_connection: {
                "args": [KEY_CONN_NAME],
                "when": "applied",
                "result": "brought_up",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "brought_up",
        "post_state": "CONFIG_LOADING",
    },
    "UNINSTALL": {
        "pipeline": {
            ensure_dhcp_connection: {
                "args": ["meta", "job"],
                "result": "applied",
            },
            bring_up_connection: {
                "args": [KEY_CONN_NAME],
                "when": "applied",
                "result": "brought_up",
            },
        },
        "label": UNINSTALLED_LABEL,
        "success_key": "brought_up",
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

