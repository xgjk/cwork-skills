# cwork-skills

本仓库用于统一管理工作协同相关的 skill 源码，遵循“一个目录一个 skill”的组织方式。当前仓库中暂时只有一个 skill。

## Skills 索引

- `cms-cwork-workflow/`：管理工作协同中的员工查询、汇报处理、待办闭环和任务协作流程

## 仓库结构

```text
cwork-skills/
├── README.md
└── <skill-name>/
    ├── SKILL.md
    ├── design/
    │   └── DESIGN.md
    ├── references/
    └── scripts/
```

当前仓库中的实际 skill 为 `cms-cwork-workflow/`。

## 目录说明

- `SKILL.md`：skill 的入口文档，包含 YAML 头、能力说明、使用方式和输出约定
- `scripts/`：实际执行脚本，封装 CWork API 调用与编排逻辑
- `references/`：接口和客户端参考资料，供维护和扩展时查阅
- `design/DESIGN.md`：对应 skill 的架构设计说明

## 当前约定

### Skill 命名

- skill 目录名即 skill 名称
- 统一使用小写字母、数字和连字符 `-`
- 推荐使用 `cms-业务域-动作` 风格
- 当前 skill 名称为 `cms-cwork-workflow`

### 最小可交付内容

- skill 目录必须包含 `SKILL.md`
- `scripts/` 必须可执行并与 `SKILL.md` 中的能力说明保持一致
- 不保留无关草稿、复盘记录或临时占位内容
- 提交前应确认无协议占位符残留

### 新增 Skill

1. 在仓库根目录新增一个独立 skill 目录
2. 保持目录名、`SKILL.md` 中的 `name`、`skillcode` 一致
3. 补齐 `SKILL.md`、`scripts/`，并按需补充 `design/`、`references/`

### 文档和脚本关系

- `SKILL.md` 描述对外使用方式和脚本输出协议
- `scripts/` 负责把底层平台接口封装为更适合 Agent 调用的 JSON 输出
- `references/` 仅作为参考资料，不参与 skill 运行

## 开发与维护建议

1. 修改脚本时，同步更新 `cms-cwork-workflow/SKILL.md`
2. 如涉及架构变化，同步更新 `cms-cwork-workflow/design/DESIGN.md`
3. 如涉及接口变化，可同步更新 `cms-cwork-workflow/references/`
4. 删除文件或目录前，先确认是否属于最终交付物

## 仓库地址

- GitHub: [xgjk/cwork-skills](https://github.com/xgjk/cwork-skills)