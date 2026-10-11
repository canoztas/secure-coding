"""Local XML parsing and a deliberately small NoSQL teaching model."""

from __future__ import annotations

import json
from pathlib import Path

from lxml import etree


XML_NORMAL = "<note>Hello</note>"
XML_EXPLOIT = '<!DOCTYPE note [<!ENTITY ext SYSTEM "file:///lab/message.txt">]><note>&ext;</note>'
XML_SCOPE = (
    "This uses the real lxml parser. The lab resolver maps only "
    "file:///lab/message.txt to a temporary DEMO-DATA file created for this request; "
    "all other external file and network addresses are rejected. no_network=True alone "
    "does not prevent local file reads."
)
NOSQL_NORMAL = '{"sku":"P100"}'
NOSQL_EXPLOIT = '{"sku":{"$ne":""}}'
NOSQL_SCOPE = (
    "This is a Python teaching model; it does not run MongoDB. It supports only "
    "string equality and {$ne: string} conditions on the sku field. Other query operators are unsupported."
)
PRODUCTS = (
    {"sku": "P100", "name": "Notebook"},
    {"sku": "P200", "name": "Pen"},
)


def _result(status, output, trace, summary, artifacts=None):
    return {"status": status, "output": output, "trace": trace,
            "summary": summary, "artifacts": artifacts or []}


def _xml_fixture(context):
    fixture = Path(context["root"]) / "lab" / "message.txt"
    fixture.parent.mkdir(parents=True, exist_ok=True)
    fixture.write_text("DEMO-DATA", encoding="utf-8")
    return fixture


class LabFileResolver(etree.Resolver):
    """Never fall back to libxml's unrestricted file or network resolution."""

    def __init__(self, fixture, trace):
        super().__init__()
        self.fixture, self.trace = fixture, trace

    def resolve(self, url, public_id, context):
        if url != "file:///lab/message.txt":
            self.trace.append({"label": "External resource decision", "value": "Rejected: " + url})
            raise ValueError("The lab can resolve only file:///lab/message.txt.")
        self.trace.append({"label": "External resource read", "value": url + " → DEMO-DATA"})
        return self.resolve_filename(str(self.fixture), context)


def xml_vulnerable(value: str, context: dict):
    fixture = _xml_fixture(context)
    trace = [{"label": "XML input", "value": value}]
    parser = etree.XMLParser(resolve_entities=True, load_dtd=True, no_network=True)
    parser.resolvers.add(LabFileResolver(fixture, trace))
    trace.append({"label": "Parser settings", "value":
                  "resolve_entities=True, load_dtd=True, no_network=True"})
    try:
        root = etree.fromstring(value.encode("utf-8"), parser)
    except (etree.XMLSyntaxError, ValueError, UnicodeError) as error:
        trace.append({"label": "Parsing decision", "value": str(error)})
        return _result(400, "XML could not be parsed or the external resource is outside the lab scope.", trace,
                       "An invalid document or a resource outside the lab scope was rejected.")
    output = root.text or ""
    trace.extend([{"label": "DOCTYPE", "value": root.getroottree().docinfo.doctype or "None"},
                  {"label": "root.text", "value": output}])
    return _result(200, output, trace,
                   "External entity resolution is enabled: an entity declaration can bring the sample file's contents into the response.")


def xml_safe(value: str, context: dict):
    fixture = _xml_fixture(context)
    trace = [{"label": "XML input", "value": value}]
    parser = etree.XMLParser(resolve_entities=False, load_dtd=False, no_network=True)
    parser.resolvers.add(LabFileResolver(fixture, trace))
    trace.append({"label": "Parser settings", "value":
                  "resolve_entities=False, load_dtd=False, no_network=True"})
    try:
        root = etree.fromstring(value.encode("utf-8"), parser)
    except (etree.XMLSyntaxError, ValueError, UnicodeError) as error:
        trace.append({"label": "Parsing decision", "value": str(error)})
        return _result(400, "Invalid XML.", trace, "The malformed XML document was rejected.")
    if root.getroottree().docinfo.doctype:
        trace.append({"label": "DTD decision", "value": "DOCTYPE present → HTTP 400; entity not resolved."})
        return _result(400, "This endpoint does not accept DTDs.", trace,
                       "External entities were not resolved; the document containing a DTD was rejected.")
    output = root.text or ""
    trace.extend([{"label": "DTD decision", "value": "No DOCTYPE → accepted"},
                  {"label": "root.text", "value": output}])
    return _result(200, output, trace, "Normal XML was processed with external entity resolution disabled.")


def _json_type(value):
    if isinstance(value, str):
        return "string"
    if isinstance(value, dict):
        return "object"
    if isinstance(value, list):
        return "array"
    if value is None:
        return "null"
    if isinstance(value, bool):
        return "boolean"
    return "number"


def _decode_sku(value, trace):
    try:
        body = json.loads(value)
    except (json.JSONDecodeError, RecursionError) as error:
        raise ValueError("Provide a valid JSON body.") from error
    if not isinstance(body, dict) or set(body) != {"sku"}:
        raise ValueError("The body must be a JSON object containing only the sku field.")
    sku = body["sku"]
    trace.extend([{"label": "sku type", "value": _json_type(sku)},
                  {"label": "sku value", "value": sku}])
    return sku


def match_products(query: dict):
    """Python model: only {sku: str} and {sku: {$ne: str}}; not MongoDB."""
    if set(query) != {"sku"}:
        raise ValueError("The model supports only the sku field.")
    condition = query["sku"]
    if isinstance(condition, str):
        return [dict(row) for row in PRODUCTS if row["sku"] == condition]
    if (isinstance(condition, dict) and set(condition) == {"$ne"}
            and isinstance(condition["$ne"], str)):
        return [dict(row) for row in PRODUCTS if row["sku"] != condition["$ne"]]
    raise ValueError("The model supports only string equality or a {$ne: string} condition.")


def nosql_vulnerable(value: str, context: dict):
    trace = [{"label": "JSON input", "value": value}]
    try:
        sku = _decode_sku(value, trace)
        query = {"sku": sku}
        trace.append({"label": "Filter sent to the model", "value": query})
        rows = match_products(query)
    except ValueError as error:
        trace.append({"label": "Model decision", "value": str(error)})
        return _result(400, {"error": str(error)}, trace, "An invalid or unsupported query was rejected.")
    trace.append({"label": "Result rows", "value": rows})
    return _result(200, rows, trace,
                   "sku entered the filter without a type check; $ne inside an object can change the query condition.")


def nosql_safe(value: str, context: dict):
    trace = [{"label": "JSON input", "value": value}]
    try:
        sku = _decode_sku(value, trace)
    except ValueError as error:
        trace.append({"label": "Body decision", "value": str(error)})
        return _result(400, {"error": str(error)}, trace, "An invalid JSON body was rejected.")
    if not isinstance(sku, str):
        trace.append({"label": "Type decision", "value": "sku is not a string → HTTP 400; no filter was created."})
        return _result(400, {"error": "sku must be a string."}, trace,
                       "The type check rejected the value before a query was built; the model was not run.")
    query = {"sku": sku}
    trace.extend([{"label": "Type decision", "value": "sku is a string → accepted"},
                  {"label": "Filter sent to the model", "value": query}])
    rows = match_products(query)
    trace.append({"label": "Result rows", "value": rows})
    return _result(200, rows, trace,
                   "The server built a fixed equality filter from the SKU string after checking its type.")
