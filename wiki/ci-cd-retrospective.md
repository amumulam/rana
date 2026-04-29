# CI/CD Pipeline 建设复盘与认知

> rana 项目从"手动发布"到"Tag 推送即自动发布"的过程中，连续失败 5 次，每次修完一个 bug 又冒出新的。这篇文档按概念而非时间线组织，解释每个问题的机制、为什么会遇到、正确的做法是什么。Pipeline 的逐轮事实记录附在末尾。

---

## 概念：CI 脚本中的多层转义问题

CI/CD pipeline 脚本涉及多层语法嵌套，每一层有不同的特殊字符和转义规则。数据从 git log 经过这些层到达 GitLab API，每一层都可能破坏数据：

```
数据源（git log）
   ↓  第1层：Shell 语法（$、\、%、单双引号规则）
   ↓  第2层：YAML 语法（花括号、冒号、缩进规则、单引号保护规则）
   ↓  第3层：JSON 语法（双引号、转义反斜杠、Unicode）
   ↓  第4层：curl 参数（--data 的引号规则）
   ↓  目的地（GitLab API / Mattermost Webhook）
```

在某一层加转义只能解决该层的特定字符问题。由于 git log 中的 commit message 可以包含任意字符，逐层打补丁无法覆盖所有情况。**解决方向是改变数据流架构——让数据通过文件传递而非穿过多层 shell 变量转义。**

---

## 一、printf 不能用于输出不可控内容

### 机制

`printf` 的第一个参数是格式字符串，不是普通字符串。格式字符串中的 `%` 是特殊字符——`%d`、`%s`、`%f` 是格式 specifier，`%` 后面跟非格式字符（如 `50% ` 中的 `% `）是非法格式，会报 `invalid format` 错误。

因此只要是 `printf` 输出包含不可控源（git log、用户输入、环境变量）的文本，就会有 `%` 被解释为格式 specifier 的风险。

### 发生的情况（printf 部分）

`generate-changelog.sh` 用 `printf "$HEADER"` 输出 changelog。本地测试正常，因为测试用的最近几个 commit message 中没有 `%`。CI 中脚本读取了完整的 git history，命中了这条 commit message：

```
docs: update wiki image style — rounded 16px, 1px 20% border, 50% caption
```

`printf` 把 `50%` 的 `%` 解释为格式 specifier 前缀，后面跟了空格而非合法格式字符，报 `invalid format`。脚本设了 `set -e`，立即退出。`$()` 命令替换捕获到非零退出码，整个 CI job 失败。

**Pipeline Round 4** 的完整错误日志：
```
$ CHANGELOG=$(sh scripts/generate-changelog.sh $CI_COMMIT_TAG)
sh: % border, 50% caption
• 448efd5 docs: add image captions and border-radius to wiki images
...
: invalid format
ERROR: Job failed: exit code 1
```

日志里的 `sh:` 前缀让错误看起来像是 shell 试图执行 commit message 作为命令。实际原因是 `printf` 的格式错误导致脚本退出，错误信息中混入了 commit message 文本。

### 为什么本地测试没发现

- 本地只测试了最近几个 commit 的 changelog 生成，这些 commit message 中没有 `%`
- CI 用完整 git history（GIT_DEPTH: 0），历史 commit 中包含 `%` 的 message 被扫到了
- 本地测试的样本太小，无法覆盖真实数据中的所有字符

### Round 3 的误诊

在 `printf` 问题暴露之前，Round 3 中看到类似错误时，误诊为"脚本路径在 `cd` 后找不到"。做了 MR !9 把 changelog 生成移到 `cd` 之前。顺序调整的结果是合理的（changelog 确实应该在项目根目录生成），但没有解决 `printf` 的根因，导致 Round 4 再次报同样的错误。

误诊原因：CI 日志的错误信息看起来像是"脚本找不到"（`sh:` 前缀 + commit message 片段）。如果逐行分析日志，会发现错误来自脚本内部执行而非文件路径。

### 做法

CI 脚本中，`printf` 只可用于格式字符串完全由自己控制的场景（如 `printf "%s\n" "hello"`）。不要用 `printf` 输出可能含不可控内容的变量。`echo` 不解释格式 specifier，在 CI 脚本中是更安全的选择。

修后的脚本用 `echo` 逐行输出 + 写文件替代了 `printf "$HEADER"`：

```sh
# 旧（危险）
HEADER="${HEADER}\n### ✨ Features\n${FEATS}\n"
printf "$HEADER"

# 新（安全）
echo "### ✨ Features"
echo "$FEATS"
echo ""
```

---

## 二、Shell 变量不适合承载多行 JSON 数据

### 机制

Shell 变量赋值和 JSON 字面量拼接涉及多层独立的转义规则，叠加后很难管理：

| 层 | 特殊字符 | 转义方式 |
|----|----------|----------|
| Shell 单引号 | 所有字符都是字面量 | 无需转义，但无法嵌入变量 |
| Shell 双引号 | `$`、`\`、`"`、`!` | `\` 转义 |
| Shell `$()` | 会吃掉尾换行 | 无法挽救 |
| YAML 单引号 | `'` 需要双写 `'` | `'` → `''` |
| YAML 双引号 | `\`、`"` | `\` 转义 |
| JSON 双引号 | `"`、`\` | `\` 转义 |
| curl --data | 取决于引号类型 | 与 shell 规则叠加 |
| GitLab CI `'` 前缀 | 阻止 YAML 变量展开 | 只影响 YAML 层 |

一个包含双引号、换行、`\n`、emoji 的 changelog 文本，要安全穿过"Shell → YAML → JSON → curl"四层到达 API，需要同时满足所有层的转义规则。任何一层遗漏都会导致数据断裂。

### 发生的情况：
```yaml
script:
  - CHANGELOG=$(sh scripts/generate-changelog.sh $CI_COMMIT_TAG)
  - 'curl --header "JOB-TOKEN: $CI_JOB_TOKEN" --header "Content-Type: application/json"
     --data "{\"tag_name\":\"$CI_COMMIT_TAG\",\"name\":\"rana $CI_COMMIT_TAG\",
              \"description\":\"$CHANGELOG\"}"
     "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/releases"'
```

这条路径上的失败点：

1. `$()` 吃掉尾换行：`CHANGELOG` 变量的最后一行换行被吞掉，JSON decoding 可能出错
2. 多行文本嵌入 JSON 字面量：`$CHANGELOG` 是多行文本，直接放入 `"description":"$CHANGELOG"` 会导致 JSON 中出现未转义的换行符（JSON 规范要求换行必须是 `\n`）
3. 双引号冲突：changelog 中的双引号（commit message 可能含 `"fixed bug"`）与外围 JSON 的双引号冲突
4. `\n` 双重语义：shell 中的 `\n` 是字面两字符 `\`+`n`，JSON 中的 `\n` 是换行 escape——同一字符在两层中有不同含义
5. emoji：git log 输出中的 emoji（如 ✨🐛📦）可能在 curl `-d` 传输时被截断或误编码

### 尝试的中间方案（均失败）
```yaml
- PAYLOAD=$(jq -n --arg tag "$CI_COMMIT_TAG" --argjson desc "$CHANGELOG" \
    '{"tag_name":$tag,"name":$name,"description":$desc}')
```

失败原因：jq 表达式中的 `{`、`$tag`、`$name`、`$desc` 和字符串拼接 `+` 让 YAML 解析器混乱。Python YAML 库报 `ParserError`：
```
yaml.parser.ParserError: while parsing a block mapping
  in ".gitlab-ci.yml", line 48, column 7
expected <block end>, but found '<scalar>'
```

即使加 GitLab CI 的单引号保护（`'` 前缀阻止 YAML 变量展开），YAML 解析器仍然无法正确处理 jq 语法中的花括号和变量引用。

**方案 B**：分离 changelog→JSON 转换到单独步骤
```yaml
- CHANGELOG=$(jq -Rs . changelog.txt)
- PAYLOAD=$(jq -n --arg tag ... --argjson desc "$CHANGELOG" ...)
```

失败原因：`$CHANGELOG` 是 `jq -Rs` 输出的 JSON 字面量字符串（带双引号包围），把它作为 `--argjson` 的参数传入另一个 `jq` 命令时，shell 的变量展开与 jq 的参数解析产生冲突——当字符串中包含 shell 特殊字符时，展开结果被 shell 重新解释。

### 最终方案：数据走文件传递

```
旧路径（数据穿过多层 shell 变量转义）：
  git log → printf → $CHANGELOG → JSON字面量 → curl --data "$PAYLOAD"

新路径（数据走文件，不经过 shell 变量）：
  git log → echo → changelog.txt → jq --rawfile → payload.json → curl --data @payload.json
```

新路径的每个环节：

1. `generate-changelog.sh` 用 `echo` 写内容到 `changelog.txt`（不用 `printf`，不用 shell 变量拼接）
2. `build-release-payload.sh` 用 `jq --rawfile desc changelog.txt` 从文件直接读取原始文本，构建 JSON 对象，输出到 `payload.json`。`--rawfile` 是关键——它让 `jq` 从文件读取未经过任何 shell 处理的原始内容
3. `curl --data @payload.json` 从文件读取整个 HTTP body，不需要任何 shell 引号或转义

CI 中的 YAML 只需要写一行简单调用：
```yaml
- sh scripts/generate-changelog.sh "$CI_COMMIT_TAG" changelog.txt
- sh scripts/build-release-payload.sh "$CI_COMMIT_TAG" changelog.txt payload.json
- 'curl --header "JOB-TOKEN: $CI_JOB_TOKEN" --header "Content-Type: application/json" --data @payload.json "${CI_API_V4_URL}/projects/${CI_PROJECT_ID}/releases"'
```

Shell 的职责是调用命令和传递文件路径，不适合承载多行、多格式、多编码的数据流。当你在 shell 里做字符串拼接、JSON 构建、转义管理时，应该考虑换用文件传递数据。

---

## 三、复杂 shell 逻辑不要内联在 YAML 中

### 本质

YAML 是数据序列化格式，不是编程语言。把编程逻辑（jq 表达式、字符串拼接、条件判断）内联在 YAML 的 script 字段中，会遇到两类问题：

1. 语法冲突：编程逻辑中的 `{}`、`$var`、`+`、`()` 与 YAML 的映射、字符串、缩进规则冲突
2. 可维护性不足：YAML 没有变量、函数、注释块等基本抽象能力，内联逻辑只能硬编码

### 我们的经历

在修复 Shell→JSON 问题时，尝试把 jq JSON 构建逻辑写在 `.gitlab-ci.yml` 的 script 字段中：

```yaml
- PAYLOAD=$(jq -n --arg tag "$CI_COMMIT_TAG" --argjson desc "$CHANGELOG" --arg url "${CI_PROJECT_URL}/-/releases/$CI_COMMIT_TAG" '{"text":("rana " + $tag + " released!\n\n" + $desc + "\n\nRelease: " + $url)}')
```

这一行超过 200 个字符，包含：
- YAML 的单引号保护规则（`'` 前缀）
- Shell 的 `$()`、`"$VAR"`、`\n`
- jq 的 `--arg`、`--argjson`、`$变量`引用、`+` 字符串拼接、`()` 迎合表达式、`{}` 对象构造
- GitLab CI 变量 `$CI_COMMIT_TAG`、`$CI_PROJECT_URL`

Python YAML 解析器直接拒绝：
```
yaml.parser.ParserError: expected <block end>, but found '<scalar>'
```

LSP 工具也持续误报 "Missing closing quote"，因为 YAML 解析器无法理解 jq 表达式中的花括号和 `$` 变量引用。

### 做法

超过 20 个字符的复杂 shell 逻辑，抽到 `.sh` 脚本文件里。YAML 只写一行调用：`sh scripts/xxx.sh arg1 arg2`。

这样做的好处：
1. 脚本文件可以用 POSIX shell 语法自由表达，不受 YAML 规则约束
2. YAML 行简短，没有转义嵌套问题
3. 脚本文件可以独立测试（`sh scripts/build-release-payload.sh v0.4.1 changelog.txt payload.json`），不需要先推 CI 再看结果

我们最终的做法：新增 `scripts/build-release-payload.sh` 和 `scripts/build-mattermost-payload.sh`，CI 中每个 script 只写 3 行简单调用。

---

## 四、本地环境和 CI 环境存在结构性差异

### 本质

开发者本地与 CI（Docker executor）的环境差异是结构性的，不是表面的：

| 维度 | 本地 | CI（Docker executor） |
|------|------|----------------------|
| Git history | 完整（所有分支、所有 tag、所有 commit） | Shallow clone（默认最近 20 个 commit） |
| Commit message 采样 | 开发者最近写的几个消息 | 全部历史 commit（包括其他人写的、可能含任何字符） |
| 运行环境 | macOS / Linux 完整系统 | 精简 alpine/python-slim 容器，缺失很多工具 |
| 工作目录 | 当前项目目录，所有文件都在 | 从零 clone 的新目录 |
| Shell 版本 | zsh/bash（可能有本地 alias） | busybox ash（功能受限） |
| 网络环境 | VPN + 内网直接访问 | 容器内网络，需 DNS 解析 |
| 并发 | 开发者的终端独占 | Runner 队列排队，可能等 5-10 分钟 |

这些差异意味着：在本地通过的测试，只是验证了脚本在本地环境正确，不是验证了脚本在 CI 环境正确。

### 发生的情况：本地 `generate-changelog.sh` 正常运行，因为本地有完整的 git history。CI 默认 GIT_DEPTH=20，shallow clone 只能看到最近 20 个 commit。`git log v0.4.1..v0.4.2-rc1` 需要对比两个 tag 之间的所有 commit，但 shallow clone 中 v0.4.1 可能在 20 个 commit 范围之外，`git log` 报错或返回空结果。

Commit message 采样差异：本地测试 changelog 脚本时，只在最近几个 commit 上运行，这些 commit 都是开发者自己写的，message 格式规范且不含特殊字符。CI 用 GIT_DEPTH=0 拉取完整 history 后，历史中包含了 `%`、emoji、中文引号等各种字符。

Package Registry 403：本地开发时参照了 GitLab 官方文档的"Release + Package"模式，没有考虑自托管实例可能禁用了 Generic Package Registry。这个差异只在实际 curl 上传时才暴露。

### 做法

CI 脚本的验证需要在模拟 CI 环境中完成，不能依赖本地通过的测试。具体做法：

- 测试 changelog 脚本时，用 `GIT_DEPTH: 0` 确保完整 history 被扫到
- 测试 JSON 构建脚本时，故意输入包含 `%`、`"`、`\n`、emoji 的内容
- 测试 curl API 调用时，确认目标 GitLab 实例的 feature 可用性，而不是假设官方文档描述等于你的实例配置

---

## 五、GIT_DEPTH 按需设置，不要全局一刀切

### 本质

GitLab Runner 的 `GIT_DEPTH` 变量决定了 clone 深度——多少 commit 和 tag 被拉取到 CI 的工作目录中。默认值是 20（只拉最近 20 个 commit）。

默认值对大多数 CI job 足够（跑测试、lint、编译都不需要 git history），但依赖 `git log`、`git diff`、`git tag --list`、`git archive` 的 job 需要完整的 commit graph，shallow clone 下这些命令无法正确工作。

GIT_DEPTH 是一个权衡：浅 clone 让大多数 job 更快，但需要 git history 的 job 必须显式请求完整 clone。

### 我们的经历

初始代码全局设了 `GIT_DEPTH: 0`（所有 job 全量 clone）。这让 auto-release 拥有完整 history，changelog 正常。副作用是 pytest 每次也要全量 clone——在 Docker executor（无 pip cache）的环境下，pytest 约 5 分钟，其中 pip install 占 3 分钟，全量 clone 又增加了传输时间。

修复方案：移除全局 `GIT_DEPTH: 0`，只在真正需要 git history 的 job 上设 per-job `GIT_DEPTH: 0`：

```yaml
pytest:
  # 不设 GIT_DEPTH → 使用默认 depth=20 → 足够跑测试

auto-release:
  variables:
    GIT_DEPTH: 0    # 需要 git log 对比 tag 之间的完整 history

notify-mattermost:
  variables:
    GIT_DEPTH: 0    # 同理，需要生成 changelog
```

**Pipeline #47 验证**：pytest 在默认 depth 下成功通过（~5 分钟），auto-release 和 notify-mattermost 在 GIT_DEPTH=0 下成功运行。

### 做法

GIT_DEPTH 按 job 的实际需要设置：跑代码的 job 用默认值，跑 git history 的 job 用 GIT_DEPTH: 0。全局全量 clone 是浪费。

---

## 六、不要为不存在的需求加 Pipeline 功能

### 机制

CI/CD pipeline 的每个 job、每行配置都有维护成本。每加一个功能，就多一个可能在 CI 环境中失败的东西。

判断一个功能是否需要加入 pipeline：这个功能是否服务于目标交付物的分发？如果不是，就是不必要的复杂度。

### 发生的情况

auto-release 最初的设计参照了 GitLab 官方文档的推荐模式，包含 Package Registry 上传步骤：

1. `git archive` 打包源代码为 zip
2. `curl upload` 上传 zip 到 Generic Package Registry
3. 在 Release 页面添加指向 Package 的下载链接

这个设计在两个地方失败：

1. `git archive` 脱离 git 目录：先 `cd /tmp/rana-release` 再执行 `git archive`，脱离了项目 git 目录，报 `fatal: not a git repository`。
2. Package Registry 403 Forbidden：上传到 Generic Package Registry 时 curl 返回 403。原因是 GitLab 实例的 Package Registry 未启用或 CI_JOB_TOKEN 没有写入权限。

重新审视需求：rana Skill 的分发方式是什么？

答案是 rsync 文件复制——CI 的 sync-skill job 直接把 `rana/` 目录 rsync 到 `~/.agents/skills/rana/`（本地）和 `~/.openclaw/skills/rana/`（服务器）。agent 直接从文件系统读取 Skill，不需要从 Package Registry 下载 zip。

Package Registry 上传不服务于实际分发方式，增加了 pipeline 的复杂度（5 行 script + 2 个额外包安装），但没有增加任何实际价值。

删除后，auto-release script 从 7 行简化到 4 行。

### 做法

往 pipeline 加功能前，先明确：这个功能服务于什么？交付物是什么？谁消费它？如果答案是"参照了官方文档但实际没人用"，就不该加。

---

## 七、错误诊断必须基于完整日志

### 机制

CI job 失败后的日志通常很长（apk 安装、pip 安装、before_script 输出混在一起），关键错误信息往往只有一行。CI 日志中的错误信息含义常与表象不同：

- `sh: some text` 不等于"shell 试图执行 some text"，可能是 `printf` 格式错误的副作用
- `fatal: not a git repository` 不等于"git 没在工作目录"，可能是 `cd` 后的命令脱离了 git 仓库
- `sh: script not found` 不等于"脚本文件不存在"，可能是脚本执行失败导致的错误信息被误解

### 发生的情况

Round 3 中，看到 CI 日志错误信息后，直接下结论认为"changelog 脚本在 cd 后找不到"，做了 MR !9 把 changelog 生成移到 cd 之前。

实际根因是 `printf` 格式 bug（见第一节），与文件路径无关。MR !9 的修复让顺序更合理，但没有解决错误，导致 Round 4 再失败。

正确的诊断流程应该是：

1. 读完整的 auto-release job 日志，不只看报错行
2. 找到 `CHANGELOG=$(sh scripts/generate-changelog.sh ...)` 这一行的完整输出
3. 注意 `sh:` 前缀后面是 commit message 内容片段，而非文件路径
4. 判断：脚本被执行了（输出含 commit message），而非没找到文件
5. 查看脚本代码，发现 `printf "$HEADER"` 是可疑点
6. 用 `printf "50% text"` 在终端手动测试，确认 `invalid format` 错误

这样做只需要一个 MR，而不是两个，可以省掉 Round 3 的等待时间。

### 做法

诊断流程：读完整日志 → 定位出错命令行 → 分析该行的完整输入输出 → 确认是"文件不存在"还是"执行失败" → 本地复现 → 找到根因 → 再修复。猜测的修复可能碰巧合理（MR !9 的顺序调整确实更合理），但根因没找到就会再来一轮失败。

---

## 八、Runner 基础设施约束不是代码问题

### 机制

CI Runner 的并发数、executor 类型、缓存策略、网络能力是基础设施配置，CI 脚本无法改变这些： `concurrent=1`：Runner 只同时跑一个 job，多 pipeline 排队等待
- Docker executor：每个 job 从全新容器启动，没有 pip cache、没有 docker layer cache
- 无 cache mount：每次 pip install 从网络下载所有包

这些约束导致 pytest 每次跑 ~5 分钟（3 分钟 pip install + 2 分钟 pytest），多 pipeline 排队时更慢（我们的 pipeline 从触发到完成平均等等 8-15 分钟）。

### 为什么不能用代码解决

pytest 的 pip install 时间无法通过代码优化（alpine 容器每次全新）。Runner 的 concurrent=1 无法通过 `.gitlab-ci.yml` 改变（需要改 Runner 的 config.toml）。Docker executor 的无缓存无法通过 CI 变量解决（需要 Runner config 的 volumes mount）。

这些都是运维层面的配置，需要改 `~/.gitlab-runner/config.toml`，而非 `.gitlab-ci.yml`。

### 做法

区分代码问题和基础设施问题。代码问题用 MR 解决，基础设施问题用 Runner 配置解决。不要试图用 CI 脚本优化来弥补基础设施瓶颈。

---

## 附录：Pipeline 逐轮记录

以下是 5 轮 Pipeline 的完整事实记录，作为上述认知的证据材料。

### Round 1：Tag Regex 不匹配

- **时间**：2026-04-28 ~07:00
- **触发**：`git tag v0.4.2-rc1 && git push gitlab v0.4.2-rc1`
- **auto-release rule**：`/^v\d+\.\d+\.\d+[a-z]?$/`
- **结果**：

| Job | 状态 |
|-----|------|
| pytest | ✅ success |
| auto-release | ❌ **未触发**（regex 不匹配） |
| SAST/Secret Detection | ✅ success |

- **修复**：MR !7 — regex 改为 `/^v\d+\.\d+\.\d+(-(rc|alpha|beta)\d+)?[a-z]?$/`
- **对应**：第四节（本地不测试 regex 对边缘 tag 的匹配）

### Round 2：Shallow Clone + git archive 路径

- **时间**：2026-04-28 ~07:30
- **触发**：重建 v0.4.2-rc1 on 新 commit（含 !7 修复）
- **结果**：

| Job | 状态 |
|-----|------|
| pytest | ✅ success |
| auto-release | ❌ **failed** — `fatal: not a git repository` |
| SAST/Secret Detection | ✅ success |

- **根因叠加**：(A) GIT_DEPTH 默认 20 → changelog 需要完整 history (B) `cd /tmp/` 后 `git archive` 脱离 git 目录
- **修复**：MR !8 — 全局 GIT_DEPTH:0 + 调整 script 顺序
- **对应**：第五节（GIT_DEPTH 需 per-job）、第四节（本地 vs CI 差异）

### Round 3：误诊为路径问题

- **时间**：2026-04-28 ~08:00
- **触发**：重建 v0.4.2-rc1 on 新 commit（含 !8 修复）
- **结果**：

| Job | 状态 |
|-----|------|
| pytest | ✅ success |
| auto-release | ❌ **failed** — `sh: ... : invalid format` |

- **误诊**：错误信息看起来像"脚本路径找不到"，实际是 `printf` 格式 bug
- **修复**：MR !9 — changelog 生成移到 cd 前（顺序修复正确，根因未解决）
- **对应**：第七节（诊断必须基于完整日志）

### Round 4：printf 格式错误暴露

- **时间**：2026-04-28 ~08:15
- **触发**：重建 v0.4.2-rc1 on 新 commit（含 !9 修复）
- **完整错误日志**：
```
$ CHANGELOG=$(sh scripts/generate-changelog.sh $CI_COMMIT_TAG)
sh: % border, 50% caption
• 448efd5 docs: add image captions and border-radius to wiki images
• 91e1ff7 docs: use HTML img tags for wiki image sizing (GitLab compatible)
• 1842d3e docs: update wiki with Mattermost guide, screenshots, invite link\n\n### 📦 Other\n
• 87a71f6 Merge branch 'feat/ci-pytest-stage' into 'main'
...
: invalid format
ERROR: Job failed: exit code 1
```
- **根因**：commit message `50% caption` 中的 `%` 被 `printf` 解释为格式 specifier
- **对应**：第一节（printf 禁用于不可控内容）

### Round 4+并行：MR !10 CI 优化

- **时间**：2026-04-28 ~08:20
- **内容**：
  - 移除 Package Registry 上传（403 Forbidden，Skill 靠 rsync 分发）
  - GIT_DEPTH 从全局改为 per-job
- **对应**：第六节（不加不存在需求的功能）、第五节（GIT_DEPTH per-job）

### Round 5：最终验证通过

- **时间**：2026-04-28 ~08:45
- **触发**：重建 v0.4.2-rc1 on HEAD（含 !10 + !11 修复）
- **Pipeline #47 结果**：

| Job | 状态 | 说明 |
|-----|------|------|
| pytest | ✅ success | 默认 GIT_DEPTH=20，~5分钟 |
| auto-release | ✅ **success** | 首次成功创建 GitLab Release |
| notify-mattermost | ✅ **success** | 首次成功发送通知 |
| sync-skill | ✅ success | rsync 到两个安装目录 |
| sync-wiki | ❌ failed | SSH key `error in libcrypto` |

- **sync-wiki 失败**：CI Variable `SSH_PRIVATE_KEY` 格式与 alpine 的 OpenSSH 10.2 不兼容。`changes: wiki/**` 规则在 tag pipeline 上可能始终评估为 true（GitLab `changes` 在无 base ref 时无法判断变更范围）
- **核心发布流程已完整走通**

### Round 6：sync-wiki 排查与放弃

- **时间**：2026-04-28
- **尝试方案**（均失败）：
  1. `ssh-add` stdin 方式 + PEM 格式旧 key → OpenSSH 10.2 报 `error in libcrypto`
  2. 改用 OpenSSH 格式 ed25519 新 key → stdin `ssh-add` 仍报 `error in libcrypto`
  3. 改用文件加载方式 (`echo > file && chmod 600 && ssh-add file`) → 同报 `error in libcrypto`
  4. 改用 File-type Variable → 默认权限 0666，`chmod 600` 后权限解决但内容格式仍被破坏
  5. File-type textarea 对 SSH key 的多行逐行格式不可控（可能做 HTML entity 转义、BOM、CRLF 处理）
- **根因**：GitLab CI Variable 的 web UI 编辑器无法保证写入容器的文件逐行完整、无编码污染。SSH 私钥要求精确的7行 openSSH 格式，任何编码偏差都会导致 `ssh-add` 拒绝加载
- **结论**：放弃 sync-wiki SSH 自动化，改为纯手动 `bash scripts/sync-wiki.sh wiki`

### Round 7：RELEASE_NOTE.md 机制

- **时间**：2026-04-28
- **变更**：
  - `build-release-payload.sh`：如果 RELEASE_NOTE.md 存在就用它，否则 fallback 到 changelog.txt
  - `.gitlab-ci.yml`：auto-release job 确保可读取 RELEASE_NOTE.md
  - `AGENTS.md`：发布流程新增"写 RELEASE_NOTE.md"步骤
- **Release Note 格式要求**：
  - 按功能模块分类（`### CI/CD 流水线`、`### 发布与通知` 等）
  - 每条变更描述后括号标注 commit hash（如 `push 和 MR 自动跑 pytest（87a71f6）`）
  - 聚焦重点变更，不需要罗列每个 commit
- **结论**：Release description 支持手写优先

### Round 8：sync-wiki HTTPS + Access Token 方案成功

- **时间**：2026-04-29
- **方案**：改用 HTTPS + Project Access Token 推送 wiki，不再依赖 SSH
- **踩坑**：
  1. `bash scripts/sync-wiki.sh` → alpine 没有 bash，改用 `sh`
  2. Project Access Token Role 为 Guest → git push 403 Forbidden
  3. 改为 **Maintainer** + **write_repository** scope → 成功
- **结论**：SSH 方案在 GitLab CI 环境不可行，HTTPS + Project Access Token（Role: Maintainer）是可行方案。sync-wiki 自动化恢复。

---

## 附录：MR 合入记录

| MR | Commit | 内容 | 解决问题 |
|----|--------|------|----------|
| !6 | d76972f + d61018c | pytest + needs + sync-skill + mattermost 初始架构 | 基础搭建 |
| !7 | 0877f7e | Tag regex 支持 rc/alpha/beta | Round 1 |
| !8 | f40a54e | GIT_DEPTH:0 全局 + git archive 路径修复 | Round 2 |
| !9 | 5383d76 | changelog 生成移到 cd 前 | Round 3（误诊，顺序调整合理但根因未解） |
| !10 | 5341635 | 移除 Package Registry + GIT_DEPTH per-job | 并行优化 |
| !11 | ae1820e | echo+写文件替代 printf + jq payload builder 脚本 | Round 4+5（根因修复） |

---

## 附录：glab CLI 的注意点

在开发过程中遇到的 glab CLI 相关问题：

| 问题 | 说明 | 正确用法 |
|------|------|----------|
| `--squash` vs `-s` | glab 版本不同语法不同，有的版本 `--squash` 不认 | 先 `glab mr create --help` 确认当前版本支持的 flag |
| `--fill` 在非交互环境不可用 | 非交互 CLI 无法打开编辑器填充 title/description | 使用 `--title` + `--description` 显式指定 |
| `--source-branch` 必需 | glab 有时自动判断错误，报 `source_branch is invalid` | 显式 `--source-branch fix-xxx --target-branch main` |
| `glab mr merge` 必须在 main 目录下 | 在 worktree 目录下 merge 后 pull，worktree HEAD 不更新 | 切回 main 项目目录再执行 merge |