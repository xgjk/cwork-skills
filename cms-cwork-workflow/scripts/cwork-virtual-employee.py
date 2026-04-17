#!/usr/bin/env python3
"""
cwork-virtual-employee.py
虚拟员工管理：创建 / 列表 / 修改 / 删除
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from cwork_client import CWorkError, apply_params_file_pre_parse, make_client


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="CWork virtual employee management")
    p.add_argument(
        "--mode",
        required=True,
        choices=["add", "list", "update", "delete"],
        help="操作模式",
    )
    p.add_argument("--id", dest="virtual_emp_id", default=None, help="虚拟员工 ID")
    p.add_argument("--name", default=None, help="虚拟员工名称")
    p.add_argument("--remark", default=None, help="虚拟员工备注")
    p.add_argument("--params-file", default=None, help="UTF-8 JSON 参数文件")
    return p.parse_args()


def main() -> None:
    apply_params_file_pre_parse()
    args = parse_args()

    try:
        client = make_client()

        if args.mode == "add":
            if not args.name:
                raise ValueError("mode=add 时必须提供 --name")
            vid = client.add_virtual_employee(name=args.name, remark=args.remark)
            print(
                json.dumps(
                    {
                        "success": True,
                        "mode": "add",
                        "virtualEmpId": vid,
                        "name": args.name,
                        "remark": args.remark,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return

        if args.mode == "list":
            rows = client.list_virtual_employees()
            print(
                json.dumps(
                    {"success": True, "mode": "list", "count": len(rows), "list": rows},
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return

        if args.mode == "update":
            if not args.virtual_emp_id:
                raise ValueError("mode=update 时必须提供 --id")
            ok = client.update_virtual_employee(
                virtual_emp_id=args.virtual_emp_id, name=args.name, remark=args.remark
            )
            print(
                json.dumps(
                    {
                        "success": bool(ok),
                        "mode": "update",
                        "virtualEmpId": str(args.virtual_emp_id),
                        "name": args.name,
                        "remark": args.remark,
                    },
                    ensure_ascii=False,
                    indent=2,
                )
            )
            return

        if not args.virtual_emp_id:
            raise ValueError("mode=delete 时必须提供 --id")
        ok = client.delete_virtual_employee(args.virtual_emp_id)
        print(
            json.dumps(
                {
                    "success": bool(ok),
                    "mode": "delete",
                    "virtualEmpId": str(args.virtual_emp_id),
                },
                ensure_ascii=False,
                indent=2,
            )
        )
    except (CWorkError, ValueError, OSError, json.JSONDecodeError) as e:
        print(json.dumps({"success": False, "error": str(e)}, ensure_ascii=False), file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
