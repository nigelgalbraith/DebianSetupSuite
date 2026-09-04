# constants/YouTubeConstants.py
from pathlib import Path
from modules.browser_utils import open_browser, wait_for_user
from modules.display_utils import display_config_doc
from modules.ytdlp_utils import run_yt_dlp
from modules.system_utils import check_folder_path

# === CONFIG PATHS & KEYS ===
PRIMARY_CONFIG = "config/AppConfigSettings.json"
JOBS_KEY       = "YouTube"
CONFIG_TYPE    = "youtube"
DEFAULT_CONFIG = "Default"
CONFIG_DOC     = "doc/YouTubeDoc.json"

# === JSON KEYS ===
KEY_PLAYLIST_URL = "playlist_url"
KEY_DOWNLOAD_PATH = "download_path"
KEY_FORMAT        = "format"

# === BROWSER ===
BROWSER = "firefox"


# === VALIDATION CONFIG ===
VALIDATION_CONFIG = {
    "required_job_fields": {
        KEY_PLAYLIST_URL: str,
        KEY_DOWNLOAD_PATH: str,
        KEY_FORMAT: str,
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
LOG_PREFIX      = "youtube_job"
LOG_DIR         = Path.home() / "logs" / "youtube"
LOGS_TO_KEEP    = 10
ROTATE_LOG_NAME = f"{LOG_PREFIX}_*.log"

# === USER / LABELS ===
REQUIRED_USER       = "Standard"
INSTALLED_LABEL   = "DOWNLOAD PATH AVAILABLE"
UNINSTALLED_LABEL = "DOWNLOAD PATH UNAVAILABLE"
COMPLETE_LABEL    = "DOWNLOAD COMPLETE"

# === STATUS FUNCTION CONFIG ===
STATUS_FN_CONFIG = {
    "fn": check_folder_path,
    "args": [
        lambda j, m, c: m.get(KEY_DOWNLOAD_PATH),
    ],
    "labels": {
        True: INSTALLED_LABEL,
        False: UNINSTALLED_LABEL,
    },
}

# === DEPENDENCIES ===
DEPENDENCIES = ["firefox-esr", "ffmpeg"]

# === ACTIONS ===
ACTIONS = {
    "_meta": {
        "title": "YouTube Downloader",
    },
    "Open YouTube playlist": {
        "verb": "open youtube playlist",
        "filter_status": None,
        "label": None,
        "prompt": "Open YouTube playlist in Firefox? [y/n]: ",
        "execute_state": "OPEN_PLAYLIST",
        "post_state": "CONFIG_LOADING",
        "skip_sub_select": False,
        "skip_prepare_plan": True,
    },
    "Download playlist": {
        "verb": "download playlist",
        "filter_status": None,
        "label": COMPLETE_LABEL,
        "prompt": "Download YouTube playlist? [y/n]: ",
        "execute_state": "DOWNLOAD_PLAYLIST",
        "post_state": "CONFIG_LOADING",
        "skip_sub_select": False,
        "skip_prepare_plan": False,
    },
    "Run all": {
        "verb": "run all",
        "filter_status": None,
        "label": COMPLETE_LABEL,
        "prompt": "Open YouTube and download playlist? [y/n]: ",
        "execute_state": "RUN_ALL",
        "post_state": "CONFIG_LOADING",
        "skip_sub_select": False,
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
    "title": "Select YouTube Playlist",
    "all_label": "All",
    "cancel_label": "Cancel",
    "cancel_state": "MENU_SELECTION",
}

# === PLANNING COLUMNS ===
PLAN_COLUMN_ORDER = [
    KEY_PLAYLIST_URL,
    KEY_DOWNLOAD_PATH,
    KEY_FORMAT,
]

OPTIONAL_PLAN_COLUMNS = {}

# === PIPELINE STATES ===
PIPELINE_STATES = {
    "OPEN_PLAYLIST": {
        "pipeline": {
            open_browser: {
                "args": [
                    BROWSER,
                    lambda job, meta, ctx: meta[KEY_PLAYLIST_URL],
                ],
                "result": "browser_opened",
            },
        },
        "label": "PLAYLIST OPENED",
        "success_key": "browser_opened",
        "post_state": "CONFIG_LOADING",
    },
    "DOWNLOAD_PLAYLIST": {
        "pipeline": {
            run_yt_dlp: {
                "args": [
                    lambda job, meta, ctx: meta[KEY_PLAYLIST_URL],
                    lambda job, meta, ctx: meta[KEY_DOWNLOAD_PATH],
                    lambda job, meta, ctx: meta[KEY_FORMAT],
                    BROWSER,
                ],
                "result": "complete",
            },
        },
        "label": COMPLETE_LABEL,
        "success_key": "complete",
        "post_state": "CONFIG_LOADING",
    },
    "RUN_ALL": {
        "pipeline": {
            open_browser: {
                "args": [
                    BROWSER,
                    lambda job, meta, ctx: meta[KEY_PLAYLIST_URL],
                ],
                "result": "browser_opened",
            },
            wait_for_user: {
                "args": [
                    (
                        "\n"
                        "YouTube has been opened in Firefox.\n\n"
                        "If this is your first run, log into YouTube now.\n"
                        "If you are already logged in, no action is required.\n\n"
                        "Press ENTER when ready to continue: "
                    ),
                ],
                "result": "user_ready",
            },
            run_yt_dlp: {
                "args": [
                    lambda job, meta, ctx: meta[KEY_PLAYLIST_URL],
                    lambda job, meta, ctx: meta[KEY_DOWNLOAD_PATH],
                    lambda job, meta, ctx: meta[KEY_FORMAT],
                    BROWSER,
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