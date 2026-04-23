import importlib.util
from pathlib import Path


def _load_validator():
    p = Path(__file__).parent.parent.parent / "rana" / "scripts" / "quality-validator.py"
    spec = importlib.util.spec_from_file_location("quality_validator", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_v = _load_validator()

has_traceability = _v.has_traceability
is_table_separator = _v.is_table_separator
check_traceability_final_analysis = _v.check_traceability_final_analysis
check_sections = _v.check_sections
check_p0_sections = _v.check_p0_sections
EXPECTED_CHAPTERS = _v.EXPECTED_CHAPTERS
OPTIONAL_CHAPTERS = _v.OPTIONAL_CHAPTERS


def test_has_traceability_prd():
    assert has_traceability("用户可发送消息 [PRD第2节]") is True


def test_has_traceability_infer():
    assert has_traceability("[推断：参考同类产品]") is True


def test_has_traceability_plain():
    assert has_traceability("用户可发送消息") is False


def test_is_table_separator():
    assert is_table_separator("|---|---|") is True


def test_has_traceability_prd_with_space():
    assert has_traceability("背景说明 [PRD 第 1 节]") is True


def test_has_traceability_prd_named_section():
    assert has_traceability("来自需求清单 [PRD 需求清单]") is True


def test_has_traceability_user_confirm():
    assert has_traceability("目标用户范围已确认 [用户确认]") is True


def test_has_traceability_user_confirm_timestamp():
    assert has_traceability("约束条件已确认 [用户确认 19:16]") is True


def test_has_traceability_analysis_infer():
    assert has_traceability("该字段为系统默认 [分析推断]") is True


def test_has_traceability_analysis_create():
    assert has_traceability("版本/迭代号 v1.0 [分析创建]") is True


def test_has_traceability_pm_confirm_with_space():
    assert has_traceability("目标用户范围已确认 [PM 确认]") is True


def test_has_traceability_pm_confirm_with_space_and_note():
    assert has_traceability("风险点 [PM 确认：交设计处理]") is True


def test_has_traceability_dev_confirm_with_space():
    assert has_traceability("接口依赖已确认 [研发确认]") is True
    assert has_traceability("接口依赖已确认 [研发 确认]") is True


def test_has_traceability_test_confirm_with_space():
    assert has_traceability("验收规则 [测试 确认]") is True


def test_has_traceability_business_confirm_with_space():
    assert has_traceability("业务规则 [业务 确认]") is True


def test_has_traceability_designer_confirm_with_space():
    assert has_traceability("视觉规范 [设计师 确认]") is True


def test_traceability_final_analysis_annotated():
    content = """\
## 二、用户

### 2.1 核心用户画像

| 角色 | 关键特征 | 量级 | 来源 |
|------|---------|------|------|
| 高频支付用户 | 25-35岁，通勤单手操作 | 约50万 | [PRD第1节] |

## 三、现状

### 3.1 现状与根因拆解

- 用户找不到常用银行卡 [PRD第2节]
- 顶部入口曝光不足 [截图 1]
"""
    result = check_traceability_final_analysis(content)
    assert result["pass_rate"] == 1.0, f"issues={result['issues']}"


def test_traceability_final_analysis_none_annotated():
    content = """\
## 二、用户

| 角色 | 关键特征 | 量级 |
|------|---------|------|
| 高频支付用户 | 25-35岁 | 约50万 |
"""
    result = check_traceability_final_analysis(content)
    assert result["pass_rate"] == 0.0


def test_traceability_final_analysis_skip_summary_section():
    content = """\
## 总结

成立。

- 核心矛盾：支付效率低
- 建议优先解决MVP主干
"""
    result = check_traceability_final_analysis(content)
    assert result["checked"] == 0 or result["pass_rate"] == 1.0


def test_traceability_final_analysis_skip_p0_clarification():
    content = """\
### 待澄清项

| # | 问题 | 影响 | 截止 | 状态 |
|---|------|------|------|------|
| 1 | 入口位置在哪？ | 高 | 设计前 | 待确认 |
"""
    result = check_traceability_final_analysis(content)
    assert result["checked"] == 0 or result["pass_rate"] == 1.0


def test_traceability_final_analysis_skip_optional_chapter():
    content = """\
## 八、各角色重点关注（可选）

### 产品经理关注

- 核心链路转化率
- 商业指标达成
"""
    result = check_traceability_final_analysis(content)
    assert result["checked"] == 0 or result["pass_rate"] == 1.0


def test_traceability_final_analysis_cross_reference_row():
    content = """\
## 六、方案与验证

### 6.3 需求全清单与优先级分级

| 功能点 | 优先级 | 来源 |
|--------|--------|------|
| 统一消息中心 | P0 | [PRD第1节] |
| 消息分类跳转 | [见3.1现状] | — |
"""
    result = check_traceability_final_analysis(content)
    assert result["pass_rate"] == 1.0, f"issues={result['issues']}"


def test_traceability_skip_code_block():
    content = "```\n无注释的行\n```\n"
    result = check_traceability_final_analysis(content)
    assert result["checked"] == 0


def test_has_traceability_screenshot_with_space():
    assert has_traceability("页面结构信息 [截图 1]") is True


def test_has_traceability_screenshot_no_space():
    assert has_traceability("页面结构信息 [截图1]") is True


def test_has_traceability_screenshot_with_note():
    assert has_traceability("导航栏结构 [截图 1 局部]") is True


def test_check_p0_sections_all_present():
    content = """\
### 1.1 需求概述
内容
### 1.2 需求来源
内容
### 2.1 核心用户画像
内容
### 2.3 场景与用户目标
内容
### 3.1 现状与根因拆解
内容
### 4.1 业务北极星
内容
### 6.1 MVP
内容
### 6.3 需求全清单与优先级分级
内容
"""
    result = check_p0_sections(content)
    assert result["status"] == "PASS"
    assert len(result["missing"]) == 0
    assert len(result["found"]) == 8


def test_check_p0_sections_missing_one():
    content = """\
### 1.1 需求概述
内容
### 1.2 需求来源
内容
### 2.1 核心用户画像
内容
### 2.3 场景与用户目标
内容
### 3.1 现状与根因拆解
内容
### 4.1 业务北极星
内容
### 6.1 MVP
内容
"""
    result = check_p0_sections(content)
    assert result["status"] == "FAIL"
    assert len(result["missing"]) == 1
    assert "6.3" in result["missing"][0]


def test_check_p0_sections_empty():
    content = "# 空文档\n"
    result = check_p0_sections(content)
    assert result["status"] == "FAIL"
    assert len(result["missing"]) == 8


def test_check_sections_all_present():
    content = "## 一、概述\n## 二、用户\n## 三、现状\n## 四、业务目标\n## 五、策略\n## 六、方案与验证\n## 七、风险与建议\n## 总结\n"
    result = check_sections(content, EXPECTED_CHAPTERS, OPTIONAL_CHAPTERS)
    assert result["fail"] == []
    assert len(result["pass"]) == 8


def test_check_sections_missing_one():
    content = "## 一、概述\n## 二、用户\n## 三、现状\n## 四、业务目标\n## 五、策略\n## 六、方案与验证\n## 总结\n"
    result = check_sections(content, EXPECTED_CHAPTERS)
    assert "七、风险与建议" in result["fail"]
