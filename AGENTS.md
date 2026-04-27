# AGENTS.md — UX Requirement Analysis

This project is an **OpenCode Skill** that helps UX designers turn PM PRDs into structured requirement analysis documents. The core deliverable is `rana/` — a skill directory installable into `~/.agents/skills/`.

**GitHub:** https://github.com/amumulam/rana
**GitLab:** https://gitlab.vmic.xyz/ued-ai-lab/rana
**Wiki:** https://gitlab.vmic.xyz/ued-ai-lab/rana/-/wikis/home — 面向 UX 设计师的 Mattermost 使用指南

---

## Remote Repositories

| Remote | URL | Purpose |
|--------|-----|---------|
| `origin` | `https://github.com/amumulam/rana.git` | Public mirror |
| `gitlab` | `git@gitlab.vmic.xyz:ued-ai-lab/rana.git` | Internal (primary) |

Push to both: `git push origin main && git push gitlab main`

---

## Deployment Environments

| Environment | Platform | Skill install path | Notes |
|-------------|----------|--------------------|-------|
| Local (macOS) | BlueCode / OpenCode | `~/.agents/skills/rana/` | Dev machine |
| Server | OpenClaw | `~/.openclaw/skills/rana/` | Production environment used for real online tests |

**Important**: When reviewing online test outputs, the validator path `~/.openclaw/skills/rana/scripts/quality-validator.py` is the **real, correct path** on the server. Do NOT flag this as an error or "forged result".

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

**本项目遵循 `skill-creat-guideline/` 目录下的指南进行 skill 开发。**

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

如需重新生成 fixture 输出，删除对应 `tests/fixtures/file-input/outputs/` 子目录后重跑测试即可。

### SKILL.md accuracy note

`SKILL.md` currently states: _"直接将 .pdf 文件上传给模型即可。模型原生支持多模态读取"_

This is accurate **only** when the skill is used via a web UI that supports file attachments. When used via CLI agents (OpenCode, BlueCode), the PDF must be pre-processed. The SKILL.md user-facing instructions do not need to change (they describe the UX designer's experience, not the technical pipeline), but any agent doing integration testing must be aware of this gap.

---

## Project Structure

```
rana/  (repo root, local path: requirements-analysis/)
├── rana/         # Skill source (canonical copy)
│   ├── SKILL.md                     # Skill definition — dual-mode routing + shared bootstrap (~240 lines, v0.4.1)
│   ├── scripts/
│   │   └── quality-validator.py     # CLI quality gate checker (v0.4.0, 3 required files + P0 sections)
│   ├── references/
│   │   ├── workflow-quick-mode-guideline.md   # Quick Mode 全流程 + 四维度框架 + 边界场景
│   │   ├── workflow-full-mode-guideline.md    # Full Mode 串联流程 + 质量验证 + 多功能处理
│   │   ├── collaboration-protocol.md          # 批判反驳与协作对话规范（Quick/Full 通用）
│   │   ├── p0-gates.md               # P0 缺口规则
│   │   ├── stage-1-diagnosis.md      # 诊断层详细流程
│   │   ├── stage-2-solution.md       # 方案层详细流程
│   │   ├── stage-3-refine.md         # 提炼层详细流程
│   │   ├── analysis-methods.md       # HMW/MVP/五问法/X-Y Problem
│   │   └── quality-validator.md      # Validator 行为详细说明
│   ├── assets/
│   │   ├── analysis-template-full.md  # Full Mode 输出模板（8章+总结）
│   │   └── analysis-template-quick.md # Quick Mode 快速分析模板
│   └── config.yaml                    # file_parser 配置
├── scripts/
│   └── sync-wiki.sh                 # 手动同步 wiki/ 到 GitLab Wiki（CI 不可用时的备用方案）
├── tests/
│   ├── unit/                        # pytest unit tests for validator functions
│   ├── e2e/                         # E2E tests via subprocess CLI calls
│   ├── integration/                 # Integration tests with pdfplumber
│   └── fixtures/                    # Test fixtures (validator input/output)
│       ├── test-a-normal/           # Normal case → PASS
│       ├── test-b-edge/             # Minimal input → FAIL (missing field)
│       ├── test-c-multi-feature/    # Multi-feature PRD → PASS
│       ├── test-d-conflict/         # Conflict in change-log → PASS
│       ├── test-e-traceability-fail/# Low traceability rate → FAIL
│       ├── test-f-screenshot-input/  # Screenshot input → PASS
│       └── file-input/              # Integration test fixtures (PDF/XLSX)
├── wiki/                            # GitLab Wiki 源文件（push 后自动同步）
│   ├── Home.md                      # Wiki 首页
│   └── assets/                      # Wiki 图片资源
├── workflow-diagram/                 # 架构图
│   ├── rana-workflow-v0.4.html       # v0.4.1 架构图（当前）
│   └── rana-workflow-v0.3.html       # v0.3 架构图（旧版）
├── .gitlab-ci.yml                   # CI/CD — auto-release + wiki sync
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

---

## Wiki Sync

项目仓库中的 `wiki/` 目录会通过 CI/CD 自动同步到 GitLab Wiki。

**手动同步**（CI 不可用时）：
```bash
bash scripts/sync-wiki.sh wiki
```

**自动同步**：修改 `wiki/` 目录并 push 到 `gitlab/main` 后，`.gitlab-ci.yml` 中的 `sync-wiki` job 会自动执行同步。

需要 GitLab CI Variable `SSH_PRIVATE_KEY` 配置（Settings → CI/CD → Variables）。

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
集成测试会自动用 pdfplumber 提取 `tests/fixtures/file-input/fixtures/` 中的 PDF，
生成 `tests/fixtures/file-input/outputs/` 下的输出文件，然后验证其结构。
fixture 文件不存在时自动跳过对应场景，不视为失败。

### Run the validator manually
```bash
python3 rana/scripts/quality-validator.py tests/fixtures/test-a-normal
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

## Development & Project Management Workflow

### 核心原则

- **Plane 是唯一看板**：只在这里看"接下来做什么"，不维护 GitLab Issues/Milestones
- **Worktree 是唯一开发环境**：多 feature 并行互不干扰，不用 stash 或来回 checkout
- **Conventional Commits 是唯一记录**：靠语义化前缀自动生成 Changelog，不关联 Issue ID
- **Tag 是唯一发令枪**：打 Tag 即发布，CI 自动打包 + Release
- **双 remote 同步**：`origin` (GitHub 公开镜像) + `gitlab` (内网主力)

---

### 第一阶段：规划（Plane.so）

1. 在 Plane UEDAILAB 项目（ID: `974c1f39-00b3-4305-9ee5-a5d3c7166294`）建 Work Item
   - 标题用 Conventional Commits 格式：`feat: xxx` / `fix: xxx`
   - 状态改为 In Progress
   - 放入当前版本 Cycle
2. 开始工作时看 Plane，确定做哪个卡片

**不在 GitLab 平面维护任何 Issue / Milestone / Board。**

---

### 第二阶段：开发（Local + Worktree）

```bash
# 1. 开 Worktree
git worktree add -b feat/xxx .worktrees/feat-xxx

# 2. 编码（在独立文件夹，主项目停在 main 不受影响）

# 3. 提交（Conventional Commits）
git commit -m "feat: xxx"
# 前缀：feat / fix / docs / style / refactor / test / chore / ci

# 4. 一键推送 + MR + 合并
gmr
```

**gmr 做了什么：**
- push origin + gitlab
- glab mr create（squash + remove-source-branch）
- glab mr merge（squash 合入 main）
- checkout main + pull 双 remote（自动 stash 处理本地未提交文件）
- 删除 feat branch + worktree

---

### 第三阶段：状态更新（Plane.so）

把 Work Item 状态改为 Done。零 ID 搬运，零同步脚本。

**Done 时必须在 Work Item 下写 comment**，记录过程、结论和关联代码。

comment 使用 HTML（Plane 不渲染 markdown），格式如下：

```
<strong>[动作标签] 标题</strong>

<strong>关联：</strong><a href="GitLab commit 链接">short_hash</a> commit message

<strong>描述：</strong>正文内容

<strong>变更内容：</strong>
- item1
- item2
```

动作标签：
- `[完成]` — Done 时记录过程和结论
- `[更新]` — 开发中的进展同步
- `[阻塞]` — 遇到阻碍需要讨论

规则：
- `<strong>` 作标题，`<code>` 作行内代码，`<br>` 换行，`<a href>` 作链接
- 不用 `<h1>` `<h2>` `<h3>` `<ul>` `<li>` 等标签（Plane 渲染异常）
- commit 关联必须附带 GitLab commit 链接
- 简洁不啰嗦

---

### 第四阶段：发布（Tag → CI 自动化）

```bash
# Cycle 内所有卡片 Done → 打 Tag
git tag v0.x.x
git push origin v0.x.x && git push gitlab v0.x.x
```

CI 自动执行：
- **SAST + Secret Detection**：安全扫描
- **auto-release**：`generate-changelog.sh` 提取 feat/fix/docs → zip 打包 → curl API 创建 GitLab Release
- **sync-wiki**：wiki/ 变更自动同步

Release description 自动按分类格式化：
```
## v0.x.x
Changes since v0.y.y:
### ✨ Features
• abc123 feat: xxx
### 🐛 Fixes
• def567 fix: yyy
```

---

### 速查表

| 动作 | 命令 |
|------|------|
| 规划 | Plane 建 Work Item → 放入 Cycle |
| 开始做 | `git worktree add -b feat/xxx .worktrees/feat-xxx` |
| 写代码 | IDE 在独立文件夹开发 |
| 保存进度 | `git commit -m "feat: xxx"` |
| 合入 main | `gmr` |
| 标记完成 | Plane 拖卡片到 Done |
| 发布 | `git tag v0.x.x && git push origin v0.x.x && git push gitlab v0.x.x` |
| Skill 安装同步 | `cp -r rana/. ~/.agents/skills/rana/` |

---

### 测试 & 验证

```bash
python3 -m pytest tests/ -v       # 所有测试
python3 -m pytest tests/unit/ -v  # 单元
python3 -m pytest tests/e2e/ -v   # E2E
ruff check rana/scripts/          # Lint
```

---

### 待后续优化

| 项 | 优先级 |
|-----|--------|
| CI test stage（pytest） | 中 |
| Mattermost 通知 | 低 |
| Skill 安装同步自动化 | 低 |

---

### gmr 踩坑记录

1. **worktree 与 main 同文件冲突**：在 worktree commit 并 push 后，main 目录如有同文件未提交改动，`git pull` 会冲突。gmr 里的 `git stash -u` 只能解决 main 侧的两个 remote 同步冲突，但 main 与 worktree 之间的文件冲突要靠自律——**不要在 main 上修改 worktree 正在改的文件**。
2. **glab mr create 的 --title**：commit message 含中文引号或特殊字符时，`--title` 解析可能异常，改用 `--fill` 让 glab 自动从 commits 生成为最稳。
3. **glab squash flag**：`--squash` 是 `-s`，不是 `--squash` 或 `--squash-merge`。
4. **glab mr merge 时机**：`glab mr merge` 必须在 main 目录下执行（不能在 worktree 目录下），否则 pull 后 worktree 的 HEAD 不会更新。

---

## SKILL.md Key Locations (v0.4.1)

| Section | Lines | Notes |
|---------|-------|-------|
| 互动风格 + 工作原则 + 批判反驳概要 | ~30-75 | 人设、C1-C7 触发条件 |
| 双模式概览（mermaid） | ~77-125 | Quick/Full 流程图 + 模式选择逻辑 |
| 输出目录约定 | ~127-147 | `_temp/` 和 `<需求名称>/<YYYY-MM-DD>/` 目录结构 |
| Quick Mode | ~211-218 | 路由行 → workflow-quick-mode-guideline.md |
| Full Mode | ~217-222 | 路由行 → workflow-full-mode-guideline.md |
| Gotchas | ~223-230 | 知识库、PDF、多次分析 |
| 引用文件 | ~231-241 | 所有 references 和 assets 清单 |

**注意**：SKILL.md v0.4.1 为精简路由版（~240行），Full Mode 内联流程已移至 workflow-full-mode-guideline.md，Quick Mode 内联流程已移至 workflow-quick-mode-guideline.md。

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
