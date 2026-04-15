# BlockStreaming 三段式输出设计

**日期**: 2026-04-15
**版本**: v0.3.2b
**功能编号**: F18（Stage 输出呈现优化 v2）

---

## 背景

v0.3.2b F17 已修改 Stage 输出呈现：去掉代码块包裹、直接输出、各阶段针对性呈现。

用户反馈：报告中每个位置展示溯源标记影响阅读体验，已在 F16 移除。

用户进一步需求：希望报告全文作为独立消息块展示，与引导语、确认提示语分离，实现更好的阅读体验。

---

## 技术方案：blockStreaming 分块流式传输

### 方案选型对比

| 方案 | 优点 | 缺点 | 结论 |
|------|------|------|------|
| blockStreaming | 官方原生、无副作用、自动分块 | 需配置启用 | ✓ 采用 |
| sessions_yield | 子会话返回 | 中断流程、不适用于此场景 | ✗ 不用 |
| context.send | 手动发送 | 非官方推荐方式 | ✗ 不用 |
| 普通单次回复 | 无分块 | 所有内容揉在一起 | ✗ 不用 |

### blockStreaming 配置层级

根据 OpenClaw 文档调研：

- `agents.defaults.*` — 全局默认配置（所有 agent 继承）
- `channels.<channel>.*` — Channel 级覆盖（优先级最高）
- blockStreaming 配置 **不支持 Per-Agent 覆盖**（只能全局配置）
- 修改全局配置会影响所有 agent（用户已确认接受）

---

## 设计段 1：整体架构

### 新增功能模块

| 模块 | 位置 | 作用 |
|------|------|------|
| 启动自检 | SKILL.md Stage 0 前 | 检查 OpenClaw blockStreaming 配置状态并提醒用户 |
| 三段式输出指令 | SKILL.md Stage 1/2/3 输出呈现 | 规定引导语+报告+确认语三段独立消息 |

### 执行流程

```
用户触发 rana skill
    │
    ▼
启动自检（新增）
    │ 读取 ~/.openclaw/config.yaml
    │ 检查 agents.defaults.blockStreaming* 配置
    │
    ├─ 全部符合 → 输出 ✓ 提示
    │
    └─ 任一不符 → 输出 ⚠ 提示
    │
    ▼
Stage 0：文件预处理
    │
    ▼
Stage 1/2/3 输出（blockStreaming 生效时自动分块）
    │
    ▼
消息块 1：引导语（独立）
消息块 2：报告全文（独立）
消息块 3：确认提示语（独立）
```

---

## 设计段 2：推荐配置项

### 推荐的 blockStreaming 配置

写入位置：`~/.openclaw/config.yaml` 的 `agents.defaults` 下（仅提醒用户，不自检写入）

```yaml
agents:
  defaults:
    blockStreamingDefault: "on"
    blockStreamingBreak: "text_end"
    blockStreamingChunk:
      maxChars: 100000
      breakPreference: "paragraph"
```

### 配置说明

| 配置项 | 推荐值 | 作用 |
|--------|--------|------|
| `blockStreamingDefault` | `"on"` | 启用分块流式传输 |
| `blockStreamingBreak` | `"text_end"` | 在文本结束时拆分 |
| `blockStreamingChunk.maxChars` | `100000` | 上限足够大，报告全文不被切碎 |
| `blockStreamingChunk.breakPreference` | `"paragraph"` | 按段落分割 |

### 已移除的配置项

以下配置项不纳入推荐配置（不强制约束）：
- `blockStreamingChunk.minChars` — 由框架默认值处理
- `blockStreamingCoalesce.minChars` — 由框架默认值处理
- `blockStreamingCoalesce.idleMs` — 由框架默认值处理

---

## 设计段 3：SKILL.md 自检流程指令

### 新增位置

在 SKILL.md 「Stage 0：文件预处理」章节之前新增。

### 新增内容

```markdown
## 启动自检：blockStreaming 配置检查

**目的**：确认 OpenClaw 框架的 blockStreaming 配置状态。

**执行时机**：rana skill 启动时，在 Stage 0 之前执行。

**推荐配置**：

| 配置项 | 推荐值 |
|--------|--------|
| `blockStreamingDefault` | `"on"` |
| `blockStreamingBreak` | `"text_end"` |
| `blockStreamingChunk.maxChars` | `100000` |
| `blockStreamingChunk.breakPreference` | `"paragraph"` |

**自检步骤**：

1. 读取 `~/.openclaw/config.yaml`
2. 检查 `agents.defaults` 下上述配置项

**检查结果提示**：

- 全部符合：`✓ blockStreaming 配置符合推荐值`
- 任一配置不符或缺失：`⚠️ blockStreaming 配置未完全符合推荐值`

**失败处理**：
- 若配置文件不存在或读取失败，跳过检查，继续执行
```

---

## 设计段 4：三段式输出指令

### 输出结构

| 消息块 | 内容 | Stage 1 | Stage 2 | Stage 3 |
|--------|------|---------|---------|---------|
| 块 1 | 引导语 | 「正在为你展示 Basic + Core 阶段完整分析文档」 | 「正在为你展示协作补充后的完整分析文档」 | 「正在为你展示最终完整分析说明书」 |
| 块 2 | 报告全文 | 一~四章节 | 一~四章节 | 一~八章节 |
| 块 3 | 确认提示语 | 现有确认语（保留） | 现有确认语（保留） | 现有确认语（保留） |

### Stage 1 输出呈现（修改后）

位置：SKILL.md 中 **Stage 1 输出呈现（强制要求）** 章节

```markdown
**Stage 1 输出呈现（强制要求）**：

使用三段式独立消息输出：

**消息块 1（引导语）**：
> 正在为你展示 Basic + Core 阶段完整分析文档

**消息块 2（报告本体）**：
- 静默读取 final-analysis.md 已完成部分（一~四章节）
- 逐字全文输出，不省略、不截断、不使用代码块包裹
- 不输出五~九章模板内容

**消息块 3（确认提示语）**：
> 📄 以上是 Basic + Core 阶段的完整分析文档。如需调整任何内容，请直接告知。确认无误后，我们将进入 Stage 2 协作补充。
```

### Stage 2 输出呈现（修改后）

位置：SKILL.md 中 **Stage 2 输出呈现（强制要求）** 章节

```markdown
**Stage 2 输出呈现（强制要求）**：

使用三段式独立消息输出：

**消息块 1（引导语）**：
> 正在为你展示协作补充后的完整分析文档

**消息块 2（报告本体）**：
- 静默读取 final-analysis.md 已完成部分（一~四章节）
- 逐字全文输出，不省略、不截断、不使用代码块包裹
- 不输出五~九章模板内容

**消息块 3（确认提示语）**：
> 📄 以上是协作补充后的完整分析文档。如需调整任何内容，请直接告知。确认无误后，我们将进入 Stage 3 Detail 输出。
```

### Stage 3 输出呈现（修改后）

位置：SKILL.md 中 **Stage 3 输出呈现（强制要求）** 章节

```markdown
**Stage 3 输出呈现（强制要求）**：

使用三段式独立消息输出：

**消息块 1（引导语）**：
> 正在为你展示最终完整分析说明书

**消息块 2（报告本体）**：
- 静默读取 final-analysis.md 已完成部分（一~八章节）
- 逐字全文输出，不省略、不截断、不使用代码块包裹
- 不输出九章节（P2，不填充）

**消息块 3（确认提示语）**：
> 📄 以上是本次需求分析的完整说明书。Basic + Core + Detail 阶段已输出，P0 缺口已补完。如需调整任何内容，请直接告知。
```

---

## 变更清单

| # | 变更 | 位置 | 说明 |
|---|------|------|------|
| 1 | 新增启动自检章节 | SKILL.md Stage 0 前 | blockStreaming 配置检查 |
| 2 | 修改 Stage 1 输出呈现 | SKILL.md 约第 492-503 行 | 三段式输出指令 |
| 3 | 修改 Stage 2 输出呈现 | SKILL.md 约第 647-658 行 | 三段式输出指令 |
| 4 | 修改 Stage 3 输出呈现 | SKILL.md 约第 806-817 行 | 三段式输出指令 |
| 5 | 更新 roadmap.md | docs/roadmap.md | 新增 F18 修复项 |

---

## 注意事项

1. blockStreaming 配置为全局配置，修改影响所有 agent
2. 自检仅提示用户，不自动写入配置
3. 用户需自行决定是否按推荐配置调整
4. 三段式输出的实际效果依赖 blockStreaming 配置生效