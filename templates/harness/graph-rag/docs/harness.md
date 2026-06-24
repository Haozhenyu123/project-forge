# Graph RAG Harness

Template: `graph-rag`

## Commands

- **install**: `pip install -e .`
- **test**: `pytest`
- **lint**: `ruff check .`
- **typecheck**: `mypy src`
- **build**: `python -c print('No build step')`
- **run**: `uvicorn src.main:app --reload`
- **smoke**: `python -c from src.main import app; print('OK')`

## Local Setup

1. Clone the repository
2. Run the install command
3. Run verify (test + lint + typecheck)
4. Start local dev with the run command
