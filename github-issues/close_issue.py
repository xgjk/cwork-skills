#!/usr/bin/env python3
"""
通过 GitHub REST API 关闭 Issue（无需 gh CLI）。

环境变量（任选其一，与 fetch_issues.py 一致）：
  GITHUB_TOKEN  或  GH_TOKEN  — 须具备对该仓库 **issues: write**（classic: repo 或 public_repo 视仓库而定；fine-grained: Issues 读写）

可选：
  GITHUB_REPOSITORY  — 默认 xgjk/cwork-skills（格式 owner/repo）

用法：
  python3 github-issues/close_issue.py 30
  python3 github-issues/close_issue.py 30 31 --comment "已修复，见提交 xxx"
  python3 github-issues/close_issue.py --issue 30 --comment-file note.md

关闭前若提供 --comment / --comment-file，会先 POST 评论再 PATCH state=closed。
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

DEFAULT_REPO = "xgjk/cwork-skills"


def _load_dotenv_files() -> None:
    here = Path(__file__).resolve()
    candidates = [
        here.parent.parent / ".env",
        here.parent.parent / ".env.local",
        Path.cwd() / ".env",
        Path.cwd() / ".env.local",
    ]
    seen: set[Path] = set()
    for path in candidates:
        try:
            path = path.resolve()
        except OSError:
            continue
        if path in seen or not path.is_file():
            continue
        seen.add(path)
        try:
            raw = path.read_text(encoding="utf-8")
        except OSError:
            continue
        for line in raw.splitlines():
            s = line.strip()
            if not s or s.startswith("#"):
                continue
            if s.startswith("export "):
                s = s[7:].strip()
            if "=" not in s:
                continue
            key, _, val = s.partition("=")
            key = key.strip()
            val = val.strip().strip("'").strip('"')
            if key and key not in os.environ:
                os.environ[key] = val


def _api_request(
    method: str,
    url: str,
    token: str,
    body: dict | None = None,
) -> dict:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "cwork-skills-issue-close",
        "Authorization": f"Bearer {token}",
    }
    data = json.dumps(body, ensure_ascii=False).encode("utf-8") if body is not None else None
    if body is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            raw = resp.read()
            if not raw:
                return {}
            return json.loads(raw.decode("utf-8"))
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code}: {err[:800]}") from e


def add_comment(owner: str, repo: str, token: str, issue_num: int, body: str) -> None:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}/comments"
    _api_request("POST", url, token, {"body": body})


def close_issue(owner: str, repo: str, token: str, issue_num: int) -> dict:
    url = f"https://api.github.com/repos/{owner}/{repo}/issues/{issue_num}"
    return _api_request("PATCH", url, token, {"state": "closed"})


def main() -> None:
    _load_dotenv_files()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print(
            json.dumps(
                {"success": False, "error": "请设置 GITHUB_TOKEN 或 GH_TOKEN（需 issues 写权限）"},
                ensure_ascii=False,
            ),
            file=sys.stderr,
        )
        sys.exit(1)

    repo_full = os.environ.get("GITHUB_REPOSITORY", DEFAULT_REPO).strip()
    if "/" not in repo_full:
        print(json.dumps({"success": False, "error": "GITHUB_REPOSITORY 应为 owner/repo"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    owner, repo = repo_full.split("/", 1)

    p = argparse.ArgumentParser(description="通过 GitHub API 关闭 Issue")
    p.add_argument(
        "numbers",
        nargs="*",
        type=int,
        help="Issue 编号（可多个）",
    )
    p.add_argument(
        "--issue", "-i",
        type=int,
        action="append",
        dest="issues_extra",
        default=None,
        help="Issue 编号（可重复指定）",
    )
    p.add_argument("--comment", "-c", default=None, help="关闭前发表的评论正文")
    p.add_argument("--comment-file", type=Path, default=None, help="评论正文文件（UTF-8）")
    args = p.parse_args()

    extra = args.issues_extra or []
    nums = list(args.numbers) + list(extra)
    if not nums:
        p.error("请提供至少一个 Issue 编号，例如: python close_issue.py 30")

    comment_text = args.comment
    if args.comment_file is not None:
        if comment_text is not None:
            p.error("请勿同时使用 --comment 与 --comment-file")
        comment_text = args.comment_file.read_text(encoding="utf-8")

    results = []
    for n in nums:
        if comment_text:
            add_comment(owner, repo, token, n, comment_text)
        data = close_issue(owner, repo, token, n)
        results.append(
            {
                "number": n,
                "state": data.get("state"),
                "html_url": data.get("html_url"),
                "commentPosted": bool(comment_text),
            }
        )

    print(json.dumps({"success": True, "repository": repo_full, "closed": results}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
