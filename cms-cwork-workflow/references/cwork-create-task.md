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
