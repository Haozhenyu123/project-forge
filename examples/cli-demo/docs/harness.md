# CLI Harness

This harness defines the standard Project Forge command contract for Node.js CLI tools with TypeScript.

## How to verify

Run the commands listed in `project-forge.yaml` from the project root. At minimum, verify `install`, `lint`, `typecheck`, `build`, `test`, and `smoke` before handing off the project. For CLI tools, also verify that `node dist/index.js --help` (or the equivalent entry point) produces usable output.
