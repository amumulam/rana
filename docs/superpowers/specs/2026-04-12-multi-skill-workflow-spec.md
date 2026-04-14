# Feature Spec: Rana 多技能串递工作流（基于 OpenProse）

**版本**: v3.0-draft
**作者**: Team
**日期**: 2026-04-12
**状态**: Draft

---

## 1. Problem Statement

### 用户问题

UX 设计师在使用 Rana skill 进行需求分析时，当输入为 PDF 文件时无法被正确解析——CLI agent 环境中 `read` 工具对 PDF 返回空内容。设计师需要手动将 PDF 内容转换为 Markdown 或纯文本，才能启动 Rana 分析流程。

**影响人群**: 使用 OpenCode/BlueCode/OpenClaw CLI 环境的 UX 设计师
**发生频率**: 每次需求分析涉及 PDF 输入时（高频场景）
**未解决的成本**:
- 用户体验差：需要手动预处理文件，打断自动化流程
- 时间浪费：每次 PDF 输入都需要额外操作
- 技能价值受限：Rana 无法处理最常见的 PRD 输入格式

### 核心矛盾

| 技术事实 | 影响 |
|---------|------|
| Skill 不是 Tool | Lobster 无法直接调用 Skill |
| 各 Skill 独立运行 | 无现成机制串联多个 Skill |

**解决方案**: 使用 **OpenProse**（`.prose` 格式）——AI session 编程语言，通过 `agent` + `skills[]` 机制串联多个 Skill。

---

## 2. Goals

### 用户目标

| # | 目标 | 衡量方式 |
|---|------|---------|
| U1 | 设计师运行 `/prose run ux-analysis.prose` 自动完成 PDF → 需求分析 | 无需手动预处理 |
| U2 | PDF 内容正确提取并转换为结构化格式 | 来源标注 `[PDF第X页]` 正确生成 |
| U3 | 分析结果质量不因自动化而下降 | 验证器通过率 ≥ 95% |

### 技术目标

| # | 目标 | 衡量方式 |
|---|------|---------|
| T1 | 使用 OpenProse `.prose` 格式实现多 Skill 编排 | 无需自建 Orchestrator |
| T2 | Skill 组件可插拔替换 | 修改 `.prose` 中 `import` + `skills[]` 即可换组件 |

---

## 3. Non-Goals

| # | 非目标 | 原因 |
|---|--------|------|
| NG1 | 支持 Figma 文件直接输入 | Figma 需要 MCP server |
| NG2 | 支持 Excel (.xlsx) 直接输入 | 用户可先导出 PDF |
| NG3 | 自建 Orchestrator Skill | OpenProse 已提供编排能力 |
| NG4 | 使用 Lobster 工作流 | Lobster 不支持 Skill 调用 |
| NG5 | 使用 `.md` v1.0 格式（Forme + VM） | OpenClaw 实际只有 `.prose` 格式 |
| NG6 | 使用 `use "@handle/slug"` 导入 Skills | `use` 只用于导入 programs，必须用 `import` |

---

## 4. OpenProse 技术背景

### OpenProse 核心概念

| 概念 | 说明 | 语法 |
|------|------|------|
| **Agent** | 子 Agent 配置模板（model + prompt + skills） | `agent name:` |
| **Session** | spawn 一个子 Agent 执行任务 | `session: agentName` |
| **Skills** | 附加给 Agent 的 Skill（Instructions注入） | `skills: ["name"]` |
| **Import** | 导入 Skill（从 github/npm/本地） | `import "name" from "source"` |
| **Use** | 导入 Program（从 registry） | `use "@handle/slug"` |

### Import vs Use 关键区别

| 语法 | 用途 | 来源 |
|------|------|------|
| `use "@handle/slug"` | 导入 **OpenProse programs** | p.prose.md registry |
| `import "name" from "source"` | 导入 **Skills** | github / npm / 本地路径 |

**来源格式**：
- `github:handle/repo` → GitHub 仓库
- `npm:@package/name` → npm 包
- `./relative-path` → 本地相对路径

---

## 5. User Stories

### 核心用户：UX 设计师

**US-1: PDF 自动解析触发分析**
> As a UX designer, I want to run `/prose run ux-analysis.prose --prd-path spec.pdf` and get the complete requirement analysis automatically, so that I can skip manual preprocessing.

**US-2: 替换 PDF 解析组件**
> As a power user, I want to edit `ux-analysis.prose` to use a different skill by changing `import "pdf" from "./.skills/pdf"` to `import "pdf" from "./.skills/my-pdf-parser"`, so that I can use specialized parsing.

**US-3: 查看执行状况**
> As a UX designer, I want to see the session output showing which step is running and what result each session produced, so that I know whether the workflow is proceeding.

---

## 6. Requirements

### Must-Have (P0)

#### R-P0-1: OpenProse 程序文件

**描述**: 创建 `ux-analysis.prose` 文件，定义完整的分析流程。

**文件位置**: `rana/workflows/ux-analysis.prose`

**正确语法**:

```prose
# ux-analysis.prose
# PDF → UX 需求分析流程

input prd_path: "PDF 文件路径（用户提供）"
input requirement_name: "需求名称（可选，默认从 PDF 提取）"

# 导入 Skills（使用相对路径）
import "pdf" from "./.skills/pdf"
import "rana" from "./.skills/rana"

# 定义 Agent
agent pdf-parser:
  model: qwen3.5-plus
  skills: ["pdf"]
  prompt: """
    你专门读取和分析 PRD 文档。
    提取结构化内容，标注来源：
    - 文字内容：[PDF第X页]
    - 表格内容：[PDF表格X_Y]
    - 图片描述：[PDF截图X_Y]
    
    输出 Markdown 格式。
  """

agent rana-analyst:
  model: qwen3.5-plus
  skills: ["rana"]
  prompt: """
    你是 UX 需求分析专家。
    执行完整的 6 阶段分析流程：
    - Stage 1: 输入结构化
    - Stage 2: 缺口分析
    - Stage 3: 协作对话
    - Stage 4: 质量门禁
    - Stage 5: 整合输出
    - Stage 6: 程序化验证
    
    输出目录：ux-requirement-analysis/{需求名称}/{日期}/
  """

# 执行流程
let pdf_content = session: pdf-parser
  prompt: "读取 {prd_path}，提取结构化内容"

session: rana-analyst
  prompt: "基于 PDF 内容执行 UX 需求分析"
  context: pdf_content
```

**验收标准**:
- [ ] 符合 `.prose` 语法规范
- [ ] `import` 使用相对路径
- [ ] `skills: []` 放在 agent 定义块内
- [ ] 执行 `prose compile ux-analysis.prose` 无错误

---

#### R-P0-2: 本地 Skills 目录结构

**描述**: 在项目目录下建立 `.skills/` 目录，存放技能引用。

**目录结构**:

```
requirements-analysis/               # 项目根目录
├── .skills/
│   ├── pdf/                         # 链接或复制 pdf skill
│   │   └── SKILL.md
│   └── rana/                        # 链接 rana skill
│   │   └── SKILL.md
│   │   ├── scripts/
│   │   │   └── quality-validator.py
│   │   └── ...
│   └── .gitignore                   # 不提交 .skills/（环境依赖）
│
├── rana/
│   └── workflows/
│       └── ux-analysis.prose        # OpenProse 程序
│
└── ux-requirement-analysis/         # 输出目录
    └── {需求名称}/
        └── {日期}/
            ├── input-structured.md
            ├── gap-analysis.md
            ├── change-log.md
            ├── quality-report.md
            └── final-analysis.md
```

**初始化命令**:

```bash
mkdir -p .skills
ln -s ~/.openclaw/skills/pdf .skills/pdf      # 或 ~/.agents/skills/pdf
ln -s ~/.agents/skills/rana .skills/rana
```

**验收标准**:
- [ ] `.skills/pdf/SKILL.md` 存在且可读
- [ ] `.skills/rana/SKILL.md` 存在且可读
- [ ] `import "pdf" from "./.skills/pdf"` 能正确解析

---

#### R-P0-3: OpenProse CLI 可用性

**描述**: 确保 OpenProse 可通过 OpenClaw `/prose` 命令使用。

**运行方式**:

```bash
# OpenClaw 中运行
/prose run rana/workflows/ux-analysis.prose --prd-path spec.pdf

# 或运行前编译检查
/prose compile rana/workflows/ux-analysis.prose
```

**验收标准**:
- [ ] `/prose help` 返回帮助信息
- [ ] `/prose compile ux-analysis.prose` 无语法错误
- [ ] `/prose run ux-analysis.prose` 能执行流程

---

### Nice-To-Have (P1)

#### R-P1-1: 并行 PDF + Figma 输入

**描述**: 支持同时解析 PDF 和 Figma 设计稿。

```prose
import "figma" from "./.skills/figma"

agent figma-fetcher:
  model: qwen3.5-plus
  skills: ["figma"]
  prompt: "你从 Figma 获取设计稿信息"

input figma_url: "Figma 文件链接（可选）"

# 并行执行
parallel:
  pdf_content = session: pdf-parser
    prompt: "读取 {prd_path}"
  
  design_content = session: figma-fetcher
    prompt: "从 {figma_url} 获取设计稿"

session: rana-analyst
  prompt: "基于 PDF + 设计稿执行分析"
  context: { pdf_content, design_content }
```

---

#### R-P1-2: 错误处理

**描述**: 处理 PDF 解析失败等错误情况。

```prose
try:
  let pdf_content = session: pdf-parser
    prompt: "读取 {prd_path}"

catch:
  session "通知用户：PDF 解析失败，请检查文件格式"
```

---

### Future Considerations (P2)

#### R-P2-1: 多需求并行分析

**描述**: OpenProse `parallel for` 支持并发处理多个需求。

---

#### R-P2-2: 持久化 Agent（Captain's Chair）

**描述**: 使用 `persist: true` 让 Agent 保持记忆，支持交互式分析。

---

## 7. Skills 与 Agent 的集成机制

### 关键原理

| 问题 | 答案 |
|------|------|
| Skill 如何被加载？ | `import "name" from "source"` 导入 skill 目录 |
| Skill 如何被使用？ | `skills: ["name"]` 在 agent 定义中引用 |
| Skill 内容如何注入？ | OpenProse VM 将 SKILL.md 内容注入 subagent prompt |

### 执行流程

```
import "pdf" from "./.skills/pdf"
         │
         ▼
agent pdf-parser:
  skills: ["pdf"]           ← 引用已导入的 skill
         │
         ▼
session: pdf-parser
         │
         ▼
OpenProse VM:
  1. 检测 skills: ["pdf"]
  2. 读取 .skills/pdf/SKILL.md
  3. Spawn subagent (Task tool)
  4. Prompt 包含: session prompt + SKILL.md contents
         │
         ▼
Sub agent 执行（按 pdf skill 的 instructions）
```

---

## 8. Success Metrics

| 指标 | 目标 | 衡量方式 |
|------|------|---------|
| **PDF 直通率** | ≥ 90% | `/prose run` 后生成 final-analysis.md 的成功率 |
| **验证器通过率** | ≥ 95% | quality-validator.py 返回 PASS |
| **平均处理时长** | < 10 分钟 | session 输出显示的运行时间 |

---

## 9. Open Questions（已解决）

| # | 问题 | 状态 | 答案 |
|---|------|------|------|
| Q1 | Skill 如何被 OpenProse 加载？| ✅ 已解决 | `import "name" from "source"` + `skills: ["name"]` |
| Q2 | OpenProse CLI 可用性？| ✅ 已解决 | OpenClaw `/prose` slash 命令 |
| Q3 | Skills 的 source 格式？| ✅ 已解决 | 使用 `./relative-path` 相对路径 |

---

## 10. Timeline Considerations

### Phase 1（准备，1天）
- 建立 `.skills/` 目录和链接
- 创建 `ux-analysis.prose` 文件
- 验证 `/prose compile` 通过

### Phase 2（测试，2天）
- 运行 `/prose run` 测试简单 PDF
- 验证 rana skill 能正确执行
- 调整 session prompts

### Phase 3（完善，1周）
- 完善错误处理
- 添加更多 session（如必要）
- 集成测试

---

## Appendix: 完整示例程序

### ux-analysis.prose

```prose
# UX Requirement Analysis Workflow
# PDF → Rana 分析 → 输出

input prd_path: "PDF 文件路径（用户提供）"
input requirement_name: "需求名称（可选，默认从 PDF 内容提取）"

# 导入 Skills（本地相对路径）
import "pdf" from "./.skills/pdf"
import "rana" from "./.skills/rana"

# ============================================
# AGENTS
# ============================================

agent pdf-parser:
  model: qwen3.5-plus
  skills: ["pdf"]
  prompt: """
    你专门读取和分析 PRD 文档。
    
    任务：
    1. 使用 pdfplumber 提取所有页面文字
    2. 提取表格，保留完整结构
    3. 记录图片位置信息（页码、坐标）
    4. 输出为结构化 Markdown
    
    来源标注规范：
    - 文字内容：[PDF第X页]
    - 表格内容：[PDF表格X_Y]
    - 图片描述：[PDF截图X_Y]
  """

agent input-structurer:
  model: qwen3.5-plus
  prompt: """
    你将 PDF 内容转换为 UX 需求分析 Stage 1 格式。
    
    提取字段：
    - 需求名称
    - 业务背景
    - 功能点清单（表格形式）
    - 目标用户
    - 约束条件
    - 明显缺失项
    
    每项标注来源追溯。
    
    输出文件：ux-requirement-analysis/_temp/input-structured.md
  """

agent rana-analyst:
  model: qwen3.5-plus
  skills: ["rana"]
  prompt: """
    你是 UX 需求分析专家。
    
    基于 input-structured.md 执行完整的 6 阶段分析：
    - Stage 1: 输入结构化（已完成）
    - Stage 2: 需求缺口分析 → gap-analysis.md
    - Stage 3: 协作对话（如有缺口，暂停等待确认）
    - Stage 4: 质量门禁 → quality-report.md
    - Stage 5: 整合输出 → final-analysis.md
    - Stage 6: 程序化验证 → 更新 quality-report.md
    
    工作目录：ux-requirement-analysis/{需求名称}/{YYYY-MM-DD}/
  """

agent validator:
  model: qwen3.5-plus
  prompt: """
    你运行程序化验证并解读结果。
    
    命令：python3 ~/.agents/skills/rana/scripts/quality-validator.py {analysis_dir}
    
    解读验证器输出，更新 quality-report.md 的 Stage 6 章节。
  """

# ============================================
# WORKFLOW
# ============================================

# Step 1: PDF 解析
let pdf_content = session: pdf-parser
  prompt: "读取并解析 {prd_path}"

# Step 2: 结构化转换
let structured_input = session: input-structurer
  prompt: "将 PDF 内容转换为 Stage 1 格式"
  context: pdf_content

# Step 3: Rana 分析
session: rana-analyst
  prompt: "执行完整的 UX 需求分析流程"
  context: structured_input

# Step 4: 验证
session: validator
  prompt: "运行程序化验证并报告结果"
```

### 初始化脚本

```bash
# setup-skills.sh
mkdir -p .skills

# 链接 pdf skill（根据实际位置调整）
if [ -d ~/.openclaw/skills/pdf ]; then
  ln -s ~/.openclaw/skills/pdf .skills/pdf
elif [ -d ~/.agents/skills/pdf ]; then
  ln -s ~/.agents/skills/pdf .skills/pdf
else
  echo "Warning: pdf skill not found"
fi

# 链接 rana skill（本项目本身）
ln -s ../rana .skills/rana

echo "Skills linked. Verify with:"
echo "  ls -la .skills/"
echo "  cat .skills/pdf/SKILL.md"
```