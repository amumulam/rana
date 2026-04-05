import importlib.util
from pathlib import Path


def _load_validator():
    p = (
        Path(__file__).parent.parent.parent
        / "ux-requirement-analysis"
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


def test_has_traceability_prd_with_space():
    """[PRD 第X节] 有空格变体应被识别"""
    assert has_traceability("背景说明 [PRD 第 1 节]") is True


def test_has_traceability_prd_named_section():
    """[PRD 需求清单] 命名章节应被识别"""
    assert has_traceability("来自需求清单 [PRD 需求清单]") is True


def test_has_traceability_user_confirm():
    """[用户确认] 应被识别（等价于对话确认）"""
    assert has_traceability("目标用户范围已确认 [用户确认]") is True


def test_has_traceability_user_confirm_timestamp():
    """[用户确认 19:16] 带时间戳变体应被识别"""
    assert has_traceability("约束条件已确认 [用户确认 19:16]") is True


def test_has_traceability_analysis_infer():
    """[分析推断] 裸推断变体应被识别"""
    assert has_traceability("该字段为系统默认 [分析推断]") is True


def test_has_traceability_analysis_create():
    """[分析创建] 系统生成占位应被识别"""
    assert has_traceability("版本/迭代号 v1.0 [分析创建]") is True


def test_section_level_traceability_propagates():
    """章节标题 [PRD第X节] 的来源应传播到该节下的所有列表项"""
    content = (
        "### 1. 维修模式优化 [PRD第1节]\n"
        "- **当前状态**：位于第 5 屏，CTR 5.3%\n"
        "- **优化方案**：前置到第 1 位\n"
        "- **预期指标**：CTR ≥6.0%\n"
        "\n"
        "### 2. 客服优化 [PRD第2节]\n"
        "- **高端人群**：CTR 9.01%\n"
    )
    result = check_traceability_input_structured(content)
    assert result["pass_rate"] == 1.0, f"issues={result['issues']}"
    assert result["issues"] == []


def test_section_level_traceability_stops_at_new_section():
    """进入新章节后，旧章节的来源传播应停止；新章节无标注则重新要求"""
    content = (
        "### 1. 有标注的节 [PRD第1节]\n"
        "- 这行应被豁免\n"
        "\n"
        "### 2. 没有标注的节\n"
        "- 这行应被检查（无来源）\n"
    )
    result = check_traceability_input_structured(content)
    # 第1节的列表项豁免（不计入 checked），第2节的列表项被检查且未标注
    assert result["checked"] == 1
    assert result["pass_rate"] == 0.0


def test_section_level_traceability_table_rows():
    """章节级来源传播应同样适用于表格数据行"""
    content = (
        "### 关键数据 [PRD需求清单]\n"
        "| 模块 | 当前 UV | 当前 CTR |\n"
        "|------|--------|----------|\n"
        "| 维修模式 | 4.2 万 | 5.3% |\n"
        "| 客服卡片 | - | 9.01% |\n"
    )
    result = check_traceability_input_structured(content)
    assert result["pass_rate"] == 1.0, f"issues={result['issues']}"


def test_section_h2_annotated_h3_unannotated():
    """## 有标注但 ### 子节无标注时，### 下内容应被检查（扁平替换行为）"""
    content = "## 父节 [PRD第1节]\n- 直接在 ## 下的行\n\n### 子节\n- 子节下的行\n"
    result = check_traceability_input_structured(content)
    # ## 下的列表项豁免，### 无标注所以子节下的行被检查
    assert result["checked"] == 1
    assert result["pass_rate"] == 0.0
