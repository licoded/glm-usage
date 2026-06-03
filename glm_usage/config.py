import json
import os
import sys
from pathlib import Path

DEFAULT_CONFIG = Path.home() / ".claude" / "settings.json"


def get_token(config_path: str | None = None) -> str:
    """获取 ANTHROPIC_AUTH_TOKEN，优先环境变量，其次配置文件。"""
    token = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if token:
        return token

    path = Path(config_path) if config_path else DEFAULT_CONFIG
    if not path.exists():
        print(f"错误: 配置文件不存在 {path}", file=sys.stderr)
        sys.exit(1)

    with open(path) as f:
        data = json.load(f)

    token = data.get("env", {}).get("ANTHROPIC_AUTH_TOKEN", "")
    if not token:
        print(f"错误: 在 {path} 的 env 中未找到 ANTHROPIC_AUTH_TOKEN", file=sys.stderr)
        sys.exit(1)

    return token
