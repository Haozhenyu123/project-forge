.PHONY: test verify clean install smoke evals lint

PYTHON := python

test:
	$(PYTHON) -m unittest tests/test_project_forge.py

verify: test
	$(PYTHON) scripts/evals/validate_scenarios.py evals/scenarios
	$(PYTHON) scripts/smoke_test.py --project examples/team-research --slug team-research
	$(PYTHON) scripts/cli.py superpowers-ready --slug team-research examples/team-research
	$(PYTHON) scripts/install_test.py

smoke:
	$(PYTHON) scripts/smoke_test.py --project examples/team-research --slug team-research
	$(PYTHON) scripts/cli.py superpowers-ready --slug team-research examples/team-research

evals:
	$(PYTHON) scripts/evals/validate_scenarios.py evals/scenarios
	$(PYTHON) scripts/evals/run_scenarios.py --scenario-dir evals/scenarios --responses-dir tests/fixtures/eval_responses --out /tmp/eval-results.json

evaluate: evals
	@echo ""
	@echo "Agent evaluator scores:"
	@type /tmp/eval-results.json 2>/dev/null || cat /tmp/eval-results.json

install-test:
	$(PYTHON) scripts/install_test.py

clean:
	$(PYTHON) scripts/clean.py

lint:
	$(PYTHON) -m compileall scripts
	$(PYTHON) -c "import sys; from pathlib import Path; skills = list(Path('skills').glob('*/SKILL.md')); bad = [s for s in skills if 'TODO' in s.read_text().upper() or 'TBD' in s.read_text().upper() or '[placeholder' in s.read_text().lower()]; sys.exit(1) if bad else print('Skills clean')"

cli-demo:
	$(PYTHON) scripts/cli.py list-templates
	$(PYTHON) scripts/cli.py detect . --json

e2e:
	$(PYTHON) -m unittest tests/test_project_forge.py -k Integration

