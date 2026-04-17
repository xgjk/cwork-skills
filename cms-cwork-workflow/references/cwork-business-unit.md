### 10. 业务单元管理 — `cwork-business-unit.py`

**意图**：创建/更新业务单元方案，查询业务单元，删除业务单元。

```bash
# 创建业务单元（nodeList 从 JSON 文件读取）
python3 scripts/cwork-business-unit.py save \
  --name "工作协同开发小组" \
  --description "研发周报流程" \
  --node-list-json ./nodes.json

# 更新业务单元
python3 scripts/cwork-business-unit.py save \
  --id 2043594941317410818 \
  --name "工作协同开发小组（更新）" \
  --node-list-json ./nodes.json

# 查询我的所有业务单元
python3 scripts/cwork-business-unit.py list

# 查询单条详情
python3 scripts/cwork-business-unit.py get --id 2043594941317410818

# 删除业务单元
python3 scripts/cwork-business-unit.py delete --id 2043594941317410818
```

`--node-list-json` 文件示例：

```json
[
  {
    "nodeName": "接收人",
    "nodeType": "read",
    "empList": [{"id": "1514822118611259394", "name": "张三"}]
  },
  {
    "nodeName": "建议人",
    "nodeType": "suggest",
    "empList": [{"id": "1514822194347806721", "name": "李四"}]
  }
]
```

---
