# AGENTS.md — UX Requirement Analysis

This project is an **OpenCode Skill** that helps UX designers turn PM PRDs into structured requirement analysis documents. The core deliverable is `rana/` — a skill directory installable into `~/.agents/skills/`.

**GitHub:** https://github.com/amumulam/rana

---

## Deployment Environments

This skill is deployed in **two environments**:

| Environment | Platform | Skill install path | Notes |
|-------------|----------|--------------------|-------|
| Local (macOS) | BlueCode / OpenCode | `~/.agents/skills/rana/` | Dev machine |
| Server | OpenClaw | `~/.openclaw/skills/rana/` | Production environment used for real online tests |

**Important**: When reviewing online test outputs (e.g. `tests/online-test/*/out/quality-report.md`), the validator path `~/.openclaw/skills/rana/scripts/quality-validator.py` is the **real, correct path** on the server. Do NOT flag this as an error or "forged result".

---

## Development Workflow

**DO NOT auto-sync to any skill install directory during development.**

- The `~/.agents/skills/rana/` directory is the local BlueCode/OpenCode install target
- The `~/.openclaw/skills/rana/` directory is the production deployment target
- **Sync only when explicitly requested by user** (e.g., user says "同步" or "sync to install directory")
- Development work happens in `rana/` directory in this repo
- Manual sync commands when needed:
  - Local: `cp -r rana/. ~/.agents/skills/rana/`
  - Server: `cp -r rana/. ~/.openclaw/skills/rana/`

---

## Skill Creation Guideline

**本项目遵循 `./skill-creat-guideline/` 目录下的指南进行 skill 开发。**

关键规范：

### 目录结构

```
skill-name/
├── SKILL.md (required)
└── Bundled Resources (optional)
    ├── scripts/          - 可执行代码（Python/Bash等）
    ├── references/       - 需加载入 context 的参考文档
    └── assets/           - 输出使用的文件（模板、图标等）
```

### 文件命名规范

- **所有文件名使用英文**，避免中英夹杂
- 中文名称的内容文件移至 `assets/` 或 `references/`，使用英文命名并在文件开头注明中文标题

### 核心原则（来自 Best practices for skill creators.md）

1. **SKILL.md 精简** — 建议不超过 500 行 / 5000 tokens
2. **渐进式披露** — 详细内容放 `references/`，在 SKILL.md 中说明何时加载
3. **避免重复** — 信息只存在一处，不同时在 SKILL.md 和 references 中
4. **提供默认而非菜单** — 多个选项时给出默认推荐
5. **按脆弱性校准** — 脆弱操作用具体指令，灵活操作用原则指导

---

## Critical Technical Reality: PDF Handling in CLI Agents

**The `read` tool does NOT work on PDFs in OpenCode/BlueCode.** It returns `PDF read successfully` with no content.

"Models can natively read PDFs" is true in web UIs (e.g., Claude.ai with file upload). It is **not true** in CLI agent environments where the only input channel is text/tool calls.

### What is and isn't available in this environment

| Method | Status | Notes |
|--------|--------|-------|
| `read` tool on `.pdf` | **Broken** | Returns no content |
| `pdfplumber` (Python) | Not installed | Would need `pip install` |
| `pdf2image` (Python) | Not installed | Would need poppler |
| `pdftotext` (CLI) | Not installed | Would need poppler-utils |
| `PyMuPDF` / `pypdf` | Not installed | Would need `pip install` |
| macOS `textutil` | Fails on PDF | Only works on Office/RTF/HTML |
| macOS `qlmanage` | Partial | Can render preview but not extract text programmatically |

### Correct strategy for PDF integration tests

**已采用方案：pdfplumber 作为 dev 依赖（安装命令：`pip3 install pdfplumber`）**

`tests/integration/conftest.py` 在 pytest session 启动时自动用 pdfplumber 提取
PDF 文字/表格/图片元数据，生成 Stage 1 格式的 `input-structured.md`，
不依赖任何 LLM API 调用，纯静态文件操作。

测试全部在 CLI agent session 中端到端自动运行：

```bash
python3 -m pytest tests/integration/ -v
```

如需重新生成 fixture 输出，删除对应 `test-runs/file-input/outputs/` 子目录后重跑测试即可。

### SKILL.md accuracy note

`SKILL.md` currently states: _"直接将 .pdf 文件上传给模型即可。模型原生支持多模态读取"_

This is accurate **only** when the skill is used via a web UI that supports file attachments. When used via CLI agents (OpenCode, BlueCode), the PDF must be pre-processed. The SKILL.md user-facing instructions do not need to change (they describe the UX designer's experience, not the technical pipeline), but any agent doing integration testing must be aware of this gap.

---

## Project Structure

```
rana/  (repo root, local path: requirements-analysis/)
├── rana/         # Skill source (canonical copy)
│   ├── SKILL.md                     # Skill definition — dual-mode workflow, 3-stage specs (~300 lines)
│   ├── scripts/
│   │   └── quality-validator.py     # CLI quality gate checker (v0.4.0, 3 required files + P0 sections)
│   ├── references/
│   │   ├── collaboration-protocol.md  # 批判反驳与协作对话规范（Quick/Full 通用）
│   │   ├── p0-gates.md               # P0 缺口规则（v0.4.0）
│   │   ├── stage-1-diagnosis.md      # 诊断层详细流程（v0.4.0）
│   │   ├── stage-2-solution.md       # 方案层详细流程（v0.4.0）
│   │   ├── stage-3-refine.md         # 提炼层详细流程（v0.4.0）
│   │   ├── analysis-methods.md       # HMW/MVP/五问法/X-Y Problem
│   │   ├── _archived-stage-1-guideline.md  # 归档旧四阶段版
│   │   ├── _archived-stage-2-guideline.md  # 归档旧四阶段版
│   │   ├── _archived-stage-3-guideline.md  # 归档旧四阶段版
│   │   ├── analysis-checklist.md     # 33-item checklist (旧版,待评估)
│   │   ├── traceability-guide.md     # Source annotation conventions (旧版,待评估)
│   │   └── quality-gates.md          # 5-dimension quality gate standards (旧版,待评估)
│   ├── assets/
│   │   ├── analysis-template-full.md  # Full Mode 输出模板（8章+总结，v0.4.0）
│   │   └── analysis-template-quick.md # Quick Mode 快速分析模板（四维度+提问清单，v0.4.0）
│   └── config.yaml                    # file_parser 配置
├── tests/
│   ├── unit/                        # pytest unit tests for validator functions
│   └── e2e/                         # E2E tests via subprocess CLI calls
├── test-runs/                       # E2E test fixtures (one dir per scenario)
│   ├── test-a-normal/               # Normal case → PASS
│   ├── test-b-edge/                 # Minimal input → FAIL (missing field)
│   ├── test-c-multi-feature/        # Multi-feature PRD → PASS
│   ├── test-d-conflict/             # Conflict in change-log → PASS
│   └── test-e-traceability-fail/    # Low traceability rate → FAIL
├── docs/superpowers/
│   ├── specs/                       # Design documents (brainstorming output)
│   └── plans/                       # Implementation plans (writing-plans output)
├── ref/                             # Reference outputs (输出参考.md)
└── pyproject.toml                   # pytest + ruff config
```

**Runtime directories (created during skill execution):**

```
<workspace>/
├── ux-requirement-analysis/
│   ├── _temp/                            # Stage 0 文件预处理临时输出
│   │   └── {filename}/auto/{filename}.md
│   └── <需求名称>/<YYYY-MM-DD>/
│       ├── final-analysis.md              # Full Mode 主输出（8章+总结）
│       ├── quick-analysis.md              # Quick Mode 快速分析
│       ├── change-log.md                  # 协作记录
│       └── quality-report.md              # AI自评（简化）
```

**Install copy:** After every change to `rana/`, sync:
```bash
cp -r rana/. ~/.agents/skills/rana/
```

---

## Build / Lint / Test Commands

### Install dev dependencies (first time)
```bash
pip3 install pdfplumber
```

### Run all tests
```bash
python3 -m pytest tests/ -v
```

### Run a single test file
```bash
python3 -m pytest tests/unit/test_traceability.py -v
```

### Run a single test by name
```bash
python3 -m pytest tests/unit/test_traceability.py::test_has_traceability_prd -v
```

### Run only unit tests
```bash
python3 -m pytest tests/unit/ -v
```

### Run only E2E tests
```bash
python3 -m pytest tests/e2e/ -v
```

### Run integration tests (requires pdfplumber)
```bash
python3 -m pytest tests/integration/ -v
```
集成测试会自动用 pdfplumber 提取 `test-runs/file-input/fixtures/` 中的 PDF，
生成 `test-runs/file-input/outputs/` 下的输出文件，然后验证其结构。
fixture 文件不存在时自动跳过对应场景，不视为失败。

### Run the validator manually
```bash
python3 rana/scripts/quality-validator.py test-runs/test-a-normal
```

### Lint (ruff must be installed: `pip3 install ruff`)
```bash
ruff check rana/scripts/
```

**Note:** Use `python3` not `python` — only `python3` is on PATH. pytest is at `~/.Library/Python/3.9/bin/pytest` but `python3 -m pytest` always works.

---

## Code Style — quality-validator.py

### Language & version
- Python 3.9+, no third-party dependencies (stdlib only: `re`, `sys`, `pathlib`)

### Imports
- Stdlib only; grouped as: stdlib → (no third-party) → local
- One import per line; `pathlib.Path` preferred over `os.path`

### Formatting
- Line length: 100 characters (per pyproject.toml)
- 4-space indentation, no tabs
- Section separators use `# ──────────────────────────────────────────────`
- Constants in `UPPER_SNAKE_CASE` at module level, grouped by purpose

### Types
- No type annotations required, but function signatures use basic annotations where present:
  `def fn(content: str) -> dict:` / `-> list:` / `-> bool:`
- Return dicts use consistent key names: `{"checked": int, "issues": list, "pass_rate": float}`

### Naming conventions
- Functions: `check_<what>` for validators, `has_<property>` for boolean helpers
- Constants: `REQUIRED_FILES`, `OPTIONAL_FILES`, `VAGUE_TERMS`, `P0_REQUIRED_SECTIONS`, `EXPECTED_CHAPTERS`, `OPTIONAL_CHAPTERS`, `TRACEABILITY_PATTERNS`
- Internal helpers: prefix with `_` (e.g. `_make_result`)

### Error handling
- Validator is a CLI tool — no exceptions raised to caller; errors print to stdout
- File I/O uses `Path.read_text(encoding="utf-8")`
- Missing files: skip gracefully in `run_validation`, already handled by `check_file_structure`

### Output conventions
- Console output uses `✓ PASS`, `⚠ WARN`, `✗ FAIL` prefixes
- Section headers via `print_header()` and `print_section()` helpers
- Issue previews truncated to 80 chars; lists truncated to 5 items with `... 共N个` suffix

---

## Code Style — Tests

### Import pattern for unit tests
The validator filename has a hyphen (`quality-validator.py`), so use `importlib`:

```python
import importlib.util
from pathlib import Path

def _load_validator():
    p = (
        Path(__file__).parent.parent.parent
        / "rana"
        / "scripts"
        / "quality-validator.py"
    )
    spec = importlib.util.spec_from_file_location("quality_validator", p)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod

_v = _load_validator()
fn_under_test = _v.fn_under_test
```

### E2E test pattern
```python
import subprocess, sys
from pathlib import Path

def run_validator(scenario_dir):
    result = subprocess.run(
        [sys.executable, str(VALIDATOR), str(scenario_dir)],
        capture_output=True, text=True,
    )
    return result.returncode, result.stdout
```

### Test naming
- Unit: `test_<function>_<scenario>` e.g. `test_has_traceability_prd`
- E2E: `test_scenario_<fixture_name>` e.g. `test_scenario_a_normal`

### Assertions
- Use `assert x == y, f"message with {context}"` for E2E assertions
- Prefer specific assertions: `assert "需求拆解" in result["missing"]` over `assert len(...) > 0`

### Table header trap
In unit tests that construct markdown tables, use a first cell that is in `HEADER_KEYWORDS` (e.g. `"字段"`, `"内容"`) so the header row is skipped by the validator. Using `"功能"` as header first cell will cause it to be counted as a data row.

---

## Validator Key Behaviors to Know (v0.4.0)

### Traceability check threshold
Pass rate ≥ 80% required. `pass_rate = (checked - issues) / checked`. Empty document = `pass_rate = 1.0` (vacuously passes).

### Files checked/skipped for traceability
- `final-analysis.md` — fully checked (8 chapters + summary)
- `change-log.md` — skipped (process document)
- `quality-report.md` — skipped (AI evaluation)
- `quick-analysis.md` — skipped (Quick Mode, not full deliverable)

### Sections skipped in final-analysis.md traceability
- "总结" — conclusions, already traced in body
- "待澄清项/待澄清" — AI-generated questions, no source needed
- "八、各角色重点关注" — P2 optional, not required to trace

### P0 section check (replaces 需求分析卡)
Checks 8 P0 required sections exist in final-analysis.md via regex: `section_num.*section_name`. Missing any → FAIL.

P0 sections: 1.1 需求概述, 1.2 需求来源, 2.1 核心用户画像, 2.3 场景与用户目标, 3.1 现状与根因拆解, 4.1 业务北极星, 6.1 MVP, 6.3 需求全清单与优先级分级

### VAGUE_TERMS — intentionally excluded words
`"相关"`, `"一般"`, `"通常"`, `"正常情况下"` were removed due to high false-positive rate. Do not re-add without updating the comment block in the config section.

---

## Development Workflow

1. Edit `rana/` source
2. Run `python3 -m pytest tests/ -v` — must stay 70/70 green
3. Run validator manually on relevant fixture to confirm behavior
4. Sync install copy: `cp -r rana/. ~/.agents/skills/rana/`
5. Commit source + tests together

Design docs → `docs/superpowers/specs/YYYY-MM-DD-<topic>-design.md`
Implementation plans → `docs/superpowers/plans/YYYY-MM-DD-<topic>.md`
Version roadmap → `docs/roadmap.md`

---

## SKILL.md Key Locations (v0.4.0)

| Section | Lines | Notes |
|---------|-------|-------|
| 互动风格 + 工作原则 + 批判反驳概要 | ~30-90 | 新增 v0.4.0：人设、C1-C7 触发条件 |
| 双模式概览（mermaid） | ~95-145 | Quick/Full 流程图 + 模式选择逻辑 |
| 输出目录约定 | ~148-165 | `_temp/` 和 `<需求名称>/<YYYY-MM-DD>/` 目录结构 |
| Quick Mode 流程 | ~195-215 | 四步：共识单→讨论→提问清单→升级提示 |
| Full Mode 三阶段概览 | ~218-240 | 诊断层→方案层→提炼层，引用 references |
| 注意事项 | ~245-250 | Quick Mode 不适用 P0 缺口规则 |

**注意**：SKILL.md v0.4.0 为 Clean Break 重写（~300行），旧 v0.3.3 的章节模板、四阶段推进规则等已移至 references/ 或归档。

---

## OpenProse 工作流

### rana-workflow.prose

自动化 PDF → 需求分析流程：

**位置**：`~/.openclaw/skills/rana-workflow.prose`

**使用**：

```
/prose run ~/.openclaw/skills/rana-workflow.prose --prd-path spec.pdf
/prose run ~/.openclaw/skills/rana-workflow.prose --prd-path spec.pdf --requirement-name "需求名称"
```

**依赖**（同级目录）：
- `mineru-pipeline` - PDF 解析
- `rana` - UX 需求分析

**技术原理**：
- `import "name" from "./dir"` 相对路径导入同级 skills
- `agent.skills: ["name"]` 注入 skill instructions 到 subagent
