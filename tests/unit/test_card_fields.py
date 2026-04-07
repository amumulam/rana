import importlib.util
from pathlib import Path


def _load_validator():
    p = Path(__file__).parent.parent.parent / "rana" / "scripts" / "quality-validator.py"
    spec = importlib.util.spec_from_file_location("quality_validator", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_v = _load_validator()

check_card_fields = _v.check_card_fields

FULL_CARD = """## 交付物 A：需求分析卡

| 字段 | 内容 | 来源追溯 |
|------|------|---------|
| **需求名称** | 测试需求 | [PRD第1节] |
| **版本/迭代号** | v1.0 | [PRD第1节] |
| **需求来源** | 用户反馈 | [PRD第1节] |
| **背景说明** | 背景内容 | [PRD第1节] |
| **目标用户** | 已登录用户 | [PRD第1节] |
| **使用场景** | 日常使用 | [PRD第1节] |
| **核心问题** | 核心问题描述 | [PRD第1节] |
| **需求拆解** | [见交付物 B] | — |
| **业务规则** | 业务规则内容 | [PRD第1节] |
| **约束条件** | 约束内容 | [PRD第1节] |
| **优先级** | P0 | [PRD第1节] |
| **待澄清项** | [见交付物 D] | — |
| **风险点** | 风险内容 | [PRD第1节] |
| **需求结论** | [见交付物 E] | — |
"""


def test_card_fields_pass():
    result = check_card_fields(FULL_CARD)
    assert result["status"] == "PASS"
    assert result["missing"] == []
    assert result["extra"] == []


def test_card_fields_fail_missing_one():
    content = FULL_CARD.replace("| **需求拆解** | [见交付物 B] | — |\n", "")
    result = check_card_fields(content)
    assert result["status"] == "FAIL"
    assert "需求拆解" in result["missing"]


def test_card_fields_extra_does_not_downgrade():
    """扩展字段（模板增强）不应导致状态降级——全部必填字段存在时应为 PASS"""
    extra_rows = (
        "| **自定义字段A** | 额外内容 | [PRD第1节] |\n| **自定义字段B** | 额外内容 | [PRD第1节] |\n"
    )
    content = FULL_CARD.rstrip() + "\n" + extra_rows
    result = check_card_fields(content)
    assert result["status"] == "PASS", f"扩展字段不应降级，实际 status={result['status']}"
    assert len(result["extra"]) == 2  # extra 列表仍记录，但不影响状态


def test_card_fields_no_section():
    content = "# 随便一篇文档\n\n没有需求分析卡章节\n"
    result = check_card_fields(content)
    # No section found → found=[] → returns all 14 as missing, status=FAIL
    assert result["status"] == "FAIL"
    assert len(result["missing"]) == 14


def test_card_fields_truncation_8_missing():
    lines_to_remove = [
        "需求拆解",
        "业务规则",
        "约束条件",
        "优先级",
        "待澄清项",
        "风险点",
        "需求结论",
        "背景说明",
    ]
    content = FULL_CARD
    for field in lines_to_remove:
        content = content.replace(f"| **{field}**", f"| **REMOVED_{field}**")
    result = check_card_fields(content)
    assert result["status"] == "FAIL"
    assert len(result["missing"]) == 8


# 与 FULL_CARD 相同内容，但改用单 # 标题
FULL_CARD_H1 = """# 交付物 A：需求分析卡

| 字段 | 内容 | 来源追溯 |
|------|------|---------|
| **需求名称** | 测试需求 | [PRD第1节] |
| **版本/迭代号** | v1.0 | [PRD第1节] |
| **需求来源** | 用户反馈 | [PRD第1节] |
| **背景说明** | 背景内容 | [PRD第1节] |
| **目标用户** | 已登录用户 | [PRD第1节] |
| **使用场景** | 日常使用 | [PRD第1节] |
| **核心问题** | 核心问题描述 | [PRD第1节] |
| **需求拆解** | [见交付物 B] | — |
| **业务规则** | 业务规则内容 | [PRD第1节] |
| **约束条件** | 约束内容 | [PRD第1节] |
| **优先级** | P0 | [PRD第1节] |
| **待澄清项** | [见交付物 D] | — |
| **风险点** | 风险内容 | [PRD第1节] |
| **需求结论** | [见交付物 E] | — |
"""


def test_card_fields_h1_title_pass():
    """# 级别标题（单井号）的需求分析卡应被正确识别"""
    result = check_card_fields(FULL_CARD_H1)
    assert result["status"] == "PASS", f"missing={result['missing']}"
    assert result["missing"] == []


def test_card_fields_h1_subsections_pass():
    """# 级别标题 + ## 子分组表格，所有字段应被合并识别"""
    content = """# 交付物 A：需求分析卡

## 基本信息

| 字段 | 内容 | 来源追溯 |
|------|------|---------|
| **需求名称** | 测试需求 | [PRD第1节] |
| **版本/迭代号** | v1.0 | [PRD第1节] |
| **需求来源** | 用户反馈 | [PRD第1节] |
| **背景说明** | 背景内容 | [PRD第1节] |

## 用户与场景

| 字段 | 内容 | 来源追溯 |
|------|------|---------|
| **目标用户** | 已登录用户 | [PRD第1节] |
| **使用场景** | 日常使用 | [PRD第1节] |
| **核心问题** | 核心问题描述 | [PRD第1节] |

## 需求内容

| 字段 | 内容 | 来源追溯 |
|------|------|---------|
| **需求拆解** | [见交付物 B] | — |
| **业务规则** | 业务规则内容 | [PRD第1节] |
| **约束条件** | 约束内容 | [PRD第1节] |
| **优先级** | P0 | [PRD第1节] |

## 风险与待确认

| 字段 | 内容 | 来源追溯 |
|------|------|---------|
| **待澄清项** | [见交付物 D] | — |
| **风险点** | 风险内容 | [PRD第1节] |

## 结论

| 字段 | 内容 | 来源追溯 |
|------|------|---------|
| **需求结论** | [见交付物 E] | — |

# 交付物 B：需求拆解清单
"""
    result = check_card_fields(content)
    assert result["status"] == "PASS", f"missing={result['missing']}"
    assert result["missing"] == []
