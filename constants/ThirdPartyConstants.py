# constants/ThirdPartyConstants.py

from pathlib import Path
from modules.package_utils import check_package, install_packages, uninstall_packages
from modules.apt_repo_utils import add_apt_repository, remove_apt_repo_and_keyring
from modules.display_utils import display_config_doc

# === CONFIG PATHS & KEYS ===
PRIMARY_CONFIG   = "config/AppConfigSettings.json"
JOBS_KEY         = "ThirdParty"
CONFIG_TYPE      = "third-party"
DEFAULT_CONFIG   = "Default"
CONFIG_DOC       = "doc/ThirdPartyDoc.json"

# === JSON KEYS ===
KEY_REPO_URL        = "url"
KEY_REPO_KEY        = "key"           
KEY_REPO_NAME       = "repo_name"
KEY_CODENAME        = "codename"
KEY_COMPONENT       = "component"
KEY_KEYRING_DIR     = "keyring_dir"
KEY_KEYRING_NAME    = "keyring_name"  


# === VALIDATION CONFIG ===
VALIDATION_CONFIG = {
    "required_job_fields": {
        KEY_REPO_NAME : str,
        KEY_REPO_URL: str,
        KEY_REPO_KEY: str,
        KEY_KEYRING_NAME: str,
        KEY_CODENAME: str,
        KEY_COMPONENT: str,
        KEY_KEYRING_DIR: str,
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
LOG_PREFIX      = "thirdparty_install"
LOG_DIR         = Path.home() / "logs" / "thirdparty"
LOGS_TO_KEEP    = 10
ROTATE_LOG_NAME = f"{LOG_PREFIX}_*.log"

# === USER / LABELS ===
REQUIRED_USER     = "Standard"
INSTALLED_LABEL   = "INSTALLED"
UNINSTALLED_LABEL = "UNINSTALLED"

# === STATUS CHECK CONFIG ===
STATUS_FN_CONFIG = {
    "fn": check_package,                 
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
    "Remove repo & keyring only": {
        "verb": "remove",
        "filter_status": None,
        "label": "REMOVED",
        "prompt": "Remove repo & keyring for the selected entries? [y/n]: ",
        "execute_state": "REMOVE_REPO_KEYRING", 
        "post_state": "CONFIG_LOADING",
        "skip_sub_select": False,
        "skip_prepare_plan": False,
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
    "title": "Select Third-Party package",
    "all_label": "All",
    "cancel_label": "Cancel",
    "cancel_state": "MENU_SELECTION",
}

# === DEPENDENCIES ===
DEPENDENCIES = ["curl", "gpg"]

# === TABLE COLUMNS ===
PLAN_COLUMN_ORDER = [
    KEY_REPO_NAME,
    KEY_REPO_URL,
    KEY_REPO_KEY,
    KEY_CODENAME,
    KEY_COMPONENT,
    KEY_KEYRING_DIR,
    KEY_KEYRING_NAME,
]

OPTIONAL_PLAN_COLUMNS = {}

# === PIPELINES ===
PIPELINE_STATES = {
    "INSTALL": {
        "pipeline": {
            add_apt_repository: {
                "args": [
                    KEY_REPO_NAME,
                    KEY_REPO_URL,
                    KEY_REPO_KEY,
                    KEY_CODENAME,
                    KEY_COMPONENT,
                    KEY_KEYRING_DIR,
                    KEY_KEYRING_NAME,
                ],
                "result": "repo_added",
            },
            install_packages: {
                "args": ["job"],
                "when": "repo_added",
                "result": "installed",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "installed",
        "post_state": "CONFIG_LOADING",
    },
    "UNINSTALL": {
        "pipeline": {
            uninstall_packages: {
                "args": ["job"],
                "result": "uninstalled",
            },
        },
        "label": UNINSTALLED_LABEL,
        "success_key": "uninstalled",
        "post_state": "CONFIG_LOADING",
    },
    "REMOVE_REPO_KEYRING": {
        "pipeline": {
            remove_apt_repo_and_keyring: {
                "args": ["job", KEY_KEYRING_DIR, KEY_KEYRING_NAME],
                "result": "removed",
            },
        },
        "label": "REMOVED",
        "success_key": "removed",
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
