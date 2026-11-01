# constants/FunctionConstants.py

from pathlib import Path
from modules.function_utils import (
    job_is_ready,
    load_module_functions,
    load_module_function_docs,
    scan_function_usage,
    detect_usage,
    print_usage_summary,
    print_functions_summary,
)
from modules.display_utils import display_config_doc

# === CONFIG PATHS & KEYS ===
PRIMARY_CONFIG   = "config/AppConfigSettings.json"
JOBS_KEY         = "Functions"
CONFIG_TYPE      = "function_usage"
DEFAULT_CONFIG   = "Default"
CONFIG_DOC       = "doc/FunctionDoc.json"

# === JSON KEYS (per job) ===
KEY_MODULE_FOLDER  = "ModuleFolder"
KEY_CHECK_FOLDERS  = "CheckFolders"
KEY_CHECK_FILES    = "CheckFiles"


# === VALIDATION CONFIG ===
VALIDATION_CONFIG = {
    "required_job_fields": {
        KEY_MODULE_FOLDER: str,
        KEY_CHECK_FOLDERS: list,
        KEY_CHECK_FILES: list,
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
LOG_PREFIX      = "fn_usage"
LOG_DIR         = Path.home() / "logs" / "fn_usage"
LOGS_TO_KEEP    = 10
ROTATE_LOG_NAME = f"{LOG_PREFIX}_*.log"

# === USER / LABELS ===
REQUIRED_USER       = "standard"
INSTALLED_LABEL     = "READY"
UNINSTALLED_LABEL   = "NOT_READY"

# === STATUS CHECK CONFIG ===
STATUS_FN_CONFIG = {
    "fn": job_is_ready,
    "args": [KEY_MODULE_FOLDER],
    "labels": {True: INSTALLED_LABEL, False: UNINSTALLED_LABEL},
}

# === MENU / ACTIONS ===
ACTIONS = {
    "_meta": {"title": "Select analysis mode"},
    f"Analyze {JOBS_KEY}": {
        "verb": "analyze",
        "filter_status": None,
        "label": None,
        "prompt": "\nRun static function-usage scan now? [y/n]: ",
        "execute_state": "ANALYZE",
        "post_state": "CONFIG_LOADING",
    },
    f"Show {JOBS_KEY}": {
        "verb": "show",
        "filter_status": None,
        "label": None,
        "prompt": "\nShow module functions + docstrings now? [y/n]: ",
        "execute_state": "SHOW_FUNCTIONS",
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
    "title": "Select Module",
    "all_label": "All",
    "cancel_label": "Cancel",
    "cancel_state": "MENU_SELECTION",
}

# === DEPENDENCIES ===
DEPENDENCIES = []

# === PLAN COLUMN DISPLAYS ===
PLAN_COLUMNS_ANALYZE = [
    KEY_MODULE_FOLDER,
    KEY_CHECK_FOLDERS,
    KEY_CHECK_FILES,
]


PLAN_COLUMNS_SHOW = [
    KEY_MODULE_FOLDER,
]

PLAN_COLUMN_ORDER = PLAN_COLUMNS_ANALYZE

OPTIONAL_PLAN_COLUMNS = {
    f"Analyze {JOBS_KEY}": PLAN_COLUMNS_ANALYZE,
    f"Show {JOBS_KEY}": PLAN_COLUMNS_SHOW,
}


# === PIPELINES ===
PIPELINE_STATES = {
    "ANALYZE": {
        "pipeline": {
            load_module_functions: {
                "args": [KEY_MODULE_FOLDER, "job"],
                "result": "module_functions",
            },
            scan_function_usage: {
                "args": ["module_functions", KEY_CHECK_FOLDERS, KEY_CHECK_FILES, KEY_MODULE_FOLDER],
                "when": "module_functions",
                "result": "scan_result",
            },
            print_usage_summary: {
                "args": ["job", "scan_result"],
                "when": "scan_result",
            },
            detect_usage: {
                "args": ["scan_result"],
                "when": "scan_result",
                "result": "used",
            },
        },
        "success_key": "used",
    },
    "SHOW_FUNCTIONS": {
        "pipeline": {
            load_module_function_docs: {
                "args": [KEY_MODULE_FOLDER, "job"],
                "result": "fn_docs",
            },
            print_functions_summary: {
                "args": ["job", "fn_docs"],
                "when": "fn_docs",
                "result": "ok",
            },
        },
        "success_key": "ok",
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

