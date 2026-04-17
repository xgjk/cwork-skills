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
