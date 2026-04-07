# 产品知识库（Knowledge Base）Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 rana skill 中集成产品知识库，Stage 1 开始时检索 `knowledge/` 目录获取产品上下文，Stage 5 结束后将本次分析发现的固有知识回写到知识库。

**Architecture:** 纯 SKILL.md 文本改动，分三处插入：①「输出目录约定」节新增 knowledge 目录说明；②Stage 1「接收输入」之前新增知识库检索步骤；③Stage 5 结束语之后新增知识回写步骤。无代码改动，无 validator 变更。

**Tech Stack:** Markdown 文本编辑；回归测试用 `python3 -m pytest tests/ -v`（70 个测试，必须保持全绿）

**Spec:** `docs/superpowers/specs/2026-04-07-knowledge-base-design.md`

**重点：** 检索逻辑是核心，Task 2 的细节最关键——产品线匹配、文件选择、未匹配时的询问格式必须精确。

---

## 文件改动清单

| 文件 | 变更类型 | 位置 |
|------|---------|------|
| `rana/SKILL.md` | 修改（3处） | ①「输出目录约定」节；②Stage 1「接收输入」前；③Stage 5 结束语后 |

---

## Task 1：输出目录约定节新增 knowledge 目录说明

**Files:**
- Modify: `rana/SKILL.md`（「输出目录约定」节，约第 49-83 行）

- [ ] **Step 1: 定位目标段落**

  找到「输出目录约定」节中的 workspace 目录树示例：

  ```markdown
  <workspace>/
  └── ux-requirement-analysis/              ← 语义容器（所有需求分析的统一存放位置）
  ```

- [ ] **Step 2: 在目录树中新增 knowledge 目录**

  将目录树从：

  ```markdown
  <workspace>/
  └── ux-requirement-analysis/              ← 语义容器（所有需求分析的统一存放位置）
      └── <需求名称>/
          └── <YYYY-MM-DD>/
              ├── input-structured.md       ← Stage 1 输出
              ├── gap-analysis.md           ← Stage 2 输出
              ├── change-log.md             ← Stage 3 输出
              ├── quality-report.md         ← Stage 4 输出
              └── final-analysis.md         ← Stage 5 输出
  ```

  改为：

  ```markdown
  <workspace>/
  ├── ux-requirement-analysis/              ← 语义容器（所有需求分析的统一存放位置）
  │   └── <需求名称>/
  │       └── <YYYY-MM-DD>/
  │           ├── input-structured.md       ← Stage 1 输出
  │           ├── gap-analysis.md           ← Stage 2 输出
  │           ├── change-log.md             ← Stage 3 输出
  │           ├── quality-report.md         ← Stage 4 输出
  │           └── final-analysis.md         ← Stage 5 输出
  └── knowledge/                            ← 产品知识库（见下方说明）
      ├── _temp/                            ← AI 临时暂存，用户确认后移入正式目录
      └── <产品线>/                         ← 如 vivo-service/、vivo-mall/
          ├── overview.md                   ← 产品线概览（可选）
          └── *.md                          ← 其他业务规则文件（自由命名）
  ```

  在目录树之后，在「若用户指定了路径，以用户指定路径为准。」一句之前，插入 knowledge 目录说明：

  ```markdown
  **knowledge 目录约定：**

  - 产品线目录名由设计师自由定义（如 `vivo-service`、`vivo-mall`），AI 靠目录名 + 文件首行标题判断相关性
  - 文件命名不强制，推荐语义化命名（如 `member-system.md`、`device-rules.md`）
  - 初期由设计师手动维护；AI 在 Stage 5 结束后可将新发现的固有知识追加到对应文件（须用户确认）
  - `_temp/` 由 AI 自动管理，用户无需手动操作
  ```

- [ ] **Step 3: 运行回归测试**

  ```bash
  python3 -m pytest tests/ -v --tb=short -q
  ```

  预期：`70 passed`

- [ ] **Step 4: 提交**

  ```bash
  git add rana/SKILL.md
  git commit -m "feat(skill): 输出目录约定新增 knowledge 知识库目录说明"
  ```

---

## Task 2：Stage 1 新增知识库检索步骤（核心）

**Files:**
- Modify: `rana/SKILL.md`（Stage 1「接收输入」节，第 116 行附近）

- [ ] **Step 1: 定位插入位置**

  找到 Stage 1「接收输入」节的提示语块（`> 请提供以下材料...`），检索步骤要插入在**这段提示语之前**，也就是用户提供材料之前先检索知识库。

  找到这一行：
  ```markdown
  ### 接收输入
  ```

- [ ] **Step 2: 在「接收输入」标题之前插入知识库检索节**

  在 `### 接收输入` 这一行之前插入：

  ```markdown
  ### 知识库检索（Stage 1 第一步）

  在提示用户提供材料之前，先检索产品知识库获取相关上下文。

  **Step K1：扫描知识库目录**

  列出 `knowledge/` 下所有子目录名（产品线列表）。若 `knowledge/` 目录不存在，跳过检索步骤，直接进入「接收输入」。

  **Step K2：判断匹配产品线**

  根据用户已提供的任何信息（需求名称、PRD 关键词、产品名称）：
  - 判断最可能匹配的产品线目录
  - 一次只匹配一个产品线（最高置信度优先）
  - 匹配逻辑：目录名与需求名称或 PRD 内容中的产品名有语义重叠即视为匹配

  **Step K3a（匹配成功）：按需读入文件**

  1. 列出该产品线目录下所有文件名
  2. 优先读入 `overview.md`（如存在）
  3. 根据需求关键词，再选 1-2 个最相关的专项文件读入（如 `member-system.md`、`device-rules.md`）
  4. 知识库内容作为分析上下文，**不直接向用户输出，不在分析文档中重复抄写**
  5. 在后续生成的 `input-structured.md` 头部注明参考文件（见模板）

  **Step K3b（未找到匹配）：询问用户**

  停下来发送以下消息（不继续分析，等待用户回复）：

  > 我在知识库中没有找到匹配的产品线，请确认：
  > - 这个需求属于哪个产品线？（如：`vivo-service`）
  > - 是否有特定业务模块需要参考？（如：会员体系、设备规则）
  >
  > 如果知识库暂无相关内容，回复「跳过」继续分析。

  - 用户指定产品线后：重新执行 K2 → K3a
  - 目录存在但无匹配文件：告知「`knowledge/<产品线>/` 目录暂无文件，建议后续创建」，继续分析
  - 用户回复「跳过」：直接进入「接收输入」

  **Step K4：用户可纠正**

  若用户指出参考文件有误（如「应该参考 device-rules.md」），重新读入指定文件，更新 `input-structured.md` 中的参考知识库注明。

  ---

  ```

- [ ] **Step 3: 更新 input-structured.md 模板，新增参考知识库字段**

  找到 `### 输出：input-structured.md` 下的模板，在 `**分析日期**：YYYY-MM-DD` 这行之后、`---` 分隔线之前，插入可选字段：

  ```markdown
  **参考知识库**：knowledge/<产品线>/<文件名>.md（知识库为空或跳过时省略此行）
  ```

- [ ] **Step 4: 运行回归测试**

  ```bash
  python3 -m pytest tests/ -v --tb=short -q
  ```

  预期：`70 passed`

- [ ] **Step 5: 提交**

  ```bash
  git add rana/SKILL.md
  git commit -m "feat(skill): stage1 新增知识库检索步骤（产品线匹配 + 未匹配询问）"
  ```

---

## Task 3：Stage 5 结束后新增知识回写步骤

**Files:**
- Modify: `rana/SKILL.md`（Stage 5「Stage 5 完成后必须执行」节，约第 659-667 行）

- [ ] **Step 1: 定位插入位置**

  找到 Stage 5 完成后的结束语节：

  ```markdown
  ### Stage 5 完成后必须执行：主动向用户呈现完整报告
  ```

  知识回写步骤要插入在**结束语之后**（即用户已看到完整报告之后），在 `---` 分隔线（通往 Stage 6）之前。

  找到这段结束语的末尾：
  ```markdown
  > 以上是本次需求分析的完整报告。所有 P0 缺口已补完，可进入设计分析阶段。如需调整任何内容，请直接告知。
  ```

- [ ] **Step 2: 在结束语之后、`---` 之前插入知识回写节**

  在结束语引用块之后插入：

  ```markdown

  ### Stage 5 完成后可选执行：知识库回写

  完整报告呈现给用户后，若本次分析中发现了可复用的产品固有知识，执行回写流程：

  **Step W1：识别固有知识**

  从 `change-log.md` 和 `final-analysis.md` 中提取本次确认的产品固有知识。

  **判断标准——固有知识（回写）vs 单次决策（不回写）：**

  | 固有知识（回写） | 单次决策（不回写） |
  |---|---|
  | 会员等级体系、机型划分规则 | Tab 默认选中、入口具体位置 |
  | 客服分流沿用现有逻辑的说明 | 本次迭代的优先级、排期 |
  | 产品已有功能模块的说明 | 某功能本期不做的原因 |

  **判断原则**：这条信息在下一次完全不同的需求分析中是否仍然成立？若是，则为固有知识；若仅针对本次需求，则为单次决策。

  若无固有知识可提取，跳过回写流程，不向用户发起询问。

  **Step W2：写入临时目录**

  将提取的固有知识写入：
  ```
  knowledge/_temp/<YYYY-MM-DD>-<需求名称>.md
  ```

  **Step W3：向用户展示并确认**

  发送以下格式的消息：

  > 本次分析中发现以下产品固有知识，建议写入知识库：
  >
  > | 内容 | 建议写入文件 |
  > |------|-------------|
  > | [固有知识1] | `knowledge/<产品线>/<文件名>.md` |
  > | [固有知识2] | `knowledge/<产品线>/<文件名>.md` |
  >
  > 确认写入？可修改目标路径，或回复「跳过」。

  **Step W4a（用户确认）：移入正式目录，清空 `_temp/`**

  - 目标文件已存在：在文件末尾追加，格式为：
    ```markdown

    ---
    <!-- 来源：[需求分析确认 YYYY-MM-DD，需求：<需求名称>] -->

    [固有知识内容]
    ```
  - 目标文件不存在：自动创建，写入内容（含来源注释）
  - 写入完成后，删除 `knowledge/_temp/` 下对应临时文件

  **Step W4b（用户回复「跳过」）：**

  删除 `knowledge/_temp/` 下对应临时文件，不做任何写入，流程结束。
  ```

- [ ] **Step 3: 运行回归测试**

  ```bash
  python3 -m pytest tests/ -v --tb=short -q
  ```

  预期：`70 passed`

- [ ] **Step 4: 提交**

  ```bash
  git add rana/SKILL.md
  git commit -m "feat(skill): stage5 结束后新增知识库回写步骤（temp 暂存 + 用户确认）"
  ```

---

## Task 4：同步安装 + 最终回归

**Files:**
- 无代码改动

- [ ] **Step 1: 同步安装到本地 skill 目录**

  ```bash
  cp -r rana/. ~/.agents/skills/rana/
  ```

- [ ] **Step 2: 验证安装目录与源目录一致**

  ```bash
  diff -r rana/ ~/.agents/skills/rana/ --exclude="*.pyc"
  ```

  预期：无输出（完全一致）

- [ ] **Step 3: 运行完整回归测试**

  ```bash
  python3 -m pytest tests/ -v
  ```

  预期：`70 passed`

- [ ] **Step 4: 手动验证 validator 仍可运行**

  ```bash
  python3 rana/scripts/quality-validator.py test-runs/test-a-normal
  ```

  预期：退出码 0，输出包含 `✓ PASS`

---

## 完成标准

- [ ] `python3 -m pytest tests/ -v` → 70 passed
- [ ] `diff -r rana/ ~/.agents/skills/rana/ --exclude="*.pyc"` → 无差异
- [ ] `rana/SKILL.md` 「输出目录约定」节包含 `knowledge/` 目录树和说明
- [ ] `rana/SKILL.md` Stage 1 包含 `### 知识库检索（Stage 1 第一步）` 节，含 K1-K4 步骤
- [ ] Stage 1 知识库检索节包含「未找到匹配」时的完整询问格式
- [ ] `input-structured.md` 模板包含 `**参考知识库**` 可选字段
- [ ] `rana/SKILL.md` Stage 5 包含 `### Stage 5 完成后可选执行：知识库回写` 节，含 W1-W4 步骤
- [ ] 回写节包含固有知识 vs 单次决策的判断表格
