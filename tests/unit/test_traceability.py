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
check_traceability_input_structured = _v.check_traceability_input_structured
check_traceability_final_analysis = _v.check_traceability_final_analysis
check_traceability_gap_analysis = _v.check_traceability_gap_analysis


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


def test_has_traceability_pm_confirm_with_space():
    """[PM 确认] 带空格变体应被识别"""
    assert has_traceability("目标用户范围已确认 [PM 确认]") is True


def test_has_traceability_pm_confirm_with_space_and_note():
    """[PM 确认：交设计处理] 带空格和附注应被识别"""
    assert has_traceability("风险点 [PM 确认：交设计处理]") is True


def test_has_traceability_dev_confirm_with_space():
    """[研发 确认] 等带空格变体应被识别"""
    assert has_traceability("接口依赖已确认 [研发确认]") is True
    assert has_traceability("接口依赖已确认 [研发 确认]") is True


def test_has_traceability_test_confirm_with_space():
    """[测试 确认] 带空格变体应被识别"""
    assert has_traceability("验收规则 [测试 确认]") is True


def test_has_traceability_business_confirm_with_space():
    """[业务 确认] 带空格变体应被识别"""
    assert has_traceability("业务规则 [业务 确认]") is True


def test_has_traceability_designer_confirm_with_space():
    """[设计师 确认] 带空格变体应被识别"""
    assert has_traceability("视觉规范 [设计师 确认]") is True


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


def test_final_analysis_cross_reference_rows_skipped():
    """来源列为 — 且内容为「见下文/见交付物」的交叉引用行应被跳过"""
    content = """\
## 需求分析卡

| 字段 | 内容 | 来源追溯 |
|------|------|---------|
| **需求名称** | 服务优化 | [PRD第1节] |
| **需求拆解** | 见下文「需求拆解清单」 | — |
| **需求结论** | 见下文「需求分析结论」 | — |
"""
    result = check_traceability_final_analysis(content)
    # 需求名称有来源，需求拆解和需求结论是引用行应跳过
    assert result["pass_rate"] == 1.0, f"issues={result['issues']}, checked={result['checked']}"


def test_final_analysis_dash_source_column_skipped():
    """来源列（第3列）为 — 的 [见交付物] 行应被视为合法引用行，跳过检查"""
    content = """\
## 需求分析卡

| 字段 | 内容 | 来源追溯 |
|------|------|---------|
| **待澄清项** | [见交付物 D] | — |
| **风险点** | 风险内容 | [PRD第1节] |
"""
    result = check_traceability_final_analysis(content)
    assert result["pass_rate"] == 1.0, f"issues={result['issues']}, checked={result['checked']}"


# ──────────────────────────────────────────────
# Bug 1: 分组行 | **▌ 基本信息** | | | 不应被计入检查
# ──────────────────────────────────────────────


def test_final_analysis_group_row_skipped():
    """需求分析卡分组行（**▌ 分组名**）不含实质内容，不应被计入来源追溯检查"""
    content = """\
## 需求分析卡

| 字段 | 内容 | 来源追溯 |
|------|------|---------|
| **▌ 基本信息** | | |
| 需求名称 | 服务首页优化 | [用户确认] |
| **▌ 用户与场景** | | |
| 目标用户 | 所有 vivo 用户 | [PM 确认] |
"""
    result = check_traceability_final_analysis(content)
    assert result["pass_rate"] == 1.0, f"issues={result['issues']}, checked={result['checked']}"


# ──────────────────────────────────────────────
# Bug 2: [截图 1] 带空格应被 has_traceability 识别
# ──────────────────────────────────────────────


def test_has_traceability_screenshot_with_space():
    """[截图 1] 截图编号与数字之间有空格，应被识别为合法来源"""
    assert has_traceability("页面结构信息 [截图 1]") is True


def test_has_traceability_screenshot_no_space():
    """[截图1] 无空格变体仍应被识别"""
    assert has_traceability("页面结构信息 [截图1]") is True


def test_has_traceability_screenshot_with_note():
    """[截图 1 局部] 带附注变体应被识别"""
    assert has_traceability("导航栏结构 [截图 1 局部]") is True


def test_gap_analysis_7dim_table_inline_source():
    """gap-analysis 7维度拆解表：来源嵌在内容列（cells[1]）时，整行应被认为有追溯"""
    content = """\
## 需求拆解（7 维度）

### 功能一：维修楼层前置

| 维度 | 内容 | 状态 |
|------|------|------|
| 主任务 | 用户快速进入维修服务 [截图 1] | ✓ 明确 |
| 子任务 | 预约维修、寄修服务 [截图 1] | ✓ 明确 |
| 分支流程 | [缺失] 不同维修类型分流逻辑 [缺失] | ✗ 缺失 |
"""
    result = check_traceability_gap_analysis(content)
    assert result["pass_rate"] == 1.0, f"issues={result['issues']}, checked={result['checked']}"


# ──────────────────────────────────────────────
# Bug 3: 交付物B表头行（页面/分支条件/流程描述）未被跳过
# ──────────────────────────────────────────────


def test_final_analysis_deliverable_b_table_headers_skipped():
    """交付物B中页面/入口/来源、分支条件/流程描述/来源等表头行应被跳过"""
    content = """\
## 需求拆解清单

### 功能一：维修楼层前置

| 页面 | 入口 | 来源 |
|------|------|------|
| 服务首页 | 底部导航「服务」Tab | [截图 1] |

| 分支条件 | 流程描述 | 来源 |
|---------|---------|------|
| 用户已登录 | 直接进入维修模式页面 | [推断：线上原有逻辑] |
"""
    result = check_traceability_final_analysis(content)
    assert result["pass_rate"] == 1.0, f"issues={result['issues']}, checked={result['checked']}"


# ──────────────────────────────────────────────
# Bug 4: 交付物D（状态说明/待澄清问题表/汇总统计）应整体跳过
# ──────────────────────────────────────────────


def test_final_analysis_deliverable_d_status_table_skipped():
    """交付物D内的状态说明表不需要来源标注，应被跳过"""
    content = """\
# 交付物 D：待澄清问题清单

## 状态说明

| 状态 | 含义 |
|------|------|
| ⏳ 待确认 | 尚未得到回答 |
| ✓ 已确认 | 已得到明确答复，记录在 change-log.md |
| ⚠ 风险 | 无法在本期内确认，已标注为风险点 |
"""
    result = check_traceability_final_analysis(content)
    assert result["checked"] == 0 or result["pass_rate"] == 1.0, (
        f"issues={result['issues']}, checked={result['checked']}"
    )


def test_final_analysis_deliverable_d_summary_table_skipped():
    """交付物D汇总统计表不需要来源标注，应被跳过"""
    content = """\
# 交付物 D：待澄清问题清单

## 汇总统计

| 确认对象 | 问题数 | P0 | P1 | P2 |
|---------|--------|----|----|-----|
| 研发 | 1 | 0 | 1 | 0 |
| 测试 | 0 | 0 | 0 | 0 |
"""
    result = check_traceability_final_analysis(content)
    assert result["checked"] == 0 or result["pass_rate"] == 1.0, (
        f"issues={result['issues']}, checked={result['checked']}"
    )


# ──────────────────────────────────────────────
# Bug 5: 交付物E（需求分析结论）应整体跳过
# ──────────────────────────────────────────────


def test_final_analysis_deliverable_e_skipped():
    """交付物E的列表项是结论汇总，已在前面追溯，不应再要求逐行标注"""
    content = """\
# 交付物 E：需求分析结论

## 详细说明

**在什么场景**

描述：
- 维修场景：手机出故障时，用户焦急地寻找维修入口
- 客服场景：使用遇到问题时，用户需要快速获得帮助

**本次优先解决**

描述：
1. 维修楼层前置：将维修模式从底部功能列表移至「我要维修」楼层内
2. 客服楼层改造：按会员等级展示专属皮肤
"""
    result = check_traceability_final_analysis(content)
    assert result["checked"] == 0 or result["pass_rate"] == 1.0, (
        f"issues={result['issues']}, checked={result['checked']}"
    )
