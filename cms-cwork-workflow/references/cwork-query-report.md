### 2. 查询汇报 — `cwork-query-report.py`

**意图**：收件箱 / 发件箱 / 未读 / 汇报详情 / 节点详情 / **历史上下文检索** / **按汇报 ID 查询正文与附件等简要信息** / **按条件分页检索汇报列表** ✨

```bash
# 收件箱（默认）
python3 scripts/cwork-query-report.py --mode inbox --page-size 20

# 未读汇报
python3 scripts/cwork-query-report.py --mode unread --page-size 20

# 发件箱
python3 scripts/cwork-query-report.py --mode outbox

# 详情模式（包含回复链）
python3 scripts/cwork-query-report.py --mode detail --report-id <id>

# 节点详情（含审批/建议/反馈状态与处理意见）
python3 scripts/cwork-query-report.py --mode node-detail --report-id <id>

# 历史上下文检索（审批决策支持）
# 查询发件人历史汇报
python3 scripts/cwork-query-report.py --mode sender-history \
  --sender-emp-id <empId> \
  --days 90

# 关键字搜索汇报（客户端过滤）
python3 scripts/cwork-query-report.py --mode keyword-search \
  --keyword "公章" \
  --days 90

# 按汇报记录 ID 查询正文 / 附件 / 回复 / 关联邮件等简要信息
python3 scripts/cwork-query-report.py --mode record-simple-info \
  --report-record-id <reportRecordId> \
  --type content \
  --type attachment \
  --type reply \
  --type mail \
  --associated-report \
  --associated-report-file

# 按条件分页检索汇报列表（支持时间范围 / 关键词 / 汇报分类 / 发件人 / 收件人范围）
python3 scripts/cwork-query-report.py --mode search-list \
  --page-index 1 \
  --page-size 20 \
  --start-date 2026-01-01 \
  --end-date 2026-01-31 \
  --keyword "公章" \
  --classification-id 31121223 \
  --from-emp-id <senderEmpId> \
  --to-emp-id <receiverEmpId>

# 仅按时间范围分页检索
python3 scripts/cwork-query-report.py --mode search-list \
  --page-index 1 \
  --page-size 20 \
  --start-date <StartDate> \
  --end-date <EndDate>

# 按汇报唯一编码精确检索
python3 scripts/cwork-query-report.py --mode search-list \
  --page-index 1 \
  --page-size 20 \
  --report-code <ReportCode>

# 默认会为部分模式返回的汇报补充 shareLink（最多前 20 条）
python3 scripts/cwork-query-report.py --mode inbox --with-share-link --share-top-n 20

# 如需关闭补链
python3 scripts/cwork-query-report.py --mode inbox --no-share-link

# 当前页全部补链
python3 scripts/cwork-query-report.py --mode inbox --share-top-n 0
```

| 参数 | 说明 |
|------|------|
| `--mode` | `inbox` / `outbox` / `unread` / `detail` / `node-detail` / `sender-history` / `keyword-search` / `search-list` / `pending` / `my-sent` / `record-simple-info` |
| `--page-size` | 分页大小（默认 20） |
| `--page-index` | 页码（默认 1） |
| `--report-id` | 汇报 ID（detail / node-detail 必填） |
| `--report-record-id` | 汇报记录 ID（record-simple-info 必填） |
| `--sender-emp-id` | 发件人员工 ID（sender-history 必填） |
| `--receiver-emp-id` | 收件人员工 ID（search-list 可选） |
| `--keyword` | 搜索关键词（keyword-search / search-list 可选） |
| `--days` | 回溯天数（sender-history / keyword-search，默认 90） |
| `--report-type` | 汇报类型：1-工作交流 / 2-工作指引 / 3-文件签批 / 4-AI汇报 / 5-工作汇报（仅 inbox/outbox/pending 可选） |
| `--report-code` | 汇报唯一编码（search-list 优先使用，适合精确定位） |
| `--classification-id` | 汇报分类 ID 列表（search-list 可多次传入） |
| `--from-emp-id` | 发汇报人员工 ID 列表（search-list 可多次传入） |
| `--to-emp-id` | 收汇报人员工 ID 列表（search-list 可多次传入） |
| `--status` | 已读状态：0=未读 / 1=已读 |
| `--start-date` / `--end-date` | 时间范围（YYYY-MM-DD；search-list 可选） |
| `--with-share-link` / `--no-share-link` | 是否补充汇报分享链接（默认开启） |
| `--share-top-n` | 列表场景最多补充前 N 条 `shareLink`（默认 20，传 0 表示当前页全部） |
| `--type` | record-simple-info 模式下要查询的内容类型，可多次传入：`content`(正文)、`attachment`(附件)、`reply`(回复)、`mail`(关联邮件)。未传时默认四种全查。 |
| `--associated-report` / `--no-associated-report` | record-simple-info 模式：是否需要关联汇报的内容（默认 false）。 |
| `--associated-report-file` / `--no-associated-report-file` | record-simple-info 模式：是否需要关联汇报的附件内容（默认 false）。 |

**收件箱 / 发件箱列表 vs 详情**：`inbox` / `outbox` / `pending` / `unread` / `my-sent`（与 `outbox` 同脚本路径）等模式返回的 **`data` 为接口原始分页结构**（常见含 `list`、`total`）。列表项里的「正文」类字段多为**摘要**，与 `send-report` 的 `--content` 全文不一定一致；需要全文或完整字段时请用 **`--mode detail --report-id`**（或 `node-detail`）拉详情。默认会在可识别到汇报 ID 的结果上补充 `shareLink`，便于点击打开原始汇报。

**编码优先原则**：当用户给出汇报唯一编码时，不要先通过收件箱/发件箱翻页搜索标题；应直接使用 `search-list` + `--report-code` 命中具体汇报记录，然后再继续调用 `detail` 或 `record-simple-info` 获取正文、回复与待办事项。

> 文档示例里的编码必须使用占位符（例如 `<ReportCode>`），不要写真实编号，避免把示例误当成固定值。

**路由识别规则**：如果用户原话里同时包含“汇报/搜汇报/查汇报/找汇报/搜索汇报”等动作词和一段疑似编码（通常为 6~20 位、包含字母和数字，允许单字母开头），就应该把这段内容解释为 `--report-code`，而不是普通 `--keyword`。

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

**输出格式**（record-simple-info）：

```json
{
  "success": true,
  "data": {
    "reportRecordId": "2049459912303788033",
    "writeEmpId": "1518900100127248386",
    "writeEmpName": "陈明",
    "createTime": "2026-04-29T12:26:52.000+00:00",
    "reportRecord": {
      "main": "项目周报",
      "content": "本周完成接口联调",
      "leadContent": "下周推进上线"
    },
    "associatedContent": {
      "fileList": [
        {
          "fileName": "立项会AI模板BD反馈-20260429.docx",
          "fileSummary": "细节调整：...",
          "downloadUrl": "https://xxx.com/xxx.docx?...",
          "suffix": "docx",
          "size": 49196
        }
      ]
    },
    "replyList": [
      {
        "content": "请补充风险项",
        "createTime": "2026-04-20 10:00:00",
        "replyEmpName": "李四",
        "title": "项目经理",
        "type": "suggest",
        "fileList": []
      }
    ],
    "mailBoxList": [
      {
        "subject": "项目周报补充说明",
        "realContent": "abc"
      }
    ],
    "associatedReportList": [],
    "planList": []
  }
}
```

### AI 汇总输出建议（含可点击链接）

- 当结果项包含 `shareLink` 时，AI 在汇总文本中应将链接直接附在标题后，避免用户二次追问。
- 推荐格式：`- <汇报标题>（[打开汇报](<shareLink>)）`
- 若存在时间与汇报人，建议补充为：`- <汇报标题>（<时间>，<汇报人>，[打开汇报](<shareLink>)）`
- 若某条无 `shareLink`，使用降级文案：`- <汇报标题>（链接暂不可用，可让我重试补链）`
- 禁止编造链接；仅可使用脚本返回的真实 `shareLink`。

对于 **record-simple-info** 模式，LLM 需要特别关注：

- 当用户说「查汇报附件 / 查某条汇报的正文 / 查关联邮件 / 查某条汇报的回复 / 查汇报关联内容」时，应优先使用 `record-simple-info`，并根据意图选择合适的 `typeList`：
  - 只要附件：仅传 `attachment`
  - 附件 + 正文：传 `content` + `attachment`
  - 附件 + 回复 + 关联邮件：传 `attachment` + `reply` + `mail`
- 返回时请将附件的 `fileName` + 大小（`size`）+ 后缀（`suffix`）+ 摘要（`fileSummary`）以列表形式清晰呈现；`downloadUrl` 以链接形式暴露但不要修改或伪造。

---
