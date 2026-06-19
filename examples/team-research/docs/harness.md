# Harness

team-research follows the Project Forge command contract in project-forge.yaml.

## How to verify

Run commands from the team-research project root unless a command names a repository-relative path.

- install: npm ci
- test: npm test
- lint: npm run lint
- typecheck: npm run typecheck
- build: npm run build
- run: npm start
- smoke: python ../../scripts/smoke_test.py --project . --slug team-research

The smoke command validates that the research evidence, ADR, harness contract, harness guide, and Superpowers handoff all refer to team-research.
