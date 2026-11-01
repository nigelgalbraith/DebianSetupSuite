
from __future__ import annotations

from pathlib import Path
from typing import Dict, Any

from modules.test_utils import (
    load_test_pipelines,
    check_pipeline_success_keys,
)
from modules.system_utils import check_folder_path
from modules.display_utils import display_config_doc


# === CONFIG PATHS & KEYS ===
PRIMARY_CONFIG = "config/AppConfigSettings.json"
JOBS_KEY       = "Tests"
CONFIG_TYPE    = "constants_tests"
DEFAULT_CONFIG = "Default"
CONFIG_DOC     = "doc/TestsDoc.json"


# === JSON KEYS ===
KEY_TESTS    = "Tests"
KEY_PIPELINE = "pipeline"


# === VALIDATION CONFIG ===
VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        KEY_TESTS: list,
    },
    "example_config": CONFIG_DOC,
}


# === SECONDARY VALIDATION ===
SECONDARY_VALIDATION: Dict[str, Any] = {
    KEY_TESTS: {
        "required_job_fields": {
            KEY_PIPELINE: str,
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
}


# === LOGGING ===
LOG_PREFIX      = "tests"
LOG_DIR         = Path.home() / "logs" / "tests"
LOGS_TO_KEEP    = 10
ROTATE_LOG_NAME = f"{LOG_PREFIX}_*.log"


# === USER / LABELS ===
REQUIRED_USER     = "root"
INSTALLED_LABEL   = "AVAILABLE"
UNINSTALLED_LABEL = "MISSING"
TESTED_LABEL      = "TESTED"


# === STATUS CHECK CONFIG ===
STATUS_FN_CONFIG = {
    "fn": check_folder_path,
    "args": ["job"],
    "labels": {
        True: INSTALLED_LABEL,
        False: UNINSTALLED_LABEL,
    },
}


# === COLUMN ORDER ===
PLAN_COLUMN_ORDER = [
    KEY_TESTS,
]

OPTIONAL_PLAN_COLUMNS = {}


# === ACTIONS ===
ACTIONS: Dict[str, Dict[str, Any]] = {
    "_meta": {"title": f"{JOBS_KEY} Runner"},

    "Run Tests": {
        "verb": "test",
        "filter_status": True,
        "label": INSTALLED_LABEL,
        "prompt": "Run selected tests? [y/n]: ",
        "execute_state": "RUN_TESTS",
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


# === SUB MENU ===
SUB_MENU: Dict[str, str] = {
    "title": "Select Tests",
    "all_label": "All",
    "cancel_label": "Cancel",
    "cancel_state": "MENU_SELECTION",
}


# === DEPENDENCIES ===
DEPENDENCIES = []


# === PIPELINES ===
PIPELINE_STATES: Dict[str, Dict[str, Any]] = {
    "RUN_TESTS": {
        "pipeline": {
            load_test_pipelines: {
                "args": ["job", KEY_TESTS],
                "result": "pipelines_loaded",
            },
            check_pipeline_success_keys: {
                "args": ["pipelines_loaded"],
                "when": "pipelines_loaded",
                "result": "ok",
            },
        },
        "label": TESTED_LABEL,
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
