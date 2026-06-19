# FastAPI Harness

This harness defines the standard Project Forge command contract for FastAPI Python projects.

## How to verify

Run the commands listed in `project-forge.yaml` from the project root. At minimum, verify `install`, `lint`, `typecheck`, `test`, and `smoke` before handing off the project. FastAPI projects skip the build step by default; add a Docker build command if containerization is part of the delivery contract.
