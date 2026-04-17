### 7. 待办管理 — `cwork-todo.py`

**意图**：查询待办列表 / 完成待办（支持决策/建议/反馈三种类型）

**支持的三种待办类型**：
| 类型 | 英文标识 | 必填参数 | 说明 |
|------|---------|---------|------|
| **决策** | `decide` | `--operate agree/disagree` | 决策人必须明确同意或不同意 |
| **建议** | `suggest` | `--content` | 建议人提供意见或建议 |
| **反馈** | `feedback` | `--content` | 反馈人回复评论或补充信息 |

```bash
# 查询待办列表（API 5.15 分页结构为 PageInfo，条目见 items，字段含 todoId、reportId、main、todoType 等）
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
