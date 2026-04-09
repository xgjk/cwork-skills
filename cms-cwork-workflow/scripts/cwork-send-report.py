#!/usr/bin/env python3
"""
cwork-send-report.py
发送汇报：解析接收人 → 全量保存/更新草稿（5.23）→ 输出完整草稿详情（5.25）供用户确认
→ 仅在 --confirm-send 后调用 5.27 将草稿转为正式汇报。

更新草稿前会先拉取详情，与本次参数合并后整包提交，避免全量覆盖导致字段丢失。

Usage:
  # 1) 仅存草稿 + 输出完整预览（默认，不发送）
  python3 scripts/cwork-send-report.py --title "..." --content-html "<p>...</p>" --receivers "张三"

  # 2) 用户确认后，仅凭汇报 id 发出（5.27）
  python3 scripts/cwork-send-report.py --draft-id <汇报id> --confirm-send

  # 3) 一步：保存并发出（需显式确认）
  python3 scripts/cwork-send-report.py --title "..." --content-html "..." --receivers "张三" --confirm-send

Environment:
  CWORK_APP_KEY  (required)
  CWORK_BASE_URL (optional)
"""

from __future__ import annotations

import sys
import json
import copy
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cwork_client import (
    make_client,
    CWorkError,
    apply_params_file_pre_parse,
    flatten_emp_search_bucket,
)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def parse_args():
    p = argparse.ArgumentParser(description="Send a CWork report (draft-first, 5.27 to publish)")
    p.add_argument("--title", "-t", default=None, help="汇报标题（发送-only 模式可不填）")
    p.add_argument("--content-html", "-c", default=None, help="正文 HTML（发送-only 模式可不填）")
    p.add_argument(
        "--receivers", "-r", default="",
        help="Comma-separated receiver names (will be resolved to empId)",
    )
    p.add_argument(
        "--cc", dest="cc_names", default="",
        help="Comma-separated CC recipient names",
    )
    p.add_argument(
        "--grade", "-g", default="一般",
        choices=["一般", "紧急"],
        help="Report urgency",
    )
    p.add_argument(
        "--type-id", dest="type_id", type=int, default=9999,
        help="Report type ID (default 9999)",
    )
    p.add_argument(
        "--file-paths", nargs="*", dest="file_paths", default=[],
        help="Local file paths to attach (up to 10)",
    )
    p.add_argument(
        "--file-names", nargs="*", dest="file_names", default=[],
        help="File names for attachments (same order as --file-paths)",
    )
    p.add_argument(
        "--plan-id", dest="plan_id", default=None,
        help="Linked plan/task ID",
    )
    p.add_argument(
        "--preview-only", dest="preview_only", action="store_true",
        help="仅保存草稿并输出完整预览（与默认不发送行为一致，便于显式调用）",
    )
    p.add_argument(
        "--draft-id", dest="draft_id", default=None,
        help="汇报 id：更新已有草稿；与 --confirm-send 单独使用时仅执行 5.27 发出",
    )
    p.add_argument(
        "--confirm-send", dest="confirm_send", action="store_true",
        help="用户已预览完整草稿并同意发出后，再指定此参数才会调用 5.27",
    )
    p.add_argument(
        "--report-level-json", dest="report_level_json", default=None,
        help="UTF-8 JSON 文件路径，内容为 reportLevelList 数组（覆盖详情中的流程节点）",
    )
    p.add_argument(
        "--params-file", dest="params_file", default=None,
        help="UTF-8 JSON 文件路径，从文件读取参数（用于 Windows 下传递中文内容）",
    )
    return p.parse_args()


# ---------------------------------------------------------------------------
# Resolve / validate names
# ---------------------------------------------------------------------------

def resolve_receivers(client, names: list[str]) -> dict:
    results = {}
    for name in names:
        if not name.strip():
            continue
        try:
            data = client.search_emp_by_name(name.strip())
        except CWorkError as e:
            results[name] = {"status": "error", "message": str(e)}
            continue

        inside = flatten_emp_search_bucket(data.get("inside"))

        if inside:
            candidates = inside
        else:
            candidates = flatten_emp_search_bucket(data.get("outside"))

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
# Draft detail → saveOrUpdate 全量字段
# ---------------------------------------------------------------------------

def _emp_ids_from_detail(emp_list: list | None) -> list[str]:
    if not emp_list:
        return []
    out: list[str] = []
    for e in emp_list:
        if isinstance(e, dict) and e.get("id") is not None:
            out.append(str(e["id"]))
    return out


def _file_vos_from_detail(file_list: list | None) -> list[dict]:
    if not file_list:
        return []
    out: list[dict] = []
    for f in file_list:
        if not isinstance(f, dict):
            continue
        fid = f.get("fileId")
        if not fid:
            continue
        out.append({
            "fileId": str(fid),
            "name": f.get("name") or "",
            "type": f.get("type") or "file",
        })
    return out


def _report_level_param_from_detail(nodes: list | None) -> list[dict] | None:
    if not nodes:
        return None
    result: list[dict] = []
    for node in nodes:
        if not isinstance(node, dict):
            continue
        emp_list = node.get("empList") or []
        level_users = []
        for e in emp_list:
            if not isinstance(e, dict):
                continue
            eid = e.get("empId", e.get("id"))
            if eid is not None:
                level_users.append({"empId": eid})
        entry = {
            "type": node.get("type"),
            "level": node.get("level"),
            "nodeCode": node.get("nodeCode"),
            "nodeName": node.get("nodeName"),
            "levelUserList": level_users,
            "groupIdList": node.get("groupIdList"),
            "requirement": node.get("requirement"),
        }
        result.append({k: v for k, v in entry.items() if v is not None})
    return result or None


def _receiver_node_index_for_cli_sync(nodes: list[dict]) -> int:
    """选择应将 ``--receivers`` 写入 ``levelUserList`` 的节点（与 5.1/5.23 一致：接收人以 reportLevelList 为准）。"""
    for i, n in enumerate(nodes):
        if isinstance(n, dict) and isinstance(n.get("type"), str) and n["type"].lower() == "read":
            return i
    for i, n in enumerate(nodes):
        if isinstance(n, dict) and n.get("levelUserList"):
            return i
    return 0


def _apply_cli_receivers_to_report_level_list(
    report_level_list: list[dict],
    accept_emp_ids: list[str],
) -> list[dict]:
    """用本次 CLI 解析出的接收人覆盖目标节点 ``levelUserList``，避免仅更新 acceptEmpIdList 时详情仍显示旧人。"""
    if not report_level_list or not accept_emp_ids:
        return report_level_list
    out = copy.deepcopy(report_level_list)
    idx = _receiver_node_index_for_cli_sync(out)
    if idx < 0 or idx >= len(out):
        return report_level_list
    level_users: list[dict] = []
    for eid in accept_emp_ids:
        try:
            level_users.append({"empId": int(str(eid))})
        except (TypeError, ValueError):
            level_users.append({"empId": eid})
    node = dict(out[idx])
    node["levelUserList"] = level_users
    node.pop("groupIdList", None)
    out[idx] = {k: v for k, v in node.items() if v is not None}
    return out


def load_report_level_json(path: str) -> list[dict]:
    raw = Path(path).read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("report-level-json 根节点须为 JSON 数组")
    return data


# ---------------------------------------------------------------------------
# Upload files
# ---------------------------------------------------------------------------

def upload_files(client, file_paths: list[str], file_names: list[str]) -> list[dict]:
    if not file_paths:
        return []
    file_vos = []
    for i, path in enumerate(file_paths):
        fname = file_names[i] if i < len(file_names) else Path(path).name
        try:
            result = client.upload_file(path)
            file_id = result.get("fileId", "")
            file_vos.append({
                "fileId": str(file_id) if file_id is not None else "",
                "name": fname,
                "type": "file",
            })
        except CWorkError as e:
            print(json.dumps({
                "step": "upload",
                "file": fname,
                "error": str(e),
            }, ensure_ascii=False), file=sys.stderr)
    return file_vos


# ---------------------------------------------------------------------------
# Merge + save draft (5.23 全量)
# ---------------------------------------------------------------------------

def build_save_draft_kwargs(
    args,
    *,
    detail: dict | None,
    accept_emp_ids: list[str],
    cc_emp_ids: list[str],
    file_vos: list[dict],
    receiver_names_nonempty: bool,
    cc_names_nonempty: bool,
    new_uploads: bool,
) -> dict:
    """构造 save_draft 的完整参数，避免更新时省略字段导致服务端清空。"""
    if args.report_level_json:
        report_level_list = load_report_level_json(args.report_level_json)
    elif detail is not None:
        rll = detail.get("reportLevelList")
        if rll:
            converted = _report_level_param_from_detail(rll)
            report_level_list = converted if converted is not None else []
        else:
            report_level_list = []
    else:
        report_level_list = None

    if detail:
        if receiver_names_nonempty:
            final_accept = accept_emp_ids
        else:
            final_accept = _emp_ids_from_detail(detail.get("acceptEmployeeList"))
        if cc_names_nonempty:
            final_cc = cc_emp_ids
        else:
            final_cc = _emp_ids_from_detail(detail.get("copyEmployeeList"))
        if new_uploads:
            final_files = file_vos
        else:
            final_files = _file_vos_from_detail(detail.get("fileList"))
        privacy_level = detail.get("privacyLevel") or "非涉密"
        template_raw = detail.get("templateId")
        template_id = str(template_raw) if template_raw is not None else None
        plan_raw = args.plan_id if args.plan_id is not None else detail.get("planId")
        plan_id = str(plan_raw) if plan_raw is not None else None
        # CLI 约定正文为 HTML，与 --content-html 一致，避免沿用详情里 markdown 与 HTML 混用
        content_type = "html"
    else:
        final_accept = accept_emp_ids
        final_cc = cc_emp_ids
        final_files = file_vos
        privacy_level = "非涉密"
        template_id = None
        plan_id = str(args.plan_id) if args.plan_id is not None else None
        content_type = "html"

    # 5.1/5.23：接收人以 reportLevelList 为准；acceptEmpIdList 仅在 reportLevelList 为空时兜底。
    # 更新草稿且用户显式传 --receivers 时，必须把新人写入 reportLevelList，否则详情仍显示旧 empList。
    if (
        receiver_names_nonempty
        and not args.report_level_json
        and isinstance(report_level_list, list)
        and len(report_level_list) > 0
    ):
        report_level_list = _apply_cli_receivers_to_report_level_list(
            report_level_list, final_accept
        )

    return {
        "main": args.title,
        "content_html": args.content_html,
        "content_type": content_type,
        "type_id": args.type_id,
        "grade": args.grade,
        "privacy_level": privacy_level,
        "plan_id": plan_id,
        "template_id": template_id,
        "accept_emp_id_list": final_accept,
        "copy_emp_id_list": final_cc,
        "report_level_list": report_level_list,
        "file_vo_list": final_files,
        "draft_id": args.draft_id,
    }


def save_draft_full(client, kwargs: dict) -> str | None:
    draft_id = kwargs.pop("draft_id", None)
    try:
        result = client.save_draft(draft_id=draft_id, **kwargs)
        rid = result.get("id")
        return str(rid) if rid is not None else None
    except CWorkError as e:
        print(json.dumps({"step": "save_draft", "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        return None


# ---------------------------------------------------------------------------
# Preview output（完整草稿，来自 5.25）
# ---------------------------------------------------------------------------

def build_preview_shell(args, confirmed: list[dict], cc_confirmed: list[dict],
                        file_vos: list[dict], *, from_api_detail: dict) -> dict:
    import re
    html = from_api_detail.get("contentHtml") or ""
    plain = re.sub(r"<[^>]+>", "", html)
    plain_stripped = plain.strip()
    plain_len = len(plain_stripped)

    # summary.contentPreview：极短正文不截断，避免占位符被「摘要」误伤；仅超长纯文本才截断
    preview_cap = 4000
    if len(plain) <= preview_cap:
        content_preview = plain
    else:
        content_preview = plain[:preview_cap] + "…"

    # confirmPrompt 内嵌正文：用纯文本预览，避免重复塞入整段 HTML；短正文全文展示便于审核
    prompt_body_cap = 2000
    prompt_plain = plain if len(plain) <= prompt_body_cap else plain[:prompt_body_cap] + "…"

    preview_warnings: list[str] = []
    if plain_len < 50:
        preview_warnings.append(
            f"正文去标签后仅 {plain_len} 个字符，可能为过短或占位内容，发送前请与用户确认"
        )

    accept_names = [e["name"] for e in confirmed]
    cc_names = [e["name"] for e in cc_confirmed]

    summary: dict = {
        "title": from_api_detail.get("main"),
        "grade": from_api_detail.get("grade"),
        "typeId": from_api_detail.get("typeId"),
        "planId": from_api_detail.get("planId"),
        "contentType": from_api_detail.get("contentType"),
        "receiversResolved": accept_names,
        "ccResolved": cc_names,
        "attachmentsThisRun": [{"name": f["name"]} for f in file_vos],
        "contentPlainText": plain,
        "contentPreview": content_preview,
        "contentPlainLength": plain_len,
    }
    if preview_warnings:
        summary["previewWarnings"] = preview_warnings

    warn_prefix = ("⚠ " + preview_warnings[0] + "\n\n") if preview_warnings else ""
    confirm_prompt = (
        warn_prefix
        + "【请用户确认以下完整草稿后再发送】\n"
        f"标题：{from_api_detail.get('main')}\n"
        f"优先级：{from_api_detail.get('grade')}\n"
        "正文（纯文本预览；完整富文本见 draftDetail.contentHtml）：\n"
        f"{prompt_plain}\n"
        f"接收人（解析结果）：{', '.join(accept_names) or '（沿用草稿详情）'}\n"
        f"抄送：{', '.join(cc_names) or '（沿用草稿详情）'}\n"
        f"附件：{json.dumps(from_api_detail.get('fileList') or [], ensure_ascii=False)}\n"
        f"流程节点 reportLevelList：{json.dumps(from_api_detail.get('reportLevelList') or [], ensure_ascii=False)}\n"
        "\n用户同意后，执行：--draft-id <汇报id> --confirm-send"
    )

    return {
        "reportId": from_api_detail.get("id"),
        "note": (
            "以下为接口 5.25 返回的完整草稿数据（draftDetail），请向用户展示全文后再发送。"
            "确认无误后使用 --draft-id <汇报id> --confirm-send。"
        ),
        "draftDetail": from_api_detail,
        "summary": summary,
        "confirmPrompt": confirm_prompt,
    }


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

    send_only = bool(args.confirm_send and args.draft_id and not args.preview_only)

    if send_only:
        if args.title is not None or args.content_html is not None:
            print(json.dumps({
                "success": False,
                "error": "发送-only 模式请勿再传 --title/--content-html；仅需 --draft-id 与 --confirm-send",
            }, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)
    else:
        if not args.title or args.content_html is None:
            print(json.dumps({
                "success": False,
                "error": "保存草稿需要 --title 与 --content-html（或使用 --draft-id + --confirm-send 仅发出）",
            }, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)

    client = make_client()

    if send_only:
        try:
            ok = client.submit_draft(args.draft_id)
            print(json.dumps({
                "success": bool(ok),
                "reportId": args.draft_id,
                "submitted": bool(ok),
                "message": "已通过 5.27 将草稿转为正式汇报" if ok else "5.27 返回未成功",
            }, ensure_ascii=False, indent=2))
            sys.exit(0 if ok else 1)
        except CWorkError as e:
            print(json.dumps({
                "success": False,
                "error": str(e),
                "reportId": args.draft_id,
            }, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)

    receiver_names = [n.strip() for n in args.receivers.split(",") if n.strip()]
    cc_names = [n.strip() for n in args.cc_names.split(",") if n.strip()]
    receiver_nonempty = bool(receiver_names)
    cc_nonempty = bool(cc_names)

    resolved = resolve_receivers(client, receiver_names)
    confirmed, errors = validate_receivers(resolved)
    cc_resolved = resolve_receivers(client, cc_names)
    cc_confirmed, cc_errors = validate_receivers(cc_resolved)

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

    accept_emp_ids = [str(e["empId"]) for e in confirmed]
    cc_emp_ids = [str(e["empId"]) for e in cc_confirmed]

    detail: dict | None = None
    if args.draft_id:
        try:
            detail = client.get_draft_detail(args.draft_id)
        except CWorkError as e:
            print(json.dumps({
                "success": False,
                "step": "get_draft_detail",
                "error": str(e),
            }, ensure_ascii=False), file=sys.stderr)
            sys.exit(1)

    file_vos = upload_files(client, args.file_paths, args.file_names)
    new_uploads = bool(args.file_paths)

    kwargs = build_save_draft_kwargs(
        args,
        detail=detail,
        accept_emp_ids=accept_emp_ids,
        cc_emp_ids=cc_emp_ids,
        file_vos=file_vos,
        receiver_names_nonempty=receiver_nonempty,
        cc_names_nonempty=cc_nonempty,
        new_uploads=new_uploads,
    )
    saved_report_id = save_draft_full(client, kwargs)

    if not saved_report_id:
        print(json.dumps({
            "success": False,
            "step": "save_draft",
            "message": "草稿保存失败",
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    try:
        fresh_detail = client.get_draft_detail(saved_report_id)
    except CWorkError as e:
        print(json.dumps({
            "success": False,
            "step": "get_draft_detail",
            "error": str(e),
            "reportId": saved_report_id,
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    preview = build_preview_shell(
        args, confirmed, cc_confirmed, file_vos, from_api_detail=fresh_detail,
    )
    preview["success"] = True
    # draftId：历史 JSON 键名，值为汇报 id，与 reportId / draftDetail.id 相同（非草稿箱记录 id）
    preview["draftId"] = saved_report_id

    if not args.confirm_send or args.preview_only:
        preview["nextStep"] = (
            "已向用户展示完整草稿（draftDetail）并确认无误后，再执行："
            f"--draft-id {saved_report_id} --confirm-send"
        )
        if args.preview_only and args.confirm_send:
            preview["noteOnFlags"] = "已指定 --preview-only，不会发出；忽略 --confirm-send"
        print(json.dumps(preview, ensure_ascii=False, indent=2))
        return

    try:
        ok = client.submit_draft(saved_report_id)
    except CWorkError as e:
        print(json.dumps({
            "success": False,
            "step": "submit_draft_5_27",
            "error": str(e),
            "draftId": saved_report_id,
        }, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)

    if not ok:
        print(json.dumps({
            "success": False,
            "step": "submit_draft_5_27",
            "draftId": saved_report_id,
            "message": "5.27 返回未成功",
        }, ensure_ascii=False, indent=2))
        sys.exit(1)

    print(json.dumps({
        "success": True,
        "reportId": saved_report_id,
        "submitted": True,
        "receivers": accept_emp_ids,
        "cc": cc_emp_ids,
        "attachmentsThisRun": len(file_vos),
        "message": "已通过 5.27 将草稿转为正式汇报",
    }, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
