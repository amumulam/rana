import importlib.util
from pathlib import Path


def _load_validator():
    p = (
        Path(__file__).parent.parent.parent
        / "ux-requirements-analyzer"
        / "scripts"
        / "quality-validator.py"
    )
    spec = importlib.util.spec_from_file_location("quality_validator", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_v = _load_validator()
has_traceability = _v.has_traceability
is_table_separator = _v.is_table_separator
check_traceability_input_structured = _v.check_traceability_input_structured


def test_has_traceability_prd():
    assert has_traceability("用户可发送消息 [PRD第2节]") is True


def test_has_traceability_infer():
    assert has_traceability("[推断：参考同类产品]") is True


def test_has_traceability_plain():
    assert has_traceability("用户可发送消息") is False


def test_is_table_separator():
    assert is_table_separator("|---|---|") is True


def test_traceability_all_annotated():
    # Use a header row whose first cell is in HEADER_KEYWORDS so it is skipped
    content = (
        "| 字段 | 内容 | 来源追溯 |\n"
        "|---|---|---|\n"
        "| 登录 | 用户登录 | [PRD第1节] |\n"
        "| 注册 | 新用户注册 | [PRD第2节] |\n"
        "| 退出 | 用户退出 | [PRD第3节] |\n"
    )
    result = check_traceability_input_structured(content)
    assert result["pass_rate"] == 1.0
    assert result["issues"] == []


def test_traceability_none_annotated():
    # Use a header row whose first cell is in HEADER_KEYWORDS so it is skipped
    content = (
        "| 字段 | 内容 |\n"
        "|---|---|\n"
        "| 登录 | 用户登录 |\n"
        "| 注册 | 新用户注册 |\n"
        "| 退出 | 用户退出 |\n"
    )
    result = check_traceability_input_structured(content)
    assert result["pass_rate"] == 0.0


def test_traceability_boundary_75pct():
    # 4 data rows: 3 annotated, 1 not → pass_rate = 0.75 < 0.80
    # Use header row with first cell in HEADER_KEYWORDS so it is skipped
    content = (
        "| 字段 | 内容 |\n"
        "|---|---|\n"
        "| 登录 | 用户登录 [PRD第1节] |\n"
        "| 注册 | 新用户注册 [PRD第2节] |\n"
        "| 退出 | 用户退出 [PRD第3节] |\n"
        "| 搜索 | 用户搜索商品 |\n"
    )
    result = check_traceability_input_structured(content)
    assert result["pass_rate"] == 0.75
    assert len(result["issues"]) == 1


def test_traceability_skip_code_block():
    # Lines inside code blocks should not be counted
    content = "```\n无注释的行\n```\n"
    result = check_traceability_input_structured(content)
    assert result["checked"] == 0
