#!/usr/bin/env python3
"""
草稿箱辅助：分页列表（5.24）、批量删除（5.28）。

用法:
  python3 scripts/cwork-draft-box.py list --page-size 20
  python3 scripts/cwork-draft-box.py batch-delete --ids 2036325013120483329,2036325013120483330
  python3 scripts/cwork-draft-box.py batch-delete --begin-ms 1711785600000 --end-ms 1711872000000 --dry-run
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cwork_client import CWorkError, apply_params_file_pre_parse, make_client


def cmd_list(args: argparse.Namespace) -> None:
    client = make_client()
    data = client.list_drafts(page_index=args.page_index, page_size=args.page_size)
    rows = data.get("list") or []
    out = {
        "success": True,
        "action": "list",
        "total": data.get("total", len(rows)),
        "items": [
            {
                "draftBoxId": row.get("id"),
                "businessId": row.get("businessId"),
                "bizType": row.get("bizType"),
                "title": row.get("title") or row.get("main"),
            }
            for row in rows
            if isinstance(row, dict)
        ],
        "note": "删除单条草稿用 5.26 时路径 id 须为 draftBoxId；仅持有汇报 id 时请用 cwork_client.delete_draft_by_report_id",
    }
    print(json.dumps(out, ensure_ascii=False, indent=2))


def cmd_batch_delete(args: argparse.Namespace) -> None:
    id_list = None
    if args.ids.strip():
        id_list = [x.strip() for x in args.ids.split(",") if x.strip()]
    begin_ms = args.begin_ms
    end_ms = args.end_ms

    if begin_ms is not None and end_ms is None:
        print(json.dumps({"success": False, "error": "batch-delete 需同时指定 --begin-ms 与 --end-ms"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    if end_ms is not None and begin_ms is None:
        print(json.dumps({"success": False, "error": "batch-delete 需同时指定 --begin-ms 与 --end-ms"}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)
    if (begin_ms is None or end_ms is None) and not id_list:
        print(json.dumps({
            "success": False,
            "error": "请指定 --ids（草稿箱 id，逗号分隔）或 --begin-ms 与 --end-ms（毫秒时间戳）",
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    preview = {
        "success": True,
        "dryRun": True,
        "action": "batch-delete",
        "idList": id_list,
        "beginTime": begin_ms,
        "endTime": end_ms,
    }
    if args.dry_run:
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return

    client = make_client()
    try:
        deleted = client.batch_delete_drafts(
            id_list=id_list,
            begin_time_ms=begin_ms,
            end_time_ms=end_ms,
        )
    except CWorkError as e:
        print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    print(json.dumps({
        "success": True,
        "action": "batch-delete",
        "deletedCount": deleted,
    }, ensure_ascii=False, indent=2))


def main() -> None:
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    apply_params_file_pre_parse()

    p = argparse.ArgumentParser(description="CWork 草稿箱列表与批量删除（5.24 / 5.28）")
    p.add_argument("--params-file", dest="params_file", default=None, help="UTF-8 JSON 参数文件")
    sub = p.add_subparsers(dest="action", required=True)

    pl = sub.add_parser("list", help="分页列出草稿（5.24）")
    pl.add_argument("--page-index", type=int, default=1)
    pl.add_argument("--page-size", type=int, default=20)
    pl.set_defaults(func=cmd_list)

    pb = sub.add_parser("batch-delete", help="批量删除（5.28）；时间范围优先于 --ids")
    pb.add_argument("--ids", default="", help="草稿箱记录 id，逗号分隔（勿传汇报 id / businessId）")
    pb.add_argument("--begin-ms", type=int, default=None, dest="begin_ms")
    pb.add_argument("--end-ms", type=int, default=None, dest="end_ms")
    pb.add_argument("--dry-run", action="store_true", help="仅打印将提交的参数，不调用接口")
    pb.set_defaults(func=cmd_batch_delete)

    args = p.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
