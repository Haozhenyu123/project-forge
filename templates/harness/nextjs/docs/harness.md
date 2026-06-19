# Next.js Harness

This harness defines the standard Project Forge command contract for Next.js App Router projects with TypeScript.

## How to verify

Run the commands listed in `project-forge.yaml` from the project root. At minimum, verify `install`, `lint`, `typecheck`, `build`, `test`, and `smoke` before handing off the project. Pay special attention to `npm run build` -- a passing Next.js production build catches most integration issues early.
