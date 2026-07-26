# constants/UnattendedRootConstants.py
from pathlib import Path
from modules.display_utils import display_config_doc
from modules.state_machine_utils import execute_loader_job, unattended_available

# === CONFIG PATHS & KEYS ===
PRIMARY_CONFIG = "config/AppConfigSettings.json"
JOBS_KEY       = "UnattendedRoot"
CONFIG_TYPE    = "unattendedRoot"
DEFAULT_CONFIG = "Default"
CONFIG_DOC     = "doc/UnattendedRootDoc.json"

# === JSON KEYS ===
KEY_CONSTANTS           = "Constants"
KEY_ACTION              = "Action"

# === LOADERS ===
LOADER      = "DebianLoader.py"


# === VALIDATION CONFIG ===
VALIDATION_CONFIG = {
    "required_job_fields": {
        KEY_CONSTANTS: str,
        KEY_ACTION: str,
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
LOG_PREFIX      = "unattended_root_job"
LOG_DIR         = Path.home() / "logs" / "unattended_root"
LOGS_TO_KEEP    = 10
ROTATE_LOG_NAME = f"{LOG_PREFIX}_*.log"

# === USER / LABELS ===
REQUIRED_USER       = "root"
INSTALLED_LABEL     = "WORKFLOW AVAILABLE"
UNINSTALLED_LABEL   = "NO WORKFLOW"
COMPLETE_LABEL      = "WORKFLOW COMPLETE"

# === STATUS FUNCTION CONFIG ===
STATUS_FN_CONFIG = {
    "fn": unattended_available,
    "args": [LOADER],
    "labels": {
        True: INSTALLED_LABEL,
        False: UNINSTALLED_LABEL,
    },
}

# === DEPENDENCIES ===
DEPENDENCIES = []

# === ACTIONS ===
ACTIONS = {
    "_meta": {
        "title": "Unattended Root",
    },
    "Run unattended root": {
        "verb": "run unattended root",
        "filter_status": None,
        "label": COMPLETE_LABEL,
        "prompt": "Run unattended root setup? [y/n]: ",
        "execute_state": "RUN_UNATTENDED",
        "post_state": "CONFIG_LOADING",
        "skip_sub_select": True,
        "skip_prepare_plan": False,
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

# === SUB-MENU ===
SUB_MENU = {
    "title": "Select Unattended Workflow",
    "all_label": "All",
    "cancel_label": "Cancel",
    "cancel_state": "MENU_SELECTION",
}

# === PLANNING COLUMNS ===
PLAN_COLUMN_ORDER = [
    KEY_CONSTANTS,
    KEY_ACTION,
]

OPTIONAL_PLAN_COLUMNS = {}

# === PIPELINE STATES ===
PIPELINE_STATES = {
    "RUN_UNATTENDED": {
        "pipeline": {
            execute_loader_job: {
                "args": [
                    lambda job, meta, ctx: meta,
                ],
                "result": "complete",
            },
        },
        "label": COMPLETE_LABEL,
        "success_key": "complete",
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