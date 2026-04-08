#!/usr/bin/env python3
"""
cwork-send-report.py
Send a work report: search recipients → validate → save draft → show preview → send → cleanup

Usage:
  python3 scripts/cwork-send-report.py --title "汇报标题" \
    --content-html "<p>汇报内容</p>" \
    --receivers "张三,李四" \
    --grade "一般"

Environment:
  CWORK_APP_KEY  (required)
  CWORK_BASE_URL (optional, default: https://sg-al-cwork-web.mediportal.com.cn)
"""

import sys
import json
import argparse
from pathlib import Path

# Allow running as `python3 scripts/send-report.py` from skill root
sys.path.insert(0, str(Path(__file__).parent))
from cwork_client import make_client, CWorkError, apply_params_file_pre_parse


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="Send a CWork report")
    p.add_argument("--title", "-t", required=True, help="Report title")
    p.add_argument("--content-html", "-c", required=True, help="Report body HTML")
    p.add_argument(
        "--receivers", "-r", default="",
        help="Comma-separated receiver names (will be resolved to empId)"
    )
    p.add_argument(
        "--cc", dest="cc_names", default="",
        help="Comma-separated CC recipient names"
    )
    p.add_argument(
        "--grade", "-g", default="一般",
        choices=["一般", "紧急"],
        help="Report urgency"
    )
    p.add_argument(
        "--type-id", dest="type_id", type=int, default=9999,
        help="Report type ID (default 9999)"
    )
    p.add_argument(
        "--file-paths", nargs="*", dest="file_paths", default=[],
        help="Local file paths to attach (up to 10)"
    )
    p.add_argument(
        "--file-names", nargs="*", dest="file_names", default=[],
        help="File names for attachments (same order as --file-paths)"
    )
    p.add_argument(
        "--plan-id", dest="plan_id", default=None,
        help="Linked plan/task ID"
    )
    p.add_argument(
        "--preview-only", dest="preview_only", action="store_true",
        help="Save draft and print preview JSON, do not send"
    )
    p.add_argument(
        "--draft-id", dest="draft_id", default=None,
        help="汇报 ID（report ID），用于更新已有草稿；来自上次 --preview-only 输出的 draftId 字段"
    )
    p.add_argument(
        "--params-file", dest="params_file", default=None,
        help="UTF-8 JSON 文件路径，从文件读取参数（用于 Windows 下传递中文内容）"
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Step 1 — Resolve names → empIds
# ---------------------------------------------------------------------------

def resolve_receivers(client, names: list[str]) -> dict:
    """Search each name; return {name: {status, empId, title, dept}}"""
    results = {}
    for name in names:
        if not name.strip():
            continue
        try:
            data = client.search_emp_by_name(name.strip())
        except CWorkError as e:
            results[name] = {"status": "error", "message": str(e)}
            continue

        inside_raw = data.get("inside", {})
        inside = inside_raw.get("empList", []) if isinstance(inside_raw, dict) else []

        # Priority: internal employees first; only check outside if inside is empty
        if inside:
            candidates = inside
        else:
            outside_raw = data.get("outside")
            if isinstance(outside_raw, dict):
                candidates = outside_raw.get("empList", [])
            elif isinstance(outside_raw, list):
                candidates = [e for g in outside_raw if isinstance(g, dict)
                              for e in g.get("empList", [])]
            else:
                candidates = []

        if len(candidates) == 0:
            results[name] = {"status": "not_found"}
        elif len(candidates) == 1:
            emp = candidates[0]
            results[name] = {
                "status": "found",
                "empId": emp["id"],
                "name": emp["name"],
                "title": emp.get("title", ""),
                "dept": emp.get("mainDept", ""),
            }
        else:
            results[name] = {
                "status": "multiple",
                "employees": [
                    {"empId": e["id"], "name": e["name"],
                     "title": e.get("title", ""), "dept": e.get("mainDept", "")}
                    for e in candidates
                ],
            }
    return results


def validate_receivers(resolved: dict) -> tuple[list[dict], list[dict]]:
    """Return (confirmed list, structured error list).

    Each error dict has keys: name, reason, candidates (for 'multiple').
    Structured errors allow the agent to present disambiguation info.
    """
    confirmed = []
    errors = []
    for name, info in resolved.items():
        if info["status"] == "not_found":
            errors.append({"name": name, "reason": "not_found"})
        elif info["status"] == "multiple":
            errors.append({
                "name": name,
                "reason": "multiple_matches",
                "candidates": [
                    {"empId": e["empId"], "name": e["name"],
                     "title": e.get("title", ""), "dept": e.get("dept", "")}
                    for e in info["employees"]
                ],
            })
        elif info["status"] == "found":
            confirmed.append({"empId": info["empId"], "name": info["name"]})
    return confirmed, errors


# ---------------------------------------------------------------------------
# Step 2 — Upload files
# ---------------------------------------------------------------------------

def upload_files(client, file_paths: list[str], file_names: list[str]) -> list[dict]:
    """Upload files; return fileVO list for submit."""
    if not file_paths:
        return []
    file_vos = []
    for i, path in enumerate(file_paths):
        fname = file_names[i] if i < len(file_names) else Path(path).name
        try:
            result = client.upload_file(path)
            file_id = result.get("fileId", "")
            file_vos.append({
                "fileId": file_id,
                "name": fname,
                "type": "file",
            })
        except CWorkError as e:
            print(json.dumps({
                "step": "upload",
                "file": fname,
                "error": str(e)
            }, ensure_ascii=False), file=sys.stderr)
    return file_vos


# ---------------------------------------------------------------------------
# Step 3 — Save draft
# ---------------------------------------------------------------------------

def save_draft(client, args, accept_emp_ids: list[str], copy_emp_ids: list[str],
               file_vos: list[dict]) -> str | None:
    """Save or update draft; return report ID (汇报ID, not 草稿箱ID)."""
    params = {
        "main": args.title,
        "content_html": args.content_html,
        "content_type": "html",
        "type_id": args.type_id,
        "grade": args.grade,
        "accept_emp_id_list": accept_emp_ids or None,
        "copy_emp_id_list": copy_emp_ids or None,
        "file_vo_list": file_vos or None,
        "plan_id": args.plan_id,
    }
    if args.draft_id:
        # API 5.23: 更新草稿需传 id（汇报ID）；client.save_draft 的参数名是 draft_id
        params["draft_id"] = args.draft_id
    try:
        result = client.save_draft(**{k: v for k, v in params.items() if v is not None})
        return result.get("id")
    except CWorkError as e:
        print(json.dumps({"step": "save_draft", "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Step 4 — Preview
# ---------------------------------------------------------------------------

def build_preview(args, confirmed: list[dict], cc_confirmed: list[dict],
                  file_vos: list[dict]) -> dict:
    accept_names = [e["name"] for e in confirmed]
    cc_names = [e["name"] for e in cc_confirmed]
    import re
    plain = re.sub(r"<[^>]+>", "", args.content_html)

    return {
        "report": {
            "title": args.title,
            "grade": args.grade,
            "type_id": args.type_id,
            "plan_id": args.plan_id,
        },
        "receivers": {
            "count": len(accept_names),
            "names": accept_names,
            "confirmed": confirmed,
        },
        "cc": {
            "count": len(cc_names),
            "names": cc_names,
        },
        "attachments": {
            "count": len(file_vos),
            "files": [{"name": f["name"]} for f in file_vos],
        },
        "contentPreview": plain[:300] + ("..." if len(plain) > 300 else ""),
        "confirmPrompt": (
            f"【汇报预览】\n"
            f"标题：{args.title}\n"
            f"优先级：{args.grade}\n"
            f"接收人：{', '.join(accept_names) or '（无）'}\n"
            f"抄送：{', '.join(cc_names) or '（无）'}\n"
            f"附件：{', '.join(f['name'] for f in file_vos) or '无附件'}\n"
            f"正文预览：{plain[:200]}...\n"
            f"\n回复「是」确认发送，或告诉我需要修改的内容。"
        ),
    }


# ---------------------------------------------------------------------------
# Step 5 — Send
# ---------------------------------------------------------------------------

def submit_report(client, args, accept_emp_ids: list[str], copy_emp_ids: list[str],
                  file_vos: list[dict]) -> str | None:
    params = {
        "main": args.title,
        "content_html": args.content_html,
        "content_type": "html",
        "type_id": args.type_id,
        "grade": args.grade,
        "accept_emp_id_list": accept_emp_ids or None,
        "copy_emp_id_list": copy_emp_ids or None,
        "file_vo_list": file_vos or None,
        "plan_id": args.plan_id,
    }
    try:
        result = client.submit_report(**{k: v for k, v in params.items() if v is not None})
        return result.get("id")
    except CWorkError as e:
        print(json.dumps({"step": "submit", "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Step 6 — Cleanup draft
# ---------------------------------------------------------------------------

def cleanup_draft(client, draft_id: str):
    try:
        client.delete_draft(draft_id)
    except CWorkError as e:
        print(json.dumps({"step": "cleanup_draft", "draftId": draft_id, "error": str(e)}, ensure_ascii=False), file=sys.stderr)


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except AttributeError:
        pass
    apply_params_file_pre_parse()
    args = parse_args()
    client = make_client()

    # ---- Step 1: Resolve receiver names ----
    receiver_names = [n.strip() for n in args.receivers.split(",") if n.strip()]
    cc_names = [n.strip() for n in args.cc_names.split(",") if n.strip()]

    resolved = resolve_receivers(client, receiver_names)
    confirmed, errors = validate_receivers(resolved)
    cc_resolved = resolve_receivers(client, cc_names)
    cc_confirmed, cc_errors = validate_receivers(cc_resolved)

    # Both receiver and CC errors are fatal: ambiguous/missing names must be
    # resolved before sending, otherwise recipients would be silently dropped.
    all_errors = []
    if errors:
        all_errors.append({"field": "receivers", "errors": errors})
    if cc_errors:
        all_errors.append({"field": "cc", "errors": cc_errors})
    if all_errors:
        print(json.dumps({
            "success": False,
            "step": "validate_names",
            "message": "部分姓名未能唯一匹配，请确认后重试",
            "details": all_errors,
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    accept_emp_ids = [e["empId"] for e in confirmed]
    cc_emp_ids = [e["empId"] for e in cc_confirmed]

    # ---- Step 2: Upload files ----
    file_vos = upload_files(client, args.file_paths, args.file_names)

    # ---- Step 3: Save draft ----
    # save_draft returns the 汇报ID (report ID), NOT the 草稿箱记录ID.
    # The delete API (5.26) needs the 草稿箱ID (DraftBoxListVO.id).
    # We look it up via list_drafts by matching businessId == report_id.
    saved_report_id = save_draft(client, args, accept_emp_ids, cc_emp_ids, file_vos)
    draft_box_id = None
    if saved_report_id:
        try:
            pages = client.list_drafts(1, 20)
            for d in (pages.get("list") or []):
                if d.get("bizType") == "report" and str(d.get("businessId")) == str(saved_report_id):
                    draft_box_id = str(d.get("id"))
                    break
        except CWorkError:
            pass

    # ---- Step 4: Build preview ----
    preview = build_preview(args, confirmed, cc_confirmed, file_vos)
    preview["draftId"] = saved_report_id

    if args.preview_only:
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return

    # Send confirmation loop would happen at the Agent layer.
    # Here we just proceed to send.
    report_id = submit_report(client, args, accept_emp_ids, cc_emp_ids, file_vos)

    if report_id:
        # ---- Step 6: Cleanup ----
        if draft_box_id:
            cleanup_draft(client, draft_box_id)
        result = {
            "success": True,
            "reportId": report_id,
            "receivers": accept_emp_ids,
            "cc": cc_emp_ids,
            "attachments": len(file_vos),
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = {
            "success": False,
            "step": "submit",
            "draftId": saved_report_id,
            "message": "汇报发送失败，请检查草稿是否已保存",
        }
        print(json.dumps(result, ensure_ascii=False, indent=2))
        sys.exit(1)


if __name__ == "__main__":
    main()
