"""Auditable execution for structured harness commands."""

import json
import os
import signal
import subprocess
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from pathlib import Path

from project_forge.errors import ExecutionBlocked
from project_forge.models import COMMAND_ORDER, CommandSpec, ProjectContract, ReadinessStatus


DEFAULT_EXECUTE = ("test", "lint", "typecheck", "build", "smoke")


@dataclass
class CommandResult:
    stack: str
    command: str
    status: str
    returncode: int
    duration_seconds: float
    stdout: str
    stderr: str


def _terminate(proc):
    if proc.poll() is not None:
        return
    try:
        if os.name == "nt":
            subprocess.run(
                ["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                capture_output=True,
                check=False,
            )
        else:
            os.killpg(proc.pid, signal.SIGTERM)
    except OSError:
        proc.kill()


def execute_command(spec, project_root, timeout, allow_legacy_shell=False):
    cwd = (Path(project_root) / spec.cwd).resolve()
    project = Path(project_root).resolve()
    try:
        cwd.relative_to(project)
    except ValueError as exc:
        raise ExecutionBlocked(f"command cwd escapes project: {spec.cwd}") from exc
    if not cwd.is_dir():
        raise ExecutionBlocked(f"command cwd does not exist: {spec.cwd}")
    if spec.legacy_shell and not allow_legacy_shell:
        raise ExecutionBlocked("legacy shell command requires --allow-legacy-shell")
    argv = spec.argv if spec.argv else spec.legacy_shell
    shell = bool(spec.legacy_shell)
    started = time.monotonic()
    popen_kwargs = {
        "cwd": cwd,
        "text": True,
        "stdout": subprocess.PIPE,
        "stderr": subprocess.PIPE,
        "shell": shell,
    }
    if os.name != "nt":
        popen_kwargs["start_new_session"] = True
    proc = subprocess.Popen(argv, **popen_kwargs)
    try:
        stdout, stderr = proc.communicate(timeout=timeout)
        status = "passed" if proc.returncode == 0 else "failed"
    except subprocess.TimeoutExpired:
        _terminate(proc)
        stdout, stderr = proc.communicate()
        status = "timeout"
    return proc.returncode if status != "timeout" else 124, status, time.monotonic() - started, stdout, stderr


def execute_contract(
    contract: ProjectContract,
    project_root,
    selected=None,
    include_install=False,
    include_run=False,
    allow_legacy_shell=False,
    timeout_seconds=300,
    continue_on_failure=False,
):
    names = list(selected or DEFAULT_EXECUTE)
    if include_install and "install" not in names:
        names.insert(0, "install")
    if include_run and "run" not in names:
        names.append("run")
    unknown = sorted(set(names) - set(COMMAND_ORDER))
    if unknown:
        raise ExecutionBlocked("unknown command names: " + ", ".join(unknown))
    results = []
    for stack in contract.all_stacks():
        for name in names:
            spec = stack.commands[name]
            try:
                returncode, status, duration, stdout, stderr = execute_command(
                    spec,
                    project_root,
                    min(timeout_seconds, spec.timeout_seconds),
                    allow_legacy_shell,
                )
            except ExecutionBlocked as exc:
                returncode, status, duration, stdout, stderr = 126, "blocked", 0.0, "", str(exc)
            results.append(CommandResult(stack.id, name, status, returncode, duration, stdout, stderr))
            if status != "passed" and not continue_on_failure:
                return results
    return results


def write_report(project_root, results, selected):
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    run_dir = Path(project_root) / ".project-forge" / "verification" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    serialized = []
    for index, result in enumerate(results, start=1):
        stem = f"{index:02d}-{result.stack}-{result.command}"
        (run_dir / f"{stem}.stdout.log").write_text(result.stdout, encoding="utf-8")
        (run_dir / f"{stem}.stderr.log").write_text(result.stderr, encoding="utf-8")
        item = asdict(result)
        item["stdout_log"] = f"{stem}.stdout.log"
        item["stderr_log"] = f"{stem}.stderr.log"
        item.pop("stdout")
        item.pop("stderr")
        serialized.append(item)
    statuses = {item["status"] for item in serialized}
    if statuses == {"passed"}:
        readiness = ReadinessStatus.VERIFIED.value
    elif "failed" in statuses or "timeout" in statuses or "blocked" in statuses:
        readiness = ReadinessStatus.FAILED.value
    else:
        readiness = ReadinessStatus.PARTIAL.value
    payload = {
        "schema_version": 1,
        "run_id": run_id,
        "status": readiness,
        "selected_commands": list(selected),
        "results": serialized,
    }
    report = run_dir / "report.json"
    report.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return report, payload
