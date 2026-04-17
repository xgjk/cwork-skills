### 12. 虚拟员工管理 — `cwork-virtual-employee.py`

**意图**：创建、查询、修改、删除当前用户的虚拟员工（NPC），用于后续代发汇报/回复/任务。  
**触发词**：创建虚拟人 / 新建虚拟员工 / 添加虚拟助手 / 新增虚拟人 / 申请虚拟人 / 分配虚拟人。

---

> 写/发汇报场景下的“发送前虚拟身份检查”规则，见 `references/report-virtual-identity.md`。

```bash
# 创建虚拟员工
python3 scripts/cwork-virtual-employee.py \
  --mode add \
  --name "小风助手" \
  --remark "简小风数字分身助手"

# 查询我的虚拟员工列表
python3 scripts/cwork-virtual-employee.py --mode list

# 修改虚拟员工（改名/改备注，至少传一个）
python3 scripts/cwork-virtual-employee.py \
  --mode update \
  --id "2043613046072700929" \
  --name "小风助手2"

# 删除虚拟员工
python3 scripts/cwork-virtual-employee.py \
  --mode delete \
  --id "2043613046072700929"
```

参数说明：

| 参数 | 必填 | 说明 |
|------|------|------|
| `--mode` | ✅ | `add` / `list` / `update` / `delete` |
| `--id` | `update/delete` 必填 | 虚拟员工 ID |
| `--name` | `add` 必填，`update` 可选 | 虚拟员工名称 |
| `--remark` | ❌ | 备注 |
| `--params-file` | ❌ | UTF-8 JSON 参数文件 |

---

## 代发透传

创建后返回 `virtualEmpId`（字符串），在以下脚本中透传 `--virtual-emp-id`：

- `cwork-send-report.py`（发汇报）
- `cms-match-businessunit.py`（匹配业务单元后发汇报）
- `cwork-review-report.py --mode reply`（回复汇报）
- `cwork-create-task.py`（创建任务）

示例：

```bash
python3 scripts/cwork-send-report.py \
  --title "周报" \
  --content "<p>本周工作进展</p>" \
  --receivers "张三" \
  --virtual-emp-id "2043613046072700929"
```
