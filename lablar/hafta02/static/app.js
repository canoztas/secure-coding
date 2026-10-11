"use strict";

(() => {
  const byId = (id) => document.getElementById(id);
  const variantNames = { vulnerable: "Vulnerable", safe: "Fixed" };
  const shortNames = {
    sql: ["SQL Injection", "SQL query"],
    command: ["OS Command Injection", "Shell command"],
    argument: ["Argument Injection", "Command argument"],
    path: ["Path Traversal", "File path"],
    ssti: ["Template Injection", "Server template · SSTI"],
    xml: ["XML External Entity", "XML parser · XXE"],
    nosql: ["NoSQL Injection", "Query operator"],
  };
  const state = { scenarios: [], scenario: null, variant: "vulnerable", busy: false, generation: 0, resultInput: null, toastTimer: null };

  function text(value) {
    return typeof value === "string" ? value : JSON.stringify(value, null, 2) ?? "";
  }

  function el(tag, className, content) {
    const node = document.createElement(tag);
    if (className) node.className = className;
    if (content !== undefined) node.textContent = text(content);
    return node;
  }

  function toast(message) {
    clearTimeout(state.toastTimer);
    byId("toast").textContent = message;
    byId("toast").hidden = false;
    state.toastTimer = setTimeout(() => { byId("toast").hidden = true; }, 2500);
  }

  async function copy(content) {
    try {
      if (navigator.clipboard && window.isSecureContext) {
        await navigator.clipboard.writeText(content);
      } else {
        const field = el("textarea");
        field.value = content;
        field.style.position = "fixed";
        field.style.left = "-9999px";
        document.body.append(field);
        field.select();
        const copied = document.execCommand("copy");
        field.remove();
        if (!copied) throw new Error("copy");
      }
      toast("Copied to clipboard.");
    } catch (_) {
      toast("Could not copy. You can select and copy the text manually.");
    }
  }

  function requestText(variant = state.variant, input = byId("scenario-input").value, scenario = state.scenario) {
    if (!scenario) return "";
    return `POST /api/run/${encodeURIComponent(scenario.id)}/${variant} HTTP/1.1\nHost: ${location.host}\nContent-Type: application/json\n\n${JSON.stringify({ input })}`;
  }

  function updateRequest() {
    byId("request-preview").textContent = requestText();
    const existingNotice = byId("results").querySelector(".input-changed");
    if (existingNotice) existingNotice.remove();
    if (state.resultInput !== null && state.resultInput !== byId("scenario-input").value) {
      byId("results").prepend(el("p", "input-changed", "The input has changed. The result below is from the previous request; run the new input."));
    }
  }

  function renderSource(container, source) {
    container.replaceChildren();
    if (!source || typeof source.source !== "string") {
      container.textContent = "Source code not found.";
      return;
    }
    const focused = new Set(source.focus_lines || []);
    const start = Number(source.line) || 1;
    const lines = source.source.replace(/\r\n/g, "\n").split("\n");
    // A final newline terminates the last source line; it is not another numbered line.
    if (lines[lines.length - 1] === "") lines.pop();
    lines.forEach((line, index) => {
      const row = el("span", `code-line${focused.has(index + 1) ? " focus-line" : ""}`);
      const number = el("span", "line-number", start + index);
      number.setAttribute("aria-hidden", "true");
      row.append(number, el("span", "line-content", line));
      container.append(row);
    });
  }

  function resetResults() {
    state.resultInput = null;
    byId("result-state").textContent = "NOT RUN YET";
    const empty = el("div", "empty-result");
    const symbol = el("span", "", "↳");
    symbol.setAttribute("aria-hidden", "true");
    const message = el("p", "", "Send your first request.");
    message.append(el("small", "", "The HTTP status, output, and execution trace will appear here."));
    empty.append(symbol, message);
    byId("results").replaceChildren(empty);
  }

  function setVariant(variant, clear = false) {
    state.variant = variant;
    document.querySelectorAll("[data-variant]").forEach((button) => {
      button.setAttribute("aria-pressed", String(button.dataset.variant === variant));
    });
    const code = state.scenario.code?.[variant];
    byId("source-variant").textContent = variantNames[variant];
    byId("source-variant").classList.toggle("safe", variant === "safe");
    document.querySelector(".source-panel").classList.toggle("safe", variant === "safe");
    byId("source-file").textContent = code ? `${code.file} : ${code.line}` : "";
    byId("source-full").href = code ? `/api/source/${encodeURIComponent(code.file)}` : "#";
    byId("source-full").hidden = !code;
    renderSource(byId("source-code"), code);
    if (clear) resetResults();
    updateRequest();
  }

  function selectScenario(id) {
    const scenario = state.scenarios.find((item) => item.id === id);
    if (!scenario) return;
    state.generation += 1;
    state.scenario = scenario;
    setBusy(false);
    const index = state.scenarios.indexOf(scenario);
    document.querySelectorAll(".scenario-link").forEach((button) => {
      if (button.dataset.scenario === id) button.setAttribute("aria-current", "page");
      else button.removeAttribute("aria-current");
    });
    const fields = {
      "scenario-index": `EXPERIMENT ${String(index + 1).padStart(2, "0")}`,
      "scenario-engine": scenario.engine,
      "scenario-title": scenario.title,
      "scenario-subtitle": scenario.subtitle,
      "scenario-summary": scenario.summary,
      "input-label": scenario.field,
      "scenario-explanation": scenario.explanation,
      "scenario-fix": scenario.fix,
      "scenario-scope": scenario.scope,
      "scenario-fixtures": scenario.fixtures,
      "normal-expected": scenario.normal_expected,
      "vulnerable-expected": scenario.vulnerable_expected,
      "safe-expected": scenario.safe_expected,
    };
    Object.entries(fields).forEach(([elementId, value]) => { byId(elementId).textContent = text(value ?? ""); });
    byId("scenario-input").value = typeof scenario.normal === "string" ? scenario.normal : text(scenario.normal);
    byId("scenario-steps").replaceChildren(...(scenario.steps || []).map((step) => el("li", "", step)));
    byId("input-help").textContent = scenario.constrained
      ? "This experiment has input or execution limits; see Experiment scope for details."
      : "Preset buttons only fill in the input. Click Run to send the request.";
    byId("input-help").classList.toggle("constrained", Boolean(scenario.constrained));
    byId("route-file").textContent = scenario.route_code ? `${scenario.route_code.file} : ${scenario.route_code.line}` : "";
    document.querySelector(".route-details").hidden = !scenario.route_code;
    document.querySelector(".route-details").open = false;
    renderSource(byId("route-code"), scenario.route_code);
    document.querySelectorAll(".teaching-details").forEach((details) => { details.open = false; });
    setVariant(state.variant, true);
    byId("lab-content").hidden = false;
    document.title = `${scenario.title} · Secure Coding Lab`;
    const url = new URL(location.href);
    url.hash = id;
    history.replaceState(null, "", url);
  }

  function setBusy(busy) {
    state.busy = busy;
    byId("result-panel").setAttribute("aria-busy", String(busy));
    ["run-button", "compare-button", "normal-input", "exploit-input"].forEach((id) => { byId(id).disabled = busy; });
    document.querySelectorAll("[data-variant]").forEach((button) => { button.disabled = busy; });
    byId("scenario-input").readOnly = busy;
  }

  function statusClass(status) {
    if (status >= 200 && status < 300) return "success";
    if (status >= 400 && status < 500) return "client-error";
    if (status >= 500) return "server-error";
    return "";
  }

  function addDetails(parent, heading, content, open = false) {
    const details = el("details", "result-details");
    details.open = open;
    details.append(el("summary", "", heading), content);
    parent.append(details);
  }

  function renderResult(result) {
    const { variant, status, body, input, request, error } = result;
    const card = el("article", "result-card");
    const heading = el("div", "result-card-header");
    heading.append(el("h3", "", `${variantNames[variant]} version`));
    if (status) heading.append(el("span", `http-status ${statusClass(status)}`, `HTTP ${status}`));
    else heading.append(el("span", "http-status server-error", "CONNECTION ERROR"));
    card.append(heading);
    if (error) card.append(el("p", "result-summary", error));
    if (body) {
      if (body.summary || body.error) card.append(el("p", "result-summary", body.summary || body.error));
      if (Object.prototype.hasOwnProperty.call(body, "output")) {
        card.append(el("span", "output-label", "SCENARIO OUTPUT · output"), el("pre", "result-output", body.output === "" ? "(empty string)" : body.output));
      }
      if (Array.isArray(body.trace) && body.trace.length) {
        const trace = el("dl", "trace-list");
        body.trace.forEach((entry) => {
          const item = el("div", "trace-item");
          item.append(el("dt", "", entry.label), el("dd", "", entry.value));
          trace.append(item);
        });
        addDetails(card, `Execution trace · ${body.trace.length} steps`, trace, true);
      }
      if (Array.isArray(body.artifacts) && body.artifacts.length) {
        const artifacts = el("div", "artifacts");
        body.artifacts.forEach((artifact) => {
          artifacts.append(el("p", "artifact-path", artifact.path), el("pre", "result-output", artifact.content));
        });
        addDetails(card, `Created files / side effects · ${body.artifacts.length}`, artifacts, true);
      }
      const raw = el("pre", "result-output", body);
      addDetails(card, "Raw JSON response", raw);
      const metadata = [];
      if (body.request_id) metadata.push(`Request: ${body.request_id}`);
      if (body.source_sha256) metadata.push(`Source SHA-256: ${body.source_sha256}`);
      if (metadata.length) card.append(el("p", "result-meta", metadata.join("\n")));
    }
    addDetails(card, "HTTP request for this result", el("pre", "result-output", request));
    card.dataset.input = input;
    return card;
  }

  async function sendRequest(scenario, variant, input) {
    const request = requestText(variant, input, scenario);
    try {
      const response = await fetch(`/api/run/${encodeURIComponent(scenario.id)}/${variant}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ input }),
      });
      let body;
      try { body = await response.json(); }
      catch (_) { return { variant, input, request, status: response.status, error: "The server did not return a valid JSON response." }; }
      return { variant, input, request, status: response.status, body };
    } catch (error) {
      return { variant, input, request, error: `Could not send the request. Check that the local server is running. ${error.message}` };
    }
  }

  async function run(compare = false) {
    if (!state.scenario || state.busy) return;
    const scenario = state.scenario;
    const generation = state.generation;
    const input = byId("scenario-input").value;
    const variants = compare ? ["vulnerable", "safe"] : [state.variant];
    setBusy(true);
    state.resultInput = null;
    byId("result-state").textContent = "SENDING REQUEST";
    const pending = el("div", "pending-result");
    const spinner = el("span", "spinner");
    spinner.setAttribute("aria-hidden", "true");
    pending.append(spinner, el("span", "", compare ? "Running the same input in both versions…" : "Waiting for the server response…"));
    byId("results").replaceChildren(pending);
    // Run in order so demonstrations with local side effects remain deterministic.
    const results = [];
    for (const variant of variants) {
      results.push(await sendRequest(scenario, variant, input));
      if (generation !== state.generation) return;
    }
    if (generation !== state.generation) return;
    state.resultInput = input;
    byId("results").replaceChildren(...results.map(renderResult));
    byId("result-state").textContent = compare ? "SAME INPUT · 2 RESPONSES" : "RESPONSE RECEIVED";
    if (results.some((result) => !result.status)) byId("result-state").textContent = "CONNECTION ERROR";
    setBusy(false);
    updateRequest();
  }

  async function load() {
    byId("load-error").hidden = true;
    try {
      const response = await fetch("/api/scenarios", { cache: "no-store" });
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const data = await response.json();
      if (!Array.isArray(data.scenarios) || !data.scenarios.length) throw new Error("The server did not return a list of experiments.");
      state.scenarios = data.scenarios;
      byId("scenario-count").textContent = String(data.scenarios.length).padStart(2, "0");
      byId("scenario-nav").replaceChildren(...data.scenarios.map((scenario, index) => {
        const button = el("button", "scenario-link");
        button.type = "button";
        button.dataset.scenario = scenario.id;
        const names = shortNames[scenario.id] || [scenario.title, scenario.engine];
        const label = el("span", "nav-label");
        label.append(el("span", "nav-title", names[0]), el("span", "nav-subtitle", names[1]));
        button.append(el("span", "nav-index", String(index + 1).padStart(2, "0")), label);
        button.addEventListener("click", () => selectScenario(scenario.id));
        return button;
      }));
      byId("connection").className = "connection connected";
      byId("connection").querySelector("span").textContent = "Local server connected";
      const hashId = location.hash.slice(1);
      selectScenario(state.scenarios.some((item) => item.id === hashId) ? hashId : state.scenarios[0].id);
    } catch (error) {
      byId("connection").className = "connection failed";
      byId("connection").querySelector("span").textContent = "Server unreachable";
      byId("load-error-message").textContent = `Open this page through the lab's local Python server. Start the server, then try again. Details: ${error.message}`;
      byId("load-error").hidden = false;
      byId("lab-content").hidden = true;
      byId("scenario-nav").replaceChildren(el("p", "nav-loading", "Waiting for a server connection."));
    }
  }

  byId("run-form").addEventListener("submit", (event) => { event.preventDefault(); run(); });
  byId("compare-button").addEventListener("click", () => run(true));
  byId("scenario-input").addEventListener("input", updateRequest);
  byId("scenario-input").addEventListener("keydown", (event) => {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") { event.preventDefault(); run(); }
  });
  ["normal", "exploit"].forEach((preset) => {
    byId(`${preset}-input`).addEventListener("click", () => {
      if (!state.scenario || state.busy) return;
      byId("scenario-input").value = text(state.scenario[preset]);
      resetResults();
      updateRequest();
      byId("scenario-input").focus();
    });
  });
  document.querySelectorAll("[data-variant]").forEach((button) => {
    button.addEventListener("click", () => { if (!state.busy) setVariant(button.dataset.variant); });
  });
  byId("copy-request").addEventListener("click", () => copy(requestText()));
  byId("copy-code").addEventListener("click", () => copy(state.scenario?.code?.[state.variant]?.source || ""));
  byId("retry-load").addEventListener("click", load);
  window.addEventListener("hashchange", () => {
    if (state.scenarios.some((item) => item.id === location.hash.slice(1))) selectScenario(location.hash.slice(1));
  });
  load();
})();
