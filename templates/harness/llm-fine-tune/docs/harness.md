# LLM Fine-tuning Pipeline Harness

Template: `llm-fine-tune`

## Commands

- **install**: `pip install -e .`
- **test**: `pytest`
- **lint**: `ruff check .`
- **typecheck**: `mypy src`
- **build**: `python -m src.train`
- **run**: `python -m src.serve`
- **smoke**: `python -c import transformers; print('OK')`

## Local Setup

1. Clone the repository
2. Run the install command
3. Run verify (test + lint + typecheck)
4. Start local dev with the run command
