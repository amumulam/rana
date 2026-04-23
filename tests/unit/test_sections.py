import importlib.util
from pathlib import Path


def _load_validator():
    p = Path(__file__).parent.parent.parent / "rana" / "scripts" / "quality-validator.py"
    spec = importlib.util.spec_from_file_location("quality_validator", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_v = _load_validator()

check_sections = _v.check_sections
check_file_structure = _v.check_file_structure
EXPECTED_CHAPTERS = _v.EXPECTED_CHAPTERS
OPTIONAL_CHAPTERS = _v.OPTIONAL_CHAPTERS
REQUIRED_FILES = _v.REQUIRED_FILES
OPTIONAL_FILES = _v.OPTIONAL_FILES


FULL_FINAL = """## 一、概述
内容
## 二、用户
内容
## 三、现状
内容
## 四、业务目标
内容
## 五、策略
内容
## 六、方案与验证
内容
## 七、风险与建议
内容
## 总结
内容
"""


def test_sections_all_present():
    result = check_sections(FULL_FINAL, EXPECTED_CHAPTERS, OPTIONAL_CHAPTERS)
    assert result["fail"] == []
    assert len(result["pass"]) == 8


def test_sections_missing_one():
    content = FULL_FINAL.replace("## 七、风险与建议\n内容\n", "")
    result = check_sections(content, EXPECTED_CHAPTERS)
    assert "七、风险与建议" in result["fail"]


def test_sections_optional_present():
    content = FULL_FINAL + "## 八、各角色重点关注\n内容\n"
    result = check_sections(content, EXPECTED_CHAPTERS, OPTIONAL_CHAPTERS)
    assert len(result["optional_pass"]) == 1
    assert result["optional_fail"] == []


def test_sections_optional_missing_not_counted_as_fail():
    result = check_sections(FULL_FINAL, EXPECTED_CHAPTERS, OPTIONAL_CHAPTERS)
    assert result["optional_fail"] == ["八、各角色重点关注"]


def test_file_structure_all_present(tmp_path):
    for fname in REQUIRED_FILES:
        (tmp_path / fname).write_text("content")
    result = check_file_structure(tmp_path)
    assert result["fail"] == []
    assert len(result["pass"]) == 3


def test_file_structure_missing_one(tmp_path):
    for fname in ["final-analysis.md", "change-log.md"]:
        (tmp_path / fname).write_text("content")
    result = check_file_structure(tmp_path)
    assert "quality-report.md" in result["fail"]


def test_file_structure_optional_detected(tmp_path):
    for fname in REQUIRED_FILES:
        (tmp_path / fname).write_text("content")
    (tmp_path / "quick-analysis.md").write_text("content")
    result = check_file_structure(tmp_path)
    assert result["optional_pass"] == ["quick-analysis.md"]
    assert result["optional_fail"] == []
