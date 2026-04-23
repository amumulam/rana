import importlib.util
from pathlib import Path


def _load_validator():
    p = Path(__file__).parent.parent.parent / "rana" / "scripts" / "quality-validator.py"
    spec = importlib.util.spec_from_file_location("quality_validator", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_v = _load_validator()

check_p0_sections = _v.check_p0_sections
P0_REQUIRED_SECTIONS = _v.P0_REQUIRED_SECTIONS


FULL_P0 = """\
### 1.1 需求概述
核心矛盾描述
### 1.2 需求来源
来源描述
### 2.1 核心用户画像
用户画像内容
### 2.3 场景与用户目标
场景描述
### 3.1 现状与根因拆解
现状描述
### 4.1 业务北极星
指标内容
### 6.1 MVP
核心主干
### 6.3 需求全清单与优先级分级
清单内容
"""


def test_p0_sections_pass():
    result = check_p0_sections(FULL_P0)
    assert result["status"] == "PASS"
    assert result["missing"] == []
    assert len(result["found"]) == 8


def test_p0_sections_fail_missing_one():
    content = FULL_P0.replace("### 6.3 需求全清单与优先级分级\n清单内容\n", "")
    result = check_p0_sections(content)
    assert result["status"] == "FAIL"
    assert "6.3 需求全清单与优先级分级" in result["missing"]


def test_p0_sections_empty_document():
    content = "# 随便一篇文档\n\n没有P0小节\n"
    result = check_p0_sections(content)
    assert result["status"] == "FAIL"
    assert len(result["missing"]) == 8


def test_p0_sections_regex_flexible():
    content = """\
###  1.1 需求概述
内容
### 2.1 核心用户画像（基础属性+痛点）
内容
###  6.1 MVP 核心主干
内容
"""
    result = check_p0_sections(content)
    assert "1.1 需求概述" in result["found"]
    assert "2.1 核心用户画像" in result["found"]
    assert "6.1 MVP" in result["found"]
