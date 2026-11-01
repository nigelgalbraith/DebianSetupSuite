# constants/FirewallConstants.py

from pathlib import Path
from modules.firewall_utils import (
    reset_ufw,
    enable_ufw,
    disable_ufw,
    enable_logging_ufw,
    reload_ufw,
    status_ufw,
    status_ufw_display,              
    allow_application,        
    apply_singleports,
    apply_portranges,
)
from modules.display_utils import display_config_doc

# === CONFIG PATHS & KEYS ===
PRIMARY_CONFIG   = "config/AppConfigSettings.json"
JOBS_KEY         = "Firewall"
CONFIG_TYPE      = "firewall"
DEFAULT_CONFIG   = "Default"
CONFIG_DOC       = "doc/FirewallDoc.json"

# === JSON KEYS ===
KEY_APPLICATIONS = "Applications"
KEY_SINGLE_PORTS = "SinglePorts"
KEY_PORT_RANGES  = "PortRanges"
KEY_PORT         = "Port"
KEY_PROTOCOL     = "Protocol"
KEY_IPS          = "IPs"
KEY_START_PORT   = "StartPort"
KEY_END_PORT     = "EndPort"
KEY_RULE_NAME    = "RuleName"


# === VALIDATION CONFIG ===
VALIDATION_CONFIG = {
    "required_job_fields": {
        KEY_APPLICATIONS: list,
        KEY_SINGLE_PORTS: list,
        KEY_PORT_RANGES: list,
    },
}

# === SECONDARY VALIDATION  ===
SECONDARY_VALIDATION = {
    KEY_APPLICATIONS: {
        "required_job_fields": {},  
        "allow_empty": True,
    },
    KEY_SINGLE_PORTS: {
        "required_job_fields": {
            KEY_RULE_NAME: str,
            KEY_PORT: int,
            KEY_PROTOCOL: str,
            KEY_IPS: list,
        },
        "allow_empty": True,
    },
    KEY_PORT_RANGES: {
        "required_job_fields": {
            KEY_RULE_NAME: str,
            KEY_START_PORT: int,
            KEY_END_PORT: int,
            KEY_PROTOCOL: str,
            KEY_IPS: list,
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
LOG_PREFIX      = "firewall"
LOG_DIR         = Path.home() / "logs" / "firewall"
LOGS_TO_KEEP    = 10
ROTATE_LOG_NAME = f"{LOG_PREFIX}_*.log"

# === USER / LABELS ===
REQUIRED_USER     = "root"
INSTALLED_LABEL   = "APPLIED"
UNINSTALLED_LABEL = "PENDING"

# === STATUS CHECK CONFIG ===
STATUS_FN_CONFIG = {
    "fn": status_ufw,  
    "args": [],
    "labels": {True: INSTALLED_LABEL, False: UNINSTALLED_LABEL},
}

# === MENU / ACTIONS ===
ACTIONS = {
    "_meta": {"title": "Select an option"},
    "Apply firewall rules": {
        "verb": "apply",
        "filter_status": None,
        "label": INSTALLED_LABEL,
        "prompt": "Apply the firewall rules? [y/n]: ",
        "execute_state": "APPLY_RULES",
        "post_state": "CONFIG_LOADING",
        "skip_sub_select": True,
        "skip_prepare_plan": False,
        "filter_jobs": None,
    },
    "Show UFW status": {
        "verb": "status",
        "filter_status": None,
        "label": "STATUS",
        "prompt": "Show UFW status now? [y/n]: ",
        "execute_state": "STATUS_ONLY",
        "post_state": "CONFIG_LOADING",
        "skip_sub_select": True,
        "skip_prepare_plan": True,
        "filter_jobs": None,
        "skip_confirm": True,
    },
    "Enable UFW": {
        "verb": "enable",
        "filter_status": None,
        "label": INSTALLED_LABEL,
        "prompt": "Enable UFW and logging? [y/n]: ",
        "execute_state": "ENABLE_ONLY",
        "post_state": "CONFIG_LOADING",
        "skip_sub_select": True,
        "skip_prepare_plan": True,
        "filter_jobs": None,
    },
    "Disable UFW": {
        "verb": "disable",
        "filter_status": None,
        "label": UNINSTALLED_LABEL,
        "prompt": "Disable UFW? [y/n]: ",
        "execute_state": "DISABLE_ONLY",
        "post_state": "CONFIG_LOADING",
        "skip_sub_select": True,
        "skip_prepare_plan": True,
        "filter_jobs": None,
    },
    "Reset UFW (flush rules)": {
        "verb": "reset",
        "filter_status": None,
        "label": "RESET",
        "prompt": "Reset UFW (flush all rules)? [y/n]: ",
        "execute_state": "RESET_ONLY",
        "post_state": "CONFIG_LOADING",
        "skip_sub_select": True,
        "skip_prepare_plan": True,
        "filter_jobs": None,
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
    "title": "Select Firewall job",
    "all_label": "All",
    "cancel_label": "Cancel",
    "cancel_state": "MENU_SELECTION",
}

# === DEPENDENCIES ===
DEPENDENCIES = ["ufw"]

# === TABLE COLUMNS ===
PLAN_COLUMN_ORDER = [KEY_APPLICATIONS, KEY_SINGLE_PORTS, KEY_PORT_RANGES]
OPTIONAL_PLAN_COLUMNS = {}



# === PIPELINES ===
PIPELINE_STATES = {
    "APPLY_RULES": {
        "pipeline": {
            reset_ufw: {
                "args": [],
                "result": "reset",
            },
            enable_ufw: {
                "args": [],
                "when": "reset",
                "result": "enabled",
            },
            enable_logging_ufw: {
                "args": [],
                "when": "enabled",
                "result": "logging_enabled",
            },
            allow_application: {
                "args": [KEY_APPLICATIONS],
                "when": ["logging_enabled", f"meta.{KEY_APPLICATIONS}"],
            },
            apply_singleports: {
                "args": [KEY_SINGLE_PORTS],
                "when": ["logging_enabled", f"meta.{KEY_SINGLE_PORTS}"],
            },
            apply_portranges: {
                "args": [KEY_PORT_RANGES],
                "when": ["logging_enabled", f"meta.{KEY_PORT_RANGES}"],
            },
            reload_ufw: {
                "args": [],
                "when": "logging_enabled",
                "result": "reloaded",
            },
            status_ufw: {
                "args": [],
                "when": "reloaded",
                "result": "ok",
            },
            status_ufw_display: {
                "args": [],
                "when": "ok",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "STATUS_ONLY": {
        "pipeline": {
            status_ufw_display: {
                "args": [],
                "result": "ok",
            },
        },
        "label": "STATUS",
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "ENABLE_ONLY": {
        "pipeline": {
            enable_ufw: {
                "args": [],
                "result": "enabled",
            },
            enable_logging_ufw: {
                "args": [],
                "when": "enabled",
            },
            status_ufw: {
                "args": [],
                "when": "enabled",
                "result": "ok",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "DISABLE_ONLY": {
        "pipeline": {
            disable_ufw: {
                "args": [],
                "result": "disabled",
            },
            status_ufw: {
                "args": [],
                "when": "disabled",
                "result": "ok",
            },
        },
        "label": UNINSTALLED_LABEL,
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "RESET_ONLY": {
        "pipeline": {
            reset_ufw: {
                "args": [],
                "result": "reset",
            },
            status_ufw: {
                "args": [],
                "when": "reset",
                "result": "ok",
            },
        },
        "label": "RESET",
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
