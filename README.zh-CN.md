# rana — UX 需求分析 Skill

中文 | [English](./README.md)

一个可部署到 **OpenClaw、OpenCode、Claude Code** 等 CLI agent 平台的 **agent skill**，帮助 UX 交互设计师将 PM 的 PRD/需求文档转化为结构化的需求分析交付物。

## 功能

- **Quick Mode**：四维度快速分析（问题 → 目标 → 供给 → 指标）+ 澄清提问清单
- **Full Mode**：三阶段渐进式完整分析（诊断层 → 方案层 → 提炼层），产出 8 章节+总结的完整说明书
- **内置质量门禁**：`quality-validator.py` 自动校验文件结构、来源追溯、P0 小节、章节完整性和模糊表述

## 快速开始

```bash
# 安装 skill（根据你的 agent 平台调整路径）
cp -r rana/. ~/.agents/skills/rana/       # OpenCode / BlueCode
cp -r rana/. ~/.openclaw/skills/rana/     # OpenClaw

# 在 agent session 中使用
# 直接提供 PRD 文本、PDF 或截图 — rana 自动检测输入类型
```

## 项目结构

```
rana/
├── SKILL.md                              # Skill 入口 — 双模式路由 + 共享启动流程
├── scripts/quality-validator.py          # CLI 质量门禁校验器
├── references/
│   ├── workflow-quick-mode-guideline.md  # Quick Mode 全流程
│   ├── workflow-full-mode-guideline.md   # Full Mode 全流程
│   ├── collaboration-protocol.md         # 批判反驳与协作对话规范（双模式通用）
│   ├── p0-gates.md                       # P0 缺口规则
│   ├── stage-1-diagnosis.md              # 诊断层详细流程
│   ├── stage-2-solution.md               # 方案层详细流程
│   ├── stage-3-refine.md                 # 提炼层详细流程
│   ├── analysis-methods.md               # HMW / MVP / 五问法 / X-Y Problem
│   └── quality-validator.md              # Validator 行为文档
├── assets/
│   ├── analysis-template-full.md         # Full Mode 输出模板（8章节+总结）
│   └── analysis-template-quick.md        # Quick Mode 输出模板
└── config.yaml                           # 文件解析配置
```

## 测试

```bash
pip3 install pdfplumber ruff   # 开发依赖

python3 -m pytest tests/ -v    # 运行全部测试（单元 + E2E + 集成）
python3 -m pytest tests/unit/ -v
python3 -m pytest tests/e2e/ -v
python3 -m pytest tests/integration/ -v

ruff check rana/scripts/       # 代码检查
```

## 开发

1. 编辑 `rana/` 源码
2. 运行 `python3 -m pytest tests/ -v` — 保持全绿
3. 同步安装副本：`cp -r rana/. ~/.agents/skills/rana/`

详见 [AGENTS.md](./AGENTS.md)。

## 许可

内部工具，未公开发布。