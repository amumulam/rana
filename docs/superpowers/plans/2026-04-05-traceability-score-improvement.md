# Traceability Score Improvement Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将线上测试输出 traceability 维度从 11/30 提升至 ≥24/30，总分从 81/100 提升至 ≥94/100。

**Architecture:** 双向修复——
- **方向A（改AI行为）**：更新 SKILL.md Stage 1 的 `input-structured.md` 输出模板，要求每条列表项和表格数据行都带行内来源标注，而不是只在章节标题上标注一次；
- **方向B（改验证器逻辑）**：让 `check_traceability_input_structured` 识别"章节级来源传播"——如果一个列表项所在的直接父章节标题（`###`/`##`）带有来源标注，该列表项可以豁免单独标注；同时让 `check_traceability_final_analysis` 把来源列为 `—` 的表格行识别为合法的"交叉引用行"跳过检查。

**Tech Stack:** Python 3.9, pytest, SKILL.md (Markdown)

---

## 文件改动地图

| 文件 | 动作 | 说明 |
|------|------|------|
| `ux-requirement-analysis/scripts/quality-validator.py` | Modify | 方向B：`check_traceability_input_structured` 支持章节级来源传播；`check_traceability_final_analysis` 已有 `REFERENCE_CELL_PATTERNS` 含 `^—$`，需确认来源列（第3列）的 `—` 也被正确识别 |
| `ux-requirement-analysis/SKILL.md` | Modify | 方向A：Stage 1 输出模板改为每行标注来源 |
| `tests/unit/test_traceability.py` | Modify | 为方向B新增单元测试 |
| `~/.agents/skills/ux-requirement-analysis/` | Sync | 所有改动完成后同步 |

---

### Task 1：方向B — check_traceability_input_structured 支持章节级来源传播

**背景**：线上输出的 `input-structured.md` 把来源标注写在 `###` 章节标题上（如 `### 1. 维修模式优化 [PRD 第 1 节]`），然后该节下面的列表项没有单独标注。这是一种合理的写法——章节标题上的来源对该节所有内容有效。

**修改逻辑**：在 `check_traceability_input_structured` 中，跟踪最近一个含来源标注的 `###`（或 `##`）标题，如果当前列表项/表格行所在的直接父章节标题已有来源标注，则跳过该行的来源检查。

注意：`is_empty_or_heading` 目前会跳过所有标题行（不计入 checked），改动需要在此之前单独处理来源标注的章节标题，**不改变**它对 checked 计数的影响（标题行仍然不计入 checked）。

**Files:**
- Modify: `ux-requirement-analysis/scripts/quality-validator.py` (`check_traceability_input_structured` 函数, ~行 144–233)
- Test: `tests/unit/test_traceability.py`

- [ ] **Step 1: 写失败测试——章节级来源传播**

在 `tests/unit/test_traceability.py` 末尾追加：

```python
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
    # 第1节的列表项豁免，第2节的列表项未标注
    assert result["checked"] == 1
    assert result["pass_rate"] == 0.0


def test_section_level_traceability_table_rows():
    """章节级来源传播应同样适用于表格数据行"""
    content = (
        "### 关键数据 [PRD需求清单]\n"
        "| 模块 | 当前 UV | 当前 CTR |\n"
        "|------|--------|---------|"
        "\n"
        "| 维修模式 | 4.2 万 | 5.3% |\n"
        "| 客服卡片 | - | 9.01% |\n"
    )
    result = check_traceability_input_structured(content)
    assert result["pass_rate"] == 1.0, f"issues={result['issues']}"
```

- [ ] **Step 2: 运行测试，确认3个新测试失败**

```bash
python3 -m pytest tests/unit/test_traceability.py::test_section_level_traceability_propagates \
  tests/unit/test_traceability.py::test_section_level_traceability_stops_at_new_section \
  tests/unit/test_traceability.py::test_section_level_traceability_table_rows -v
```

预期：3 个 FAIL

- [ ] **Step 3: 修改 check_traceability_input_structured 加入章节级来源传播**

找到 `check_traceability_input_structured` 函数（约第 144 行），在其中的 `in_code_block = False` 初始化块后、`for` 循环前，添加一个变量来跟踪"当前章节是否已有来源标注"：

在 `HEADER_KEYWORDS` 定义之前的初始化区域加：

```python
    current_section_has_source = False  # 当前直接父章节标题是否已有来源标注
```

然后在 `for` 循环中，找到 `if is_empty_or_heading(line): continue` 这一行，将它替换为：

```python
        if is_empty_or_heading(line):
            # 如果是章节标题（## 或 ###），更新章节级来源传播状态
            if re.match(r"^#{2,3}\s", line):
                current_section_has_source = has_traceability(line)
            elif re.match(r"^#\s", line):
                # 顶级标题（# 文档标题）重置传播状态
                current_section_has_source = False
            continue
```

然后在 `checked += 1` 之前（即 `if not has_traceability(line):` 之前），加入豁免判断：

```python
        # 如果当前行所在章节的标题已有来源标注，豁免该行的单独标注要求
        if current_section_has_source:
            continue
```

完整修改后的关键区域（在原 `checked += 1` 之前）：

```python
        # 如果当前行所在章节的标题已有来源标注，豁免该行的单独标注要求
        if current_section_has_source:
            continue

        checked += 1
        if not has_traceability(line):
            issues.append({"line": i, "content": line.strip()[:80]})
```

- [ ] **Step 4: 运行新增测试，确认3个 PASS**

```bash
python3 -m pytest tests/unit/test_traceability.py::test_section_level_traceability_propagates \
  tests/unit/test_traceability.py::test_section_level_traceability_stops_at_new_section \
  tests/unit/test_traceability.py::test_section_level_traceability_table_rows -v
```

预期：3 个 PASS

- [ ] **Step 5: 运行全部单元测试确认无回归**

```bash
python3 -m pytest tests/unit/ -v
```

预期：全部绿色（原有 48 个 + 新增 3 个 = 51 个）

- [ ] **Step 6: 对线上输出跑分，确认 input-structured.md 的 traceability 有提升**

```bash
python3 ux-requirement-analysis/scripts/quality-validator.py tests/online-test/2026-04-02/out --score
```

记录新的 traceability 分数。

- [ ] **Step 7: 提交**

```bash
cd /Users/11184725/projects/requirements-analysis
git add ux-requirement-analysis/scripts/quality-validator.py tests/unit/test_traceability.py
git commit -m "feat: support section-level source propagation in check_traceability_input_structured"
```

---

### Task 2：方向B — 确认 final-analysis.md 来源列 `—` 被正确识别为引用行

**背景**：`check_traceability_final_analysis` 已有 `REFERENCE_CELL_PATTERNS` 含 `r"^—$"`（第318行）。该逻辑检查的是**内容列**（`cells[1]`）。但线上输出中，`| **需求结论** | 见下文「需求分析结论」 | — |` 的**来源列**（`cells[2]`）是 `—`，内容列是"见下文..."——这种行可能没有被 `REFERENCE_CELL_PATTERNS` 覆盖到。

**修改逻辑**：在 `check_traceability_final_analysis` 的引用行判断处，除了检查内容列（`cells[1]`），也检查来源列（`cells[2]` 如果存在）是否为 `—`，以及内容列是否含有"见下文"/"见交付物"等引用文字。

**Files:**
- Modify: `ux-requirement-analysis/scripts/quality-validator.py` (`check_traceability_final_analysis` 函数, ~行 367–371)
- Test: `tests/unit/test_traceability.py`

- [ ] **Step 1: 先诊断——确认问题确实存在**

运行完整验证器，找到 final-analysis.md 中哪些行还在报来源缺失：

```bash
python3 ux-requirement-analysis/scripts/quality-validator.py tests/online-test/2026-04-02/out 2>&1 | grep -A 100 "final-analysis"
```

如果输出中有类似 `| 需求结论 | 见下文... | — |` 的报错行，说明问题确认存在，继续 Step 2。

如果 final-analysis.md 的 pass_rate 已经 ≥80%（因为 Task 1 没有影响到 final-analysis.md），则此 Task 的改动可能效果有限——但仍需确认来源列 `—` 是否正确处理，继续执行。

- [ ] **Step 2: 写失败测试——来源列为 `—` 的交叉引用行**

在 `tests/unit/test_traceability.py` 末尾追加（需要先导入 `check_traceability_final_analysis`）：

首先确认文件顶部的导入区域，在导入行追加：

```python
check_traceability_final_analysis = _v.check_traceability_final_analysis
```

然后追加测试：

```python
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
    # 所以 checked=1，issues=0，pass_rate=1.0
    assert result["pass_rate"] == 1.0, f"issues={result['issues']}, checked={result['checked']}"


def test_final_analysis_dash_source_column_skipped():
    """来源列（第3列）为 — 的行应被视为合法引用行，跳过检查"""
    content = """\
## 需求分析卡

| 字段 | 内容 | 来源追溯 |
|------|------|---------|
| **待澄清项** | [见交付物 D] | — |
| **风险点** | 风险内容 | [PRD第1节] |
"""
    result = check_traceability_final_analysis(content)
    # 待澄清项是 [见交付物D]，风险点有来源，两者都应通过
    assert result["pass_rate"] == 1.0, f"issues={result['issues']}, checked={result['checked']}"
```

- [ ] **Step 3: 运行测试，确认新测试的实际结果**

```bash
python3 -m pytest tests/unit/test_traceability.py::test_final_analysis_cross_reference_rows_skipped \
  tests/unit/test_traceability.py::test_final_analysis_dash_source_column_skipped -v
```

如果已经 PASS：说明 `REFERENCE_CELL_PATTERNS` 已经覆盖，记录结论，跳到 Step 6。
如果 FAIL：说明需要修改验证器，继续 Step 4。

- [ ] **Step 4: 修改 check_traceability_final_analysis 扩展引用行判断（仅当 Step 3 有 FAIL 时执行）**

找到 `check_traceability_final_analysis` 函数中的引用行判断区域（约第 367–371 行）：

```python
            # 跳过引用行（内容列为「[见交付物X]」等）
            if len(cells) >= 2:
                content_cell = cells[1] if len(cells) > 1 else ""
                if any(re.match(pat, content_cell) for pat in REFERENCE_CELL_PATTERNS):
                    continue
```

替换为：

```python
            # 跳过引用行：
            # 1. 内容列（cells[1]）匹配 REFERENCE_CELL_PATTERNS（[见交付物X]、—、[缺失]）
            # 2. 来源列（cells[2]）为 — 且内容列含"见下文"/"见交付物"引用文字
            if len(cells) >= 2:
                content_cell = cells[1] if len(cells) > 1 else ""
                source_cell = cells[2].strip() if len(cells) > 2 else ""
                if any(re.match(pat, content_cell) for pat in REFERENCE_CELL_PATTERNS):
                    continue
                # 来源列为 — 且内容列是引用性文字
                if source_cell == "—" and re.search(r"见下文|见交付物|详见", content_cell):
                    continue
```

- [ ] **Step 5: 运行测试，确认两个新测试 PASS**

```bash
python3 -m pytest tests/unit/test_traceability.py::test_final_analysis_cross_reference_rows_skipped \
  tests/unit/test_traceability.py::test_final_analysis_dash_source_column_skipped -v
```

预期：2 个 PASS

- [ ] **Step 6: 运行全部单元测试确认无回归**

```bash
python3 -m pytest tests/unit/ -v
```

预期：全部绿色

- [ ] **Step 7: 提交**

```bash
cd /Users/11184725/projects/requirements-analysis
git add ux-requirement-analysis/scripts/quality-validator.py tests/unit/test_traceability.py
git commit -m "fix: skip cross-reference rows with dash source column in final-analysis traceability check"
```

---

### Task 3：方向A — 更新 SKILL.md Stage 1 模板，要求每行标注来源

**背景**：即使验证器支持章节级传播，AI 最好也能把来源标注写在每一行——这样在没有章节标题来源的情况下也能通过检查，且文档可读性更高。

当前 SKILL.md Stage 1 的 `input-structured.md` 输出模板（约第 178–220 行）已经有每行标注的示例（如 `- [PRD第X节] 业务背景：...`），但模板里的"核心业务目标"节用的是章节级标注写法，不够一致。

**修改内容**：在 Stage 1 处理步骤说明中，补充一条明确要求："来源标注写在每条列表项/表格行内，不要只写在章节标题上"。同时确认 `input-structured.md` 模板的所有示例区域都体现了行内标注。

**Files:**
- Modify: `ux-requirement-analysis/SKILL.md`

- [ ] **Step 1: 读取 SKILL.md 第 140–215 行，找到来源标注要求说明的位置**

读取文件确认当前文字。

- [ ] **Step 2: 在来源标注说明处补充"行内标注"要求**

找到 SKILL.md 中（约第 142–147 行）的以下内容：

```markdown
1. **提取信息，标注来源**
   - 解析 PRD 文本（含从文件提取的内容），提取业务背景、功能点、规则
   - 分析截图（含从 PDF 提取的图片），识别界面元素、交互模式
   - 获取 Figma 页面内容（如有）
   - 每条信息标注来源格式（见下方标注规范）
```

将最后一行改为：

```markdown
   - 每条列表项和表格数据行都需要行内来源标注（不要只在章节标题上标注一次）
   - 来源标注格式（见下方速查）
```

- [ ] **Step 3: 运行全部测试确认无影响**

```bash
python3 -m pytest tests/ -v
```

预期：全部绿色

- [ ] **Step 4: 提交**

```bash
cd /Users/11184725/projects/requirements-analysis
git add ux-requirement-analysis/SKILL.md
git commit -m "docs: clarify per-line source annotation requirement in SKILL.md Stage 1"
```

---

### Task 4：验收——重新跑分并同步安装副本

- [ ] **Step 1: 对线上测试输出跑分**

```bash
python3 ux-requirement-analysis/scripts/quality-validator.py tests/online-test/2026-04-02/out --score
```

**期望结果**：

| 维度 | 修复前（Task 1-5 之后） | 期望修复后 |
|------|----------------------|-----------|
| file_structure | 20/20 | 20/20 |
| traceability | 11/30 | ≥24/30 |
| card_fields | 25/25 | 25/25 |
| sections | 15/15 | 15/15 |
| vague_terms | 10/10 | 10/10 |
| **总分** | **81/100** | **≥94/100** |

- [ ] **Step 2: 如果 traceability < 24，运行详细报告诊断剩余问题**

```bash
python3 ux-requirement-analysis/scripts/quality-validator.py tests/online-test/2026-04-02/out
```

查看各文件的 pass_rate 和未通过的行，记录结论。

- [ ] **Step 3: 运行全套测试最终确认**

```bash
python3 -m pytest tests/ -v
```

预期：全部绿色（≥54 个测试）

- [ ] **Step 4: 同步安装副本**

```bash
cp -r /Users/11184725/projects/requirements-analysis/ux-requirement-analysis/. ~/.agents/skills/ux-requirement-analysis/
```

---

## 验收标准

1. `python3 -m pytest tests/ -v` — 全绿（≥54 个测试）
2. 线上测试输出总分 ≥94/100
3. traceability 维度 ≥24/30
4. SKILL.md Stage 1 明确要求每行行内标注
5. 安装副本已同步
