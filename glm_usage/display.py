import unicodedata


def display_width(s: str) -> int:
    """计算字符串的终端显示宽度（CJK 字符占2列）。"""
    return sum(2 if unicodedata.east_asian_width(ch) in ("W", "F") else 1 for ch in s)


def pad(s: str, width: int) -> str:
    """按显示宽度右填充空格。"""
    return s + " " * (width - display_width(s))


def bar(pct: int, width: int = 20) -> str:
    """生成进度条。"""
    filled = int(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def fmt_tokens(n: int) -> str:
    """格式化 token 数量为人类可读格式。"""
    if n >= 1_000_000_000:
        return f"{n / 1_000_000_000:.1f}B"
    if n >= 1_000_000:
        return f"{n / 1_000_000:.1f}M"
    if n >= 1_000:
        return f"{n / 1_000:.1f}K"
    return str(n)
