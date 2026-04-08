#!/usr/bin/env python3
"""cwork-report-issue.py — 自动上报问题到 GitHub Issues。

使用场景：
  Agent 遇到脚本报错或 API 异常时，调用本脚本将问题自动提交为 GitHub Issue。

认证方式（优先级从高到低）：
  1. 环境变量 GITHUB_TOKEN
  2. --token 参数（仅调试用，不要在 CI/生产环境使用）

用法示例：
  python3 scripts/cwork-report-issue.py \\
    --title "bug: cwork-send-report.py 发送失败" \\
    --script cwork-send-report.py \\
    --error '{"success": false, "error": "API Error (200003)"}' \\
    --body "复现步骤：python3 scripts/cwork-send-report.py --title 测试"
"""
from __future__ import annotations

import sys
import json
import os
import argparse
import urllib.request
import urllib.error
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")

GITHUB_REPO = "xgjk/cwork-skills"
GITHUB_API_URL = f"https://api.github.com/repos/{GITHUB_REPO}/issues"
DEFAULT_LABELS = ["bug", "cms-cwork-workflow"]

# Fine-grained token，仅限 xgjk/cwork-skills 仓库的 Issues: Read and Write 权限。
# 无法读写代码、推送提交或访问其他仓库。所有安装此 skill 的用户共享此 token。
# 如需使用自己的 token，设置环境变量 GITHUB_TOKEN 即可覆盖。
_BUILTIN_TOKEN = "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"




def output_json(data: dict, *, to_stderr: bool = False) -> None:
    out = sys.stderr if to_stderr else sys.stdout
    print(json.dumps(data, ensure_ascii=False, indent=2), file=out)


def create_github_issue(token: str, title: str, body: str, labels: list[str]) -> dict:
    payload = json.dumps({
        "title": title,
        "body": body,
        "labels": labels,
    }).encode("utf-8")

    req = urllib.request.Request(
        GITHUB_API_URL,
        data=payload,
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github.v3+json",
            "Content-Type": "application/json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode("utf-8"))
            return {
                "success": True,
                "issue_number": result["number"],
                "issue_url": result["html_url"],
                "title": result["title"],
            }
    except urllib.error.HTTPError as e:
        error_body = e.read().decode("utf-8", errors="replace")
        try:
            detail = json.loads(error_body).get("message", error_body)
        except Exception:
            detail = error_body
        return {
            "success": False,
            "error": f"GitHub API HTTP {e.code}: {detail}",
        }
    except urllib.error.URLError as e:
        return {
            "success": False,
            "error": f"网络错误: {e.reason}",
        }


def build_issue_body(
    script: str | None,
    error: str | None,
    body: str | None,
    extra: str | None,
) -> str:
    parts: list[str] = []

    if script:
        parts.append(f"## 出错脚本\n\n`{script}`")

    if error:
        # 尝试格式化 JSON 错误输出
        try:
            parsed = json.loads(error)
            formatted = json.dumps(parsed, ensure_ascii=False, indent=2)
        except Exception:
            formatted = error
        parts.append(f"## 错误信息\n\n```json\n{formatted}\n```")

    if body:
        parts.append(f"## 问题描述\n\n{body}")

    if extra:
        parts.append(f"## 附加信息\n\n{extra}")

    parts.append("## Skill\n\n`cms-cwork-workflow`")

    return "\n\n---\n\n".join(parts)


def apply_params_file_pre_parse() -> None:
    """从 --params-file 读取参数并注入 sys.argv（与其他脚本保持一致）。"""
    if "--params-file" not in sys.argv:
        return
    idx = sys.argv.index("--params-file")
    if idx + 1 >= len(sys.argv):
        return
    path = sys.argv[idx + 1]
    try:
        raw = Path(path).read_bytes()
        # 处理 UTF-8 BOM
        if raw.startswith(b"\xef\xbb\xbf"):
            raw = raw[3:]
        params = json.loads(raw.decode("utf-8"))
        injected: list[str] = []
        for key, value in params.items():
            arg_key = f"--{key}" if not key.startswith("--") else key
            injected.extend([arg_key, str(value)])
        # 插入到 --params-file 之前
        sys.argv = sys.argv[:idx] + injected + sys.argv[idx + 2:]
    except Exception as exc:
        print(
            json.dumps({"success": False, "error": f"读取 --params-file 失败: {exc}"}, ensure_ascii=False),
            file=sys.stderr,
        )
        sys.exit(1)


def main() -> None:
    sys.path.insert(0, str(Path(__file__).parent))
    apply_params_file_pre_parse()

    parser = argparse.ArgumentParser(
        description="自动上报 cms-cwork-workflow 问题到 GitHub Issues",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument("--title", "-T", required=True, help="Issue 标题（必填）")
    parser.add_argument("--script", "-s", help="出错的脚本名称，如 cwork-send-report.py")
    parser.add_argument("--error", "-e", help="错误信息（脚本 stderr 的 JSON 输出）")
    parser.add_argument("--body", "-b", help="问题描述（补充说明、复现步骤等）")
    parser.add_argument("--extra", help="附加信息（环境、版本等）")
    parser.add_argument(
        "--labels",
        default="",
        help="额外标签（逗号分隔，默认已含 bug 和 cms-cwork-workflow）",
    )
    parser.add_argument(
        "--token",
        help="GitHub Token（优先从环境变量 GITHUB_TOKEN 读取，此参数仅供调试）",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="预览将要提交的 Issue 内容，不实际创建",
    )
    parser.add_argument("--params-file", help="从 UTF-8 JSON 文件读取参数")

    args = parser.parse_args()

    # 解析 token：环境变量 > --token 参数 > 内置共享 token
    token = os.environ.get("GITHUB_TOKEN") or args.token or _BUILTIN_TOKEN
    if not token and not args.dry_run:
        output_json(
            {
                "success": False,
                "error": "缺少 GitHub Token，且内置 token 不可用。",
                "hint": "设置环境变量 GITHUB_TOKEN 或使用 --token 参数。",
            },
            to_stderr=True,
        )
        sys.exit(1)

    # 构建标签
    labels = list(DEFAULT_LABELS)
    if args.labels:
        labels.extend(lbl.strip() for lbl in args.labels.split(",") if lbl.strip())

    # 构建正文
    issue_body = build_issue_body(
        script=args.script,
        error=args.error,
        body=args.body,
        extra=args.extra,
    )

    # --dry-run：只展示，不提交
    if args.dry_run:
        output_json(
            {
                "success": True,
                "dry_run": True,
                "would_create": {
                    "repo": GITHUB_REPO,
                    "title": args.title,
                    "labels": labels,
                    "body": issue_body,
                },
            }
        )
        return

    result = create_github_issue(token, args.title, issue_body, labels)

    if result["success"]:
        output_json(result)
    else:
        output_json(result, to_stderr=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
