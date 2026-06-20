# ⚒️ Project Forge

<p align="center">
  <img src="assets/logo.png" alt="Project Forge" width="180">
</p>

<p align="center">
  <b>别急着写代码。先想清楚：做什么、为什么、怎么架构。</b>
</p>

<p align="center">
  <a href="LICENSE"><img src="https://img.shields.io/badge/License-MIT-blue.svg" alt="License"></a>
  <a href="CHANGELOG.md"><img src="https://img.shields.io/badge/version-0.3.3-brightgreen" alt="Version"></a>
  <a href="."><img src="https://img.shields.io/badge/tests-132%20passed-brightgreen" alt="Tests"></a>
  <a href="#"><img src="https://img.shields.io/badge/Python-3.9+-blue?logo=python" alt="Python"></a>
  <a href="#"><img src="https://img.shields.io/badge/platform-Codex%20%7C%20Claude%20Code-purple" alt="Platform"></a>
</p>

---

## 🤔 你有没有过这样的经历？

> "这个需求听起来不错，开干吧！"
>
> *—— 两周后 ——*
>
> "为什么选了 Vue？团队明明全是 React 熟手……"
> "谁决定的用 MongoDB？数据关系这么复杂……"
> "当初是怎么想的来着？？"

**你不是一个人。** 99% 的项目在启动时跳过了最关键的步骤：**系统性决策**。

因为做决策很难。需要调研、论证、对比、记录。而人都是懒惰的——写代码多爽啊。

**现在，让 AI 替你做好这件事。**

---

## 🎯 一句话说清

**Project Forge = AI 创意总监 + AI 架构师 + 工程脚手架**

在你写下第一行代码之前，它已经帮你完成了：

- ✅ 产品方向分析（面向谁？切哪个点？凭什么赢？）
- ✅ 证据收集与调研（GitHub / npm / PyPI / Web 搜索）
- ✅ 架构方案对比与 ADR（为什么选它而不是别的？）
- ✅ 工程 harness 契约（装什么、怎么测、怎么跑、怎么 CI）
- ✅ Superpowers 交接包（结构化 Markdown + JSON，可供下游消费）

**它不是代码生成器，它是"决定该生成什么代码"的决策引擎。**

---

## ⚡ 30 秒看懂

```mermaid
flowchart LR
    A[💭 模糊想法] -->|AI 创意总监| B[🎨 3个产品方向 + 推荐]
    B -->|AI 架构师| C[🔬 证据调研 + 候选对比]
    C -->|AI 架构师| D[📋 ADR 架构决策 + 置信度]
    D -->|工程脚手架| E[⚙️ 安装/测试/构建/CI 契约]
    E -->|就绪检查| F[📦 Superpowers 交接包]
```

```
输入：「我想做一个团队冲刺看板」
输出：创意简报 + 调研证据 + 架构决策 + CI 配置 + 交接包
```

---

## 🔥 为什么爆？

### 1️⃣ 这是 AI 编程时代最稀缺的能力

Cursor、Copilot、Claude Code 让"写代码"变得极其廉价。

但**"决定写什么代码"**反而变得极度稀缺和昂贵。

Project Forge 补上了 AI 编程工作流中缺失的**决策层**。

### 2️⃣ 和 Superpowers 完美分工

| | Project Forge | Superpowers |
|---|---|---|
| **管什么** | 方向、证据、架构、契约 | 规划、TDD、调试、代码审查、分支 |
| **产出什么** | creative-brief + ADR + project-forge.yaml + 交接包 | 可运行的代码 |
| **边界** | "该做什么？为什么？" | "怎么做？做得对吗？" |

**Forge 做决策，Superpowers 做实现。上下游关系，各司其职。**

### 3️⃣ 决策可追溯、可审计

每次运行都留下完整决策痕迹：

```
.project-forge/
├── history/          ← 每次运行的决策历史
├── backups/          ← 覆盖前的自动备份
└── verification/     ← superpowers-ready 检查报告
```

三个月后有人问"当初为什么选这个技术栈"，你不需要回忆，直接翻 ADR。

---

## 中文快速入门 · Quick Start

Project Forge 负责编码之前的产品方向、研究证据、架构决策、Harness 和 Superpowers 交接。

### 安装

```powershell
# Codex
git clone https://github.com/Haozhenyu123/project-forge.git
cd project-forge
python scripts/cli.py plugin install --host codex
python scripts/cli.py plugin verify --host codex

# Claude Code
python scripts/cli.py plugin install --host claude
python scripts/cli.py plugin verify --host claude
```

兼容个人 Marketplace 和 Claude Code 原生命令的安装材料也已包含在仓库中：
`install/codex-marketplace.personal.json`、`/plugin install $env:USERPROFILE\plugins\project-forge`。

### 第一次使用

```powershell
# 1. 预览（不写文件）
python scripts/cli.py init my-app --stack nextjs --goal "一个帮助小团队聚焦冲刺目标的仪表盘" --dry-run

# 2. 正式运行
python scripts/cli.py init my-app --stack nextjs --goal "一个帮助小团队聚焦冲刺目标的仪表盘"

# 3. 检查是否准备好交给 Superpowers
python scripts/cli.py superpowers-ready --slug my-app my-app

# 4. 看看生成了什么
ls my-app/docs/
# creative-brief.md          ← 产品方向分析
# architecture/ADR-0001-stack.md  ← 架构决策
# research/my-app/evidence.jsonl   ← 调研证据
# superpowers-handoff.md     ← 交接清单
# superpowers-handoff.json   ← 结构化交接包
```

---

## 🧰 命令一览

| 命令 | 作用 | 什么时候用 |
|---|---|---|
| `init` | 从想法到决策全覆盖 | 新项目启动 |
| `detect . --json` | 识别已有项目的技术栈 | 接手老项目 / 做架构审计 |
| `inspect . --json` | 审查项目结构（不执行代码） | 快速了解陌生仓库 |
| `research --query "..."` | 针对架构问题做调研 | 技术选型纠结时 |
| `harness compose` | 编排多技术栈混合项目 | 前后端分离 / monorepo |
| `superpowers-ready` | 检查交接包是否就绪 | 交付前最后一步验证 |
| `doctor` | 检查安装和运行时环境 | 遇到问题时排查 |
| `backups / restore` | 备份和恢复决策文件 | 回滚某个决策 |

---

## 📦 支持的技术栈（8 个模板）

| 模板 | 技术栈 | 自动检测信号 |
|---|---|---|
| `nextjs` | Next.js App Router | `package.json` 含 `next` 依赖 |
| `fastapi` | FastAPI | `pyproject.toml` / `main.py` 特征 |
| `electron` | Electron 桌面应用 | `package.json` 含 `electron` 依赖 |
| `cli` | Node.js CLI 工具 | `package.json` 含 `bin` 字段 |
| `chrome-extension` | Chrome 扩展 MV3 | `manifest.json` 存在 |
| `node-ts` | Node.js + TypeScript | `package.json` 存在 |
| `python` | Python 通用 | `pyproject.toml` / `requirements.txt` |
| `generic` | 任意技术栈 | 手动指定（兜底） |

---

## 🛡️ 安全第一

我们**默认保守**，因为决策文件也是你的重要资产：

- 🔒 已有文件**默认不覆盖**，`--force` 会先自动备份
- 🔍 `--dry-run` 预览所有操作，不写任何文件
- 📜 每次成功运行记录完整决策历史
- 🚫 没有网络时**不编造证据**，标注为 provisional
- ⚠️ `superpowers-ready` 默认只做结构检查，`--execute` 才执行命令
- 🛑 `--strict` 模式下，警告也视为失败，确保零问题交接

---

## 🎬 真实案例

```powershell
# 案例：一个模糊的想法 —— "团队需要更好的研究协作工具"
python scripts/cli.py init team-research --stack node-ts --goal "团队研究决策与引文管理"
```

产出物：

```
examples/team-research/
├── docs/
│   ├── creative-brief.md              ← 「面向 5-30 人工程团队的研究决策工具」
│   ├── research/team-research/evidence.jsonl  ← 结构化调研证据
│   ├── architecture/ADR-0001-stack.md  ← Node.js + TS，Why Not Python/FastAPI
│   ├── harness.md                      ← 安装 → 测试 → 构建 → 冒烟
│   ├── superpowers-handoff.md          ← Markdown 交接包
│   └── superpowers-handoff.json        ← 结构化交接包（JSON Schema）
├── project-forge.yaml                  ← 命令契约
└── .github/workflows/project-forge-ci.yml  ← CI 配置
```

**从一句话到完整、可审计、可交接的决策包。**

👉 更多案例：`examples/fastapi-demo`、`examples/nextjs-fastapi-demo`、`examples/chrome-extension-demo`、`examples/cli-demo`

---

## 🗺️ 架构全景

```
你的想法
  │
  ├─ forge-intake (skill)         ← 澄清目标、范围、约束
  │
  ├─ creative-director (skill)    ← 产品方向 × 3，选最佳
  │
  ├─ ai-architect (skill)         ← 证据调研 + 方案对比 + ADR
  │
  ├─ harness-engineer (skill)     ← 模板应用 + 命令契约 + CI
  │
  ├─ forge-project (skill)        ← 协调器：整合所有产出
  │
  └─ 输出 ────────────────────────→ Superpowers 接手实现
```

每个 Skill 之间是**显式传递关系**，上一个产出会自动衔接到下一个输入。不需要调度器——Skill 自己告诉宿主下一步该调谁。

---

## ✅ Verify · 质量保证

```powershell
# 运行全部测试（132 个，当前全通过 ✅）
python -m pytest tests/ -q

# 兼容 unittest 的核心测试入口
python -m unittest tests/test_project_forge.py

# 安装验证（12 项检查）
python scripts/install_test.py

# 评估场景验证
python scripts/evals/validate_scenarios.py evals/scenarios

# 交接包就绪检查
python scripts/cli.py superpowers-ready --slug team-research examples/team-research

# 全面验证
make verify
```

---

## 🔄 Update · 更新

```powershell
git pull origin main
python scripts/cli.py plugin update --host codex
python scripts/cli.py plugin verify --host codex
python scripts/cli.py doctor
```

Claude Code 使用相同流程，将 `--host codex` 替换为 `--host claude`。

---

## 🤝 贡献

欢迎贡献！大方向：

- 🧩 **新模板**：让 Project Forge 支持更多技术栈
- 🔬 **新证据源**：接入更多数据源（bundlephobia、CVE、Stack Overflow trends 等）
- 🎯 **Eval 场景**：贡献压力测试用例
- 🐛 **Bug 修复 & 文档改进**

详见 [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📜 License · 许可证

MIT © [Haozhenyu123](https://github.com/Haozhenyu123)

---

<p align="center">
  <b>写代码之前，先锻造你的决策。</b><br>
  <sub>Your architecture deserves more than a 3am Slack decision.</sub>
</p>

<p align="center">
  ⭐ Star 这个项目，如果你也觉得「先想清楚再写代码」是正道
</p>
