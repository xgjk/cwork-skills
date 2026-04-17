### 4. 审阅汇报 — `cwork-review-report.py`

**意图**：回复汇报 / 标记已读 / 查询待审汇报

```bash
# 标记已读
python3 scripts/cwork-review-report.py --mode mark-read --report-id <id>

# 回复（默认 markdown，可发内部链接；需纯 HTML 段落可加 --content-type html）
python3 scripts/cwork-review-report.py --mode reply \
  --report-id <id> --reply "回复内容"

# 回复并上传附件（本地文件）
python3 scripts/cwork-review-report.py --mode reply \
  --report-id <id> \
  --reply "回复内容（含附件）" \
  --file-paths "/path/a.docx" "/path/b.png" \
  --file-names "方案.docx" "截图.png"

# 查询待审汇报列表
python3 scripts/cwork-review-report.py --mode pending --page-size 20
```

| 参数 | 说明 |
|------|------|
| `--mode` | `reply` / `mark-read` / `pending` |
| `--report-id` | 汇报记录 ID（reply / mark-read 必填） |
| `--reply` | 回复正文（reply 必填；格式由 `--content-type` 决定） |
| `--content-type` | `markdown`（默认）或 `html`（`html` 时包成 `<p>…</p>`） |
| `--at` | 回复中 @的人姓名（自动解析 empId） |
| `--file-paths` | 本地附件路径列表（reply 模式可选；会先上传后作为回复附件提交） |
| `--file-names` | 附件显示名称（可选，与 `--file-paths` 顺序一致） |
| `--page-index` | 页码（pending 模式，默认 1） |
| `--page-size` | 每页大小（pending 模式，默认 20） |
| `--report-type` | 汇报类型筛选 1-5（pending 模式可选） |
| `--dry-run` | 仅预览，不调用 API |

---
