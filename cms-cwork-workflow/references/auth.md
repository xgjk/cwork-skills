### cms-auth-skills：AppKey 获取与注入（强制）

这份规则用于约束 Agent：任何需要执行本 Skill 的 `scripts/*.py` 的链路，AppKey 获取必须通过依赖 Skill `cms-auth-skills` 完成。

#### 必须做
- 只要确定要进入本 Skill 的执行链路（`exec python3 scripts/<name>.py`），在调用目标脚本之前，**必须先调用** `cms-auth-skills` 获取 AppKey。
- 将 `cms-auth-skills` 返回的 AppKey **以 `--app-key`** 注入到后续执行命令：
  - `python3 scripts/<name>.py ... --app-key "<AppKey>"`
- 若使用 `--params-file` 注入参数，则把 AppKey 放入 JSON 的 `app_key` 字段：
  - `{ "app_key": "<AppKey>", ... }`

#### 必须禁止
- 禁止自行从环境变量读取 AppKey（例如 `CWORK_APP_KEY`、`XG_BIZ_API_KEY` 等）。
- 禁止按某种“自动解析逻辑”（如从 sender_id/account_id、上下文字段等推断）去获取 AppKey。
- 禁止向用户索要 AppKey（不要问“把 AppKey 发我/让我用哪个键”这类话）。
- 禁止在 `cms-auth-skills` 未返回可用 AppKey 时继续调用 `scripts/*.py`。

#### 失败处理
- `cms-auth-skills` 获取失败或无可用 AppKey：必须停止当前链路，并引导用户重新完成授权/登录；然后再重新尝试进入执行链路。

