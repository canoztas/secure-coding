"""Exercise actual local HTTP endpoints and browser interactions; save evidence."""

from __future__ import annotations

import hashlib
import inspect
import json
import logging
import platform
import threading
from datetime import datetime, timezone
from importlib.metadata import version
from pathlib import Path

from playwright.sync_api import sync_playwright
from werkzeug.serving import make_server

from app import HANDLERS, create_app
from catalog import SCENARIOS


ROOT = Path(__file__).resolve().parent
EVIDENCE = ROOT / "evidence"
ALICE = [{"name": "alice", "email": "alice@example.test"}]
USERS = ALICE + [{"name": "bob", "email": "bob@example.test"}]
NOTE = "Lesson note: validate untrusted input."
PRODUCTS = [{"sku": "P100", "name": "Notebook"}, {"sku": "P200", "name": "Pen"}]
EXPECTED = {
    "sql": [(200, ALICE), (200, USERS), (200, [])],
    "command": [(200, "Hello alice\n"), (200, "Hello alice\nDEMO\n"), (200, "Hello alice; echo DEMO\n")],
    "argument": [(200, "Add notes\n"), (200, ""), (200, "")],
    "path": [(200, NOTE), (200, "DEMO_ONLY=classroom-example"), (403, "Forbidden")],
    "ssti": [(200, "Hello alice"), (200, "Hello 49"), (200, "Hello {{ 7*7 }}")],
    "xml": [(200, "Hello"), (200, "DEMO-DATA"), (400, "This endpoint does not accept DTDs.")],
    "nosql": [(200, PRODUCTS[:1]), (200, PRODUCTS), (400, {"error": "sku must be a string."})],
}


def check_result(response, scenario, variant, preset):
    body = response.json()
    index = 0 if preset == "normal" else (2 if variant == "safe" else 1)
    status, output = EXPECTED[scenario][index]
    assert response.status == body["status"] == status, (scenario, variant, body)
    assert body["output"] == output, (scenario, variant, body)
    artifacts = [{"path": "demo.txt", "content": "Add notes\n"}] if (scenario, variant, preset) == ("argument", "vulnerable", "exploit") else []
    assert body["artifacts"] == artifacts, (scenario, variant, body)
    function = HANDLERS[scenario][variant == "safe"]
    assert body["source_sha256"] == hashlib.sha256(inspect.getsource(function).encode()).hexdigest()
    assert body["scenario"] == scenario and body["variant"] == variant
    assert body["trace"] and body["request_id"]
    return body


def main():
    EVIDENCE.mkdir(exist_ok=True)
    logging.getLogger("werkzeug").setLevel(logging.ERROR)
    server = make_server("127.0.0.1", 0, create_app(), threaded=True)
    worker = threading.Thread(target=server.serve_forever, daemon=True)
    worker.start()
    base = f"http://127.0.0.1:{server.server_port}"
    records, boundary, browser_checks, screenshots = [], [], [], []
    errors = []
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(channel="msedge", headless=True)
            try:
                context = browser.new_context(base_url=base, viewport={"width": 1600, "height": 1000})
                api = context.request
                listed = api.get("/api/scenarios").json()["scenarios"]
                assert len(listed) == 7
                for spec in listed:
                    for variant in ("vulnerable", "safe"):
                        function = HANDLERS[spec["id"]][variant == "safe"]
                        assert spec["code"][variant]["source"] == inspect.getsource(function).rstrip()
                        full = api.get("/api/source/" + spec["code"][variant]["file"])
                        assert full.status == 200 and spec["code"][variant]["source"] in full.text()
                    for preset in ("normal", "exploit"):
                        for variant in ("vulnerable", "safe"):
                            response = api.post(f"/api/run/{spec['id']}/{variant}", data={"input": spec[preset]})
                            result = check_result(response, spec["id"], variant, preset)
                            records.append({"scenario": spec["id"], "preset": preset, "variant": variant,
                                            "input": spec[preset], "actual": result, "passed": True})

                malformed = [
                    ("sql", "vulnerable", "'", 400),
                    ("path", "vulnerable", "../../outside.txt", 403),
                    ("path", "safe", "missing.txt", 404),
                    ("command", "vulnerable", "alice; whoami", 400),
                    ("argument", "vulnerable", "--output=../outside.txt", 400),
                    ("ssti", "vulnerable", "{{ range(999999999) }}", 400),
                    ("xml", "vulnerable", "<note>", 400),
                    ("xml", "vulnerable", '<!DOCTYPE note [<!ENTITY x SYSTEM "file:///outside.txt">]><note>&x;</note>', 400),
                    ("nosql", "vulnerable", '{"sku":{"$gt":""}}', 400),
                    ("nosql", "safe", "{", 400),
                    ("sql", "safe", "x" * 4097, 400),
                    ("path", "safe", "\x00", 400),
                ]
                for scenario, variant, value, status in malformed:
                    response = api.post(f"/api/run/{scenario}/{variant}", data={"input": value})
                    assert response.status == status, (scenario, value, response.text())
                    boundary.append({"scenario": scenario, "variant": variant, "input": value,
                                     "status": response.status, "passed": True})
                invalid_requests = [
                    ("missing input", {}, {}, 400),
                    ("invalid input type", {"input": 1}, {}, 400),
                    ("cross origin", {"input": "1"}, {"Origin": "https://example.test"}, 403),
                    ("malformed origin", {"input": "1"}, {"Origin": "http://["}, 403),
                    ("invalid Unicode", {"input": "\ud800"}, {}, 400),
                ]
                for label, payload, headers, status in invalid_requests:
                    response = api.post("/api/run/sql/vulnerable", data=json.dumps(payload),
                                        headers={"Content-Type": "application/json", **headers})
                    assert response.status == status, (label, response.text())
                    boundary.append({"case": label, "status": response.status, "passed": True})
                for value in ("0 UNION SELECT x'41', NULL", "0 UNION SELECT 1e999, 2"):
                    response = api.post("/api/run/sql/vulnerable", data={"input": value})
                    assert response.status == 200
                    json.loads(response.text(), parse_constant=lambda value: (_ for _ in ()).throw(ValueError(value)))
                    boundary.append({"case": "SQL value serializes to strict JSON", "input": value,
                                     "status": response.status, "passed": True})

                page = context.new_page()
                page.on("pageerror", lambda error: errors.append(str(error)))
                posts = []
                page.on("request", lambda request: posts.append(request.url) if request.method == "POST" else None)
                page.goto(base, wait_until="networkidle")
                page.wait_for_selector(".scenario-link")
                assert not posts, "Loading the page must not run a scenario."
                page.locator("#exploit-input").click()
                assert not posts, "A preset must only fill the field."
                for spec in SCENARIOS:
                    page.locator(f'[data-scenario="{spec["id"]}"]').click()
                    assert page.locator(".result-card").count() == 0
                    page.locator("#exploit-input").click()
                    assert page.locator("#scenario-input").input_value() == spec["exploit"]
                    before = len(posts)
                    page.locator("#compare-button").click()
                    page.locator("#results .result-card").nth(1).wait_for(state="visible")
                    assert len(posts) == before + 2
                    for i, variant in enumerate(("vulnerable", "safe")):
                        card = page.locator(".result-card").nth(i)
                        status, output = EXPECTED[spec["id"]][i + 1]
                        assert card.locator(".http-status").inner_text() == f"HTTP {status}"
                        visible_output = card.locator(".result-output").first.inner_text()
                        if isinstance(output, (dict, list)):
                            assert json.loads(visible_output) == output
                        elif output:
                            assert visible_output == output
                        else:
                            assert "empty string" in visible_output
                    page.locator('[data-variant="safe"]').click()
                    assert page.locator(".result-card").count() == 2, "Inspecting safe code must retain comparison."
                    assert spec["id"] + "_safe" in page.locator("#source-code").inner_text()
                    assert page.locator("#source-full").get_attribute("href").startswith("/api/source/")
                    if spec["id"] in ("sql", "argument"):
                        page.evaluate("window.scrollTo(0, 0)")
                        target = EVIDENCE / f"{spec['id']}-compare.png"
                        page.screenshot(path=str(target), full_page=True, animations="disabled")
                        screenshots.append(target.name)
                    browser_checks.append({"scenario": spec["id"], "same_input_comparison": True,
                                           "source_switch_keeps_results": True, "passed": True})

                page.locator('[data-scenario="sql"]').click()
                page.locator('[data-variant="vulnerable"]').click()
                page.locator("#scenario-input").fill("2")
                page.locator("#run-button").click()
                page.wait_for_selector(".result-card")
                assert json.loads(page.locator(".result-output").first.inner_text()) == USERS[1:]
                page.locator("#scenario-input").fill("1")
                assert page.locator(".input-changed").count() == 1
                browser_checks.append({"case": "edited input runs; old results visibly marked", "passed": True})
                page.set_viewport_size({"width": 390, "height": 844})
                assert page.evaluate("document.documentElement.scrollWidth <= window.innerWidth")
                page.evaluate("window.scrollTo(0, 0)")
                target = EVIDENCE / "mobile.png"
                page.screenshot(path=str(target), animations="disabled")
                screenshots.append(target.name)
                browser_checks.append({"case": "390px mobile viewport has no horizontal overflow", "passed": True})
                assert not errors, errors
            finally:
                browser.close()
    finally:
        server.shutdown()
        server.server_close()
        worker.join(timeout=5)
    assert not worker.is_alive()
    sources = [*ROOT.glob("*.py"), *ROOT.glob("*.txt"), ROOT / "README.md", *sorted((ROOT / "static").glob("*"))]
    report = {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "environment": {"platform": platform.platform(), "python": platform.python_version(),
                        **{name: version(name) for name in ("Flask", "Jinja2", "lxml", "playwright")}},
        "scope": "Real local HTTP plus browser UI. NoSQL is a Python model; no MongoDB process.",
        "server_shutdown": True, "all_passed": True, "javascript_errors": errors,
        "source_sha256": {str(path.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources},
        "http_cases": records, "boundary_checks": boundary, "browser_checks": browser_checks,
        "screenshots": [{"file": name, "sha256": hashlib.sha256((EVIDENCE / name).read_bytes()).hexdigest()} for name in screenshots],
    }
    (EVIDENCE / "checks.json").write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"PASS: {len(records)} HTTP scenarios, {len(boundary)} boundary checks, {len(browser_checks)} browser checks; 0 JS errors.")
    print(f"Evidence: {EVIDENCE / 'checks.json'}")


if __name__ == "__main__":
    main()
