# DownloadConstants.py

from __future__ import annotations

from pathlib import Path
from typing import Dict, Any, List

from modules.download_utils import (
    is_job_incomplete,
    filter_downloads,
    run_link_jobs,
)

from modules.system_utils import run_script_dict
from modules.display_utils import display_config_doc

# ==================================================
# CONFIG PATHS & KEYS
# ==================================================

PRIMARY_CONFIG = "config/AppConfigSettings.json"
JOBS_KEY = "Downloads"
CONFIG_TYPE = "downloads"
DEFAULT_CONFIG = "Default"
CONFIG_DOC       = "doc/DownloadDoc.json"

# ==================================================
# JSON KEYS (UNIFIED LINKS)
# ==================================================

KEY_LINKS = "links"
KEY_LINKS_CONFIGS = "LinksConfigs"
KEY_OUTPUT_PATH = "output_path"
KEY_EXTRACT = "extract"
KEY_EXTRACT_EXTENSIONS = "extract_extensions"
KEY_CHECK_FILES = "check_files"  # Links config sentinel list (all links)


# ==================================================
# SCRIPT RUNNER SETTINGS
# ==================================================

LINKS_TO_JSON_SCRIPT = "settings/downloads/links_to_json.py"


# ==================================================
# VALIDATION CONFIG (UPDATED REQUIRED FIELDS)
# ==================================================

VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        KEY_LINKS: dict,
    },
    "example_config": CONFIG_DOC,
}

SECONDARY_VALIDATION: Dict[str, Any] = {
    KEY_LINKS: {
        "required_job_fields": {
            KEY_OUTPUT_PATH: str,
            KEY_EXTRACT: bool,
            KEY_EXTRACT_EXTENSIONS: list,
            KEY_LINKS_CONFIGS: list,
        },
        "allow_empty": True,
    },
    "example_config": CONFIG_DOC,
}

# ==================================================
# DETECTION CONFIG
# ==================================================

DETECTION_CONFIG: Dict[str, Any] = {
    "primary_config": PRIMARY_CONFIG,
    "config_type": CONFIG_TYPE,
    "jobs_key": JOBS_KEY,
    "default_config": DEFAULT_CONFIG,
    "default_config_note": (
        "No model-specific Downloads config was found. "
        "Using the 'Default' section instead. "
    ),
}


# ==================================================
# LOGGING
# ==================================================

LOG_PREFIX = "downloads"
LOG_DIR = Path.home() / "logs" / "downloads"
LOGS_TO_KEEP = 10
ROTATE_LOG_NAME = f"{LOG_PREFIX}_*.log"


# ==================================================
# USER / LABELS
# ==================================================

REQUIRED_USER = "Standard"
INSTALLED_LABEL = "COMPLETE"
UNINSTALLED_LABEL = "INCOMPLETE"


# ==================================================
# STATUS CHECK CONFIG 
# ==================================================

STATUS_FN_CONFIG = {
    "fn": is_job_incomplete,
    "args": ["meta"],
    "labels": {True: UNINSTALLED_LABEL, False: INSTALLED_LABEL},
}

# ==================================================
# COLUMN ORDER 
# ==================================================

PLAN_COLUMN_ORDER = [
    KEY_LINKS,
]
OPTIONAL_PLAN_COLUMNS = {}


# ==================================================
# ACTIONS
# ==================================================

ACTIONS: Dict[str, Dict[str, Any]] = {
    "_meta": {"title": f"{JOBS_KEY} Setup"},

    "Download Missing Files": {
        "verb": "download",
        "filter_status": True,
        "label": UNINSTALLED_LABEL,
        "prompt": "Downloads incomplete. Download missing files now? [y/n]: ",
        "execute_state": "DOWNLOAD_MISSING",
        "post_state": "CONFIG_LOADING",
    },

    "Generate Links JSON": {
        "verb": "generate",
        "filter_status": None,
        "label": None,
        "prompt": "Run links_to_json to generate a JSON config now? [y/n]: ",
        "execute_state": "LINKS_TO_JSON",
        "post_state": "CONFIG_LOADING",
        "skip_sub_select": True,
        "skip_prepare_plan": True,
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
    "title": "Select Download Task",
    "all_label": "All",
    "cancel_label": "Cancel",
    "cancel_state": "MENU_SELECTION",
}


# ==================================================
# DEPENDENCIES
# ==================================================

DEPENDENCIES: List[str] = ["wget", "unzip", "p7zip-full"]



# ==================================================
# PIPELINES
# ==================================================
PIPELINE_STATES: Dict[str, Dict[str, Any]] = {
    "DOWNLOAD_MISSING": {
        "pipeline": {
            filter_downloads: {
                "args": ["meta"],
                "result": "filtered",
            },
            run_link_jobs: {
                "args": ["filtered"],
                "when": "filtered",
                "result": "links_ok",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "links_ok",
        "post_state": "CONFIG_LOADING",
    },
    "LINKS_TO_JSON": {
        "pipeline": {
            run_script_dict: {
                "args": [[
                    {
                        "script": LINKS_TO_JSON_SCRIPT,
                        "args": [],
                    }
                ]],
                "result": "json_ok",
            },
        },
        "label": "DONE",
        "success_key": "json_ok",
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

