#!/usr/bin/env python3
"""
cwork-business-unit.py
业务单元管理：保存/更新、列表、详情、删除

Usage:
  # 新增
  python3 scripts/cwork-business-unit.py save \
    --name "工作协同开发小组" \
    --description "研发周报流程" \
    --node-list-json ./nodes.json

  # 更新（传 --id）
  python3 scripts/cwork-business-unit.py save \
    --id 2043594941317410818 \
    --name "工作协同开发小组（更新）" \
    --node-list-json ./nodes.json

  # 查询全部
  python3 scripts/cwork-business-unit.py list

  # 查询详情
  python3 scripts/cwork-business-unit.py get --id 2043594941317410818

  # 删除
  python3 scripts/cwork-business-unit.py delete --id 2043594941317410818
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cwork_client import CWorkError, apply_params_file_pre_parse, make_client


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Manage CWork business units")
    p.add_argument(
        "--params-file",
        dest="params_file",
        default=None,
        help="UTF-8 JSON 文件路径，从文件读取参数（键名与长参数一致）",
    )
    sub = p.add_subparsers(dest="action", required=True)

    save = sub.add_parser("save", help="保存或更新业务单元")
    save.add_argument("--id", dest="business_unit_id", default=None, help="业务单元 ID；传入代表更新")
    save.add_argument("--name", required=True, help="方案名称")
    save.add_argument("--description", default=None, help="方案说明")
    save.add_argument(
        "--node-list-json",
        required=True,
        help="UTF-8 JSON 文件路径，内容为 nodeList 数组",
    )
    save.add_argument("--dry-run", action="store_true", help="仅校验参数，不调用 API")

    list_cmd = sub.add_parser("list", help="查询我的所有业务单元")
    list_cmd.add_argument("--dry-run", action="store_true", help="仅输出说明，不调用 API")

    get = sub.add_parser("get", help="查询业务单元详情")
    get.add_argument("--id", dest="business_unit_id", required=True, help="业务单元 ID")
    get.add_argument("--dry-run", action="store_true", help="仅校验参数，不调用 API")

    delete = sub.add_parser("delete", help="删除业务单元")
    delete.add_argument("--id", dest="business_unit_id", required=True, help="业务单元 ID")
    delete.add_argument("--dry-run", action="store_true", help="仅校验参数，不调用 API")

    return p.parse_args()


def load_node_list(path: str) -> list[dict]:
    raw = Path(path).read_text(encoding="utf-8-sig")
    data = json.loads(raw)
    if not isinstance(data, list):
        raise ValueError("node-list-json 根节点必须是数组")
    if not data:
        raise ValueError("nodeList 不能为空")

    allowed_types = {"read", "suggest", "decide"}
    out: list[dict] = []
    for idx, node in enumerate(data):
        if not isinstance(node, dict):
            raise ValueError(f"nodeList[{idx}] 必须是对象")
        node_name = node.get("nodeName")
        node_type = node.get("nodeType")
        emp_list = node.get("empList")
        if not node_name:
            raise ValueError(f"nodeList[{idx}].nodeName 必填")
        if node_type not in allowed_types:
            raise ValueError(
                f"nodeList[{idx}].nodeType 仅支持 read/suggest/decide，当前为: {node_type}"
            )
        if not isinstance(emp_list, list) or not emp_list:
            raise ValueError(f"nodeList[{idx}].empList 必须为非空数组")

        normalized_emp_list: list[dict] = []
        for j, emp in enumerate(emp_list):
            if not isinstance(emp, dict):
                raise ValueError(f"nodeList[{idx}].empList[{j}] 必须是对象")
            emp_id = emp.get("id")
            emp_name = emp.get("name")
            if emp_id is None or str(emp_id).strip() == "":
                raise ValueError(f"nodeList[{idx}].empList[{j}].id 必填（empId）")
            if not emp_name:
                raise ValueError(f"nodeList[{idx}].empList[{j}].name 必填")
            normalized_emp_list.append({"id": str(emp_id), "name": str(emp_name)})

        out.append(
            {
                "nodeName": str(node_name),
                "nodeType": str(node_type),
                "empList": normalized_emp_list,
            }
        )
    return out


def main() -> None:
    apply_params_file_pre_parse()
    args = parse_args()

    try:
        if args.action == "save":
            node_list = load_node_list(args.node_list_json)
            if args.dry_run:
                print(
                    json.dumps(
                        {
                            "success": True,
                            "action": "save",
                            "dryRun": True,
                            "payload": {
                                "id": args.business_unit_id,
                                "name": args.name,
                                "description": args.description,
                                "nodeList": node_list,
                            },
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return
            client = make_client()
            business_unit_id = client.save_business_unit(
                name=args.name,
                description=args.description,
                node_list=node_list,
                business_unit_id=args.business_unit_id,
            )
            print(
                json.dumps(
                    {
                        "success": True,
                        "action": "save",
                        "businessUnitId": business_unit_id,
                        "mode": "update" if args.business_unit_id else "create",
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return

        if args.action == "list":
            if args.dry_run:
                print(json.dumps({"success": True, "action": "list", "dryRun": True}, ensure_ascii=False, indent=2))
                return
            client = make_client()
            data = client.list_all_business_units()
            print(
                json.dumps(
                    {
                        "success": True,
                        "action": "list",
                        "count": len(data),
                        "data": data,
                        "message": (
                            "未查询到业务单元（可能是未配置，或当前 appKey/access-token 对应的用户下暂无数据）"
                            if not data
                            else "查询成功"
                        ),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return

        if args.action == "get":
            if args.dry_run:
                print(
                    json.dumps(
                        {
                            "success": True,
                            "action": "get",
                            "dryRun": True,
                            "businessUnitId": str(args.business_unit_id),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return
            client = make_client()
            data = client.get_business_unit_by_id(args.business_unit_id)
            print(json.dumps({"success": True, "action": "get", "data": data}, ensure_ascii=False, indent=2))
            return

        if args.action == "delete":
            if args.dry_run:
                print(
                    json.dumps(
                        {
                            "success": True,
                            "action": "delete",
                            "dryRun": True,
                            "businessUnitId": str(args.business_unit_id),
                        },
                        ensure_ascii=False,
                        indent=2,
                    )
                )
                return
            client = make_client()
            ok = client.delete_business_unit(args.business_unit_id)
            print(
                json.dumps(
                    {
                        "success": bool(ok),
                        "action": "delete",
                        "businessUnitId": str(args.business_unit_id),
                        "deleted": bool(ok),
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return

    except (CWorkError, OSError, ValueError, json.JSONDecodeError) as e:
        print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
