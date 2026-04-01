"""
集成测试：文件输入处理行为验证（两步分离）

## 使用方式

### 第一步（人工，每次需要验证时执行）
将 PDF 文件交给 AI（在 AI session 中）：
  「请加载 ux-requirement-analysis skill，处理这个 PDF 文件的 Stage 1，
    将输出保存到 test-runs/file-input/outputs/a-pdf-with-images/input-structured.md」

将 Excel 文件交给 AI，观察 skill 的响应，手动保存响应文本到：
  test-runs/file-input/outputs/b-excel-any/skill-response.txt

### 第二步（自动，可重复运行）
python3 tests/integration/test_file_input.py [scenario]
  scenario: a | b | all (默认 all)

outputs/ 目录为空时各场景自动跳过，不视为失败，不影响 CI。

## 场景说明
  A — PDF 含截图  → 验证 input-structured.md 结构和来源标注质量
  B — Excel 任意  → 验证 skill 响应包含 PDF 转换要求，不含分析内容
"""

import sys
import re
from pathlib import Path

# ──────────────────────────────────────────────
# Paths
# ──────────────────────────────────────────────

ROOT = Path(__file__).parent.parent.parent
FIXTURES = ROOT / "test-runs" / "file-input" / "fixtures"
OUTPUTS = ROOT / "test-runs" / "file-input" / "outputs"

# ──────────────────────────────────────────────
# Config: update filenames when files arrive
# ──────────────────────────────────────────────

FIXTURE_FILES = {
    "a": FIXTURES / "pdf-with-images" / "【服务首页优化】需求清单（有插图）.pdf",
    "b": FIXTURES / "excel-any" / "【服务首页优化】需求清单（有插图）.xlsx",
}

# ──────────────────────────────────────────────
# Result helpers
# ──────────────────────────────────────────────


def _pass(msg: str):
    print(f"  ✓ PASS  {msg}")


def _fail(msg: str):
    print(f"  ✗ FAIL  {msg}")


def _skip(msg: str):
    print(f"  ─ SKIP  {msg}")


def _section(title: str):
    print(f"\n{'─' * 60}")
    print(f"  {title}")
    print(f"{'─' * 60}")


# ──────────────────────────────────────────────
# Shared output checker
# ──────────────────────────────────────────────

REQUIRED_SECTIONS = [
    "业务背景与目标",
    "功能点清单",
    "界面信息",
    "约束条件",
    "假设与前提",
]

SOURCE_ANNOTATION_PATTERN = re.compile(r"\[(?:PDF第\d+页|PDF截图\d+|截图\d+)\]")


def check_output(output_md: Path) -> dict:
    """
    验证 input-structured.md 的结构和来源标注质量。

    Returns:
        {"pass": bool, "issues": list[str], "stats": dict}
    """
    issues = []
    stats = {}

    if not output_md.exists():
        return {"pass": False, "issues": [f"输出文件不存在: {output_md}"], "stats": {}}

    content = output_md.read_text(encoding="utf-8")

    # 1. 必要章节
    missing_sections = [s for s in REQUIRED_SECTIONS if s not in content]
    if missing_sections:
        issues.append(f"缺少章节: {missing_sections}")
    stats["missing_sections"] = missing_sections

    # 2. 来源标注覆盖率（简化版：检查正文行中带标注的比例）
    lines = [l.strip() for l in content.splitlines() if l.strip() and not l.startswith("#")]
    annotated = sum(1 for l in lines if SOURCE_ANNOTATION_PATTERN.search(l))
    rate = annotated / len(lines) if lines else 1.0
    stats["annotation_rate"] = round(rate, 2)
    stats["annotated_lines"] = annotated
    stats["total_lines"] = len(lines)
    if rate < 0.5:
        issues.append(f"来源标注覆盖率过低: {rate:.0%}（建议 ≥ 50%）")

    return {"pass": len(issues) == 0, "issues": issues, "stats": stats}


def print_check_result(result: dict):
    for issue in result["issues"]:
        _fail(issue)
    s = result["stats"]
    if s:
        print(
            f"       来源标注覆盖率: {s.get('annotated_lines', '?')}/{s.get('total_lines', '?')} 行 ({s.get('annotation_rate', '?'):.0%})"
        )


# ──────────────────────────────────────────────
# Scenario A: PDF with images
# ──────────────────────────────────────────────


def run_scenario_a():
    _section("场景 A — PDF 含截图")
    fixture = FIXTURE_FILES["a"]

    if not fixture.exists():
        _skip(f"fixture 文件不存在，跳过: {fixture.name}")
        return True

    print(f"  文件: {fixture.name} ({fixture.stat().st_size // 1024} KB)")

    output_md = OUTPUTS / "a-pdf-with-images" / "input-structured.md"
    output_md.parent.mkdir(parents=True, exist_ok=True)

    if not output_md.exists():
        _skip(
            "输出文件不存在，跳过验证。\n"
            "  → 如何生成：将 PDF 交给 AI，在 AI session 中执行 Stage 1，\n"
            "    将输出保存到 test-runs/file-input/outputs/a-pdf-with-images/input-structured.md"
        )
        return True

    result = check_output(output_md)
    print_check_result(result)

    # 场景 A 专项：检查 [PDF截图X] 或 [PDF第X页] 标注
    content = output_md.read_text(encoding="utf-8")
    pdf_annotated = "[PDF截图" in content or "[PDF第" in content
    if not pdf_annotated:
        _fail("未找到 [PDF截图X] 或 [PDF第X页] 标注，PDF 内容可能未被正确引用")
    else:
        _pass("[PDF截图X] / [PDF第X页] 标注存在")

    passed = result["pass"] and pdf_annotated
    if passed:
        _pass("场景 A 全部验证通过")
    return passed


# ──────────────────────────────────────────────
# Scenario B: Excel (any) → must trigger conversion prompt
# ──────────────────────────────────────────────


def run_scenario_b():
    _section("场景 B — Excel 文件（任意，含图/无图/图片丢失均适用）")
    fixture = FIXTURE_FILES["b"]

    if not fixture.exists():
        _skip(f"fixture 文件不存在，跳过: {fixture.name}")
        return True

    print(f"  文件: {fixture.name} ({fixture.stat().st_size // 1024} KB)")

    output_log = OUTPUTS / "b-excel-any" / "skill-response.txt"
    output_log.parent.mkdir(parents=True, exist_ok=True)

    if not output_log.exists():
        _skip(
            "响应文件不存在，跳过验证。\n"
            "  → 如何生成：将 Excel 文件交给 AI，观察 skill 响应，\n"
            "    手动保存响应文本到 test-runs/file-input/outputs/b-excel-any/skill-response.txt"
        )
        return True

    response = output_log.read_text(encoding="utf-8")
    has_convert_prompt = ("导出" in response or "转" in response) and "PDF" in response
    has_analysis_output = "业务背景与目标" in response or "功能点清单" in response

    if not has_convert_prompt:
        _fail("skill 未输出 PDF 转换要求（期望包含「导出/转」+「PDF」）")
        return False
    _pass("skill 输出了 PDF 转换要求")

    if has_analysis_output:
        _fail("skill 不应在要求转换的同时产出分析内容")
        return False
    _pass("skill 未提前产出分析内容（符合预期）")

    _pass("场景 B 全部验证通过")
    return True


# ──────────────────────────────────────────────
# Runner
# ──────────────────────────────────────────────

SCENARIOS = {
    "a": run_scenario_a,
    "b": run_scenario_b,
}


def main():
    arg = sys.argv[1].lower() if len(sys.argv) > 1 else "all"

    print("\n文件输入集成测试")
    print("=" * 60)
    print("说明：fixtures 为空时各场景自动跳过，不视为失败")

    if arg == "all":
        targets = list(SCENARIOS.keys())
    elif arg in SCENARIOS:
        targets = [arg]
    else:
        print(f"未知场景: {arg}，可选: a | b | all")
        sys.exit(1)

    all_ok = True
    for key in targets:
        ok = SCENARIOS[key]()
        all_ok = all_ok and ok

    print(f"\n{'=' * 60}")
    if all_ok:
        print("结果: 全部通过（含跳过）")
    else:
        print("结果: 有失败项，请检查上方输出")
        sys.exit(1)


if __name__ == "__main__":
    main()
