import os
import subprocess
import sys
import importlib.util
from pathlib import Path

from modules.display_utils import print_dict_table


def _supports_color() -> bool:
    """Return True if we should emit ANSI colors."""
    return sys.stdout.isatty() and os.getenv("NO_COLOR") is None


def _c(text: str, code: str) -> str:
    """Wrap text with an ANSI color code if supported."""
    if not _supports_color():
        return text
    return f"\033[{code}m{text}\033[0m"


def tag_test() -> str:
    """Return a TEST tag."""
    return _c("[TEST] ", "36")  # cyan


def tag_ok() -> str:
    """Return an OK tag."""
    return _c("[OK]   ", "32")  # green


def tag_fail() -> str:
    """Return a FAIL tag."""
    return _c("[FAIL] ", "31")  # red


def tag_skip() -> str:
    """Return a SKIP tag."""
    return _c("[SKIP] ", "33")  # yellow


def tag_error() -> str:
    """Return an ERROR tag."""
    return _c("[ERROR]", "31")  # red


def ensure_executable(path: Path) -> bool:
    """Ensure a file is executable; return True if successful."""
    try:
        mode = path.stat().st_mode
        if mode & 0o111:
            return True
        path.chmod(mode | 0o111)
        return True
    except Exception as e:
        print(f"{tag_error()} Could not make executable: {path} ({e})")
        return False


def run_tests(tests: list[dict]) -> bool:
    """Run a list of test definitions."""
    all_ok = True
    for test in tests or []:
        label = test.get("label", "unnamed-test")
        raw_path = test.get("path", "")
        port = test.get("port")
        path = Path(os.path.expandvars(raw_path)).expanduser().resolve()
        print()
        print(f"{tag_test()} {label} → {path}")
        if not path.exists():
            print(f"{tag_fail()} Test path does not exist: {path}")
            all_ok = False
            continue
        if path.is_dir():
            command = ["pytest", "."]
            cwd = path
        else:
            if not ensure_executable(path):
                print(
                    f"{tag_fail()} Test '{label}' is not executable "
                    "and could not be fixed."
                )
                all_ok = False
                continue
            command = [str(path)]
            cwd = path.parent
            if port is not None:
                command.extend(["--port", str(port)])
        res = subprocess.run(command, cwd=cwd, check=False)
        if res.returncode != 0:
            print(f"{tag_fail()} {label}")
            all_ok = False
        else:
            print(f"{tag_ok()}  {label}")
    print()
    return all_ok

# ----------------------------------------------------------------------------
# PIPELINE TESTS
# ----------------------------------------------------------------------------


def load_test_pipelines(job: str, tests: list[dict]) -> dict:
    """Load the selected pipelines from a constants file."""
    try:
        path = Path(job).resolve()
        if not path.is_file():
            print(f"{tag_error()} Constants file not found: {path}")
            return {}
        spec = importlib.util.spec_from_file_location(path.stem, path)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        available = module.PIPELINE_STATES
        pipelines = {}
        for test in tests or []:
            name = test.get("pipeline")
            if name not in available:
                print(f"{tag_fail()} Pipeline '{name}' not found")
                return {}
            pipelines[name] = available[name]
        print(f"{tag_ok()} Loaded {len(pipelines)} pipelines from {job}")
        return pipelines
    except Exception as e:
        print(f"{tag_error()} Could not load {job}: {e}")
        return {}


def check_pipeline_success_keys(pipelines: dict) -> bool:
    """Validate pipeline functions, dependencies, and success keys."""
    all_ok = True
    summary = []
    for name, state in pipelines.items():
        rows = []
        results = set()
        pipeline_ok = True
        for action, config in state["pipeline"].items():
            fn = config.get("fn", action)
            action_name = getattr(fn, "__name__", str(fn))
            condition = config.get("when")
            result = config.get("result")
            function_ok = callable(fn)
            conditions = condition if isinstance(condition, list) else [condition]
            dependency_ok = all(
                not part or any(
                    option.strip() in results or option.strip().startswith("meta.")
                    for option in part.split(" or ")
                )
                for part in conditions
            )
            status = "PASS" if function_ok and dependency_ok else "FAIL"
            if status == "FAIL":
                pipeline_ok = False
            rows.append({
                "Function": action_name,
                "When": str(condition) if condition else "-",
                "Result": result or "-",
                "Status": status,
            })
            if result and result != "_":
                results.add(result)
        success_key = state.get("success_key")
        success_ok = success_key in results
        if not success_ok:
            pipeline_ok = False
        rows.append({
            "Function": "SUCCESS KEY",
            "When": "-",
            "Result": success_key or "-",
            "Status": "PASS" if success_ok else "FAIL",
        })
        print_dict_table(
            rows,
            ["Function", "When", "Result", "Status"],
            f"{name} Pipeline Validation",
        )
        summary.append({
            "Pipeline": name,
            "Status": "PASS" if pipeline_ok else "FAIL",
        })
        if not pipeline_ok:
            all_ok = False
    print_dict_table(
        summary,
        ["Pipeline", "Status"],
        "Pipeline Validation Summary",
    )
    passed = sum(row["Status"] == "PASS" for row in summary)
    print(f"[SUMMARY] Passed: {passed}, Failed: {len(summary) - passed}")
    return all_ok and bool(summary)

