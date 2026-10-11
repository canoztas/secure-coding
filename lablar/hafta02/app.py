"""Interactive lesson 2 lab. Run: python -X utf8 lablar/hafta02/app.py"""

from __future__ import annotations

import argparse
import hashlib
import inspect
import tempfile
import uuid
from pathlib import Path
from urllib.parse import urlsplit

from flask import Flask, jsonify, request
from werkzeug.exceptions import HTTPException

import scenarios
import process_scenarios
import structured_scenarios
from catalog import SCENARIOS


ROOT = Path(__file__).resolve().parent
SOURCE_FILES = {name: ROOT / name for name in (
    "app.py", "scenarios.py", "process_scenarios.py", "structured_scenarios.py", "catalog.py"
)}
HANDLERS = {
    "sql": (scenarios.sql_vulnerable, scenarios.sql_safe),
    "command": (process_scenarios.command_vulnerable, process_scenarios.command_safe),
    "argument": (process_scenarios.argument_vulnerable, process_scenarios.argument_safe),
    "path": (scenarios.path_vulnerable, scenarios.path_safe),
    "ssti": (scenarios.ssti_vulnerable, scenarios.ssti_safe),
    "xml": (structured_scenarios.xml_vulnerable, structured_scenarios.xml_safe),
    "nosql": (structured_scenarios.nosql_vulnerable, structured_scenarios.nosql_safe),
}


def source_block(function) -> dict:
    lines, number = inspect.getsourcelines(function)
    focus = [i for i, line in enumerate(lines, 1) if any(token in line for token in (
        "query =", "parameters =", "db.execute(", "target =", "is_relative_to(download_root)",
        "template =", "from_string(", "command =", "argv =", "args =", "subprocess.run(",
        "XMLParser(", "fromstring(", "doctype", "isinstance(", "filter =", "match_products("
    ))]
    return {"file": Path(inspect.getsourcefile(function)).name, "line": number,
            "source": "".join(lines).rstrip(), "focus_lines": focus}


def create_app() -> Flask:
    app = Flask(__name__, static_folder=str(ROOT / "static"), static_url_path="/static")
    app.config["MAX_CONTENT_LENGTH"] = 32768
    app.json.ensure_ascii = False
    app.json.sort_keys = False

    @app.before_request
    def local_requests_only():
        if request.remote_addr not in ("127.0.0.1", "::1"):
            return jsonify(error="This lab only accepts requests from localhost."), 403
        if request.host.split(":", 1)[0] not in ("127.0.0.1", "localhost"):
            return jsonify(error="Unexpected Host header."), 403
        origin = request.headers.get("Origin")
        if origin:
            try:
                valid_origin = urlsplit(origin).netloc == request.host
            except ValueError:
                valid_origin = False
            if not valid_origin:
                return jsonify(error="Send the request from this application's own page."), 403

    @app.after_request
    def headers(response):
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Content-Security-Policy"] = (
            "default-src 'self'; script-src 'self'; style-src 'self'; "
            "img-src 'self' data:; connect-src 'self'; frame-ancestors 'none'; base-uri 'none'"
        )
        return response

    @app.get("/")
    def index():
        return app.send_static_file("index.html")

    @app.get("/api/scenarios")
    def list_scenarios():
        entries = []
        for specification in SCENARIOS:
            entry = dict(specification)
            vulnerable, safe = HANDLERS[entry["id"]]
            entry["code"] = {"vulnerable": source_block(vulnerable), "safe": source_block(safe)}
            entry["route_code"] = source_block(run_scenario)
            entries.append(entry)
        return jsonify(scenarios=entries)

    @app.get("/api/source/<name>")
    def read_source(name: str):
        if name not in SOURCE_FILES:
            return jsonify(error="Source file not found."), 404
        return app.response_class(SOURCE_FILES[name].read_text(encoding="utf-8"), mimetype="text/plain")

    @app.post("/api/run/<scenario>/<variant>")
    def run_scenario(scenario: str, variant: str):
        if scenario not in HANDLERS or variant not in ("vulnerable", "safe"):
            return jsonify(error="Scenario or version not found."), 404
        payload = request.get_json()
        if not isinstance(payload, dict) or not isinstance(payload.get("input"), str):
            return jsonify(error="The input field in the JSON body must be a string."), 400
        value = payload["input"]
        try:
            value.encode("utf-8")
        except UnicodeError:
            return jsonify(error="Input must be valid Unicode text."), 400
        if len(value) > 4096 or "\x00" in value:
            return jsonify(error="Input must be at most 4096 characters and must not contain NUL."), 400
        handler = HANDLERS[scenario][variant == "safe"]
        with tempfile.TemporaryDirectory(prefix="secure-coding-web-") as directory:
            context = {"root": Path(directory).resolve()}
            try:
                result = handler(value, context)
            except ValueError as error:
                result = {"status": 400, "output": str(error), "trace": [],
                          "summary": "This input is outside the scenario's supported lab scope."}
        result.update(scenario=scenario, variant=variant, request_id=uuid.uuid4().hex[:12],
                      source_sha256=hashlib.sha256(inspect.getsource(handler).encode()).hexdigest())
        result.setdefault("artifacts", [])
        return jsonify(result), result["status"]

    @app.errorhandler(HTTPException)
    def http_error(error):
        return jsonify(error=error.description), error.code

    @app.errorhandler(Exception)
    def unexpected_error(error):
        app.logger.exception("Lab request failed")
        return jsonify(error="The request could not be completed. See the server log for details."), 500

    return app


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=5023)
    args = parser.parse_args()
    print(f"Week 2 lab: http://127.0.0.1:{args.port}", flush=True)
    create_app().run(host="127.0.0.1", port=args.port, debug=False, threaded=True)


if __name__ == "__main__":
    main()
