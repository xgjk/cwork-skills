# GitHub Issues 本地快照

用于把仓库 Issues 拉到本地 JSON，供 Agent 对照代码与文档做分析（见根目录 `.cursorrules` §6）。

## 拉取

可将 `GITHUB_TOKEN` 写在**仓库根目录** `.env`（已 gitignore），在项目根执行：

```bash
python github-issues/fetch_issues.py
```

或显式设置环境变量（勿把真实 token 写进仓库）：

```bash
# Windows PowerShell
$env:GITHUB_TOKEN = "…"
python github-issues/fetch_issues.py
```

- 默认仓库：`xgjk/cwork-skills`（可用环境变量 `GITHUB_REPOSITORY=owner/repo` 覆盖）
- 输出：`snapshot-open.json`、`snapshot-closed.json`（默认不提交，见根 `.gitignore`）

## 关闭 Issue（无 gh CLI 时）

与拉取脚本共用 `GITHUB_TOKEN` / `GH_TOKEN` 与 `GITHUB_REPOSITORY`；Token 需要对目标仓库具备 **Issues 写权限**。

```bash
python github-issues/close_issue.py 30
python github-issues/close_issue.py 30 --comment "已修复，见提交 abc123"
python github-issues/close_issue.py --issue 30 --issue 31 -c "批量关闭说明"
```

关闭前若带 `--comment`（或 `--comment-file`），会先发表评论再 `state=closed`。成功时 stdout 为 JSON。

## CWork 冒烟自测（改 workflow 后）

在仓库根目录、已配置 `CWORK_APP_KEY` 时：

```bash
python github-issues/smoke_cwork_api.py
```

会真实调用搜人、草稿列表、正文过短拦截、预览保存（**仅草稿**）、待审列表、5.28 时间窗删除（**极早时间戳，预期删 0 条**）。详见根目录 `.cursorrules` §6。

## 安全

- **不要**把 token 或含 token 的文件提交到 Git。
- `snapshot-*.json` 已忽略；若需共享脱敏摘要，另写人工整理版。
