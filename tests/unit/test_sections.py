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

check_sections = _v.check_sections
check_file_structure = _v.check_file_structure

EXPECTED = ["需求分析卡", "需求拆解清单", "场景与边界说明", "待澄清问题清单", "需求分析结论"]

FULL_FINAL = """## 需求分析卡
内容
## 需求拆解清单
内容
## 场景与边界说明
内容
## 待澄清问题清单
内容
## 需求分析结论
内容
"""


def test_sections_all_present():
    result = check_sections(FULL_FINAL, EXPECTED)
    assert result["fail"] == []
    assert len(result["pass"]) == 5


def test_sections_missing_one():
    content = FULL_FINAL.replace("## 需求分析结论\n内容\n", "")
    result = check_sections(content, EXPECTED)
    assert "需求分析结论" in result["fail"]


def test_file_structure_all_present(tmp_path):
    for fname in [
        "input-structured.md",
        "gap-analysis.md",
        "change-log.md",
        "quality-report.md",
        "final-analysis.md",
    ]:
        (tmp_path / fname).write_text("content")
    result = check_file_structure(tmp_path)
    assert result["fail"] == []
    assert len(result["pass"]) == 5


def test_file_structure_missing_one(tmp_path):
    for fname in ["input-structured.md", "change-log.md", "quality-report.md", "final-analysis.md"]:
        (tmp_path / fname).write_text("content")
    # gap-analysis.md intentionally not created
    result = check_file_structure(tmp_path)
    assert "gap-analysis.md" in result["fail"]
