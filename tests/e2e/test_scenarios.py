import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).parent.parent.parent
VALIDATOR = REPO_ROOT / "rana" / "scripts" / "quality-validator.py"
TEST_RUNS = Path(__file__).parent.parent / "fixtures"

# v0.4.0 validator changes:
# - Required files: final-analysis.md, change-log.md, quality-report.md (3, not 5)
# - input-structured.md and gap-analysis.md removed (v0.3 deliverables)
# - P0 section check replaces "字段完整性" (需求分析卡 14-field card check)
# - Chapter check: 八章节+总结 (not five 交付物)


def run_validator(scenario_dir: Path):
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(scenario_dir)],
        capture_output=True,
        text=True,
    )
    return result.returncode, result.stdout


def test_scenario_a_normal():
    code, out = run_validator(TEST_RUNS / "test-a-normal")
    assert code == 0, f"Expected exit 0, got {code}\nOutput:\n{out}"
    assert "✓ PASS" in out


def test_scenario_b_edge():
    code, out = run_validator(TEST_RUNS / "test-b-edge")
    assert code == 1, f"Expected exit 1, got {code}\nOutput:\n{out}"
    assert "P0 小节完整性" in out


def test_scenario_c_multi_feature():
    code, out = run_validator(TEST_RUNS / "test-c-multi-feature")
    assert code == 0, f"Expected exit 0, got {code}\nOutput:\n{out}"
    assert "✓ PASS" in out


def test_scenario_d_conflict():
    code, out = run_validator(TEST_RUNS / "test-d-conflict")
    assert code == 0, f"Expected exit 0, got {code}\nOutput:\n{out}"
    assert "✓ PASS" in out


def test_scenario_e_traceability_fail():
    code, out = run_validator(TEST_RUNS / "test-e-traceability-fail")
    assert code == 1, f"Expected exit 1, got {code}\nOutput:\n{out}"
    assert "来源追溯" in out or "可追溯性" in out


def test_scenario_f_screenshot_input():
    """截图输入场景：覆盖 [截图 1] [PM 确认] 等截图类来源追溯标注"""
    code, out = run_validator(TEST_RUNS / "test-f-screenshot-input")
    assert code == 0, f"Expected exit 0, got {code}\nOutput:\n{out}"
    assert "✓ PASS" in out
