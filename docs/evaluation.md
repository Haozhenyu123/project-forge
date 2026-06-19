# Evaluation

Project Forge uses two evaluation layers.

Static scenarios under `evals/scenarios/` score saved responses for fast regression checks.

Live agent scenarios under `evals/agent/` can run Codex or Claude Code in an isolated temporary HOME and project directory. Missing CLIs are reported as `skip`, not `pass`. The live runner checks:

- expected Project Forge skill signals;
- no premature implementation tool usage before a required skill;
- response assertions;
- generated artifacts;
- command assertions.

Run a live scenario when the relevant CLI is installed:

```powershell
python scripts/evals/agent_runner.py --provider codex --scenario evals/agent/vague-idea.json
```

The live scenarios stop at Project Forge's boundary: creative direction, evidence, architecture, harness, and Superpowers handoff.
