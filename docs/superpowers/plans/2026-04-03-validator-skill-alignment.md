# Validator-Skill Alignment Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复验证器与 SKILL.md 输出格式不一致导致的低分问题（线上测试 47/100），将分数提升至 ≥85/100。

**Architecture:** 双向修复——扩展验证器 `TRACEABILITY_PATTERNS` 兼容 AI 实际输出的合法变体；同时在 SKILL.md / traceability-guide.md 中明确列出规范格式，减少 AI 自由发挥；另外修复 `check_card_fields` 同时识别 `#` 和 `##` 级别的需求分析卡标题。

**Tech Stack:** Python 3.9, pytest, SKILL.md (Markdown)

---

## 文件改动地图

| 文件 | 动作 | 说明 |
|------|------|------|
| `ux-requirement-analysis/scripts/quality-validator.py` | Modify | 扩展 `TRACEABILITY_PATTERNS`；修复 `check_card_fields` 标题层级识别 |
| `ux-requirement-analysis/references/traceability-guide.md` | Modify | 补充"同义/变体格式"对照表，让 AI 知道哪些写法验证器能识别 |
| `ux-requirement-analysis/SKILL.md` | Modify | Stage 1/3/5 来源标注规范中显式列出合法格式列表（含变体） |
| `tests/unit/test_traceability.py` | Modify | 新增变体格式测试（`[用户确认]`、`[PRD 第X节]` 有空格） |
| `tests/unit/test_card_fields.py` | Modify | 新增 `#` 级别标题的卡片识别测试 |
| `~/.agents/skills/ux-requirement-analysis/` | Sync | 每次改完源文件后同步安装副本 |

---

### Task 1：扩展 TRACEABILITY_PATTERNS 兼容常见变体

**目标**：让以下 AI 实际输出的合法格式被验证器识别：
- `[PRD 第X节]`（有空格）
- `[PRD 需求清单]`、`[PRD 封面]`（非数字章节引用）
- `[用户确认]`、`[用户确认 HH:MM]`（用户口头确认）
- `[分析创建]`（系统生成内容，等价于无需来源的占位）
- `[分析推断]`（裸推断，和 `[推断：...]` 同义）

**Files:**
- Modify: `ux-requirement-analysis/scripts/quality-validator.py` (lines 30–46)
- Test: `tests/unit/test_traceability.py`

- [ ] **Step 1: 写失败测试——验证新变体当前不被识别**

在 `tests/unit/test_traceability.py` 末尾追加：

```python
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
```

- [ ] **Step 2: 运行测试，确认全部失败**

```bash
python3 -m pytest tests/unit/test_traceability.py::test_has_traceability_prd_with_space \
  tests/unit/test_traceability.py::test_has_traceability_prd_named_section \
  tests/unit/test_traceability.py::test_has_traceability_user_confirm \
  tests/unit/test_traceability.py::test_has_traceability_user_confirm_timestamp \
  tests/unit/test_traceability.py::test_has_traceability_analysis_infer \
  tests/unit/test_traceability.py::test_has_traceability_analysis_create \
  -v
```

预期：6 个 FAIL

- [ ] **Step 3: 在 quality-validator.py 中扩展 TRACEABILITY_PATTERNS**

将 `TRACEABILITY_PATTERNS` 列表（大约第 30-46 行）改为：

```python
TRACEABILITY_PATTERNS = [
    r"\[PRD[^\]]+\]",          # [PRD第X节] / [PRD 第X节] / [PRD 需求清单] 等所有 PRD 引用
    r"\[截图\d+[^\]]*\]",
    r"\[PDF第\d+页[^\]]*\]",   # PDF 文字内容引用
    r"\[PDF截图\d+[^\]]*\]",   # PDF 图片引用
    r"\[Figma[^\]]+\]",
    r"\[PM确认[^\]]*\]",
    r"\[研发确认[^\]]*\]",
    r"\[测试确认[^\]]*\]",
    r"\[业务确认[^\]]*\]",
    r"\[设计师确认[^\]]*\]",
    r"\[用户确认[^\]]*\]",     # [用户确认] / [用户确认 19:16] — 对话确认通用格式
    r"\[推断[^\]]*\]",         # [推断：依据] / [推断] 裸标注
    r"\[分析推断[^\]]*\]",     # [分析推断] — 裸推断变体
    r"\[场景还原推断[^\]]*\]",
    r"\[五问法推断[^\]]*\]",
    r"\[X-Y分析推断[^\]]*\]",
    r"\[缺失[^\]]*\]",
    r"\[口头说明[^\]]*\]",
    r"\[CHG-\d+\]",
    r"\[原始输入[^\]]*\]",
    r"\[分析创建[^\]]*\]",     # [分析创建] — 系统生成内容，无外部来源
    r"\[quality-report[^\]]*\]",
]
```

- [ ] **Step 4: 运行测试确认新增6个 PASS，原有测试保持绿色**

```bash
python3 -m pytest tests/unit/test_traceability.py -v
```

预期：全部 PASS（含原有13个 + 新增6个 = 19个）

- [ ] **Step 5: 提交**

```bash
cd /Users/11184725/projects/requirements-analysis
git add ux-requirement-analysis/scripts/quality-validator.py tests/unit/test_traceability.py
git commit -m "fix: extend TRACEABILITY_PATTERNS to accept common AI output variants"
```

---

### Task 2：修复 check_card_fields 识别 # 级别标题

**目标**：让 `check_card_fields` 同时识别 `# 交付物 A：需求分析卡` 和 `## 交付物 A：需求分析卡`。

线上输出用的是单 `#` 级别，但验证器只用 `re.match(r"^##\s", line)` 匹配，导致完全找不到卡片区域，14个字段全部缺失。

**Files:**
- Modify: `ux-requirement-analysis/scripts/quality-validator.py` (`check_card_fields` 函数, ~行 603–615)
- Test: `tests/unit/test_card_fields.py`

- [ ] **Step 1: 写失败测试——# 级别标题的卡片**

在 `tests/unit/test_card_fields.py` 末尾追加：

```python
# 与 FULL_CARD 相同内容，但改用单 # 标题
FULL_CARD_H1 = """# 交付物 A：需求分析卡

| 字段 | 内容 | 来源追溯 |
|------|------|---------|
| **需求名称** | 测试需求 | [PRD第1节] |
| **版本/迭代号** | v1.0 | [PRD第1节] |
| **需求来源** | 用户反馈 | [PRD第1节] |
| **背景说明** | 背景内容 | [PRD第1节] |
| **目标用户** | 已登录用户 | [PRD第1节] |
| **使用场景** | 日常使用 | [PRD第1节] |
| **核心问题** | 核心问题描述 | [PRD第1节] |
| **需求拆解** | [见交付物 B] | — |
| **业务规则** | 业务规则内容 | [PRD第1节] |
| **约束条件** | 约束内容 | [PRD第1节] |
| **优先级** | P0 | [PRD第1节] |
| **待澄清项** | [见交付物 D] | — |
| **风险点** | 风险内容 | [PRD第1节] |
| **需求结论** | [见交付物 E] | — |
"""


def test_card_fields_h1_title_pass():
    """# 级别标题（单井号）的需求分析卡应被正确识别"""
    result = check_card_fields(FULL_CARD_H1)
    assert result["status"] == "PASS", f"missing={result['missing']}"
    assert result["missing"] == []


def test_card_fields_h1_subsections_pass():
    """# 级别标题 + ### 子分组表格，所有字段应被合并识别"""
    content = """# 交付物 A：需求分析卡

## 基本信息

| 字段 | 内容 | 来源追溯 |
|------|------|---------|
| **需求名称** | 测试需求 | [PRD第1节] |
| **版本/迭代号** | v1.0 | [PRD第1节] |
| **需求来源** | 用户反馈 | [PRD第1节] |
| **背景说明** | 背景内容 | [PRD第1节] |

## 用户与场景

| 字段 | 内容 | 来源追溯 |
|------|------|---------|
| **目标用户** | 已登录用户 | [PRD第1节] |
| **使用场景** | 日常使用 | [PRD第1节] |
| **核心问题** | 核心问题描述 | [PRD第1节] |

## 需求内容

| 字段 | 内容 | 来源追溯 |
|------|------|---------|
| **需求拆解** | [见交付物 B] | — |
| **业务规则** | 业务规则内容 | [PRD第1节] |
| **约束条件** | 约束内容 | [PRD第1节] |
| **优先级** | P0 | [PRD第1节] |

## 风险与待确认

| 字段 | 内容 | 来源追溯 |
|------|------|---------|
| **待澄清项** | [见交付物 D] | — |
| **风险点** | 风险内容 | [PRD第1节] |

## 结论

| 字段 | 内容 | 来源追溯 |
|------|------|---------|
| **需求结论** | [见交付物 E] | — |

# 交付物 B：需求拆解清单
"""
    result = check_card_fields(content)
    assert result["status"] == "PASS", f"missing={result['missing']}"
    assert result["missing"] == []
```

- [ ] **Step 2: 运行测试，确认两个新测试失败**

```bash
python3 -m pytest tests/unit/test_card_fields.py::test_card_fields_h1_title_pass \
  tests/unit/test_card_fields.py::test_card_fields_h1_subsections_pass -v
```

预期：2 个 FAIL

- [ ] **Step 3: 修改 check_card_fields 支持 # 和 ## 两级标题**

在 `quality-validator.py` 的 `check_card_fields` 函数中，找到行：

```python
    CARD_SECTION_KEYWORDS = ["需求分析卡", "交付物 A", "交付物A"]

    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        if re.match(r"^##\s", line):
            heading_text = line.strip()
            if any(kw in heading_text for kw in CARD_SECTION_KEYWORDS):
                in_card_section = True
            elif in_card_section:
                break
            continue

        if re.match(r"^###", line):
            continue
```

替换为：

```python
    CARD_SECTION_KEYWORDS = ["需求分析卡", "交付物 A", "交付物A"]

    # 记录进入卡片区域时的标题级别（# 或 ##），以便遇到同级或更高标题时退出
    card_heading_level = None

    for line in lines:
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # 检查标题行（# 或 ## 或 ### 等）
        heading_match = re.match(r"^(#{1,6})\s", line)
        if heading_match:
            heading_level = len(heading_match.group(1))
            heading_text = line.strip()

            if not in_card_section:
                # 尚未进入卡片区域：检查是否是卡片标题（支持 # 和 ## 两级）
                if heading_level <= 2 and any(kw in heading_text for kw in CARD_SECTION_KEYWORDS):
                    in_card_section = True
                    card_heading_level = heading_level
            else:
                # 已在卡片区域内：遇到同级或更高标题时退出
                if heading_level <= card_heading_level:
                    break
            continue

        if not in_card_section:
            continue
```

注意：同时删除原来 `if re.match(r"^###", line): continue` 这一行（已被新逻辑覆盖）。

- [ ] **Step 4: 运行全部 card_fields 测试确认都通过**

```bash
python3 -m pytest tests/unit/test_card_fields.py -v
```

预期：全部 PASS（含原有5个 + 新增2个 = 7个）

- [ ] **Step 5: 运行全部单元测试确认无回归**

```bash
python3 -m pytest tests/unit/ -v
```

预期：全部绿色

- [ ] **Step 6: 提交**

```bash
cd /Users/11184725/projects/requirements-analysis
git add ux-requirement-analysis/scripts/quality-validator.py tests/unit/test_card_fields.py
git commit -m "fix: check_card_fields now recognizes both # and ## level card section headings"
```

---

### Task 3：更新 traceability-guide.md — 补充变体对照表

**目标**：让 AI 看到 traceability-guide.md 时知道哪些格式是验证器能识别的，哪些不能用。

**Files:**
- Modify: `ux-requirement-analysis/references/traceability-guide.md`

- [ ] **Step 1: 在 traceability-guide.md 末尾追加"变体对照表"小节**

在文件末尾（`## 快速参考` 之后）追加：

```markdown

---

## 验证器识别的完整格式列表

验证器通过正则匹配来源标注。只要符合以下任意一种格式，该行即视为"已标注"。

| 来源类型 | 验证器可识别的格式 | 说明 |
|---------|-----------------|------|
| PRD 章节 | `[PRD第X节]` `[PRD 第X节]` `[PRD第X.Y节]` `[PRD 需求清单]` `[PRD 封面]` | `[PRD...]` 开头均可 |
| 截图 | `[截图1]` `[截图2附注]` | 必须含数字编号 |
| PDF | `[PDF第1页]` `[PDF截图1]` | |
| Figma | `[Figma页面: 登录流程]` `[Figma组件: Card]` | `[Figma...]` 开头均可 |
| 对话确认 | `[PM确认]` `[研发确认]` `[测试确认]` `[业务确认]` `[设计师确认]` `[用户确认]` `[用户确认 19:16]` | 带时间戳也可 |
| 推断 | `[推断：依据]` `[推断]` `[分析推断]` `[场景还原推断：依据]` `[五问法推断：依据]` `[X-Y分析推断：依据]` | |
| 信息缺失 | `[缺失]` `[缺失：原因]` | |
| 口头说明 | `[口头说明：内容]` | |
| 变更记录引用 | `[CHG-1]` `[CHG-12]` | |
| 原始输入 | `[原始输入：内容]` | |
| 系统生成 | `[分析创建]` | 版本号等系统自动填入内容 |

> **不在上述列表中的格式不会被识别**，等价于"未标注"，会被计为来源缺失。
> 例如：`[analysis infer]`、`[来自PRD]`、`[设计稿]` 均不被识别。
```

- [ ] **Step 2: 验证文件可正常读取（无语法问题）**

```bash
python3 -c "from pathlib import Path; print(Path('ux-requirement-analysis/references/traceability-guide.md').read_text()[-200:])"
```

预期：打印出最后200个字符，应包含"系统生成"字样。

- [ ] **Step 3: 提交**

```bash
cd /Users/11184725/projects/requirements-analysis
git add ux-requirement-analysis/references/traceability-guide.md
git commit -m "docs: add validator-recognized format reference table to traceability guide"
```

---

### Task 4：更新 SKILL.md — 来源标注规范显式列出合法格式

**目标**：在 Stage 1 的"标注规范"说明中，直接给出验证器能识别的格式列表，减少 AI 自由发挥（如写出 `[PRD 第 1-3 节]` 带连字符这类不被识别的变体）。

**Files:**
- Modify: `ux-requirement-analysis/SKILL.md`

- [ ] **Step 1: 读取 SKILL.md 当前的 Stage 1 来源标注说明**

阅读 SKILL.md 第 142–196 行（`### 处理步骤` 部分），确认当前 Stage 1 中来源标注格式的描述位置。

- [ ] **Step 2: 在 Stage 1「标注来源格式」说明后插入规范格式速查表**

找到 SKILL.md 中以下内容（约第 146 行附近）：

```markdown
   - 每条信息标注来源格式（见下方标注规范）
```

在该行的下方插入：

```markdown

   **来源标注合法格式速查（验证器识别格式）：**
   ```
   [PRD第X节]           ← PRD章节，无空格，推荐格式
   [PRD 第X节]          ← PRD章节有空格变体，也可识别
   [PRD 需求清单]        ← PRD命名章节引用
   [截图X]              ← 界面截图，X为编号
   [PDF第X页]           ← PDF文字内容
   [PDF截图X]           ← PDF嵌入图片
   [Figma页面: 名称]    ← Figma页面引用
   [PM确认]             ← PM对话确认（首选）
   [用户确认]           ← 对话确认通用格式（含 [用户确认 HH:MM]）
   [研发确认]           ← 技术确认
   [推断：依据]          ← 有依据的推断（推荐）
   [分析推断]           ← 裸推断变体（可接受）
   [场景还原推断：依据]  ← 场景还原分析
   [缺失]               ← 信息缺失占位
   [分析创建]           ← 版本号等系统生成内容
   ```
   > **注意**：`[PRD 第 1-3 节]`（带连字符范围）、`[analysis infer]`（英文）等非标准格式不会被识别。
```

- [ ] **Step 3: 运行全套测试确认 SKILL.md 改动没有影响测试**

```bash
python3 -m pytest tests/ -v
```

预期：全部绿色（unit + e2e）

- [ ] **Step 4: 提交**

```bash
cd /Users/11184725/projects/requirements-analysis
git add ux-requirement-analysis/SKILL.md
git commit -m "docs: add traceability format quick reference to SKILL.md Stage 1"
```

---

### Task 5：对线上测试输出重新跑分，验证改动效果

**目标**：确认修复后，线上测试输出目录 `tests/online-test/2026-04-02/out/` 的得分显著提升。

**Files:**
- Read-only: `tests/online-test/2026-04-02/out/`

- [ ] **Step 1: 对线上输出重新跑分**

```bash
python3 ux-requirement-analysis/scripts/quality-validator.py tests/online-test/2026-04-02/out --score
```

记录输出的各维度分数和总分。

- [ ] **Step 2: 预期分数变化分析**

| 维度 | 修复前 | 预期修复后 | 说明 |
|------|--------|-----------|------|
| file_structure | 20 | 20 | 无变化 |
| traceability | 2 | ≥20 | 扩展 PATTERNS 后 input-structured 和 final-analysis 中的标注可被识别 |
| card_fields | 0 | 25 | # 级别标题被识别，14字段全部找到 |
| sections | 15 | 15 | 无变化 |
| vague_terms | 10 | 10 | 无变化 |
| **total** | **47** | **≥70** | 目标 ≥85 |

> 如果 traceability 仍然偏低（<20），需要进一步分析 input-structured.md / final-analysis.md 中哪些行还是不匹配。

- [ ] **Step 3: 若总分 <70，诊断剩余来源标注问题**

```bash
python3 ux-requirement-analysis/scripts/quality-validator.py tests/online-test/2026-04-02/out
```

查看详细报告，找出还有哪些行来源标注格式不被识别，决定是否继续扩展 PATTERNS 或标记为文档改进建议。

- [ ] **Step 4: 同步安装副本**

```bash
cp -r /Users/11184725/projects/requirements-analysis/ux-requirement-analysis/. ~/.agents/skills/ux-requirement-analysis/
```

- [ ] **Step 5: 运行全套测试最终确认**

```bash
python3 -m pytest tests/ -v
```

预期：全部绿色

---

## 验收标准

1. `python3 -m pytest tests/ -v` — 全绿（至少 40+7+6 = 53 个测试通过）
2. `python3 ux-requirement-analysis/scripts/quality-validator.py tests/online-test/2026-04-02/out --score` — 总分 ≥70（card_fields 得 25 分，traceability 显著提升）
3. `traceability-guide.md` 末尾有"验证器识别的完整格式列表"小节
4. `SKILL.md` Stage 1 中有来源标注合法格式速查表
5. 安装副本已同步到 `~/.agents/skills/ux-requirement-analysis/`
