#!/usr/bin/env python3
"""
质量门禁校验脚本
UX Requirements Analyzer Skill - Quality Validator

用法：
  python3 quality-validator.py <分析目录>

示例：
  python3 quality-validator.py ./my-analysis/

来源追溯检查策略（按文件分级）：
  input-structured.md  : 检查所有表格数据行和列表项（事实提取文档）
  gap-analysis.md      : 只检查数据表，跳过检查清单和分析方法区块（AI判断内容）
  final-analysis.md    : 检查5个交付物章节，跳过待澄清清单和引用行
  change-log.md        : 跳过——协作过程记录，确认方字段已作为来源标注
  quality-report.md    : 跳过——纯AI评估文档，无需来源标注
"""

import re
import sys
from pathlib import Path


# ──────────────────────────────────────────────
# 配置
# ──────────────────────────────────────────────

# 来源标注模式
TRACEABILITY_PATTERNS = [
    r"\[PRD[^\]]+\]",  # [PRD第X节] / [PRD 第X节] / [PRD 需求清单] 等所有 PRD 引用
    r"\[截图\d+[^\]]*\]",
    r"\[PDF第\d+页[^\]]*\]",  # PDF 文字内容引用
    r"\[PDF截图\d+[^\]]*\]",  # PDF 图片引用
    r"\[Figma[^\]]+\]",
    r"\[PM确认[^\]]*\]",
    r"\[研发确认[^\]]*\]",
    r"\[测试确认[^\]]*\]",
    r"\[业务确认[^\]]*\]",
    r"\[设计师确认[^\]]*\]",
    r"\[用户确认[^\]]*\]",  # [用户确认] / [用户确认 19:16] — 对话确认通用格式
    r"\[推断[^\]]*\]",  # [推断：依据] / [推断] 裸标注
    r"\[分析推断[^\]]*\]",  # [分析推断] — 裸推断变体
    r"\[场景还原推断[^\]]*\]",
    r"\[五问法推断[^\]]*\]",
    r"\[X-Y分析推断[^\]]*\]",
    r"\[缺失[^\]]*\]",
    r"\[口头说明[^\]]*\]",
    r"\[CHG-\d+\]",
    r"\[原始输入[^\]]*\]",
    r"\[分析创建[^\]]*\]",  # [分析创建] — 系统生成内容，无外部来源
    r"\[quality-report[^\]]*\]",
]

# 模糊表述（不可执行词汇）
# 注：以下词汇因高误报率已移除：
#   "相关"       — 常出现在「相关度算法」等技术术语中
#   "一般"       — 叙述性语言中误报率高
#   "通常"       — 常出现在来源标注的推断依据中（如 [推断：...通常用于...]）
#   "正常情况下"  — 分析注释背景描述会被误拦
# 这些词的漏报成本低：真正模糊的需求通常同时触发完整性维度 FAIL
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

# 预期文件列表（相对于分析目录）
EXPECTED_FILES = [
    "input-structured.md",
    "gap-analysis.md",
    "change-log.md",
    "quality-report.md",
    "final-analysis.md",
]

# 预期章节（在 final-analysis.md 中）
EXPECTED_SECTIONS = {
    "final-analysis.md": [
        "需求分析卡",
        "需求拆解清单",
        "场景与边界说明",
        "待澄清问题清单",
        "需求分析结论",
    ]
}

# 需求分析卡必填字段（来自 templates/requirement-card.md，共14项）
REQUIRED_CARD_FIELDS = [
    "需求名称",
    "版本/迭代号",
    "需求来源",
    "背景说明",
    "目标用户",
    "使用场景",
    "核心问题",
    "需求拆解",
    "业务规则",
    "约束条件",
    "优先级",
    "待澄清项",
    "风险点",
    "需求结论",
]


# ──────────────────────────────────────────────
# 来源追溯：通用工具函数
# ──────────────────────────────────────────────


def has_traceability(line: str) -> bool:
    """检查一行是否含有来源标注"""
    return any(re.search(pat, line) for pat in TRACEABILITY_PATTERNS)


def is_table_separator(line: str) -> bool:
    return bool(re.match(r"^\|[-:\s|]+\|", line))


def is_empty_or_heading(line: str) -> bool:
    return bool(re.match(r"^\s*$", line) or re.match(r"^#+\s", line))


def table_cells(line: str) -> list:
    """解析表格行的单元格列表"""
    return [c.strip() for c in line.strip().strip("|").split("|")]


# ──────────────────────────────────────────────
# 来源追溯：按文件类型分策略检查
# ──────────────────────────────────────────────


def check_traceability_input_structured(content: str) -> dict:
    """
    input-structured.md：检查所有表格数据行和列表项。
    这是原始输入的结构化整理，每条事实都应标注来源。
    """
    lines = content.split("\n")
    issues = []
    checked = 0
    in_code_block = False

    # 表头关键词：这些作为首列时说明是表头行
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
        "条件值",
        "边界类型",
        "影响",
        "截止",
        "确认结果",
        "类别",
        "类型",
        "主任务",
        "子任务",
        "前置条件",
        "主流程",
        "异常处理",
        "对象",
        "角色",
        "可操作",
        "不可操作",
        "#",
        "检查内容",
        "场景",
        "入口",
        "问题描述",
        "影响评估",
        "确认方",
    ]

    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue
        if is_empty_or_heading(line):
            continue
        if re.match(r"^>\s", line) or re.match(r"^\*\*[^*]+\*\*\s*$", line):
            continue

        is_table_row = "|" in line and not is_table_separator(line)
        is_list_item = bool(re.match(r"^\s*[-*]\s+\S", line) or re.match(r"^\s*\d+\.\s+\S", line))

        if not (is_table_row or is_list_item):
            continue

        # 跳过表头行
        if is_table_row:
            cells = table_cells(line)
            if cells and any(kw in cells[0] for kw in HEADER_KEYWORDS):
                continue
            # 跳过纯数字/百分比统计行
            non_empty = [c for c in cells if c and c not in ("—", "-")]
            if non_empty and all(re.match(r"^[\d%（）().*A-Z\s]+$", c) for c in non_empty):
                continue

        # 跳过列表中的纯结构说明行
        if is_list_item:
            stripped = line.strip().lstrip("- *0123456789.")
            if re.match(
                r"^(参考|引用|时间|触发|确认方|影响|原因|来源|类型|详情|建议|说明|注意|用法|示例|格式|输入|输出|处理|状态)[:：]",
                stripped,
            ):
                continue

        checked += 1
        if not has_traceability(line):
            issues.append({"line": i, "content": line.strip()[:80]})

    return _make_result(checked, issues)


def check_traceability_final_analysis(content: str) -> dict:
    """
    final-analysis.md：检查5个交付物章节中的表格数据行和列表项。
    跳过：
    - 结构引用行（如 | **需求拆解** | [见交付物 B] | — |）
    - 纯粗体标签行
    - 来源注脚行（以「来源：」开头的列表行）
    - 待澄清清单（交付物D）整个区块的表格行（AI生成的问题，无需来源标注）
    - 设计输入建议区块的纯操作步骤列表（AI分析性文字）
    - 使用「下一行 来源：」模式的主场景/边界描述行（来源在下一行标注）
    """
    lines = content.split("\n")
    issues = []
    checked = 0
    in_code_block = False
    in_skip_section = False  # 待澄清清单、设计输入建议等跳过区块

    # 进入跳过区块的标题关键词
    SKIP_SECTION_HEADERS = [
        "待澄清问题清单",
        "交付物 D",
        "交付物D",
        "设计输入建议",
        "当前分析状态",  # B中的AI评估表
    ]

    # 回到检查区块的标题关键词
    RESUME_SECTION_HEADERS = [
        "交付物 E",
        "交付物E",
        "需求分析结论",
        "一句话结论",
        "详细说明",
    ]

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
        "条件值",
        "边界类型",
        "影响",
        "截止",
        "确认结果",
        "类别",
        "类型",
        "主任务",
        "子任务",
        "前置条件",
        "主流程",
        "异常处理",
        "对象",
        "角色",
        "可操作",
        "不可操作",
        "#",
        "检查内容",
        "场景",
        "入口",
        "问题描述",
        "影响评估",
        "确认方",
        "序号",
        "缺口描述",
        "需问谁",
        "优先级",
        "限制类型",
        "具体限制",
    ]

    # 表格引用值（内容列为「[见交付物X]」等的行不需要追溯）
    REFERENCE_CELL_PATTERNS = [
        r"^\[见交付物",
        r"^—$",
        r"^\[缺失\]",
        r"^见交付物",
    ]

    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # 检测是否进入/离开跳过区块
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

        # 跳过表头行
        if is_table_row:
            cells = table_cells(line)
            if cells and any(kw in cells[0] for kw in HEADER_KEYWORDS):
                continue
            # 跳过纯数字/百分比统计行
            non_empty = [c for c in cells if c and c not in ("—", "-")]
            if non_empty and all(re.match(r"^[\d%（）().*A-Z\s]+$", c) for c in non_empty):
                continue
            # 跳过引用行（内容列为「[见交付物X]」等）
            if len(cells) >= 2:
                content_cell = cells[1] if len(cells) > 1 else ""
                if any(re.match(pat, content_cell) for pat in REFERENCE_CELL_PATTERNS):
                    continue

        if is_list_item:
            # 去掉列表前缀（- 或数字.），保留 ** 等标记
            stripped_prefix = re.sub(r"^\s*[-*]\s+", "", line.strip())
            stripped_prefix = re.sub(r"^\s*\d+\.\s+", "", stripped_prefix)
            # 也计算去掉 ** 的纯文字版本（用于简单前缀匹配）
            stripped = re.sub(r"^\*\*[^*]*\*\*\s*", "", stripped_prefix).strip()
            bare = re.sub(r"\*\*", "", stripped_prefix).strip()

            # 跳过「来源：」注脚行
            if re.match(r"^来源[:：]", stripped_prefix) or re.match(r"^来源[:：]", bare):
                continue
            # 跳过其他结构说明行
            if re.match(
                r"^(参考|引用|时间|触发|确认方|影响|原因|来源|类型|详情|建议|说明|注意|用法|示例|格式|输入|输出|处理|状态)[:：]",
                bare,
            ):
                continue
            # 跳过「下一行是来源标注」模式的场景/边界/不支持描述行
            # 模式：**场景 N**：...  或  **边界 N**：...  或  不支持：...
            # 来源在下一行：  - 来源：...
            next_line = lines[i] if i < len(lines) else ""
            has_next_source = bool(
                re.match(r"^\s+-\s+来源[:：]", next_line) or re.match(r"^\s+来源[:：]", next_line)
            )
            if has_next_source:
                # 如果行本身是以 **场景/边界/不支持 开头的描述行，跳过
                if re.match(r"^\*\*(场景|边界|不支持)", stripped_prefix):
                    continue
                if re.match(r"^不支持[：:]", bare):
                    continue

        checked += 1
        if not has_traceability(line):
            issues.append({"line": i, "content": line.strip()[:80]})

    return _make_result(checked, issues)


def check_traceability_gap_analysis(content: str) -> dict:
    """
    gap-analysis.md：只检查数据表（目标用户表、场景清单、7维度表、边界条件表）。
    跳过：
    - 33项检查清单（纯AI分析——每项是「检查X是否满足」的判断，不是从输入提取的事实）
    - 检查结果汇总（纯统计行）
    - 缺口汇总表（AI生成的优先级矩阵）
    - 方法论应用区块（五问法/X-Y Problem/场景还原，全部是AI分析文字）
    检查：
    - 目标用户表、场景清单、7维度拆解表、边界条件表（从输入提取的事实内容）
    """
    lines = content.split("\n")
    issues = []
    checked = 0
    in_code_block = False
    in_skip_section = False  # 标记是否在需要跳过的区块中

    # 进入跳过区块的关键词（支持多种文档格式）
    SKIP_SECTION_KEYWORDS = [
        "33项检查清单",
        "33 项检查清单",
        "检查清单逐项",
        "检查结果汇总",
        "缺口汇总",
        "方法论应用",
        "五问法",
        "X-Y Problem",
        "场景还原",
        "缺口汇总清单",
    ]

    # 回到检查区块的关键词（数据表区块）
    RESUME_SECTION_KEYWORDS = [
        "用户与场景",
        "目标用户",
        "场景清单",
        "需求拆解",
        "边界条件",
        "边界与约束",
    ]

    # 数据表的表头关键词（表头行本身跳过）
    HEADER_KEYWORDS = [
        "角色",
        "描述",
        "来源",
        "状态",
        "维度",
        "内容",
        "边界类型",
        "条件值",
        "字段",
        "项",
        "检查内容",
        "检查项",
        "通过标准",
        "说明",
    ]

    for i, line in enumerate(lines, 1):
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # 检测章节标题（## 和 ###）
        if re.match(r"^#{1,3}\s", line):
            heading_text = line.strip()
            if any(kw in heading_text for kw in SKIP_SECTION_KEYWORDS):
                in_skip_section = True
            elif any(kw in heading_text for kw in RESUME_SECTION_KEYWORDS):
                in_skip_section = False
            continue

        if in_skip_section:
            continue

        if is_empty_or_heading(line):
            continue
        if re.match(r"^>\s", line):
            continue

        # 跳过段落汇总行（如 **A 类通过：1/4（25%）**）
        if re.match(r"^\*\*[A-Z].*通过.*\*\*$", line.strip()):
            continue

        is_table_row = "|" in line and not is_table_separator(line)
        is_list_item = bool(re.match(r"^\s*[-*]\s+\S", line) or re.match(r"^\s*\d+\.\s+\S", line))

        if not (is_table_row or is_list_item):
            continue

        # 跳过表头行
        if is_table_row:
            cells = table_cells(line)
            if cells and any(kw in cells[0] for kw in HEADER_KEYWORDS):
                continue
            # 跳过纯数字/百分比统计行
            non_empty = [c for c in cells if c and c not in ("—", "-")]
            if non_empty and all(re.match(r"^[\d%（）().*A-Z\s]+$", c) for c in non_empty):
                continue

        if is_list_item:
            stripped = line.strip().lstrip("- *0123456789.")
            if re.match(
                r"^(参考|引用|时间|触发|确认方|影响|原因|来源|类型|详情|建议|说明|注意|用法|示例|格式|输入|输出|处理|状态|发现|设计启发|追问|真实问题|评估|表面需求|真实需求)[:：→]",
                stripped,
            ):
                continue
            # 跳过粗体标签开头的分析段落行（如 **Why 1**：、**需求**：）
            if re.match(r"^\*\*[^*]+\*\*[：:]", stripped):
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
    """检查预期文件是否存在"""
    results = {"pass": [], "fail": []}
    for filename in EXPECTED_FILES:
        filepath = analysis_dir / filename
        if filepath.exists():
            results["pass"].append(filename)
        else:
            results["fail"].append(filename)
    return results


# ──────────────────────────────────────────────
# 模糊表述检查
# ──────────────────────────────────────────────


def check_vague_terms(content: str) -> list:
    """检测模糊表述"""
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


def check_sections(content: str, expected_sections: list) -> dict:
    """检查文档是否包含预期章节"""
    results = {"pass": [], "fail": []}
    for section in expected_sections:
        if section in content:
            results["pass"].append(section)
        else:
            results["fail"].append(section)
    return results


def check_card_fields(content: str) -> dict:
    """
    检查 final-analysis.md 中需求分析卡的字段完整性。
    定位「交付物 A：需求分析卡」或「需求分析卡」章节（## 级别），
    提取所有表格数据行的第一列作为字段名，与 REQUIRED_CARD_FIELDS 对比。

    返回：
      {
        "missing": [...],   # 必填但缺失的字段
        "extra": [...],     # 存在但不在必填列表的字段
        "found": [...],     # 实际找到的所有字段名
        "status": "PASS" | "WARN" | "FAIL"
      }
    """
    lines = content.split("\n")
    in_card_section = False
    found_fields = []
    in_code_block = False

    CARD_SECTION_KEYWORDS = ["需求分析卡", "交付物 A", "交付物A"]

    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        if re.match(r"^##\s", line):
            heading_text = line.strip()
            if any(kw in heading_text for kw in CARD_SECTION_KEYWORDS):
                in_card_section = True
            elif in_card_section:
                break
            continue

        if re.match(r"^###", line):
            continue

        if not in_card_section:
            continue

        if "|" not in line or is_table_separator(line):
            continue

        cells = table_cells(line)
        if not cells:
            continue

        field_name = re.sub(r"\*\*", "", cells[0]).strip()

        if field_name in ("字段", "内容", "来源追溯", "来源", ""):
            continue

        if not field_name or field_name in ("—", "-"):
            continue

        found_fields.append(field_name)

    if not found_fields:
        return {
            "missing": REQUIRED_CARD_FIELDS[:],
            "extra": [],
            "found": [],
            "status": "FAIL",
        }

    required_set = set(REQUIRED_CARD_FIELDS)
    found_set = set(found_fields)

    missing = [f for f in REQUIRED_CARD_FIELDS if f not in found_set]
    extra = [f for f in found_fields if f not in required_set]

    if missing:
        status = "FAIL"
    elif extra:
        status = "WARN"
    else:
        status = "PASS"

    return {
        "missing": missing,
        "extra": extra,
        "found": found_fields,
        "status": status,
    }


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

# 各维度满分
SCORE_WEIGHTS = {
    "file_structure": 20,  # 5个文件各4分
    "traceability": 30,  # 3个被检文件各10分，按 pass_rate 线性折算
    "card_fields": 25,  # 14个必填字段线性折算
    "sections": 15,  # 5个必要章节各3分
    "vague_terms": 10,  # 0处=10分，每处扣2分，最低0
}


def compute_score(analysis_dir: Path) -> dict:
    """
    计算分析目录的量化得分（0-100）。

    Returns:
        {
            "total": int,          # 总分 0-100
            "dimensions": {
                "file_structure": int,
                "traceability":   int,
                "card_fields":    int,
                "sections":       int,
                "vague_terms":    int,
            },
            "pass": bool,          # 是否通过（无 FAIL 维度）
        }
    """
    dims = {}
    failed = False

    # ── 1. 文件结构（20分，5个文件各4分）──
    structure = check_file_structure(analysis_dir)
    missing_count = len(structure["fail"])
    dims["file_structure"] = max(0, SCORE_WEIGHTS["file_structure"] - missing_count * 4)
    if missing_count > 0:
        failed = True

    # ── 2. 来源追溯（30分，3个被检文件各10分按 pass_rate 折算）──
    trace_files = [
        ("input-structured.md", check_traceability_input_structured),
        ("gap-analysis.md", check_traceability_gap_analysis),
        ("final-analysis.md", check_traceability_final_analysis),
    ]
    trace_score = 0
    per_file = SCORE_WEIGHTS["traceability"] // len(trace_files)  # 10
    for fname, checker in trace_files:
        fpath = analysis_dir / fname
        if not fpath.exists():
            continue  # 文件缺失已在 file_structure 扣分
        content = fpath.read_text(encoding="utf-8")
        result = checker(content)
        file_score = round(per_file * result["pass_rate"])
        trace_score += file_score
        if result["pass_rate"] < 0.8:
            failed = True
    dims["traceability"] = min(SCORE_WEIGHTS["traceability"], trace_score)

    # ── 3. 字段完整性（25分，14个必填字段线性折算）──
    final_path = analysis_dir / "final-analysis.md"
    if final_path.exists():
        content = final_path.read_text(encoding="utf-8")
        card = check_card_fields(content)
        found = len(card["found"])
        required = len(REQUIRED_CARD_FIELDS)
        dims["card_fields"] = round(SCORE_WEIGHTS["card_fields"] * found / required)
        if card["status"] == "FAIL":
            failed = True
    else:
        dims["card_fields"] = 0

    # ── 4. 章节完整性（15分，5个必要章节各3分）──
    if final_path.exists():
        content = final_path.read_text(encoding="utf-8")
        sections_result = check_sections(content, EXPECTED_SECTIONS["final-analysis.md"])
        missing_sections = len(sections_result["fail"])
        dims["sections"] = max(0, SCORE_WEIGHTS["sections"] - missing_sections * 3)
        if missing_sections > 0:
            failed = True
    else:
        dims["sections"] = 0

    # ── 5. 模糊表述控制（10分，每处扣2分，最低0）──
    vague_count = 0
    for fname in VAGUE_CHECK_FILES:
        fpath = analysis_dir / fname
        if fpath.exists():
            content = fpath.read_text(encoding="utf-8")
            vague_count += len(check_vague_terms(content))
    dims["vague_terms"] = max(0, SCORE_WEIGHTS["vague_terms"] - vague_count * 2)

    total = sum(dims.values())
    return {
        "total": total,
        "dimensions": dims,
        "pass": not failed,
    }


# ──────────────────────────────────────────────
# 主验证流程
# ──────────────────────────────────────────────

# 每个文件对应的追溯检查函数
# None = 跳过（过程文档/AI评估文档，无需追溯）
TRACEABILITY_CHECKERS = {
    "input-structured.md": check_traceability_input_structured,
    "gap-analysis.md": check_traceability_gap_analysis,
    "change-log.md": None,  # 跳过：协作过程记录，确认方字段已作为来源
    "quality-report.md": None,  # 跳过：纯AI评估，无需来源标注
    "final-analysis.md": check_traceability_final_analysis,
}

# 只对这些文件检查模糊表述（final-analysis 是交付物，必须无模糊词）
VAGUE_CHECK_FILES = {"input-structured.md", "final-analysis.md"}


def run_validation(analysis_dir: Path):
    """运行完整验证"""
    print_header("UX 需求分析质量门禁校验")
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

    # ─ 2. 各文件逐项检查 ─
    for filename in EXPECTED_FILES:
        filepath = analysis_dir / filename
        if not filepath.exists():
            continue

        content = filepath.read_text(encoding="utf-8")
        print_section(f"2. {filename}")

        # 可追溯性
        checker = TRACEABILITY_CHECKERS.get(filename)
        if checker is None:
            skip_reason = {
                "change-log.md": "协作过程记录，确认方字段已记录来源",
                "quality-report.md": "AI评估文档，无需来源标注",
            }.get(filename, "过程文档，无需来源标注")
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

        # 模糊表述（只检查交付物文件）
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
            print("  模糊表述: — 跳过（过程文档）")

        # 章节检查（针对 final-analysis.md）
        if filename in EXPECTED_SECTIONS:
            sections = check_sections(content, EXPECTED_SECTIONS[filename])
            if sections["fail"]:
                print(f"  章节完整性: ✗ FAIL（缺失 {len(sections['fail'])} 个章节）")
                for s in sections["fail"]:
                    print(f"    缺失: {s}")
                failed_dimensions.append(f"{filename} 章节")
            else:
                print("  章节完整性: ✓ PASS")

        # 字段完整性检查（针对 final-analysis.md 的需求分析卡）
        if filename == "final-analysis.md":
            card = check_card_fields(content)
            total = len(card["found"])
            required_count = len(REQUIRED_CARD_FIELDS)
            if card["status"] == "PASS":
                print(f"  字段完整性: ✓ PASS（{total}/{required_count}）")
            elif card["status"] == "WARN":
                extra_preview = ", ".join(card["extra"][:3])
                if len(card["extra"]) > 3:
                    extra_preview += f"... 共{len(card['extra'])}个"
                print(
                    f"  字段完整性: ⚠ WARN（{required_count}/{required_count} 必填字段存在，"
                    f"另有 {len(card['extra'])} 个扩展字段：{extra_preview}）"
                )
            else:  # FAIL
                missing_fields = card["missing"]
                missing_preview = "、".join(missing_fields[:5])
                if len(missing_fields) > 5:
                    missing_preview += f"... 共{len(missing_fields)}个"
                print(f"  字段完整性: ✗ FAIL（缺失必填字段：{missing_preview}）")
                total_issues += len(card["missing"])
                failed_dimensions.append(f"{filename} 字段完整性")

    # ─ 3. 总结 ─
    print_header("验证结果汇总")
    if failed_dimensions:
        print(f"  状态: ✗ FAIL")
        print(f"  总问题数: {total_issues}")
        print(f"  失败维度:")
        for d in failed_dimensions:
            print(f"    - {d}")
        print("\n  建议：返回 Stage 3 补充缺失内容后重新运行验证")
    else:
        print(f"  状态: ✓ PASS")
        print(f"  总问题数: {total_issues}（均为 WARN，不阻断）")
        print("\n  可以进入 Stage 5 整合输出")

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
