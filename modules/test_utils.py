import os
import subprocess
import sys
from pathlib import Path


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
    for test in tests:
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
