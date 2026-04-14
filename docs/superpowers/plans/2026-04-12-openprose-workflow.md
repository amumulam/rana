# [Rana Workflow] OpenProse 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 创建 OpenProse `.prose` 工作流文件，实现 PDF → Rana 需求分析的自动化串递。

**Architecture:** 将 `rana-workflow.prose` 直接放到 OpenClaw skills 目录（`~/.openclaw/skills/`），使用相对路径引用同级目录下的 mineru-pipeline 和 rana skills。

**Tech Stack:** OpenProse `.prose` 语法、OpenClaw `/prose` 命令

---

## 文件结构

本次实现涉及的文件：

| 文件 | 类型 | 说明 |
|------|------|------|
| `~/.openclaw/skills/rana-workflow.prose` | 新建 | OpenProse 主程序 |
| `AGENTS.md` | 修改 | 更新工作流说明 |

**前置条件**（已存在）：
- `~/.openclaw/skills/mineru-pipeline/` - PDF 解析 skill
- `~/.openclaw/skills/rana/` - UX 需求分析 skill

---

### Task 1: 创建 rana-workflow.prose

**Files:**
- Create: `~/.openclaw/skills/rana-workflow.prose`

- [ ] **Step 1: 编写 rana-workflow.prose**

```bash
cat > ~/.openclaw/skills/rana-workflow.prose << 'EOF'
# Rana Workflow - UX Requirement Analysis
# PDF → Rana 分析 → 输出
#
# 用法：
#   /prose run ~/.openclaw/skills/rana-workflow.prose --prd-path spec.pdf
#   /prose run ~/.openclaw/skills/rana-workflow.prose --prd-path spec.pdf --requirement-name "订单搜索优化"

input prd_path: "PDF 文件路径（用户提供）"
input requirement_name: "需求名称（可选，默认从 PDF 内容提取）"

# 导入 Skills（同级目录，使用 ./ 相对路径）
import "mineru-pipeline" from "./mineru-pipeline"
import "rana" from "./rana"

# ============================================
# AGENTS - 模型按任务复杂度分层
# ============================================

# PDF 解析：Sonnet（结构化提取）
agent pdf-parser:
  model: sonnet
  skills: ["mineru-pipeline"]
  prompt: """
你专门读取和分析 PRD PDF 文档，使用 mineru-pipeline 技能的能力。

提取内容并标注来源：
- 文字内容：[PDF第X页]
- 表格内容：[PDF表格X_Y]
- 图片描述：[PDF截图X_Y]

输出结构化 Markdown，包含：
1. 文档元数据（标题、页数）
2. 每页文字内容（保留段落结构）
3. 表格数据（Markdown 表格格式）
4. 图片位置信息（页码、坐标）

如果 PDF 无法解析，报告具体错误原因。
"""

# 结构化转换：Sonnet（规则性提取）
agent input-structurer:
  model: sonnet
  prompt: """
你将 PDF 内容转换为 UX 需求分析 Stage 1 格式的 input-structured.md。

提取字段：
- 需求名称：从标题或第一节提取
- 版本/迭代号：搜索关键词「版本」「v」「迭代」
- 业务背景：搜索「背景」「目标」「迭代」「现状」
- 目标用户：列表形式，每项标注来源
- 功能点：表格形式（功能名称 | 描述 | 来源）
- 界面信息：如有截图/Figma 链接
- 约束条件：搜索「限制」「约束」「规则」「边界」
- 明显缺失项：未找到的信息标记为 [缺失]

来源追溯规范：
- 文字：[PDF第X页]
- 表格：[PDF表格X_Y]
- 图片：[PDF截图X_Y]
- 缺失：[缺失]

输出路径：ux-requirement-analysis/_temp/input-structured.md
"""

# Rana 分析：Sonnet（需要理解 Skill instructions）
agent rana-analyst:
  model: sonnet
  skills: ["rana"]
  prompt: """
你是 UX 需求分析专家，执行 Rana 的 6 阶段分析流程。

已完成的阶段：
- Stage 1: 输入结构化（使用已生成的 input-structured.md）

待执行的阶段：
- Stage 2: 需求缺口分析（33 项检查清单）→ gap-analysis.md
- Stage 3: 协作对话补充（如有缺口，列出待澄清项）
- Stage 4: 质量门禁验证（5 维度评估）→ quality-report.md
- Stage 5: 整合输出 → final-analysis.md（含 5 项交付物）
- Stage 6: 程序化验证 → 更新 quality-report.md

输出目录结构：
ux-requirement-analysis/{需求名称}/{YYYY-MM-DD}/
  ├── input-structured.md  （已存在）
  ├── gap-analysis.md
  ├── change-log.md
  ├── quality-report.md
  └── final-analysis.md

注意：
- 每个输出文件必须有来源追溯
- Stage 6 执行 quality-validator.py 脚本验证结果
"""

# 验证报告：Sonnet（解读脚本输出）
agent validator:
  model: sonnet
  prompt: """
你运行程序化验证器并解读结果。

执行命令：
python3 ~/.openclaw/skills/rana/scripts/quality-validator.py {analysis_dir}

解读验证器输出：
- 如果返回 PASS：确认质量合格
- 如果返回 FAIL：列出具体问题清单
- 如果返回 WARN：列出警告项

更新 quality-report.md 的 Stage 6 章节：
- 状态：PASS / FAIL / WARN
- 检查项通过率
- 具体问题清单（如有）
- 建议修复方案（如有）
"""

# ============================================
# WORKFLOW
# ============================================

# Phase 1: PDF 解析
let pdf_content = session: pdf-parser
  prompt: "读取并解析 PDF 文件：{prd_path}"

# Phase 2: 结构化转换
let structured_input = session: input-structurer
  prompt: """
将 PDF 内容转换为 Rana Stage 1 格式。
需求名称：{requirement_name}（如果为空则从 PDF 内容提取）
"""
  context: pdf_content

# Phase 3: Rana 分析（核心流程）
session: rana-analyst
  prompt: """
执行完整的 UX 需求分析流程。
输入：input-structured.md（已生成）
需求名称：{requirement_name}

输出所有 5 项交付物，执行 Stage 6 程序化验证。
"""
  context: structured_input

# Phase 4: 最终验证报告（可选，确认状态）
let final_status = session: validator
  prompt: """
确认分析结果质量状态。
分析目录：ux-requirement-analysis/{requirement_name}/{YYYY-MM-DD}/
"""

# 输出结果摘要
output analysis_complete = session "生成结果摘要"
  prompt: """
简要报告分析完成状态：
- 需求名称
- 输出目录路径
- overall 状态（PASS/FAIL/WARN）
- 主要交付物文件列表
"""
  context: final_status
EOF
```

- [ ] **Step 2: 验证文件创建成功**

```bash
ls -la ~/.openclaw/skills/rana-workflow.prose
head -20 ~/.openclaw/skills/rana-workflow.prose
```

---

### Task 2: 测试 OpenProse 编译

- [ ] **Step 1: 在 OpenClaw 中验证语法**

```bash
# OpenClaw 会话中执行
/prose compile ~/.openclaw/skills/rana-workflow.prose
```

Expected: 无语法错误

---

### Task 3: 测试基本执行

- [ ] **Step 1: 找一个测试用 PDF 文件**

```bash
ls test-runs/file-input/fixtures/*.pdf 2>/dev/null || echo "检查是否有可用 PDF"
```

- [ ] **Step 2: 运行工作流（在 OpenClaw 中）**

```bash
/prose run ~/.openclaw/skills/rana-workflow.prose --prd-path test-runs/file-input/fixtures/a-pdf-with-images.pdf
```

- [ ] **Step 3: 验证输出**

```bash
ls -la ux-requirement-analysis/
```

---

### Task 4: 更新 AGENTS.md

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: 添加工作流说明**

在 AGENTS.md 中添加：

```markdown
## OpenProse 工作流

### rana-workflow.prose

自动化 PDF → 需求分析流程：

**位置**：`~/.openclaw/skills/rana-workflow.prose`

**使用**：

```bash
/prose run ~/.openclaw/skills/rana-workflow.prose --prd-path spec.pdf
/prose run ~/.openclaw/skills/rana-workflow.prose --prd-path spec.pdf --requirement-name "需求名称"
```

**依赖**（同级目录）：
- `mineru-pipeline` - PDF 解析
- `rana` - UX 需求分析

**技术原理**：
- `import "name" from "./dir"` 相对路径导入同级 skills
- `agent.skills: ["name"]` 注入 skill instructions 到 subagent
```

---

### Task 5: 自检

- [ ] **Step 1: 检查 Spec 覆盖**

| Spec Requirement | Covering Task |
|-----------------|---------------|
| R-P0-1: OpenProse 程序文件 | Task 1 | 
| R-P0-2: Skills 引用 | Task 1 (使用 ./ 同级路径) |
| R-P0-3: OpenProse CLI 可用性 | Task 2, 3 |

---

## 验收标准

| # | 验收项 | 验证命令 |
|---|--------|---------|
| 1 | prose 文件存在 | `ls ~/.openclaw/skills/rana-workflow.prose` |
| 2 | 语法正确 | `/prose compile rana-workflow.prose` |
| 3 | 可执行 | `/prose run rana-workflow.prose --prd-path ...` |

---

## 依赖项（已存在）

| Skill | 位置 | 状态 |
|-------|------|------|
| mineru-pipeline | `~/.openclaw/skills/mineru-pipeline` | ✅ 已存在 |
| rana | `~/.openclaw/skills/rana` | ✅ 已存在 |