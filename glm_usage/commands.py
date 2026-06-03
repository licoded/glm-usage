import json
from datetime import datetime, timedelta, timezone

from .client import fetch_quota, fetch_model_usage
from .display import bar, display_width, fmt_tokens, pad

UTC8 = timezone(timedelta(hours=8))


def _now() -> datetime:
    """当前 UTC+8 时间。"""
    return datetime.now(UTC8)


def _from_ts(ms: int) -> datetime:
    """epoch ms 转 UTC+8 时间。"""
    return datetime.fromtimestamp(ms / 1000, tz=UTC8)


def _fmt_window(start: datetime, end: datetime) -> str:
    """格式化时间区间显示。"""
    return f"{start.strftime('%m-%d %H:%M')} ~ {end.strftime('%m-%d %H:%M')}"


def _build_quota_result(token: str) -> list[dict]:
    """构建配额数据结构。"""
    data = fetch_quota(token)["data"]
    result = []
    for item in data["limits"]:
        end = _from_ts(item["nextResetTime"])
        entry = {"percentage": item["percentage"], "nextResetTime": item["nextResetTime"]}
        if item["type"] == "TOKENS_LIMIT":
            window = "5h" if item["unit"] == 3 else "weekly"
            duration = timedelta(hours=5) if item["unit"] == 3 else timedelta(days=7)
            entry["window"] = window
            entry["start"] = (end - duration).strftime("%Y-%m-%d %H:%M")
            entry["end"] = end.strftime("%Y-%m-%d %H:%M")
        elif item["type"] == "TIME_LIMIT":
            entry["window"] = "monthly_mcp"
            entry["current"] = item["currentValue"]
            entry["total"] = item["usage"]
            entry["details"] = item.get("usageDetails", [])
        result.append(entry)
    return result


def show_quota(token: str, as_json: bool = False):
    """显示配额用量（5小时/周/月MCP）。"""
    if as_json:
        print(json.dumps(_build_quota_result(token), ensure_ascii=False, indent=2))
        return

    data = fetch_quota(token)["data"]
    lines = []
    for item in data["limits"]:
        pct = item["percentage"]
        end = _from_ts(item["nextResetTime"])
        if item["type"] == "TOKENS_LIMIT":
            window = "5小时窗口" if item["unit"] == 3 else "周额度"
            duration = timedelta(hours=5) if item["unit"] == 3 else timedelta(days=7)
            start = end - duration
            lines.append((f"Token ({window})", f"{bar(pct)} {pct}%"))
            lines.append((f"  {_fmt_window(start, end)}", ""))
        elif item["type"] == "TIME_LIMIT":
            cur, total = item["currentValue"], item["usage"]
            lines.append((f"MCP (月) {cur}/{total}", f"{bar(pct)} {pct}%"))
            for d in item.get("usageDetails", []):
                lines.append((f"  {d['modelCode']}", str(d["usage"])))

    name_w = max(display_width(r[0]) for r in lines) + 2
    print(f"  {pad('项目', name_w)}  已用")
    print(f"  {'─' * (name_w + 20)}")
    for name, val in lines:
        print(f"  {pad(name, name_w)}  {val}")


def _build_token_result(token: str, days: int | None = None,
                        hours: int | None = None) -> dict:
    """构建模型用量数据结构。"""
    now = _now()
    start = now - (timedelta(days=days) if days is not None else timedelta(hours=hours))
    time_fmt = "%Y-%m-%d %H:%M:%S"
    data = fetch_model_usage(token, start.strftime(time_fmt), now.strftime(time_fmt))["data"]
    total_usage = data["totalUsage"]
    return {
        "period": {
            "start": start.strftime("%Y-%m-%d %H:%M"),
            "end": now.strftime("%Y-%m-%d %H:%M"),
        },
        "totalTokens": total_usage["totalTokensUsage"],
        "totalPrompts": total_usage["totalModelCallCount"],
        "models": [
            {"name": m["modelName"], "tokens": m["totalTokens"]}
            for m in total_usage["modelSummaryList"]
        ],
    }


def show_token(token: str, days: int | None = None, hours: int | None = None,
               as_json: bool = False):
    """显示 Token 消耗明细（各模型用量）。"""
    if as_json:
        print(json.dumps(_build_token_result(token, days=days, hours=hours),
                         ensure_ascii=False, indent=2))
        return

    result = _build_token_result(token, days=days, hours=hours)
    period = f"过去 {days} 天" if days is not None else f"过去 {hours} 小时"
    total_tokens = result["totalTokens"]
    total_prompts = result["totalPrompts"]
    models = result["models"]

    col_model, col_tokens, col_pct = "模型", "Token 消耗", "占比"
    rows = [(m["name"], m["tokens"]) for m in models]
    model_w = max(display_width(col_model), *(display_width(r[0]) for r in rows)) + 2
    token_w = max(len(col_tokens), *(len(fmt_tokens(r[1])) for r in rows)) + 2

    print(f"  Token 消耗明细（{period}）")
    print()
    print(f"  {pad(col_model, model_w)} {col_tokens:<{token_w}} {col_pct}")
    print(f"  {'─' * (model_w + token_w + 10)}")
    for name, tokens in rows:
        pct = tokens / total_tokens * 100 if total_tokens else 0
        print(f"  {pad(name, model_w)} {fmt_tokens(tokens):<{token_w}} {pct:.1f}%")
    print(f"  {'─' * (model_w + token_w + 10)}")
    print(f"  {pad('合计', model_w)} {fmt_tokens(total_tokens):<{token_w}}")
    print(f"  {pad('Prompts', model_w)} {total_prompts}")
