"""Run a plan-only Superpowers handoff compatibility evaluation."""

import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from project_forge.hosts import HostService

from .models import CompatibilityResult, EvalStatus


CREDENTIAL_KEYS = {
    "codex": ("OPENAI_API_KEY", "CODEX_API_KEY"),
    "claude": ("ANTHROPIC_API_KEY",),
}


def load_matrix(path):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if data.get("schema_version") != 1 or not isinstance(data.get("versions"), list):
        raise ValueError("unsupported compatibility matrix")
    return data


def matrix_entry(matrix, version, host):
    for entry in matrix["versions"]:
        if entry.get("superpowers") == version and host in entry.get("hosts", []):
            return entry
    return None


def provider_command(host):
    executable = shutil.which(host)
    return [executable] if executable else None


def probe(command):
    try:
        result = subprocess.run(
            [*command, "--version"], capture_output=True, text=True, timeout=15, check=False
        )
    except (OSError, subprocess.TimeoutExpired):
        return False
    return result.returncode == 0


def credentials_available(host, env):
    return any(env.get(key) for key in CREDENTIAL_KEYS[host])


def load_handoff(project):
    path = Path(project) / "docs" / "superpowers-handoff.json"
    data = json.loads(path.read_text(encoding="utf-8"))
    if data.get("kind") != "project-forge.superpowers-handoff":
        raise ValueError("invalid Superpowers handoff kind")
    if data.get("schema_version") not in {1, 2}:
        raise ValueError("unsupported Superpowers handoff schema")
    return data


def plan_prompt(handoff, superpowers_dir):
    artifacts = handoff.get("artifacts", {})
    first_task = handoff.get("superpowers", {}).get("first_task", "")
    adr = artifacts.get("adr", "docs/architecture/ADR-0001-stack.md")
    contract = artifacts.get("contract", "project-forge.yaml")
    return "\n".join(
        [
            "Use the Superpowers planning workflow located at %s." % superpowers_dir,
            "Read docs/superpowers-handoff.json and produce an implementation PLAN ONLY.",
            "Do not edit files, run project commands, implement code, or choose a different architecture.",
            "Honor Project Forge's accepted decisions and return these exact headings:",
            "Architecture basis: %s" % adr,
            "Harness basis: %s" % contract,
            "First task: %s" % first_task,
            "Implementation status: not started",
            "Then give ordered implementation steps and identify which Superpowers-owned discipline applies.",
        ]
    )


def command_for_plan(host, command, prompt):
    if host == "codex":
        return [*command, "exec", "--json", "--sandbox", "read-only", prompt]
    return [
        *command,
        "-p",
        prompt,
        "--output-format",
        "stream-json",
        "--permission-mode",
        "plan",
    ]


def output_text(stdout):
    parts = []
    for line in stdout.splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            parts.append(line)
            continue
        for key in ("text", "result"):
            if event.get(key):
                parts.append(str(event[key]))
        message = event.get("message")
        if isinstance(message, dict):
            for item in message.get("content", []) or []:
                if isinstance(item, dict) and item.get("text"):
                    parts.append(str(item["text"]))
        item = event.get("item")
        if isinstance(item, dict) and item.get("text"):
            parts.append(str(item["text"]))
    return "\n".join(parts)


def snapshot_files(root):
    result = {}
    for path in sorted(Path(root).rglob("*")):
        if path.is_file():
            result[path.relative_to(root).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def evaluate_plan(text, handoff, before, after):
    artifacts = handoff.get("artifacts", {})
    adr = artifacts.get("adr", "docs/architecture/ADR-0001-stack.md")
    contract = artifacts.get("contract", "project-forge.yaml")
    first_task = handoff.get("superpowers", {}).get("first_task", "")
    assertions = {
        "references_adr": ("Architecture basis: %s" % adr).lower() in text.lower(),
        "references_harness": ("Harness basis: %s" % contract).lower() in text.lower(),
        "references_first_task": ("First task: %s" % first_task).lower() in text.lower(),
        "declares_not_started": "implementation status: not started" in text.lower(),
        "project_unchanged": before == after,
        "does_not_reselect_architecture": not any(
            phrase in text.lower()
            for phrase in ("switch the architecture", "replace the chosen stack", "choose a different stack")
        ),
    }
    failures = [name.replace("_", " ") for name, passed in assertions.items() if not passed]
    return assertions, failures


def _install_superpowers(source, destination):
    if destination.exists():
        shutil.rmtree(destination)
    shutil.copytree(source, destination, ignore=shutil.ignore_patterns(".git", "__pycache__"))


def run_compatibility(
    host,
    project,
    plugin_root,
    superpowers_dir,
    superpowers_version,
    matrix_path,
    log_root,
    command_override=None,
    env=None,
    timeout_seconds=180,
    require_credentials=True,
):
    host = str(host)
    credential_env = dict(os.environ if env is None else env)
    environment = dict(os.environ)
    if env:
        environment.update(env)
    matrix = load_matrix(matrix_path)
    entry = matrix_entry(matrix, superpowers_version, host)
    if not entry:
        return CompatibilityResult(
            EvalStatus.NOT_RUN, host, superpowers_version, "version/host is absent from the matrix"
        )
    if require_credentials and not credentials_available(host, credential_env):
        return CompatibilityResult(EvalStatus.NOT_RUN, host, superpowers_version, "%s credentials unavailable" % host)
    command = command_override or provider_command(host)
    if not command or not command[0] or not (Path(command[0]).exists() or shutil.which(command[0])):
        return CompatibilityResult(EvalStatus.NOT_RUN, host, superpowers_version, "%s CLI unavailable" % host)
    if not probe(command):
        return CompatibilityResult(EvalStatus.NOT_RUN, host, superpowers_version, "%s CLI probe failed" % host)
    superpowers_dir = Path(superpowers_dir) if superpowers_dir else None
    if not superpowers_dir or not superpowers_dir.is_dir():
        return CompatibilityResult(
            EvalStatus.NOT_RUN, host, superpowers_version, "Superpowers source unavailable"
        )
    try:
        handoff = load_handoff(project)
    except (OSError, ValueError, KeyError) as exc:
        return CompatibilityResult(EvalStatus.FAIL, host, superpowers_version, str(exc))

    log_dir = Path(log_root) / ("%d-%s-%s" % (int(time.time() * 1000), host, superpowers_version))
    log_dir.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory() as home_value, tempfile.TemporaryDirectory() as project_value:
        home, isolated_project = Path(home_value), Path(project_value) / "project"
        shutil.copytree(project, isolated_project)
        if host == "codex":
            service = HostService.codex(plugin_root, home / ".codex", home / ".agents")
            installed_superpowers = home / ".codex" / "plugins" / "superpowers"
        else:
            marketplace = home / ".claude" / "project-forge-marketplace"
            service = HostService.claude(plugin_root, marketplace)
            installed_superpowers = marketplace / "plugins" / "superpowers"
        install_result = service.install(cachebuster="compat")
        if not install_result.ok:
            return CompatibilityResult(
                EvalStatus.FAIL, host, superpowers_version, "; ".join(install_result.errors)
            )
        _install_superpowers(superpowers_dir, installed_superpowers)
        prompt = plan_prompt(handoff, installed_superpowers)
        argv = command_for_plan(host, command, prompt)
        run_env = dict(environment)
        run_env.update({"HOME": str(home), "USERPROFILE": str(home)})
        before = snapshot_files(isolated_project)
        try:
            proc = subprocess.run(
                argv,
                cwd=isolated_project,
                env=run_env,
                text=True,
                capture_output=True,
                timeout=timeout_seconds,
                check=False,
            )
            timed_out = False
        except subprocess.TimeoutExpired as exc:
            proc = subprocess.CompletedProcess(argv, 124, exc.stdout or "", exc.stderr or "")
            timed_out = True
        after = snapshot_files(isolated_project)
        stdout = proc.stdout or ""
        (log_dir / "stdout.log").write_text(stdout, encoding="utf-8")
        (log_dir / "stderr.log").write_text(proc.stderr or "", encoding="utf-8")
        (log_dir / "prompt.txt").write_text(prompt, encoding="utf-8")
        assertions, failures = evaluate_plan(output_text(stdout), handoff, before, after)
        if proc.returncode != 0:
            failures.append("host CLI returned %s" % proc.returncode)
        if timed_out:
            failures.append("host CLI timed out")
        status = EvalStatus.PASS if not failures else EvalStatus.FAIL
        result = CompatibilityResult(
            status,
            host,
            superpowers_version,
            returncode=proc.returncode,
            timed_out=timed_out,
            assertions=assertions,
            failures=failures,
            log_dir=str(log_dir),
        )
        (log_dir / "result.json").write_text(
            json.dumps(result.to_dict(), indent=2, sort_keys=True) + "\n", encoding="utf-8"
        )
        return result
