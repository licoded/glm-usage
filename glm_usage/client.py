import json
from urllib.parse import quote_plus
from urllib.request import Request, urlopen

API_BASE = "https://api.z.ai"


def api_get(token: str, path: str, params: dict | None = None) -> dict:
    """调用 Z.ai 监控 API，返回 JSON 数据。"""
    url = f"{API_BASE}{path}"
    if params:
        qs = "&".join(f"{k}={quote_plus(str(v))}" for k, v in params.items())
        url = f"{url}?{qs}"

    req = Request(url)
    req.add_header("Authorization", token)
    req.add_header("Content-Type", "application/json")

    with urlopen(req) as resp:
        return json.loads(resp.read())


def fetch_quota(token: str) -> dict:
    """获取配额限制数据。"""
    return api_get(token, "/api/monitor/usage/quota/limit")


def fetch_model_usage(token: str, start: str, end: str) -> dict:
    """获取模型用量数据。"""
    return api_get(token, "/api/monitor/usage/model-usage", {
        "startTime": start,
        "endTime": end,
    })
