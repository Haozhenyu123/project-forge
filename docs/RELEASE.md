# Publishing a GitHub Release for Project Forge v1.0.0

## Prerequisites

- Git tag `v1.0.0` pushed to `Haozhenyu123/project-forge`
- Release artifacts built in `.project-forge-dist/`

## One-time: Create the GitHub Release

1. Go to https://github.com/Haozhenyu123/project-forge/releases/new
2. Tag: `v1.0.0`
3. Title: `Project Forge v1.0.0 - Persona-driven architecture pipeline`
4. Description:

```
### What's new in v1.0.0

**Four persona-driven roles** — every step in the pipeline is a senior AI prompt engineer:
- 资深产品需求分析师 (Intake)
- 资深AI Prompt工程师 + 产品架构师 (Creative Director)
- 资深AI Prompt工程师 + 技术架构师 (AI Architect)
- 资深AI Prompt工程师 + DevOps工程师 (Harness Engineer)

**Domain classification** — 10 domains with probing axes for deep product discovery:
medical, finance, legal, education, gaming, ecommerce, enterprise, content, iot, general

**29 stack templates** — mini-programs, mobile, AI/ML, games, IoT, data pipelines

**One-line installer** — no git, no Python required

### Installation

```powershell
irm https://raw.githubusercontent.com/Haozhenyu123/project-forge/main/install/install-codex.ps1 | iex
```

Restart Codex → Settings → Plugins → Personal → Project Forge → ON
```

5. Upload these files from `.project-forge-dist/`:
   - `project-forge-codex-1.0.0.zip`
   - `project-forge-codex-1.0.0.submission.json`
   - `project-forge-claude-1.0.0.zip`
   - `project-forge-claude-1.0.0.submission.json`
   - `install-codex.ps1`
   - `install-codex.cmd`
   - `SHA256SUMS`
   - `HOST-SHA256SUMS`

6. Publish

## User-facing one-liner (share this everywhere)

### PowerShell (recommended)
```powershell
irm https://raw.githubusercontent.com/Haozhenyu123/project-forge/main/install/install-codex.ps1 | iex
```

### CMD
```cmd
curl -L -o %TEMP%\install-codex.cmd https://raw.githubusercontent.com/Haozhenyu123/project-forge/main/install/install-codex.cmd && %TEMP%\install-codex.cmd
```

### Manual (if you already have the repo cloned)
```powershell
cd project-forge
.\install\install-codex.ps1
```

## After installation

1. Restart the Codex desktop app
2. Go to Settings → Plugins
3. Find "Project Forge" under the Personal section
4. Toggle it ON
5. Start a new chat: "I want to build a medical consultation app"

The full persona pipeline will activate: intent classification → creative director probing → architecture selection → harness generation.
