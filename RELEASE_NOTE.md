## v0.4.2

### Skill 功能

- Quick Mode 四段式消息呈现 + 术语优化 + 目录重命名（4316bd7）
- 显式嵌入分析方法到 Quick/Full 流程（baacf04）
- file_parser 配置更新：PDF 用 pdf 技能，xlsx/xls 用 xlsx 技能（b7f4d7b）

### CI/CD 

- push 和 MR 自动跑 pytest，测试失败则阻止发布（87a71f6）
- auto-release 通过 needs 依赖 pytest，形成质量门禁（87a71f6）
- CI tag regex 支持 rc/alpha/beta 预发布标识（b0fe209）
- pip install 加超时重试防止下载失败（84464e5）
- sync-wiki 自动同步 wiki 到 GitLab Wiki（HTTPS + Access Token）（f4fa670）
- Skill 安装同步自动化 — tag 发布后 rsync 到安装目录（d61018c）
- changelog 脚本改用 echo+写文件替代 printf（防止 % 被误解释）（ae1820e）
- JSON payload 构建改用 jq 从文件读取，避免 shell 变量嵌入多行文本（ae1820e）
- GIT_DEPTH 改为 per-job 设置（pytest 默认 depth 20，release/notify 用 depth 0）（4a7740e）
- 移除 Package Registry 上传步骤（403，Skill 靠 rsync 分发）（4a7740e）