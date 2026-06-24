# Project Forge v0.4.0 全维度技术拆解与从零教学

> **适合读者**：Python 3.9+ 零基础到中级、想理解"AI 驱动的架构决策引擎"如何从零搭建的开发者
> **阅读时长**：完整阅读约 60-90 分钟
> **前置知识最低门槛**：会用 Python 写简单的函数和类即可

---

## 一、项目全局认知与架构全景

### 1.1 项目价值与业务逻辑

#### 它解决了什么真实痛点？

在 AI 编程时代，Cursor、Copilot、Claude Code 让"写代码"变得极其廉价。但出现了一个新问题：**"谁来决定写什么代码？"**

真实场景：团队拿到需求就开始写代码，两周后发现技术选型错了、架构不合理、产品方向跑偏——因为没有人系统性地做过**前置决策**。

**Project Forge 定位**：它不是代码生成器，它是"在写第一行代码之前，帮你完成产品方向、证据调研、架构决策、工程契约、交接包生成"的**决策引擎**。

#### 核心业务流转（闭环）

```
模糊想法
  ↓ [AI 创意总监] → 3 个产品方向 + 推荐方向
  ↓ [证据收集器] → GitHub / npm / PyPI / Web 搜索
  ↓ [AI 架构师] → 9 维度评分对比 → ADR 架构决策
  ↓ [工程脚手架] → Harness 契约 (install/test/lint/build/run/smoke)
  ↓ [就绪检查] → Superpowers 交接包 (Markdown + JSON)
  ↓ [v0.4.0 Loop] → 接收实现反馈 → 自动修订 → 新交接包（闭环）
```

#### 业务关键词解释

- **Creative Direction**（创意方向）：产品应该面向谁、切哪个市场、凭什么赢——不是代码层面的事，是商业决策
- **ADR**（Architecture Decision Record）：架构决策记录，永久记录"为什么选了技术 A 而不是 B"
- **Harness**：工程契约，规定项目必须能 install、test、lint、typecheck、build、run、smoke 七步走
- **Superpowers Handoff**：交接包，下游 AI 编码 Agent（如 Claude Code）直接消费的结构化指令
- **Decision Loop**：反馈闭环——当实现过程中发现架构假设不对，自动回到 Forge 修订

### 1.2 架构分层与模块划分

Project Forge 采用**领域驱动模块化**（非严格分层，而是按业务领域拆包）：

```
                     ┌──────────────────────────────┐
                     │     CLI (scripts/cli.py)      │  ← 用户入口
                     └────────────┬─────────────────┘
                                  │
          ┌───────────────────────┼───────────────────────┐
          │                       │                       │
    ┌─────▼──────┐    ┌──────────▼──────────┐   ┌────────▼───────┐
    │  Creative   │    │     Decision        │   │   Loop        │ ← v0.4.0
    │  Director  │    │     Engine          │   │   Engine      │
    │  (产品方向) │    │  (架构决策)          │   │  (反馈闭环)    │
    └─────┬──────┘    └──────────┬──────────┘   └────────┬───────┘
          │                       │                       │
          │    ┌──────────────────┼───────────────┐       │
          │    │                  │               │       │
     ┌────▼────▼──┐   ┌──────────▼──┐   ┌───────▼───┐   │
     │  Evidence  │   │   Harness   │   │  Handoff  │◄──┘
     │  (证据)    │   │  (工程契约)  │   │  (交接包)  │
     └────────────┘   └─────────────┘   └───────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
        ┌─────▼────┐  ┌─────▼─────┐  ┌─────▼─────┐
        │ Inventory│  │ Readiness │  │  Hosts    │
        │(项目扫描) │  │ (就绪检查) │  │(宿主适配) │
        └──────────┘  └───────────┘  └───────────┘
```

**模块职责边界**：

| 模块 | 文件 | 职责 | 不负责 |
|------|------|------|--------|
| `creative/` | `models.py`, `service.py`, `signals.py` | 基于目标+约束生成 3 个产品方向并评分推荐 | 写代码、选技术栈 |
| `evidence/` | `models.py`, `providers.py`, `normalize.py`, `tiers.py` | 从 GitHub/npm/PyPI/OSV 等数据源采集证据，标准化并去重 | 做决策 |
| `decision/` | `engine.py`, `scoring.py`, `catalog.py`, `patterns.py` | 9 维度评分所有候选技术栈，输出 ADR | 产生证据 |
| `harness/` | `composer.py`, `executor.py`, `ci.py`, `templates.py`, `lifecycle.py` | 生成工程契约，执行命令验证 | 决定架构 |
| `handoff/` | `service.py` | 生成 Markdown + JSON 交接包 | 实现代码 |
| `loop/` | `models.py`, `signals.py`, `state_machine.py`, `strategy.py`, `impact.py`, `convergence.py`, `storage.py`, `report.py`, `service.py` | 接收反馈信号→评估影响→自动修订→新交接包（闭环） | 写应用代码、执行命令 |
| `inventory/` | `scanner.py`, `cli.py`, `render.py` | 扫描项目文件结构，生成 JSON/Mermaid 拓扑 | 修改代码 |
| `readiness/` | `service.py` | 检查所有产物是否存在+合规+可执行 | 修复代码问题 |
| `hosts/` | `models.py`, `service.py`, `bundles.py` | 管理 Codex/Claude Code 宿主的插件安装和版本 | 定义宿主能力 |
| `evals/` | `compatibility.py`, `models.py` | Agent 评估框架 | 替代 Superpowers |

### 1.3 技术全景地图

```
┌─ 表现层 ─────────────────────────────────────────────────────┐
│  CLI (argparse)           │  MCP Server (stdio JSON-RPC)     │
│  project-forge init/detect/│  tools: github_search,          │
│  research/handoff/loop/... │  web_search, detect_stack,      │
│  15 个子命令                │  superpowers_ready, etc.       │
├─ 业务逻辑层 ─────────────────────────────────────────────────┤
│  Creative Director         │  Decision Engine               │
│  - 3 方向评分              │  - 9 维度加权评分              │
│  - evidence 置信度关联     │  - 冲突检测                    │
│                            │  - ADR 生成                    │
│  Loop Engine (v0.4.0)      │  Evidence Pipeline             │
│  - 状态机 (8 状态)         │  - 7 个 Provider               │
│  - 信号路由                │  - 标准化+指纹去重             │
│  - 收敛检测                │  - 质量分级                    │
│  - 自动修订                │                                │
├─ 工程层 ────────────────────────────────────────────────────┤
│  Harness Composer          │  Readiness Checker             │
│  - 7 命令契约              │  - 结构化检查                  │
│  - 模板渲染                │  - 执行验证                    │
│  - CI 生成                 │  - 分级通过                    │
├─ 数据持久层 ────────────────────────────────────────────────┤
│  project-forge.yaml (Schema v2)   │  原子文件存储 (.tmp→os.replace)  │
│  evidence.jsonl (JSON Lines)      │  备份+回滚                      │
│  状态文件: state.json / runs/ / inbox/ / processed/                │
├─ 基础设施层 ─────────────────────────────────────────────────┤
│  Python 3.9+      │  setuptools   │  pytest      │  GitHub Actions   │
│  stdlib only      │  ruff + mypy  │  unittest    │  三平台 CI 矩阵   │
│  (无运行时依赖)    │  (静态检查)    │  184 测试    │  decision-drift   │
└──────────────────────────────────────────────────────────────────┘
```

**关键技术决策**：整个项目**零运行时依赖**。`dependencies = []` 意味着 pip install project-forge 不需要下载任何第三方包。这是架构层面的刻意选择——降低安装摩擦、消除依赖冲突风险。验证用 PyYAML + jsonschema 是可选的 opt-in。

---

## 二、技术栈选型深度解析

### 2.1 语言：Python 3.9+

#### 技术本质定位

Python 是一门**动态类型、解释执行的通用高级语言**。它的核心设计哲学是"可读性优先"（`import this` 可以看到 Python 之禅）。在工程工具领域，Python 的优势在于：脚本化部署零成本、跨平台开箱即用、CI 集成简单。

#### 选型决策

| 维度 | Python | Node.js/TypeScript | Go |
|------|--------|--------------------|----|
| **开发效率** | ★★★★★ 极快，适合快速迭代 | ★★★★ 需编译/构建步骤 | ★★★ 编译慢，不适合脚本型工具 |
| **零依赖部署** | ★★★★★ 标准库极丰富（urllib/http/json/subprocess/pathlib/dataclasses） | ★★★ 标准库弱，需 npm 依赖 | ★★★★ 编译成单二进制，但工具链重 |
| **AI/ML 生态** | ★★★★★ LangChain、RAG 工具链全在 Python | ★★ AI 生态弱 | ★★ |
| **跨平台 CI** | ★★★★★ GitHub Actions ubuntu/macos/windows 原生支持 | ★★★★ | ★★★★ |
| **项目适配性** | ★★★★★ CLI 工具类项目最佳语言 | ★★★ 适合 Web 服务 | ★★ 更适合系统级工具 |
| **团队维护成本** | ★★★★ 易读易维护 | ★★★ 类型系统增加复杂度 | ★★★ |

**核心取舍**：选了 Python 的"开箱即用"和 AI 生态，牺牲了编译型语言的性能和类型安全。但在 CLI 工具场景中，IO 等待远比 CPU 计算多，性能劣势可以忽略。类型安全通过 mypy（可选）+ dataclass 弥补。

#### 版本选择：3.9+

- **选择理由**：3.9 是首个稳定支持 `dataclasses` 字段默认值完美工作、`zoneinfo` 时区处理、`pathlib` 完整文件操作的版本
- **不用更高版本**：3.10 的 match-case、3.11 的性能提升在这个项目中不是刚需，向下兼容更重要
- **不用更低版本**：3.8 的 dataclass 和类型提示有兼容问题

### 2.2 项目核心：dataclass + Enum（数据模型层）

#### 技术本质定位

`@dataclass` 是 Python 3.7+ 引入的装饰器，**自动为你生成 `__init__`、`__repr__`、`__eq__` 方法**。它解决的是：你定义了一个数据类，却要手写几十行样板代码的问题。

```python
# 不用 dataclass（Python 传统做法）
class StackContract:
    def __init__(self, id="", template="", ...):
        self.id = id
        self.template = template
        # 手写 20 行赋值...

# 用 dataclass（Project Forge 的做法）
@dataclass
class StackContract:
    id: str = ""
    template: str = ""
    # 自动生成 __init__, __repr__, __eq__
```

`Enum` 解决的是：当状态只有几种合法值时（如 `IDLE/COLLECTING/EVALUATING/...`），**字符串拼写错误在运行时才能发现**。Enum 让拼写错误变成语法错误。

#### 在项目中的落地模式

Project Forge 大量使用一种**"Model + to_dict + from_dict"模式**：

```python
@dataclass
class LoopSignal:
    signal_id: str
    kind: SignalKind          # ← 类型安全：只能用 SignalKind 枚举
    severity: SignalSeverity  # ← 同上
    fingerprint: str = ""    # ← 有默认值的可选字段放后面

    def __post_init__(self):  # ← dataclass 特殊钩子：构造后自动执行
        if not self.fingerprint:
            self.fingerprint = self._compute_fingerprint()

    def to_dict(self) -> Dict:   # ← 序列化：Python 对象 → JSON
        ...

    @classmethod
    def from_dict(cls, data) -> "LoopSignal":  # ← 反序列化：JSON → Python 对象
        ...
```

**设计亮点**：`__post_init__` 钩子自动计算指纹，开发者不需要主动调用——创建对象即完成去重标记。

### 2.3 构建系统：setuptools + pyproject.toml

#### 技术本质

`pyproject.toml` 是 Python 生态的统一项目配置文件（PEP 518/621），它替代了过去混乱的 `setup.py`/`setup.cfg`/`MANIFEST.in` 三件套。`setuptools` 是 Python 最老牌、最广泛使用的打包构建工具。

#### 选型理由

- **不用 Poetry**：Poetry 更现代但增加学习成本，Project Forge 零运行时依赖不需要复杂的依赖解析
- **不用 Flit**：Flit 更简洁但生态支持不如 setuptools 广泛
- **不用 Hatchling**：太新，CI 环境兼容性风险

```toml
[build-system]
requires = ["setuptools>=68"]       # 构建系统自己的依赖
build-backend = "setuptools.build_meta"

[project]
name = "project-forge"
version = "0.4.0"
requires-python = ">=3.9"
dependencies = []                   # ← 核心：零运行时依赖

[tool.setuptools.packages.find]
where = ["src"]                     # ← src/ 布局：源码与配置分离
```

**src/ 布局的好处**：强制你必须先 `pip install -e .` 才能 import，避免直接在项目根目录 import 导致隐式路径依赖。这是 Python 社区推荐的最佳实践。

### 2.4 证据基础设施：标准库 urllib + JSON Lines

#### 技术选型逻辑

Project Forge 的证据采集器（providers.py）完全基于 Python 标准库 `urllib.request`，没有用 `requests`。

| 对比 | urllib（本项目） | requests |
|------|------------------|----------|
| **安装** | 零依赖，标准库自带 | `pip install requests` |
| **API 简洁性** | 较繁琐，需手写 headers | 极其简洁 |
| **连接池/重试** | 需自己实现 | 内置 |
| **JSON 支持** | 需 `json.loads(response.read())` | `response.json()` 一行 |

**核心取舍**：牺牲 API 便利性，换取零依赖。在工具类项目中，安装摩擦是致命伤——用户不会为了用你的工具先解决依赖冲突。且所有 Provider 都通过 `Transport` 协议抽象，未来随时可以注入 requests 替换。

**设计亮点**：`Transport` 协议（Protocol）允许测试时注入 mock，避免了真正的 HTTP 调用。这是典型的"依赖倒置"。

### 2.5 证据存储：JSON Lines (.jsonl)

#### 为什么不是 SQLite/纯 JSON？

| 模式 | 优点 | 缺点 |
|------|------|------|
| **JSON Lines** | 可追加写入、可逐行流读、Git diff 友好、人类可读 | 不支持复杂查询 |
| **纯 JSON 数组** | 一次读写 | 追加需重写整个文件、Git diff 整个文件冲突 |
| **SQLite** | 支持查询、事务 | 引入 C 扩展依赖、二进制不可 diff |

对于**证据记录——每行独立、主要操作是追加和顺序读取**的场景，JSON Lines 是最小阻力方案。

```jsonl
{"evidence_id":"gh-1","title":"React","stars":230000,"observed_at":"2026-06-20"}
{"evidence_id":"gh-2","title":"Vue","stars":220000,"observed_at":"2026-06-20"}
```

### 2.6 CLI 框架：argparse（标准库）

#### 为什么不选 Click/Typer？

Click 和 Typer 提供更优雅的装饰器式 CLI 定义，但它们都是第三方依赖。对于 15 个子命令的 CLI，argparse 完全够用。

**项目中的高级用法**：

```python
# 嵌套子命令：loop → run / ingest / status / resume
loop_parser = subparsers.add_parser("loop")
loop_sub = loop_parser.add_subparsers(dest="loop_command", required=True)
loop_run = loop_sub.add_parser("run", help="Run one loop iteration")
loop_run.add_argument("--slug", required=True)
loop_run.add_argument("--json", action="store_true")
```

`required=True` 确保不输入子命令时直接报错，而不是静默 fallback。

### 2.7 状态机引擎：显式转移表（Loop Engine v0.4.0）

#### 技术本质

状态机（Finite State Machine）是一种计算模型：系统在任何时刻只能处于一个确定的状态，状态的改变（转移）由明确定义的事件触发。

**常见错误做法**：用一大串 if/elif 散落在代码各处管理状态。

**Project Forge 的做法**：集中定义一个**转移表**：

```python
TRANSITIONS: Set[Tuple[LoopStatus, LoopStatus]] = {
    (LoopStatus.IDLE, LoopStatus.COLLECTING),       # 空闲 → 收集信号
    (LoopStatus.COLLECTING, LoopStatus.EVALUATING),  # 收集完了 → 评估
    (LoopStatus.EVALUATING, LoopStatus.REVISING),    # 评估完了 → 修订
    (LoopStatus.EVALUATING, LoopStatus.BLOCKED),     # 评估不了 → 阻塞
    # ... 共 16 条合法转移
}
```

**核心设计思想**：状态管理应该是一张表，不是一堆散落的条件判断。转移函数在每次状态变更时做守卫检查，非法转移直接抛异常，**让状态 bug 在开发阶段就暴露**。

### 2.8 测试：unittest + pytest

#### 为什么同时用两个？

| 工具 | 角色 |
|------|------|
| `unittest` | CI 中的 `python -m unittest` 零依赖执行 |
| `pytest` | 本地开发时 `python -m pytest` 获得更清晰的输出 |

项目故意不依赖 pytest 运行——CI 用的是 `python -m unittest discover`，确保即使 pytest 未安装也能跑通。

### 2.9 静态检查：ruff + mypy（可选依赖）

```
[project.optional-dependencies]
dev = ["ruff>=0.5", "mypy>=1.10", "PyYAML>=6,<7", "jsonschema>=4,<5"]
```

**ruff**：用 Rust 写的 Python linter，比 Flake8 快 10-100 倍，用 `[tool.ruff]` 段配置。  
**mypy**：Python 可选类型检查器，配置 `check_untyped_defs = true` 确保即使在无类型注解的函数里也做推理。

这两个是开发工具，不进入 `dependencies`。用户安装 Project Forge 不需要它们。

---

## 三、全量知识点从零系统化教学

### 3.1 dataclass 深入

#### 前置知识
- Python 类的基本写法（`class Foo: def __init__(self, x): self.x = x`）
- 类型注解基础（`name: str = ""`）

#### 核心原理解析

`@dataclass` 是 Python 的**代码生成装饰器**。当解释器遇到这个装饰器时，它读取类的字段定义（带类型注解的类变量），自动生成以下方法的字节码，注入到类中：

1. `__init__`：按字段声明顺序接收参数（必选在前，有默认值的在后）
2. `__repr__`：返回可读的字符串表示（如 `LoopSignal(signal_id='test-1', kind='manual')`）
3. `__eq__`：按值比较（两个对象字段全等则为 True）
4. 如果 `frozen=True`，还会生成 `__hash__`，让对象可放入 set/dict

**容易踩的坑**：默认值不能是可变对象！

```python
# ❌ 错误：所有实例共享同一个 list
@dataclass
class Foo:
    items: list = []  # ← Python 3.9 会报错，3.10+ 可以但行为不对

# ✅ 正确：用 field(default_factory=list)
@dataclass
class Foo:
    items: list = field(default_factory=list)
```

`field(default_factory=list)` 的含义：**每次创建新实例时，调用 `list()` 生成一个新的空列表**。

#### 在项目中的作用

Project Forge 的所有数据模型（约 15 个 dataclass）全部使用这种模式。它们构成了一层"类型安全的数据传输层"——任何模块之间传递的都是具类型的对象而非裸 dict。

---

### 3.2 Enum 枚举深入

#### 为什么要用 Enum？

```python
# ❌ 传统做法：字符串魔法值
status = "blocked"
if status == "blocked":     # 拼写错误 'blocked' 写成 'bloked' 不会报错！
    ...

# ✅ Enum 做法
class LoopStatus(str, Enum):
    BLOCKED = "blocked"

status = LoopStatus.BLOCKED   # 拼写错误 IDE 立刻标红
if status == LoopStatus.BLOCKED:
    ...
```

**项目设计技巧**：继承 `str` 而非纯 `Enum`，让枚举值可以直接当字符串用：

```python
class LoopStatus(str, Enum):
    IDLE = "idle"

status = LoopStatus.IDLE
json.dumps({"status": status})  # {"status": "idle"}，不需要 .value
f"Current: {status}"            # "Current: idle"
```

---

### 3.3 合约模式（Contract Pattern）

#### 核心概念

**合约（Contract）**是一个软件设计模式：两个模块之间的交互，不靠口头约定或"读代码猜"，而是通过一份**结构化、可验证的文档**来定义。

在 Project Forge 中，`project-forge.yaml` 就是合约：

```yaml
schema_version: 2
project:
  slug: "my-project"
  goal: "Build a dashboard"
stacks:
  primary:
    id: "primary"
    template: "node-ts"
    commands:
      install: {argv: ["npm", "install"], cwd: "."}
      test: {argv: ["npm", "test"], cwd: "."}
      # ... 7 个命令
```

**合约的可验证性**：`Contract.validate()` 方法会检查所有必选命令是否存在、slug 是否填写。任何时候加载合约，如果不符合 Schema，立刻报错——不让坏数据在系统中传播。

---

### 3.4 策略模式（Strategy Pattern）在评分引擎中的应用

#### 问题

评分一个技术栈需要 9 个维度（约束匹配、证据新鲜度、来源多样性、维护活跃度、许可证、安全风险、部署成本、复杂度、Harness 可用性），每个维度的计算方法完全不同。

#### 解决方案

```python
# 每个维度一个独立的评分函数
DIMENSIONS = (
    "constraint_fit", "evidence_freshness", "source_diversity",
    "maintenance_activity", "license", "security_risk",
    "deployment_cost", "complexity", "harness_availability",
)

def score_stack(stack, desired, evidence, weights, as_of):
    dimensions = {
        "constraint_fit": _fit(stack, desired, weights),      # ← 策略函数
        "evidence_freshness": _freshness(matched, weights, as_of),
        # ...
    }
    total = round(sum(v.score * v.weight for v in dimensions.values()), 2)
    return {"total": total, "dimensions": {...}}
```

**核心设计**：每个维度是独立的、可替换的策略函数。如果你以后想改变"复杂度"的评分算法，只改 `_complexity` 函数，不影响其他维度。

---

### 3.5 文件原子操作

#### 为什么重要

假设你在写 `state.json`，写到一半程序崩溃了——文件损坏，下次启动读不到有效状态。原子操作保证：要么是旧文件，要么是完整的新文件，不存在中间态。

```python
def atomic_write(path, text):
    tmp = path.with_suffix(path.suffix + ".tmp")  # 先写临时文件
    tmp.write_text(text, encoding="utf-8")
    os.replace(str(tmp), str(path))                # 原子替换（OS 级别保证）
```

`os.replace` 在 POSIX 系统上是 `rename()`，在 Windows 上是 `MoveFileEx(MOVEFILE_REPLACE_EXISTING)`，两者都由操作系统保证原子性。

**项目的三层安全**：写入前先备份 → 写入临时文件 → 原子替换。任何一步失败都可以回滚。

---

## 四、技术在项目中的落地运用详解

### 4.1 证据管线的完整流程

```
用户输入 goal: "build a team dashboard"
      │
      ▼
┌─────────────────────────────────────────────────────┐
│  1. Web Search (Google/Bing)                        │
│     scripts/research/web_search.py                  │
│     → 返回 5 条关于 "team dashboard" 的搜索结果      │
│     → 写入 evidence/web.jsonl                        │
├─────────────────────────────────────────────────────┤
│  2. GitHub Search                                   │
│     scripts/research/github_search.py               │
│     → 搜索 match goal 的开源仓库                     │
│     → 写入 evidence/github.jsonl                     │
├─────────────────────────────────────────────────────┤
│  3. 标准化 (Normalization)                          │
│     scripts/research/normalize_evidence.py           │
│     → 统一格式 (evidence_id, source, title, url...)  │
│     → 计算指纹 (SHA256 去重)                         │
│     → 打质量标签 (primary/registry/unverified)        │
│     → 写入 evidence/normalized.jsonl                 │
├─────────────────────────────────────────────────────┤
│  4. 接入决策引擎                                   │
│     decision/engine.py 读取 normalized 证据          │
│     → 每条证据通过 evidence_for_stack() 匹配到       │
│       对应的技术栈                                   │
│     → 参与 9 维度评分                                │
└─────────────────────────────────────────────────────┘
```

**关键代码——证据与栈的匹配**：

```python
def evidence_for_stack(rows, stack):
    aliases = {stack.id.lower(), stack.name.lower(), *stack.aliases}
    matched = []
    for row in rows:
        text = " ".join(str(row.get(k, "")) for k in ("title","summary","description","url","source")).lower()
        explicit = {str(item).lower() for item in row.get("evidence_for", [])}
        if stack.id.lower() in explicit or any(alias in text for alias in aliases):
            matched.append(row)
    return matched
```

**两个匹配路径**：
1. `evidence_for` 显式标注——强信号
2. 文本中关键词匹配——弱信号（如证据里提到 "react"，自动关联到 node-ts 栈）

### 4.2 决策引擎评分实战

9 个维度的权重（可配置）：

| 维度 | 权重 | 含义 |
|------|------|------|
| constraint_fit | 25% | 技术栈能力与项目需求的匹配度 |
| evidence_freshness | 12% | 最新证据的时间新鲜度（≤90天=满分） |
| source_diversity | 8% | 证据来源的多样性 |
| maintenance_activity | 12% | 社区活跃度 |
| license | 8% | 许可证风险（AGPL/GPL 扣分） |
| security_risk | 10% | 安全漏洞数量（OSV 查询） |
| deployment_cost | 8% | 部署成本和复杂度 |
| complexity | 10% | 技术栈复杂度 |
| harness_availability | 7% | Project Forge 模板覆盖度 |

**maturity 惩罚机制**：如果技术栈的市场存在时间少于 18 个月，总分乘以 0.45 的惩罚因子。

```python
if int(stack.baselines.get("maturity_months", 0)) < 18:
    total = round(total * 0.45, 2)
```

这是**工程判断的量化**：太新的技术文档少、社区小、踩坑成本高。

### 4.3 Loop Engine 状态机实战

完整的生命周期流转：

```
ingest_signal ──→ inbox/xxx.json
       │
       ▼
  [IDLE] ──→ [COLLECTING] ──→ [EVALUATING]
                                    │
                          ┌─────────┴──────────┐
                          ▼                     ▼
                     [REVISING]            [BLOCKED]
                          │                     │
                          ▼                     ▼
                  [HANDOFF_READY]         resume_loop
                          │                     │
                          ▼                     │
               [AWAITING_FEEDBACK] ◄────────────┘
                          │
                    新信号到来
                          │
                          ▼
                    [COLLECTING] （新一轮迭代）
```

**信号路由决策**：

```python
FORGE_KINDS = {
    SignalKind.CONSTRAINT_CHANGE,     # 约束变了 → Forge 重新评估架构
    SignalKind.EVIDENCE_EXPIRY,       # 证据过期 → Forge 刷新证据
    SignalKind.SECURITY_ADVISORY,     # 安全漏洞 → Forge 考虑栈切换
    SignalKind.LICENSE_CONFLICT,      # 许可冲突 → Forge 考虑栈切换
}

SUPERPOWERS_KINDS = {
    SignalKind.VERIFICATION_FAILURE,   # 测试挂了 → Superpowers 修代码
    SignalKind.ARCHITECTURE_FEEDBACK,  # 架构反馈 → 先看是不是实现问题
    SignalKind.SUPERPOWERS_FEEDBACK,   # 通用反馈 → Superpowers
}
```

**收敛检测**——避免无限循环：

```python
@property
def has_stale_progress(self) -> bool:
    if len(self.iterations) < 2:
        return False
    last_two = self.iterations[-2:]
    return (last_two[0].decision_hash == last_two[1].decision_hash
            and last_two[1].action != "reroute")
```

两轮连续出相同决策哈希但问题未解决 → 陷入死循环 → 自动 `blocked`，等待人工介入。

### 4.4 Harness 合约生成与执行

**生成阶段**：`harness/composer.py` 根据选择的栈模板渲染：

```yaml
# 从 templates/harness/node-ts/project-forge.yaml 模板生成
stacks:
  primary:
    template: "node-ts"
    commands:
      install: {argv: ["npm", "install"]}
      test: {argv: ["npm", "test"]}
      lint: {argv: ["npm", "run", "lint"]}
      # ...
```

**执行阶段**：`harness/executor.py` 的安全策略：

```python
# 安全策略 1：cwd 不能逃逸项目目录
cwd = (Path(project_root) / spec.cwd).resolve()
try:
    cwd.relative_to(project)
except ValueError:
    raise ExecutionBlocked("command cwd escapes project")

# 安全策略 2：禁止 legacy shell 字符串
if spec.legacy_shell and not allow_legacy_shell:
    raise ExecutionBlocked("legacy shell command requires --allow-legacy-shell")

# 安全策略 3：每命令独立超时 + 强制终止
proc = subprocess.Popen(argv, ...)
try:
    stdout, stderr = proc.communicate(timeout=timeout)
except subprocess.TimeoutExpired:
    _terminate(proc)  # taskkill /T /F on Windows, SIGTERM on Unix
```

**设计理念**：Harness 执行器对所有命令都做三层防御——路径逃逸检测、Shell 注入防御、超时强制终止。

---

## 五、常见问题与踩坑复盘

### 5.1 Python 编码问题（BOM、GBK）

**症状**：Windows 上写入中文文件，测试报 `AssertionError: file is missing YAML frontmatter`

**根因**：`Out-File -Encoding utf8` 在 PowerShell 中默认带 BOM (`\ufeff`)。Python 的 `text.startswith("---\n")` 匹配不到以 BOM 开头的文件。

**排查方法**：
```python
with open(path, 'rb') as f:
    first_bytes = f.read(3)
    if first_bytes == b'\xef\xbb\xbf':
        print("文件有 BOM！")
```

**本项目的解决方案**：所有 skill 文件和输出文件必须用"UTF-8 without BOM"写入：
```python
[System.IO.File]::WriteAllText($file, $content, (New-Object System.Text.UTF8Encoding $false))
```

### 5.2 dataclass 可变默认值陷阱

**症状**：修改一个 LoopEpisode 的 `iterations` 列表，另一个不相干的 Episode 也被改了。

**根因**：
```python
# ❌ 错误——所有实例共享同一个 list 对象
@dataclass
class LoopEpisode:
    iterations: List = []  # ← 这是类级别的可变对象！

# ✅ 正确
@dataclass
class LoopEpisode:
    iterations: List = field(default_factory=list)
```

**排查**：用 `id(obj.iterations)` 检查两个实例的列表是否指向同一块内存。

### 5.3 字符串枚举比较陷阱

**症状**：信心检查永远返回 `False`，即使 confidence 是 `"high"`。

**根因**：`"high" < "medium"` 在字符串比较中是**字典序**，`'h' < 'm' → True`，但 `"high" < "low"` 也是 `True`（因为 `'h' < 'l'`）。

**本项目修复**：引入数值映射 `{"high": 3, "medium": 2, "low": 1}`，比较数值而非字符串。

### 5.4 原子写入的 Windows 兼容性

**症状**：`os.replace(tmp, target)` 在 Windows 上偶尔报 `PermissionError`。

**根因**：如果目标文件正被另一个进程（如杀毒软件、文件索引）持有，Windows 不允许替换。

**缓解方案**：本项目不做额外处理——这种情况概率极低，且属于操作系统层面的问题。如果未来遇到，可加 3 次重试+短暂 sleep 的退避策略。

### 5.5 多模块循环导入

**症状**：`ImportError: cannot import name 'LoopEpisode' from partially initialized module`

**根因**：模块 A `from .B import X`，模块 B `from .A import Y`，形成循环。

**本项目的规避**：所有 `from .xxx import` 都放在函数体内而非模块顶层（lazy import），打破导入时循环：

```python
# service.py 中的做法
def _apply_revision(project, slug, signal, impact, policy):
    from project_forge.decision.engine import build_decision  # ← 函数内导入
    from project_forge.contract import load_contract
    ...
```

### 5.6 项目级安全风险与防御

| 风险 | 防御措施 |
|------|---------|
| Loop 写入应用代码 | `policy.allow_application_writes = False`，Loop service 只操作 Forge 归档目录 |
| 执行恶意 shell | `allow_legacy_shell` 默认 false，必须是结构化的 `argv` |
| 路径穿越 | `cwd.relative_to(project)` 验证 cwd 不逃逸项目目录 |
| 状态文件损坏 | `atomic_write` + `backup_file` 双重保障 |
| 信号重复处理 | SHA256 指纹去重，`processed/` 目录归档 |
| 无限循环 | 最大 3 轮迭代上限，两轮同哈希自动 blocked |

### 5.7 通用排查方法论

**当测试失败时，按以下顺序排查**：

1. **先读测试名**：`test_xxx` 的 xxx 就是失败原因的关键词
2. **看 `AssertionError` 的 diff**：`-` 是预期值，`+` 是实际值，直接告诉你偏差在哪
3. **检查文件编码**：Windows 上的中文问题 80% 是 BOM/GBK/UTF-8 之争
4. **检查 import**：如果 `ImportError`，先确认 `sys.path` 有没有加 `src/`
5. **检查版本号**：CLI、plugin manifest、MCP server、package.json 四处版本号必须同步

---

## 六、项目拓展与进阶思考

### 6.1 性能优化方向

| 优化项 | 当前状态 | 优化路径 | 预期收益 |
|--------|---------|---------|---------|
| 证据采集并行化 | 串行请求 | `concurrent.futures.ThreadPoolExecutor` 并行搜 GitHub+npm+PyPI | 搜索时间从 10s 降到 2s |
| 评分缓存 | 每次重新计算 | 基于 decision_hash 缓存历史评分结果 | 重复评估几乎零耗时 |
| 文件扫描 | 递归遍历 | `.gitignore` 感知的增量扫描 | 大项目扫描从 5s 降到 0.5s |
| ADR 差分 | 全量重写 | 只追加修订段落 | 历史 ADR 可完整追溯 |

### 6.2 生产级改造清单

如果要让 Project Forge 成为 SaaS 服务（而非本地 CLI 工具），还需要：

- **API 服务层**：FastAPI 封装 REST API（项目已有 `handoff` 的 Schema v2 可重用）
- **用户认证**：JWT + API Key 双模式
- **多租户隔离**：按 workspace/project 隔离文件系统
- **异步任务队列**：Celery 或 ARQ 处理证据采集
- **数据库**：SQLite → PostgreSQL 迁移（证据和状态持久化）
- **缓存层**：Redis 缓存评分结果、Provider 响应
- **监控告警**：Sentry 错误追踪 + Prometheus 指标 + Grafana 仪表盘
- **CI/CD**：Docker 镜像 → GitHub Container Registry → K8s 部署

### 6.3 技术复用性

这套技术栈（Python dataclass + 合约模式 + 状态机 + 证据管道 + 9 维评分）可以复用到：

| 场景 | 差异性 | 关键改造点 |
|------|--------|-----------|
| **技术选型内部平台** | 评分维度从代码栈扩展到中间件(RabbitMQ/Kafka) | 新增 `catalog/` 条目和 baseline |
| **合规审查工具** | 评分维度侧重许可证+安全 | 增强 OSV provider，加入 SBOM 解析 |
| **开源项目健康度评估** | 评分维度加入 community_health, bus_factor | 新增 GitHub API provider 指标 |
| **AI Agent 任务分配器** | Loop Engine 的"信号→路由→修订"模式直接复用 | 把信号类型从技术问题换成任务描述 |

### 6.4 架构升级路径

**短期（v0.5.0）**：
- 证据 Provider 并行化
- CLI 交互模式增强（现在只有 `init --interactive`，可扩展到 `loop run --interactive`）
- MCP Server 增加 `loop_ingest`、`loop_status` 工具

**中期（v0.6.0）**：
- Plugin 系统：允许第三方注册自定义 Provider 和评分维度
- Web Dashboard：FastAPI + Vue3 的可视化决策仪表盘
- Git 集成：自动检测 `git diff` 触发 Loop 信号

**远期（v1.0.0）**：
- 决策知识图谱：从 ADR 历史自动提取决策模式
- 多 Agent 协作：Forge + Superpowers + Loop 三个 Agent 独立运行并协调
- 持续决策 CI：每个 PR 自动评估"这个改动是否还符合 ADR"

---

## 附录：项目中的关键设计模式汇总

| 模式 | 应用位置 | 一句话解释 |
|------|---------|-----------|
| **合约模式** | `contract.py`, `project-forge.yaml` | 模块间的交互由可验证的结构化文档定义，不是口头约定 |
| **策略模式** | `scoring.py` 的 9 个 `_xxx()` 函数 | 每个评分维度独立，可替换 |
| **状态机** | `loop/state_machine.py` | 显式转移表替代散落的 if/else |
| **依赖倒置** | `providers.py` 的 `Transport` 协议 | 抽象 HTTP 传输，方便注入 mock |
| **工厂方法** | `LoopSignal.from_dict()` | 统一的反序列化入口 |
| **模板方法** | `forge_project.py` → 各子脚本 | CLI 统一调用约定 |
| **观察者** | Loop 信号 → inbox → 状态机 | 事件驱动的异步解耦 |
| **原子操作** | `storage.py` 的 `atomic_write` | OS 级别保证的完整写入 |
| **门面模式** | `cli.py` | 用户只看到 15 个子命令，背后调用复杂模块 |

---

> **读完这篇拆解，你应该能回答以下问题：**
> 1. Project Forge 的"想法→交接包"的 5 步管道分别是什么？
> 2. 为什么选 Python 而不是 Go/Node.js？为什么零运行时依赖？
> 3. dataclass + Enum 如何替代 ORM 成为数据层？
> 4. 评分引擎的 9 个维度各测什么？maturity 惩罚的逻辑是什么？
> 5. Loop 状态机的 8 种状态如何流转？收敛检测如何防止无限循环？
> 6. 文件原子写入和备份回滚的三层安全机制是什么？
> 7. 如何避免 Windows BOM、dataclass 可变默认值、字符串枚举比较这三类坑？
> 8. 这套架构可以复用到哪些其他场景？

---

*本文基于 Project Forge v0.4.0 源码分析，含 184 个自动化测试的验证结果。写作时间：2026-06-22。*
