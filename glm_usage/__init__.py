#!/usr/bin/env python3
"""查询 GLM Coding Plan 用量统计

用法:
  glm_usage status            查看配额用量
  glm_usage status --json     JSON 格式输出
  glm_usage token -d 3        过去 3 天的 Token 消耗
  glm_usage token -h 5 -j     过去 5 小时的 Token 消耗 (JSON)
"""

import argparse
import sys

from .commands import show_quota, show_token
from .config import get_token


def _add_common_args(parser: argparse.ArgumentParser):
    """为子命令添加通用参数。"""
    parser.add_argument("-j", "--json", action="store_true", help="以 JSON 格式输出")
    parser.add_argument("config", nargs="?", default=None, help="指定配置文件路径")


def main():
    parser = argparse.ArgumentParser(
        prog="glm_usage",
        description="查询 GLM Coding Plan 用量统计",
    )
    sub = parser.add_subparsers(dest="command")

    # status 子命令
    st = sub.add_parser("status", aliases=["st"], help="查看配额用量")
    _add_common_args(st)

    # token 子命令
    tk = sub.add_parser("token", help="查看 Token 消耗明细", add_help=False)
    group = tk.add_mutually_exclusive_group(required=True)
    group.add_argument("-d", "--day", type=int, metavar="N", help="过去 N 天")
    group.add_argument("-h", "--hour", type=int, metavar="N", help="过去 N 小时")
    _add_common_args(tk)

    args = parser.parse_args()

    if args.command in ("status", "st"):
        token = get_token(args.config)
        show_quota(token, as_json=args.json)
    elif args.command == "token":
        token = get_token(args.config)
        show_token(token, days=args.day, hours=args.hour, as_json=args.json)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
