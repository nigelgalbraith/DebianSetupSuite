#!/usr/bin/env python3
"""
state_machine_utils.py

Small utilities used by the installer state machine: constants loading, CLI parsing,
argument resolution, and step conditions.
"""

import argparse
import importlib
import subprocess
import sys
import os  
from typing import Any, Dict, List, Optional

# ---------------------------------------------------------------------
# SMALL HELPERS
# ---------------------------------------------------------------------


def status_candidates(job_status: Dict[str, bool], want: Optional[bool]) -> List[str]:
    """
    Return job names filtered by desired status without changing the original order.

    want:
      - None  -> all jobs
      - True  -> only installed/ok jobs
      - False -> only not-installed/fail jobs

    Example:
        targets = status_candidates(status_map, want=True)
    """
    if want is None:
        return list(job_status.keys())
    if want is True:
        return [j for j, ok in job_status.items() if ok]
    return [j for j, ok in job_status.items() if not ok]


# ---------------------------------------------------------------------
# CONSTANTS / CLI
# ---------------------------------------------------------------------


def load_constants_from_module(module_path: str, required: list[str]):
    """
    Import a constants module and return a namespace-like object of uppercase attributes.

    Validates that all names in `required` exist in the imported module.

    Example:
        consts = load_constants_from_module("constants.DebConstants", ["ACTIONS", "JOBS"])
    """
    mod = importlib.import_module(module_path)
    consts = {name: getattr(mod, name) for name in dir(mod) if name.isupper()}
    missing = [n for n in required if n not in consts]
    if missing:
        raise SystemExit(
            f"[FATAL] Constants module '{module_path}' is missing: {', '.join(missing)}"
        )
    return type("Constants", (), consts)()


def parse_args_early() -> argparse.Namespace:
    """
    Parse only the --constants flag early, before full constants-dependent parsing.

    Example:
        early = parse_args_early()
        consts = load_constants_from_module(early.constants, required=[...])
    """
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("--constants", help="Python module path for constants (e.g. constants.DebConstants)")
    return p.parse_known_args()[0]


def parse_args(consts: Any) -> argparse.Namespace:
    """
    Parse CLI flags for non-interactive state machine operation.

    Builds --action choices dynamically from consts.ACTIONS (excluding '_meta').

    Example:
        args = parse_args(consts)
        if args.status:
            ...
    """
    p = argparse.ArgumentParser(description="Installer state machine")
    p.add_argument("--yes", "-y", action="store_true", help="Auto-confirm prompts (non-interactive).")

    action_choices = [k for k in consts.ACTIONS.keys() if k != "_meta"]
    if "Cancel" in action_choices:
        action_choices = [c for c in action_choices if c != "Cancel"] + ["Cancel"]

    p.add_argument("--action", choices=action_choices,
                   help="Action to perform non-interactively.")
    p.add_argument("--targets", help="Comma-separated list of job names to operate on (used with --action).")
    p.add_argument("--status", action="store_true", help="Status-only: show installed/uninstalled summary and exit.")
    p.add_argument("--plan-only", action="store_true", help="Print the execution plan and exit without making changes.")
    p.add_argument("--constants", default="constants.DebConstants",
                   help="Python module path for constants (e.g. constants.DebConstants)")
    return p.parse_args()

# ---------------------------------------------------------------------
# ARG RESOLUTION / CONDITIONS
# ---------------------------------------------------------------------


def resolve_arg(spec: Any, job: str, meta: Dict[str, Any], ctx: Dict[str, Any]) -> Any:
    """
    Resolve a pipeline arg spec into a concrete value.

    Resolution order:
      1) callable(spec) -> spec(job, meta, ctx)
      2) ctx lookup (string key)
      3) meta lookup (supports dotted key form; uses last segment)
      4) literal "job" -> job name
      5) fallback -> original spec

    Example:
        value = resolve_arg("paths.output", job, meta, ctx)
    """
    if callable(spec):
        return spec(job, meta, ctx)
    if isinstance(spec, str):
        if spec in ctx:
            return ctx[spec]
        key = spec.split(".", 1)[-1]
        if key in meta:
            return meta[key]
        if spec == "job":
            return job
    return spec


def check_when(cond: Any, job: str, meta: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
    """
    Evaluate a step's `when` condition and return True if the step should run.

    Supported forms:
      - None: always run
      - callable: cond(job, meta, ctx) -> truthy
      - string/arg spec: resolved via resolve_arg() then cast to bool
      - literal: bool(literal)

    Example:
        if check_when(step.get("when"), job, meta, ctx):
            ...
    """
    if cond is None:
        return True
    if callable(cond):
        return bool(cond(job, meta, ctx))
    return bool(resolve_arg(cond, job, meta, ctx))


def execute_loader_job(meta: dict) -> bool:
    constants = meta["Constants"]
    action = meta["Action"]
    command = [
        sys.executable,
        "DebianLoader.py",
        "--constants",
        constants,
        "--action",
        action,
        "--yes",
    ]
    try:
        subprocess.run(command, check=True)
        return True
    except (subprocess.CalledProcessError, OSError):
        return False

def unattended_available(loader: str) -> bool:
    """
    Return True if the unattended loader exists.
    """
    return os.path.isfile(loader)