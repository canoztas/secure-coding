# Week 2 — interactive web lab

Edit the input, send a real HTTP request, and inspect the running Python code and its result on the same screen. The app uses an English interface and a black theme.

Start from the repository root:

```powershell
python -m pip install -r lab/hafta02/requirements.txt
python -X utf8 lab/hafta02/app.py
```

Open **http://127.0.0.1:5023**. Use `--port 5024` to change the port. Stop the server with `Ctrl+C` in the terminal. Command and argument examples require Git on PATH; Windows uses the POSIX tools bundled with Git for Windows. No internet connection or separate database service is needed to run the app.

## Classroom walkthrough

1. Select a scenario. Explain its purpose and initial data.
2. Select **Normal input**, then **Run** to send the request.
3. Connect `input` in the HTTP body to the Python function's `value` argument. Follow the highlighted line to its interpreter.
4. Select **Exploit input** to change only the input. Ask students to predict the result before running it.
5. Select **Compare both versions** to send the same input to the Vulnerable and Fixed versions. Compare HTTP status, output, and file side effects.
6. Compare the normal input too, showing that the fix preserves expected behavior.

Preset buttons fill the field without sending a request. Results come from the actual server response. The code panel reads the running function with `inspect.getsourcelines()`. The full-source link also shows setup and helper functions.

## Scenarios

The main lesson uses SQL injection, command injection, and the path traversal lab. Argument injection, SSTI, NoSQL, and XXE are optional examples.

| Scenario | Normal → exploit | Running component | Fix |
|---|---|---|---|
| SQL injection | `1` → `1 OR 1=1` | Real SQLite, two fictional records | `?` + separate parameter |
| Command injection | `alice` → `alice; echo DEMO` | Real POSIX shell and echo | An argv list without a shell |
| Argument injection | `notes.txt` → `--output=demo.txt` | Real temporary Git repository | End options with `--` |
| Path traversal | `notes.txt` → `../private/demo-secret.txt` | Temporary sample files | Keep the resolved path inside the download root |
| SSTI | `alice` → `{{ 7*7 }}` | Real Jinja | A fixed template + separate data |
| XXE | `<note>Hello</note>` → XML with an external entity | Real lxml, temporary `DEMO-DATA` file | Disable entity resolution; reject DTDs |
| NoSQL operator injection | `{"sku":"P100"}` → `{"sku":{"$ne":""}}` | **Python query model; MongoDB does not run** | Validate the string type before querying |

The intentional vulnerabilities are for local teaching. The server binds to `127.0.0.1`. Each request gets fresh databases/files, removed after the request. Command/argument examples accept the documented fixed inputs. SSTI accepts small arithmetic expressions; the XML resolver opens only the sample file. The path example can read the fictional private file outside the download directory, but cannot leave the lab directory. These lab boundaries are separate from the application fixes shown in the code panel.

## HTTP and source files

The endpoint is `POST /api/run/<scenario>/<vulnerable|safe>`. The JSON body's `input` string is passed to the selected Python function. The actual result is returned in `output`, intermediate values in `trace`, and file side effects in `artifacts`. A 400 or 403 result also sets the real HTTP status. NoSQL/XML documents travel as strings inside this outer JSON envelope; the second parsing step is visible in the code. The UI label **Fixed** maps to the `safe` route.

The original `/profile`, `/download`, and `/hello` app used in the slides is preserved in `scripts/hafta02_demo.py`. This is a separate interactive app using the same scenario inputs and fictional records. Its lesson-note text is localized as `Lesson note: validate untrusted input.` The original slide screenshot evidence describes the original app, not this one.

| File | Purpose |
|---|---|
| `app.py` | HTTP, temporary workspace, source-code access |
| `scenarios.py` | SQLite, path traversal, Jinja |
| `process_scenarios.py` | Shell/echo and Git |
| `structured_scenarios.py` | XML parser and NoSQL model |
| `catalog.py` | Explanations, expected behavior, preset inputs |
| `static/` | Browser UI, including the black theme |
| `verify.py` | Actual HTTP and browser verification |
| `evidence/` | Verification record and app screenshots |

Verification also requires Playwright and Microsoft Edge:

```powershell
python -m pip install playwright
python -X utf8 lab/hafta02/verify.py
```

Verification starts and stops its own temporary server without affecting the classroom server. It writes `evidence/checks.json`. It does not commit, push, or publish anything.
