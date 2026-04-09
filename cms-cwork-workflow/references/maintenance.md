# 维护信息

## 基本信息

- 版本：见 `version.json`
- ClawHub slug：`cms-cwork-workflow`

## GitHub 地址

- 仓库：https://github.com/xgjk/cwork-skills
- Skill 目录：`cwork-skills/cms-cwork-workflow/`

## 官方 API 文档

- [工作协同 Open API 接口文档](https://github.com/xgjk/dev-guide/blob/main/02.%E4%BA%A7%E5%93%81%E4%B8%9A%E5%8A%A1AI%E6%96%87%E6%A1%A3/%E5%B7%A5%E4%BD%9C%E5%8D%8F%E5%90%8C/%E5%B7%A5%E4%BD%9C%E5%8D%8F%E5%90%8CAPI%E8%AF%B4%E6%98%8E.md)

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

*最后更新：2026-04-05*
