# constants/StartUpServicesConstants.py

from pathlib import Path

from modules.service_utils import (
    check_service_status,
    enable_and_start_service,
    stop_and_disable_service,
    restart_service,
)
from modules.system_utils import (  
    copy_script_template,
    copy_file,
    copy_files,
    copy_folders,
    remove_file,
    remove_files,
    remove_folders,
    reload_systemd,
)
from modules.logger_utils import (
    install_logrotate_config,
    remove_logrotate_config,
)
from modules.display_utils import display_config_doc

# === CONFIG PATHS & KEYS ===
PRIMARY_CONFIG   = "config/AppConfigSettings.json"
JOBS_KEY         = "ScheduleServices"
CONFIG_TYPE      = "ScheduleServices"
DEFAULT_CONFIG   = "Default"
CONFIG_DOC       = "doc/ScheduleServicesDoc.json"

# === JSON KEYS ===
KEY_ORDER               = "Order"
KEY_NAME                = "Name"           
KEY_SCRIPT_SRC          = "ScriptSrc"
KEY_SCRIPT_DEST         = "ScriptDest"
KEY_SERVICE_SRC         = "ServiceSrc"
KEY_SERVICE_DEST        = "ServiceDest"
KEY_LOG_NAME            = "LogName"
KEY_LOGROTATE           = "LogrotateCfg"
KEY_OPTIONAL_FILES      = "OptionalFiles"
KEY_OPTIONAL_FOLDERS    = "OptionalFolders"
KEY_TIMER_SRC           = "TimerSrc"
KEY_TIMER_DEST          = "TimerDest"


# === VALIDATION CONFIG ===
VALIDATION_CONFIG = {
    "required_job_fields": {
        KEY_SCRIPT_SRC: str,
        KEY_SCRIPT_DEST: str,
        KEY_SERVICE_SRC: str,
        KEY_SERVICE_DEST: str,
        KEY_TIMER_SRC: str,
        KEY_TIMER_DEST: str,
        KEY_LOG_NAME: str,
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
LOG_PREFIX      = "ScheduleServices"
LOG_DIR         = Path.home() / "logs" / "services"
LOGS_TO_KEEP    = 10
ROTATE_LOG_NAME = f"{LOG_PREFIX}_*.log"

# === USER / LABELS ===
REQUIRED_USER     = "root"
INSTALLED_LABEL   = "ENABLED"
UNINSTALLED_LABEL = "DISABLED"

# === STATUS CHECK CONFIG ===
STATUS_FN_CONFIG = {
    "fn": check_service_status,
    "args": ["job"],
    "labels": {
        True: INSTALLED_LABEL,
        False: UNINSTALLED_LABEL,
    },
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
    "Restart timers": {
        "verb": "restart",
        "filter_status": True,   
        "label": "RESTARTED",
        "prompt": "Restart selected timers? [y/n]: ",
        "execute_state": "RESTART",
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
    "title": "Select Timer",
    "all_label": "All",
    "cancel_label": "Cancel",
    "cancel_state": "MENU_SELECTION",
}

# === DEPENDENCIES ===
DEPENDENCIES = ["logrotate"]

# === TABLE COLUMNS ===
PLAN_COLUMN_ORDER = [
    KEY_ORDER,
    KEY_SCRIPT_SRC,
    KEY_SCRIPT_DEST,
    KEY_SERVICE_SRC,
    KEY_SERVICE_DEST,
    KEY_TIMER_SRC,
    KEY_TIMER_DEST,
    KEY_LOG_NAME,
    KEY_LOGROTATE,
    KEY_NAME,
]

OPTIONAL_PLAN_COLUMNS = {}


# === PIPELINES ===
PIPELINE_STATES = {
    "INSTALL": {
        "pipeline": {
            install_logrotate_config: {
                "args": [KEY_LOGROTATE, KEY_LOG_NAME],
                "when": [f"meta.{KEY_LOGROTATE}", f"meta.{KEY_LOG_NAME}"],
                "result": "logrotate_ok",
            },
            copy_script_template: {
                "args": [KEY_SCRIPT_SRC, KEY_SCRIPT_DEST],
                "result": "script_copied",
            },
            copy_files: {
                "args": [f"?{KEY_OPTIONAL_FILES}"],
                "when": f"meta.{KEY_OPTIONAL_FILES}",
                "result": "files_copied",
            },
            copy_folders: {
                "args": [f"?{KEY_OPTIONAL_FOLDERS}"],
                "when": f"meta.{KEY_OPTIONAL_FOLDERS}",
                "result": "folders_copied",
            },
            "copy_service_file": {
                "fn": copy_file,
                "args": [KEY_SERVICE_SRC, KEY_SERVICE_DEST],
                "when": "script_copied",
                "result": "service_copied",
            },
            "copy_timer_file": {
                "fn": copy_file,
                "args": [KEY_TIMER_SRC, KEY_TIMER_DEST],
                "when": "script_copied",
                "result": "timer_copied",
            },
            reload_systemd: {
                "args": [],
                "when": ["service_copied", "timer_copied"],
                "result": "reloaded",
            },
            enable_and_start_service: {
                "args": ["job"],
                "when": "reloaded",
                "result": "ok",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "UNINSTALL": {
        "pipeline": {
            remove_logrotate_config: {
                "args": [KEY_LOG_NAME],
                "when": f"meta.{KEY_LOG_NAME}",
                "result": "logrotate_removed",
            },
            stop_and_disable_service: {
                "args": ["job"],
                "result": "stopped",
            },
            "remove_timer_file": {
                "fn": remove_file,
                "args": [KEY_TIMER_DEST],
                "when": "stopped",
                "result": "timer_removed",
            },
            "remove_service_file": {
                "fn": remove_file,
                "args": [KEY_SERVICE_DEST],
                "when": "stopped",
                "result": "service_removed",
            },
            reload_systemd: {
                "args": [],
                "when": ["timer_removed", "service_removed"],
                "result": "reloaded",
            },
            "remove_script_file": {
                "fn": remove_file,
                "args": [KEY_SCRIPT_DEST],
                "when": "reloaded",
                "result": "script_removed",
            },
            remove_files: {
                "args": [f"?{KEY_OPTIONAL_FILES}"],
                "when": f"meta.{KEY_OPTIONAL_FILES}",
                "result": "files_removed",
            },
            remove_folders: {
                "args": [f"?{KEY_OPTIONAL_FOLDERS}"],
                "when": f"meta.{KEY_OPTIONAL_FOLDERS}",
                "result": "folders_removed",
            },
        },
        "label": UNINSTALLED_LABEL,
        "success_key": "script_removed",
        "post_state": "CONFIG_LOADING",
    },
    "RESTART": {
        "pipeline": {
            restart_service: {
                "args": ["job"],
                "result": "ok",
            },
        },
        "label": "RESTARTED",
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

