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
