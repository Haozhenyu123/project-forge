"""Generate CI for one or more structured harness stacks."""

from pathlib import Path


def _quote(argv):
    return " ".join(f'"{item}"' if " " in item else item for item in argv)


def _job_id(value):
    return value.replace("-", "_")


def render_ci(contract):
    lines = [
        "name: Project Forge CI",
        "",
        "on:",
        "  push:",
        "  pull_request:",
        "",
        "jobs:",
    ]
    job_ids = []
    for stack in contract.all_stacks():
        job = "verify_" + _job_id(stack.id)
        job_ids.append(job)
        lines.extend([
            f"  {job}:",
            f"    name: Verify {stack.id}",
            "    runs-on: ubuntu-latest",
            "    steps:",
            "      - uses: actions/checkout@v4",
        ])
        if stack.template in {"node-ts", "nextjs", "electron", "cli", "chrome-extension"}:
            lines.extend([
                "      - uses: actions/setup-node@v4",
                "        with:",
                '          node-version: "22"',
            ])
        if stack.template in {"python", "fastapi"}:
            lines.extend([
                "      - uses: actions/setup-python@v5",
                "        with:",
                '          python-version: "3.12"',
            ])
        for name in ("install", "test", "lint", "typecheck", "build", "smoke"):
            command = stack.commands[name]
            if command.argv:
                lines.append(f"      - name: {stack.id} {name}")
                lines.append(f"        working-directory: {stack.root}")
                lines.append(f"        run: {_quote(command.argv)}")
            else:
                lines.append(f"      - name: {stack.id} {name} (legacy)")
                lines.append(f"        working-directory: {stack.root}")
                lines.append(f"        run: {command.legacy_shell}")
    if len(job_ids) > 1:
        lines.extend([
            "  integration_smoke:",
            "    name: Multi-stack contract smoke",
            "    runs-on: ubuntu-latest",
            "    needs: [" + ", ".join(job_ids) + "]",
            "    steps:",
            "      - uses: actions/checkout@v4",
            f"      - run: python scripts/cli.py superpowers-ready --slug {contract.project.slug} --json .",
        ])
    return "\n".join(lines) + "\n"


def write_ci(path, contract):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="\n") as handle:
        handle.write(render_ci(contract))
