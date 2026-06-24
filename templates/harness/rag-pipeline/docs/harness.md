# RAG Pipeline Harness

Template: `rag-pipeline`

## Commands

- **install**: `pip install -e .`
- **test**: `pytest`
- **lint**: `ruff check .`
- **typecheck**: `mypy src`
- **build**: `python -c print('No build step for Python RAG pipeline')`
- **run**: `uvicorn src.main:app --reload`
- **smoke**: `python -c from src.main import app; print('App loaded OK')`

## Local Setup

1. Clone the repository
2. Run the install command
3. Run verify (test + lint + typecheck)
4. Start local dev with the run command
