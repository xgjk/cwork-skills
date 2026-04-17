### 9. 草稿箱列表与批量删除 — `cwork-draft-box.py`

**意图**：分页查看草稿箱（API 5.24）；按草稿箱记录 id 列表或时间范围批量删除（API 5.28）。**`--ids` 须为 API 5.24 返回的 `draftBoxId`（列表项 `id`），不是汇报 id / `businessId`**；仅持有汇报 id 时请用 `cwork_client.delete_draft_by_report_id`（此为客户端封装方法，脚本暂不支持直接通过汇报 id 删除）。

```bash
python3 scripts/cwork-draft-box.py list --page-size 20
python3 scripts/cwork-draft-box.py batch-delete --ids 2036325013120483329,2036325013120483330
python3 scripts/cwork-draft-box.py batch-delete --begin-ms 1711785600000 --end-ms 1711872000000 --dry-run
```

开放 API 约定 **时间范围优先**：同时传时间与 `idList` 时仅执行时间范围删除。

---
