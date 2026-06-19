# Chrome Extension Harness

This harness defines the standard Project Forge command contract for Chrome Extension (Manifest V3) projects with TypeScript.

## How to verify

Run the commands listed in `project-forge.yaml` from the project root. At minimum, verify `install`, `lint`, `typecheck`, `build`, `test`, and `smoke` before handing off the project. Chrome Extensions require manual loading from `chrome://extensions` in developer mode; the `run` command documents this step rather than opening a browser automatically.
