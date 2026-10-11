"""Small, observable lesson examples; every request gets fresh fictional data."""

from __future__ import annotations

import math
import re
import sqlite3
from pathlib import Path

from jinja2.sandbox import SandboxedEnvironment


USERS = [(1, "alice", "alice@example.test"), (2, "bob", "bob@example.test")]
NOTE = "Lesson note: validate untrusted input."
SECRET = "DEMO_ONLY=classroom-example"
SSTI_SCOPE = (
    "Jinja actually runs. This lab accepts names/text and expressions such as {{ 7*7 }} "
    "using +, - or * with numbers up to two digits. Object access and loops are disabled."
)


def make_database() -> sqlite3.Connection:
    db = sqlite3.connect(":memory:")
    db.setlimit(sqlite3.SQLITE_LIMIT_LENGTH, 1_000_000)
    db.setlimit(sqlite3.SQLITE_LIMIT_SQL_LENGTH, 16_384)
    db.row_factory = sqlite3.Row
    db.execute("CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT, email TEXT)")
    db.executemany("INSERT INTO users VALUES (?, ?, ?)", USERS)
    # Bound computation for freely editable teaching queries.
    ticks = 0

    def budget() -> int:
        nonlocal ticks
        ticks += 1
        return int(ticks > 100)

    db.set_progress_handler(budget, 1000)
    return db


def json_row(row: sqlite3.Row) -> dict:
    # Custom SQL may return BLOB or non-finite numbers; JSON has neither type.
    result = {}
    for key, value in dict(row).items():
        if isinstance(value, bytes):
            value = {"sqlite_type": "BLOB", "hex": value.hex()}
        elif isinstance(value, float) and not math.isfinite(value):
            value = {"sqlite_type": "REAL", "value": str(value)}
        result[key] = value
    return result


def sql_vulnerable(value: str, context: dict) -> dict:
    uid = value
    query = "SELECT name, email FROM users WHERE id = " + uid
    trace = [{"label": "uid · str", "value": uid},
             {"label": "SQL sent to SQLite", "value": query},
             {"label": "Separate parameters", "value": []}]
    db = make_database()
    try:
        rows = [json_row(row) for row in db.execute(query).fetchall()]
    except sqlite3.Error as error:
        return {"status": 400, "output": str(error), "trace": trace,
                "summary": "SQLite could not complete the query. This is the actual database error."}
    finally:
        db.close()
    trace.append({"label": "fetchall() · row count", "value": len(rows)})
    return {"status": 200, "output": rows, "trace": trace,
            "summary": f"SQLite selected {len(rows)} row(s). The input was interpreted as part of the SQL statement."}


def sql_safe(value: str, context: dict) -> dict:
    uid = value
    query = "SELECT name, email FROM users WHERE id = ?"
    parameters = (uid,)
    db = make_database()
    try:
        rows = [json_row(row) for row in db.execute(query, parameters).fetchall()]
    finally:
        db.close()
    return {"status": 200, "output": rows,
            "trace": [{"label": "uid · str", "value": uid},
                      {"label": "Fixed SQL statement", "value": query},
                      {"label": "Separate parameter list", "value": list(parameters)},
                      {"label": "fetchall() · row count", "value": len(rows)}],
            "summary": f"{len(rows)} row(s) returned. The input is treated as a single parameter value, not a query condition."}


def prepare_files(root: Path) -> Path:
    (root / "data").mkdir(exist_ok=True)
    (root / "private").mkdir(exist_ok=True)
    (root / "data/notes.txt").write_text(NOTE, encoding="utf-8")
    (root / "private/demo-secret.txt").write_text(SECRET, encoding="utf-8")
    return root / "data"


def path_trace(root: Path, filename: str, target: Path) -> list:
    joined = root / "data" / filename
    logical_joined = "/demo/" + joined.relative_to(root).as_posix() if joined.is_relative_to(root) else joined.as_posix()
    logical = "/demo/" + target.relative_to(root).as_posix() if target.is_relative_to(root) else "Outside the lab"
    return [{"label": "file · str", "value": filename},
            {"label": "Joined path", "value": logical_joined},
            {"label": "After resolve()", "value": logical},
            {"label": "Inside the data directory?", "value": target.is_relative_to(root / "data")}]


def path_vulnerable(value: str, context: dict) -> dict:
    root = context["root"]
    download_root = prepare_files(root)
    filename = value
    target = (download_root / filename).resolve()
    trace = path_trace(root, filename, target)
    # Lab containment only: the fictional private/ folder is still exposed.
    if not target.is_relative_to(root):
        return {"status": 403, "output": "Access outside the lab is blocked.", "trace": trace,
                "summary": "The lab boundary blocked the request. This is separate from the application's data-directory check."}
    if not target.is_file():
        return {"status": 404, "output": "File not found.", "trace": trace,
                "summary": "There is no sample file at the resolved path."}
    content = target.read_text(encoding="utf-8")
    inside = target.is_relative_to(download_root)
    return {"status": 200, "output": content, "trace": trace,
            "summary": "The lesson note was read." if inside else "The fictional private file outside the data directory was read."}


def path_safe(value: str, context: dict) -> dict:
    root = context["root"]
    download_root = prepare_files(root)
    filename = value
    target = (download_root / filename).resolve()
    trace = path_trace(root, filename, target)
    if not target.is_relative_to(download_root):
        return {"status": 403, "output": "Forbidden", "trace": trace,
                "summary": "The resolved path is outside the data directory. The request was rejected before reading the file."}
    if not target.is_file():
        return {"status": 404, "output": "File not found.", "trace": trace,
                "summary": "This file does not exist in the allowed directory."}
    content = target.read_text(encoding="utf-8")
    return {"status": 200, "output": content, "trace": trace,
            "summary": "The directory boundary check passed. The normal lesson note was read."}


def check_template_input(value: str) -> None:
    # Permit small arithmetic expressions, not arbitrary template programs.
    stripped = re.sub(r"\{\{\s*\d{1,2}\s*[+*\-]\s*\d{1,2}\s*\}\}", "", value)
    if len(value) > 300 or any(character in stripped for character in "{}"):
        raise ValueError(SSTI_SCOPE)


def ssti_vulnerable(value: str, context: dict) -> dict:
    check_template_input(value)
    name = value
    template = "Hello " + name
    engine = SandboxedEnvironment(autoescape=True)
    rendered = engine.from_string(template).render()
    return {"status": 200, "output": rendered,
            "trace": [{"label": "name · str", "value": name},
                      {"label": "Template compiled by Jinja", "value": template},
                      {"label": "Separate data", "value": {}}],
            "summary": "Jinja compiled and rendered this text as a template. In this version, the input becomes part of the template source."}


def ssti_safe(value: str, context: dict) -> dict:
    check_template_input(value)
    name = value
    template = "Hello {{ name }}"
    engine = SandboxedEnvironment(autoescape=True)
    rendered = engine.from_string(template).render(name=name)
    return {"status": 200, "output": rendered,
            "trace": [{"label": "name · str", "value": name},
                      {"label": "Fixed Jinja template", "value": template},
                      {"label": "Separate data", "value": {"name": name}}],
            "summary": "The input was inserted as the name value. Any {{ … }} inside it was not evaluated as template code."}
