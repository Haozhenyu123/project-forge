# Harness 工程与 Loop 工程深度解析（面试专项）

> 面试场景：当面试官问 "你在 Project Forge 里做了什么"，用这篇讲清楚两项可迁移的工程方法论。

---

## 第一部分：Harness 工程

### 一、什么是 Harness 工程

#### 1.1 一句话定义

**Harness（工程契约）是一份结构化、可自动验证的"项目能做什么"的合约。** 它不关心你怎么写代码，只关心你的项目能不能通过以下七个标准关卡。

#### 1.2 为什么需要 Harness

想象你接手一个陌生项目，README 写了三行。你不知道：
- 怎么装依赖？
- 跑什么命令测试？
- 有没有 lint？
- 能不能构建？
- 怎么启动？

你用猜的方式 `npm install && npm start`，十分钟后报错说缺 Python 3.9。

**Harness 解决的就是这个"项目自描述能力缺失"的问题。** 它把 7 个标准命令写进一份合约，任何人（包括 AI Agent）拿到项目都知道怎么操作。

#### 1.3 Harness 不是什么

- ❌ 不是 CI 配置文件（.github/workflows/ 是 CI，Harness 是 CI 的"上游指令"）
- ❌ 不是 Makefile（Makefile 管的是构建任务编排，Harness 管的是"项目能做什么"的声明）
- ❌ 不是 Dockerfile（Dockerfile 管运行环境，Harness 管开发契约）

**一句话**：Harness 是你对 AI Agent 和同事说"这个项目的标准操作就是这七步"的那份说明书。

---

### 二、Harness 在 Project Forge 中的落地

#### 2.1 七步标准命令

```
install  → 装依赖（npm install / pip install）
test     → 跑测试
lint     → 代码规范检查
typecheck→ 类型检查（tsc / mypy）
build    → 构建产物
run      → 启动项目
smoke    → 冒烟测试（启动后快速验证核心路径）
```

**为什么是这七步而不是五步或十步？** 因为这是从数百个开源项目的实践中提炼出的最小完备集：能跑通这七步的项目，在开发、CI、部署三个环境都能正常工作。

#### 2.2 结构化命令契约

```yaml
# project-forge.yaml 中的 Harness 段
stacks:
  primary:
    id: "primary"
    template: "node-ts"
    commands:
      install:
        argv: ["npm", "install"]        # ← 结构化参数，不是 shell 字符串
        cwd: "."
        timeout_seconds: 300
      test:
        argv: ["npm", "test"]
        cwd: "."
      lint:
        argv: ["npm", "run", "lint"]
      typecheck:
        argv: ["npm", "run", "typecheck"]
      build:
        argv: ["npm", "run", "build"]
      run:
        argv: ["npm", "run", "dev"]
        mutates: false                   # ← 声明这个命令不修改文件
      smoke:
        argv: ["npm", "run", "smoke"]
```

**为什么用 `argv` 数组而不是一个 shell 字符串？**

```python
# ❌ 不安全：Shell 注入
"test": "npm test && rm -rf /"

# ✅ 安全：结构化参数，每个参数独立
"test": {"argv": ["npm", "test"]}
```

`argv` 数组绕过 shell 解析，无法注入 `&&` 或 `|` 管道。同时 `cwd` 限定在工作目录内不会逃逸。

#### 2.3 三层安全防御

```python
# 防御 1：路径逃逸检测
cwd = (Path(project_root) / spec.cwd).resolve()
try:
    cwd.relative_to(project)             # 如果 cwd 跳到项目外，抛异常
except ValueError:
    raise ExecutionBlocked("command cwd escapes project")

# 防御 2：Shell 注入防御
if spec.legacy_shell and not allow_legacy_shell:
    raise ExecutionBlocked("legacy shell command requires --allow-legacy-shell")

# 防御 3：超时强制终止
try:
    stdout, stderr = proc.communicate(timeout=timeout)
except subprocess.TimeoutExpired:
    _terminate(proc)  # Windows: taskkill /T /F, Unix: SIGTERM → SIGKILL
```

**面试可以这样讲**：我做 Harness 执行器时，对每个命令做了三层防御——路径逃逸检测防止读到项目外文件、禁止 legacy shell 字符串防止注入、每个命令独立超时兜底。这三层保证了即使 Harness 配置被恶意篡改，也不会危及宿主机。

#### 2.4 Harness 模板系统

```
templates/harness/
├── node-ts/          ← TypeScript 项目模板
│   └── project-forge.yaml (npm install / npm test / tsc / ...)
├── python/           ← Python 项目模板
│   └── project-forge.yaml (pip install / pytest / ruff / mypy / ...)
├── nextjs/           ← Next.js 模板
├── fastapi/          ← FastAPI 模板
├── electron/         ← Electron 模板
├── cli/              ← CLI 工具模板
├── chrome-extension/ ← Chrome 插件模板
└── generic/          ← 通用回退模板
```

每个模板都预先填好该技术栈最标准的命令组合。用户只需要 `project-forge init --stack node-ts`，七步命令自动生成。同时 catalog 中的每个栈都有 `harness_availability` 维度评分——有模板的栈在评分时获得加分。

---

### 三、Harness 如何复用到其他项目

#### 3.1 适用场景

| 场景 | 怎么用 |
|------|--------|
| **新项目启动** | 团队先用 Harness 定义"什么算完成"的标准，再开始写代码 |
| **AI Agent 安全执行** | 把 Harness 作为 Agent 的允许命令列表，Agent 不能执行合约外的任何命令 |
| **CI 标准化** | 从 Harness 合约自动生成 CI workflow，不再每个项目手写 |
| **技术债审计** | 扫描现有项目，列出缺失的 Harness 命令（没测试？没 lint？一目了然） |
| **onboarding 自动化** | 新人拿到项目，跑 `harness test` 就知道环境对不对 |

#### 3.2 让面试官眼前一亮的点

1. **"我把 Harness 设计成可执行合约而非配置文件"**——它不仅定义命令，还自动执行并生成 verification report
2. **"安全不是附加功能，是 Harness 执行器的默认约束"**——默认禁止 shell 字符串、默认检查路径逃逸
3. **"Harness 让 AI Agent 有了安全边界"**——Agent 只能执行合约里登记的命令，不能自由发挥

---

## 第二部分：Loop 工程

### 四、什么是 Loop 工程

#### 4.1 一句话定义

**Loop（决策循环）是一个有限状态自动机，它在"决策→执行→反馈→修订→新决策"的闭环中运行，保证架构决策不会在一次决策后就变成无法修正的死文档。**

#### 4.2 为什么需要 Loop

传统的架构决策流程是一次性的：

```
需求 → 选技术栈 → 写 ADR → 开始写代码
                                │
                        两周后发现选错了
                                │
                        要么推倒重来，要么硬撑
```

**有了 Loop，这个流程变成：**

```
需求 → 选技术栈 → 写 ADR → 交接给 Superpowers 实现
                              │
                    实现中发现架构问题
                              │
                    发信号 → Loop 接收
                              │
                    自动路由：这个问题归谁？
                    ├── 实现问题 → 还给 Superpowers 修
                    └── 架构问题 → Forge 重新评估
                              │
                    重新评分 → 修订 ADR → 新交接包
                              │
                    再次实现 → 再次反馈 → ...
```

Loop 的核心价值不是"自动化"，而是**"可控的修订"**——每次修订都有迹可查、有上限保护、有阻塞兜底。

#### 4.3 Loop 不是什么

- ❌ 不是 CI/CD 的替代品——CI 是代码级自动验证，Loop 是架构级决策修订
- ❌ 不是持续部署——Loop 只管决策文档（ADR、合约、交接包），不改代码
- ❌ 不是无限循环——最多 3 轮，超限自动进入 Human Decision Packet

---

### 五、Loop 在 Project Forge 中的落地

#### 5.1 五种信号输入

```python
class SignalKind(str, Enum):
    VERIFICATION_FAILURE:    # 测试挂了，Harness 合约执行失败
    ARCHITECTURE_FEEDBACK:   # 实现中发现架构假设不对（如"选了 MongoDB 但需要事务"）
    CONSTRAINT_CHANGE:       # 外部约束变了（如"客户要求必须用 AWS，不能用 Vercel"）
    EVIDENCE_EXPIRY:         # 证据过期（半年前的 GitHub 数据已经不准了）
    SECURITY_ADVISORY:       # 安全漏洞（OSV 报告严重 CVE）
    LICENSE_CONFLICT:        # 许可证冲突（AGPL 不能用）
    SUPERPOWERS_FEEDBACK:    # Superpowers 的通用反馈
    MANUAL:                  # 人工提交的信号
```

**面试可以这样讲**：我设计了八种信号类型，每种都有预定义的路由规则。比如安全漏洞和许可证冲突直接路由到人工审核（因为涉及合规风险），而验证失败则路由回 Superpowers 修代码——Loop 不替实现者修 bug。

#### 5.2 八状态状态机

```
                 ┌──────────────────────────┐
                 │        IDLE (空闲)        │
                 └──────────┬───────────────┘
                            │ 收到信号
                            ▼
                 ┌──────────────────────────┐
                 │    COLLECTING (收集中)     │
                 └──────────┬───────────────┘
                            │ 分类+去重完成
                            ▼
                 ┌──────────────────────────┐
                 │    EVALUATING (评估中)     │
                 └──────────┬───────────────┘
                            │
              ┌─────────────┴──────────────┐
              ▼                            ▼
   ┌──────────────────┐         ┌──────────────────┐
   │  REVISING (修订)  │         │  BLOCKED (阻塞)   │
   └────────┬─────────┘         └────────┬─────────┘
            │                            │ resume_loop
            ▼                            ▼
   ┌──────────────────┐         ┌──────────────────┐
   │HANDOFF_READY(就绪)│         │  回到 COLLECTING  │
   └────────┬─────────┘         └──────────────────┘
            │
            ▼
   ┌──────────────────────────┐
   │AWAITING_FEEDBACK(等待反馈)│
   └──────────┬───────────────┘
              │ 新一轮信号
              ▼
         COLLECTING
```

**面试重点**：这张图不是画着好看的——每个状态转移都在代码里有显式守卫。16 条合法转移中任何一步试图跳到非法状态，直接抛 ValueError。这意味着**状态 bug 在开发阶段就暴露，而不是在生产环境才发现**。

#### 5.3 三层安全阀

```python
# 安全阀 1：重复决策检测（两轮同哈希 → 死循环 → blocked）
@property
def has_stale_progress(self) -> bool:
    if len(self.iterations) < 2:
        return False
    last_two = self.iterations[-2:]
    return (last_two[0].decision_hash == last_two[1].decision_hash
            and last_two[1].action != "reroute")

# 安全阀 2：最大迭代上限（默认 3 轮）
@property
def is_exhausted(self) -> bool:
    return len(self.iterations) >= self.policy.max_iterations

# 安全阀 3：Human Decision Packet（三轮回合耗尽时生成）
# 包含：冲突摘要、候选方案、已有证据、必须人工选择的问题
```

**面试可以这样讲**：Loop 的核心设计哲学不是"自动解决所有问题"，而是"自动解决能自动解决的，明确标记必须人工介入的"。三个安全阀保证了这一点——两轮同哈希说明系统卡住了、三轮上限防止无限消耗、Human Packet 把决策权交还给人。

#### 5.4 信号去重与幂等

```python
def _compute_fingerprint(self) -> str:
    core = json.dumps(
        [self.signal_id, self.kind.value, self.source, self.summary],
        sort_keys=True,
    )
    return hashlib.sha256(core.encode()).hexdigest()[:16]
```

同一个信号（比如同一个测试失败）即使被多次提交，SHA256 指纹相同，Loop 只处理一次。**保证幂等——同一个信号被重复消费不会产生副作用。**

#### 5.5 原子安全写入

```python
def atomic_write(path, text):
    tmp = path.with_suffix(path.suffix + ".tmp")  # 1. 写临时文件
    tmp.write_text(text, encoding="utf-8")
    os.replace(str(tmp), str(path))               # 2. OS级原子替换

def backup_file(path):
    backup = path.with_suffix(path.suffix + f".bak-{timestamp}")
    shutil.copy2(str(path), str(backup))           # 3. 修改前先备份
    return backup
```

**三种文件操作保证**：
1. 修改前备份 → 任何时刻可以回滚
2. 写入临时文件 → 即使写一半崩溃也不污染正式文件
3. OS 级原子替换 → 要么是旧文件，要么是完整新文件，不存在中间态

#### 5.6 Loop 的安全边界

Loop 有一条铁律：**只修改 Forge 自己的产出物，绝不碰应用代码。**

| 允许 | 禁止 |
|------|------|
| 修改 ADR (docs/architecture/ADR-0001-stack.md) | 修改 src/*.py 或 src/*.ts |
| 修改 project-forge.yaml | 修改 package.json |
| 修改 handoff 包 | 执行 npm install / pip install |
| 生成 loop 报告 | 执行 npm run dev |
| 刷新证据和风险评估 | 写入应用配置 |

**面试可以这样讲**：Loop 和 Superpowers 之间有一条明确的边界线。Loop 管"方向对不对"，Superpowers 管"代码怎么写"。Loop 永远不会越界去修改应用代码——这是设计层面的安全承诺，不是靠程序员自律。

---

### 六、Loop 如何复用到其他项目

#### 6.1 适用场景

| 场景 | 怎么用 |
|------|--------|
| **微服务架构治理** | 每个服务的架构决策用 Loop 管理，服务间依赖变化自动触发重新评估 |
| **合规审查自动化** | 法规变化（如 GDPR 更新）→ 信号 → Loop 评估现有系统是否合规 → 修订合规文档 |
| **技术债管理系统** | 每次 code review 发现架构级问题 → 生成信号 → Loop 决定是还债还是记录 |
| **多 Agent 协调器** | Agent A 的输出是 Agent B 的输入 → Loop 作为"调度器"，决定哪个 Agent 干活、什么时候交接 |
| **产品决策闭环** | A/B 测试结果 → 信号 → Loop 评估是否要改产品方向 → 修订 PRD |
| **开源项目维护** | issue 被标记为 "architecture" → 自动生成信号 → Loop 评估是否需要 ADR 修订 |

#### 6.2 通用 Loop 设计模板

如果要在你自己的项目里实现一个 Loop 系统，最小可行的骨架是：

```python
# 1. 定义信号类型（你的项目关心什么变化）
class Signal:
    kind: str        # security / performance / dependency / requirement_change
    severity: str    # critical / high / medium / low
    summary: str

# 2. 定义路由规则（每个信号归谁处理）
def route(signal):
    if signal.kind == "security" and signal.severity == "critical":
        return "human"
    if signal.kind in ("requirement_change", "dependency"):
        return "architect"
    return "developer"

# 3. 定义收敛条件（什么时候停止循环）
def check_convergence(episode):
    if episode.iterations >= 3:
        return "human_packet"     # 三轮没解决 → 人介入
    if last_two_hashes_same:
        return "blocked"          # 卡住了 → 人介入
    return "continue"

# 4. 保证幂等（同一个信号不被处理两次）
def dedup(signals, known_fingerprints):
    return [s for s in signals if s.fingerprint not in known_fingerprints]

# 5. 原子写入（永远不要直接写文件）
def save_state(state):
    atomic_write("state.json.tmp", state)
    os.replace("state.json.tmp", "state.json")
```

#### 6.3 让面试官眼前一亮的点

1. **"我把状态机写成了显式转移表"**——16 条合法转移全部静态定义，非法转移在测试阶段就暴露
2. **"Loop 的核心不是自动化，是可控修订"**——最大三轮、两轮同哈希阻塞、超限生成人工决策包
3. **"Loop 和 Superpowers 之间有明确的边界"**——Loop 管决策方向，Superpowers 管代码实现，永远不会越界
4. **"幂等性不是事后打的补丁，是设计之初的约束"**——SHA256 指纹去重，同一个信号可以安全地重放

---

## 第七部分：Harness + Loop 的协同效应

### 七、两者如何互补

```
Harness（执行层契约）          Loop（决策层闭环）
─────────────────────        ─────────────────────
定义"项目能做什么"            定义"方向应该怎么调"
静态合约                     动态状态机
一次性验证                   持续修订
└─────────────────────────────┘
           │
           ▼
    Harness 验证失败
           │
           ▼
    生成 VERIFICATION_FAILURE 信号
           │
           ▼
    Loop 路由：实现问题还是架构问题？
    ├── 实现问题 → 还给 Superpowers（不改架构）
    └── 架构问题 → 重新评分 → 修订 ADR → 新 Harness → 新 Handoff
```

**核心思想**：Harness 发现"有什么不对"，Loop 决定"应该怎么改"。两者结合形成完整的决策→验证→修订闭环。

### 七、面试话术

> "我们在 v0.4.0 里把 Harness 和 Loop 打通了。Harness 合约执行失败不再是简单的 pass/fail——每个失败都会生成一个 Loop 信号，Loop 自动判断是代码实现问题还是架构设计问题。如果是架构问题，Loop 自动重新评分技术栈、修订 ADR、生成新的交接包。整个过程有明确的安全边界和迭代上限，不会无限循环也不会越权修改应用代码。"

---

*本文为面试专项资料，聚焦 Harness 和 Loop 两项可迁移工程方法论。完整代码参考 Project Forge v0.4.0 源码。*
