# Project Forge

Project Forge is a dual-harness plugin for Codex and Claude Code. It helps agents turn a rough project idea into a researched architecture, an implementation-ready harness, and repeatable verification steps.

## What It Provides

- AI Creative Design Director: shapes ambiguous product intent into a coherent creative and user experience direction before implementation starts.
- AI Architect: researches comparable projects, records evidence, chooses a stack, and writes architecture decisions with clear trade-offs.
- Harness Engineering: defines install, test, lint, typecheck, build, run, and smoke commands so the project can be verified consistently.
- Research scripts: collect and normalize GitHub and web evidence for stack decisions and implementation planning.
- Templates: provide starter harness contracts, documentation, and CI workflows for common project shapes.
- Evals: validate Project Forge scenarios and keep the plugin behavior measurable as the system evolves.

## Install And Use

For Codex, install or symlink this repository as a Codex plugin, then confirm `.codex-plugin/plugin.json` is discoverable. The Codex manifest points at `./skills/` and exposes the plugin as `Project Forge`.

For Claude Code, install or symlink this repository as a Claude plugin, then confirm `.claude-plugin/plugin.json` is discoverable. The Claude manifest points at the same `./skills/` directory and exposes the plugin as `Project Forge`.

Typical usage:

1. Start with the forge intake skill to capture the project goal and constraints.
2. Use the creative director and architect skills to refine direction, collect evidence, and choose a stack.
3. Use the harness engineer skill to write `project-forge.yaml`, harness docs, and verification commands.
4. Run the research scripts, templates, and evals as needed to check that the project remains grounded and testable.

## Quickstart in Chinese

中文快速开始：

1. 在 Codex 或 Claude Code 中安装或链接这个插件仓库。
2. 确认插件名称显示为 `Project Forge`。
3. 先使用 intake 流程说明项目目标、约束和成功标准。
4. 让 AI Architect 基于 GitHub 和 Web 证据选择技术栈，并写下取舍理由。
5. 让 Harness Engineer 生成 `project-forge.yaml` 和验证命令，再运行 install/test/lint/typecheck/build/run/smoke 检查项目。

## Sample Contract

The root `project-forge.yaml` is a compact sample output contract. Project templates may provide more specific versions for Node, Python, or generic stacks.

## License

MIT
