#!/usr/bin/env python3
"""
质量门禁校验脚本
UX Requirements Analyzer Skill - Quality Validator (v0.4.0)

用法：
  python3 quality-validator.py <分析目录>

示例：
  python3 quality-validator.py ./my-analysis/

v0.4.0 变更（适配八章节+总结双模式结构）：
  - 移除 input-structured.md 和 gap-analysis.md（v0.3 交付物）
  - 移除「需求分析卡」字段检查（v0.3 交付物A），改为 P0 必填章节检查
  - quick-analysis.md 为可选文件（Quick Mode 输出）
  - 必需文件：final-analysis.md, change-log.md, quality-report.md
  - 必须章节：一~七 + 总结（八为可选）
  - P0 必填小节检查替代原字段完整性检查

来源追溯检查策略（按文件分级）：
  final-analysis.md    : 检查八章节+总结中的表格数据行和列表项，跳过待澄清清单和总结判定
  change-log.md        : 跳过——协作过程记录
  quality-report.md    : 跳过——纯AI评估文档，无需来源标注
  quick-analysis.md    : 跳过——Quick Mode 快速分析，非完整交付物
"""

import re
import sys
from pathlib import Path


# ──────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────

TRACEABILITY_PATTERNS = [
    r"\[PRD[^\]]+\]",
    r"\[截图\s*\d+[^\]]*\]",
    r"\[PDF第\d+页[^\]]*\]",
    r"\[PDF截图\d+[^\]]*\]",
    r"\[Figma[^\]]+\]",
    r"\[PM\s*确认[^\]]*\]",
    r"\[研发\s*确认[^\]]*\]",
    r"\[测试\s*确认[^\]]*\]",
    r"\[业务\s*确认[^\]]*\]",
    r"\[设计师\s*确认[^\]]*\]",
    r"\[用户\s*确认[^\]]*\]",
    r"\[推断[^\]]*\]",
    r"\[分析推断[^\]]*\]",
    r"\[场景还原推断[^\]]*\]",
    r"\[五问法推断[^\]]*\]",
    r"\[X-Y分析推断[^\]]*\]",
    r"\[缺失[^\]]*\]",
    r"\[口头说明[^\]]*\]",
    r"\[CHG-\d+\]",
    r"\[原始输入[^\]]*\]",
    r"\[分析创建[^\]]*\]",
    r"\[quality-report[^\]]*\]",
]

VAGUE_TERMS = [
    "适当",
    "合理",
    "友好",
    "简洁",
    "清晰",
    "尽量",
    "尽可能",
    "TBD",
    "待定",
    "暂定",
    "后续确认",
    "后续讨论",
]

REQUIRED_FILES = [
    "final-analysis.md",
    "change-log.md",
    "quality-report.md",
]

OPTIONAL_FILES = [
    "quick-analysis.md",
]

EXPECTED_CHAPTERS = [
    "一、概述",
    "二、用户",
    "三、现状",
    "四、业务目标",
    "五、策略",
    "六、方案与验证",
    "七、风险与建议",
    "总结",
]

OPTIONAL_CHAPTERS = [
    "八、各角色重点关注",
]

P0_REQUIRED_SECTIONS = [
    ("1.1", "需求概述"),
    ("1.2", "需求来源"),
    ("2.1", "核心用户画像"),
    ("2.3", "场景与用户目标"),
    ("3.1", "现状与根因拆解"),
    ("4.1", "业务北极星"),
    ("6.1", "MVP"),
    ("6.3", "需求全清单与优先级分级"),
]


# ──────────────────────────────────────────────
# 来源追溯：通用工具函数
# ──────────────────────────────────────────────


def has_traceability(line: str) -> bool:
    return any(re.search(pat, line) for pat in TRACEABILITY_PATTERNS)


def is_table_separator(line: str) -> bool:
    return bool(re.match(r"^\|[-:\s|]+\|", line))


def is_empty_or_heading(line: str) -> bool:
    return bool(re.match(r"^\s*$", line) or re.match(r"^#+\s", line))


def table_cells(line: str) -> list:
    return [c.strip() for c in line.strip().strip("|").split("|")]


# ──────────────────────────────────────────────
# 来源追溯：final-analysis.md
# ──────────────────────────────────────────────


def check_traceability_final_analysis(content: str) -> dict:
    """
    final-analysis.md：检查八章节+总结中的表格数据行和列表项。
    跳过：
    - 待澄清项区块（AI生成的问题，无需来源标注）
    - 总结中的成立/不成立判定行（AI判断结论）
    - 各角色重点关注章节（P2 可选内容）
    """
    lines = content.split("\n")
    issues = []
    checked = 0
    in_code_block = False
    in_skip_section = False

    SKIP_SECTION_HEADERS = [
        "待澄清项",
        "待澄清",
        "八、各角色重点关注",
        "八、各角色关注",
        "各角色重点关注",
        "各角色关注",
        "总结",
    ]

    RESUME_SECTION_HEADERS = []

    HEADER_KEYWORDS = [
        "字段",
        "内容",
        "来源追溯",
        "来源",
        "状态",
        "说明",
        "描述",
        "维度",
        "检查项",
        "通过标准",
        "触发条件",
        "用户目标",
        "角色",
        "场景",
        "序号",
        "缺口描述",
        "需问谁",
        "优先级",
        "限制类型",
        "具体限制",
        "目标值",
        "基准值",
        "指标名称",
        "统计口径",
        "验证方式",
        "核心场景",
        "边缘场景",
        "子任务",
        "优先级分级",
        "功能点",
    ]

    REFERENCE_CELL_PATTERNS = [
        r"^\[见",
        r"^—$",
        r"^\[缺失\]",
    ]

    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        if re.match(r"^##", line):
            if any(kw in line for kw in SKIP_SECTION_HEADERS):
                in_skip_section = True
            elif any(kw in line for kw in RESUME_SECTION_HEADERS):
                in_skip_section = False
            continue
        if re.match(r"^###", line):
            if any(kw in line for kw in SKIP_SECTION_HEADERS):
                in_skip_section = True
            elif any(kw in line for kw in RESUME_SECTION_HEADERS):
                in_skip_section = False
            continue

        if in_skip_section:
            continue

        if is_empty_or_heading(line):
            continue
        if re.match(r"^>\s", line):
            continue

        is_table_row = "|" in line and not is_table_separator(line)
        is_list_item = bool(re.match(r"^\s*[-*]\s+\S", line) or re.match(r"^\s*\d+\.\s+\S", line))

        if not (is_table_row or is_list_item):
            continue

        if is_table_row:
            cells = table_cells(line)
            if cells and any(kw in cells[0] for kw in HEADER_KEYWORDS):
                continue
            non_empty = [c for c in cells if c and c not in ("—", "-")]
            if non_empty and all(re.match(r"^[\d%（）().*A-Z\s]+$", c) for c in non_empty):
                continue
            if len(cells) >= 2:
                content_cell = cells[1] if len(cells) > 1 else ""
                source_cell = cells[2].strip() if len(cells) > 2 else ""
                if any(re.match(pat, content_cell) for pat in REFERENCE_CELL_PATTERNS):
                    continue
                if source_cell == "—" and re.search(r"见下文|详见|见第六章", content_cell):
                    continue

        if is_list_item:
            stripped_prefix = re.sub(r"^\s*[-*]\s+", "", line.strip())
            stripped_prefix = re.sub(r"^\s*\d+\.\s+", "", stripped_prefix)
            stripped = re.sub(r"^\*\*[^*]*\*\*\s*", "", stripped_prefix).strip()
            bare = re.sub(r"\*\*", "", stripped_prefix).strip()

            if re.match(r"^来源[:：]", stripped_prefix) or re.match(r"^来源[:：]", bare):
                continue
            if re.match(
                r"^(参考|引用|时间|触发|确认方|影响|原因|来源|类型|详情|建议|说明|注意|用法|示例|格式|输入|输出|处理|状态)[:：]",
                bare,
            ):
                continue
            next_line = lines[i] if i < len(lines) else ""
            has_next_source = bool(
                re.match(r"^\s+-\s+来源[:：]", next_line) or re.match(r"^\s+来源[:：]", next_line)
            )
            if has_next_source:
                if re.match(r"^\*\*(场景|边界|不支持)", stripped_prefix):
                    continue
                if re.match(r"^不支持[：:]", bare):
                    continue

        checked += 1
        if not has_traceability(line):
            issues.append({"line": i, "content": line.strip()[:80]})

    return _make_result(checked, issues)


def _make_result(checked: int, issues: list) -> dict:
    return {
        "checked": checked,
        "issues": issues,
        "pass_rate": (checked - len(issues)) / checked if checked > 0 else 1.0,
    }


# ──────────────────────────────────────────────
# 文件结构检查
# ──────────────────────────────────────────────


def check_file_structure(analysis_dir: Path) -> dict:
    results = {"pass": [], "fail": [], "optional_pass": [], "optional_fail": []}
    for filename in REQUIRED_FILES:
        filepath = analysis_dir / filename
        if filepath.exists():
            results["pass"].append(filename)
        else:
            results["fail"].append(filename)
    for filename in OPTIONAL_FILES:
        filepath = analysis_dir / filename
        if filepath.exists():
            results["optional_pass"].append(filename)
        else:
            results["optional_fail"].append(filename)
    return results


# ──────────────────────────────────────────────
# 模糊表述检查
# ──────────────────────────────────────────────


def check_vague_terms(content: str) -> list:
    issues = []
    lines = content.split("\n")
    for i, line in enumerate(lines, 1):
        for term in VAGUE_TERMS:
            if term in line:
                issues.append({"line": i, "term": term, "content": line.strip()[:80]})
    return issues


# ──────────────────────────────────────────────
# 章节完整性检查
# ──────────────────────────────────────────────


def check_sections(content: str, expected_chapters: list, optional_chapters: list = None) -> dict:
    results = {"pass": [], "fail": [], "optional_pass": [], "optional_fail": []}
    for chapter in expected_chapters:
        if chapter in content:
            results["pass"].append(chapter)
        else:
            results["fail"].append(chapter)
    if optional_chapters:
        for chapter in optional_chapters:
            if chapter in content:
                results["optional_pass"].append(chapter)
            else:
                results["optional_fail"].append(chapter)
    return results


# ──────────────────────────────────────────────
# P0 必填小节检查
# ──────────────────────────────────────────────


def check_p0_sections(content: str) -> dict:
    """
    检查 final-analysis.md 中 P0 必填小节是否存在。
    替代原「需求分析卡字段完整性」检查。

    返回：
      {
        "missing": [...],   # 缺失的 P0 小节列表
        "found": [...],     # 存在的 P0 小节列表
        "status": "PASS" | "FAIL"
      }
    """
    missing = []
    found = []

    for section_num, section_name in P0_REQUIRED_SECTIONS:
        pattern = f"{section_num}.*{section_name}"
        if re.search(pattern, content):
            found.append(f"{section_num} {section_name}")
        else:
            missing.append(f"{section_num} {section_name}")

    status = "FAIL" if missing else "PASS"
    return {"missing": missing, "found": found, "status": status}


# ──────────────────────────────────────────────
# 报告输出
# ──────────────────────────────────────────────


def print_header(title: str):
    print(f"\n{'=' * 60}")
    print(f"  {title}")
    print(f"{'=' * 60}")


def print_section(title: str):
    print(f"\n── {title} ──")


# ──────────────────────────────────────────────
# 量化评分
# ──────────────────────────────────────────────

SCORE_WEIGHTS = {
    "file_structure": 20,
    "traceability": 25,
    "p0_sections": 25,
    "chapters": 20,
    "vague_terms": 10,
}


def compute_score(analysis_dir: Path) -> dict:
    dims = {}
    failed = False

    # ── 1. 文件结构（20分，3个必需文件各约6.67分）──
    structure = check_file_structure(analysis_dir)
    missing_count = len(structure["fail"])
    per_file = SCORE_WEIGHTS["file_structure"] // len(REQUIRED_FILES) if REQUIRED_FILES else 0
    dims["file_structure"] = max(0, SCORE_WEIGHTS["file_structure"] - missing_count * per_file)
    if missing_count > 0:
        failed = True

    # ── 2. 来源追溯（25分）──
    fpath = analysis_dir / "final-analysis.md"
    if fpath.exists():
        content = fpath.read_text(encoding="utf-8")
        trace = check_traceability_final_analysis(content)
        dims["traceability"] = round(SCORE_WEIGHTS["traceability"] * trace["pass_rate"])
        if trace["pass_rate"] < 0.8:
            failed = True
    else:
        dims["traceability"] = 0

    # ── 3. P0 小节完整性（25分，8个P0小节各约3.125分）──
    if fpath.exists():
        content = fpath.read_text(encoding="utf-8")
        p0 = check_p0_sections(content)
        found_count = len(p0["found"])
        total_p0 = len(P0_REQUIRED_SECTIONS)
        dims["p0_sections"] = round(SCORE_WEIGHTS["p0_sections"] * found_count / total_p0)
        if p0["status"] == "FAIL":
            failed = True
    else:
        dims["p0_sections"] = 0

    # ── 4. 章节完整性（20分，8个必须章节各2.5分）──
    if fpath.exists():
        content = fpath.read_text(encoding="utf-8")
        chapters_result = check_sections(content, EXPECTED_CHAPTERS, OPTIONAL_CHAPTERS)
        missing_chapters = len(chapters_result["fail"])
        per_chapter = (
            SCORE_WEIGHTS["chapters"] // len(EXPECTED_CHAPTERS) if EXPECTED_CHAPTERS else 0
        )
        dims["chapters"] = max(0, SCORE_WEIGHTS["chapters"] - missing_chapters * per_chapter)
        if missing_chapters > 0:
            failed = True
    else:
        dims["chapters"] = 0

    # ── 5. 模糊表述控制（10分，每处扣2分）──
    vague_count = 0
    if fpath.exists():
        content = fpath.read_text(encoding="utf-8")
        vague_count = len(check_vague_terms(content))
    dims["vague_terms"] = max(0, SCORE_WEIGHTS["vague_terms"] - vague_count * 2)

    total = sum(dims.values())
    return {
        "total": total,
        "dimensions": dims,
        "pass": not failed,
    }


# ──────────────────────────────────────────────
# 溯追溯检查器映射
# ──────────────────────────────────────────────

TRACEABILITY_CHECKERS = {
    "final-analysis.md": check_traceability_final_analysis,
    "change-log.md": None,
    "quality-report.md": None,
    "quick-analysis.md": None,
}

VAGUE_CHECK_FILES = {"final-analysis.md"}


# ──────────────────────────────────────────────
# 主验证流程
# ──────────────────────────────────────────────


def run_validation(analysis_dir: Path):
    print_header("UX 需求分析质量门禁校验（v0.4.0）")
    print(f"分析目录：{analysis_dir}")

    total_issues = 0
    failed_dimensions = []

    # ─ 1. 文件结构检查 ─
    print_section("1. 文件结构检查")
    structure = check_file_structure(analysis_dir)

    if structure["pass"]:
        for f in structure["pass"]:
            print(f"  ✓ {f}")
    if structure["fail"]:
        for f in structure["fail"]:
            print(f"  ✗ 缺失: {f}")
        total_issues += len(structure["fail"])
        failed_dimensions.append("文件结构")
    if structure["optional_pass"]:
        for f in structure["optional_pass"]:
            print(f"  ✓ {f}（可选）")
    if structure["optional_fail"]:
        for f in structure["optional_fail"]:
            print(f"  ○ 未提供: {f}（可选，不影响评分）")

    # ─ 2. 各文件逐项检查 ─
    all_files = REQUIRED_FILES + OPTIONAL_FILES
    for filename in all_files:
        filepath = analysis_dir / filename
        if not filepath.exists():
            continue

        content = filepath.read_text(encoding="utf-8")
        print_section(f"2. {filename}")

        checker = TRACEABILITY_CHECKERS.get(filename)
        if checker is None:
            skip_reason = {
                "change-log.md": "协作过程记录",
                "quality-report.md": "AI评估文档",
                "quick-analysis.md": "Quick Mode 快速分析",
            }.get(filename, "过程文档")
            print(f"  来源追溯: — 跳过（{skip_reason}）")
        else:
            trace = checker(content)
            pass_rate = trace["pass_rate"] * 100
            status = "✓ PASS" if pass_rate >= 80 else "✗ FAIL"
            print(f"  来源追溯: {status}（{pass_rate:.0f}%，检查了 {trace['checked']} 行）")
            if trace["issues"]:
                for issue in trace["issues"][:5]:
                    print(f"    行{issue['line']}: {issue['content']}")
                if len(trace["issues"]) > 5:
                    print(f"    ... 共 {len(trace['issues'])} 处缺少来源标注")
                total_issues += len(trace["issues"])
                if pass_rate < 80:
                    failed_dimensions.append(f"{filename} 可追溯性")

        if filename in VAGUE_CHECK_FILES:
            vague = check_vague_terms(content)
            if vague:
                print(f"  模糊表述: ⚠ WARN（发现 {len(vague)} 处）")
                for issue in vague[:3]:
                    print(f"    行{issue['line']} [{issue['term']}]: {issue['content']}")
                total_issues += len(vague)
            else:
                print("  模糊表述: ✓ PASS")
        else:
            print("  模糊表述: — 跳过")

        if filename == "final-analysis.md":
            chapters_result = check_sections(content, EXPECTED_CHAPTERS, OPTIONAL_CHAPTERS)
            if chapters_result["fail"]:
                print(f"  章节完整性: ✗ FAIL（缺失 {len(chapters_result['fail'])} 个必须章节）")
                for s in chapters_result["fail"]:
                    print(f"    缺失: {s}")
                failed_dimensions.append("章节完整性")
            else:
                found_count = len(chapters_result["pass"])
                print(f"  章节完整性: ✓ PASS（{found_count}/{len(EXPECTED_CHAPTERS)} 必须章节）")
            if chapters_result["optional_fail"]:
                for s in chapters_result["optional_fail"]:
                    print(f"    ○ 可选章节缺失: {s}")

            p0 = check_p0_sections(content)
            if p0["status"] == "PASS":
                print(
                    f"  P0 小节完整性: ✓ PASS（{len(p0['found'])}/{len(P0_REQUIRED_SECTIONS)} P0 小节）"
                )
            else:
                missing_preview = "、".join(p0["missing"][:5])
                if len(p0["missing"]) > 5:
                    missing_preview += f"... 共{len(p0['missing'])}个"
                print(f"  P0 小节完整性: ✗ FAIL（缺失P0小节：{missing_preview}）")
                total_issues += len(p0["missing"])
                failed_dimensions.append("P0 小节完整性")

    # ─ 3. 总结 ─
    print_header("验证结果汇总")
    if failed_dimensions:
        print(f"  状态: ✗ FAIL")
        print(f"  总问题数: {total_issues}")
        print(f"  失败维度:")
        for d in failed_dimensions:
            print(f"    - {d}")
        print("\n  建议：补充缺失内容后重新运行验证")
    else:
        print(f"  状态: ✓ PASS")
        print(f"  总问题数: {total_issues}（均为 WARN，不阻断）")
        print("\n  分析说明书已可交付设计分析阶段")

    return len(failed_dimensions) == 0


# ──────────────────────────────────────────────
# 入口
# ──────────────────────────────────────────────

if __name__ == "__main__":
    import json as _json

    args = sys.argv[1:]
    score_mode = "--score" in args
    args = [a for a in args if a != "--score"]

    if not args:
        print("用法：python3 quality-validator.py <分析目录> [--score]")
        print("示例：python3 quality-validator.py ./my-analysis/")
        print("      python3 quality-validator.py ./my-analysis/ --score")
        sys.exit(1)

    analysis_dir = Path(args[0])
    if not analysis_dir.exists():
        print(f"错误：目录不存在：{analysis_dir}")
        sys.exit(1)

    passed = run_validation(analysis_dir)

    if score_mode:
        score = compute_score(analysis_dir)
        print("\n" + "─" * 60)
        print("  量化评分（--score）")
        print("─" * 60)
        print(_json.dumps(score, ensure_ascii=False, indent=2))

    sys.exit(0 if passed else 1)
