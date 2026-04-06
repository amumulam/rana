# Rana 输出稳定性改进 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 通过修改 SKILL.md 和两个模板文件，在生成阶段前置控制输出质量，解决第二轮在线测试暴露的 6 个稳定性问题。

**Architecture:** 纯文本编辑，5 处变更分布在 `rana/SKILL.md`、`rana/templates/clarification-list.md`、`rana/templates/requirement-card.md` 三个文件。不涉及 validator 代码修改，改动后同步安装到 `~/.agents/skills/rana/` 并回归测试。

**Tech Stack:** Markdown 文本编辑；回归测试用 `python3 -m pytest tests/ -v`（54 个测试，所有测试须保持全绿）

---

## 文件改动清单

| 文件 | 变更类型 | 解决问题 |
|------|---------|---------|
| `rana/SKILL.md` | 修改（5处） | 问题 1-6 全部 |
| `rana/templates/clarification-list.md` | 修改（开头说明区块） | 问题 5：交付物 D 格式 |
| `rana/templates/requirement-card.md` | 修改（开头说明区块） | 问题 6：交付物 A 分组名 |

---

## Task 1：SKILL.md — Stage 1 缺失项表格来源列（变更 2）

**Files:**
- Modify: `rana/SKILL.md`（Stage 1「输出：input-structured.md」节，明显缺失项表格）

找到 Stage 1 输出示例中「明显缺失项」表格，执行以下步骤：

- [ ] **Step 1: 定位目标段落**

  在 `rana/SKILL.md` 中找到以下内容（当前在约第 184-221 行区域的 Stage 1 输出示例）：

  ```markdown
  ## 明显缺失项
  ```

  确认其下方的表格列头为：`| 缺失项 | 影响程度 | 需澄清内容 | 状态 |`

- [ ] **Step 2: 替换表格列头和示例行**

  将 Stage 1 输出示例中的「明显缺失项」表格从：

  ```markdown
  ## 明显缺失项

  | 缺失项 | 影响程度 | 需澄清内容 | 状态 |
  |--------|---------|-----------|------|
  | [缺失项名称] | 高/中/低 | 需要确认的具体内容 | [缺失] |
  ```

  改为：

  ```markdown
  ## 明显缺失项

  | 缺失项 | 影响程度 | 需澄清内容 | 来源 |
  |--------|---------|-----------|------|
  | [缺失项名称] | 高/中/低 | 需要确认的具体内容 | [缺失] |
  ```

  > 注意：只改列头「状态」→「来源」，示例行的 `[缺失]` 保持不变。

- [ ] **Step 3: 在 Stage 1「识别明显缺失」步骤后添加填写规则**

  找到 Stage 1 处理步骤「3. **识别明显缺失**」段落：

  ```markdown
  3. **识别明显缺失**
     - 标记信息不完整处，用 `[缺失]` 占位，留待 Stage 3 澄清
  ```

  在该段落后（`### 输出：input-structured.md` 之前）添加一条规范：

  ```markdown
  **「明显缺失项」表格填写规范**：「来源」列每行必须是合法来源格式之一（`[缺失]` / `[推断：...]` / `[用户确认]`），禁止写纯文字如「待定」、「待确认」、「可留设计阶段」。
  ```

- [ ] **Step 4: 运行回归测试确认全绿**

  ```bash
  python3 -m pytest tests/ -v --tb=short -q
  ```

  预期：`54 passed`

- [ ] **Step 5: 提交**

  ```bash
  git add rana/SKILL.md
  git commit -m "fix(skill): stage1 缺失项表格列名「状态」改为「来源」，加填写规范"
  ```

---

## Task 2：SKILL.md — Stage 2 检查清单加来源列（变更 1）

**Files:**
- Modify: `rana/SKILL.md`（Stage 2「输出：gap-analysis.md」节，检查清单表格格式 + 输出规范）

- [ ] **Step 1: 定位检查清单输出示例**

  在 `rana/SKILL.md` Stage 2「输出：gap-analysis.md」的 markdown 代码块中，找到检查清单格式示例。当前代码块里有类似：

  ```markdown
  | 项 | 状态 | 说明 |
  |----|------|------|
  | A1 需求名称 | ✓ 已覆盖 | ... |
  ```

  注意：当前 SKILL.md 的 Stage 2 输出示例里可能没有检查清单表格（该格式是在 `references/analysis-checklist.md` 里定义的）。检查 Stage 2 输出示例的实际内容，确认是否需要在示例里新增检查清单格式。

- [ ] **Step 2: 在 Stage 2 输出规范中新增第 4 条规范**

  找到 Stage 2 的「gap-analysis.md 输出规范」段落，当前有 3 条规范（禁止五问法重复、场景还原必须一致、检查清单汇总表数字自洽）。在第 3 条之后新增第 4 条：

  ```markdown
  4. **检查清单来源列必须逐行填写**：检查清单的每个表格必须包含「来源」列（4列格式：项 / 状态 / 说明 / 来源）。每行来源列不得为空：
     - ✓ 已覆盖行：填具体来源，如 `[截图X]` / `[PRD第X节]` / `[用户确认]`
     - ✗ 缺失行：填 `[缺失]`
     - ⚠ 部分行：填已有部分的来源 + `[缺失]`，如 `[截图1][缺失]`
  ```

- [ ] **Step 3: 在 Stage 2 输出示例（若有检查清单表格）中更新为 4 列格式**

  若 Stage 2 的 markdown 代码块示例中包含检查清单表格，将其更新为 4 列格式：

  ```markdown
  | 项 | 状态 | 说明 | 来源 |
  |----|------|------|------|
  | A1 需求名称 | ✓ 已覆盖 | 「服务首页优化」 | [用户确认] |
  | A2 版本/迭代号 | ✗ 缺失 | 未提供 | [缺失] |
  | D1 输入边界 | ⚠ 部分 | 交互边界未定义 | [截图1][缺失] |
  ```

  若示例中没有检查清单格式，则在规范第 4 条下方紧接一个示例代码块（不在 Stage 2 的大 markdown 块里，而是独立 ` ```markdown ``` ` 块）：

  ```markdown
  **检查清单格式示例（4列）：**

  \```markdown
  | 项 | 状态 | 说明 | 来源 |
  |----|------|------|------|
  | A1 需求名称 | ✓ 已覆盖 | 「服务首页优化」 | [用户确认] |
  | A2 版本/迭代号 | ✗ 缺失 | 未提供 | [缺失] |
  | D1 输入边界 | ⚠ 部分 | 交互边界未定义 | [截图1][缺失] |
  \```
  ```

- [ ] **Step 4: 运行回归测试确认全绿**

  ```bash
  python3 -m pytest tests/ -v --tb=short -q
  ```

  预期：`54 passed`

- [ ] **Step 5: 提交**

  ```bash
  git add rana/SKILL.md
  git commit -m "fix(skill): stage2 检查清单加来源列，新增第4条输出规范"
  ```

---

## Task 3：SKILL.md — Stage 3 change-log 操作性步骤（变更 3）

**Files:**
- Modify: `rana/SKILL.md`（Stage 3「change-log 编写规范」节）

- [ ] **Step 1: 定位当前声明式约束**

  在 `rana/SKILL.md` Stage 3 中找到「change-log 编写规范：」段落，当前内容为：

  ```markdown
  **change-log 编写规范：**

  - **编号必须连续**：CHG-001、CHG-002、CHG-003……按时间顺序递增，禁止跳号（如从 CHG-001 直接跳到 CHG-008）。
  - **禁止自相矛盾**：若某问题在变更记录中已标记为「已确认」，则文末「剩余待澄清问题表」中不得再将同一问题列为「待确认」。每次更新剩余问题表时，必须对照已有变更记录检查并移除已解决项。
  ```

- [ ] **Step 2: 替换为操作性步骤**

  将上述声明式约束替换为：

  ```markdown
  **change-log 编写规范：**

  **写每条新 CHG 条目前，执行以下步骤：**
  1. 找到当前文档里最后一条 CHG-XXX 的编号 N
  2. 本条编号 = N + 1，写入标题
  3. 禁止跳过、倒插、或事后补写乱序条目；若需在中间补充信息，在当前最新编号后追加新条目

  **写「剩余待澄清问题表」前，执行以下步骤：**
  1. 列出当前 change-log 里所有 CHG 条目涉及的问题描述
  2. 对照剩余问题表，逐行检查：若某问题已在任意 CHG 条目中记录了确认结果，从剩余表中删除该行
  3. 剩余表只保留确实还没有 CHG 确认记录的问题
  ```

- [ ] **Step 3: 运行回归测试确认全绿**

  ```bash
  python3 -m pytest tests/ -v --tb=short -q
  ```

  预期：`54 passed`

- [ ] **Step 4: 提交**

  ```bash
  git add rana/SKILL.md
  git commit -m "fix(skill): stage3 change-log 约束改为操作性步骤，防止跳号和矛盾"
  ```

---

## Task 4：SKILL.md + clarification-list.md — 交付物 D 格式锁定（变更 4）

**Files:**
- Modify: `rana/SKILL.md`（Stage 5 交付物 D 说明段落）
- Modify: `rana/templates/clarification-list.md`（开头说明区块）

- [ ] **Step 1: 在 SKILL.md 交付物 D 说明中添加禁止规则**

  找到 Stage 5「### 交付物 D：待澄清问题清单」段落，当前内容为：

  ```markdown
  ### 交付物 D：待澄清问题清单

  > 未确认内容显式列出，确保需求不带病进入设计。

  **格式**：参照 `templates/clarification-list.md` 结构填写。末尾汇总统计表必须生成，数字根据实际问题数量填写。

  > **截止时间填写建议**：...
  ```

  在「> 未确认内容显式列出...」引用块之后、「**格式**：参照...」之前，插入禁止规则：

  ```markdown
  **禁止输出「已确认项」区块**。交付物 D 只列仍需确认的问题，按确认对象分组（需 PM 确认 / 需研发确认 / 需测试确认 / 需业务确认）。已确认的信息体现在交付物 A 对应字段和 change-log.md 里，不在交付物 D 重复列出。

  若所有问题均已在 Stage 3 确认，交付物 D 仍需输出，但各确认对象的表格可为空（保留表头），汇总统计填 0，并在表格前注明：「本次分析所有澄清问题均已在 Stage 3 对话中确认，详见 change-log.md。」
  ```

- [ ] **Step 2: 在 clarification-list.md 开头说明区块补充禁止规则**

  找到 `rana/templates/clarification-list.md` 的开头说明区块（当前以 `> 本文件为待澄清问题清单的权威格式模板。` 开头）。在该区块最后一行（`> - ⚠ 风险` 行）后追加：

  ```markdown
  >
  > **禁止输出「已确认项」区块**：本清单只列仍需确认的问题。已确认内容记录在 change-log.md 和交付物 A 对应字段，不在此重复。
  ```

- [ ] **Step 3: 运行回归测试确认全绿**

  ```bash
  python3 -m pytest tests/ -v --tb=short -q
  ```

  预期：`54 passed`

- [ ] **Step 4: 提交**

  ```bash
  git add rana/SKILL.md rana/templates/clarification-list.md
  git commit -m "fix(skill): 交付物D禁止输出已确认项区块，锁定格式"
  ```

---

## Task 5：SKILL.md + requirement-card.md — 交付物 A 分组名反例（变更 5）

**Files:**
- Modify: `rana/SKILL.md`（Stage 5 交付物 A 字段约束说明段落）
- Modify: `rana/templates/requirement-card.md`（开头说明区块）

- [ ] **Step 1: 在 SKILL.md 交付物 A 字段约束说明后添加反例**

  找到 Stage 5「### 交付物 A：需求分析卡」段落内的字段名约束说明，当前包含：

  ```markdown
  **字段名强制约束**：分组名和字段名必须严格使用 `templates/requirement-card.md` 中定义的名称，**禁止自定义**。标准分组为：`▌ 基本信息` / `▌ 用户与场景` / `▌ 需求内容` / `▌ 风险与待确认` / `▌ 结论`。标准字段包含：需求名称、版本/迭代号、需求来源、背景说明、业务目标、目标用户、使用场景、核心问题、需求拆解、业务规则、约束条件、优先级、待澄清项、风险点、需求结论（共 15 个）。
  ```

  在该段落之后（「**多需求规则**」之前）紧接添加反例警告：

  ```markdown
  **禁止使用的自定义分组名（反例）：**
  - ✗ `业务目标` → 应为 `▌ 基本信息`（「业务目标」是该分组内的一个**字段名**，不是分组名）
  - ✗ `功能描述` → 应为 `▌ 需求内容`
  - ✗ `约束条件` → 应为 `▌ 需求内容`（「约束条件」是该分组内的一个**字段名**）
  - ✗ `验收标准` → 不是标准分组；相关内容写入 `▌ 需求内容` → 「业务规则」字段，或 `▌ 结论` → 「需求结论」字段
  - ✗ `异常处理` → 不是标准分组；相关内容写入 `▌ 需求内容` → 「业务规则」字段
  ```

- [ ] **Step 2: 在 requirement-card.md 开头说明区块补充反例**

  找到 `rana/templates/requirement-card.md` 的开头说明区块，当前最后一行是：

  ```markdown
  > **字段名强制约束**：分组名和字段名必须严格使用本模板定义的名称，**禁止自定义或替换**。错误示例：将"基本信息"改为"业务目标"，将"需求内容"改为"功能描述"。
  ```

  在该行之后追加：

  ```markdown
  >
  > **禁止使用的自定义分组名（反例）**：`业务目标`、`功能描述`、`约束条件`、`验收标准`、`异常处理`。这些都是字段名或非标准分组名，不得作为 `▌` 分组行使用。
  ```

- [ ] **Step 3: 运行回归测试确认全绿**

  ```bash
  python3 -m pytest tests/ -v --tb=short -q
  ```

  预期：`54 passed`

- [ ] **Step 4: 提交**

  ```bash
  git add rana/SKILL.md rana/templates/requirement-card.md
  git commit -m "fix(skill): 交付物A分组名约束加反例警告，防止自定义分组名"
  ```

---

## Task 6：同步安装 + 最终回归

**Files:**
- 无代码改动，只做安装和验证

- [ ] **Step 1: 同步安装到本地 skill 目录**

  ```bash
  cp -r rana/. ~/.agents/skills/rana/
  ```

- [ ] **Step 2: 验证安装目录内容与源目录一致**

  ```bash
  diff -r rana/ ~/.agents/skills/rana/ --exclude="*.pyc"
  ```

  预期：无输出（完全一致）

- [ ] **Step 3: 运行完整回归测试**

  ```bash
  python3 -m pytest tests/ -v
  ```

  预期：`54 passed`，所有测试绿色，无 warning。

- [ ] **Step 4: 手动验证 validator 仍可运行**

  ```bash
  python3 rana/scripts/quality-validator.py test-runs/test-a-normal
  ```

  预期：退出码 0，输出包含 `✓ PASS`。

- [ ] **Step 5: 最终提交（若前面有未提交的零散改动）**

  ```bash
  git status
  ```

  若有未提交改动：

  ```bash
  git add -A
  git commit -m "chore: sync install rana skill to ~/.agents/skills/rana/"
  ```

  若已全部在 Task 1-5 中提交，则跳过此步。

---

## 完成标准

所有 Task 完成后，以下条件均满足：

- [ ] `python3 -m pytest tests/ -v` → 54 passed
- [ ] `diff -r rana/ ~/.agents/skills/rana/ --exclude="*.pyc"` → 无差异
- [ ] `rana/SKILL.md` Stage 1 的缺失项表格列头为「来源」，有填写规范
- [ ] `rana/SKILL.md` Stage 2 有第 4 条输出规范（检查清单来源列），示例为 4 列格式
- [ ] `rana/SKILL.md` Stage 3 的 change-log 规范为操作性步骤（两段步骤列表）
- [ ] `rana/SKILL.md` Stage 5 交付物 D 有禁止「已确认项」区块的规则
- [ ] `rana/SKILL.md` Stage 5 交付物 A 有自定义分组名反例列表
- [ ] `rana/templates/clarification-list.md` 开头说明有禁止「已确认项」规则
- [ ] `rana/templates/requirement-card.md` 开头说明有反例列表
