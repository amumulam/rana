## v0.4.2-rc1

feat: CI pytest quality gate — push 和 MR 自动跑 pytest，测试失败则阻止发布
feat: CI→CD 串联 — auto-release 通过 needs 依赖 pytest，形成质量门禁
feat: Skill 安装同步自动化 — tag 发布后 rsync 到 ~/.agents/skills/ 和 ~/.openclaw/skills/
feat: Mattermost 版本发布通知 — Release 创建后自动发送 changelog 到频道
feat: Release description 支持 RELEASE_NOTE.md 手写优先、机械 changelog fallback
fix: CI tag regex 支持 rc/alpha/beta 预发布标识
fix: changelog 脚改用 echo+写文件替代 printf（防止 commit message 中 % 被误解释）
fix: JSON payload 构建改用 jq 从文件读取，避免 shell 变量嵌入多行文本
fix: GIT_DEPTH 改为 per-job 设置（pytest 默认 depth 20，release/notify 用 depth 0）
fix: 移除 Package Registry 上传步骤（403 Forbidden，Skill 靠 rsync 分发无需 Package）