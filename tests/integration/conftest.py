"""
conftest.py — 集成测试自动生成 fixture 输出

场景 A：用 pdfplumber 提取 PDF 文字/表格/图片元数据，
        生成符合 Stage 1 格式的 input-structured.md

场景 B：生成固定的 skill-response.txt（skill 要求用户转换 Excel → PDF 的响应）
"""

import pytest
from pathlib import Path

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────

ROOT = Path(__file__).parent.parent
FIXTURES = ROOT / "fixtures" / "file-input" / "fixtures"
OUTPUTS = ROOT / "fixtures" / "file-input" / "outputs"

PDF_FIXTURE = FIXTURES / "pdf-with-images" / "【服务首页优化】需求清单（有插图）.pdf"
EXCEL_FIXTURE = FIXTURES / "excel-any" / "【服务首页优化】需求清单（有插图）.xlsx"


# ──────────────────────────────────────────────
# PDF extraction helpers
# ──────────────────────────────────────────────


def _extract_pdf(pdf_path: Path) -> list:
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
            pages.append(
                {
                    "page": i,
                    "text": text.strip(),
                    "tables": tables,
                    "image_count": image_count,
                }
            )
    return pages


def _build_input_structured(pages: list) -> str:
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
def scenario_a_output():
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
def scenario_b_output():
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
