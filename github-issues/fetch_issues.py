#!/usr/bin/env python3
"""
将 GitHub Issues 拉取到本目录（JSON），供本地分析。

环境变量（任选其一）：
  GITHUB_TOKEN  或  GH_TOKEN  — classic PAT 或 fine-grained（需 repo issues 读权限）

可选：
  GITHUB_REPOSITORY  — 默认 xgjk/cwork-skills（格式 owner/repo）

输出（覆盖写入）：
  snapshot-open.json   — state=open
  snapshot-closed.json — state=closed（分页拉取，页数见环境变量）

环境变量（可选）：
  GITHUB_ISSUES_MAX_PAGES_OPEN   — 默认 30（每页最多 100 条）
  GITHUB_ISSUES_MAX_PAGES_CLOSED — 默认 5（closed 量可能极大，避免一次拉全库）

用法：
  export GITHUB_TOKEN=ghp_xxxx
  python3 github-issues/fetch_issues.py

也可把变量写在仓库根目录 ``.env``（已被 .gitignore 忽略）；脚本启动时会尝试加载，
且**不会**覆盖已在环境中的变量。
"""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timezone
from pathlib import Path

DEFAULT_REPO = "xgjk/cwork-skills"
ABS_CAP = 200  # 单 state 绝对页数上限，防配置过大


def _load_dotenv_files() -> None:
    """从仓库根目录或当前工作目录的 .env 注入环境变量（仅填充尚未设置的键）。"""
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


def _fetch_page(url: str, token: str | None) -> tuple[list, str | None]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": "cwork-skills-issue-fetch",
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            next_url = None
            link = resp.headers.get("Link")
            if link and 'rel="next"' in link:
                for part in link.split(","):
                    if 'rel="next"' in part:
                        next_url = part.split(";")[0].strip().strip("<>")
                        break
            body = json.loads(resp.read().decode("utf-8"))
            return body, next_url
    except urllib.error.HTTPError as e:
        err = e.read().decode("utf-8", errors="replace")
        raise SystemExit(f"HTTP {e.code}: {err[:500]}") from e


def fetch_state(
    owner: str,
    repo: str,
    token: str | None,
    state: str,
    *,
    max_pages: int,
) -> list:
    out: list = []
    base = f"https://api.github.com/repos/{owner}/{repo}/issues?state={state}&per_page=100"
    url: str | None = base
    pages = 0
    cap = max(1, min(max_pages, ABS_CAP))
    while url and pages < cap:
        batch, url = _fetch_page(url, token)
        pages += 1
        if not isinstance(batch, list):
            break
        # /issues 含 PR；仅保留无 pull_request 字段的 issue
        for item in batch:
            if item.get("pull_request") is not None:
                continue
            out.append(item)
        if not batch:
            break
    return out


def main() -> None:
    _load_dotenv_files()
    token = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        print(
            json.dumps(
                {
                    "success": False,
                    "error": "请设置环境变量 GITHUB_TOKEN 或 GH_TOKEN",
                },
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

    out_dir = Path(__file__).resolve().parent
    meta = {
        "fetchedAt": datetime.now(timezone.utc).isoformat(),
        "repository": repo_full,
    }

    max_open = int(os.environ.get("GITHUB_ISSUES_MAX_PAGES_OPEN", "30"))
    max_closed = int(os.environ.get("GITHUB_ISSUES_MAX_PAGES_CLOSED", "5"))

    open_issues = fetch_state(owner, repo, token, "open", max_pages=max_open)
    path_open = out_dir / "snapshot-open.json"
    path_open.write_text(
        json.dumps(
            {**meta, "state": "open", "maxPages": max_open, "count": len(open_issues), "issues": open_issues},
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote {path_open} ({len(open_issues)} issues)", file=sys.stderr)

    closed_issues = fetch_state(owner, repo, token, "closed", max_pages=max_closed)
    path_closed = out_dir / "snapshot-closed.json"
    path_closed.write_text(
        json.dumps(
            {
                **meta,
                "state": "closed",
                "maxPages": max_closed,
                "count": len(closed_issues),
                "issues": closed_issues,
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )
    print(f"wrote {path_closed} ({len(closed_issues)} issues)", file=sys.stderr)

    print(
        json.dumps(
            {"success": True, "openCount": len(open_issues), "closedFetched": len(closed_issues)},
            ensure_ascii=False,
        )
    )


if __name__ == "__main__":
    main()
