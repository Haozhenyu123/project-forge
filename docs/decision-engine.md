# Decision Engine

Project Forge's decision engine turns a goal, constraints, creative signals, and evidence into a bounded architecture decision. It does not generate application code and does not replace Superpowers implementation workflows.

The engine produces:

- three product directions and a selected default;
- two to four architecture candidates;
- a selected primary harness and optional secondary harness;
- rejected options with reasons;
- confidence level and revisit triggers;
- handoff requirements for the harness engineer and Superpowers.

Run it with:

```powershell
python scripts/decision/engine.py --input brief.json --out decision.json
```

Then pass the decision into Forge:

```powershell
python scripts/forge_project.py --project my-app --slug my-app --goal "..." --stack nextjs --evidence evidence.jsonl --decision-file decision.json
```
