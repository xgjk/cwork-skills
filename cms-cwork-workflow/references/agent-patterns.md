## Agent 调用模式示例

### 模式 A：简单查询（单次 exec）

```
用户：「帮我看看今天有没有未读汇报」
Agent → exec: python3 scripts/cwork-query-report.py --mode unread --page-size 10
Agent ← JSON → 摘要呈现给用户
```

### 模式 B：多步编排（Agent 协调多次 exec）

```
用户：「给张三发一份周报，内容是XXX」
Agent → exec: python3 scripts/cwork-send-report.py \
          --title "周报" --content "..." --receivers "张三"
Agent ← JSON（含完整 draftDetail、confirmPrompt；默认不会发出）
Agent → 向用户展示 **draftDetail 全文**（含正文、附件、`reportLevelList`）
用户：「确认」
Agent → exec: python3 scripts/cwork-send-report.py \
          --draft-id "<上一步的 reportId（与 draftId 同值）>" --confirm-send
Agent ← JSON（success、已通过 5.27 发出）
Agent → 告知发送成功
```

### 模式 C：催办闭环（3步分离）

```
Agent → exec: python3 scripts/cwork-nudge-report.py --mode list --days-threshold 7
Agent ← JSON（未闭环列表）
Agent → （LLM 推理）筛选需要催办的事项
Agent → exec: python3 scripts/cwork-nudge-report.py --mode nudge \
          --emp-id <empId> --task-main "任务名" --deadline YYYY-MM-DD --content "催办说明"
Agent ← JSON（已发送催办汇报）
```

### 模式 D：正文已写好 — 业务单元匹配成功

```
用户：「正文写好了」
Agent → exec: python3 scripts/cwork-business-unit.py list
Agent ← data 非空
Agent → exec: python3 scripts/cms-match-businessunit.py --title "周报" --content "..." --content-type html --dry-run
Agent ← JSON（"matched": true, matchedBusinessUnit）
Agent → 对用户：这篇汇报可以建议发给「某某业务单元小组」（结合 matched 正文说明为何贴切），是否按该小组发送？
用户：「可以 / 按你建议发」
Agent → exec: python3 scripts/cms-match-businessunit.py --title "周报" --content "..." --content-type html
Agent ← JSON（submitResult）
Agent → 告知已按业务单元发送
```

### 模式 E：正文已写好 — 业务单元未匹配（或完全无业务单元）

```
情况1：无业务单元列表 / 情况2：dry-run 返回 "matched": false
Agent → 对用户：根据您的内容，未能匹配到合适的业务单元小组。请问这篇汇报发给谁？
用户：「发给张三」
Agent → exec: cwork-search-emp.py → cwork-send-report.py --receivers "张三" ...
```

