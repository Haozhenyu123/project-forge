# Data Pipeline Harness

Template: `data-pipeline`

## Commands

- **install**: `pip install -e .`
- **test**: `pytest`
- **lint**: `ruff check .`
- **typecheck**: `mypy src`
- **build**: `dbt build`
- **run**: `airflow standalone`
- **smoke**: `dbt compile`

## Local Setup

1. Clone the repository
2. Run the install command
3. Run verify (test + lint + typecheck)
4. Start local dev with the run command
