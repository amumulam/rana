# BlockStreaming 三段式输出实现 Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 rana SKILL.md 中增加 blockStreaming 配置自检和三段式输出指令

**Architecture:** 
- 新增启动自检章节（Stage 0 前）
- 修改 Stage 1/2/3 输出呈现为三段式结构
- 更新 roadmap.md 记录 F18 修复项

**Tech Stack:** Markdown 文本编辑，无代码实现

---

## Task 1: 新增启动自检章节

**Files:**
- Modify: `rana/SKILL.md` — 在 Stage 0 前插入新章节

- [ ] **Step 1: 在 Stage 0 前插入启动自检章节**

位置：第 157 行 `## Stage 0：文件预处理` 之前

插入以下内容：

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

---

```

- [ ] **Step 2: 确认插入位置正确**

读取 SKILL.md 确认新章节在 Stage 0 之前、工作流概览之后。

---

## Task 2: 修改 Stage 1 输出呈现

**Files:**
- Modify: `rana/SKILL.md` — Stage 1 输出呈现章节

- [ ] **Step 1: 替换 Stage 1 输出呈现内容**

替换位置：`**Stage 1 输出呈现（强制要求）**：` 章节（约第 492-503 行）

将现有内容替换为：

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

---

## Task 3: 修改 Stage 2 输出呈现

**Files:**
- Modify: `rana/SKILL.md` — Stage 2 输出呈现章节

- [ ] **Step 1: 替换 Stage 2 输出呈现内容**

替换位置：`**Stage 2 输出呈现（强制要求）**：` 章节（约第 647-658 行）

将现有内容替换为：

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

---

## Task 4: 修改 Stage 3 输出呈现

**Files:**
- Modify: `rana/SKILL.md` — Stage 3 输出呈现章节

- [ ] **Step 1: 替换 Stage 3 输出呈现内容**

替换位置：`**Stage 3 输出呈现（强制要求）**：` 章节（约第 806-817 行）

将现有内容替换为：

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

## Task 5: 更新 roadmap.md

**Files:**
- Modify: `docs/roadmap.md` — v0.3.2b 修复清单

- [ ] **Step 1: 在 v0.3.2b 修复清单中添加 F18**

位置：`v0.3.2b` 章节 `修复清单（基于实际运行反馈）` 表格中

在 F17 后添加一行：

```markdown
| F18 | BlockStreaming 三段式输出 | P0 | 待修复 | 新增启动自检配置检查、三段式独立消息输出（引导语+报告+确认语） |
```

同时将 F17 状态改为「已完成」（因为 F18 是 F17 的进一步优化）：

```markdown
| F17 | Stage 输出呈现优化 | P0 | 已完成 | 去掉代码块包裹，直接输出；各阶段针对性呈现（Stage 1 只输出一~四章） |
```

---

## Task 6: 提交变更

- [ ] **Step 1: 确认所有修改完成**

读取修改后的文件确认内容正确。

- [ ] **Step 2: 提交到 git**

```bash
git add rana/SKILL.md docs/roadmap.md docs/superpowers/plans/2026-04-15-blockstreaming-output-plan.md
git commit -m "feat: v0.3.2b F18 - blockStreaming 三段式输出"
```

---

## 自检清单

完成后验证：
- [ ] SKILL.md 中「启动自检」章节在 Stage 0 之前
- [ ] Stage 1/2/3 输出呈现均为三段式结构
- [ ] roadmap.md 中 F18 已添加
- [ ] 无 placeholder 或 TBD