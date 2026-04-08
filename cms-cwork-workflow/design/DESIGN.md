# cms-cwork-workflow — Agent-First 重构设计文档

## 设计概述

将 cms-cwork-workflow 从 TypeScript 源码模式重构为 Agent-First 架构，通过 Python 编排脚本提供可组合、可复用的能力层。

## 核心设计理念

### Agent-First 架构
- **设计原则**: Agent 负责业务逻辑和 LLM 推理，脚本负责 API 编排和数据处理
- **协作模式**: Agent → JSON（工具输出）→ Agent（进一步处理）
- **边界清晰**: 脚本只做标准化的 API 调用，不做业务决策

### 编排脚本规范
- **JSON 输出**: 所有脚本输出结构化 JSON 到 stdout
- **错误处理**: stderr 输出调试信息，成功/failure 统一格式
- **参数校验**: 强制参数验证，可选参数支持默认值
- **干跑模式**: `--dry-run` / `--preview-only` 支持

## 文件结构设计

```
cms-cwork-workflow/
├── SKILL.md                           ← 产品级接口文档
├── scripts/
│   ├── cwork_client.py               ← 共享 API 客户端（HTTP 封装 + 所有 API 方法）
│   ├── cwork-report-issue.py         ← 辅助：问题自动上报到 GitHub
│   ├── cwork-search-emp.py           ← 搜索员工
│   ├── cwork-send-report.py          ← 发送汇报
│   ├── cwork-query-report.py         ← 查询汇报
│   ├── cwork-create-task.py          ← 创建任务
│   ├── cwork-review-report.py        ← 审阅汇报
│   ├── cwork-query-tasks.py          ← 查询任务
│   ├── cwork-nudge-report.py         ← 催办闭环
│   ├── cwork-todo.py                 ← 待办管理
│   └── cwork-templates.py            ← 模板管理
├── design/
│   └── DESIGN.md                     ← 本文件
└── references/
    └── maintenance.md                ← 维护说明
```

## 编排脚本架构

### 客户端层 (`cwork_client.py`)
- 封装 HTTP 请求逻辑（含 307 重定向处理）
- 统一错误处理和重试
- 参数编码和响应解析
- 所有业务 API 方法（`submit_report`、`save_draft` 等）
- 共享工具函数（`resolve_names_to_empids`、`parse_deadline`、`make_client` 等）

### 编排脚本层 (`.py`)
- argparse 命令行参数处理
- 业务逻辑编排
- 结构化 JSON 输出

## cwork_client.py API 方法索引

| API 端点 | 方法 |
|----------|------|
| `/open-api/cwork-user/searchEmpByName` | `search_emp_by_name()` |
| `/open-api/work-report/report/record/inbox` | `get_inbox_list()` |
| `/open-api/work-report/report/record/outbox` | `get_outbox_list()` |
| `/open-api/work-report/report/info` | `get_report_info()` |
| `/open-api/work-report/report/record/submit` | `submit_report()` |
| `/open-api/work-report/report/record/reply` | `reply_report()` |
| `/open-api/work-report/reportInfoOpenQuery/unreadList` | `get_unread_list()` |
| `/open-api/work-report/open-platform/report/readReport` | `mark_report_read()` |
| `/open-api/work-report/report/plan/searchPage` | `search_task_page()` |
| `/open-api/work-report/report/plan/getSimplePlanAndReportInfo` | `get_simple_plan_and_report_info()` |
| `/open-api/work-report/open-platform/report/plan/create` | `create_plan()` |
| `/open-api/work-report/draftBox/saveOrUpdate` | `save_draft()` |
| `/open-api/work-report/draftBox/listByPage` | `list_drafts()` |
| `/open-api/work-report/draftBox/detail/{id}` | `get_draft_detail()` |
| `/open-api/work-report/draftBox/delete/{id}` | `delete_draft()`（路径 id = 5.24 列表项 `id`）；`delete_draft_by_report_id()`（按 `businessId` 查列表再删） |
| `/open-api/work-report/draftBox/submit/{id}` | `submit_draft()`（5.27，路径 id 为汇报 id） |
| `/open-api/cwork-file/uploadWholeFile` | `upload_file()` |
| `/open-api/work-report/template/listTemplates` | `list_templates()` |
| `/open-api/work-report/reportInfoOpenQuery/todoList` | `get_todo_list()` |
| `/open-api/work-report/open-platform/todo/completeTodo` | `complete_todo()` |
| `/open-api/work-report/report/getReportNodeDetail` | `get_report_node_detail()` |
| — | `get_sender_history()` |
| — | `search_reports_by_keyword()` |

## API 覆盖设计

| 功能域 | 脚本 | 主要 API | 输出格式 |
|--------|------|----------|----------|
| 汇报查询 | `cwork-query-report.py` | `get_inbox_list()`, `get_outbox_list()`, `get_unread_list()` | `{"success": true, "items": [...]}` |
| 任务查询 | `cwork-query-tasks.py` | `search_task_page()`, `get_simple_plan_and_report_info()` | `{"success": true, "tasks": [...]}` |
| 审阅回复 | `cwork-review-report.py` | `reply_report()`, `mark_report_read()` | `{"success": true, "result": {...}}` |
| 催办闭环 | `cwork-nudge-report.py` | `submit_report(type=12)`, `complete_todo()` | `{"success": true, "action": "nudge"}` |
| 创建任务 | `cwork-create-task.py` | `create_plan()`, `search_emp_by_name()` | `{"success": true, "planId": "..."}` |
| 发送汇报 | `cwork-send-report.py` | `save_draft()`, `get_draft_detail()`, `submit_draft()`（5.27）, `upload_file()` | `{"success": true, "reportId": "..."}` |
| 待办管理 | `cwork-todo.py` | `get_todo_list()`, `complete_todo()` | `{"success": true, "todos": [...]}` |
| 模板管理 | `cwork-templates.py` | `list_templates()` | `{"success": true, "templates": [...]}` |

## 错误处理设计

### 成功响应
```json
{
  "success": true,
  "action": "list",
  "total": 20,
  "items": []
}
```

### 错误响应
```json
{
  "success": false,
  "error": "缺少必填参数: --report-id"
}
```

### 交互模式
```bash
# 错误信息输出到 stderr
$ python3 cwork-send-report.py --to 张三 --content "测试" --dry-run
{"success": false, "error": "缺少必填参数: --task-id"}

# 干跑模式输出到 stdout
$ python3 cwork-send-report.py --to 张三 --content "测试" --dry-run --preview-only
{"success": true, "preview": {...}, "validation": {...}}
```

## 与 Agent 协作模式

### Agent → Script
```python
Agent: "帮我查询张三的待办列表"
Agent → exec: python3 cwork-todo.py list --status pending --page-size 10
Agent ← stdout: {"success": true, "items": [...]}
```

### Script → Agent (可选)
```python
# Agent 可进一步处理脚本输出
Agent: "我发现你有3个逾期待办，需要催办吗？"
Agent → exec: python3 cwork-nudge-report.py identify --days-threshold 7
```

## 扩展性设计

### 新功能添加流程
1. 在 `cwork_client.py` 添加新的 API 方法
2. 在对应脚本中调用新 API
3. 更新 `SKILL.md` 文档
4. 按需更新 `DESIGN.md` 和 `SKILL.md` 记录设计变更

### 版本管理
- 主版本号：重大架构变更
- 次版本号：新功能增加
- 修订版本号：Bug 修复

---

## 实现状态 (v3.1.0)

### ✅ 已完成
- [x] 8个编排脚本完整实现
- [x] 共享客户端封装（含 23 个 API 方法）
- [x] JSON 输出规范
- [x] 参数校验和错误处理
- [x] Agent-First 架构设计
- [x] 文档体系完善
- [x] **决策/建议/反馈待办完整支持**（v3.1.0 新增）
- [x] **汇报节点详情查询**（`get_report_node_detail()`）

### 🆕 v3.1.0 新增功能（2026-04-03）
| 功能 | 说明 | API 接口 |
|------|------|----------|
| **决策待办** | 支持同意/不同意操作 | `complete_todo(operate="agree/disagree")` |
| **建议待办** | 支持建议内容提交 | `complete_todo(content="...")` |
| **反馈待办** | 支持反馈回复 | `complete_todo(content="...")` |
| **节点详情** | 查询汇报的审批节点与处理意见 | `get_report_node_detail()` |

### 🔄 进行中
- [ ] 单元测试覆盖
- [ ] 性能优化
- [ ] 更多汇报类型支持

### 📋 待优化
- [ ] 错误码标准化
- [ ] 重试机制完善
- [ ] 缓存策略优化

---

*最后更新: 2026-04-03*