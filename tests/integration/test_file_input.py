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
