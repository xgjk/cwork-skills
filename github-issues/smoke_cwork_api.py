#!/usr/bin/env python3
"""
CWork 开放 API 冒烟自测（真实请求，默认不正式发汇报、不按 id 批量删草稿）。

依赖：仓库根目录 .env 或环境中已设置 CWORK_APP_KEY（及可选 CWORK_BASE_URL）。

用法（仓库根目录）：
  python3 github-issues/smoke_cwork_api.py

退出码：0 全部通过，1 有失败项。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SCR = ROOT / "cms-cwork-workflow" / "scripts"


def load_env() -> None:
    for name in (".env", ".env.local"):
        p = ROOT / name
        if not p.is_file():
            continue
        for line in p.read_text(encoding="utf-8").splitlines():
            s = line.strip()
            if not s or s.startswith("#") or "=" not in s:
                continue
            key, _, val = s.partition("=")
            key = key.strip()
            val = val.strip().strip('"').strip("'")
            if key and key not in os.environ:
                os.environ[key] = val


def run_script(argv: list[str]) -> tuple[int, str, str]:
    p = subprocess.run(
        [sys.executable, str(SCR / argv[0])] + argv[1:],
        cwd=str(SCR),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return p.returncode, p.stdout, p.stderr


def main() -> int:
    load_env()
    if not os.environ.get("CWORK_APP_KEY"):
        print(
            json.dumps({"success": False, "error": "CWORK_APP_KEY 未设置"}, ensure_ascii=False),
            file=sys.stderr,
        )
        return 1

    report: dict[str, list] = {"ok": [], "fail": []}

    def ok(name: str, detail: str = "") -> None:
        report["ok"].append({"step": name, "detail": detail})

    def fail(name: str, detail: str) -> None:
        report["fail"].append({"step": name, "detail": detail})

    code, out, err = run_script(["cwork-search-emp.py", "--name", "张成鹏"])
    if code != 0:
        fail("search_emp", err[:500])
    else:
        data = json.loads(out)
        ok("search_emp", f"success={data.get('success')}")

    code, out, err = run_script(["cwork-draft-box.py", "list", "--page-size", "5"])
    if code != 0:
        fail("draft_list", err[:500])
    else:
        data = json.loads(out)
        ok("draft_list", f"items={len(data.get('items') or [])}")

    code, out, err = run_script(
        [
            "cwork-send-report.py",
            "--title",
            "smoke",
            "--content",
            "<p>一二三四五六七八九十</p>",
            "--receivers",
            "张成鹏",
            "--preview-only",
        ]
    )
    if code == 0:
        fail("short_body_reject", "expected non-zero exit")
    else:
        try:
            e = json.loads(err)
            if e.get("step") == "validate_body":
                ok("short_body_reject", f"len={e.get('contentPlainLength')}")
            else:
                fail("short_body_reject", err[:400])
        except json.JSONDecodeError:
            fail("short_body_reject", err[:400])

    ts = int(time.time())
    code, out, err = run_script(
        [
            "cwork-send-report.py",
            "--title",
            f"API冒烟草稿{ts}",
            "--content",
            "<p>自动化API冒烟：请勿点正式发出，可删草稿。</p>",
            "--receivers",
            "张成鹏，屈军利",
            "--preview-only",
        ]
    )
    if code != 0:
        fail("send_preview", err[:800])
    else:
        data = json.loads(out)
        summ = data.get("summary") or {}
        names = summ.get("receiversResolved") or []
        rid = data.get("reportId") or data.get("draftId")
        ok("send_preview", f"reportId={rid} receivers={len(names)}")

    code, out, err = run_script(
        ["cwork-review-report.py", "--mode", "pending", "--page-size", "3"]
    )
    if code != 0:
        fail("review_pending", err[:500])
    else:
        data = json.loads(out)
        ok("review_pending", f"success={data.get('success')}")

    sys.path.insert(0, str(SCR))
    from cwork_client import CWorkError, make_client

    try:
        client = make_client()
        n = client.batch_delete_drafts(begin_time_ms=1, end_time_ms=2)
        ok("batch_delete_528", f"deletedCount={n!r}")
    except CWorkError as e:
        fail("batch_delete_528", str(e))

    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())
