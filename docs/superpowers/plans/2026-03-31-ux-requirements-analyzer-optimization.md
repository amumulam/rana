# UX Requirements Analyzer — Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 ux-requirements-analyzer Skill 中实施 7 项文档改进，消除 A 类一致性问题（文档间矛盾）和 B 类确定性问题（AI 执行依赖隐式判断）。

**Architecture:** 纯文档/脚本改动，无新功能。先改引用文档（1-5），再改 SKILL.md（6），最后运行 validator 验证（7）。每项变更互相独立，仅 Task 6 依赖前五项完成。

**Tech Stack:** Markdown, Python 3

---

## 文件变更索引

| 文件 | 任务 | 操作 |
|------|------|------|
| `ux-requirements-analyzer/references/analysis-checklist.md` | Task 1 | 修改 |
| `ux-requirements-analyzer/references/traceability-guide.md` | Task 2 | 修改 |
| `ux-requirements-analyzer/templates/requirement-card.md` | Task 3 | 修改 |
| `ux-requirements-analyzer/templates/clarification-list.md` | Task 4 | 修改 |
| `ux-requirements-analyzer/scripts/quality-validator.py` | Task 5 | 修改 |
| `ux-requirements-analyzer/SKILL.md` | Task 6 | 修改 |
| `test-runs/test-a-normal/`, `test-runs/test-b-edge/` | Task 7 | 只读（验证） |

---

## Task 1：analysis-checklist.md — 加优先级标注

**Files:**
- Modify: `ux-requirements-analyzer/references/analysis-checklist.md`

- [ ] **Step 1.1：在文件开头加优先级定义**

在第 1 行 `# 需求分析检查清单` 之后、第 3 行 `在需求分析 Stage 2` 之前，插入以下内容：

```markdown

## 优先级含义

| 优先级 | 含义 |
|--------|------|
| (P0) | 缺失则无法判断功能方向或用户是谁，设计无法开始 |
| (P1) | 缺失影响设计完整性，进入详细设计前必须确认 |
| (P2) | 缺失不阻断设计，开发前确认即可 |

**Stage 4 执行规则**：所有 P0 项缺口未补完则质量状态为 FAIL；P0 全部补完后，完整性 < 80% 可酌情推进并标注已知风险。

---

```

- [ ] **Step 1.2：为每个检查项加优先级后缀**

将 `analysis-checklist.md` 中的每个检查项按以下对应关系加后缀（共 33 项）：

```
A. 基本信息：
  A1 需求名称是否明确               → (P1)
  A2 版本/迭代号是否标注            → (P2)
  A3 需求来源是否记录               → (P1)
  A4 业务背景是否说明               → (P0)

B. 用户与场景：
  B1 目标用户是否定义               → (P0)
  B2 用户角色是否划分               → (P1)
  B3 使用场景是否枚举               → (P0)
  B4 场景触发条件是否说明           → (P1)

C. 流程与状态：
  C1 主流程是否定义                 → (P0)
  C2 分支流程是否枚举               → (P1)
  C3 异常流程是否覆盖               → (P1)
  C4 状态变化是否定义               → (P1)

D. 边界与约束：
  D1 输入边界是否定义               → (P1)
  D2 数量边界是否定义               → (P1)
  D3 时间边界是否定义               → (P1)
  D4 权限边界是否定义               → (P0)
  D5 数据边界是否定义               → (P1)
  D6 技术约束是否标注               → (P2)
  D7 业务规则是否明确               → (P1)

E. 异常状态：
  E1 错误状态处理是否定义           → (P0)
  E2 空状态处理是否定义             → (P0)
  E3 加载状态是否考虑               → (P1)
  E4 网络异常是否处理               → (P1)
  E5 权限不足是否处理               → (P1)

F. 数据与依赖：
  F1 数据实体是否识别               → (P1)
  F2 数据字段是否定义               → (P2)
  F3 依赖关系是否说明               → (P1)
  F4 第三方服务依赖是否标注         → (P2)

G. 信息架构：
  G1 页面结构是否推断               → (P1)
  G2 导航层级是否识别               → (P1)
  G3 内容组织是否说明               → (P2)

H. 可追溯性：
  H1 每项分析是否标注来源           → (P0)
  H2 来源类型是否区分               → (P1)
```

具体 Edit 操作：将每行 `- [ ] Xx ...` 末尾加上对应优先级，例如：
- `- [ ] A1 需求名称是否明确` → `- [ ] A1 需求名称是否明确 (P1)`
- `- [ ] A4 业务背景是否说明（为什么要做这个需求）` → `- [ ] A4 业务背景是否说明（为什么要做这个需求）(P0)`

- [ ] **Step 1.3：验证文件行数合理**

用 `wc -l` 确认文件行数增加了（原 83 行，加优先级定义后约 100 行）：

```bash
wc -l ux-requirements-analyzer/references/analysis-checklist.md
```

预期：约 100-105 行（无精确要求，合理即可）。

- [ ] **Step 1.4：Commit**

```bash
cd /Users/11184725/projects/requirements-analysis
git add ux-requirements-analyzer/references/analysis-checklist.md
git commit -m "feat: add P0/P1/P2 priority labels to analysis checklist"
```

---

## Task 2：traceability-guide.md — 统一推断标注规范

**Files:**
- Modify: `ux-requirements-analyzer/references/traceability-guide.md`

- [ ] **Step 2.1：更新「设计师推断」行**

将来源类型表中第 19 行：

```
| 设计师推断 | `[推断]` | `[截图1推断]` | 必须带推断依据来源 |
```

替换为：

```
| 设计师推断 | `[来源推断]` | `[截图1推断：截图显示移动端界面]` | 必须带推断依据，裸 `[推断]` 不合法 |
```

- [ ] **Step 2.2：在「设计师推断」行下方新增「分析方法推断」行**

在上述行的紧接下方插入：

```
| 分析方法推断 | `[方法名推断：依据]` | `[场景还原推断：基于PRD第1节用户描述]` | 五问法/X-Y分析/场景还原得出的推断 |
```

- [ ] **Step 2.3：更新「推断必须带依据」小节**

找到第 33 行 `推断内容不能凭空出现。格式：\`[来源推断]\`` 之后，在已有示例之后插入「分析方法推断示例」：

```markdown

**分析方法推断示例**：
- `[五问法推断：追问至第3层，真实需求是快速定位未读消息]`
- `[X-Y分析推断：PM 提案是消息中心（Y），真实问题是消息感知缺失（X）]`
- `[场景还原推断：基于PRD第1节「用户反映错过消息」的心境还原]`
```

- [ ] **Step 2.4：在「快速参考」末尾补充分析方法推断条目**

在快速参考代码块的 `[缺失]` 行之前，插入：

```
[场景还原推断：依据]  ← 场景还原分析得出
[五问法推断：依据]    ← 五问法分析得出
[X-Y分析推断：依据]  ← X-Y Problem 分析得出
```

- [ ] **Step 2.5：更新「各阶段应用」表中 Stage 2 的说明**

将：

```
| Stage 2 缺口分析 | 识别到的缺口标注 `[缺失]`；推断的内容标注 `[推断]` |
```

改为：

```
| Stage 2 缺口分析 | 识别到的缺口标注 `[缺失]`；推断的内容标注 `[来源推断]` 或 `[方法名推断：依据]` |
```

- [ ] **Step 2.6：Commit**

```bash
cd /Users/11184725/projects/requirements-analysis
git add ux-requirements-analyzer/references/traceability-guide.md
git commit -m "feat: unify inference annotation rules in traceability guide"
```

---

## Task 3：templates/requirement-card.md — 加权威格式说明

**Files:**
- Modify: `ux-requirements-analyzer/templates/requirement-card.md`

- [ ] **Step 3.1：在文件开头加权威格式说明**

将第 1 行 `# 需求分析卡` 替换为：

```markdown
# 需求分析卡

> 本文件为需求分析卡的权威格式模板。AI 执行时参照此结构填写，`## 填写示例` 区块仅供人工参考，不输出至交付物。
```

- [ ] **Step 3.2：核实14字段完整性**

确认文件中包含以下 14 个字段（不计「需求拆解/待澄清项/需求结论」三个引用字段，只计实质字段）：

```
基本信息（4）：需求名称、版本/迭代号、需求来源、背景说明
用户与场景（3）：目标用户、使用场景、核心问题
需求内容（4）：需求拆解、业务规则、约束条件、优先级
风险与待确认（2）：待澄清项、风险点
结论（1）：需求结论
```

总计 14 字段，与 SKILL.md 原内嵌模板一致。

运行：

```bash
grep -c "| " ux-requirements-analyzer/templates/requirement-card.md
```

预期：不少于 18 行（含表头行）。

- [ ] **Step 3.3：Commit**

```bash
cd /Users/11184725/projects/requirements-analysis
git add ux-requirements-analyzer/templates/requirement-card.md
git commit -m "docs: mark requirement-card.md as authoritative format, suppress example output"
```

---

## Task 4：templates/clarification-list.md — 确保汇总统计表

**Files:**
- Modify: `ux-requirements-analyzer/templates/clarification-list.md`

- [ ] **Step 4.1：在文件开头加说明**

将第 1 行 `# 待澄清问题清单` 替换为：

```markdown
# 待澄清问题清单

> 本文件为待澄清问题清单的权威格式模板。末尾汇总统计表必须生成，数字根据实际问题数量填写。
```

- [ ] **Step 4.2：更新汇总统计表，加 P0/P1/P2 列**

将现有 `## 汇总统计` 表（第 53-61 行）：

```markdown
## 汇总统计

| 确认对象 | 总数 | 已确认 | 待确认 | 风险 |
|---------|------|--------|--------|------|
| PM | | | | |
| 研发 | | | | |
| 测试 | | | | |
| 业务 | | | | |
| **合计** | | | | |
```

替换为：

```markdown
## 汇总统计

| 确认对象 | 问题数 | P0 | P1 | P2 |
|---------|--------|----|----|-----|
| PM | | | | |
| 研发 | | | | |
| 测试 | | | | |
| 业务 | | | | |
| **合计** | | | | |
```

- [ ] **Step 4.3：Commit**

```bash
cd /Users/11184725/projects/requirements-analysis
git add ux-requirements-analyzer/templates/clarification-list.md
git commit -m "feat: require summary stats table in clarification list, add P0/P1/P2 columns"
```

---

## Task 5：scripts/quality-validator.py — 删除死函数

**Files:**
- Modify: `ux-requirements-analyzer/scripts/quality-validator.py`

- [ ] **Step 5.1：删除 `check_traceability_change_log` 函数**

删除第 520-537 行的函数定义（从 `def check_traceability_change_log(content: str) -> dict:` 到最后的 `return _make_result(checked, issues)`，共约 18 行，包含函数 docstring 和函数体）。

确认删除范围（用 Read 工具再次确认行号后删除）：函数从 `def check_traceability_change_log` 开始，到下一个空行 `def _make_result` 之前结束。

- [ ] **Step 5.2：更新文件头部注释**

将第 12-17 行注释：

```python
# 来源追溯检查策略（按文件分级）：
#   - input-structured.md  : 检查所有表格数据行和列表项
#   - final-analysis.md    : 检查5个交付物章节中的表格数据行和列表项（跳过结构引用行）
#   - gap-analysis.md      : 仅检查数据表（目标用户/场景/7维度/边界条件），跳过检查清单表和分析方法区块
#   - change-log.md        : 仅检查 **内容**：开头的列表项（即已澄清的信息行）
#   - quality-report.md    : 跳过（纯AI评估文字，无需来源标注）
```

替换为：

```python
# 来源追溯检查策略（按文件分级）：
#   input-structured.md  : 检查所有表格数据行和列表项（事实提取文档）
#   gap-analysis.md      : 只检查数据表，跳过检查清单和分析方法区块（AI判断内容）
#   final-analysis.md    : 检查5个交付物章节，跳过待澄清清单和引用行
#   change-log.md        : 跳过——协作过程记录，确认方字段已作为来源标注
#   quality-report.md    : 跳过——纯AI评估文档，无需来源标注
```

- [ ] **Step 5.3：验证脚本可正常执行（无 NameError）**

```bash
cd /Users/11184725/projects/requirements-analysis
python3 ux-requirements-analyzer/scripts/quality-validator.py --help 2>&1 || python3 ux-requirements-analyzer/scripts/quality-validator.py 2>&1 | head -5
```

预期：输出用法说明，无 Python 错误。

- [ ] **Step 5.4：Commit**

```bash
cd /Users/11184725/projects/requirements-analysis
git add ux-requirements-analyzer/scripts/quality-validator.py
git commit -m "refactor: remove dead function check_traceability_change_log, update header comments"
```

---

## Task 6：SKILL.md — 综合更新（5 处）

**前置要求：Task 1-5 全部完成**

**Files:**
- Modify: `ux-requirements-analyzer/SKILL.md`

- [ ] **Step 6.1：Stage 5 内嵌模板改为引用 templates/**

将 Stage 5 中每个交付物的内嵌 markdown 代码块，替换为单行引用指令。共 5 处：

**交付物 A（需求分析卡）**，将：

```markdown
### 交付物 A：需求分析卡

> 快速概览本次需求，一页内可读完。

```markdown
## 需求分析卡

| 字段 | 内容 | 来源追溯 |
...（14行表格）...
```
```

替换为：

```markdown
### 交付物 A：需求分析卡

> 快速概览本次需求，一页内可读完。

**格式**：参照 `templates/requirement-card.md` 结构填写。`## 填写示例` 区块仅供参考，不输出至交付物。
```

**交付物 B（需求拆解清单）**，将内嵌代码块替换为：

```markdown
**格式**：参照 `templates/breakdown-list.md` 结构填写。
```

**交付物 C（场景与边界说明）**，将内嵌代码块替换为：

```markdown
**格式**：参照 `templates/scenario-boundary.md` 结构填写。
```

**交付物 D（待澄清问题清单）**，将内嵌代码块替换为：

```markdown
**格式**：参照 `templates/clarification-list.md` 结构填写。末尾汇总统计表必须生成，数字根据实际问题数量填写。
```

**交付物 E（需求分析结论）**，将内嵌代码块替换为：

```markdown
**格式**：参照 `templates/analysis-conclusion.md` 结构填写。
```

- [ ] **Step 6.2：来源标注汇总表对齐**

找到 `## 来源标注规范` 下的表格（约第 473-482 行），将：

```markdown
| 设计师推断 | `[推断]` | `[截图1推断]` |
```

改为：

```markdown
| 设计师推断 | `[来源推断]` | `[截图1推断：截图显示移动端界面]` |
```

在该行下方插入新行：

```markdown
| 分析方法推断 | `[方法名推断：依据]` | `[场景还原推断：基于PRD第1节]` |
```

- [ ] **Step 6.3：Stage 3 加冲突讨论步骤**

在 `**Step 3.3 — 记录变更**` 内容末尾（在 `**Step 3.4 — 循环确认**` 之前），插入：

```markdown

**Step 3.3 补充——若确认结果与已有信息冲突：**

> [确认方A] 说「X」，[确认方B] 说「Y」，两方信息存在冲突。
> 建议 [确认方A] 和 [确认方B] 对齐讨论后确认最终值。
> 我先在 change-log 中记录冲突状态，等讨论完成后更新。

在 change-log 中记录冲突格式：

```markdown
### CHG-N：[描述]（冲突待讨论）
- **冲突**：[确认方A] 说「X」`[确认方A确认]`；[确认方B] 说「Y」`[确认方B确认]`
- **状态**：⚠ 待讨论，需 [确认方A] + [确认方B] 对齐后确认
- **内容**：[讨论完成后填写]
- **影响**：[讨论完成后填写]
```

讨论完成后将内容补全，来源标注为：`[原来源A，已与原来源B冲突，以确认方C为准]`
```

- [ ] **Step 6.4：Stage 4 执行规则加「对话穷尽」分支**

找到 `### 执行规则` 下的列表（约第 275-278 行），在现有规则末尾（`- 有 **WARN** → ...` 之后）插入：

```markdown
- 有 **FAIL**，且 Stage 3 协作对话已穷尽（确认方明确表示无法提供更多信息）
  → 可继续生成 Stage 5，但整体质量状态保持 FAIL
  → 交付物 D（待澄清清单）为本次核心产出
  → 在 quality-report.md 和 final-analysis.md 开头明确标注「当前质量状态：FAIL，信息不足，待澄清后重新分析」
```

- [ ] **Step 6.5：加多功能 PRD 说明节**

在 `## 工作流概览` 结束（`---` 分隔线）之后、`## Stage 1：输入解析与结构化` 之前，插入：

```markdown
## 多功能需求处理

当 PRD 包含多个独立功能点时，按以下方式组织：

**Stage 1**：提取时识别功能点清单，向用户确认功能边界和数量。

**Stage 2**：gap-analysis.md 按功能点分节，每节独立执行7维度拆解和缺口分析：
```
  ## 功能一：[名称]
  ## 功能二：[名称]
```
检查清单在文件末尾统一汇总（合并所有功能点通过率）。

**Stage 4**：质量门禁基于合并通过率；P0 缺口按功能点独立判断（每个功能点的 P0 缺口均需补完）。

**Stage 5**：
- 交付物 A（需求分析卡）× 每功能点一份
- 交付物 B（拆解清单）× 每功能点一份
- 交付物 C（场景边界）× 每功能点一份
- 交付物 D（待澄清清单）× 1份（跨功能点汇总）
- 交付物 E（分析结论）× 1份（整体结论）

---

```

- [ ] **Step 6.6：Commit**

```bash
cd /Users/11184725/projects/requirements-analysis
git add ux-requirements-analyzer/SKILL.md
git commit -m "feat: SKILL.md 5 updates — template refs, traceability table, conflict flow, exhausted-dialog branch, multi-feature PRD"
```

---

## Task 7：测试验证

**前置要求：Task 1-6 全部完成**

**Files:**
- Read-only: `test-runs/test-a-normal/`, `test-runs/test-b-edge/`
- Script: `ux-requirements-analyzer/scripts/quality-validator.py`

- [ ] **Step 7.1：运行 test-a-normal 验证**

```bash
cd /Users/11184725/projects/requirements-analysis
python3 ux-requirements-analyzer/scripts/quality-validator.py test-runs/test-a-normal/
```

预期输出末尾：
```
  状态: ✓ PASS
```

- [ ] **Step 7.2：运行 test-b-edge 验证**

```bash
cd /Users/11184725/projects/requirements-analysis
python3 ux-requirements-analyzer/scripts/quality-validator.py test-runs/test-b-edge/
```

预期输出末尾：
```
  状态: ✓ PASS
```

- [ ] **Step 7.3：确认脚本无 Python 错误**

如任意一步出现 `NameError`、`AttributeError` 或 `SyntaxError`，返回 Task 5 检查死函数删除是否完整。

- [ ] **Step 7.4：同步安装副本**

```bash
cp -r /Users/11184725/projects/requirements-analysis/ux-requirements-analyzer/ \
      ~/.agents/skills/ux-requirements-analyzer/
```

验证同步：

```bash
diff -r /Users/11184725/projects/requirements-analysis/ux-requirements-analyzer/ \
        ~/.agents/skills/ux-requirements-analyzer/ \
        --exclude="__pycache__"
```

预期：无任何差异输出。

- [ ] **Step 7.5：最终 Commit**

```bash
cd /Users/11184725/projects/requirements-analysis
git add .
git commit -m "chore: verify all 7 optimization changes pass validator, sync install copy"
```

---

## Self-Review

### Spec coverage check

| 设计文档变更项 | 对应任务 |
|-------------|---------|
| 变更1：analysis-checklist.md 加优先级标注 | Task 1 ✓ |
| 变更2：traceability-guide.md 统一推断规范 | Task 2 ✓ |
| 变更3：SKILL.md 多处更新（5处） | Task 6 ✓ |
| 变更4：templates/requirement-card.md 加说明 | Task 3 ✓ |
| 变更5：templates/clarification-list.md 汇总表 | Task 4 ✓ |
| 变更6：quality-validator.py 删死函数 | Task 5 ✓ |
| 变更7：测试验证 | Task 7 ✓ |

**所有设计文档中的变更均有对应任务，无遗漏。**

### Notes for executor

- Task 1-5 互相独立，可并行执行（见 dispatching-parallel-agents skill）
- Task 6 必须等 Task 1-5 完成后才能执行（SKILL.md 引用的文档已就绪）
- Task 7 必须等所有前置任务完成
- 删除死函数时，注意确认 `check_traceability_change_log` 在 `TRACEABILITY_CHECKERS` 字典中已是 `None`（不调用该函数），所以删除后不会影响运行
