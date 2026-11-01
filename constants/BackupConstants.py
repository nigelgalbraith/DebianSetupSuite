# constants/BackupConstants.py
from pathlib import Path
from modules.system_utils import copy_folder_dict, copy_file_dict, check_folder_path, make_dirs
from modules.archive_utils import create_zip_archive 
from modules.display_utils import display_config_doc

# === CONFIG PATHS & KEYS ===
PRIMARY_CONFIG = "config/AppConfigSettings.json"
JOBS_KEY       = "Backup"
CONFIG_TYPE    = "backup"
DEFAULT_CONFIG = "Default"
CONFIG_DOC     = "doc/BackupDoc.json"

# === JSON KEYS ===
KEY_BACKUP_FOLDERS          = "CopyFolders"
KEY_COPY_FOLDERS_EXCLUDE    = "CopyFoldersExclude"
KEY_SOURCE_FILES            = "CopyFiles"
KEY_ZIP_ARCHIVES            = "ZipArchives"
KEY_CHECK_PATH              = "CheckPath"

# === COMMON SUBKEYS ===
SUBKEY_COPY_NAME    = "copyName"
SUBKEY_SRC          = "src"
SUBKEY_DEST         = "dest"
SUBKEY_ZIP_NAME     = "zipName"
SUBKEY_OUTPUT       = "output"


# === VALIDATION CONFIG ===
VALIDATION_CONFIG = {
    "required_job_fields": {
        KEY_BACKUP_FOLDERS: list,
        KEY_SOURCE_FILES: list,
        KEY_ZIP_ARCHIVES: list,
        KEY_CHECK_PATH: str,
    },
    "example_config": CONFIG_DOC,
}

# === SECONDARY VALIDATION ===
SECONDARY_VALIDATION = {
    KEY_BACKUP_FOLDERS: {
        "required_job_fields": {
            SUBKEY_COPY_NAME: str,
            SUBKEY_SRC: str,
            SUBKEY_DEST: str,
        },
        "allow_empty": True,
    },

    KEY_SOURCE_FILES: {
        "required_job_fields": {
            SUBKEY_COPY_NAME: str,
            SUBKEY_SRC: str,
            SUBKEY_DEST: str,
        },
        "allow_empty": True,
    },
    KEY_ZIP_ARCHIVES: {
        "required_job_fields": {
            SUBKEY_ZIP_NAME: str,
            SUBKEY_SRC: str,
            SUBKEY_OUTPUT: str,
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
LOG_PREFIX      = "backup_job"
LOG_DIR         = Path.home() / "logs" / "backup"
LOGS_TO_KEEP    = 10
ROTATE_LOG_NAME = f"{LOG_PREFIX}_*.log"

# === USER / LABELS ===
REQUIRED_USER     = "Standard"
INSTALLED_LABEL   = "TARGET INITIALISED"
UNINSTALLED_LABEL = "TARGET EMPTY"

# === STATUS FUNCTION CONFIG ===
STATUS_FN_CONFIG = {
    "fn": check_folder_path,
    "args": [KEY_CHECK_PATH],
    "labels": {True: INSTALLED_LABEL, False: UNINSTALLED_LABEL},
}

# === DEPENDENCIES ===
DEPENDENCIES = ["rsync", "zip"]

# === ACTIONS ===
ACTIONS = {
    "_meta": {"title": "Backup Utility"},
    "Copy Folders": {
        "verb": "copy folders",
        "filter_status": None,
        "label": INSTALLED_LABEL,
        "prompt": "Copy folders to backup destination? [y/n]: ",
        "execute_state": "COPY_FOLDERS",
        "post_state": "CONFIG_LOADING",
    },
    "Copy Files": {
        "verb": "copy files",
        "filter_status": None,
        "label": INSTALLED_LABEL,
        "prompt": "Copy individual files to backup destination? [y/n]: ",
        "execute_state": "COPY_FILES",
        "post_state": "CONFIG_LOADING",
    },
    "Create Zip Archive": {
        "verb": "archive",
        "filter_status": None,
        "label": INSTALLED_LABEL,
        "prompt": "Create zip archive from backup content? [y/n]: ",
        "execute_state": "CREATE_ZIP",
        "post_state": "CONFIG_LOADING",
    },
    "Run All Tasks": {
        "verb": "run all backup tasks",
        "filter_status": None,
        "label": INSTALLED_LABEL,
        "prompt": "Run all backup steps (folders, files, zip)? [y/n]: ",
        "execute_state": "ALL_TASKS",
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

# === SUB-MENU ===
SUB_MENU = {
    "title": "Select Backup Job",
    "all_label": "All",
    "cancel_label": "Cancel",
    "cancel_state": "MENU_SELECTION",
}

# === PLANNING COLUMNS ===
PLAN_COLUMN_ORDER = [
    KEY_BACKUP_FOLDERS,
    KEY_SOURCE_FILES,
    KEY_ZIP_ARCHIVES,
]

OPTIONAL_PLAN_COLUMNS = {}


# === PIPELINE STATES ===
PIPELINE_STATES = {
    "COPY_FOLDERS": {
        "pipeline": {
            make_dirs: {
                "args": [KEY_BACKUP_FOLDERS],
                "result": "dirs_ready",
            },
            copy_folder_dict: {
                "args": [KEY_BACKUP_FOLDERS, KEY_COPY_FOLDERS_EXCLUDE],
                "when": "dirs_ready",
                "result": "folders_copied",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "folders_copied",
        "post_state": "CONFIG_LOADING",
    },
    "COPY_FILES": {
        "pipeline": {
            copy_file_dict: {
                "args": [KEY_SOURCE_FILES],
                "result": "files_copied",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "files_copied",
        "post_state": "CONFIG_LOADING",
    },
    "CREATE_ZIP": {
        "pipeline": {
            create_zip_archive: {
                "args": [KEY_ZIP_ARCHIVES],
                "result": "archives_created",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "archives_created",
        "post_state": "CONFIG_LOADING",
    },
    "ALL_TASKS": {
        "pipeline": {
            make_dirs: {
                "args": [KEY_BACKUP_FOLDERS],
                "result": "dirs_ready",
            },
            copy_folder_dict: {
                "args": [KEY_BACKUP_FOLDERS, KEY_COPY_FOLDERS_EXCLUDE],
                "when": "dirs_ready",
                "result": "folders_copied",
            },
            copy_file_dict: {
                "args": [KEY_SOURCE_FILES],
                "when": "folders_copied",
                "result": "files_copied",
            },
            create_zip_archive: {
                "args": [KEY_ZIP_ARCHIVES],
                "result": "archives_created",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "archives_created",
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
