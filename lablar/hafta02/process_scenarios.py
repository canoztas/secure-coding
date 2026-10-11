"""Run bounded, harmless process demonstrations in request-local directories."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path


COMMAND_SCOPE = (
    "Real POSIX shell and direct argv execution; Git for Windows provides the tools "
    "on Windows. Only alice, bob and alice; echo DEMO are accepted."
)
ARGUMENT_SCOPE = (
    "Each call runs real git log in a new temporary Git repository. "
    "Only notes.txt and --output=demo.txt are accepted; no network access is used."
)
_COMMAND_INPUTS = frozenset(("alice", "bob", "alice; echo DEMO"))
_ARGUMENT_INPUTS = frozenset(("notes.txt", "--output=demo.txt"))
_TIMEOUT = 10
_OUTPUT_LIMIT = 4096


def _rejected(allowed: frozenset[str]) -> dict:
    return {
        "status": 400,
        "output": "",
        "trace": [{"label": "Lab input allowlist", "value": ", ".join(sorted(allowed))}],
        "summary": "This local lab accepts only the fixed inputs shown above.",
        "artifacts": [],
    }


def _unavailable(error: Exception) -> dict:
    return {
        "status": 503,
        "output": "",
        "trace": [{"label": "Execution error", "value": str(error)[:_OUTPUT_LIMIT]}],
        "summary": "A required process tool is unavailable or the call did not finish within its time limit.",
        "artifacts": [],
    }


def _posix_tools() -> tuple[str, str]:
    if os.name == "nt":
        git = shutil.which("git")
        if git:
            # Supports Git's cmd/, bin/ and mingw64/bin/ PATH layouts.
            for directory in Path(git).resolve().parents:
                echo = directory / "usr" / "bin" / "echo.exe"
                for shell in (directory / "bin" / "sh.exe", directory / "usr" / "bin" / "sh.exe"):
                    if shell.is_file() and echo.is_file():
                        return str(shell), str(echo)
        raise FileNotFoundError("Git for Windows sh.exe and echo.exe were not found; Git must be on PATH.")
    shell = shutil.which("sh")
    echo = shutil.which("echo")
    if not shell or not echo:
        raise FileNotFoundError("The POSIX sh and echo programs were not found on PATH.")
    return shell, echo


def _process_trace(argv: list[str], result: subprocess.CompletedProcess[str]) -> list[dict]:
    return [
        {"label": "Actual subprocess argv", "value": json.dumps(argv, ensure_ascii=False)},
        {"label": "subprocess shell", "value": "False"},
        {"label": "returncode", "value": str(result.returncode)},
        {"label": "stdout", "value": result.stdout[:_OUTPUT_LIMIT]},
        {"label": "stderr", "value": result.stderr[:_OUTPUT_LIMIT]},
    ]


def _prepare_git(context: dict) -> tuple[list[str], dict[str, str], Path]:
    git = shutil.which("git")
    if not git:
        raise FileNotFoundError("Git was not found on PATH.")
    # Each variant gets its own repository, even within the same HTTP request.
    repo = Path(tempfile.mkdtemp(prefix="git_", dir=Path(context["root"]).resolve()))
    hooks = repo / "empty-hooks"
    template = repo / "empty-template"
    hooks.mkdir()
    template.mkdir()
    # Prevent inherited Git overrides, user configuration, hooks and signing.
    env = {key: value for key, value in os.environ.items() if not key.upper().startswith("GIT_")}
    env.update({
        "GIT_CONFIG_NOSYSTEM": "1",
        "GIT_CONFIG_SYSTEM": os.devnull,
        "GIT_CONFIG_GLOBAL": os.devnull,
        "GIT_CONFIG_COUNT": "0",
        "GIT_TERMINAL_PROMPT": "0",
        "GIT_ATTR_NOSYSTEM": "1",
        "GIT_PAGER": "cat",
        "PAGER": "cat",
        "LC_ALL": "C",
        "GIT_AUTHOR_NAME": "Lesson",
        "GIT_AUTHOR_EMAIL": "lesson@example.test",
        "GIT_AUTHOR_DATE": "2000-01-01T00:00:00+0000",
        "GIT_COMMITTER_NAME": "Lesson",
        "GIT_COMMITTER_EMAIL": "lesson@example.test",
        "GIT_COMMITTER_DATE": "2000-01-01T00:00:00+0000",
    })
    prefix = [
        git, "--no-pager", "-c", f"core.hooksPath={hooks}",
        "-c", "core.autocrlf=false", "-c", "commit.gpgSign=false",
        "-c", "tag.gpgSign=false", "-c", "log.showSignature=false",
        "-C", str(repo),
    ]
    subprocess.run(prefix + ["init", "-q", "-b", "main", f"--template={template}"],
                   shell=False, cwd=repo, env=env, capture_output=True,
                   text=True, encoding="utf-8", errors="replace", check=True, timeout=_TIMEOUT)
    (repo / "notes.txt").write_text("lesson\n", encoding="utf-8", newline="\n")
    for args in (["add", "--", "notes.txt"], ["commit", "-qm", "Add notes"]):
        subprocess.run(prefix + args, shell=False, cwd=repo, env=env,
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       check=True, timeout=_TIMEOUT)
    return prefix, env, repo


def command_vulnerable(value: str, context: dict) -> dict:
    if not isinstance(value, str) or value not in _COMMAND_INPUTS:
        return _rejected(_COMMAND_INPUTS)
    try:
        shell, _ = _posix_tools()
        command = "/usr/bin/echo Hello " + value
        argv = [shell, "-c", command]
        # shell=False prevents Python's implicit shell. Explicit sh -c still
        # interprets command text, including the allowed second echo command.
        result = subprocess.run(
            argv, shell=False, cwd=context["root"], capture_output=True,
            text=True, encoding="utf-8", errors="replace", check=True, timeout=_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return _unavailable(error)
    return {
        "status": 200,
        "output": result.stdout[:_OUTPUT_LIMIT],
        "trace": [{"label": "Text interpreted by the shell", "value": command}]
        + _process_trace(argv, result),
        "summary": (
            "An explicit sh -c call enables shell interpretation; the semicolon started a second echo command."
            if value == "alice; echo DEMO" else
            "The POSIX shell interpreted the concatenated command text and printed the greeting."
        ),
        "artifacts": [],
    }


def command_safe(value: str, context: dict) -> dict:
    if not isinstance(value, str) or value not in _COMMAND_INPUTS:
        return _rejected(_COMMAND_INPUTS)
    try:
        _, echo = _posix_tools()
        argv = [echo, "Hello", value]
        result = subprocess.run(
            argv, shell=False, cwd=context["root"], capture_output=True,
            text=True, encoding="utf-8", errors="replace", check=True, timeout=_TIMEOUT,
        )
    except (OSError, subprocess.SubprocessError) as error:
        return _unavailable(error)
    return {
        "status": 200,
        "output": result.stdout[:_OUTPUT_LIMIT],
        "trace": _process_trace(argv, result),
        "summary": "No shell was invoked. The input was passed to echo as a single argv item; the semicolon is plain text.",
        "artifacts": [],
    }


def argument_vulnerable(value: str, context: dict) -> dict:
    if not isinstance(value, str) or value not in _ARGUMENT_INPUTS:
        return _rejected(_ARGUMENT_INPUTS)
    try:
        prefix, env, repo = _prepare_git(context)
        argv = prefix + ["log", "-1", "--format=%s", value]
        result = subprocess.run(
            argv, shell=False, cwd=repo, env=env, capture_output=True,
            text=True, encoding="utf-8", errors="replace", check=True, timeout=_TIMEOUT,
        )
        target = repo / "demo.txt"
        artifacts = ([{"path": "demo.txt", "content": target.read_text(encoding="utf-8")[:_OUTPUT_LIMIT]}]
                     if target.is_file() else [])
    except (OSError, subprocess.SubprocessError) as error:
        return _unavailable(error)
    return {
        "status": 200,
        "output": result.stdout[:_OUTPUT_LIMIT],
        "trace": _process_trace(argv, result)
        + [{"label": "demo.txt created in the temporary repository", "value": "Yes" if artifacts else "No"}],
        "summary": (
            "Despite shell=False, Git interpreted the input as an --output option and wrote to demo.txt."
            if artifacts else
            "No shell was used; Git wrote the latest commit subject for notes.txt to standard output."
        ),
        "artifacts": artifacts,
    }


def argument_safe(value: str, context: dict) -> dict:
    if not isinstance(value, str) or value not in _ARGUMENT_INPUTS:
        return _rejected(_ARGUMENT_INPUTS)
    try:
        prefix, env, repo = _prepare_git(context)
        argv = prefix + ["log", "-1", "--format=%s", "--", value]
        result = subprocess.run(
            argv, shell=False, cwd=repo, env=env, capture_output=True,
            text=True, encoding="utf-8", errors="replace", check=True, timeout=_TIMEOUT,
        )
        target = repo / "demo.txt"
        artifacts = ([{"path": "demo.txt", "content": target.read_text(encoding="utf-8")[:_OUTPUT_LIMIT]}]
                     if target.is_file() else [])
    except (OSError, subprocess.SubprocessError) as error:
        return _unavailable(error)
    return {
        "status": 200,
        "output": result.stdout[:_OUTPUT_LIMIT],
        "trace": _process_trace(argv, result)
        + [{"label": "demo.txt created in the temporary repository", "value": "Yes" if artifacts else "No"}],
        "summary": (
            "No shell was used. -- ended option parsing; --output=demo.txt was treated as a file path and matched nothing."
            if value == "--output=demo.txt" else
            "No shell was used. After --, notes.txt was treated as a file path and its commit subject was printed."
        ),
        "artifacts": artifacts,
    }
