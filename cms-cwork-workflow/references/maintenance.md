# 维护信息

## 基本信息

- 版本：见 `version.json`
- ClawHub slug：`cms-cwork-workflow`

## GitHub 地址

- 仓库：https://github.com/xgjk/cwork-skills
- Skill 目录：`cwork-skills/cms-cwork-workflow/`

## 官方 API 文档

- [工作协同 Open API 接口文档](https://github.com/xgjk/dev-guide/blob/main/02.%E4%BA%A7%E5%93%81%E4%B8%9A%E5%8A%A1AI%E6%96%87%E6%A1%A3/%E5%B7%A5%E4%BD%9C%E5%8D%8F%E5%90%8C/%E5%B7%A5%E4%BD%9C%E5%8D%8F%E5%90%8CAPI%E8%AF%B4%E6%98%8E.md)

**唯一真相源（SSOT）**：凡涉及「接口是否支持某能力、某字段是否合法、请求该怎么组」，**一律以该文档为准**。若实际返回、产品表现或 Issue 描述与文档不一致，**以文档为仲裁依据**；文档**未写明**的能力、字段或语义，**不当作本 Skill 脚本 Bug 在客户端自行补字段或猜行为**，应判为 **新需求**（先更新开放文档或由接口方给出正式定义，再改客户端与 SKILL）。持久约束亦见仓库根目录 `.cursorrules` §2。

> 脚本已封装所有 API 调用，正常使用无需查阅。排查 API 错误码或新增 API 支持时参考。

## 如何更新

**工厂内部开发：**
1. 修改 Skill 内容
2. 更新 `_meta.json` 版本号
3. 执行 `clawhub publish`

**ClawHub 用户：**
```bash
clawhub update cms-cwork-workflow
```

---

*最后更新：2026-04-09*
