# Validator Round 2 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 quality-validator.py 的两个遗留问题：删除 4 个高误报模糊词，并新增需求分析卡字段完整性检查。

**Architecture:** 全部改动在 `scripts/quality-validator.py` 单一文件内。Task 1 删除高误报词；Task 2 新增常量 + 函数 + 接入 run_validation；Task 3 验证并同步安装副本。两个 task 互相独立，可顺序执行。

**Tech Stack:** Python 3，标准库（re, sys, pathlib）

---

## 文件变更索引

| 文件 | Task | 操作 |
|------|------|------|
| `ux-requirements-analyzer/scripts/quality-validator.py` | Task 1, 2 | 修改 |
| `~/.agents/skills/ux-requirements-analyzer/` | Task 3 | 同步（cp -r） |

---

## Task 1：删除高误报模糊词

**Files:**
- Modify: `ux-requirements-analyzer/scripts/quality-validator.py:48-66`

- [ ] **Step 1.1：替换 VAGUE_TERMS 列表并加说明注释**

将第 48-66 行：

```python
# 模糊表述（不可执行词汇）
VAGUE_TERMS = [
    "适当",
    "合理",
    "友好",
    "简洁",
    "清晰",
    "尽量",
    "尽可能",
    "TBD",
    "待定",
    "暂定",
    "后续确认",
    "后续讨论",
    "相关",
    "一般",
    "通常",
    "正常情况下",
]
```

替换为：

```python
# 模糊表述（不可执行词汇）
# 注：以下词汇因高误报率已移除：
#   "相关"       — 常出现在「相关度算法」等技术术语中
#   "一般"       — 叙述性语言中误报率高
#   "通常"       — 常出现在来源标注的推断依据中（如 [推断：...通常用于...]）
#   "正常情况下"  — 分析注释背景描述会被误拦
# 这些词的漏报成本低：真正模糊的需求通常同时触发完整性维度 FAIL
VAGUE_TERMS = [
    "适当",
    "合理",
    "友好",
    "简洁",
    "清晰",
    "尽量",
    "尽可能",
    "TBD",
    "待定",
    "暂定",
    "后续确认",
    "后续讨论",
]
```

- [ ] **Step 1.2：验证 test-b-edge 模糊词误报消失**

```bash
cd /Users/11184725/projects/requirements-analysis
python3 ux-requirements-analyzer/scripts/quality-validator.py test-runs/test-b-edge/ 2>&1 | grep "模糊表述"
```

预期输出（两行，均为 PASS）：
```
  模糊表述: ✓ PASS
  模糊表述: ✓ PASS
```

- [ ] **Step 1.3：Commit**

```bash
cd /Users/11184725/projects/requirements-analysis
git add ux-requirements-analyzer/scripts/quality-validator.py
git commit -m "fix: remove 4 high false-positive vague terms from validator"
```

---

## Task 2：新增字段完整性检查

**Files:**
- Modify: `ux-requirements-analyzer/scripts/quality-validator.py`

新增位置：
- 常量 `REQUIRED_CARD_FIELDS`：在第 86 行 `EXPECTED_SECTIONS` 块之后插入
- 函数 `check_card_fields`：在 `check_sections` 函数（第 566 行）之后插入
- `run_validation` 接入：在第 688 行 `章节完整性` 输出之后插入调用

- [ ] **Step 2.1：在 EXPECTED_SECTIONS 块之后插入 REQUIRED_CARD_FIELDS 常量**

在第 86 行 `}` 之后（`EXPECTED_SECTIONS` 关闭括号后）插入：

```python

# 需求分析卡必填字段（来自 templates/requirement-card.md，共14项）
REQUIRED_CARD_FIELDS = [
    "需求名称", "版本/迭代号", "需求来源", "背景说明",
    "目标用户", "使用场景", "核心问题",
    "需求拆解", "业务规则", "约束条件", "优先级",
    "待澄清项", "风险点", "需求结论",
]
```

- [ ] **Step 2.2：在 check_sections 函数之后插入 check_card_fields 函数**

在 `check_sections` 函数结束（`return results` 行）之后，`# 报告输出` 注释块之前，插入：

```python

def check_card_fields(content: str) -> dict:
    """
    检查 final-analysis.md 中需求分析卡的字段完整性。
    定位「交付物 A：需求分析卡」或「需求分析卡」章节（## 级别），
    提取所有表格数据行的第一列作为字段名，与 REQUIRED_CARD_FIELDS 对比。

    返回：
      {
        "missing": [...],   # 必填但缺失的字段
        "extra": [...],     # 存在但不在必填列表的字段
        "found": [...],     # 实际找到的所有字段名
        "status": "PASS" | "WARN" | "FAIL"
      }
    """
    lines = content.split("\n")
    in_card_section = False
    found_fields = []
    in_code_block = False

    # 用于识别需求分析卡章节的关键词
    CARD_SECTION_KEYWORDS = ["需求分析卡", "交付物 A", "交付物A"]

    for i, line in enumerate(lines, 1):
        # 追踪代码块（跳过代码块内容）
        if line.strip().startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            continue

        # 检测 ## 级别标题
        if re.match(r"^##\s", line):
            heading_text = line.strip()
            if any(kw in heading_text for kw in CARD_SECTION_KEYWORDS):
                in_card_section = True
            elif in_card_section:
                # 遇到下一个 ## 标题，章节结束
                break
            continue

        # 跳过 ### 及更深标题（不退出章节）
        if re.match(r"^###", line):
            continue

        if not in_card_section:
            continue

        # 处理表格行
        if "|" not in line or is_table_separator(line):
            continue

        cells = table_cells(line)
        if not cells:
            continue

        # 第一列是字段名，剥除 ** 粗体标记
        field_name = re.sub(r"\*\*", "", cells[0]).strip()

        # 跳过表头行
        if field_name in ("字段", "内容", "来源追溯", "来源", ""):
            continue

        # 跳过空行或占位行
        if not field_name or field_name in ("—", "-"):
            continue

        found_fields.append(field_name)

    # 如果没有找到任何字段，说明章节不存在或格式异常
    if not found_fields:
        return {
            "missing": REQUIRED_CARD_FIELDS[:],
            "extra": [],
            "found": [],
            "status": "FAIL",
        }

    required_set = set(REQUIRED_CARD_FIELDS)
    found_set = set(found_fields)

    missing = [f for f in REQUIRED_CARD_FIELDS if f not in found_set]
    extra = [f for f in found_fields if f not in required_set]

    if missing:
        status = "FAIL"
    elif extra:
        status = "WARN"
    else:
        status = "PASS"

    return {
        "missing": missing,
        "extra": extra,
        "found": found_fields,
        "status": status,
    }
```

- [ ] **Step 2.3：在 run_validation 中接入字段完整性检查**

找到 `run_validation` 函数内处理 `final-analysis.md` 的章节完整性输出部分（约第 680-688 行）：

```python
        # 章节检查（针对 final-analysis.md）
        if filename in EXPECTED_SECTIONS:
            sections = check_sections(content, EXPECTED_SECTIONS[filename])
            if sections["fail"]:
                print(f"  章节完整性: ✗ FAIL（缺失 {len(sections['fail'])} 个章节）")
                for s in sections["fail"]:
                    print(f"    缺失: {s}")
                failed_dimensions.append(f"{filename} 章节")
            else:
                print("  章节完整性: ✓ PASS")
```

在 `print("  章节完整性: ✓ PASS")` 之后（整个 `if filename in EXPECTED_SECTIONS` 块结束之后），插入字段完整性检查：

```python
        # 字段完整性检查（针对 final-analysis.md 的需求分析卡）
        if filename == "final-analysis.md":
            card = check_card_fields(content)
            total = len(card["found"])
            required_count = len(REQUIRED_CARD_FIELDS)
            if card["status"] == "PASS":
                print(f"  字段完整性: ✓ PASS（{total}/{required_count}）")
            elif card["status"] == "WARN":
                extra_preview = ", ".join(card["extra"][:3])
                if len(card["extra"]) > 3:
                    extra_preview += f"... 共{len(card['extra'])}个"
                print(
                    f"  字段完整性: ⚠ WARN（{required_count}/{required_count} 必填字段存在，"
                    f"另有 {len(card['extra'])} 个扩展字段：{extra_preview}）"
                )
                total_issues += len(card["extra"])
            else:  # FAIL
                missing_preview = "、".join(card["missing"])
                print(f"  字段完整性: ✗ FAIL（缺失必填字段：{missing_preview}）")
                total_issues += len(card["missing"])
                failed_dimensions.append(f"{filename} 字段完整性")
```

- [ ] **Step 2.4：验证脚本语法正确**

```bash
cd /Users/11184725/projects/requirements-analysis
python3 -c "import ux-requirements-analyzer.scripts.quality_validator" 2>&1 || \
python3 ux-requirements-analyzer/scripts/quality-validator.py 2>&1 | head -3
```

预期：输出用法说明，无 SyntaxError / NameError。

实际应运行：
```bash
python3 ux-requirements-analyzer/scripts/quality-validator.py 2>&1 | head -3
```

预期：
```
用法：python3 quality-validator.py <分析目录>
```

- [ ] **Step 2.5：验证 test-a-normal 字段完整性 PASS**

```bash
cd /Users/11184725/projects/requirements-analysis
python3 ux-requirements-analyzer/scripts/quality-validator.py test-runs/test-a-normal/ 2>&1 | grep "字段完整性"
```

预期：
```
  字段完整性: ✓ PASS（14/14）
```

- [ ] **Step 2.6：验证 test-b-edge 字段完整性 FAIL（缺失 需求拆解）**

```bash
cd /Users/11184725/projects/requirements-analysis
python3 ux-requirements-analyzer/scripts/quality-validator.py test-runs/test-b-edge/ 2>&1 | grep "字段完整性"
```

预期：
```
  字段完整性: ✗ FAIL（缺失必填字段：需求拆解）
```

（test-b-edge 的分析卡有 19 个字段，但缺失 `需求拆解`，故为 FAIL。整体 validator 结果也从 PASS 变为 FAIL，这是正确行为——检出了之前漏过的真实问题。）

- [ ] **Step 2.7：完整运行两个测试场景，确认整体状态**

```bash
cd /Users/11184725/projects/requirements-analysis
python3 ux-requirements-analyzer/scripts/quality-validator.py test-runs/test-a-normal/ 2>&1 | tail -5
```

预期（test-a）：
```
  状态: ✓ PASS
  总问题数: 0（均为 WARN，不阻断）

  可以进入 Stage 5 整合输出
```

```bash
python3 ux-requirements-analyzer/scripts/quality-validator.py test-runs/test-b-edge/ 2>&1 | tail -6
```

预期（test-b）：
```
  状态: ✗ FAIL
  总问题数: 1
  失败维度:
    - final-analysis.md 字段完整性

  建议：返回 Stage 3 补充缺失内容后重新运行验证
```

- [ ] **Step 2.8：Commit**

```bash
cd /Users/11184725/projects/requirements-analysis
git add ux-requirements-analyzer/scripts/quality-validator.py
git commit -m "feat: add requirement card field completeness check to validator"
```

---

## Task 3：同步安装副本

**Files:**
- Sync: `~/.agents/skills/ux-requirements-analyzer/`

- [ ] **Step 3.1：同步**

```bash
cp -r /Users/11184725/projects/requirements-analysis/ux-requirements-analyzer/ \
      ~/.agents/skills/ux-requirements-analyzer/
```

- [ ] **Step 3.2：验证无差异**

```bash
diff -r /Users/11184725/projects/requirements-analysis/ux-requirements-analyzer/ \
        ~/.agents/skills/ux-requirements-analyzer/ \
        --exclude="__pycache__"
```

预期：无任何输出（完全一致）。

- [ ] **Step 3.3：Commit**

```bash
cd /Users/11184725/projects/requirements-analysis
git add .
git commit -m "chore: sync updated validator to install copy"
```

---

## Self-Review

### Spec coverage

| 设计文档要求 | 对应步骤 |
|------------|---------|
| 从 VAGUE_TERMS 删除相关/一般/通常/正常情况下 | Task 1 Step 1.1 ✓ |
| 添加删除原因注释 | Task 1 Step 1.1 ✓ |
| 新增 REQUIRED_CARD_FIELDS 常量（14项） | Task 2 Step 2.1 ✓ |
| 新增 check_card_fields 函数 | Task 2 Step 2.2 ✓ |
| 缺失字段 → FAIL，多余字段 → WARN | Task 2 Step 2.2 ✓ |
| 接入 run_validation | Task 2 Step 2.3 ✓ |
| test-a PASS，test-b FAIL（字段缺失） | Task 2 Step 2.5-2.7 ✓ |
| 同步安装副本 | Task 3 ✓ |

**无遗漏。**

### Notes

- `check_card_fields` 中的 `table_cells` 和 `is_table_separator` 是已有工具函数，直接复用，无需重新定义。
- `REQUIRED_CARD_FIELDS` 常量放在配置区（`EXPECTED_SECTIONS` 之后），与其他配置常量保持一致。
- 字段完整性检查的接入代码放在 `章节完整性` 块之后，逻辑清晰，不影响其他检查流程。
