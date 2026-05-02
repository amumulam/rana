# Agent 行为约束 — v0.4.3 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 SKILL.md 中新增"Agent 行为约束"独立章节（5 项轻量禁令式规则），版本号升至 v0.4.3，同步更新 CHANGELOG.md。

**Architecture:** 在 SKILL.md 的"工作原则"和"批判反驳规则"之间插入新章节，包含引导说明和规则表格。规则覆盖内部逻辑不可见、路径问询只给路径、意图不明先追问、权限边界提供替代方案、JSON 转义注意事项五个维度。

**Tech Stack:** Markdown 文件编辑

---

### Task 1: 在 SKILL.md 中新增 Agent 行为约束章节

**Files:**
- Modify: `rana/SKILL.md`（在行 50 之后、"批判反驳规则"之前插入新章节）
- Modify: `rana/SKILL.md`（版本号 0.4.2 → 0.4.3）

- [ ] **Step 1: 插入 Agent 行为约束章节**

在 SKILL.md 中，将第 7 行 `7. **专业坚持**...` 替换为：

```
7. **专业坚持**：当用户的想法可能存在问题时，不要立即妥协，而要通过深入探讨帮助用户看到潜在风险

## Agent 行为约束

Agent 行为约束是对 [四段式消息结构](references/collaboration-protocol.md §四段式独立消息通用结构) 的补充和强化。最终交付物呈现遵循消息块 2 的规则，以下约束聚焦 Agent 日常交互行为。

| # | 规则名 | 规则内容 |
|---|--------|---------|
| B1 | **内部逻辑不可见** | 你的 CoT（思维链）、Goal、Instructions、中间日志等内部信息禁止输出给用户。始终保持中文专业业务助理身份进行对话。 |
| B2 | **文件路径问询只给路径** | 用户问"文件在哪/保存在哪/目录是什么/路径是什么"，只返回文件的绝对路径字符串。禁止打印文件正文内容。 |
| B3 | **意图不明先追问** | 用户输入模糊、意图不清时，先追问澄清，严禁猜测后直接执行。 |
| B4 | **权限边界说清替代方案** | 无权限操作时，说明系统权限限制，提供文件当前已保存的绝对路径，建议用户手动处理。不强行执行后报错卡壳。 |
| B5 | **JSON 参数注意转义** | 调用工具时严格注意 JSON 格式和引号转义，参照工具文档中的示例格式构造参数，避免转义错误导致反复重试。 |

```

- [ ] **Step 2: 确保原第 7 条末尾无逗号**

检查替换后，"工作原则"第 7 条以句号结尾（`。`），与新增章节间有空格行。

- [ ] **Step 3: 版本号 0.4.2 → 0.4.3**

将 SKILL.md 第 3 行 `version: 0.4.2` 改为 `version: 0.4.3`。

- [ ] **Step 4: 验证文件结构**

检查插入位置：`## Agent 行为约束` 章节位于 `## 批判反驳规则（概要）` 之前。

- [ ] **Step 5: Commit**

```bash
git add rana/SKILL.md
git commit -m "feat: add Agent 行为约束章节 (v0.4.3) — 5 项轻量禁令式规则约束 Agent 工具调用行为"
```

---

### Task 2: 更新 CHANGELOG.md

**Files:**
- Modify: `CHANGELOG.md`（在 v0.4.2 条目上方新增 v0.4.3 条目）

- [ ] **Step 1: 重命名 RELEASE_NOTE.md → CHANGELOG.md，删除 generate-changelog.sh**

```bash
git mv RELEASE_NOTE.md CHANGELOG.md
git rm scripts/generate-changelog.sh
```

- [ ] **Step 2: 在 CHANGELOG.md 顶部插入 v0.4.3 条目**

将 CHANGELOG.md 第 8 行 `## [0.4.2] - 2026-04-30` 替换为：

```
## [0.4.3] - 2026-05-02

### 新增

- Agent 行为约束章节（SKILL.md 独立章节），5 项轻量禁令式规则

### 移除

- `scripts/generate-changelog.sh` — 机械拼接脚本，已被 CHANGELOG.md 手写维护替代

### 变更

- `RELEASE_NOTE.md` 重命名为 `CHANGELOG.md`，格式改为 Keep a Changelog 规范

## [0.4.2] - 2026-04-30
```

- [ ] **Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: add v0.4.3 changelog entry — agent constraints + changelog refactor"
```
