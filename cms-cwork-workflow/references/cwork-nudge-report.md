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
