# LauncherConstants.py
from __future__ import annotations

from pathlib import Path
from typing import Any, Dict

from modules.archive_utils import handle_cleanup
from modules.package_utils import (
    check_package,
    download_deb_file,
    install_deb_file,
    uninstall_packages,
    install_packages,
)
from modules.service_utils import (
    restart_service,
)
from modules.system_utils import (
    copy_file_dict,
    copy_folder_dict,
    chmod_paths, chown_paths,
    create_user_login,
    remove_user,
    kill_user_session,
    add_user_to_group,
    make_dirs,
    set_default_display_manager,
    remove_paths,
)
from modules.display_utils import display_config_doc

# === CONFIG PATHS & KEYS ===
PRIMARY_CONFIG   = "config/AppConfigSettings.json"
JOBS_KEY         = "Launcher"
CONFIG_TYPE      = "Launcher"
DEFAULT_CONFIG   = "Default"
CONFIG_DOC       = "doc/LauncherDoc.json"

# === JSON KEYS ===
KEY_DOWNLOAD_URL       = "DownloadURL"
KEY_DOWNLOAD_DIR       = "download_dir"
KEY_SETTINGS_FILES     = "SettingsFiles"
KEY_SETTINGS_FOLDERS   = "SettingsFolders"
KEY_PACKAGES           = "Packages"
KEY_REMOVE_PATHS       = "RemovePaths"

# New: Dir lists & groups
KEY_SETUP_DIRS         = "SetupDirs"
KEY_USERS              = "Users"
KEY_USER_GROUPS        = "UserGroups"

# === KIOSK (JSON) KEYS ===
KEY_KIOSK_FILES            = "KioskFiles"

# === PERMS (JSON) KEYS ===
KEY_CHMOD_PATHS          = "ChmodPaths"
KEY_CHOWN_PATHS          = "ChownPaths"
KEY_CHOWN_USER           = "ChownUser"
KEY_CHOWN_RECURSIVE      = "ChownRecursive"

# settings-scoped perms ===
KEY_SETTINGS_CHMOD_PATHS = "SettingsChmodPaths"
KEY_SETTINGS_CHOWN_PATHS = "SettingsChownPaths"

# === Packages (JSON) Keys ===
KEY_ADDITIONAL_PKGS    = "AdditionalPackages"

# === Display Manager  ===
KEY_DEFAULT_DM         = "DefaultDM"   
KEY_KIOSK_DM           = "KioskDM"     

# === SUB-JSON KEYS ===
KEY_COPY_NAME          = "copyName"
KEY_SRC                = "src"
KEY_DEST               = "dest"

# === VALIDATION CONFIG ===
VALIDATION_CONFIG: Dict[str, Any] = {
    "required_job_fields": {
        KEY_DOWNLOAD_URL: str,
        KEY_DOWNLOAD_DIR: str,
        KEY_SETTINGS_FILES: list,
        KEY_SETTINGS_FOLDERS: list,
        KEY_SETTINGS_CHMOD_PATHS: list,
        KEY_SETTINGS_CHOWN_PATHS: list,
        KEY_REMOVE_PATHS: list,
        KEY_SETUP_DIRS: list,
        KEY_KIOSK_FILES: list,
        KEY_DEFAULT_DM: dict,   
        KEY_KIOSK_DM: dict,    
        KEY_ADDITIONAL_PKGS: list,
        KEY_CHMOD_PATHS: list,
        KEY_CHOWN_PATHS: list,
        KEY_CHOWN_RECURSIVE: (bool, type(None)),
        KEY_DEFAULT_DM: dict,
        KEY_KIOSK_DM: dict,
    },
    "example_config": CONFIG_DOC,
}

# === SECONDARY VALIDATION  ===
SECONDARY_VALIDATION: Dict[str, Any] = {
    KEY_SETTINGS_FILES: {
        "required_job_fields": {KEY_COPY_NAME: str, KEY_SRC: str, KEY_DEST: str},
        "allow_empty": True,
    },
    KEY_KIOSK_FILES: {
        "required_job_fields": {KEY_COPY_NAME: str, KEY_SRC: str, KEY_DEST: str},
        "allow_empty": True,
    },
    KEY_SETTINGS_FOLDERS: {
        "required_job_fields": {KEY_COPY_NAME: str, KEY_SRC: str, KEY_DEST: str},
        "allow_empty": True,
    },
    KEY_REMOVE_PATHS: {
        "allow_empty": True,
    },
    KEY_CHOWN_PATHS: {
        "required_job_fields": {"path": str},
        "allow_empty": True
    },
    KEY_SETTINGS_CHMOD_PATHS: {
        "required_job_fields": {"path": str, "mode": str},
        "allow_empty": True
    },
    KEY_SETTINGS_CHOWN_PATHS: {
        "required_job_fields": {"path": str},
        "allow_empty": True
    },
    KEY_DEFAULT_DM: {
        "required_job_fields": {"package": str, "service": str},
        "allow_empty": False
    },
    KEY_KIOSK_DM: {
        "required_job_fields": {"package": str, "service": str},
        "allow_empty": False
    },
    "example_config": CONFIG_DOC,
}

# === DETECTION CONFIG ===
DETECTION_CONFIG: Dict[str, Any] = {
    "primary_config": PRIMARY_CONFIG,
    "config_type": CONFIG_TYPE,
    "jobs_key": JOBS_KEY,
    "default_config": DEFAULT_CONFIG,
    "default_config_note": (
        "No model-specific config was found. "
        "Using the 'Default' section instead. "
    ),
}

# === LOGGING ===
LOG_PREFIX      = "launcher_install"
LOG_DIR         = Path.home() / "logs" / "deb"
LOGS_TO_KEEP    = 10
ROTATE_LOG_NAME = f"{LOG_PREFIX}_*.log"

# === USER / LABELS ===
REQUIRED_USER     = "root"
INSTALLED_LABEL   = "INSTALLED"
UNINSTALLED_LABEL = "UNINSTALLED"
RESET_LABEL       = "Reset"

# === STATUS CHECK CONFIG ===
STATUS_FN_CONFIG: Dict[str, Any] = {
    "fn": check_package,
    "args": ["job"],
    "labels": {True: INSTALLED_LABEL, False: UNINSTALLED_LABEL},
}

# === COLUMN ORDER ===
PLAN_COLUMN_ORDER = [
    KEY_DOWNLOAD_URL,
    KEY_DOWNLOAD_DIR,
    KEY_SETTINGS_FILES,
    KEY_SETTINGS_FOLDERS,
    KEY_REMOVE_PATHS,
    KEY_SETUP_DIRS,
    KEY_DEFAULT_DM,
    KEY_KIOSK_DM,
]
OPTIONAL_PLAN_COLUMNS = {}

# === ACTIONS ===
ACTIONS: Dict[str, Dict[str, Any]] = {
    "_meta": {"title": f"{JOBS_KEY} Setup"},

    f"Install / Configure {JOBS_KEY}": {
        "verb": "install",
        "filter_status": False,
        "label": UNINSTALLED_LABEL,
        "prompt": f"Install/configure {JOBS_KEY}? [y/n]: ",
        "execute_state": "INSTALL",
        "post_state": "CONFIG_LOADING",
    },
    f"Uninstall {JOBS_KEY}": {
        "verb": "uninstall",
        "filter_status": True,
        "label": INSTALLED_LABEL,
        "prompt": f"Uninstall {JOBS_KEY}? [y/n]: ",
        "execute_state": "UNINSTALL",
        "post_state": "CONFIG_LOADING",
    },
    f"Update {JOBS_KEY} Settings": {
        "verb": "update",
        "filter_status": True,
        "label": INSTALLED_LABEL,
        "prompt": f"Update {JOBS_KEY} settings (copy templates + apply edits)? [y/n]: ",
        "execute_state": "UPDATE_SETTINGS",
        "post_state": "CONFIG_LOADING",
    },
    f"Reset {JOBS_KEY} Only (recreate defaults)": {
        "verb": "reset",
        "filter_status": True,
        "label": RESET_LABEL,
        "prompt": f"Reset {JOBS_KEY} config to defaults? [y/n]: ",
        "execute_state": "RESET",
        "post_state": "CONFIG_LOADING",
    },
    "Enable Kiosk (Openbox autologin)": {
        "verb": "enable_kiosk",
        "filter_status": None,
        "label": None,
        "prompt": "Enable kiosk for selected launcher? [y/n]: ",
        "execute_state": "ENABLE_KIOSK",
        "post_state": "CONFIG_LOADING",
    },
    "Disable Kiosk (restore normal login)": {
        "verb": "disable_kiosk",
        "filter_status": None,
        "label": None,
        "prompt": "Disable kiosk for selected launcher? [y/n]: ",
        "execute_state": "DISABLE_KIOSK",
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

SUB_MENU: Dict[str, str] = {
    "title": "Select Deb Package",
    "all_label": "All",
    "cancel_label": "Cancel",
    "cancel_state": "MENU_SELECTION",
}

# === DEPENDENCIES ===
DEPENDENCIES = ["wget", "dpkg", "openbox"]

# === PIPELINES  ===
PIPELINE_STATES: Dict[str, Dict[str, Any]] = {
    "INSTALL": {
        "pipeline": {
            download_deb_file: {
                "args": ["job", KEY_DOWNLOAD_URL, KEY_DOWNLOAD_DIR],
                "result": "download_ok",
            },
            install_deb_file: {
                "args": [lambda j, m, c: Path(m[KEY_DOWNLOAD_DIR]) / f"{j}.deb", "job",],
                "result": "installed",
                "when": "download_ok",
            },
            install_packages: {
                "args": [
                    lambda j, m, c: [
                        m[KEY_DEFAULT_DM]["package"],
                        m[KEY_KIOSK_DM]["package"],
                    ] + m.get(KEY_ADDITIONAL_PKGS, []),
                ],
                "result": "pkgs_installed",
            },
            handle_cleanup: {
                "args": [
                    lambda j, m, c: Path(m[KEY_DOWNLOAD_DIR]) / f"{j}.deb",
                ],
                "result": "cleaned",
                "when": "pkgs_installed",
            },
            create_user_login: {
                "args": [
                    lambda j, m, c: m.get(KEY_CHOWN_USER, "launcher"),
                ],
                "result": "user_ok",
            },
            add_user_to_group: {
                "args": [
                    lambda j, m, c: m.get(KEY_USERS, []),
                    lambda j, m, c: m.get(KEY_USER_GROUPS, []),
                ],
                "result": "groups_added",
            },
            make_dirs: {
                "args": [KEY_SETUP_DIRS],
                "result": "setup_dirs_ok",
            },
            copy_file_dict: {
                "args": [
                    lambda j, m, c: (m.get(KEY_KIOSK_FILES, []) or []) + (m.get(KEY_SETTINGS_FILES, []) or []),
                ],
                "result": "files_copied",
            },
            copy_folder_dict: {
                "args": [KEY_SETTINGS_FOLDERS],
                "result": "settings_folders_copied",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "installed",
        "post_state": "CONFIG_LOADING",
    },

    "UPDATE_SETTINGS": {
        "pipeline": {
            create_user_login: {"args": [lambda j, m, c: m.get(KEY_CHOWN_USER, "launcher")], "result": "user_ok"},
            add_user_to_group: {"args": [lambda j, m, c: m.get(KEY_USERS, []), lambda j, m, c: m.get(KEY_USER_GROUPS, [])], "result": "groups_added"},
            make_dirs:      {"args": [KEY_SETUP_DIRS], "result": "setup_dirs_ok"},
            copy_file_dict: {"args": [KEY_SETTINGS_FILES], "result": "settings_files_copied"},
            copy_folder_dict: {"args": [KEY_SETTINGS_FOLDERS], "result": "settings_folders_copied"},
            chmod_paths: {
                "args": [lambda j, m, c: (
                    (m.get(KEY_SETTINGS_CHMOD_PATHS) or []) or
                    ([{"path": f[KEY_DEST], "mode": "644"} for f in (m.get(KEY_SETTINGS_FILES, []) or [])] +
                     [{"path": d[KEY_DEST], "mode": "755"} for d in (m.get(KEY_SETTINGS_FOLDERS, []) or [])])
                )],
                "result": "chmod_ok"
            },
            chown_paths: {
                "args": [
                    lambda j, m, c: m.get(KEY_CHOWN_USER, "launcher"),
                    lambda j, m, c: (
                        (m.get(KEY_SETTINGS_CHOWN_PATHS) or []) or
                        ([{"path": f[KEY_DEST]} for f in (m.get(KEY_SETTINGS_FILES, []) or [])] +
                         [{"path": d[KEY_DEST]} for d in (m.get(KEY_SETTINGS_FOLDERS, []) or [])])
                    ),
                    lambda j, m, c: True
                ],
                "result": "chown_ok"
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "settings_files_copied",
        "post_state": "CONFIG_LOADING",
    },

    "RESET": {
        "pipeline": {
            remove_paths: {"args": [KEY_REMOVE_PATHS], "result": "removed"},
            make_dirs:    {"args": [KEY_SETUP_DIRS], "result": "reset_ok"},
        },
        "label": RESET_LABEL,
        "success_key": "reset_ok",
        "post_state": "CONFIG_LOADING",
    },

    "UNINSTALL": {
    "pipeline": {
         uninstall_packages: {
            "args": ["job"],
            "result": "uninstalled",
        },
        remove_paths: {"args": [KEY_REMOVE_PATHS], "result": "removed"},
        set_default_display_manager: {
            "args": [
                lambda j, m, c: m[KEY_DEFAULT_DM]["package"],
                lambda j, m, c: m[KEY_DEFAULT_DM]["service"],
            ],
            "result": "dm_set"
        },
        restart_service: {"args": [lambda j, m, c: m[KEY_DEFAULT_DM]["service"]], "result": "dm_on"},
        make_dirs: {"args": [KEY_SETUP_DIRS], "result": "cleanup_ok"},
    },
    "label": UNINSTALLED_LABEL,
    "success_key": "uninstalled",
    "post_state": "CONFIG_LOADING",
    },

    "ENABLE_KIOSK": {
        "pipeline": {
            create_user_login: {"args": [lambda j, m, c: m.get(KEY_CHOWN_USER, "launcher")], "result": "user_ok"},
            add_user_to_group: {"args": [lambda j, m, c: m.get(KEY_USERS, []), lambda j, m, c: m.get(KEY_USER_GROUPS, [])], "result": "groups_added"},
            make_dirs:         {"args": [KEY_SETUP_DIRS],  "result": "setup_dirs_ok"},
            copy_file_dict:    {"args": [lambda j, m, c: (m.get(KEY_KIOSK_FILES, []) or []) + (m.get(KEY_SETTINGS_FILES, []) or [])], "result": "files_copied"},
            copy_folder_dict:  {"args": [KEY_SETTINGS_FOLDERS], "result": "settings_folders_copied"},
            chmod_paths:       {"args": [KEY_CHMOD_PATHS], "result": "chmod_ok"},
            chown_paths:       {"args": [lambda j, m, c: m.get(KEY_CHOWN_USER, "launcher"), KEY_CHOWN_PATHS, lambda j, m, c: bool(m.get(KEY_CHOWN_RECURSIVE, False))], "result": "chown_ok"},
            set_default_display_manager: {"args": [
                lambda j, m, c: m[KEY_KIOSK_DM]["package"],
                lambda j, m, c: m[KEY_KIOSK_DM]["service"],
            ], "result": "dm_set"},
            restart_service: {"args": [lambda j, m, c: m[KEY_KIOSK_DM]["service"]], "result": "dm_on"},
        },
        "label": "KIOSK",
        "success_key":  "dm_on",
        "post_state": "CONFIG_LOADING",
    },

    "DISABLE_KIOSK": {
        "pipeline": {
            set_default_display_manager: {"args": [
                lambda j,m,c: m[KEY_DEFAULT_DM]["package"],
                lambda j,m,c: m[KEY_DEFAULT_DM]["service"],
            ], "result": "dm_set"},
            restart_service: {"args": [lambda j, m, c: m[KEY_DEFAULT_DM]["service"]], "result": "dm_on"},
        },
        "label": "KIOSK",
        "success_key": "dm_on",
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
