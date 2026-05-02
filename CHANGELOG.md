# Changelog

本文件记录所有重要变更。

格式基于 [Keep a Changelog](https://keepachangelog.com/)，
本项目遵循 [语义化版本](https://semver.org/)。

## [0.4.3] - 2026-05-03

### 新增

- Agent 行为约束章节（SKILL.md 独立章节），5 项轻量禁令式规则约束 Agent 工具调用行为

### 变更

- `RELEASE_NOTE.md` 重命名为 `CHANGELOG.md`，格式改为 Keep a Changelog 规范

### 移除

- `scripts/generate-changelog.sh` — 机械拼接脚本，已被手写维护替代

## [0.4.2] - 2026-04-30

### 新增

- Quick Mode 四段式消息呈现 + 术语优化 + 目录重命名
- 显式嵌入分析方法到 Quick/Full 流程
- file_parser 配置更新：PDF 用 pdf 技能，xlsx/xls 用 xlsx 技能

### 变更

- CI tag regex 支持 rc/alpha/beta 预发布标识
- GIT_DEPTH 改为 per-job 设置（pytest 默认 depth 20，release/notify 用 depth 0）

### 修复

- pip install 加超时重试防止下载失败
- changelog 脚本改用 echo+写文件替代 printf（防止 % 被误解释）
- JSON payload 构建改用 jq 从文件读取，避免 shell 变量嵌入多行文本

### 移除

- Package Registry 上传步骤（403，Skill 靠 rsync 分发）

### 基础设施

- push 和 MR 自动跑 pytest，测试失败则阻止发布
- auto-release 通过 needs 依赖 pytest，形成质量门禁
- sync-wiki 自动同步 wiki 到 GitLab Wiki（HTTPS + Access Token）
- Skill 安装同步自动化 — tag 发布后 rsync 到安装目录

## [0.4.1] - 2026-04-24

### 新增

- Quick Mode 工作流拆分为独立 guideline 文件（渐进式披露）
- Full Mode 工作流拆分为独立 guideline 文件（渐进式披露）
- v0.4 架构图（双模式路由 + 顺序布局）
- Quick Mode 增加分析框架概览、输出格式总览、边界场景处理

### 变更

- SKILL.md 精简为路由版（~240 行），Quick/Full 流程路由到 references
- analysis-methods.md 结构统一，加载指引加入 SKILL.md

### 修复

- Quick Mode 专属 gotchas 从 SKILL.md 移入 workflow-quick-mode-guideline.md

## [0.4.0] - 2026-04-23

### 新增

- 双模式架构：Quick Mode + Full Mode 路由切换
- Full Mode 三阶段流程：诊断层→方案层→提炼层
- 批判反驳机制（collaboration-protocol.md）：Quick/Full 通用
- 八章结构输出模板（analysis-template-full.md）
- P0 缺口规则重写（p0-gates.md）适配三阶段结构
- stage-1/2/3 独立 guideline 文件
- 共享协作流程定义 + 四段式消息结构

### 变更

- SKILL.md 内联流程全部外迁至 references/
- v0.3.3 SKILL.md 重构拆解、文件规范化

## [0.3.2] - 2026-04-14

### 新增

- 迁移成本评估
- HMW 方案发散方法
- MVP 敏捷裁量

## [0.3.1] - 2026-04-14

### 新增

- 咨询式批判思维（C1-C7 触发条件）
- 启发式追问机制
- 边界场景处理

## [0.3.0] - 2026-04-14

### 新增

- Stage 1 重写为 Basic+Core 输出
- Stage 2 重写为协作补充流程
- Stage 3 重写为 Detail 输出，暂停 Stage 4
- 章节优先级定义（P0/P1/P2）
- 输出目录改为单一递增文件（final-analysis.md）
- 交互细节判断标准，保留用户删减的字段

### 变更

- 章节格式简化（一、xxx 替代 第一章：xxx）
- 输出文件重命名为 final-analysis.md，PRD 来源标注为 X.X 节格式

### 修复

- 标题和多功能处理逻辑修正
- 清理旧流程引用

## [0.2.0] - 2026-04-13

### 新增

- Stage 0 文件预处理（PDF/XLSX 等）
- file_parser 配置委托外部 skill

## [0.1.0] - 2026-04-10

### 新增

- 初始版本发布
- Skill 核心流程：Stage 1（诊断）→ Stage 2（协作）→ Stage 3（提炼）→ Stage 4（验证）
- 质量门禁验证器（quality-validator.py）：追溯检查、模糊词检查、卡片完整性检查
- 单元测试 + E2E 测试 + 集成测试
- 5 步争议处理流程
- 主路径确认节点（human-in-the-loop）
- 产品知识库检索步骤（R1-R4）+ 知识库回写步骤（W1-W4）
- 截图输入支持
- 多功能 PRD 处理 + 冲突处理流程
