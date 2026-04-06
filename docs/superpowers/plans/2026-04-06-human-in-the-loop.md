# Human-in-the-Loop 主路径确认 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 SKILL.md Stage 2 内插入主路径确认节点（Step 2.5），用户以提问形式逐条确认主任务/子任务/页面入口的正确性后，AI 再补全边界/异常等维度。

**Architecture:** 纯文本编辑，只改 `rana/SKILL.md` 的 Stage 2 节。Stage 2 处理步骤新增 Step 2.5（主路径确认），输出规范改为 2a/2b 两步描述。其他文件、validator、模板均不改动。

**Tech Stack:** Markdown 文本编辑；回归测试用 `python3 -m pytest tests/ -v`（70 个测试，所有测试须保持全绿）

**Spec:** `docs/superpowers/specs/2026-04-06-human-in-the-loop-design.md`

---

## 文件改动清单

| 文件 | 变更类型 | 位置 |
|------|---------|------|
| `rana/SKILL.md` | 修改（2处） | Stage 2「处理步骤」+ Stage 2「输出规范」 |

---

## Task 1：Stage 2 处理步骤新增 Step 2.5

**Files:**
- Modify: `rana/SKILL.md`（Stage 2「处理步骤」节，约第 240-265 行）

- [ ] **Step 1: 定位目标段落**

  在 `rana/SKILL.md` 中找到 Stage 2「处理步骤」节，确认当前步骤 3 为：

  ```markdown
  3. **拆解需求结构**（7维度）
     - 主任务
     - 子任务
     - 页面/入口
     - 分支流程
     - 异常流程
     - 状态变化
     - 依赖关系
  ```

- [ ] **Step 2: 在步骤 3 后插入 Step 2.5（主路径确认节点）**

  在步骤 3「拆解需求结构」段落之后、`### 来源追溯要求` 之前，插入以下内容：

  ```markdown
  4. **主路径确认（Step 2.5，默认开启）**

     完成步骤 3 的 7 维度拆解草稿后，**暂停输出 gap-analysis.md**，先执行主路径确认：

     **Step 2.5a：提取主路径草稿**

     从步骤 3 的拆解结果中，针对**每个功能**提取 3 个维度：
     - 主任务
     - 子任务
     - 页面/入口

     以提问形式逐条列出，每个功能单独一组问题，格式如下：

     ```
     我整理了「[功能名]」的主路径，请逐条确认：

     **主任务**
     Q1. [主任务描述，一句话陈述句]。这个对吗？

     **子任务**
     Q2. 子任务包含：[子任务列表]。这个对吗？
     Q3. [若有多条子任务逻辑，每条单独一问]。这个对吗？

     **页面/入口**
     Q4. 入口路径：[页面A] → [页面B] → [入口]。这个对吗？

     请回复每题编号 + 答案，例如：
     Q1 对  Q2 对  Q3 不对，应该是...  Q4 对
     ```

     多功能 PRD：每个功能单独一组问题，逐功能列出，不混合。

     输出末尾加一行：
     > 是否需要逐条确认主路径？**默认是**，回复「跳过」可略过直接补全边界和异常。

     **Step 2.5b：等待用户回复并更新**

     - 用户回复「跳过」→ 直接进入 Step 2.5c
     - 用户有回复 → 按修正内容更新主路径草稿，输出「已更新主路径」确认单（列出修改项）→ 进入 Step 2.5c
     - 若用户纠正引发新的不确定项（如「这个跳转逻辑要重新定义」）→ 记录到待澄清列表，Stage 3 跟进；不在 Stage 2 内继续追问

     **Step 2.5c：补全其余维度**

     基于已确认的主路径，补全每个功能的其余 4 个维度：
     - 分支流程
     - 异常流程
     - 状态变化
     - 依赖关系

     完成后输出完整 `gap-analysis.md`（7 维度）。
  ```

- [ ] **Step 3: 运行回归测试确认全绿**

  ```bash
  python3 -m pytest tests/ -v --tb=short -q
  ```

  预期：`70 passed`

- [ ] **Step 4: 提交**

  ```bash
  git add rana/SKILL.md
  git commit -m "feat(skill): stage2 新增 step 2.5 主路径确认节点（human-in-the-loop）"
  ```

---

## Task 2：Stage 2 输出规范改为 2a/2b 两步描述

**Files:**
- Modify: `rana/SKILL.md`（Stage 2「gap-analysis.md 输出规范」节，约第 326 行之后）

- [ ] **Step 1: 定位目标段落**

  找到 Stage 2 输出规范开头：

  ```markdown
  **gap-analysis.md 输出规范：**
  ```

  当前规范共 4 条（禁止五问法重复、场景还原一致、检查清单数字自洽、检查清单来源列）。

- [ ] **Step 2: 在规范开头插入两步输出说明**

  在 `**gap-analysis.md 输出规范：**` 这一行**之前**，插入：

  ```markdown
  **gap-analysis.md 分两步输出：**

  - **Step 2.5a 输出**：每个功能的主任务、子任务、页面/入口草稿（3 个维度），附提问，等待用户确认
  - **Step 2.5c 输出**：基于确认结果，补全分支流程、异常流程、状态变化、依赖关系，输出完整 `gap-analysis.md`（7 维度，结构与现有模板一致）

  ```

- [ ] **Step 3: 运行回归测试确认全绿**

  ```bash
  python3 -m pytest tests/ -v --tb=short -q
  ```

  预期：`70 passed`

- [ ] **Step 4: 提交**

  ```bash
  git add rana/SKILL.md
  git commit -m "feat(skill): stage2 输出规范标注 2a/2b 两步输出流程"
  ```

---

## Task 3：同步安装 + 最终回归

**Files:**
- 无代码改动，只做安装和验证

- [ ] **Step 1: 同步安装到本地 skill 目录**

  ```bash
  cp -r rana/. ~/.agents/skills/rana/
  ```

- [ ] **Step 2: 验证安装目录与源目录一致**

  ```bash
  diff -r rana/ ~/.agents/skills/rana/ --exclude="*.pyc"
  ```

  预期：无输出（完全一致）

- [ ] **Step 3: 运行完整回归测试**

  ```bash
  python3 -m pytest tests/ -v
  ```

  预期：`70 passed`

- [ ] **Step 4: 手动验证 validator 仍可运行**

  ```bash
  python3 rana/scripts/quality-validator.py test-runs/test-a-normal
  ```

  预期：退出码 0，输出包含 `✓ PASS`

---

## 完成标准

- [ ] `python3 -m pytest tests/ -v` → 70 passed
- [ ] `diff -r rana/ ~/.agents/skills/rana/ --exclude="*.pyc"` → 无差异
- [ ] `rana/SKILL.md` Stage 2 处理步骤包含 Step 2.5（含 2.5a/2.5b/2.5c 三个子步骤）
- [ ] `rana/SKILL.md` Stage 2 输出规范开头有「分两步输出」说明
- [ ] Stage 2 处理步骤中有提问格式示例（含 Q1/Q2/Q3/Q4 结构）
- [ ] Stage 2 处理步骤中有「跳过」路径说明
