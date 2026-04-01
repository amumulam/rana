# UX Requirements Analyzer Skill — 自动化测试计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 全自动验证 ux-requirements-analyzer Skill 的输出质量。子代理扮演「使用了 Skill 的 AI」生成所有阶段产物，另一个子代理做结构化验收，最终输出测试报告。

**Architecture:** 两阶段自动化：
1. **Generator 子代理** — 读取 SKILL.md，输入测试 PRD，忠实执行 5 阶段工作流，写出所有输出文档
2. **Validator 子代理** — 读取输出文档，逐项对照验收标准检查，写出测试报告 + 跑 quality-validator.py

**测试场景：**
- 场景 A（正常）：有缺口的完整 PRD，期望所有阶段 PASS
- 场景 B（边界）：极简一句话需求，期望优雅降级、不崩溃、不编造

---

## 文件结构

```
test-runs/
├── test-a-normal/          ← 场景 A 输出
│   ├── input-structured.md
│   ├── gap-analysis.md
│   ├── change-log.md
│   ├── quality-report.md
│   └── final-analysis.md
├── test-b-edge/            ← 场景 B 输出
│   ├── input-structured.md
│   ├── gap-analysis.md
│   ├── change-log.md
│   ├── quality-report.md
│   └── final-analysis.md
└── test-report.md          ← 最终测试报告
```

---

## 测试输入数据

### 场景 A — 消息通知中心 PRD（有缺口版）

```markdown
# 消息通知中心 PRD

## 1. 背景
用户反映错过了很多重要消息，希望有一个统一的消息中心。

## 2. 功能描述
新增「消息中心」页面，展示所有系统通知和用户行为通知。
用户可以标记已读、删除消息。

## 3. 消息类型
- 系统通知（版本更新、维护公告）
- 互动通知（评论、点赞、关注）
- 交易通知（订单状态变更）

## 4. 技术说明
消息数据由后端推送，前端做展示。
```

**故意设计的 6 个缺口（用于验证 Stage 2 识别能力）：**
1. 消息数量上限未说明
2. 空状态（无消息时）未定义
3. 未读消息视觉区分未说明
4. 消息点击后跳转行为未说明
5. 分页/加载更多机制未说明
6. 权限边界（游客是否能看消息）未说明

**Stage 3 补充信息（Generator 子代理自行补充，模拟设计师回答）：**
- 消息上限：最多保留 100 条，超出删除最旧
- 空状态：显示「暂无消息」配插图
- 未读标记：红色圆点角标
- 点击跳转：根据消息类型跳转对应页面
- 分页：下拉加载更多，每次加载 20 条
- 游客：不展示消息入口

### 场景 B — 极简需求

```
做一个搜索功能
```

---

## Task 1：创建目录结构

**Files:**
- Create: `test-runs/test-a-normal/`（目录）
- Create: `test-runs/test-b-edge/`（目录）

- [ ] **Step 1: 创建测试目录**

```bash
mkdir -p /Users/11184725/projects/requirements-analysis/test-runs/test-a-normal
mkdir -p /Users/11184725/projects/requirements-analysis/test-runs/test-b-edge
```

- [ ] **Step 2: 验证目录存在**

```bash
ls /Users/11184725/projects/requirements-analysis/test-runs/
```

Expected output:
```
test-a-normal/
test-b-edge/
```

---

## Task 2：场景 A — Generator 子代理执行工作流

**目标：** 子代理读取 SKILL.md，按 5 阶段工作流处理消息通知中心 PRD，生成所有输出文档。

**Files:**
- Create: `test-runs/test-a-normal/input-structured.md`
- Create: `test-runs/test-a-normal/gap-analysis.md`
- Create: `test-runs/test-a-normal/change-log.md`
- Create: `test-runs/test-a-normal/quality-report.md`
- Create: `test-runs/test-a-normal/final-analysis.md`

**Generator 子代理 prompt（见 Task 2 执行说明）**

- [ ] **Step 1: 派发 Generator 子代理**

Prompt 见下方「Generator Prompt — 场景 A」章节。

- [ ] **Step 2: 验证所有 5 个文件已生成**

```bash
ls /Users/11184725/projects/requirements-analysis/test-runs/test-a-normal/
```

Expected: 5 个 .md 文件全部存在。

- [ ] **Step 3: 检查文件非空**

```bash
wc -l /Users/11184725/projects/requirements-analysis/test-runs/test-a-normal/*.md
```

Expected: 每个文件 > 10 行。

---

## Task 3：场景 B — Generator 子代理执行工作流（极简输入）

**Files:**
- Create: `test-runs/test-b-edge/input-structured.md`
- Create: `test-runs/test-b-edge/gap-analysis.md`
- Create: `test-runs/test-b-edge/change-log.md`
- Create: `test-runs/test-b-edge/quality-report.md`
- Create: `test-runs/test-b-edge/final-analysis.md`

- [ ] **Step 1: 派发 Generator 子代理（场景 B）**

Prompt 见下方「Generator Prompt — 场景 B」章节。

- [ ] **Step 2: 验证文件生成**

```bash
ls /Users/11184725/projects/requirements-analysis/test-runs/test-b-edge/
```

---

## Task 4：Validator 子代理 — 验收场景 A

**目标：** 逐项对照验收标准检查场景 A 的输出，写出评分结果。

**Files:**
- Create: `test-runs/test-report.md`（部分，场景 A 章节）

- [ ] **Step 1: 派发 Validator 子代理（场景 A）**

Prompt 见下方「Validator Prompt — 场景 A」章节。

- [ ] **Step 2: 运行 quality-validator.py**

```bash
cd /Users/11184725/projects/requirements-analysis
python3 ux-requirements-analyzer/scripts/quality-validator.py test-runs/test-a-normal/
```

将输出追加到 `test-runs/test-report.md`。

---

## Task 5：Validator 子代理 — 验收场景 B

- [ ] **Step 1: 派发 Validator 子代理（场景 B）**

Prompt 见下方「Validator Prompt — 场景 B」章节。

- [ ] **Step 2: 运行 quality-validator.py（场景 B）**

```bash
python3 /Users/11184725/projects/requirements-analysis/ux-requirements-analyzer/scripts/quality-validator.py \
  /Users/11184725/projects/requirements-analysis/test-runs/test-b-edge/
```

---

## Task 6：生成最终测试报告 + 决定是否修复

**Files:**
- Modify: `test-runs/test-report.md`（写入汇总章节）

- [ ] **Step 1: 读取场景 A、B 的验收结果，写入汇总评分表**

```markdown
## 汇总评分

| 检查项 | 场景A | 场景B |
|--------|-------|-------|
| Stage 1 结构完整性 | X/Y | X/Y |
| Stage 2 缺口识别率 | X/6 | N/A |
| Stage 2 7维度拆解 | X/7 | X/7 |
| Stage 3 对话行为 | X/Y | X/Y |
| Stage 4 质量门禁格式 | PASS/FAIL | PASS/FAIL |
| 交付物A 字段完整率 | X/14 | X/14 |
| 交付物B 7维度 | X/7 | X/7 |
| 交付物C 4类场景 | X/4 | X/4 |
| 交付物D 分组格式 | PASS/FAIL | PASS/FAIL |
| 交付物E 结论公式 | PASS/FAIL | PASS/FAIL |
| 可追溯性（抽查10条）| X/10 | X/10 |
| 边界场景不编造 | N/A | PASS/FAIL |

## 整体结论
PASS / FAIL

## 需修复的问题
（列出所有 FAIL 项及对应修复建议）
```

- [ ] **Step 2: 如有 FAIL 项，修复对应 Skill 文件**

对每个 FAIL 项，直接修改对应文件：
- Stage 流程问题 → `SKILL.md`
- 检查清单问题 → `references/analysis-checklist.md`
- 质量门禁问题 → `references/quality-gates.md`
- 模板问题 → 对应 `templates/*.md`

- [ ] **Step 3: 修复后针对失败项重新生成并重验**

---

## Generator Prompt — 场景 A

```
你是一个交互设计师 AI 助手，已加载了 ux-requirements-analyzer Skill。
请严格按照 Skill 的 5 阶段工作流处理以下 PRD，生成所有阶段输出文档。

## Skill 文件位置
主文件：/Users/11184725/projects/requirements-analysis/ux-requirements-analyzer/SKILL.md
请先读取该文件，了解完整工作流程、输出格式和来源标注规范。
同时读取引用文件：
- references/analysis-checklist.md（Stage 2 使用）
- references/traceability-guide.md（全程使用）
- references/ux-analysis-methods.md（Stage 2 使用）

## 输入 PRD

# 消息通知中心 PRD

## 1. 背景
用户反映错过了很多重要消息，希望有一个统一的消息中心。

## 2. 功能描述
新增「消息中心」页面，展示所有系统通知和用户行为通知。
用户可以标记已读、删除消息。

## 3. 消息类型
- 系统通知（版本更新、维护公告）
- 互动通知（评论、点赞、关注）
- 交易通知（订单状态变更）

## 4. 技术说明
消息数据由后端推送，前端做展示。

## Stage 3 补充信息（模拟设计师已回答的澄清问题）

在 Stage 3 协作对话中，假设设计师（你自己）已补充了以下信息：
- 消息上限：最多保留 100 条，超出删除最旧 [PM确认]
- 空状态：显示「暂无消息」配插图 [PM确认]
- 未读标记：红色圆点角标 [PM确认]
- 点击跳转：根据消息类型跳转对应页面 [PM确认]
- 分页：下拉加载更多，每次加载 20 条 [研发确认]
- 游客：不展示消息入口 [PM确认]

## 输出要求

严格按照 SKILL.md 的输出格式，将以下文件写入 /Users/11184725/projects/requirements-analysis/test-runs/test-a-normal/：

1. input-structured.md — Stage 1 输出
2. gap-analysis.md — Stage 2 输出
3. change-log.md — Stage 3 输出（记录上方补充信息为变更）
4. quality-report.md — Stage 4 输出
5. final-analysis.md — Stage 5 输出（包含5项交付物：需求分析卡、拆解清单、场景边界、待澄清清单、分析结论）

## 关键要求

1. **来源标注**：每条内容必须有 [PRD第X节] / [PM确认] / [推断] / [缺失] 格式的来源标注
2. **不要编造**：没有来源的内容标 [推断] 或 [缺失]，不能凭空写实质性内容
3. **完整执行**：不能跳过任何阶段，每个阶段都要写入对应文件
4. **格式对齐**：严格对照 SKILL.md 中每个阶段的输出格式示例
5. **需求分析卡**：必须包含全部 14 个字段
6. **拆解清单**：必须包含 7 个维度
7. **分析结论**：必须遵循「谁+场景+问题+优先解决」公式

## 报告格式

完成后报告：
- Status: DONE
- 各文件行数
- 是否有遇到 SKILL.md 描述不清楚的地方（如有，列出）
```

---

## Generator Prompt — 场景 B

```
你是一个交互设计师 AI 助手，已加载了 ux-requirements-analyzer Skill。
请严格按照 Skill 的 5 阶段工作流处理以下极简需求，生成所有阶段输出文档。

## Skill 文件位置
主文件：/Users/11184725/projects/requirements-analysis/ux-requirements-analyzer/SKILL.md
请先读取该文件，了解完整工作流程、输出格式和来源标注规范。
同时读取引用文件：
- references/analysis-checklist.md
- references/traceability-guide.md

## 输入需求

做一个搜索功能

## Stage 3 说明

输入信息极度不完整，Stage 3 的协作对话中无法获得补充（假设设计师说「我也不知道，先分析看看」）。
所有不明确的内容标注 [缺失]，全部进入待澄清清单。

## 输出要求

将以下文件写入 /Users/11184725/projects/requirements-analysis/test-runs/test-b-edge/：

1. input-structured.md
2. gap-analysis.md
3. change-log.md（可以很简短，记录"设计师无法补充"）
4. quality-report.md（预期大量 FAIL 或 WARN）
5. final-analysis.md（大量字段为 [缺失]，分析结论也是基于推断）

## 关键要求

1. **不能编造**：没有来源的内容一律标 [缺失] 或 [推断]，绝不能自己补全业务内容
2. **优雅降级**：即使信息极少，也要完整走完 5 个阶段
3. **待澄清清单**：应该非常长，包含大量需要确认的问题
4. **分析结论**：应该如实反映信息不足，不能假装结论完整

## 报告格式

完成后报告：
- Status: DONE
- 各文件行数
- [缺失] 标注数量
```

---

## Validator Prompt — 场景 A

```
你是测试验证员，负责检查 UX Requirements Analyzer Skill 在场景 A 的输出质量。

## 待验收文件

目录：/Users/11184725/projects/requirements-analysis/test-runs/test-a-normal/
文件：input-structured.md, gap-analysis.md, change-log.md, quality-report.md, final-analysis.md

## 原始 PRD（用于对照）

# 消息通知中心 PRD
[背景: 统一消息中心]
[功能: 消息中心页面，标记已读、删除]
[消息类型: 系统通知、互动通知、交易通知]
[技术: 后端推送，前端展示]

## 故意设计的 6 个缺口（验证 Stage 2 识别能力）

1. 消息数量上限
2. 空状态
3. 未读消息视觉区分
4. 消息点击跳转行为
5. 分页/加载更多
6. 游客权限边界

## 验收任务

读取所有文件，逐项检查以下标准，输出评分。

### A1. Stage 1 (input-structured.md) 检查

- [ ] 包含「业务背景与目标」章节（是/否）
- [ ] 包含「功能点清单」章节（是/否）
- [ ] 包含「约束条件」章节（是/否）
- [ ] 3种消息类型均被提取（是/否）
- [ ] 抽查5条内容，均有来源标注（X/5）

### A2. Stage 2 (gap-analysis.md) 检查

缺口识别（6个故意缺口中识别了几个）：
- [ ] 消息数量上限（是/否）
- [ ] 空状态（是/否）
- [ ] 未读消息视觉区分（是/否）
- [ ] 消息点击跳转（是/否）
- [ ] 分页机制（是/否）
- [ ] 游客权限（是/否）
缺口识别率：X/6

7维度拆解是否存在：
- [ ] 主任务（是/否）
- [ ] 子任务（是/否）
- [ ] 页面/入口（是/否）
- [ ] 分支流程（是/否）
- [ ] 异常流程（是/否）
- [ ] 状态变化（是/否）
- [ ] 依赖关系（是/否）
7维度通过率：X/7

### A3. Stage 3 (change-log.md) 检查

- [ ] 记录了6条补充信息（X/6）
- [ ] 每条有来源标注 [PM确认] 或 [研发确认]（是/否）
- [ ] 格式符合 change-log 模板（是/否）

### A4. Stage 4 (quality-report.md) 检查

- [ ] 包含5个维度（是/否）
- [ ] 每个维度有明确判定（PASS/WARN/FAIL）（是/否）
- [ ] 整体状态明确（PASS/FAIL）（是/否）
- [ ] 整体状态为 PASS（预期应通过）（是/否）

### A5. Stage 5 (final-analysis.md) 检查

需求分析卡14字段：
- [ ] 需求名称 / 版本号 / 需求来源 / 背景说明
- [ ] 目标用户 / 使用场景 / 核心问题
- [ ] 需求拆解 / 业务规则 / 约束条件 / 优先级
- [ ] 待澄清项 / 风险点 / 需求结论
字段通过率：X/14

拆解清单7维度：X/7（同 A2 检查，看 final 里的版本）

场景边界说明：
- [ ] 典型使用场景 ≥1条（是/否）
- [ ] 边界场景 ≥1条（是/否）
- [ ] 不支持场景（游客）（是/否）
- [ ] 限制条件（是/否）

待澄清清单：
- [ ] 按确认对象分组（是/否）
- [ ] 有影响评估字段（是/否）

分析结论：
- [ ] 一句话结论存在（是/否）
- [ ] 「谁」字段（是/否）
- [ ] 「在什么场景」字段（是/否）
- [ ] 「遇到什么问题」字段（是/否）
- [ ] 「本次优先解决」字段（是/否）
- [ ] 设计输入建议 ≥2条（是/否）

### A6. 可追溯性抽查

从 final-analysis.md 随机抽取10条内容行，检查是否有来源标注：
覆盖率：X/10

## 输出格式

将完整评分结果写入：
/Users/11184725/projects/requirements-analysis/test-runs/test-report.md

格式：
# 测试报告

## 场景 A — 消息通知中心 PRD

### 评分汇总

| 检查项 | 得分 | 状态 |
|--------|------|------|
| Stage 1 结构 | X/5 | PASS/FAIL |
| Stage 2 缺口识别 | X/6 | PASS/FAIL |
| Stage 2 7维度 | X/7 | PASS/FAIL |
| Stage 3 变更记录 | X/6 | PASS/FAIL |
| Stage 4 质量报告 | X/3 | PASS/FAIL |
| 交付物A 字段 | X/14 | PASS/FAIL |
| 交付物C 场景边界 | X/4 | PASS/FAIL |
| 交付物E 结论公式 | X/6 | PASS/FAIL |
| 可追溯性 | X/10 | PASS/FAIL |

### 问题清单
（列出所有 FAIL 项，说明具体哪里不符合预期）

### 结论
PASS / FAIL
```

---

## Validator Prompt — 场景 B

```
你是测试验证员，负责检查 UX Requirements Analyzer Skill 在场景 B（极简输入）的输出质量。

## 待验收文件

目录：/Users/11184725/projects/requirements-analysis/test-runs/test-b-edge/

## 场景 B 的特殊验收标准

这个场景测试「极简输入下的优雅降级」，验收重点与场景 A 不同：

### B1. 不编造原则（最重要）

读取所有文件，检查是否有无来源支撑的实质性业务内容。
判断标准：如果一段内容既没有标注 [推断]，也没有标注 [缺失]，也没有 [PRD] 或确认类来源，则视为「编造」。

- [ ] 是否存在编造内容（有/无）
- [ ] 若有，列出具体行

### B2. 优雅降级

- [ ] 5个文件都已生成（是/否）
- [ ] input-structured.md 大量字段为 [缺失]（是/否）
- [ ] gap-analysis.md 缺口清单条数 ≥ 10 条（是/否）
- [ ] quality-report.md 整体状态为 FAIL（预期，信息不足）（是/否）
- [ ] final-analysis.md 待澄清清单问题数量 ≥ 10 条（是/否）

### B3. 结论诚实性

- [ ] 分析结论如实反映信息不足（不是假装完整）（是/否）
- [ ] 设计输入建议是问题形式（「需确认...」），而非断言（是/否）

## 输出格式

将结果追加到：
/Users/11184725/projects/requirements-analysis/test-runs/test-report.md

格式：
## 场景 B — 极简输入「做一个搜索功能」

### 评分汇总

| 检查项 | 结果 | 状态 |
|--------|------|------|
| 不编造原则 | 有/无编造 | PASS/FAIL |
| 5文件均生成 | 是/否 | PASS/FAIL |
| 缺口清单 ≥10条 | X条 | PASS/FAIL |
| 质量报告为FAIL | 是/否 | PASS/FAIL |
| 待澄清清单 ≥10条 | X条 | PASS/FAIL |
| 结论诚实性 | 是/否 | PASS/FAIL |

### 问题清单
（列出发现的问题）

### 结论
PASS / FAIL
```

---

## 验收标准（整体通过条件）

| 指标 | 通过标准 |
|------|---------|
| 场景 A — Stage 2 缺口识别 | ≥ 4/6 |
| 场景 A — 交付物A 字段完整率 | ≥ 12/14 |
| 场景 A — 可追溯性 | ≥ 8/10 |
| 场景 A — 整体 | 无超过2个 FAIL 项 |
| 场景 B — 不编造原则 | 必须 PASS（零容忍） |
| 场景 B — 优雅降级 | ≥ 4/5 |
