---
name: cms-cwork-workflow
description: 管理工作协同中的员工查询、汇报处理、待办闭环和任务协作流程。触发词：cwork/CWork/工作协同/发送汇报/发汇报/汇报/申请/周报/待办/任务/催办/搜索员工/查收件箱。
skillcode: cms-cwork-workflow
github: https://github.com/xgjk/cwork-skills/tree/main/cwork-skills/cms-cwork-workflow
dependencies:
  - cms-auth-skills
version: 1.0.5
tools_provided:
  - name: cwork_client
    category: exec
    risk_level: medium
    permission: exec
    description: CWork API共享客户端，封装HTTP请求、认证和所有业务API方法
    status: active
  - name: cwork-search-emp
    category: exec
    risk_level: low
    permission: read
    description: 搜索员工信息（支持模糊查询）
    status: active
  - name: cwork-send-report
    category: exec
    risk_level: medium
    permission: write
    description: 发送工作协同汇报（支持附件）
    status: active
  - name: cwork-query-report
    category: exec
    risk_level: low
    permission: read
    description: 查询汇报（收件箱/发件箱/详情/历史）
    status: active
  - name: cwork-create-task
    category: exec
    risk_level: medium
    permission: write
    description: 创建工作计划/任务
    status: active
  - name: cwork-review-report
    category: exec
    risk_level: medium
    permission: write
    description: 审阅汇报（回复/标记已读）
    status: active
  - name: cwork-query-tasks
    category: exec
    risk_level: low
    permission: read
    description: 查询任务（我的/创建的/团队/详情）
    status: active
  - name: cwork-nudge-report
    category: exec
    risk_level: medium
    permission: write
    description: 催办闭环（识别未闭环/生成催办/发送）
    status: active
  - name: cwork-todo
    category: exec
    risk_level: medium
    permission: write
    description: 待办管理（查询/完成决策/建议/反馈）
    status: active
  - name: cwork-templates
    category: exec
    risk_level: low
    permission: read
    description: 查询汇报模板列表
    status: active
  - name: cwork-report-issue
    category: exec
    risk_level: low
    permission: read
    description: 自动上报问题到 GitHub Issues（需环境变量 GITHUB_TOKEN）
    status: active
---

# cms-cwork-workflow

## 概述

本 Skill 将 CWork（工作协同平台）的完整 API 能力封装为 **9 个意图级编排脚本**，每个脚本独立可执行，Agent 通过 `exec python3 scripts/<name>.py` 调用，JSON 输出到 stdout、错误到 stderr。

**设计原则**：
- **Agent-First**：脚本负责 API 编排，Agent 负责 LLM 推理和用户交互
- **幂等安全**：所有写操作支持 `--dry-run` / `--preview-only`
- **零外部依赖**：纯 Python 3.9+，仅需标准库
- **强制封装**：所有 API 调用必须通过脚本，**禁止直接 HTTP/curl 调用**（脚本已内置 URL 编码、参数验证、错误转换、重试机制）

## 快速开始

### 发送汇报（标准 3 步流程）

```
1. 搜索接收人，确认 empId
python3 scripts/cwork-search-emp.py --name "张三"

2. 预览草稿（--preview-only 仅保存草稿，不发送）
python3 scripts/cwork-send-report.py \
  --title "周报" --content-html "<p>内容</p>" \
  --receivers "张三" --preview-only

3. 确认发送
python3 scripts/cwork-send-report.py \
  --title "周报" --content-html "<p>内容</p>" \
  --receivers "张三"
```

### 其他常用命令

```bash
# 查看未读汇报
python3 scripts/cwork-query-report.py --mode unread

# 查看待办列表
python3 scripts/cwork-todo.py list --page-size 20

# 查询我的任务
python3 scripts/cwork-query-tasks.py --mode my
```

---

## 9 个编排命令

### 0. 搜索员工 — `cwork-search-emp.py` ✨ 新增

**意图**：根据姓名/关键词搜索员工 ID 和详细信息

**使用场景**：
1. ✅ **发送汇报前确认接收人** - 确保姓名和 empId 准确
2. ✅ **处理待办时确认发件人** - 查看发件人部门/职位
3. ✅ **创建任务时确认责任人** - 避免姓名错误（重名/错别字）
4. ✅ **催办时确认责任人信息** - 获取完整的员工信息

```bash
# 基础搜索（模糊匹配）
python3 scripts/cwork-search-emp.py --name "张"

# 精确搜索
python3 scripts/cwork-search-emp.py --name "成伟"

# 详细模式（包含 personId、dingUserId 等）
python3 scripts/cwork-search-emp.py --name "刘丽华" --verbose

# 更多结果
python3 scripts/cwork-search-emp.py --name "刘" --max-results 10

# 原始 API 响应（调试用）
python3 scripts/cwork-search-emp.py --name "张" --output-raw
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `--name` / `-n` | ✅ | 员工姓名或关键词（支持模糊匹配） |
| `--max-results` / `-m` | ❌ | 每个类别最多返回数量（默认 5） |
| `--verbose` / `-v` | ❌ | 包含额外信息（personId、dingUserId、corpId） |
| `--output-raw` | ❌ | 输出原始 API 响应（调试用） |

**输出格式**：
```json
{
  "success": true,
  "searchKey": "成伟",
  "inside": [
    {
      "empId": "1514822118611259394",
      "name": "成伟",
      "title": "首席架构师",
      "mainDept": "技术部",
      "status": "在职"
    }
  ],
  "outside": [
    {
      "empId": "1897870576398327809",
      "name": "成伟",
      "title": "",
      "mainDept": "其他",
      "status": "在职",
      "company": "德镁医药"
    }
  ],
  "totalInside": 1,
  "totalOutside": 1
}
```

**注意事项**：
- ✅ **URL 编码已自动处理**（支持中文参数）
- ✅ **模糊匹配**：搜索"刘"会返回所有姓刘的员工
- ✅ **内外部区分**：`inside`（玄关健康员工）+ `outside`（外部联系人/其他公司）
- ⚠️ **重名问题**：可能返回多个同名员工，需要根据部门/职位区分
- 💡 **推荐用法**：发送汇报前先搜索确认 empId

---

### 1. 发送汇报 — `cwork-send-report.py`

**意图**：先**全量**保存/更新草稿（5.23，更新前会拉 5.25 详情合并，避免覆盖丢字段）→ 输出接口返回的**完整**草稿（`draftDetail`）供用户过目 → 仅在用户明确同意后加 `--confirm-send` 调用 **5.27**（`draftBox/submit/{汇报id}`）发出。

**汇报 id 与 `draftId` 字段（避免歧义）**

| 概念 | 含义 | 出现位置 |
|------|------|----------|
| **汇报 id** | 草稿对应的汇报记录主键 | 5.23 返回 `data.id`、5.25 路径与 `draftDetail.id`、5.27 路径 `{id}` |
| **草稿箱记录 id** | 草稿箱列表里一行的主键，**仅用于 5.26 删除** | 5.24 列表项的 `id`（勿与汇报 id 混用） |

**删除草稿（`cwork_client`）**：`delete_draft` 的参数必须是 **5.24 列表项的 `id`**。若只有汇报 id（与列表里的 `businessId` 相同），须调用 **`delete_draft_by_report_id(汇报id)`**；误把汇报 id 传给 `delete_draft` 时，接口可能仍返回 `true` 但列表中草稿未删（见开放 API 5.26 与 5.24 参数说明）。

脚本 stdout 里同时有根字段 **`reportId`** 与 **`draftId`**：二者**不是**两种 id，而是**同一汇报 id 的重复输出**——`draftId` **并非**开放平台文档里的字段名，而是本脚本为衔接历史参数 `--draft-id` 而保留的 JSON 键名，容易让人误以为是「草稿箱 id」。**以 `reportId` / `draftDetail.id` 为准即可**；后续步骤一律传该汇报 id（`--draft-id <汇报id>` 中的值也是它）。

```bash
# 第一步：保存草稿并输出完整预览（默认不会发出）
python3 scripts/cwork-send-report.py \
  --title "周报标题" \
  --content-html "<p>汇报内容</p>" \
  --receivers "张三,李四" \
  --grade "一般"

# 第二步：用户确认 draftDetail 全文后，仅发出（无需再传标题正文）
python3 scripts/cwork-send-report.py --draft-id "<汇报id>" --confirm-send

# 一步保存并发出（仍须显式 --confirm-send，表示已确认预览）
python3 scripts/cwork-send-report.py \
  --title "周报标题" \
  --content-html "<p>汇报内容</p>" \
  --receivers "张三" \
  --confirm-send
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `--title` / `-t` | 保存草稿时 ✅ | 汇报标题（与 `--draft-id --confirm-send` 单独发出时勿传） |
| `--content-html` / `-c` | 保存草稿时 ✅ | 正文 HTML（同上） |
| `--receivers` / `-r` | ❌ | 接收人姓名；更新时若省略则沿用草稿详情中的接收人。**若本次传了姓名**且草稿已有 `reportLevelList`（且未使用 `--report-level-json`），脚本会把解析后的 empId **写回**对应节点的 `levelUserList`，与开放 API「接收人以 `reportLevelList` 为准」一致，避免仅 `summary` 显示新人而 `draftDetail` 仍为旧人 |
| `--cc` | ❌ | 抄送；更新时若省略则沿用草稿中的抄送 |
| `--grade` | ❌ | 优先级：`一般`（默认）/ `紧急` |
| `--type-id` | ❌ | 汇报类型 ID（默认 9999） |
| `--file-paths` | ❌ | 本地附件；**未传且为更新**时沿用草稿已有附件 |
| `--file-names` | ❌ | 附件显示名称 |
| `--plan-id` | ❌ | 关联任务 ID |
| `--report-level-json` | ❌ | JSON 文件路径，`reportLevelList` 数组，覆盖流程节点 |
| `--preview-only` | ❌ | 仅保存+预览；**即使带 `--confirm-send` 也不会发出** |
| `--draft-id` | ❌ | **值为汇报 id**（参数名历史沿用）：更新草稿或配合 `--confirm-send` 仅执行 5.27 |
| `--confirm-send` | ❌ | **必须**在用户确认完整 `draftDetail` 后再加，才会调用 5.27 |

**流程步骤**：
1. **Resolve** — 按姓名搜索员工；本轮回填的姓名参与合并，未填则沿用 5.25 详情中的接收人/抄送
2. **Validate** — 姓名未找到或多匹配时报错终止
3. **Upload** — 若传了 `--file-paths` 则上传并作为附件；否则更新时保留原附件列表
4. **Detail（更新时）** — 若有 `--draft-id`，先 `get_draft_detail` 再与本次参数合并
5. **Draft（5.23）** — 全量 `saveOrUpdate`，返回汇报 id
6. **Preview** — 再次 `get_draft_detail`，stdout 含完整 `draftDetail`（含全文 `contentHtml`）。`summary` 含 `contentPlainText`（全文去标签）、`contentPreview`（极长纯文本时最多约 4000 字截断）、`contentPlainLength`；去标签后不足 50 字时有 `previewWarnings`。`confirmPrompt` 以纯文本展示正文（≤2000 字全文，更长截断），完整 HTML 始终以 `draftDetail.contentHtml` 为准
7. **Submit（5.27）** — 仅当 `--confirm-send` 且非 `--preview-only` 时 `submit`；**不要**再用 5.1 无 id 提交，以免产生重复汇报与孤儿草稿

---

### 2. 查询汇报 — `cwork-query-report.py`

**意图**：收件箱 / 发件箱 / 未读 / 汇报详情 / 节点详情 / **历史上下文检索** ✨ 新增

```bash
# 收件箱（默认）
python3 scripts/cwork-query-report.py --mode inbox --page-size 20

# 未读汇报
python3 scripts/cwork-query-report.py --mode unread --page-size 20

# 发件箱
python3 scripts/cwork-query-report.py --mode outbox

# 单条汇报详情（含回复链）
python3 scripts/cwork-query-report.py --mode detail --report-id <id>

# 节点详情（含审批/建议/反馈状态与处理意见）✨ v3.1.0 新增
python3 scripts/cwork-query-report.py --mode node-detail --report-id <id>

# 历史上下文检索（审批决策支持）✨ v3.1.1 新增
# 查询发件人历史汇报
python3 scripts/cwork-query-report.py --mode sender-history \
  --sender-emp-id <empId> \
  --days 90

# 关键字搜索汇报（客户端过滤）
python3 scripts/cwork-query-report.py --mode keyword-search \
  --keyword "公章" \
  --days 90
```

| 参数 | 说明 |
|------|------|
| `--mode` | `inbox` / `outbox` / `unread` / `detail` / `node-detail` / `sender-history` / `keyword-search` / `pending` / `my-sent` |
| `--page-size` | 分页大小（默认 20） |
| `--page-index` | 页码（默认 1） |
| `--report-id` | 汇报 ID（detail / node-detail 必填） |
| `--sender-emp-id` | 发件人员工 ID（sender-history 必填） |
| `--keyword` | 搜索关键词（keyword-search 必填） |
| `--days` | 回溯天数（sender-history / keyword-search，默认 90） |
| `--report-type` | 汇报类型：1-工作交流 / 2-工作指引 / 3-文件签批 / 4-AI汇报 / 5-工作汇报 |
| `--status` | 已读状态：0=未读 / 1=已读 |
| `--start-date` / `--end-date` | 时间范围（YYYY-MM-DD） |

**输出格式**（sender-history）：
```json
{
  "success": true,
  "data": {
    "senderEmpId": "1514822194347806721",
    "totalReports": 15,
    "recentReports": [
      {
        "id": "2039993163862765570",
        "main": "互联网公司公章借出申请",
        "createTime": "2026-04-03 17:11:48",
        "reportRecordType": 5
      }
    ]
  }
}
```

**输出格式**（keyword-search）：
```json
{
  "success": true,
  "data": {
    "keyword": "公章",
    "total": 5,
    "reports": [
      {
        "id": "2039993163862765570",
        "main": "互联网公司公章借出申请",
        "content": "用于办理工商变更...",
        "createTime": "2026-04-03 17:11:48",
        "sendEmpName": "刘丽华"
      }
    ]
  }
}
```

**输出格式**（node-detail）：
```json
{
  "success": true,
  "data": {
    "id": 汇报ID,
    "main": "汇报标题",
    "content": "汇报正文",
    "writeEmpName": "汇报人",
    "createTime": "发起时间",
    "nodeList": [
      {
        "nodeName": "建议人",
        "type": "建议",
        "status": "已完成",
        "level": 1,
        "userList": [
          {
            "empId": 员工ID,
            "name": "张三",
            "status": "已处理",
            "operate": "建议",
            "content": "建议增加异常处理",
            "finishTime": "2026-04-03 11:00:00"
          }
        ]
      }
    ]
  }
}
```

---

### 3. 创建任务 — `cwork-create-task.py`

**意图**：解析人员姓名 → 创建工作计划/任务

```bash
python3 scripts/cwork-create-task.py \
  --task-main "完成XXX功能" \
  --content "详细描述" \
  --assignee "张三" \
  --deadline 2026-05-01
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `--task-main` | ✅ | 任务标题 |
| `--content` | ✅ | 任务描述 |
| `--target` | ❌ | 预期目标（默认 = content） |
| `--assignee` | ❌ | 责任人姓名（自动解析 empId） |
| `--report-to` | ❌ | 汇报人姓名（不传则自动取 `--assignee` 的值；API 要求必填） |
| `--assistant` | ❌ | 协办人姓名（逗号分隔多人） |
| `--supervisor` | ❌ | 监督人姓名 |
| `--copy` | ❌ | 抄送人姓名（逗号分隔多人） |
| `--observer` | ❌ | 观察员姓名（逗号分隔多人） |
| `--deadline` | ❌ | 截止时间（YYYY-MM-DD 或 Unix ms，默认 7 天后） |
| `--push-now` | ❌ | 是否立即推送（true/false，默认 true）。开放 API 文档未说明 `pushNow=0` 时的额外字段；若服务端报「待办发送时间未设置」等错误，需向接口提供方确认是否另有未文档化参数或是否暂不支持延迟推送 |
| `--dry-run` | ❌ | 仅验证+解析，不创建 |

**流程步骤**：
1. 解析所有人员姓名 → empId
2. 校验必填项（task-main、content）
3. 汇总所有未匹配姓名 → 报错
4. `--dry-run` 时输出解析结果，不调用创建 API
5. 调用 `createPlan` API 创建任务

---

### 4. 审阅汇报 — `cwork-review-report.py`

**意图**：回复汇报 / 标记已读 / 查询待审汇报

```bash
# 标记已读
python3 scripts/cwork-review-report.py --mode mark-read --report-id <id>

# 回复（默认 markdown，可发内部链接；需纯 HTML 段落可加 --content-type html）
python3 scripts/cwork-review-report.py --mode reply \
  --report-id <id> --reply "回复内容"

# 查询待审汇报列表
python3 scripts/cwork-review-report.py --mode pending --page-size 20
```

| 参数 | 说明 |
|------|------|
| `--mode` | `reply` / `mark-read` / `pending` |
| `--report-id` | 汇报记录 ID（reply / mark-read 必填） |
| `--reply` | 回复正文（reply 必填；默认按 markdown 原样提交，支持内部链接语法） |
| `--content-type` | `markdown`（默认）或 `html`；`html` 时将正文包成 `<p>…</p>` |
| `--at` | 回复中 @的人姓名（自动解析 empId） |
| `--page-index` | 页码（pending 模式，默认 1） |
| `--page-size` | 每页大小（pending 模式，默认 20） |
| `--report-type` | 汇报类型筛选 1-5（pending 模式可选） |
| `--dry-run` | 仅预览，不调用 API |

---

### 5. 查询任务 — `cwork-query-tasks.py`

**意图**：我的任务 / 我创建的 / 团队任务 / 任务详情（含汇报链）/ 识别逾期和未闭环

```bash
# 分配给我的任务
python3 scripts/cwork-query-tasks.py --mode my --status 1

# 我创建的任务
python3 scripts/cwork-query-tasks.py --mode created

# 下属任务
python3 scripts/cwork-query-tasks.py --mode manager --subordinate-ids "id1,id2"

# 任务详情（含汇报链路）
python3 scripts/cwork-query-tasks.py --mode detail --task-id <planId>

# 识别逾期任务
python3 scripts/cwork-query-tasks.py --mode blocked --days-threshold 7
```

| 参数 | 说明 |
|------|------|
| `--mode` | `my` / `created` / `team` / `assigned` / `detail` / `chain` / `blocked` / `unclosed` / `manager` / `nudge` |
| `--task-id` | 任务/计划 ID（detail / chain 必填） |
| `--subordinate-ids` | 下属 empId 列表（逗号分隔，manager 模式必填） |
| `--assignee` | 责任人姓名（my / assigned 模式可选，自动解析 empId） |
| `--status` | 任务状态：0=已关闭 / 1=进行中 / 2=未启动 |
| `--report-status` | 汇报状态：0=关闭 / 1=待汇报 / 2=已汇报 / 3=逾期 |
| `--key-word` | 关键词搜索 |
| `--days-threshold` | 逾期天数阈值（blocked 模式，默认 7） |
| `--page-index` | 页码（默认 1） |
| `--page-size` | 每页大小（默认 20） |
| `--dry-run` | 仅预览，不调用 API |

---

### 6. 催办闭环 — `cwork-nudge-report.py`

**意图**：列出逾期未闭环任务 / 向责任人发送催办通知

```bash
# 列出逾期未闭环任务（超过阈值天数）
python3 scripts/cwork-nudge-report.py --mode list --days-threshold 7

# 向责任人发送催办（通过 empId）
python3 scripts/cwork-nudge-report.py --mode nudge \
  --emp-id <empId> \
  --task-main "完成XXX功能" \
  --deadline 2026-05-01 \
  --content "请尽快处理"

# 通过姓名自动解析 empId 并催办
python3 scripts/cwork-nudge-report.py --mode nudge \
  --assignee "张三" \
  --task-main "完成XXX功能" \
  --remind-style normal
```

| 参数 | 说明 |
|------|------|
| `--mode` | `list`=列出未闭环 / `nudge`=发送催办 |
| `--days-threshold` | 逾期天数阈值（list 模式，默认 7） |
| `--page-index` | 页码（list 模式，默认 1） |
| `--page-size` | 每页大小（list 模式，默认 50） |
| `--emp-id` | 催办对象 empId（nudge 必填，与 `--assignee` 二选一） |
| `--assignee` | 责任人姓名（nudge 模式，自动解析 empId） |
| `--task-main` | 任务名称（nudge 必填） |
| `--deadline` | 截止日期（YYYY-MM-DD 或 Unix ms） |
| `--content` | 催办内容描述（脚本自动构建 HTML 正文） |
| `--target` | 目标描述 |
| `--remind-style` | 催办风格：`polite`（默认，含礼貌用语）/ `normal`（简洁） |
| `--dry-run` | 仅预览，不调用 API |

---

### 7. 待办管理 — `cwork-todo.py`

**意图**：查询待办列表 / 完成待办（支持决策/建议/反馈三种类型）

**支持的三种待办类型**：
| 类型 | 英文标识 | 必填参数 | 说明 |
|------|---------|---------|------|
| **决策** | `decide` | `--operate agree/disagree` | 决策人必须明确同意或不同意 |
| **建议** | `suggest` | `--content` | 建议人提供意见或建议 |
| **反馈** | `feedback` | `--content` | 反馈人回复评论或补充信息 |

```bash
# 查询待办列表（5.15 分页结构为 PageInfo，条目见 items，字段含 todoId、reportId、main、todoType 等）
python3 scripts/cwork-todo.py list --page-size 20 --status pending

# 完成决策待办（必须指定 operate）
python3 scripts/cwork-todo.py complete \
  --todo-id <id> \
  --content "同意该方案，建议增加异常处理" \
  --operate agree

# 完成建议待办
python3 scripts/cwork-todo.py complete \
  --todo-id <id> \
  --content "从技术角度看，建议采用微服务架构"

# 完成反馈待办
python3 scripts/cwork-todo.py complete \
  --todo-id <id> \
  --content "已补充相关数据，详见附件"

# 查看汇报详情（含节点与处理意见）
python3 scripts/cwork-query-report.py --mode node-detail --report-id <id>
```

| 参数 | 说明 |
|------|------|
| `action` | `list` / `complete` |
| `--page-index` | 页码（默认 1） |
| `--page-size` | 每页数量（默认 20） |
| `--status` | 状态筛选 |
| `--todo-id` | 待办 ID（complete 必填） |
| `--content` | 完成说明（所有类型必填） |
| `--operate` | 决策操作：`agree`（同意）/ `disagree`（不同意）（仅决策类待办需要，不传则不发送此字段） |
| `--dry-run` | 仅预览（complete 可用） |

**输出格式**（complete）：
```json
{
  "success": true,
  "action": "complete",
  "todoId": "12345",
  "result": {}
}
```

---

### 8. 模板管理 — `cwork-templates.py`

**意图**：查询汇报模板列表

```bash
# 查询模板列表
python3 scripts/cwork-templates.py list --limit 50

# 带时间范围
python3 scripts/cwork-templates.py list --begin-time 1710000000000 --end-time 1712000000000
```

| 参数 | 说明 |
|------|------|
| `action` | `list` |
| `--limit` | 返回数量限制（默认 50） |
| `--begin-time` | 开始时间戳（毫秒） |
| `--end-time` | 结束时间戳（毫秒） |
| `--output-raw` | 输出原始 API 响应 |

**输出字段**：
- `id` — 模板 ID
- `name` — 模板名称
- `type` — 类型 ID
- `typeName` — 类型名称
- `grade` — 优先级

---

## 辅助工具

### 问题自动上报 — `cwork-report-issue.py`

**意图**：当脚本报错或 API 异常时，自动将问题提交为 GitHub Issue，便于追踪和修复。

**前置条件**：设置环境变量 `GITHUB_TOKEN`（详见 `references/maintenance.md`）。

```bash
# 上报一个脚本报错
python3 scripts/cwork-report-issue.py \
  --title "bug: cwork-send-report.py 发送失败" \
  --script cwork-send-report.py \
  --error '{"success": false, "error": "API Error (200003): 流程节点类型不正确"}' \
  --body "发送汇报时传入 reportLevelList，type 字段使用了中文导致报错"

# 先预览，不实际提交
python3 scripts/cwork-report-issue.py \
  --title "bug: ..." \
  --script cwork-query-report.py \
  --error "..." \
  --dry-run
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `--title` / `-T` | ✅ | Issue 标题 |
| `--script` / `-s` | ❌ | 出错的脚本名称 |
| `--error` / `-e` | ❌ | 错误信息（脚本 stderr 的 JSON 输出） |
| `--body` / `-b` | ❌ | 问题描述（复现步骤等） |
| `--extra` | ❌ | 附加信息（环境、版本等） |
| `--labels` | ❌ | 额外标签（逗号分隔，默认已含 `bug` 和 `cms-cwork-workflow`） |
| `--dry-run` | ❌ | 预览将提交的内容，不实际创建 |
| `--token` | ❌ | GitHub Token（仅调试用，生产环境请用环境变量 `GITHUB_TOKEN`） |

**输出格式**：
```json
{
  "success": true,
  "issue_number": 42,
  "issue_url": "https://github.com/xgjk/cwork-skills/issues/42",
  "title": "bug: cwork-send-report.py 发送失败"
}
```

**Agent 调用建议**：
- 脚本返回 `"success": false` 且错误类型为 API 异常（非参数错误）时，询问用户是否上报
- 上报前使用 `--dry-run` 预览内容，确认无敏感信息（如 appKey、empId 等）后再提交
- `--error` 传入脚本 stderr 的原始 JSON 输出即可，脚本会自动格式化

---

## `reportLevelList` 字段格式

`cwork-send-report.py` 可通过 **`--report-level-json`** 指向 UTF-8 JSON 文件（根节点为数组），内容对应 API 字段 `reportLevelList`，用于指定建议人/决策人/传阅等节点；不传时新建草稿可为空，**更新**时默认从 5.25 详情中的 `reportLevelList` 原样转换后写回，避免全量更新被清空。每个节点结构如下：

```python
report_level_list = [
    {
        "level": 1,                              # 节点序号（从1开始）
        "nodeName": "建议人",                     # 节点显示名称
        "type": "suggest",                       # suggest=建议 | decide=决策 | read=传阅
        "levelUserList": [
            {"empId": 1512393035869810694},       # empId 必须是整数（非字符串）
        ],
    }
]
```

> ⚠️ `type` 只接受英文小写 `suggest` / `decide` / `read`，不接受中文。`levelUserList` 是必填字段，不可为 `null` 或空列表。

---

## Agent 调用模式

### 模式 A：简单查询（单次 exec）

```
用户：「帮我看看今天有没有未读汇报」
Agent → exec: python3 scripts/cwork-query-report.py --mode unread --page-size 10
Agent ← JSON → 摘要呈现给用户
```

### 模式 B：多步编排（Agent 协调多次 exec）

```
用户：「给张三发一份周报，内容是XXX」
Agent → exec: python3 scripts/cwork-send-report.py \
          --title "周报" --content-html "..." --receivers "张三"
Agent ← JSON（含完整 draftDetail、confirmPrompt；默认不会发出）
Agent → 向用户展示 **draftDetail 全文**（尤其 contentHtml、附件、reportLevelList）
用户：「确认」
Agent → exec: python3 scripts/cwork-send-report.py \
          --draft-id "<上一步的 reportId（与 draftId 同值）>" --confirm-send
Agent ← JSON（success、已通过 5.27 发出）
Agent → 告知发送成功
```

### 模式 C：催办闭环（3步分离）

```
Agent → exec: python3 scripts/cwork-nudge-report.py identify --days-threshold 7
Agent ← JSON（未闭环列表）
Agent → （LLM 推理）筛选需要催办的事项
Agent → exec: python3 scripts/cwork-nudge-report.py reminder \
          --item-id <id> --recipient "张三" --days-unresolved 14 --style polite
Agent ← JSON（催办文案）
Agent → （可选 LLM 优化文案）
Agent → exec: python3 scripts/cwork-nudge-report.py nudge \
          --report-id <id> --content-html "..."
```

---

## 错误处理

所有脚本遵循统一错误约定：
- **成功**：JSON 到 stdout，含 `"success": true`
- **失败**：JSON 到 stderr，含 `"success": false` 和 `"error"` 字段，exit code ≠ 0
- **Agent 应同时检查 stdout 和 stderr**

遇到 API 异常（如 `API Error (2xxxxx)`）时，可调用 `cwork-report-issue.py` 上报问题：

```bash
python3 scripts/cwork-report-issue.py \
  --title "bug: <出错脚本> <简短描述>" \
  --script "<出错脚本>.py" \
  --error '<stderr JSON>' \
  --body "<复现步骤>"
```

> ⚠️ 上报前确认 `--error` 和 `--body` 中不含 appKey、empId 等敏感信息。

### 通用参数

所有脚本均支持以下通用参数：

| 参数 | 说明 |
|------|------|
| `--params-file <path>` | 从 UTF-8 JSON 文件读取参数，key 与命令行参数名一致（连字符格式）。用于解决 Windows PowerShell 中文编码问题。 |

**用法示例**：

```json
{
  "title": "周报标题",
  "content-html": "<p>汇报内容</p>",
  "receivers": "张三"
}
```

```bash
python3 scripts/cwork-send-report.py --params-file params.json
```

> 文件参数与命令行参数可混用，命令行参数优先级更高。文件必须为 UTF-8 编码（带或不带 BOM 均支持）。

---

## 目录结构

```
cms-cwork-workflow/
├── SKILL.md                          ← 本文件（意图级接口文档）
├── scripts/
│   ├── cwork_client.py               ← 共享 API 客户端（HTTP 封装 + 所有 API 方法）
│   ├── cwork-search-emp.py           ← 0. 搜索员工 ✨ v3.2.0 新增
│   ├── cwork-send-report.py          ← 1. 发送汇报
│   ├── cwork-query-report.py         ← 2. 查询汇报
│   ├── cwork-create-task.py          ← 3. 创建任务
│   ├── cwork-review-report.py        ← 4. 审阅汇报
│   ├── cwork-query-tasks.py          ← 5. 查询任务
│   ├── cwork-nudge-report.py         ← 6. 催办闭环
│   ├── cwork-todo.py                 ← 7. 待办管理
│   └── cwork-templates.py            ← 8. 模板管理
├── design/
│   └── DESIGN.md                     ← 架构设计文档
└── references/
    └── maintenance.md                ← 维护操作说明
```

---

## 参考资料

> 正常调用只需按本文档使用 CLI 脚本，不必直接查阅 API 文档。
> 遇到 API 错误码或需要扩展脚本时，可查阅以下官方文档：

- **工作协同 Open API 接口文档**：[工作协同API说明.md](https://github.com/xgjk/dev-guide/blob/main/02.%E4%BA%A7%E5%93%81%E4%B8%9A%E5%8A%A1AI%E6%96%87%E6%A1%A3/%E5%B7%A5%E4%BD%9C%E5%8D%8F%E5%90%8C/%E5%B7%A5%E4%BD%9C%E5%8D%8F%E5%90%8CAPI%E8%AF%B4%E6%98%8E.md)
