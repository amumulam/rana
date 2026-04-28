## v0.4.2-rc1

- 87a71f6 feat: CI pytest quality gate — push 和 MR 自动跑 pytest，测试失败则阻止发布
- 87a71f6 feat: CI→CD 串联 — auto-release 通过 needs 依赖 pytest，形成质量门禁
- d61018c feat: Skill 安装同步自动化 — tag 发布后 rsync 到 ~/.agents/skills/ 和 ~/.openclaw/skills/
- d61018c feat: Mattermost 版本发布通知 — Release 创建后自动发送 changelog 到频道
- 526e70e feat: Release description 支持 RELEASE_NOTE.md 手写优先、机械 changelog fallback
- b0fe209 fix: CI tag regex 支持 rc/alpha/beta 预发布标识
- ae1820e fix: changelog 脚本改用 echo+写文件替代 printf（防止 commit message 中 % 被误解释）
- ae1820e fix: JSON payload 构建改用 jq 从文件读取，避免 shell 变量嵌入多行文本
- 4a7740e fix: GIT_DEPTH 改为 per-job 设置（pytest 默认 depth 20，release/notify 用 depth 0）
- 4a7740e fix: 移除 Package Registry 上传步骤（403 Forbidden，Skill 靠 rsync 分发无需 Package）