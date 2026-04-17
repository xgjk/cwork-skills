### 0. 搜索员工 — `cwork-search-emp.py` ✨ 新增

**意图**：根据姓名/关键词搜索员工 ID 和详细信息

**使用场景**：
1. ✅ **确认接收人（兜底）** - 仅在无业务单元或用户明确指定具体同事时使用
2. ✅ **处理待办时确认发件人** - 查看发件人部门/职位
3. ✅ **创建任务时确认责任人** - 避免姓名错误（重名/错别字）
4. ✅ **催办时确认责任人信息** - 获取完整的员工信息

```bash
# 基础搜索（模糊匹配）
python3 scripts/cwork-search-emp.py --name "张"

# 精确搜索
python3 scripts/cwork-search-emp.py --name "成伟"

# 详细模式（包含 personId、dingUserId 等）
python3 scripts/cwork-search-emp.py --name "刘丽华" --verbose

# 更多结果
python3 scripts/cwork-search-emp.py --name "刘" --max-results 10

# 原始 API 响应（调试用）
python3 scripts/cwork-search-emp.py --name "张" --output-raw
```

| 参数 | 必填 | 说明 |
|------|------|------|
| `--name` / `-n` | ✅ | 员工姓名或关键词（支持模糊匹配） |
| `--max-results` / `-m` | ❌ | 每个类别最多返回数量（默认 5） |
| `--verbose` / `-v` | ❌ | 包含额外信息（personId、dingUserId、corpId） |
| `--output-raw` | ❌ | 输出原始 API 响应（调试用） |

**输出格式**：
```json
{
  "success": true,
  "searchKey": "成伟",
  "inside": [
    {
      "empId": "1514822118611259394",
      "name": "成伟",
      "title": "首席架构师",
      "mainDept": "技术部",
      "status": "在职"
    }
  ],
  "outside": [
    {
      "empId": "1897870576398327809",
      "name": "成伟",
      "title": "",
      "mainDept": "其他",
      "status": "在职",
      "company": "德镁医药"
    }
  ],
  "totalInside": 1,
  "totalOutside": 1
}
```

**注意事项**：
- ✅ **URL 编码已自动处理**（支持中文参数）
- ✅ **模糊匹配**：搜索"刘"会返回所有姓刘的员工
- ✅ **内外部区分**：`inside`（玄关健康员工）+ `outside`（外部联系人/其他公司）
- ⚠️ **重名问题**：可能返回多个同名员工，需要根据部门/职位区分
- 💡 **推荐用法**：发送汇报前先搜索确认 empId

---
