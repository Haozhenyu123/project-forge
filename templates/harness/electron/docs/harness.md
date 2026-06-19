# Electron Harness

This harness defines the standard Project Forge command contract for Electron desktop applications with TypeScript.

## How to verify

Run the commands listed in `project-forge.yaml` from the project root. At minimum, verify `install`, `lint`, `typecheck`, `build`, `test`, and `smoke` before handing off the project. Electron builds produce platform-specific artifacts; run `npm run build` on each target platform or verify via CI matrix builds.
