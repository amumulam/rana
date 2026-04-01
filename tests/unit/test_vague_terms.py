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

check_vague_terms = _v.check_vague_terms


def test_vague_triggers_shidang():
    issues = check_vague_terms("请适当调整字体大小")
    assert len(issues) == 1
    assert issues[0]["term"] == "适当"


def test_vague_triggers_tbd():
    issues = check_vague_terms("状态字段 TBD")
    assert len(issues) == 1
    assert issues[0]["term"] == "TBD"


def test_vague_no_trigger_xiangguan():
    # "相关" was removed from VAGUE_TERMS — should NOT trigger
    issues = check_vague_terms("通过相关度算法排序")
    assert issues == []


def test_vague_code_block_behavior():
    # check_vague_terms does NOT skip code blocks — documenting actual behavior
    content = "```\nTBD\n```"
    issues = check_vague_terms(content)
    # TBD inside code block IS detected (known behavior)
    assert any(i["term"] == "TBD" for i in issues)


def test_vague_clean_text():
    issues = check_vague_terms("用户点击按钮后进入详情页，查看订单状态")
    assert issues == []
