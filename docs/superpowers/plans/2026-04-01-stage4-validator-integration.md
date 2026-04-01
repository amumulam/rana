# Stage 4 接入 quality-validator.py 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修改 SKILL.md 的 Stage 4，让 AI 在质量门检验时优先调用 `quality-validator.py` 进行程序化验证，尽早发现问题，降级时回退 AI 自评。

**Architecture:** 仅修改 `ux-requirements-analyzer/SKILL.md` 的 Stage 4 章节，插入「调用验证器」步骤及降级路径。同步安装副本。无新文件，无新测试（验证器行为已有 27 个测试覆盖）。

**Tech Stack:** Markdown（SKILL.md）、Python 3（quality-validator.py 已有）

---

## 背景

当前 Stage 4 完全依赖 AI 自评，存在以下可靠性问题：

| 问题 | 表现 |
|------|------|
| 来源追溯率无法精确计算 | AI 不会逐行数「有标注的行 / 总数据行」 |
| 14 个字段靠记忆核对 | 容易漏检，尤其多功能 PRD（两张卡） |
| 模糊词扫描不可靠 | AI 不会系统性扫描词表 |
| 质量报告不可重复 | 同一份文档 AI 两次判断可能不同 |

`quality-validator.py` 已具备程序化检查能力（5 个文件、来源追溯率、字段完整性、章节完整性、模糊词），且有 27 个测试覆盖。本计划将其接入 Stage 4 的运行时流程。

## 分工

| 检查项 | 负责方 | 原因 |
|--------|--------|------|
| 文件结构（5个文件是否存在） | 验证器 | 确定性检查 |
| 来源追溯率（≥80%） | 验证器 | 逐行计数，AI 不可靠 |
| 字段完整性（14个必填字段） | 验证器 | 词表匹配，AI 容易漏 |
| 章节完整性（5个交付物） | 验证器 | 字符串匹配，AI 可靠但验证器更快 |
| 模糊词检测 | 验证器 | 词表扫描，产生 WARN |
| **正确性** | AI | 需理解语义，验证器无法判断 |
| **一致性** | AI | 跨文件语义比较，验证器无法判断 |
| **可验证性** | AI | 需判断验收标准是否可测，验证器无法判断 |

---

## Task 1：修改 SKILL.md — Stage 4 新增验证器调用步骤

**Files:**
- Modify: `ux-requirements-analyzer/SKILL.md` — Stage 4 章节（`## Stage 4：质量门禁验证` 到 `## Stage 5` 之间）

### 当前 Stage 4 结构（修改前）

```
## Stage 4：质量门禁验证

输入：input-structured.md + gap-analysis.md + change-log.md

加载 references/quality-gates.md，逐维度验证。

### 5维度检查（AI 自评表格）

### 执行规则（5条分支）

### 输出：quality-report.md（模板）
```

### 修改后 Stage 4 结构

```
## Stage 4：质量门禁验证

输入：input-structured.md + gap-analysis.md + change-log.md

### Step A：程序化验证（优先执行）← 新增

### Step B：AI 补充验证（正确性/一致性/可验证性）← 替换原「5维度检查」表

### 执行规则（整合程序化+AI结果）← 更新

### 输出：quality-report.md（模板，加入程序化验证结果区块）← 更新
```

---

- [ ] **Step 1：在 Stage 4「输入」说明后、原「5维度检查」表前，插入 Step A 小节**

  在 `## Stage 4：质量门禁验证` 节的「加载 `references/quality-gates.md`，逐维度验证。」这行**之后**，插入：

  ````markdown
  ### Step A：程序化验证（优先执行）

  若执行环境支持 Bash 工具，**立即运行验证器**：

  ```bash
  python3 ~/.agents/skills/ux-requirements-analyzer/scripts/quality-validator.py <分析目录>
  ```

  > `<分析目录>` = 当前会话中存放 `input-structured.md` 等文件的目录（如 `./my-analysis/`）

  **解读验证器输出：**

  | 验证器输出 | 含义 |
  |-----------|------|
  | `文件结构: ✓ PASS` | 5 个必要文件均存在 |
  | `文件结构: ✗ FAIL` | 有必要文件缺失，无法进入 Stage 5 |
  | `来源追溯: ✓ PASS` | 该文件来源标注率 ≥ 80% |
  | `来源追溯: ✗ FAIL` | 来源标注率 < 80%，需补标后重新运行 |
  | `字段完整性: ✓ PASS` | 需求分析卡 14 个必填字段全部存在 |
  | `字段完整性: ✗ FAIL` | 需求分析卡缺失必填字段，输出中列出缺失项 |
  | `章节完整性: ✓ PASS` | final-analysis.md 包含全部 5 个交付物章节 |
  | `章节完整性: ✗ FAIL` | final-analysis.md 缺失交付物章节 |
  | `模糊表述: ⚠ WARN` | 存在「适当」「合理」等模糊词，需替换为可测量描述 |
  | 退出码 `0` | 程序化检查全部通过（PASS 或仅 WARN） |
  | 退出码 `1` | 存在 FAIL，需修正后重新运行验证器 |

  **若 Bash 不可用（纯对话环境）：**
  跳过本步骤，直接执行 Step B，全程使用 AI 自评。在 `quality-report.md` 的程序化验证结果区块中注明：「程序化验证未执行（环境不支持 Bash）」。
  ````

- [ ] **Step 2：将原「5维度检查」表替换为「Step B：AI 补充验证」**

  删除原有的 5 维度表格（`| 维度 | 核心问题 | 通过标准 |` 整表），替换为：

  ````markdown
  ### Step B：AI 补充验证

  验证器已覆盖：文件结构、来源追溯、字段完整性、章节完整性、模糊词检测。
  以下三个维度需 AI 结合文档内容逐项判断（参考 `references/quality-gates.md` 对应章节）：

  | 维度 | 核心问题 | 通过标准 |
  |------|---------|---------|
  | **正确性** | 需求是否真实反映业务和用户问题？ | 无明显理解偏差；所有推断有来源依据 |
  | **一致性** | 同一需求在不同来源中是否一致？ | 无冲突描述；或冲突已在 change-log 解决 |
  | **可验证性** | 需求能否通过原型/评审/数据验证？ | 核心功能有可测试的验收标准 |

  > **注（Bash 不可用时）**：还需补充自评以下两项：
  > - **完整性**：33 项检查清单通过率 ≥ 80%（参考 `references/analysis-checklist.md`）
  > - **可执行性**：无「适当」「合理」「友好」「TBD」等模糊表述
  ````

- [ ] **Step 3：更新「执行规则」，将验证器结果整合进判断逻辑**

  将原「执行规则」小节替换为：

  ````markdown
  ### 执行规则

  综合 Step A（验证器输出）和 Step B（AI 补充判断）的结果：

  - **全部 PASS**（验证器退出码 0 且 AI 补充三项均 PASS）→ 进入 Stage 5
  - **任意 FAIL**（P0 缺口未补完）→ 返回 Stage 3 补充；修正后重新运行验证器确认
  - **FAIL**（完整性 < 80% 但所有 P0 缺口已补完）→ 可酌情推进 Stage 5，但需在 quality-report.md 和 final-analysis.md 中明确标注剩余 FAIL 项为「已知风险，待后续迭代补充」
  - **仅 WARN** → 可继续，但需在最终文档标注风险点
  - **FAIL 且 Stage 3 已穷尽**（确认方明确无法提供更多信息）→ 可继续生成 Stage 5，但整体质量状态保持 FAIL；交付物 D（待澄清清单）为本次核心产出；在 quality-report.md 和 final-analysis.md 开头明确标注「当前质量状态：FAIL，信息不足，待澄清后重新分析」
  ````

- [ ] **Step 4：更新「输出：quality-report.md」模板，加入程序化验证结果区块**

  在 quality-report.md 模板的 `# 质量门禁报告` 头部信息之后、`## 逐维度结果` 之前，插入：

  ````markdown
  ## 程序化验证结果

  **运行命令**：`python3 ~/.agents/skills/ux-requirements-analyzer/scripts/quality-validator.py <目录>`
  **退出码**：0（PASS）/ 1（FAIL）

  | 检查项 | 结果 | 详情 |
  |--------|------|------|
  | 文件结构 | ✓ PASS | 5/5 文件存在 |
  | input-structured.md 追溯 | ✓ PASS | 95%（42行） |
  | gap-analysis.md 追溯 | ✓ PASS | 88%（25行） |
  | final-analysis.md 追溯 | ✓ PASS | 91%（67行） |
  | 章节完整性 | ✓ PASS | 5/5 交付物章节存在 |
  | 字段完整性 | ✓ PASS | 14/14 必填字段存在 |
  | 模糊表述 | ✓ PASS | 无 |

  > 若 Bash 不可用，本节填写：「程序化验证未执行（环境不支持 Bash）」
  ````

  同时将 `## 逐维度结果` 中的「完整性」和「可执行性」维度注释更新，说明这两项已由验证器程序化判断（Bash 可用时），AI 补充的是正确性/一致性/可验证性三项。

  具体：在「完整性」和「可执行性」条目下各加一行注释：
  - 完整性：`> 来源追溯率和字段完整性已由验证器程序化确认；此处仅补充 AI 对 33 项检查清单语义覆盖的判断`
  - 可执行性：`> 模糊词已由验证器扫描；此处仅补充 AI 对「是否能直接支撑设计决策」的判断`

- [ ] **Step 5：通读修改后的完整 Stage 4，检查逻辑连贯性**

  确认：
  - Step A 和 Step B 的分工表述清晰
  - 「执行规则」中的「验证器退出码 0」和「AI 补充三项均 PASS」两个条件正确对应
  - quality-report.md 模板中程序化验证结果区块的示例数字是占位示例（不是真实值）

- [ ] **Step 6：同步安装副本**

  ```bash
  cp -r ux-requirements-analyzer/. ~/.agents/skills/ux-requirements-analyzer/
  ```

  预期：命令无报错，静默完成。

---

## Task 2：验证修改不破坏现有测试

**Files:**
- Run: `python3 -m pytest tests/ -v`

- [ ] **Step 1：运行全量测试**

  ```bash
  python3 -m pytest tests/ -v
  ```

  预期结果：**27/27 passed**

  > 所有测试针对 `quality-validator.py` 的函数行为，SKILL.md 变化不影响。

- [ ] **Step 2：手动运行验证器确认 CLI 行为不变**

  ```bash
  python3 ux-requirements-analyzer/scripts/quality-validator.py test-runs/test-a-normal
  ```

  预期：输出末尾显示 `状态: ✓ PASS`，退出码 0

  ```bash
  python3 ux-requirements-analyzer/scripts/quality-validator.py test-runs/test-b-edge
  ```

  预期：输出末尾显示 `状态: ✗ FAIL`，退出码 1

- [ ] **Step 3：提交**

  ```bash
  git add ux-requirements-analyzer/SKILL.md
  git commit -m "feat: integrate quality-validator into Stage 4 workflow"
  ```

---

## 自检结果

| 检查项 | 结论 |
|--------|------|
| 有 Bash 时调用验证器 | ✅ Task 1 Step 1 |
| 无 Bash 时降级 AI 自评 | ✅ Task 1 Step 1（降级路径） |
| 验证器输出解读表 | ✅ Task 1 Step 1 |
| AI 补充正确性/一致性/可验证性 | ✅ Task 1 Step 2 |
| Bash 不可用时 AI 补充完整性/可执行性 | ✅ Task 1 Step 2（注释） |
| 执行规则整合两路结果 | ✅ Task 1 Step 3 |
| quality-report.md 模板含程序化结果 | ✅ Task 1 Step 4 |
| 安装副本同步 | ✅ Task 1 Step 6 |
| 测试不回退（27/27） | ✅ Task 2 Step 1 |
| Placeholder 扫描 | ✅ 无 TBD/TODO/「后续实现」 |
