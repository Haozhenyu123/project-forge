#!/usr/bin/env python3
"""Run live Project Forge agent evaluation scenarios in isolation."""

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from pathlib import Path


def load_scenario(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    required = {"id", "title", "prompt", "expected_skills"}
    missing = sorted(required - set(data))
    if missing:
        raise ValueError(f"{path}: missing {', '.join(missing)}")
    return data


def provider_command(provider):
    if provider == "codex":
        command = shutil.which("codex")
        return [command] if command else None
    if provider == "claude":
        command = shutil.which("claude")
        return [command] if command else None
    raise ValueError(f"Unknown provider: {provider}")


def probe(command):
    try:
        proc = subprocess.run(
            [*command, "--version"],
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return proc.returncode == 0


def command_for_prompt(provider, command, prompt):
    if provider == "codex":
        return [*command, prompt]
    if provider == "claude":
        return [*command, "-p", prompt, "--output-format", "stream-json"]
    return [*command, prompt]


def parse_event(line):
    try:
        return json.loads(line)
    except json.JSONDecodeError:
        return {"type": "text", "text": line}


def normalize_events(stdout):
    events = []
    for line in stdout.splitlines():
        if line.strip():
            events.append(parse_event(line))
    return events


def event_text(event):
    if "text" in event:
        return str(event["text"])
    if "result" in event:
        return str(event["result"])
    message = event.get("message")
    if isinstance(message, dict):
        content = message.get("content")
        if isinstance(content, list):
            return " ".join(str(item.get("text", "")) for item in content if isinstance(item, dict))
        return str(content)
    item = event.get("item")
    if isinstance(item, dict):
        return str(item.get("text") or item.get("command") or "")
    return ""


def tool_name(event):
    if event.get("type") == "tool_use":
        return event.get("name")
    message = event.get("message")
    if isinstance(message, dict):
        for item in message.get("content", []) or []:
            if isinstance(item, dict) and item.get("type") == "tool_use":
                return item.get("name")
    item = event.get("item")
    if isinstance(item, dict):
        if item.get("type") == "command_execution":
            return "command_execution"
        command = str(item.get("command", ""))
        if command:
            return "command_execution"
    return None


def skill_name(event):
    message = event.get("message")
    if isinstance(message, dict):
        for item in message.get("content", []) or []:
            if isinstance(item, dict) and item.get("name") == "Skill":
                payload = item.get("input", {})
                return payload.get("skill")
    text = event_text(event).lower()
    for skill in ("forge-intake", "creative-director", "ai-architect", "harness-engineer", "forge-project"):
        if skill in text:
            return skill
    return None


def evaluate_assertions(scenario, events, project_dir, plugin_dir):
    expected_skills = scenario.get("expected_skills", [])
    triggered = []
    called_tools = []
    tools_before_skill = []
    skill_seen = False

    for event in events:
        skill = skill_name(event)
        if skill:
            skill_seen = True
            if skill not in triggered:
                triggered.append(skill)
        name = tool_name(event)
        if name:
            called_tools.append(name)
            if not skill_seen and name != "Skill":
                tools_before_skill.append(name)

    response = "\n".join(event_text(event) for event in events)
    failures = []
    for skill in expected_skills:
        if skill not in triggered:
            failures.append(f"missing expected skill: {skill}")
    for text in scenario.get("response_assertions", {}).get("contains", []):
        if text not in response:
            failures.append(f"response missing: {text}")
    for text in scenario.get("response_assertions", {}).get("not_contains", []):
        if text in response:
            failures.append(f"response contained forbidden text: {text}")
    for assertion in scenario.get("artifact_assertions", []):
        path = project_dir / assertion["path"]
        if not path.is_file():
            failures.append(f"missing artifact: {assertion['path']}")
            continue
        body = path.read_text(encoding="utf-8")
        for text in assertion.get("contains", []):
            if text not in body:
                failures.append(f"artifact {assertion['path']} missing: {text}")
    for assertion in scenario.get("command_assertions", []):
        argv = [
            item.replace("{python}", sys.executable).replace("{plugin}", str(plugin_dir))
            for item in assertion["argv"]
        ]
        proc = subprocess.run(argv, cwd=project_dir, text=True, capture_output=True, check=False)
        if proc.returncode != assertion.get("exit_code", 0):
            failures.append(f"command assertion failed: {' '.join(argv)}")
    if scenario.get("forbid_tools_before_skill") and tools_before_skill:
        failures.append("tool used before required skill")

    return {
        "passed": not failures,
        "failures": failures,
        "tools_before_skill": tools_before_skill,
        "skills": {"triggered": triggered},
        "tools": {"called": called_tools},
    }


def run_scenario(scenario, provider, repo_root, log_root, command_override=None):
    repo_root = Path(repo_root)
    log_root = Path(log_root)
    command = command_override or provider_command(provider)
    if not command or not command[0]:
        return {"status": "skip", "reason": f"{provider} CLI unavailable"}
    if command_override and not Path(command[0]).exists() and not shutil.which(command[0]):
        return {"status": "skip", "reason": f"{provider} CLI unavailable"}
    if not probe(command):
        return {"status": "skip", "reason": f"{provider} CLI probe failed"}

    log_dir = log_root / f"{int(time.time() * 1000)}-{scenario['id']}-{provider}"
    log_dir.mkdir(parents=True, exist_ok=True)

    timeout = float(scenario.get("timeout_seconds", 180))
    with tempfile.TemporaryDirectory() as home, tempfile.TemporaryDirectory() as project:
        env = os.environ.copy()
        env["HOME"] = home
        env["USERPROFILE"] = home
        project_dir = Path(project)
        plugin_dir = repo_root
        argv = command_for_prompt(provider, command, scenario["prompt"])
        try:
            proc = subprocess.run(
                argv,
                cwd=project_dir,
                env=env,
                text=True,
                capture_output=True,
                timeout=timeout,
                check=False,
            )
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            proc = subprocess.CompletedProcess(argv, 124, exc.stdout or "", exc.stderr or "")
            timed_out = True

        (log_dir / "stdout.log").write_text(proc.stdout or "", encoding="utf-8")
        (log_dir / "stderr.log").write_text(proc.stderr or "", encoding="utf-8")
        events = normalize_events(proc.stdout or "")
        (log_dir / "events.jsonl").write_text(
            "\n".join(json.dumps(event, sort_keys=True) for event in events) + "\n",
            encoding="utf-8",
        )
        assertions = evaluate_assertions(scenario, events, project_dir, plugin_dir)

        status = "pass" if assertions["passed"] and proc.returncode == 0 and not timed_out else "fail"
        return {
            "status": status,
            "provider": provider,
            "scenario": scenario["id"],
            "returncode": proc.returncode,
            "timed_out": timed_out,
            "log_dir": str(log_dir),
            "isolation": {
                "temporary_home": True,
                "temporary_project": True,
            },
            **assertions,
        }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--scenario", required=True)
    parser.add_argument("--provider", choices=["codex", "claude"], required=True)
    parser.add_argument("--repo-root", default=".")
    parser.add_argument("--log-root", default=".project-forge/agent-evals")
    args = parser.parse_args()
    result = run_scenario(
        load_scenario(args.scenario),
        args.provider,
        Path(args.repo_root),
        Path(args.log_root),
    )
    print(json.dumps(result, indent=2, sort_keys=True))
    return 0 if result["status"] in {"pass", "skip"} else 1


if __name__ == "__main__":
    raise SystemExit(main())
