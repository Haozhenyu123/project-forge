## Summary

## Project Forge Boundary

- [ ] This changes direction, evidence, architecture, harness, evaluation, packaging, or handoff.
- [ ] This does not reimplement Superpowers-owned TDD, debugging, code review, worktree, or branch workflows.

## Verification

```text
python -m unittest tests/test_project_forge.py
python scripts/install_test.py
python scripts/evals/validate_scenarios.py evals/scenarios
```
