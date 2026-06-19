#!/usr/bin/env python3
"""Project Forge MCP server -- provides search, template, and eval tools via MCP protocol.

Run as an MCP server:
  python scripts/mcp/server.py
"""

import json
import subprocess
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[2]
SCRIPTS_ROOT = REPO_ROOT / "scripts"

SERVER_NAME = "project-forge"
SERVER_VERSION = "0.2.5"

TEMPLATES = ["node-ts", "python", "generic", "nextjs", "fastapi", "electron", "cli", "chrome-extension"]


def log(message):
    print(f"[project-forge-mcp] {message}", file=sys.stderr, flush=True)


def read_message():
    line = sys.stdin.readline()
    if not line:
        return None
    return json.loads(line)


def write_message(message):
    sys.stdout.write(json.dumps(message, sort_keys=True) + "\n")
    sys.stdout.flush()


def write_response(request_id, result):
    write_message({"jsonrpc": "2.0", "id": request_id, "result": result})


def write_error(request_id, code, message):
    write_message({"jsonrpc": "2.0", "id": request_id, "error": {"code": code, "message": message}})


def run_script(script, *args):
    proc = subprocess.run(
        [sys.executable, str(SCRIPTS_ROOT / script), *args],
        cwd=REPO_ROOT,
        text=True,
        capture_output=True,
    )
    return proc.returncode, proc.stdout, proc.stderr


TOOLS = [
    {
        "name": "github_search",
        "description": "Search GitHub repositories for architecture research evidence.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "GitHub search query"},
                "limit": {"type": "integer", "description": "Max results (default 10)", "default": 10},
            },
            "required": ["query"],
        },
    },
    {
        "name": "web_search",
        "description": "Record a web search query for host agent execution. Returns a search instruction when no API key is configured.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "query": {"type": "string", "description": "Web search query"},
                "limit": {"type": "integer", "description": "Max results (default 5)", "default": 5},
            },
            "required": ["query"],
        },
    },
    {
        "name": "detect_stack",
        "description": "Detect the project stack and return harness command contract.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project directory path"},
            },
            "required": ["project"],
        },
    },
    {
        "name": "apply_template",
        "description": "Apply a harness template to a project directory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "template": {"type": "string", "enum": TEMPLATES, "description": "Template name"},
                "project": {"type": "string", "description": "Target project directory"},
                "force": {"type": "boolean", "description": "Overwrite existing files", "default": False},
            },
            "required": ["template", "project"],
        },
    },
    {
        "name": "forge_project",
        "description": "Run the full Project Forge coordinator flow: evidence, ADR, harness, and handoff.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Target project directory"},
                "slug": {"type": "string", "description": "Project slug"},
                "goal": {"type": "string", "description": "Project goal description"},
                "stack": {"type": "string", "enum": TEMPLATES, "description": "Harness template"},
                "evidence": {"type": "string", "description": "Path to evidence JSON/JSONL file or directory"},
                "force": {"type": "boolean", "description": "Overwrite existing Forge artifacts", "default": False},
            },
            "required": ["project", "slug", "goal", "stack", "evidence"],
        },
    },
    {
        "name": "export_handoff",
        "description": "Export a Superpowers implementation handoff from Forge artifacts.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project directory"},
                "slug": {"type": "string", "description": "Project slug"},
                "out": {"type": "string", "description": "Output file path"},
            },
            "required": ["project", "slug"],
        },
    },
    {
        "name": "superpowers_ready",
        "description": "Check whether Project Forge artifacts are ready for Superpowers consumption.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project": {"type": "string", "description": "Project directory"},
                "slug": {"type": "string", "description": "Project slug"},
                "strict": {"type": "boolean", "description": "Treat warnings as failures", "default": False},
            },
            "required": ["project", "slug"],
        },
    },
    {
        "name": "validate_evidence",
        "description": "Validate an evidence JSONL file for completeness.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "evidence_file": {"type": "string", "description": "Path to evidence.jsonl"},
            },
            "required": ["evidence_file"],
        },
    },
    {
        "name": "list_templates",
        "description": "List available harness templates.",
        "inputSchema": {
            "type": "object",
            "properties": {},
        },
    },
    {
        "name": "run_evals",
        "description": "Run evaluation scenarios against response fixtures.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "scenario_dir": {"type": "string", "description": "Path to scenario directory"},
                "responses_dir": {"type": "string", "description": "Path to fixture responses directory"},
            },
            "required": ["scenario_dir", "responses_dir"],
        },
    },
]


def handle_initialize(request_id, params):
    return write_response(request_id, {
        "protocolVersion": "2024-11-05",
        "capabilities": {"tools": {}},
        "serverInfo": {"name": SERVER_NAME, "version": SERVER_VERSION},
    })


def handle_tools_list(request_id, params):
    return write_response(request_id, {"tools": TOOLS})


def handle_tools_call(request_id, params):
    tool_name = params.get("name")
    tool_args = params.get("arguments", {})

    tool_map = {
        "github_search": lambda a: run_script(
            "research/github_search.py",
            "--query", a["query"],
            "--limit", str(a.get("limit", 10)),
            "--out", str(REPO_ROOT / "tmp_mcp_github.jsonl"),
        ),
        "web_search": lambda a: run_script(
            "research/web_search.py",
            "--query", a["query"],
            "--limit", str(a.get("limit", 5)),
            "--out", str(REPO_ROOT / "tmp_mcp_web.jsonl"),
        ),
        "detect_stack": lambda a: run_script(
            "harness/detect_stack.py",
            "--project", a["project"],
            "--json",
        ),
        "apply_template": lambda a: run_script(
            "harness/apply_template.py",
            "--template", a["template"],
            "--project", a["project"],
            *(["--force"] if a.get("force") else []),
        ),
        "forge_project": lambda a: run_script(
            "forge_project.py",
            "--project", a["project"],
            "--slug", a["slug"],
            "--goal", a["goal"],
            "--stack", a["stack"],
            "--evidence", a["evidence"],
            *(["--force"] if a.get("force") else []),
        ),
        "export_handoff": lambda a: run_script(
            "export_handoff.py",
            "--project", a["project"],
            "--slug", a["slug"],
            "--out", a.get("out", f"{a['project']}/docs/superpowers-handoff.md"),
        ),
        "superpowers_ready": lambda a: run_script(
            "superpowers_ready.py",
            "--project", a["project"],
            "--slug", a["slug"],
            "--json",
            *(["--strict"] if a.get("strict") else []),
        ),
        "validate_evidence": lambda a: run_script(
            "research/validate_evidence.py", a["evidence_file"],
        ),
        "list_templates": lambda a: (0, json.dumps({"templates": TEMPLATES}), ""),
        "run_evals": lambda a: run_script(
            "evals/run_scenarios.py",
            "--scenario-dir", a["scenario_dir"],
            "--responses-dir", a["responses_dir"],
            "--out", str(REPO_ROOT / "tmp_mcp_evals.json"),
        ),
    }

    handler = tool_map.get(tool_name)
    if not handler:
        return write_error(request_id, -32601, f"Unknown tool: {tool_name}")

    try:
        returncode, stdout, stderr = handler(tool_args)
        if returncode != 0:
            return write_response(request_id, {
                "content": [{"type": "text", "text": f"Tool {tool_name} failed:\n{stderr}"}],
                "isError": True,
            })
        return write_response(request_id, {
            "content": [{"type": "text", "text": stdout.strip() or f"Tool {tool_name} completed successfully."}],
        })
    except Exception as exc:
        return write_error(request_id, -32000, str(exc))


def handle_notifications_initialized(request_id, params):
    pass


METHOD_MAP = {
    "initialize": handle_initialize,
    "notifications/initialized": handle_notifications_initialized,
    "tools/list": handle_tools_list,
    "tools/call": handle_tools_call,
}


def main():
    log(f"Starting Project Forge MCP server v{SERVER_VERSION}")
    while True:
        try:
            message = read_message()
        except json.JSONDecodeError as exc:
            log(f"Invalid JSON: {exc}")
            continue
        if message is None:
            log("EOF -- exiting")
            break

        request_id = message.get("id")
        method = message.get("method")
        params = message.get("params", {})

        handler = METHOD_MAP.get(method)
        if not handler:
            write_error(request_id, -32601, f"Method not found: {method}")
            continue

        try:
            handler(request_id, params)
        except Exception as exc:
            log(f"Unhandled error in {method}: {exc}")
            if request_id is not None:
                write_error(request_id, -32603, str(exc))


if __name__ == "__main__":
    main()
