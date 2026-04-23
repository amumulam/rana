"""
单元测试：--score 量化分数功能

v0.4.0 分数模型（满分100）：
  文件结构完整性   20分  — 3个必需文件各约6.67分，缺一扣相应分
  来源追溯覆盖率   25分  — final-analysis.md 按 pass_rate 线性折算
  P0 小节完整性    25分  — 8个P0小节各约3.125分，按存在数量线性折算
  章节完整性       20分  — 8个必须章节各2.5分，缺一扣相应分
  模糊表述控制     10分  — 0处=10分，每处扣2分，最低0分
"""

import importlib.util
from pathlib import Path
import tempfile
import textwrap


def _load_validator():
    p = Path(__file__).parent.parent.parent / "rana" / "scripts" / "quality-validator.py"
    spec = importlib.util.spec_from_file_location("quality_validator", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_v = _load_validator()


def _make_dir(files: dict) -> Path:
    tmp = tempfile.mkdtemp()
    d = Path(tmp)
    for name, content in files.items():
        (d / name).write_text(textwrap.dedent(content), encoding="utf-8")
    return d


MINIMAL_FINAL = """\
## 一、概述

### 1.1 需求概述
核心矛盾描述 [PRD第1节]

### 1.2 需求来源
来源描述 [PRD第1节]

## 二、用户

### 2.1 核心用户画像
用户画像内容 [PRD第1节]

### 2.3 场景与用户目标
场景描述 [PRD第1节]

## 三、现状

### 3.1 现状与根因拆解
现状描述 [PRD第1节]

## 四、业务目标

### 4.1 业务北极星
指标内容 [PRD第1节]

## 五、策略
策略内容 [PRD第1节]

## 六、方案与验证

### 6.1 MVP
核心主干 [PRD第1节]

### 6.3 需求全清单与优先级分级
清单内容 [PRD第1节]

## 七、风险与建议
风险内容 [PRD第1节]

## 总结
成立。
"""

MINIMAL_CHANGELOG = "# 变更日志\n\n- 无变更\n"
MINIMAL_QUALITY = "# 质量报告\n\n- 通过\n"


def test_compute_score_returns_dict():
    d = _make_dir(
        {
            "final-analysis.md": MINIMAL_FINAL,
            "change-log.md": MINIMAL_CHANGELOG,
            "quality-report.md": MINIMAL_QUALITY,
        }
    )
    result = _v.compute_score(d)
    assert isinstance(result, dict)
    assert "total" in result
    assert "dimensions" in result
    assert "pass" in result


def test_compute_score_total_range():
    d = _make_dir(
        {
            "final-analysis.md": MINIMAL_FINAL,
            "change-log.md": MINIMAL_CHANGELOG,
            "quality-report.md": MINIMAL_QUALITY,
        }
    )
    result = _v.compute_score(d)
    assert 0 <= result["total"] <= 100


def test_compute_score_dimensions_keys():
    d = _make_dir(
        {
            "final-analysis.md": MINIMAL_FINAL,
            "change-log.md": MINIMAL_CHANGELOG,
            "quality-report.md": MINIMAL_QUALITY,
        }
    )
    result = _v.compute_score(d)
    expected_keys = {"file_structure", "traceability", "p0_sections", "chapters", "vague_terms"}
    assert expected_keys == set(result["dimensions"].keys())


def test_compute_score_perfect_score():
    d = _make_dir(
        {
            "final-analysis.md": MINIMAL_FINAL,
            "change-log.md": MINIMAL_CHANGELOG,
            "quality-report.md": MINIMAL_QUALITY,
        }
    )
    result = _v.compute_score(d)
    assert result["total"] == 100, (
        f"完整输入期望得100分，实际得 {result['total']} 分\n各维度: {result['dimensions']}"
    )


def test_compute_score_missing_file_deducts_points():
    d = _make_dir(
        {
            "final-analysis.md": MINIMAL_FINAL,
            "change-log.md": MINIMAL_CHANGELOG,
        }
    )
    result = _v.compute_score(d)
    assert result["dimensions"]["file_structure"] < 20
    assert result["total"] < 100


def test_compute_score_low_traceability_deducts_points():
    bad_final = """\
## 一、概述

### 1.1 需求概述
核心矛盾描述（无标注）

### 1.2 需求来源

| 来源类型 | 具体来源 | 说明 |
|----------|---------|------|
| 用户反馈 | 客服渠道反馈 | 无标注行1 |
| 产品需求 | PRD原文 | 无标注行2 |

## 二、用户

| 角色 | 特征 | 量级 | 来源 |
|------|------|------|------|
| 所有用户 | 无标注特征 | 无标注量级 | 无标注来源 |

### 2.1 核心用户画像
无标注用户画像

### 2.3 场景与用户目标

| 场景 | 用户目标 |
|------|---------|
| 日常使用 | 无标注目标 |

## 三、现状

### 3.1 现状与根因拆解

- 无标注的现状描述
- 无标注的根因分析

## 四、业务目标

### 4.1 业务北极星

| 指标名称 | 目标值 | 统计口径 | 来源 |
|----------|--------|---------|------|
| 支付成功率 | 95% | 完成/进入 | 无标注 |

## 五、策略
- 无标注策略[PRD第1节]

## 六、方案与验证

### 6.1 MVP
- 无标注MVP内容

### 6.3 需求全清单与优先级分级

| 功能点 | 优先级 | 来源 |
|--------|--------|------|
| 搜索功能 | P0 | [PRD第1节] |
| 表单优化 | P1 | [PRD第2节] |

## 七、风险与建议

- 无标注风险 [PRD第3节]

## 总结
成立。
"""
    d = _make_dir(
        {
            "final-analysis.md": bad_final,
            "change-log.md": MINIMAL_CHANGELOG,
            "quality-report.md": MINIMAL_QUALITY,
        }
    )
    result = _v.compute_score(d)
    assert result["dimensions"]["traceability"] < 25, (
        f"低标注率时 traceability 应 < 25，实际 {result['dimensions']['traceability']}"
    )


def test_compute_score_missing_p0_sections_deducts_points():
    bad_final = """\
## 一、概述

### 1.1 需求概述
内容 [PRD第1节]

## 二、用户
## 三、现状
## 四、业务目标
## 五、策略
## 六、方案与验证
## 七、风险与建议
## 总结
"""
    d = _make_dir(
        {
            "final-analysis.md": bad_final,
            "change-log.md": MINIMAL_CHANGELOG,
            "quality-report.md": MINIMAL_QUALITY,
        }
    )
    result = _v.compute_score(d)
    assert result["dimensions"]["p0_sections"] < 25


def test_compute_score_missing_chapters_deducts_points():
    bad_final = """\
## 一、概述
内容 [PRD第1节]
## 二、用户
内容 [PRD第1节]
## 三、现状
内容 [PRD第1节]
## 四、业务目标
内容 [PRD第1节]

### 1.1 需求概述
内容 [PRD第1节]
### 1.2 需求来源
内容 [PRD第1节]
### 2.1 核心用户画像
内容 [PRD第1节]
### 2.3 场景与用户目标
内容 [PRD第1节]
### 3.1 玄武与根因拆解
内容 [PRD第1节]
### 4.1 业务北极星
内容 [PRD第1节]
### 6.1 MVP
内容 [PRD第1节]
### 6.3 需求全清单与优先级分级
内容 [PRD第1节]
"""
    d = _make_dir(
        {
            "final-analysis.md": bad_final,
            "change-log.md": MINIMAL_CHANGELOG,
            "quality-report.md": MINIMAL_QUALITY,
        }
    )
    result = _v.compute_score(d)
    assert result["dimensions"]["chapters"] < 20


def test_compute_score_vague_terms_deduct_points():
    vague_final = """\
## 一、概述
### 1.1 需求概述
按钮样式应适当美观 [PRD第1节]
界面要友好清晰 [PRD第1节]

### 1.2 需求来源
来源 [PRD第1节]

## 二、用户
### 2.1 核心用户画像
用户画像 [PRD第1节]
### 2.3 场景与用户目标
场景 [PRD第1节]

## 三、现状
### 3.1 现状与根因拆解
现状 [PRD第1节]

## 四、业务目标
### 4.1 业务北极星
北极星 [PRD第1节]

## 五、策略
策略 [PRD第1节]

## 六、方案与验证
### 6.1 MVP
MVP [PRD第1节]
### 6.3 需求全清单与优先级分级
清单 [PRD第1节]

## 七、风险与建议
风险 [PRD第1节]

## 总结
成立。
"""
    d = _make_dir(
        {
            "final-analysis.md": vague_final,
            "change-log.md": MINIMAL_CHANGELOG,
            "quality-report.md": MINIMAL_QUALITY,
        }
    )
    result = _v.compute_score(d)
    assert result["dimensions"]["vague_terms"] < 10
