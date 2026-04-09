# 维护信息

## 基本信息

- **版本号须两处一致**：`SKILL.md` 前言（YAML 的 `version:`）与根目录 **`version.json`** 的 `version` 字段；发布或 bump 时**必须同时改这两处**，避免平台与文档不一致。
- ClawHub slug：`cms-cwork-workflow`

## GitHub 地址

- 仓库：https://github.com/xgjk/cwork-skills
- Skill 目录：`cwork-skills/cms-cwork-workflow/`

## 官方 API 文档

- [工作协同 Open API 接口文档](https://github.com/xgjk/dev-guide/blob/main/02.%E4%BA%A7%E5%93%81%E4%B8%9A%E5%8A%A1AI%E6%96%87%E6%A1%A3/%E5%B7%A5%E4%BD%9C%E5%8D%8F%E5%90%8C/%E5%B7%A5%E4%BD%9C%E5%8D%8F%E5%90%8CAPI%E8%AF%B4%E6%98%8E.md)

本 Skill 已把常用能力封装为脚本；**日常按 `SKILL.md` 调用即可**。若在本地扩展脚本、核对请求字段或查接口错误码，可打开上表链接对照说明。

## 如何更新

**工厂内部开发：**
1. 修改 Skill 内容
2. 若变更版本：同时更新 **`SKILL.md` 的 `version:`** 与 **`version.json`**
3. 执行 `clawhub publish`

**ClawHub 用户：**
```bash
clawhub update cms-cwork-workflow
```

---

*最后更新：2026-04-09*
