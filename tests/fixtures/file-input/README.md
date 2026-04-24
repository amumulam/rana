# 文件输入集成测试

测试目标：验证 skill 对 PDF / Excel 文件的处理行为符合预期。

## 目录结构

```
file-input/
├── fixtures/
│   ├── pdf-with-images/   ← 放置含截图的 PDF 文件（场景 A）
│   └── excel-any/         ← 放置任意 Excel 文件（场景 B，含图/无图/图片丢失均可）
├── outputs/               ← 测试运行后的输出（input-structured.md 或 skill-response.txt）
└── README.md
```

## 放置测试文件

- `fixtures/pdf-with-images/` → 含截图的 PDF（如 `requirement.pdf`）
- `fixtures/excel-any/`       → 任意 `.xlsx` 文件（如 `requirement.xlsx`）

## 生成测试输出（第一步，人工触发）

outputs/ 目录需要事先由 AI 生成。方法：

**场景 A（PDF 分析输出）：**
在 AI session 中加载 `ux-requirement-analysis` skill，提供 `fixtures/pdf-with-images/` 中的 PDF 文件，
执行 Stage 1，将产出的 `input-structured.md` 保存到：
`outputs/a-pdf-with-images/input-structured.md`

**场景 B（Excel 拒绝响应）：**
在 AI session 中加载 `ux-requirement-analysis` skill，提供 `fixtures/excel-any/` 中的任意 Excel 文件，
将 skill 的响应文本保存到：
`outputs/b-excel-any/skill-response.txt`

## 运行测试

```bash
python3 tests/integration/test_file_input.py
python3 tests/integration/test_file_input.py a   # 仅场景 A
python3 tests/integration/test_file_input.py b   # 仅场景 B
```

## 验证维度

| 场景 | 文件类型 | 期望行为 | 验证点 |
|------|---------|---------|--------|
| A | PDF 含截图 | 正常分析，输出 `input-structured.md` | 五个必要章节齐全；来源标注 `[PDF截图X]` 或 `[PDF第X页]` 存在；标注覆盖率 ≥ 50% |
| B | Excel（任意） | **停止分析**，要求用户转为 PDF | 响应包含「导出/转」+「PDF」关键词；不产出分析内容 |

## 质量判定标准（场景 A）

`input-structured.md` 需满足：
1. 包含「业务背景与目标」「功能点清单」「界面信息」「约束条件」「假设与前提」五个章节
2. 每条信息有来源标注（`[PDF第X页]` / `[PDF截图X]` 等）
3. 通过 `quality-validator.py` 的来源追溯检查（pass_rate ≥ 80%）

## 质量判定标准（场景 B）

skill 响应需满足：
1. 包含 PDF 转换要求（「导出」或「转」+「PDF」）
2. 不包含需求分析结构内容（「业务背景与目标」「功能点清单」等章节标题）
