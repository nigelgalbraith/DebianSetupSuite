# constants/DockerConstants.py

from pathlib import Path

from modules.docker_utils import (
    docker_image_exists,
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
)
from modules.archive_utils import download_archive_file, install_archive_file, handle_cleanup
from modules.system_utils import expand_path
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
    "args": [
        "job",
        (lambda job, meta, ctx: meta),
        KEY_COMPOSE_CONTAINERS
    ],
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
            (lambda job: (print(f"[SKIP]  '{job}': no Download/TmpDir configured.") or False)): {
                "args": ["job"],
                "when": (lambda job, meta, ctx: (not meta.get(KEY_DOWNLOAD)) or (not meta.get(KEY_TMPDIR))),
                "result": "ok",
            },
            download_archive_file: {
                "args": [f"meta.{KEY_NAME}", f"meta.{KEY_DOWNLOAD}", f"meta.{KEY_TMPDIR}"],
                "when": (lambda job, meta, ctx: bool(meta.get(KEY_DOWNLOAD)) and bool(meta.get(KEY_TMPDIR))),
                "result": "archive",
            },
            install_archive_file: {
                "args": [
                    (lambda job, meta, ctx: ctx.get("archive")),
                    f"meta.{KEY_LOCATION}",
                    True,
                ],
                "when": (lambda job, meta, ctx: bool(ctx.get("archive")) and bool(meta.get(KEY_LOCATION))),
                "result": "ok",
            },
            handle_cleanup: {
                "args": [(lambda job, meta, ctx: ctx.get("archive"))],
                "when": (lambda job, meta, ctx: bool(ctx.get("archive"))),
                "result": "_",
            },
        },
        "label": "DOWNLOADED",
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "START": {
        "pipeline": {
            # --- Compose start ---
            compose_up: {
                "args": [f"meta.{KEY_COMPOSE_FILE}", f"meta.{KEY_COMPOSE_DIR}"],
                "when": (lambda job, meta, ctx: bool(meta.get(KEY_COMPOSE_FILE))),
                "result": "ok",
            },
            # --- Single container start ---
            docker_image_exists: {
                "args": [lambda job, meta, ctx: meta.get(KEY_IMAGE, "")],
                "when": (lambda job, meta, ctx: not bool(meta.get(KEY_COMPOSE_FILE))),
                "result": "has_image",
            },
            (lambda path: (expand_path(path).mkdir(parents=True, exist_ok=True) or True)): {
                "args": [f"meta.{KEY_LOCATION}"],
                "when": (lambda job, meta, ctx: (not bool(meta.get(KEY_COMPOSE_FILE))) and bool(meta.get(KEY_LOCATION))),
                "result": "_",
            },
            build_docker_container: {
                "args": [
                    f"meta.{KEY_NAME}",
                    (lambda job, meta, ctx: str(expand_path(meta.get(KEY_LOCATION, "")))),
                    f"meta.{KEY_IMAGE}",
                ],
                "when": (lambda job, meta, ctx: (not bool(meta.get(KEY_COMPOSE_FILE))) and (not bool(ctx.get("has_image"))) and bool(meta.get(KEY_LOCATION))),
                "result": "_",
            },
            start_container: {
                "args": [f"meta.{KEY_NAME}", f"meta.{KEY_PORT}", f"meta.{KEY_IMAGE}"],
                "when": (lambda job, meta, ctx: not bool(meta.get(KEY_COMPOSE_FILE))),
                "result": "ok",
            },
        },
        "label": INSTALLED_LABEL,
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "STATUS": {
        "pipeline": {
            status_compose: {
                "args": ["job", f"meta.{KEY_COMPOSE_CONTAINERS}"],
                "when": (lambda job, meta, ctx: bool(meta.get(KEY_COMPOSE_FILE))),
                "result": "ok",
            },
            status_container: {
                "args": [f"meta.{KEY_NAME}"],
                "when": (lambda job, meta, ctx: not bool(meta.get(KEY_COMPOSE_FILE))),
                "result": "ok",
            },
        },
        "label": "STATUS",
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "BUILD": {
        "pipeline": {
            compose_down: {
                "args": [f"meta.{KEY_COMPOSE_FILE}", f"meta.{KEY_COMPOSE_DIR}"],
                "when": (lambda job, meta, ctx: bool(meta.get(KEY_COMPOSE_FILE))),
                "result": "_",
            },
            compose_build: {
                "args": [f"meta.{KEY_COMPOSE_FILE}", f"meta.{KEY_COMPOSE_DIR}"],
                "when": (lambda job, meta, ctx: bool(meta.get(KEY_COMPOSE_FILE))),
                "result": "_",
            },
            compose_up: {
                "args": [f"meta.{KEY_COMPOSE_FILE}", f"meta.{KEY_COMPOSE_DIR}"],
                "when": (lambda job, meta, ctx: bool(meta.get(KEY_COMPOSE_FILE))),
                "result": "ok",
            },
            stop_container: {
                "args": [f"meta.{KEY_NAME}"],
                "when": (lambda job, meta, ctx: not bool(meta.get(KEY_COMPOSE_FILE))),
                "result": "_",
            },
            remove_container: {
                "args": [f"meta.{KEY_NAME}"],
                "when": (lambda job, meta, ctx: not bool(meta.get(KEY_COMPOSE_FILE))),
                "result": "_",
            },
            build_docker_container: {
                "args": [
                    f"meta.{KEY_NAME}",
                    f"meta.{KEY_LOCATION}",
                    f"meta.{KEY_IMAGE}",
                ],
                "when": (lambda job, meta, ctx: not bool(meta.get(KEY_COMPOSE_FILE))),
                "result": "_",
            },
            start_container: {
                "args": [f"meta.{KEY_NAME}", f"meta.{KEY_PORT}", f"meta.{KEY_IMAGE}"],
                "when": (lambda job, meta, ctx: not bool(meta.get(KEY_COMPOSE_FILE))),
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
                "args": [f"meta.Tests"],
                "when": (lambda job, meta, ctx: bool(meta.get("Tests"))),
                "result": "ok",
            },
        },
        "label": "TESTED",
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "STOP": {
        "pipeline": {
            # Compose stop
            compose_down: {
                "args": [f"meta.{KEY_COMPOSE_FILE}", f"meta.{KEY_COMPOSE_DIR}"],
                "when": (lambda job, meta, ctx: bool(meta.get(KEY_COMPOSE_FILE))),
                "result": "ok",
            },
            # Single container stop
            stop_container: {
                "args": [f"meta.{KEY_NAME}"],
                "when": (lambda job, meta, ctx: not bool(meta.get(KEY_COMPOSE_FILE))),
                "result": "ok",
            },
        },
        "label": UNINSTALLED_LABEL,
        "success_key": "ok",
        "post_state": "CONFIG_LOADING",
    },
    "REMOVE": {
        "pipeline": {
            compose_down: {
                "args": [f"meta.{KEY_COMPOSE_FILE}", f"meta.{KEY_COMPOSE_DIR}"],
                "when": (lambda job, meta, ctx: bool(meta.get(KEY_COMPOSE_FILE))),
                "result": "ok",
            },
            remove_container: {
                "args": [f"meta.{KEY_NAME}"],
                "when": (lambda job, meta, ctx: not bool(meta.get(KEY_COMPOSE_FILE))),
                "result": "ok",
            },
        },
        "label": UNINSTALLED_LABEL,
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
