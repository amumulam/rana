## v0.4.2-rc1

### CI/CD 流水线

- push 和 MR 自动跑 pytest，测试失败则阻止发布（87a71f6）
- auto-release 通过 needs 依赖 pytest，形成质量门禁（87a71f6）
- CI tag regex 支持 rc/alpha/beta 预发布标识（b0fe209）

### 发布与通知

- Skill 安装同步自动化 — tag 发布后 rsync 到安装目录（d61018c）
- Mattermost 版本发布通知 — Release 创建后发送 release note 到频道（d61018c）
- Release description 支持 RELEASE_NOTE.md 手写优先、机械 changelog fallback（526e70e）

### CI 脚本修复

- changelog 脚本改用 echo+写文件替代 printf（防止 % 被误解释）（ae1820e）
- JSON payload 构建改用 jq 从文件读取，避免 shell 变量嵌入多行文本（ae1820e）
- GIT_DEPTH 改为 per-job 设置（pytest 默认 depth 20，release/notify 用 depth 0）（4a7740e）
- 移除 Package Registry 上传步骤（403，Skill 靠 rsync 分发）（4a7740e）