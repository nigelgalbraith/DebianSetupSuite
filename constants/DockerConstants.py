# constants/DockerConstants.py

import os
from pathlib import Path

from modules.docker_utils import (
    docker_image_doesnt_exist,
    build_docker_container,
    start_container,
    stop_container,
    status_container,
    compose_build,
    compose_up,
    compose_down,
    status_compose,
    docker_workload_running,
    remove_container, 
    docker_image_exists,
)
from modules.archive_utils import download_archive_file, install_archive_file, handle_cleanup
from modules.system_utils import (
    expand_path, 
    add_current_user_to_group, 
    is_missing,
)   
from modules.display_utils import display_config_doc
from modules.test_utils import run_tests

# === CONFIG PATHS & KEYS ===
PRIMARY_CONFIG   = "config/AppConfigSettings.json"
JOBS_KEY         = "Docker"
CONFIG_TYPE      = "docker"
DEFAULT_CONFIG   = "default"
CONFIG_DOC       = "doc/DockerDoc.json"

# === JSON KEYS ===
KEY_NAME               = "Name"
KEY_IMAGE              = "Image"
KEY_PORT               = "Port"
KEY_LOCATION           = "Location"
KEY_DOWNLOAD           = "Download"
KEY_TMPDIR             = "TmpDir"
KEY_COMPOSE_FILE       = "ComposeFile"
KEY_COMPOSE_DIR        = "ComposeDir"
KEY_COMPOSE_CONTAINERS = "ComposeContainers"

# === VALIDATION CONFIG ===
VALIDATION_CONFIG = {
    "required_job_fields": {
        KEY_NAME: str,
        KEY_LOCATION: str,
    },
    "example_config": CONFIG_DOC,
}

SECONDARY_VALIDATION = {}

# === DETECTION CONFIG ===
DETECTION_CONFIG = {
    "primary_config": PRIMARY_CONFIG,
    "config_type": CONFIG_TYPE,
    "jobs_key": JOBS_KEY,
    "default_config": DEFAULT_CONFIG,
    "default_config_note": (
        "No model-specific docker config was found. Using the 'default' section instead."
    ),
}

# === LOGGING ===
LOG_PREFIX      = "docker"
LOG_DIR         = Path.home() / "logs" / "docker"
LOGS_TO_KEEP    = 10
ROTATE_LOG_NAME = f"{LOG_PREFIX}_*.log"

# === USER / LABELS ===
REQUIRED_USER     = "Standard"
INSTALLED_LABEL   = "RUNNING"
UNINSTALLED_LABEL = "STOPPED"

# === STATUS CHECK CONFIG ===
STATUS_FN_CONFIG = {
    "fn": docker_workload_running,
    "args": ["job", "meta", KEY_COMPOSE_CONTAINERS],
    "labels": {True: INSTALLED_LABEL, False: UNINSTALLED_LABEL},
}


# === MENU / ACTIONS ===
ACTIONS = {
    "_meta": {"title": "Select an option"},
    f"Download {JOBS_KEY} File": {
        "verb": "download",
        "filter_status": None,
        "label": "DOWNLOADED",
        "prompt": "Download (and extract) sources? [y/n]: ",
        "execute_state": "DOWNLOAD",
        "post_state": "CONFIG_LOADING",
    },
    f"Start {JOBS_KEY} File": {
        "verb": "start",
        "filter_status": False,
        "label": INSTALLED_LABEL,
        "prompt": "Proceed with start? [y/n]: ",
        "execute_state": "START",
        "post_state": "CONFIG_LOADING",
    },
    f"{JOBS_KEY} File Status": {
        "verb": "status",
        "filter_status": None,
        "label": "STATUS",
        "prompt": None,
        "execute_state": "STATUS",
        "post_state": "CONFIG_LOADING",
    },
    f"Rebuild {JOBS_KEY} File": {
        "verb": "build",
        "filter_status": None,
        "label": "BUILT",
        "prompt": "Rebuild image from source? [y/n]: ",
        "execute_state": "BUILD",
        "post_state": "CONFIG_LOADING",
    },
    f"Test {JOBS_KEY} File": {
        "verb": "test",
        "filter_status": True,
        "label": "TESTED",
        "prompt": "Run tests now? [y/n]: ",
        "execute_state": "TEST",
        "post_state": "CONFIG_LOADING",
    },
    f"Stop {JOBS_KEY} File": {
        "verb": "stop",
        "filter_status": True,
        "label": UNINSTALLED_LABEL,
        "prompt": "Proceed with stop? [y/n]: ",
        "execute_state": "STOP",
        "post_state": "CONFIG_LOADING",
    },
    f"Remove {JOBS_KEY} File": {
        "verb": "remove",
        "filter_status": True,
        "label": UNINSTALLED_LABEL,
        "prompt": "This will REMOVE the container(s). Proceed? [y/n]: ",
        "execute_state": "REMOVE",
        "post_state": "CONFIG_LOADING",
    },
    "Add Current User to Docker Group": {
        "verb": "add_docker_group",
        "filter_status": None,
        "label": "GROUP UPDATED",
        "prompt": "Docker group membership grants root-level privileges. Proceed? [y/n]: ",
        "execute_state": "ADD_DOCKER_GROUP",
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
        "prompt": None,
        "execute_state": "FINALIZE",
        "post_state": "FINALIZE",
    },
}

SUB_MENU = {
    "title": "Select container",
    "all_label": "All",
    "cancel_label": "Cancel",
    "cancel_state": "MENU_SELECTION",
}

# === DEPENDENCIES ===
DEPENDENCIES = []

# === TABLE COLUMNS ===
PLAN_COLUMN_ORDER = [
    KEY_NAME,
    KEY_IMAGE,
    KEY_PORT,
    KEY_LOCATION,
    KEY_DOWNLOAD,
    KEY_TMPDIR,
    KEY_COMPOSE_FILE,
    KEY_COMPOSE_DIR,
    KEY_COMPOSE_CONTAINERS,
]

OPTIONAL_PLAN_COLUMNS = {}


# === PIPELINES ===
PIPELINE_STATES = {
    "DOWNLOAD": {
        "pipeline": {
            download_archive_file: {
                "args": [KEY_NAME, KEY_DOWNLOAD, KEY_TMPDIR],
                "result": "archive",
            },
            install_archive_file: {
                "args": ["archive", KEY_LOCATION, True],
                "when": "archive",
                "result": "installed",
            },
            handle_cleanup: {
                "args": ["archive"],
                "when": "installed",
            },
        },
        "label": "DOWNLOADED",
        "success_key": "installed",
        "post_state": "CONFIG_LOADING",
    },
    "START": {
        "pipeline": {
            compose_up: {
                "args": [KEY_COMPOSE_FILE, KEY_COMPOSE_DIR],
                "when": f"meta.{KEY_COMPOSE_FILE}",
                "result": "ok",
            },
            is_missing: {
                "args": [
                    f"?{KEY_COMPOSE_FILE}",
                    "No Compose file configured; using single container.",
                ],
                "result": "single_container",
            },
            docker_image_exists: {
                "args": [KEY_IMAGE],
                "when": "single_container",
                "result": "image_present",
            },
            docker_image_doesnt_exist: {
                "args": [KEY_IMAGE],
                "when": "single_container",
                "result": "image_missing",
            },
            build_docker_container: {
                "args": [KEY_NAME, KEY_LOCATION, KEY_IMAGE],
                "when": "image_missing",
                "result": "image_built",
            },
            start_container: {
                "args": [KEY_NAME, KEY_PORT, KEY_IMAGE],
                "when": ["single_container", "image_present or image_built"],
                "result": "ok",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "STATUS": {
        "pipeline": {
            is_missing: {
                "args": [
                    f"?{KEY_COMPOSE_FILE}",
                    "No Compose file configured; using single container.",
                ],
                "result": "single_container",
            },
            status_compose: {
                "args": ["job", KEY_COMPOSE_CONTAINERS],
                "when": f"meta.{KEY_COMPOSE_FILE}",
                "result": "ok",
            },
            status_container: {
                "args": [KEY_NAME],
                "when": "single_container",
                "result": "ok",
            },
        },
        "label": "STATUS",
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "BUILD": {
        "pipeline": {
            is_missing: {
                "args": [
                    f"?{KEY_COMPOSE_FILE}",
                    "No Compose file configured; using single container.",
                ],
                "result": "single_container",
            },
            compose_down: {
                "args": [KEY_COMPOSE_FILE, KEY_COMPOSE_DIR],
                "when": f"meta.{KEY_COMPOSE_FILE}",
                "result": "compose_stopped",
            },
            compose_build: {
                "args": [KEY_COMPOSE_FILE, KEY_COMPOSE_DIR],
                "when": "compose_stopped",
                "result": "compose_built",
            },
            compose_up: {
                "args": [KEY_COMPOSE_FILE, KEY_COMPOSE_DIR],
                "when": "compose_built",
                "result": "ok",
            },
            stop_container: {
                "args": [KEY_NAME],
                "when": "single_container",
                "result": "container_stopped",
            },
            remove_container: {
                "args": [KEY_NAME],
                "when": "container_stopped",
                "result": "container_removed",
            },
            build_docker_container: {
                "args": [KEY_NAME, KEY_LOCATION, KEY_IMAGE],
                "when": "container_removed",
                "result": "image_built",
            },
            start_container: {
                "args": [KEY_NAME, KEY_PORT, KEY_IMAGE],
                "when": "image_built",
                "result": "ok",
            },
        },
        "label": "BUILT",
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "TEST": {
        "pipeline": {
            run_tests: {
                "args": ["meta.Tests"],
                "result": "ok",
            },
        },
        "label": "TESTED",
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "STOP": {
        "pipeline": {
            is_missing: {
                "args": [
                    f"?{KEY_COMPOSE_FILE}",
                    "No Compose file configured; using single container.",
                ],
                "result": "single_container",
            },
            compose_down: {
                "args": [KEY_COMPOSE_FILE, KEY_COMPOSE_DIR],
                "when": f"meta.{KEY_COMPOSE_FILE}",
                "result": "ok",
            },
            stop_container: {
                "args": [KEY_NAME],
                "when": "single_container",
                "result": "ok",
            },
        },
        "label": UNINSTALLED_LABEL,
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "REMOVE": {
        "pipeline": {
            is_missing: {
                "args": [
                    f"?{KEY_COMPOSE_FILE}",
                    "No Compose file configured; using single container.",
                ],
                "result": "single_container",
            },
            compose_down: {
                "args": [KEY_COMPOSE_FILE, KEY_COMPOSE_DIR],
                "when": f"meta.{KEY_COMPOSE_FILE}",
                "result": "ok",
            },
            remove_container: {
                "args": [KEY_NAME],
                "when": "single_container",
                "result": "ok",
            },
        },
        "label": UNINSTALLED_LABEL,
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "ADD_DOCKER_GROUP": {
        "pipeline": {
            add_current_user_to_group: {
                "args": ["docker"],
                "result": "ok",
            },
        },
        "label": "GROUP UPDATED",
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

