# 设计文档：UX Requirements Analyzer 全面测试计划

**日期：** 2026-03-31  
**范围：** `quality-validator.py` 单元测试 + E2E 场景扩充 + pyproject.toml 配置  
**方案：** 方案 C（分层独立测试 + ruff/pytest CI 钩子）

---

## 背景

`quality-validator.py` 经过 Round 1 和 Round 2 优化后，具备 7 个检查维度，但目前：
- 零单元测试
- 现有 2 个 E2E 场景均设计为通过，无专门触发 FAIL 路径的 fixture
- 以下路径完全未被测试：多功能 PRD、冲突解决路径、来源追溯 80% 边界失败

本计划通过添加单元测试和新 E2E fixture 来补全覆盖。

---

## 目标

1. 对核心逻辑函数建立 pytest 单元测试（覆盖正常/边界/FAIL 路径）
2. 新增 3 个 E2E 测试 fixture，覆盖此前缺失的场景
3. 配置 `pyproject.toml` 使 `python -m pytest` 和 `ruff check` 可一键运行

---

## 目录结构

```
requirements-analysis/
├── tests/
│   ├── unit/
│   │   ├── test_traceability.py     # 来源追溯 3 个函数
│   │   ├── test_vague_terms.py      # 模糊词检查
│   │   ├── test_card_fields.py      # 字段完整性检查
│   │   └── test_sections.py        # 章节/文件结构检查
│   └── e2e/
│       └── test_scenarios.py       # 5 个 E2E 场景（2 已有 + 3 新增）
├── test-runs/
│   ├── test-a-normal/              ← 已有：正常场景，预期 PASS
│   ├── test-b-edge/                ← 已有：极简输入，预期 FAIL（缺失需求拆解字段）
│   ├── test-c-multi-feature/       ← 新增：多功能 PRD（2 张需求卡），预期 PASS
│   ├── test-d-conflict/            ← 新增：change-log 含 ⚠ 待讨论条目，预期 PASS
│   └── test-e-traceability-fail/   ← 新增：input-structured 注释率 < 80%，预期 FAIL
├── pyproject.toml                  ← 新增：pytest + ruff 配置
└── ux-requirements-analyzer/
    └── scripts/quality-validator.py  ← 不修改
```

**运行命令：**
```bash
python -m pytest tests/ -v          # 全部测试
python -m pytest tests/unit/ -v     # 仅单元测试
python -m pytest tests/e2e/ -v      # 仅 E2E 测试
ruff check ux-requirements-analyzer/scripts/  # lint
```

---

## 单元测试设计

### `tests/unit/test_traceability.py`

测试 `has_traceability()`、`is_table_separator()`、`check_traceability_input_structured()` 的核心行为。

| 测试用例 | 输入 | 期望 |
|---|---|---|
| 带 `[PRD第2节]` 的行 → 有来源 | `"用户可发送消息 [PRD第2节]"` | `has_traceability()` → True |
| 带 `[推断：...]` 的行 → 有来源 | `"[推断：参考同类产品]"` | True |
| 纯文本行 → 无来源 | `"用户可发送消息"` | False |
| 表格分隔符行 → True | `"\|---|---\|"` | `is_table_separator()` → True |
| `check_traceability_input_structured` 全部有注释 → pass_rate=1.0 | 3 行带注释的表格 | pass_rate=1.0, issues=[] |
| `check_traceability_input_structured` 全部无注释 → pass_rate=0.0 | 3 行无注释的表格 | pass_rate=0.0 |
| 边界值：75% 注释率（4行中3行有） → 低于 80% | 4 行，3 行有注释 | pass_rate=0.75, issues 非空 |
| 代码块内的行 → 跳过不计入 checked | ` ```\n无注释行\n``` ` | checked=0 |

### `tests/unit/test_vague_terms.py`

测试 `check_vague_terms()` 的检测和豁免行为。

| 测试用例 | 输入 | 期望 |
|---|---|---|
| 包含 `适当` → 触发 | `"请适当调整字体大小"` | issues 包含该行 |
| 包含 `TBD` → 触发 | `"状态字段 TBD"` | issues 包含该行 |
| `相关度算法` → 不触发（已从 VAGUE_TERMS 移除） | `"通过相关度算法排序"` | issues=[] |
| 代码块内 `TBD` → 不触发 | ` ```\nTBD\n``` ` | issues=[] |
| 干净文本 → 全部通过 | 无任何模糊词的正文 | issues=[] |

### `tests/unit/test_card_fields.py`

测试 `check_card_fields()` 的 PASS/WARN/FAIL 分支及截断逻辑。

| 测试用例 | 输入 | 期望 |
|---|---|---|
| 14/14 字段齐全 → PASS | 完整 requirement-card 模板内容 | status=PASS, missing=[], extra=[] |
| 缺少 `需求拆解` → FAIL | 去掉一行 | status=FAIL, missing=[需求拆解] |
| 多出 2 个自定义字段 → WARN | 在表格加 2 行 | status=WARN, extra 长度=2 |
| 无需求分析卡段落 → PASS（跳过） | 不含该章节标题的文档 | status=PASS |
| 缺失 8 个字段 → 截断预览到 5 | 去掉 8 个字段行 | missing 长度=8，preview 格式含 "... 共8个" |

### `tests/unit/test_sections.py`

测试 `check_sections()` 和 `check_file_structure()` 的检查行为。

| 测试用例 | 输入 | 期望 |
|---|---|---|
| 包含全部 5 个交付物章节 → PASS | 完整 final-analysis | issues=[] |
| 缺少 `需求分析结论` → FAIL | 去掉该 heading | issues 包含 "需求分析结论" |
| 包含全部 5 个输出文件 → PASS | 模拟完整目录（tmp_path） | PASS |
| 缺少 `gap-analysis.md` → FAIL | 模拟缺文件的目录 | FAIL，提示缺少该文件 |

---

## E2E 测试设计

E2E 测试通过 `subprocess.run` 调用 CLI，断言退出码和标准输出关键词。

### 已有场景

| 场景 | 预期退出码 | 预期输出关键词 |
|---|---|---|
| test-a-normal | 0 | `✓ PASS` |
| test-b-edge | 1 | `字段完整性` |

### 新增场景

#### test-c-multi-feature — 多功能 PRD

**场景描述：** 一个 PRD 同时包含「消息通知」和「消息搜索」两个功能，`final-analysis.md` 产出 2 张需求分析卡（各 14/14 字段）。

**fixture 构造要点：**
- `final-analysis.md` 包含 2 个 `## 需求分析卡` 节（或用功能名区分标题）
- 每张卡各 14 个字段，全部有来源注释
- 其余 4 个文件结构正常

**预期验证器结果：** 退出码 0，输出 `✓ PASS`，字段完整性显示两张卡各 `14/14`

#### test-d-conflict — 冲突解决路径

**场景描述：** `change-log.md` 含一条 `⚠ 待讨论` 状态条目（PM 与研发对消息上限有分歧），其余文件正常。此场景验证验证器不会误判冲突状态为错误。

**fixture 构造要点：**
- `change-log.md` 至少包含 1 条带 `⚠ 待讨论` 的 CHG 条目
- `final-analysis.md` 正常，14/14 字段

**预期验证器结果：** 退出码 0，输出 `✓ PASS`（验证器当前跳过 change-log，冲突状态不阻断）

#### test-e-traceability-fail — 来源追溯 80% 边界失败

**场景描述：** `input-structured.md` 的数据行中只有约 60% 带来源注释，低于 80% 阈值。

**fixture 构造要点：**
- `input-structured.md` 包含 10 行数据，其中 4 行无来源注释（注释率 60%）
- 其余文件正常，`final-analysis.md` 有 14/14 字段

**预期验证器结果：** 退出码 1，输出含 `✗ FAIL` 和 `input-structured.md` 来源追溯维度失败信息

### E2E 汇总

| 场景 | 退出码 | 输出关键词 |
|---|---|---|
| test-a-normal | 0 | `✓ PASS` |
| test-b-edge | 1 | `字段完整性` |
| test-c-multi-feature | 0 | `✓ PASS` |
| test-d-conflict | 0 | `✓ PASS` |
| test-e-traceability-fail | 1 | `来源追溯` |

---

## pyproject.toml 配置

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = "-v --tb=short"

[tool.ruff]
line-length = 100
target-version = "py39"
select = ["E", "F", "W", "I"]
exclude = ["test-runs/", ".ruff_cache/"]
```

---

## 已知局限（不纳入本期范围）

1. **change-log 结构检查**：空白 change-log 目前不被验证器拦截，这是已知行为，未来可单独立项。
2. **Figma MCP 路径**：SKILL.md 中提及，但无法通过 CLI 自动化测试。
3. **Stage 3 用尽对话分支**：极端边界，暂不建立测试 fixture。

---

## 交付物清单

| 交付物 | 路径 | 备注 |
|---|---|---|
| 单元测试 × 4 | `tests/unit/test_*.py` | 共 ~22 个测试用例 |
| E2E 测试 | `tests/e2e/test_scenarios.py` | 5 个场景 |
| E2E fixture × 3 | `test-runs/test-c/d/e/` | 各含 5 个文件 |
| pyproject.toml | 项目根目录 | pytest + ruff 配置 |
