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
from typing import Any, Dict, List, Optional, Callable

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

# ---------------------------------------------------------------------
# PIPELINE
# ---------------------------------------------------------------------

def run_pipeline(active_jobs: Dict[str, Dict[str, Any]],
                 pipeline: Dict[Any, Dict[str, Any]],
                 *, label: str, success_key: str,
                 log: Callable[[str], None]) -> None:
    """Run a pipeline over active jobs and report successful jobs."""
    jobs = active_jobs or {"__setup__": {}}
    success = 0
    total = len(jobs)
    for job, meta in jobs.items():
        ctx: Dict[str, Any] = {}
        failed = False
        for key, step in pipeline.items():
            fn = key if callable(key) else step.get("fn")
            if not callable(fn):
                raise ValueError(f"Invalid pipeline step: {key}")
            fn_name = fn.__name__
            if not check_when(step.get("when"), job, meta, ctx):
                log(f"[SKIPPED] {job}: {fn_name}")
                continue
            try:
                args = [resolve_arg(a, job, meta, ctx) for a in step.get("args", [])]
                result = fn(*args)
                rkey = step.get("result")
                if rkey is not None:
                    ctx[rkey] = result
                    if not result and rkey != "_":
                        failed = True
                        log(f"[FAIL] {job}: {fn_name}")
            except Exception as e:
                failed = True
                ctx.setdefault("errors", []).append({
                    "step": fn_name,
                    "error": str(e)
                })
                log(f"[ERROR] {job}: {fn_name} failed → {e!r}")
        if not failed and bool(ctx.get(success_key)):
            success += 1
        log("")
    log(f"{label}: {success}/{total} succeeded")



# ---------------------------------------------------------------------
# ARGS
# ---------------------------------------------------------------------

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
    Resolve pipeline arguments.

    meta            -> Entire metadata dictionary
    ?Key            -> Optional metadata value (None if missing)
    ctx key         -> Previous pipeline result
    meta.Key        -> Metadata value
    meta.Key.field  -> Nested metadata value
    job             -> Job name
    otherwise       -> Original value
    """
    if callable(spec):
        return spec(job, meta, ctx)
    if isinstance(spec, str):
        if spec == "meta":
            return meta
        if spec.startswith("?"):
            return meta.get(spec[1:])
        if spec in ctx:
            return ctx[spec]
        if spec.startswith("meta."):
            value = meta
            for key in spec[5:].split("."):
                if not isinstance(value, dict) or key not in value:
                    return None
                value = value[key]
            return value
        if spec in meta:
            return meta[spec]
        if spec == "job":
            return job
    return spec


def check_when(cond: Any, job: str, meta: Dict[str, Any], ctx: Dict[str, Any]) -> bool:
    """Evaluate when conditions using lists for AND and strings for OR."""
    if cond is None:
        return True
    if callable(cond):
        return bool(cond(job, meta, ctx))
    if isinstance(cond, list):
        return all(check_when(part, job, meta, ctx) for part in cond)
    if isinstance(cond, str):
        if " or " in cond:
            return any(check_when(part, job, meta, ctx) for part in cond.split(" or "))
        valid = cond == "job" or cond in ctx or cond in meta or cond.startswith("meta.")
        result = valid and bool(resolve_arg(cond, job, meta, ctx))
        if result:
            print(f"[OK] Condition met: {cond}")
        else:
            print(f"[SKIP] Condition not met: {cond}")
        return result
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
