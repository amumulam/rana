# Rana 多技能串递工作流实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 构建基于 OpenClaw Lobster 的多技能串递工作流，将 PDF 解析能力委托给 pdf skill，生成结构化 markdown 后输入 rana skill 进行 UX 需求分析。

**Architecture:** 采用 Lobster workflow 作为编排层，通过步骤管道串联 pdf skill（文件解析）和 rana skill（需求分析）。pdf skill 输出结构化 markdown，rana skill 进行 5 阶段分析流程，验证器做最终质检。

**Tech Stack:** OpenClaw Lobster DSL、pdf skill (pdfplumber)、rana skill (quality-validator.py)、JSON 管道、state.json 外部记忆

---

## 设计背景与约束

### 核心问题

当前 rana skill 无法直接解析 PDF 文件（`read` 工具在 CLI agent 环境下对 PDF 返回空内容）。

### 两份参考文档对比

| 文档 | 核心思路 | 适用场景 |
|------|---------|---------|
| `workflow/report.md` | 自建混合编排架构（Orchestrator Skill + SOP + state.json + sessions_spawn） | 未了解 Lobster 时的方案，架构复杂，需自建调度器 |
| `workflow/lobster.md` | 使用 OpenClaw Lobster DSL（`.lobster` 文件 + JSON 管道 + llm-task） | 官方推荐的确定性工作流方案，简单轻量 |

**结论**：采用 Lobster 方案作为串递机制，利用其「小命令 + JSON 管道」模式串联技能。

### 关键约束

1. **PDF 解析委托**：pdf skill 负责 PDF → Markdown 转换（使用 pdfplumber 提取文字/表格/图片元数据）
2. **技能隔离**：各技能独立执行，通过 JSON/文件管道传递数据
3. **状态持久化**：使用 `state.json` 作为外部记忆，避免 LLM 遗忘 sessionId
4. **校验闭环**：rana 的 quality-validator.py 作为最后质检步骤

---

## 架构设计

### 整体流程

```
输入: PDF 文件
       │
       ▼
Step 1: pdf skill 解析  →  input-structured.md (Stage 1 格式)
       │
       ▼
Step 2: rana skill 分析  →  gap-analysis.md, change-log.md, final-analysis.md
       │
       ▼
Step 3: quality-validator  →  更新 quality-report.md
```

### Lobster 工作流定义

```yaml
# ux-requirement-analysis.lobster
name: ux-requirement-analysis
args:
  input_file:
    required: true
  requirement_name:
    default: "未命名需求"
  output_dir:
    default: "ux-requirement-analysis"

steps:
  # Step 1: PDF 解析 → Markdown
  - id: parse_pdf
    command: >-
      openclaw.invoke --tool pdf --action extract --args-json
      '{"input":"{{input_file}}","format":"markdown","output":"{{output_dir}}/_temp/pdf-content.md"}'

  # Step 2: 提取结构化信息 (LLM 辅助)
  - id: structure_input
    command: >-
      openclaw.invoke --tool llm-task --action json --args-json
      '{"prompt":"将 PDF 内容转换为 rana Stage 1 格式的 input-structured.md","input_file":"{{output_dir}}/_temp/pdf-content.md","schema":{"type":"object","properties":{"requirement_name":{"type":"string"},"background":{"type":"string"},"features":{"type":"array"},"constraints":{"type":"array"}}}}'
    stdin: $parse_pdf.stdout

  # Step 3: 写入 input-structured.md
  - id: write_input_structured
    command: >-
      openclaw.invoke --tool write --args-json
      '{"path":"{{output_dir}}/{{requirement_name}}/{{date}}/input-structured.md","content":"{{structure_input.json}}"}'

  # Step 4: rana 需求分析 (多阶段)
  - id: rana_analysis
    command: >-
      openclaw.invoke --tool skill --action run --args-json
      '{"skill":"rana","workspace":"{{output_dir}}/{{requirement_name}}/{{date}}"}'
    stdin: $write_input_structured.stdout
    timeout: 600000

  # Step 5: 程序化验证
  - id: validate
    command: >-
      python3 ~/.openclaw/skills/rana/scripts/quality-validator.py {{output_dir}}/{{requirement_name}}/{{date}}

  # Step 6: 输出结果
  - id: output_result
    command: >-
      openclaw.invoke --tool message --action send --args-json
      '{"content":"需求分析完成，报告路径：{{output_dir}}/{{requirement_name}}/{{date}}/final-analysis.md"}'
    condition: $validate.returncode == 0
```

---

## 文件结构设计

### 技能目录布局

```
~/.openclaw/skills/
├── pdf/                      # 已存在的 PDF 处理技能
│   ├── SKILL.md
│   └── scripts/
│       └── convert_pdf_to_structured.py  ← 新增：PDF → rana 格式转换脚本
│
└── rana/                     # UX 需求分析技能
│   ├── SKILL.md
│   ├── scripts/
│   │   └── quality-validator.py
│   ├── references/
│   └── templates/
│
└── workflows/                # 工作流定义目录（新增）
    ├── ux-requirement-analysis.lobster  ← Lobster 工作流定义
    ├── state.json            ← 运行状态（外部记忆）
    └── runs/                 ← 运行记录
        └── {run_id}/
            ├── input.pdf
            └── outputs/
```

### 运行时目录约定

```
ux-requirement-analysis/
└── {需求名称}/
    └── {YYYY-MM-DD}/
        ├── input-structured.md    ← pdf skill + llm-task 生成
        ├── gap-analysis.md        ← rana Stage 2
        ├── change-log.md          ← rana Stage 3
        ├── quality-report.md      ← rana Stage 4 + Stage 6
        └── final-analysis.md      ← rana Stage 5
```

---

## state.json Schema

```json
{
  "run_id": "run_20260412_113700",
  "status": "running",
  "current_step": "parse_pdf",
  "args": {
    "input_file": "inputs/spec.pdf",
    "requirement_name": "订单搜索优化",
    "output_dir": "ux-requirement-analysis"
  },
  "steps_completed": ["parse_pdf", "structure_input"],
  "outputs": {
    "parse_pdf": "ux-requirement-analysis/_temp/pdf-content.md",
    "structure_input": {
      "requirement_name": "订单搜索优化",
      "background": "...",
      "features": [...]
    }
  },
  "errors": []
}
```

---

## 实现任务分解

---

### Task 1: 创建 Lobster 工作流定义文件

**Files:**
- Create: `~/.openclaw/skills/workflows/ux-requirement-analysis.lobster`

- [ ] **Step 1: 创建 workflows 目录**

```bash
mkdir -p ~/.openclaw/skills/workflows
```

- [ ] **Step 2: 编写 Lobster 工作流定义**

```yaml
name: ux-requirement-analysis
args:
  input_file:
    required: true
    description: "PDF 需求文档路径"
  requirement_name:
    default: "未命名需求"
    description: "需求名称，用于组织输出目录"
  output_dir:
    default: "ux-requirement-analysis"
    description: "输出根目录"

steps:
  - id: parse_pdf
    description: "使用 pdf skill 解析 PDF 文件"
    command: python3 ~/.openclaw/skills/pdf/scripts/convert_pdf_to_structured.py "{{input_file}}" "{{output_dir}}/_temp/"
    outputs:
      stdout: json
    onSuccess: write_state

  - id: write_state
    description: "更新 state.json"
    command: >-
      openclaw.invoke --tool write --args-json
      '{"path":"{{output_dir}}/.state.json","content":{"run_id":"{{run_id}}","status":"parsing_complete","pdf_output":"$parse_pdf.stdout"}}'

  - id: structure_input
    description: "LLM 提取结构化信息"
    command: >-
      openclaw.invoke --tool llm-task --action json --args-json
      '{"prompt":"将以下 PDF 内容转换为 UX 需求分析 Stage 1 格式。提取：需求名称、业务背景、目标用户、功能点清单、约束条件。每项标注来源 [PDF第X页] 或 [PDF截图X]","schema":{"type":"object","properties":{"requirement_name":{"type":"string"},"version":{"type":"string"},"background":{"type":"string"},"target_users":{"type":"array"},"features":{"type":"array","items":{"type":"object","properties":{"name":{"type":"string"},"description":{"type":"string"},"source":{"type":"string"}}}},"constraints":{"type":"array"},"missing_items":{"type":"array"}}}}'
    stdin: $parse_pdf.stdout

  - id: create_output_dir
    description: "创建输出目录结构"
    command: mkdir -p "{{output_dir}}/{{structure_input.json.requirement_name}}/{{date}}"

  - id: write_input_structured
    description: "写入 input-structured.md"
    command: >-
      openclaw.invoke --tool write --args-json
      '{"path":"{{output_dir}}/{{structure_input.json.requirement_name}}/{{date}}/input-structured.md","content":"{{structure_input.formatted_markdown}}"}'

  - id: rana_analysis
    description: "执行 rana 需求分析（5 阶段）"
    command: >-
      openclaw.invoke --tool skill --action run --args-json
      '{"skill":"rana","prompt":"请基于 {{output_dir}}/{{structure_input.json.requirement_name}}/{{date}}/input-structured.md 进行完整的需求分析"}'
    timeoutMs: 600000
    approval: optional

  - id: validate
    description: "运行程序化验证器"
    command: python3 ~/.openclaw/skills/rana/scripts/quality-validator.py "{{output_dir}}/{{structure_input.json.requirement_name}}/{{date}}"

  - id: report_result
    description: "输出分析结果"
    command: >-
      openclaw.invoke --tool message --action send --args-json
      '{"content":"需求分析完成。状态：{{validate.status}}，报告路径：{{output_dir}}/{{structure_input.json.requirement_name}}/{{date}}/final-analysis.md"}'
```

- [ ] **Step 3: 保存文件**

保存至：`~/.openclaw/skills/workflows/ux-requirement-analysis.lobster`

---

### Task 2: 创建 PDF 结构化转换脚本

**Files:**
- Create: `~/.openclaw/skills/pdf/scripts/convert_pdf_to_structured.py`

- [ ] **Step 1: 编写 PDF 解析脚本**

```python
#!/usr/bin/env python3
"""
PDF → 结构化 Markdown 转换脚本
用于 Lobster 工作流的 Step 1

输入：PDF 文件路径
输出：JSON（包含文字内容、表格、图片元数据）
"""

import sys
import json
import re
from pathlib import Path

try:
    import pdfplumber
except ImportError:
    print(json.dumps({"error": "pdfplumber not installed", "hint": "pip install pdfplumber"}))
    sys.exit(1)


def extract_pdf_content(pdf_path: str) -> dict:
    """提取 PDF 内容，返回结构化 JSON"""
    result = {
        "pages": [],
        "tables": [],
        "images": [],
        "metadata": {}
    }
    
    with pdfplumber.open(pdf_path) as pdf:
        result["metadata"] = {
            "page_count": len(pdf.pages),
            "title": pdf.metadata.get("Title", ""),
            "author": pdf.metadata.get("Author", "")
        }
        
        for i, page in enumerate(pdf.pages, 1):
            page_content = {
                "page_number": i,
                "text": page.extract_text() or "",
                "tables": [],
                "images": []
            }
            
            # 提取表格
            tables = page.extract_tables()
            for j, table in enumerate(tables, 1):
                if table and len(table) > 0:
                    page_content["tables"].append({
                        "table_id": f"T{i}_{j}",
                        "rows": len(table),
                        "headers": table[0] if table else [],
                        "data": table[1:] if len(table) > 1 else []
                    })
            
            # 提取图片元数据（尺寸、位置）
            images = page.images
            for k, img in enumerate(images, 1):
                page_content["images"].append({
                    "image_id": f"IMG{i}_{k}",
                    "x0": img.get("x0"),
                    "y0": img.get("top"),
                    "width": img.get("width"),
                    "height": img.get("height")
                })
            
            result["pages"].append(page_content)
    
    return result


def format_as_markdown(content: dict) -> str:
    """将提取内容格式化为 Markdown"""
    lines = []
    lines.append(f"# PDF 内容提取")
    lines.append(f"\n**页数**: {content['metadata']['page_count']}")
    lines.append(f"**标题**: {content['metadata']['title']}\n")
    
    for page in content["pages"]:
        lines.append(f"\n## 第 {page['page_number']} 页\n")
        
        # 文字内容
        if page["text"]:
            lines.append(page["text"])
        
        # 表格
        for table in page["tables"]:
            lines.append(f"\n### 表格 {table['table_id']}\n")
            if table["headers"]:
                header_row = "| " + " | ".join(str(h) for h in table["headers"]) + " |"
                separator = "|" + "|".join(["---" for _ in table["headers"]]) + "|"
                lines.append(header_row)
                lines.append(separator)
                for row in table["data"]:
                    data_row = "| " + " | ".join(str(cell) if cell else "" for cell in row) + " |"
                    lines.append(data_row)
        
        # 图片说明
        if page["images"]:
            lines.append(f"\n**图片**: {len(page['images'])} 张")
            for img in page["images"]:
                lines.append(f"- {img['image_id']}: ({img['x0']}, {img['y0']}) {img['width']}x{img['height']}")
    
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "Usage: convert_pdf_to_structured.py <pdf_path> [output_dir]"}))
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_dir = sys.argv[2] if len(sys.argv) > 2 else None
    
    if not Path(pdf_path).exists():
        print(json.dumps({"error": f"File not found: {pdf_path}"}))
        sys.exit(1)
    
    content = extract_pdf_content(pdf_path)
    
    # 输出 JSON（供 Lobster 管道使用）
    output = {
        "status": "success",
        "source": pdf_path,
        "content": content,
        "markdown": format_as_markdown(content)
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))
    
    # 如果指定了输出目录，写入文件
    if output_dir:
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        md_path = Path(output_dir) / "pdf-content.md"
        md_path.write_text(output["markdown"], encoding="utf-8")
        json_path = Path(output_dir) / "pdf-content.json"
        json_path.write_text(json.dumps(content, ensure_ascii=False, indent=2), encoding="utf-8")


if __name__ == "__main__":
    main()
```

- [ ] **Step 2: 测试脚本**

```bash
python3 ~/.openclaw/skills/pdf/scripts/convert_pdf_to_structured.py test-runs/file-input/fixtures/a-pdf-with-images.pdf
```

Expected: JSON 输出包含 `"pages"`, `"tables"`, `"images"` 字段

---

### Task 3: 创建 LLM 输入结构化配置

**Files:**
- Create: `~/.openclaw/skills/workflows/input-structured-schema.json`

- [ ] **Step 1: 定义 JSON Schema**

```json
{
  "$schema": "http://json-schema.org/draft-07/schema#",
  "title": "UX Requirement Analysis Stage 1 Input",
  "type": "object",
  "properties": {
    "requirement_name": {
      "type": "string",
      "description": "需求名称"
    },
    "version": {
      "type": "string",
      "description": "版本/迭代号"
    },
    "analysis_date": {
      "type": "string",
      "format": "date",
      "description": "分析日期 YYYY-MM-DD"
    },
    "background": {
      "type": "string",
      "description": "业务背景与迭代目标"
    },
    "target_users": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "role": { "type": "string" },
          "description": { "type": "string" },
          "source": { "type": "string" }
        }
      },
      "description": "目标用户"
    },
    "features": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "id": { "type": "integer" },
          "name": { "type": "string" },
          "description": { "type": "string" },
          "source": { "type": "string" },
          "priority": { "type": "string", "enum": ["P0", "P1", "P2"] }
        },
        "required": ["id", "name", "description", "source"]
      },
      "description": "功能点清单"
    },
    "screens": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "screen_id": { "type": "string" },
          "description": { "type": "string" },
          "source": { "type": "string" }
        }
      },
      "description": "界面信息（来自截图/PDF图片）"
    },
    "constraints": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "type": { "type": "string", "enum": ["技术", "权限", "业务规则", "时间", "资源"] },
          "description": { "type": "string" },
          "source": { "type": "string" }
        }
      },
      "description": "约束条件"
    },
    "missing_items": {
      "type": "array",
      "items": {
        "type": "object",
        "properties": {
          "item": { "type": "string" },
          "impact": { "type": "string", "enum": ["高", "中", "低"] },
          "clarification_needed": { "type": "string" },
          "source": { "type": "string", "const": "[缺失]" }
        }
      },
      "description": "明显缺失项"
    }
  },
  "required": ["requirement_name", "features"]
}
```

---

### Task 4: 编写 LLM Task Prompt 模板

**Files:**
- Create: `~/.openclaw/skills/workflows/prompts/structure-pdf-content.md`

- [ ] **Step 1: 创建 Prompt 模板**

```markdown
# PDF 内容结构化 Prompt

## 任务
将 PDF 提取的内容转换为 UX 需求分析 Stage 1 格式的结构化数据。

## 输入
PDF 内容 JSON，包含：
- pages: 每页文字内容
- tables: 表格数据
- images: 图片元数据（位置、尺寸）

## 输出格式
符合 `input-structured-schema.json` 的 JSON 对象。

## 提取规则

### 1. 需求名称
- 通常在文档标题或第一节
- 如果无法确定，使用「未命名需求」
- 来源标注：[PDF第X页]

### 2. 业务背景
- 搜索关键词：「背景」「目标」「迭代」「背景说明」
- 合并相关段落，保持语义完整
- 来源标注：[PDF第X页]

### 3. 功能点
- 从标题层级识别功能章节（如「## 功能一」「### 1.1」）
- 从表格提取功能列表（如有「功能」「描述」列）
- 每个功能点需有：
  - 名称（简短）
  - 描述（一句话）
  - 来源（[PDF第X页] 或 [PDF表格X]）

### 4. 界面信息
- PDF 图片标记为截图来源
- 来源格式：[PDF截图X]

### 5. 约束条件
- 搜索关键词：「限制」「约束」「规则」「边界」「条件」
- 分类：技术约束、权限规则、业务规则

### 6. 缺失项
- 未找到的信息标记为 [缺失]
- 列出影响程度：高/中/低

## 来源标注规范
- 文字内容：[PDF第X页]
- 表格数据：[PDF表格X_Y] (X=页号，Y=表格序号)
- 图片内容：[PDF截图X_Y]
- 信息缺失：[缺失]

## 输出示例
```json
{
  "requirement_name": "订单搜索优化",
  "version": "v1.5",
  "background": "当前订单搜索功能效率低...",
  "features": [
    {"id": 1, "name": "智能搜索", "description": "...", "source": "[PDF第2页]"},
    {"id": 2, "name": "筛选优化", "description": "...", "source": "[PDF表格3_1]"}
  ],
  "screens": [
    {"screen_id": "IMG1_1", "description": "搜索结果页", "source": "[PDF截图1_1]"}
  ],
  "missing_items": [
    {"item": "权限规则", "impact": "高", "clarification_needed": "不同角色的搜索范围", "source": "[缺失]"}
  ]
}
```
```

---

### Task 5: 修改 rana SKILL.md 支持 Lobster 调用

**Files:**
- Modify: `rana/SKILL.md:180-200`（PDF 文件处理部分）

- [ ] **Step 1: 更新 PDF 处理说明**

当前 SKILL.md 第 196 行说明：
> "直接将 `.pdf` 文件上传给模型即可。模型原生支持多模态读取"

需要更新为：

```markdown
**PDF 文件处理模式**：

### 模式 A：Lobster 工作流调用（推荐）
当通过 `ux-requirement-analysis.lobster` 工作流触发时，PDF 文件由前置的 pdf skill 解析，生成结构化 markdown 后自动传入 Stage 1。无需用户手动处理。

调用方式：
```bash
lobster run ux-requirement-analysis.lobster --args-json '{"input_file":"spec.pdf","requirement_name":"订单搜索"}'
```

### 模式 B：直接调用（CLI Agent 环境）
在 CLI agent 环境中，`read` 工具无法直接读取 PDF 内容。需先运行 PDF 解析脚本：
```bash
python3 ~/.agents/skills/pdf/scripts/convert_pdf_to_structured.py spec.pdf ux-requirement-analysis/_temp/
```
然后读取生成的 `pdf-content.md` 作为输入。

### Web UI 环境
在支持文件上传的 Web UI 环境中，可直接上传 PDF 文件，模型原生支持多模态读取。
```

---

### Task 6: 创建工作流运行脚本

**Files:**
- Create: `~/.openclaw/skills/workflows/run-analysis.sh`

- [ ] **Step 1: 创建 Shell 入口脚本**

```bash
#!/bin/bash
# UX Requirement Analysis Workflow Runner
# Usage: run-analysis.sh <pdf_file> [requirement_name]

set -e

PDF_FILE="${1:-}"
REQ_NAME="${2:-未命名需求}"

if [[ -z "$PDF_FILE" ]]; then
    echo "Usage: run-analysis.sh <pdf_file> [requirement_name]"
    exit 1
fi

if [[ ! -f "$PDF_FILE" ]]; then
    echo "Error: File not found: $PDF_FILE"
    exit 1
fi

# 生成运行 ID
RUN_ID="run_$(date +%Y%m%d_%H%M%S)"
DATE=$(date +%Y-%m-%d)

# 创建输出目录
OUTPUT_DIR="ux-requirement-analysis"
mkdir -p "$OUTPUT_DIR/_temp"

# 初始化 state.json
STATE_FILE="$OUTPUT_DIR/.state.json"
cat > "$STATE_FILE" << EOF
{
  "run_id": "$RUN_ID",
  "status": "started",
  "current_step": "parse_pdf",
  "args": {
    "input_file": "$PDF_FILE",
    "requirement_name": "$REQ_NAME",
    "output_dir": "$OUTPUT_DIR"
  },
  "date": "$DATE",
  "steps_completed": [],
  "errors": []
}
EOF

echo "[$RUN_ID] Starting UX requirement analysis..."
echo "Input: $PDF_FILE"
echo "Requirement: $REQ_NAME"

# Step 1: PDF 解析
echo "Step 1: Parsing PDF..."
python3 ~/.openclaw/skills/pdf/scripts/convert_pdf_to_structured.py "$PDF_FILE" "$OUTPUT_DIR/_temp/" > "$OUTPUT_DIR/_temp/pdf-parse-result.json"

# 更新 state
python3 -c "
import json
state = json.load(open('$STATE_FILE'))
state['status'] = 'pdf_parsed'
state['steps_completed'].append('parse_pdf')
state['outputs'] = {'pdf_content': '$OUTPUT_DIR/_temp/pdf-content.md'}
json.dump(state, open('$STATE_FILE', 'w'), indent=2)
"

# Step 2: Lobster 工作流执行
echo "Step 2: Running Lobster workflow..."
lobster run ~/.openclaw/skills/workflows/ux-requirement-analysis.lobster \
    --args-json '{"input_file":"$PDF_FILE","requirement_name":"$REQ_NAME","run_id":"$RUN_ID"}'

echo "Analysis complete. Check: $OUTPUT_DIR/$REQ_NAME/$DATE/"
```

---

### Task 7: 编写集成测试

**Files:**
- Create: `tests/workflow/test_lobster_workflow.py`
- Create: `tests/workflow/fixtures/sample-prd.pdf`

- [ ] **Step 1: 创建测试文件**

```python
import subprocess
import json
import tempfile
from pathlib import Path
import pytest

WORKFLOW_DIR = Path.home() / ".openclaw" / "skills" / "workflows"
PDF_SCRIPT = Path.home() / ".openclaw" / "skills" / "pdf" / "scripts" / "convert_pdf_to_structured.py"

class TestLobsterWorkflow:
    """Lobster 工作流集成测试"""
    
    def test_pdf_parser_outputs_json(self, tmp_path):
        """验证 PDF 解析脚本输出有效 JSON"""
        fixture = Path("tests/workflow/fixtures/sample-prd.pdf")
        if not fixture.exists():
            pytest.skip("Fixture PDF not found")
        
        result = subprocess.run(
            ["python3", str(PDF_SCRIPT), str(fixture)],
            capture_output=True, text=True
        )
        
        assert result.returncode == 0, f"PDF parser failed: {result.stderr}"
        
        output = json.loads(result.stdout)
        assert output["status"] == "success"
        assert "pages" in output["content"]
        assert len(output["content"]["pages"]) > 0
        
    def test_lobster_workflow_structure(self):
        """验证 Lobster 文件结构正确"""
        lobster_file = WORKFLOW_DIR / "ux-requirement-analysis.lobster"
        assert lobster_file.exists()
        
        content = lobster_file.read_text()
        assert "name:" in content
        assert "steps:" in content
        assert "parse_pdf" in content
        assert "rana_analysis" in content
        assert "validate" in content
    
    def test_state_json_schema(self, tmp_path):
        """验证 state.json 符合预期结构"""
        state_file = tmp_path / "state.json"
        state_file.write_text(json.dumps({
            "run_id": "test_run",
            "status": "running",
            "current_step": "parse_pdf",
            "args": {"input_file": "test.pdf"},
            "steps_completed": [],
            "errors": []
        }))
        
        state = json.loads(state_file.read_text())
        assert state["run_id"] == "test_run"
        assert "args" in state
```

- [ ] **Step 2: 创建简单 fixture PDF**

使用 reportlab 生成测试 PDF：

```python
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter

c = canvas.Canvas("tests/workflow/fixtures/sample-prd.pdf", pagesize=letter)
width, height = letter

c.drawString(100, height - 100, "需求文档：订单搜索优化")
c.drawString(100, height - 130, "版本：v1.5")
c.drawString(100, height - 180, "一、业务背景")
c.drawString(100, height - 200, "当前订单搜索效率低，用户反馈搜索结果不准确。")
c.drawString(100, height - 250, "二、功能需求")
c.drawString(100, height - 270, "1. 智能搜索：支持关键词联想")
c.drawString(100, height - 290, "2. 筛选优化：增加时间范围筛选")

c.save()
```

---

### Task 8: 更新 AGENTS.md 文档

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: 添加工作流章节**

在 AGENTS.md 中添加新章节：

```markdown
## Lobster 工作流集成

### 工作流定义

多技能串递通过 OpenClaw Lobster 实现：

```
ux-requirement-analysis.lobster
├── Step 1: pdf skill 解析 PDF
├── Step 2: llm-task 提取结构化信息
├── Step 3: rana skill 需求分析
└── Step 4: quality-validator 质检
```

### 运行命令

```bash
# Lobster CLI 运行
lobster run ~/.openclaw/skills/workflows/ux-requirement-analysis.lobster \
    --args-json '{"input_file":"spec.pdf","requirement_name":"订单搜索"}'

# Shell 脚本运行
~/.openclaw/skills/workflows/run-analysis.sh spec.pdf "订单搜索"
```

### 技能路径约定

| 环境 | pdf skill | rana skill | workflows |
|------|-----------|-----------|-----------|
| 本地 (BlueCode) | `~/.agents/skills/pdf/` | `~/.agents/skills/rana/` | `~/.agents/skills/workflows/` |
| 服务器 (OpenClaw) | `~/.openclaw/skills/pdf/` | `~/.openclaw/skills/rana/` | `~/.openclaw/skills/workflows/` |
```

---

## 验收标准

| # | 验收项 | 通过标准 |
|---|--------|---------|
| 1 | Lobster 文件语法 | `lobster validate ux-requirement-analysis.lobster` 返回成功 |
| 2 | PDF 解析输出 JSON | `convert_pdf_to_structured.py` 输出有效 JSON，含 pages/tables/images |
| 3 | JSON Schema 校验 | LLM 输出符合 `input-structured-schema.json` |
| 4 | 工作流端到端运行 | 输入 PDF → 生成 `final-analysis.md` |
| 5 | state.json 持久化 | 每步更新 state.json，重启可恢复 |
| 6 | 验证器集成 | Stage 6 验证器在 Lobster Step 中被调用 |
| 7 | 集成测试通过 | `pytest tests/workflow/ -v` 全部_PASS |

---

## 风险与缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| pdfplumber 依赖缺失 | PDF 解析失败 | 在 SKILL.md 中注明需要 `pip install pdfplumber` |
| LLM 输出格式漂移 | 后续步骤崩溃 | 强制 JSON Schema 校验 + 最大 3 次重试 |
| Lobster timeout | 长文档分析超时 | 设置 `timeoutMs: 600000` (10分钟) |
| sessionId 遗忘 | 子 Agent 状态丢失 | 每步写入 state.json |
| state.json 并发写 | 数据损坏 | 使用原子写入（ tempfile + rename） |

---

## 实施顺序

1. **Phase 1（基础，1周）**
   - Task 1: Lobster 工作流定义
   - Task 2: PDF 解析脚本
   - Task 3: JSON Schema

2. **Phase 2（集成，1周）**
   - Task 4: LLM Prompt 模板
   - Task 5: rana SKILL.md 更新
   - Task 6: Shell 运行脚本

3. **Phase 3（验证，1周）**
   - Task 7: 集成测试
   - Task 8: AGENTS.md 文档

---

## 与 report.md 方案的对比

| 特性 | report.md 方案 | 本方案 (Lobster) |
|------|---------------|-----------------|
| 编排机制 | 自建 Orchestrator Skill | 官方 Lobster DSL |
| 状态管理 | state.json + 自建调度器 | Lobster 内置 state + revision |
| 技能调用 | sessions_spawn + sessions_yield | openclaw.invoke --tool |
| 开发复杂度 | 高（需自建调度器） | 低（声明式 YAML） |
| 持久化 | 需手动实现 | Lobster 内置 |
| 适用性 | 复杂多 Agent 协作 | 确定性单线工作流 |

**结论**：对于「PDF 解析 → 需求分析 → 验证」这一确定性流程，Lobster 方案更轻量、更可靠。report.md 方案可作为后续扩展（如需要人工审批门控、动态分支判断等复杂场景）时的参考。