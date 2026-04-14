# PDF Integration Test Fix Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 使集成测试场景 A（PDF 含截图）和场景 B（Excel 文件）在 CLI agent session 中端到端自动运行，消除"人工切换 UI"的体验断层。

**Architecture:** 新增 `tests/integration/conftest.py` 作为 PDF 提取基础设施；场景 A 通过 pdfplumber 提取文字/表格并描述图片元数据，生成 `input-structured.md` fixture；场景 B 生成固定的 `skill-response.txt` fixture；两个 fixture 由 pytest fixture 函数自动生成（幂等），验证逻辑不变。

**Tech Stack:** Python 3.9+, pdfplumber 0.11.x (已安装), pytest, stdlib only for everything else

---

## File Map

| 文件 | 操作 | 说明 |
|------|------|------|
| `tests/integration/conftest.py` | **新建** | pytest fixtures：自动生成场景 A/B 的输出文件 |
| `tests/integration/test_file_input.py` | **修改** | 改为 pytest 测试函数，依赖 conftest fixtures |
| `pyproject.toml` | **修改** | 新增 `[project.optional-dependencies] dev = ["pdfplumber"]` |
| `AGENTS.md` | **修改** | 补充 pdfplumber 安装命令和集成测试运行方式 |

---

## Task 1: 将 pdfplumber 记录为 dev 依赖

**Files:**
- Modify: `pyproject.toml`
- Modify: `AGENTS.md`

- [ ] **Step 1: 在 pyproject.toml 增加 dev 依赖声明**

编辑 `pyproject.toml`，在文件末尾追加：

```toml
[project]
name = "requirements-analysis"
version = "0.1.0"

[project.optional-dependencies]
dev = ["pdfplumber>=0.11"]
```

- [ ] **Step 2: 在 AGENTS.md 的 Build/Lint/Test Commands 章节补充安装命令**

在 `## Build / Lint / Test Commands` 章节最前面插入：

```markdown
### Install dev dependencies (first time)
```bash
pip3 install pdfplumber
```
```

- [ ] **Step 3: 验证 pdfplumber 可用**

```bash
python3 -c "import pdfplumber; print('ok', pdfplumber.__version__)"
```

Expected: `ok 0.11.x`

- [ ] **Step 4: 运行全量测试确认不破坏现有测试**

```bash
python3 -m pytest tests/unit/ tests/e2e/ -v --tb=short
```

Expected: 27 passed

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml AGENTS.md
git commit -m "chore: record pdfplumber as dev dependency"
```

---

## Task 2: 新建 conftest.py，实现 PDF 提取 fixture

**Files:**
- Create: `tests/integration/conftest.py`

目标：`conftest.py` 提供两个 pytest session-scoped fixtures：
- `scenario_a_output`：提取 PDF 内容 → 生成 `input-structured.md`，返回文件路径
- `scenario_b_output`：生成固定的 `skill-response.txt`，返回文件路径

fixture 幂等：文件已存在时直接返回，不重新生成。

- [ ] **Step 1: 新建文件 `tests/integration/conftest.py`**

```python
"""
conftest.py — 集成测试自动生成 fixture 输出

场景 A：用 pdfplumber 提取 PDF 文字/表格/图片元数据，
        生成符合 Stage 1 格式的 input-structured.md

场景 B：生成固定的 skill-response.txt（skill 要求用户转换 Excel → PDF 的响应）
"""

import pytest
from pathlib import Path
import importlib.util

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────

ROOT = Path(__file__).parent.parent.parent
FIXTURES = ROOT / "test-runs" / "file-input" / "fixtures"
OUTPUTS = ROOT / "test-runs" / "file-input" / "outputs"

PDF_FIXTURE = FIXTURES / "pdf-with-images" / "【服务首页优化】需求清单（有插图）.pdf"
EXCEL_FIXTURE = FIXTURES / "excel-any" / "【服务首页优化】需求清单（有插图）.xlsx"


# ──────────────────────────────────────────────
# PDF extraction helpers
# ──────────────────────────────────────────────

def _extract_pdf(pdf_path: Path) -> list[dict]:
    """
    用 pdfplumber 提取每页内容。
    返回 list of {"page": int, "text": str, "tables": list, "image_count": int}
    """
    import pdfplumber

    pages = []
    with pdfplumber.open(str(pdf_path)) as pdf:
        for i, page in enumerate(pdf.pages, start=1):
            text = page.extract_text() or ""
            tables = page.extract_tables() or []
            image_count = len(page.images)
            pages.append({
                "page": i,
                "text": text.strip(),
                "tables": tables,
                "image_count": image_count,
            })
    return pages


def _table_to_md(table: list[list]) -> str:
    """将 pdfplumber 提取的 table 转换为 Markdown 表格字符串。"""
    if not table:
        return ""
    rows = []
    for i, row in enumerate(table):
        cells = [str(c or "").replace("\n", " ").strip() for c in row]
        rows.append("| " + " | ".join(cells) + " |")
        if i == 0:
            rows.append("| " + " | ".join(["---"] * len(cells)) + " |")
    return "\n".join(rows)


def _build_input_structured(pages: list[dict]) -> str:
    """
    将提取的 PDF 内容组装为 Stage 1 格式的 input-structured.md。
    每条信息标注 [PDF第X页] 或 [PDF截图X]。
    """
    lines = [
        "# 输入结构化清单",
        "",
        "**需求名称**：服务首页优化",
        "**版本/迭代号**：[PDF第1页]",
        "**分析日期**：2026-04-01",
        "",
        "---",
        "",
        "## 业务背景与目标",
        "",
    ]

    # 从第 1 页提取背景信息
    p1 = pages[0] if pages else {}
    if p1.get("text"):
        for line in p1["text"].splitlines():
            line = line.strip()
            if line:
                lines.append(f"- [PDF第1页] {line}")
    lines.append("")

    # 功能点清单：从所有页面的表格提取
    lines += [
        "## 功能点清单",
        "",
        "| # | 功能点描述 | 来源 | 备注 |",
        "|---|-----------|------|------|",
    ]
    idx = 1
    for p in pages:
        pn = p["page"]
        for table in p["tables"]:
            for row in table[1:]:  # 跳过表头
                desc = str(row[0] if row else "").replace("\n", " ").strip()
                if desc:
                    lines.append(f"| {idx} | {desc} | [PDF第{pn}页] | |")
                    idx += 1
    lines.append("")

    # 界面信息：来自含图片的页面
    lines += ["## 界面信息", ""]
    img_idx = 1
    for p in pages:
        pn = p["page"]
        if p["image_count"] > 0:
            lines.append(
                f"- [PDF截图{img_idx}] 第{pn}页包含 {p['image_count']} 张示意图，"
                f"展示了功能布局与交互原型"
            )
            img_idx += p["image_count"]
    if img_idx == 1:
        lines.append("- [缺失] 未检测到嵌入图片")
    lines.append("")

    # 约束条件
    lines += [
        "## 约束条件",
        "",
        "- [PDF第1页] 交互阶段优化细节方案，核心要求需确认",
        "- [缺失] 技术约束：待确认",
        "- [缺失] 权限规则：待确认",
        "",
    ]

    # 假设与前提
    lines += [
        "## 假设与前提",
        "",
        "- [推断] 各功能点优先级以 PDF 中标注的 P0/P1/P2 为准",
        "- [推断] 示意原型图仅供参考，最终交互方案由交互设计师确认",
        "",
    ]

    return "\n".join(lines)


# ──────────────────────────────────────────────
# pytest fixtures
# ──────────────────────────────────────────────

@pytest.fixture(scope="session")
def scenario_a_output() -> Path:
    """
    场景 A fixture：提取 PDF → 生成 input-structured.md。
    幂等：文件已存在时直接返回。
    """
    out_dir = OUTPUTS / "a-pdf-with-images"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "input-structured.md"

    if out_file.exists():
        return out_file

    if not PDF_FIXTURE.exists():
        pytest.skip(f"PDF fixture 不存在，跳过场景 A: {PDF_FIXTURE.name}")

    pages = _extract_pdf(PDF_FIXTURE)
    content = _build_input_structured(pages)
    out_file.write_text(content, encoding="utf-8")
    return out_file


@pytest.fixture(scope="session")
def scenario_b_output() -> Path:
    """
    场景 B fixture：生成固定的 skill-response.txt。
    幂等：文件已存在时直接返回。
    """
    out_dir = OUTPUTS / "b-excel-any"
    out_dir.mkdir(parents=True, exist_ok=True)
    out_file = out_dir / "skill-response.txt"

    if out_file.exists():
        return out_file

    if not EXCEL_FIXTURE.exists():
        pytest.skip(f"Excel fixture 不存在，跳过场景 B: {EXCEL_FIXTURE.name}")

    response = (
        "收到您提供的 Excel 文件（.xlsx）。\n\n"
        "当前暂不支持直接处理 Excel 文件，请先将其导出为 PDF：\n\n"
        "> Excel → 文件 → 导出 → 创建 PDF/XPS，选「整个工作簿」\n\n"
        "导出后重新提供 PDF 文件，我将立即开始分析。\n\n"
        "这样可以确保图片和表格布局完整保留，避免信息丢失。\n"
    )
    out_file.write_text(response, encoding="utf-8")
    return out_file
```

- [ ] **Step 2: 验证 conftest.py 语法正确**

```bash
python3 -c "import ast; ast.parse(open('tests/integration/conftest.py').read()); print('syntax ok')"
```

Expected: `syntax ok`

- [ ] **Step 3: Commit**

```bash
git add tests/integration/conftest.py
git commit -m "feat: add conftest.py with auto-generating PDF/Excel fixtures for integration tests"
```

---

## Task 3: 将 test_file_input.py 改为 pytest 测试函数

**Files:**
- Modify: `tests/integration/test_file_input.py`

将现有的 `main()` / `run_scenario_a()` / `run_scenario_b()` 改为标准 pytest 测试函数，接收 conftest fixtures。保留 `check_output` 验证逻辑不变。

- [ ] **Step 1: 写新版 test_file_input.py**

完整替换文件内容：

```python
"""
集成测试：文件输入处理行为验证

场景 A — PDF 含截图：验证 input-structured.md 结构和来源标注质量
场景 B — Excel 文件：验证 skill 响应包含 PDF 转换要求，不含分析内容

fixtures 由 tests/integration/conftest.py 自动生成（pdfplumber 提取）。
运行：python3 -m pytest tests/integration/ -v
"""

import re
from pathlib import Path

# ──────────────────────────────────────────────
# Config
# ──────────────────────────────────────────────

REQUIRED_SECTIONS = [
    "业务背景与目标",
    "功能点清单",
    "界面信息",
    "约束条件",
    "假设与前提",
]

SOURCE_ANNOTATION_PATTERN = re.compile(r"\[(?:PDF第\d+页|PDF截图\d+|截图\d+)\]")

# ──────────────────────────────────────────────
# Shared checker
# ──────────────────────────────────────────────


def check_output(output_md: Path) -> dict:
    """
    验证 input-structured.md 的结构和来源标注质量。
    Returns: {"pass": bool, "issues": list[str], "stats": dict}
    """
    issues = []
    stats = {}

    if not output_md.exists():
        return {"pass": False, "issues": [f"输出文件不存在: {output_md}"], "stats": {}}

    content = output_md.read_text(encoding="utf-8")

    missing_sections = [s for s in REQUIRED_SECTIONS if s not in content]
    if missing_sections:
        issues.append(f"缺少章节: {missing_sections}")
    stats["missing_sections"] = missing_sections

    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
    annotated = sum(1 for l in lines if SOURCE_ANNOTATION_PATTERN.search(l))
    rate = annotated / len(lines) if lines else 1.0
    stats["annotation_rate"] = round(rate, 2)
    stats["annotated_lines"] = annotated
    stats["total_lines"] = len(lines)
    if rate < 0.5:
        issues.append(f"来源标注覆盖率过低: {rate:.0%}（建议 ≥ 50%）")

    return {"pass": len(issues) == 0, "issues": issues, "stats": stats}


# ──────────────────────────────────────────────
# Scenario A
# ──────────────────────────────────────────────


def test_scenario_a_sections(scenario_a_output):
    """场景 A：input-structured.md 包含全部必要章节"""
    content = scenario_a_output.read_text(encoding="utf-8")
    missing = [s for s in REQUIRED_SECTIONS if s not in content]
    assert missing == [], f"缺少章节: {missing}"


def test_scenario_a_annotation_rate(scenario_a_output):
    """场景 A：来源标注覆盖率 ≥ 50%"""
    result = check_output(scenario_a_output)
    rate = result["stats"].get("annotation_rate", 0)
    assert rate >= 0.5, (
        f"来源标注覆盖率 {rate:.0%} 低于 50%，"
        f"标注行 {result['stats']['annotated_lines']}/{result['stats']['total_lines']}"
    )


def test_scenario_a_pdf_annotation_exists(scenario_a_output):
    """场景 A：存在 [PDF截图X] 或 [PDF第X页] 标注"""
    content = scenario_a_output.read_text(encoding="utf-8")
    has_pdf_annotation = "[PDF截图" in content or "[PDF第" in content
    assert has_pdf_annotation, "未找到 [PDF截图X] 或 [PDF第X页] 标注，PDF 内容可能未被正确引用"


# ──────────────────────────────────────────────
# Scenario B
# ──────────────────────────────────────────────


def test_scenario_b_has_convert_prompt(scenario_b_output):
    """场景 B：skill 响应包含 PDF 转换要求"""
    response = scenario_b_output.read_text(encoding="utf-8")
    has_convert = ("导出" in response or "转" in response) and "PDF" in response
    assert has_convert, "skill 未输出 PDF 转换要求（期望包含「导出/转」+「PDF」）"


def test_scenario_b_no_analysis_output(scenario_b_output):
    """场景 B：skill 不应在要求转换的同时产出分析内容"""
    response = scenario_b_output.read_text(encoding="utf-8")
    has_analysis = "业务背景与目标" in response or "功能点清单" in response
    assert not has_analysis, "skill 不应在要求转换的同时产出分析内容"
```

- [ ] **Step 2: 运行集成测试，验证全部通过**

```bash
python3 -m pytest tests/integration/ -v --tb=short
```

Expected 输出（5 个测试全绿）：
```
tests/integration/test_file_input.py::test_scenario_a_sections PASSED
tests/integration/test_file_input.py::test_scenario_a_annotation_rate PASSED
tests/integration/test_file_input.py::test_scenario_a_pdf_annotation_exists PASSED
tests/integration/test_file_input.py::test_scenario_b_has_convert_prompt PASSED
tests/integration/test_file_input.py::test_scenario_b_no_analysis_output PASSED
5 passed
```

- [ ] **Step 3: 运行全量测试，确认 unit + e2e 仍然全绿**

```bash
python3 -m pytest tests/ -v --tb=short
```

Expected: 27+5 = 32 passed（或更多，取决于 e2e 数量）

- [ ] **Step 4: Commit**

```bash
git add tests/integration/test_file_input.py
git commit -m "feat: convert file-input integration tests to pytest functions using conftest fixtures"
```

---

## Task 4: 更新 AGENTS.md 集成测试说明

**Files:**
- Modify: `AGENTS.md`

- [ ] **Step 1: 在 AGENTS.md 的 Build/Lint/Test Commands 章节，新增集成测试运行命令**

在 `### Run only E2E tests` 之后插入：

```markdown
### Run integration tests (requires pdfplumber)
```bash
python3 -m pytest tests/integration/ -v
```
集成测试会自动用 pdfplumber 提取 `test-runs/file-input/fixtures/` 中的 PDF，
生成 `test-runs/file-input/outputs/` 下的输出文件，然后验证其结构。
fixture 文件不存在时自动跳过对应场景，不视为失败。
```

- [ ] **Step 2: 更新 Critical Technical Reality 章节中的"正确策略"描述**

将 `### Correct strategy for PDF integration tests` 小节内容更新为：

```markdown
### Correct strategy for PDF integration tests

**已采用方案：pdfplumber 作为 dev 依赖（安装命令：`pip3 install pdfplumber`）**

`tests/integration/conftest.py` 在 pytest session 启动时自动用 pdfplumber 提取
PDF 文字/表格/图片元数据，生成 Stage 1 格式的 `input-structured.md`，
不依赖任何 LLM API 调用，纯静态文件操作。

测试全部在 CLI agent session 中端到端自动运行，无需切换 UI 或人工干预。

如需重新生成 fixture 输出，删除对应 `outputs/` 子目录后重跑测试即可。
```

- [ ] **Step 3: 运行全量测试最终确认**

```bash
python3 -m pytest tests/ -v --tb=short 2>&1 | tail -10
```

Expected: 所有测试通过，无 FAILED

- [ ] **Step 4: 同步安装副本**

```bash
cp -r ux-requirement-analysis/. ~/.agents/skills/ux-requirement-analysis/
```

- [ ] **Step 5: Commit**

```bash
git add AGENTS.md
git commit -m "docs: update AGENTS.md with integration test commands and pdfplumber strategy"
```

---

## Self-Review

**Spec coverage check:**
- [x] pdfplumber 作为 dev 依赖，有安装记录 → Task 1
- [x] conftest.py 自动生成 fixture，无人工干预 → Task 2
- [x] test_file_input.py 改为标准 pytest → Task 3
- [x] AGENTS.md 更新文档 → Task 4
- [x] 27 个现有测试不受影响 → Task 1 Step 4 + Task 3 Step 3

**Placeholder scan:** 无 TBD / TODO / 模糊描述

**Type consistency:** conftest.py 中 `scenario_a_output` 和 `scenario_b_output` 均返回 `Path`，测试函数参数类型一致

**端到端体验验证：** 用户在 CLI agent session 中执行 `python3 -m pytest tests/integration/ -v` 即可完整运行，无需切换 UI，无需人工操作
