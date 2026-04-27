# Full Mode 流程

## 三阶段概览

| Stage | 名称 | 输出章节 | 核心动作 | 详情指引 |
|-------|------|---------|---------|---------|
| 1 | 诊断层 | 二（用户）、三（现状）、四（业务目标） | 找病因 + 按需协作 | `references/stage-1-diagnosis.md` |
| 2 | 方案层 | 五（策略）、六（方案与验证）、七（风险）、八（各角色关注） | 开药方 + 按需协作 | `references/stage-2-solution.md` |
| 3 | 提炼层 | 一（概述）+ 总结 | 倒推提炼 + 按需协作 | `references/stage-3-refine.md` |

## 四段式输出结构

每个 Stage 结束时执行四段式输出。通用结构见 `references/collaboration-protocol.md` §四段式独立消息通用结构

## 通用规则

- 各 Stage 均可按需触发协作讨论（缺口/疑点/批判反驳）
- 协作讨论为多轮对话（人在环中），规范见 `references/collaboration-protocol.md`
- P0 缺口规则见 `references/p0-gates.md`
- 缺口补齐后不重新输出报告本体，仅输出确认

## 多功能需求处理

当 PRD 包含多个独立功能点时：

- **Stage 1**：识别功能点清单，向用户确认功能边界
- **Stage 2**：协作讨论按功能点逐项澄清
- **Stage 3**：功能点分节仅在六、需求清单中体现；五、七、八章节保持整体输出

P0 缺口按功能点独立判断。

## 质量验证（仅 Full Mode）

Stage 3 完成后，运行质量门禁校验脚本验证输出完整性：

```bash
python3 rana/scripts/quality-validator.py <分析目录> [--score]
```

**Quick Mode 不执行质量验证**（Quick Mode 不产生 final-analysis.md，不符合校验前提）。

校验内容：文件结构、来源追溯、P0 小节完整性、章节完整性、模糊表述。详见 `references/quality-validator.md`。

## 输出文件

- `final-analysis.md` — Full Mode 主输出（8章+总结，使用 `assets/analysis-template-full.md`）
- `change-log.md` — 协作记录
- `quality-report.md` — AI 自评