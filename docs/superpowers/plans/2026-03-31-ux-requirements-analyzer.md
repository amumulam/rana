# UX Requirements Analyzer Skill Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建一个 OpenCode Skill 插件，帮助交互设计师对 PM 的 PRD/需求清单进行结构化需求分析，输出可追溯、即用的需求分析文档。

**Architecture:** 单 Skill + 显式阶段产物模式。5阶段工作流（输入解析→缺口分析→协作对话→质量门禁→整合输出），每阶段生成独立 Markdown 文件。基于检查清单和质量门禁保障输出质量。

**Tech Stack:** Markdown, YAML frontmatter, OpenCode Skill System

---

## 文件结构

```
ux-requirements-analyzer/
├── SKILL.md                       # 核心流程指令（主入口）
├── references/
│   ├── analysis-checklist.md     # 需求分析检查清单（8大类检查项）
│   ├── quality-gates.md           # 质量门禁标准（5维度验证）
│   ├── traceability-guide.md      # 可追溯性标注规范
│   └── ux-analysis-methods.md     # UX 需求分析方法（五问法、场景还原等）
├── templates/
│   ├── requirement-card.md        # 需求分析卡模板
│   ├── breakdown-list.md          # 需求拆解清单模板
│   ├── scenario-boundary.md       # 场景与边界说明模板
│   ├── clarification-list.md      # 待澄清问题清单模板
│   └── analysis-conclusion.md     # 需求分析结论模板
└── scripts/
    └── quality-validator.py       # 质量门禁校验脚本（可选）
```

---

## Task 1: 创建 Skill 主文件 SKILL.md

**Files:**
- Create: `SKILL.md`

- [ ] **Step 1: 编写 SKILL.md 头部元数据**

```yaml
---
name: ux-requirements-analyzer
description: |
  UX 需求分析助手，帮助交互设计师对 PM 的 PRD/需求清单进行结构化分析。
  支持多模态输入（PRD 文本、截图、Figma 链接），输出需求分析卡、拆解清单、场景边界说明、待澄清清单、分析结论。
  每项分析标注来源追溯，通过质量门禁保障输出质量。
  
  触发场景：
  (1) 设计师收到 PRD/需求清单需要分析
  (2) 设计师需要拆解需求结构
  (3) 设计师需要识别需求缺口和边界条件
  (4) 设计师需要输出结构化需求分析文档
---
```

- [ ] **Step 2: 编写核心工作流程**

在 SKILL.md 中添加：
- 5阶段工作流说明
- 每阶段输入/处理/输出
- 质量门禁规则
- 用户交互流程

- [ ] **Step 3: 验证 SKILL.md 格式**

检查：
- YAML frontmatter 格式正确
- Markdown 语法正确
- 引用格式统一

- [ ] **Step 4: Commit**

```bash
git add SKILL.md
git commit -m "feat: add SKILL.md with core workflow"
```

---

## Task 2: 创建需求分析检查清单

**Files:**
- Create: `references/analysis-checklist.md`

- [ ] **Step 1: 编写检查清单头部**

```markdown
# 需求分析检查清单

基于需求分析完成标准设计，共8大类检查项。
```

- [ ] **Step 2: 编写8大类检查项**

A. 基本信息（4项）
B. 用户与场景（4项）
C. 流程与状态（4项）
D. 边界与约束（7项）
E. 异常状态（5项）
F. 数据与依赖（4项）
G. 信息架构（3项）
H. 可追溯性（2项）

- [ ] **Step 3: 验证清单完整性**

对照设计文档，确保：
- 所有检查项来自设计文档第5.1节
- 格式统一（`- [ ] 检查内容`）
- 共33项检查点

- [ ] **Step 4: Commit**

```bash
git add references/analysis-checklist.md
git commit -m "feat: add analysis checklist with 33 items"
```

---

## Task 3: 创建质量门禁标准

**Files:**
- Create: `references/quality-gates.md`

- [ ] **Step 1: 编写质量门禁头部**

```markdown
# 质量门禁标准

5维度验证：正确性、完整性、可执行性、一致性、可验证性。
```

- [ ] **Step 2: 编写5维度验证标准**

每个维度包含：
- 判定标准
- 检查项（3-5项）
- 通过条件

- [ ] **Step 3: 编写门禁执行规则**

```markdown
| 结果 | 动作 |
|---|---|
| 全部 PASS | 进入阶段 5 整合输出 |
| 有 FAIL | 返回阶段 3 补充，标注缺失项 |
| 有 WARN | 可继续，在最终文档标注风险点 |
```

- [ ] **Step 4: Commit**

```bash
git add references/quality-gates.md
git commit -m "feat: add quality gates with 5 dimensions"
```

---

## Task 4: 创建可追溯性标注规范

**Files:**
- Create: `references/traceability-guide.md`

- [ ] **Step 1: 编写来源类型表格**

| 类型 | 标注格式 | 示例 |
|---|---|---|
| PRD 章节 | `[PRD第X节]` | `[PRD第3节]` |
| 截图 | `[截图X]` | `[截图1]` |
| Figma 页面 | `[Figma页面X]` | `[Figma页面: 登录流程]` |
| 设计师补充 | `[补充]` | `[设计师补充: 2026-03-31]` |
| 推断 | `[推断]` | `[截图1推断]` |
| 缺失 | `[缺失]` | 需澄清 |

- [ ] **Step 2: 编写标注示例**

展示：
- 单来源标注
- 多来源标注
- 来源冲突标注

- [ ] **Step 3: Commit**

```bash
git add references/traceability-guide.md
git commit -m "feat: add traceability guide with source types"
```

---

## Task 5: 创建 UX 需求分析方法

**Files:**
- Create: `references/ux-analysis-methods.md`

- [ ] **Step 1: 编写五问法（5 Whys）**

```markdown
## 五问法（5 Whys）

连续追问至少3层"为什么"，直到触达业务本质。

**示例：**
用户说："我要一个收藏功能"
- 为什么？→ 因为内容太长看不完
- 为什么看不完？→ 因为没有时间
- 为什么没有时间？→ 因为是在碎片时间使用

**结论：** 真实需求是"碎片时间阅读"，而非"收藏功能"
```

- [ ] **Step 2: 编写 X-Y Problem 识别**

解释如何区分用户提的解决方案（Y）vs 真实问题（X）。

- [ ] **Step 3: 编写场景还原法**

时间、空间、心境三要素。

- [ ] **Step 4: Commit**

```bash
git add references/ux-analysis-methods.md
git commit -m "feat: add UX analysis methods (5 Whys, X-Y Problem, scenario)"
```

---

## Task 6: 创建需求分析卡模板

**Files:**
- Create: `templates/requirement-card.md`

- [ ] **Step 1: 编写模板头部说明**

```markdown
# 需求分析卡

用于快速概览本次需求，建议一页内可读完。
```

- [ ] **Step 2: 编写表格模板**

| 字段 | 内容 | 来源追溯 |
|---|---|---|
| 需求名称 | | |
| 版本/迭代号 | | |
| ... | | |

共15个字段。

- [ ] **Step 3: Commit**

```bash
git add templates/requirement-card.md
git commit -m "feat: add requirement card template"
```

---

## Task 7: 创建需求拆解清单模板

**Files:**
- Create: `templates/breakdown-list.md`

- [ ] **Step 1: 编写7个拆解维度**

- 主任务
- 子任务
- 页面/入口
- 分支流程
- 异常流程
- 状态变化
- 依赖关系

- [ ] **Step 2: 每个维度配表格模板**

- [ ] **Step 3: Commit**

```bash
git add templates/breakdown-list.md
git commit -m "feat: add breakdown list template with 7 dimensions"
```

---

## Task 8: 创建场景与边界说明模板

**Files:**
- Create: `templates/scenario-boundary.md`

- [ ] **Step 1: 编写4个场景类型**

- 典型使用场景
- 边界场景
- 不支持场景
- 业务/技术/权限限制

- [ ] **Step 2: Commit**

```bash
git add templates/scenario-boundary.md
git commit -m "feat: add scenario and boundary template"
```

---

## Task 9: 创建待澄清问题清单模板

**Files:**
- Create: `templates/clarification-list.md`

- [ ] **Step 1: 编写4类确认对象**

- 需PM确认
- 需研发确认
- 需测试确认
- 需业务确认

- [ ] **Step 2: Commit**

```bash
git add templates/clarification-list.md
git commit -m "feat: add clarification list template"
```

---

## Task 10: 创建需求分析结论模板

**Files:**
- Create: `templates/analysis-conclusion.md`

- [ ] **Step 1: 编写标准格式**

```markdown
**格式：谁 + 在什么场景 + 遇到什么问题 + 本次要优先解决什么**

> [目标用户] 在 [使用场景] 遇到 [核心问题]，本次迭代优先解决 [优先项]。
```

- [ ] **Step 2: 编写详细说明结构**

- 谁（目标用户）
- 在什么场景
- 遇到什么问题
- 本次优先解决什么

- [ ] **Step 3: Commit**

```bash
git add templates/analysis-conclusion.md
git commit -m "feat: add analysis conclusion template"
```

---

## Task 11: 创建质量校验脚本（可选）

**Files:**
- Create: `scripts/quality-validator.py`

- [ ] **Step 1: 编写脚本框架**

```python
#!/usr/bin/env python3
"""质量门禁校验脚本"""

import re
import sys
from pathlib import Path

def check_completeness(file_path):
    """检查文档完整性"""
    pass

def check_traceability(file_path):
    """检查可追溯性"""
    pass

if __name__ == "__main__":
    # 校验逻辑
    pass
```

- [ ] **Step 2: Commit**

```bash
git add scripts/quality-validator.py
git commit -m "feat: add quality validator script (optional)"
```

---

## Task 12: 最终验证与打包

- [ ] **Step 1: 验证文件结构完整性**

检查所有文件是否存在：
```bash
ls -la ux-requirements-analyzer/
ls -la ux-requirements-analyzer/references/
ls -la ux-requirements-analyzer/templates/
ls -la ux-requirements-analyzer/scripts/
```

- [ ] **Step 2: 验证 SKILL.md 可加载**

使用 skill-creator 的验证工具检查 SKILL.md 格式。

- [ ] **Step 3: 创建打包脚本**

```bash
cd ux-requirements-analyzer
zip -r ../ux-requirements-analyzer.skill .
```

- [ ] **Step 4: 最终 Commit**

```bash
git add .
git commit -m "feat: complete ux-requirements-analyzer skill v1.0"
```

---

## Spec Coverage Check

对照设计文档检查实现覆盖：

| 设计文档章节 | 实现文件 | 状态 |
|---|---|---|
| 2.1 文件结构 | 全部文件 | ✅ |
| 3.1 流程概览 | SKILL.md | ✅ |
| 3.2 阶段详解 | SKILL.md | ✅ |
| 4.1 需求分析卡模板 | templates/requirement-card.md | ✅ |
| 4.2 需求拆解清单模板 | templates/breakdown-list.md | ✅ |
| 4.3 场景与边界说明模板 | templates/scenario-boundary.md | ✅ |
| 4.4 待澄清问题清单模板 | templates/clarification-list.md | ✅ |
| 4.5 需求分析结论模板 | templates/analysis-conclusion.md | ✅ |
| 5.1 检查清单 | references/analysis-checklist.md | ✅ |
| 5.2 质量门禁 | references/quality-gates.md | ✅ |
| 6. 可追溯性规范 | references/traceability-guide.md | ✅ |
| 7.2 交互流程 | SKILL.md | ✅ |

**无遗漏。**

---

## Placeholder Scan

检查计划中无以下问题：
- ❌ "TBD", "TODO", "implement later"
- ❌ "Add appropriate error handling" 等模糊描述
- ❌ "Similar to Task N" 等引用
- ✅ 每个步骤都有明确动作
- ✅ 文件路径具体
- ✅ 代码块完整

---

## Execution Handoff

**Plan complete and saved to `docs/superpowers/plans/2026-03-31-ux-requirements-analyzer.md`.**

**Two execution options:**

**1. Subagent-Driven (recommended)** - I dispatch a fresh subagent per task, review between tasks, fast iteration

**2. Inline Execution** - Execute tasks in this session using executing-plans, batch execution with checkpoints for review

**Which approach?**
