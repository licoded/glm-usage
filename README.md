# GLM Usage

中文 | [English](README_EN.md)

[GLM Coding Plan](https://docs.z.ai) 用量查询 CLI 工具。支持查看配额用量、Token 消耗明细，以及 JSON 格式输出。

> **GLM Coding Plan** 是 [Z.ai](https://z.ai)（智谱 AI 国际站）推出的编程订阅套餐，可在 Claude Code、Cline 等编码工具中使用 GLM 系列模型。

## 安装

```bash
# 需要 uv 或 pip
uv tool install git+https://github.com/licoded/glm-usage.git

# 或者从源码安装
git clone https://github.com/licoded/glm-usage.git
cd glm_usage
uv tool install -e .
```

## 前置配置

工具会按以下顺序查找 `ANTHROPIC_AUTH_TOKEN`：

1. 环境变量 `ANTHROPIC_AUTH_TOKEN`
2. `~/.claude/settings.json` 中的 `env.ANTHROPIC_AUTH_TOKEN`

如果你已经用 Claude Code 接入了 Z.ai，通常无需额外配置。

## 用法

```
glm_usage status        查看配额用量（5h / 周 / 月 MCP）
glm_usage st            同上（简写）
glm_usage token -d 7    查看过去 7 天的 Token 消耗明细
glm_usage token -h 5    查看过去 5 小时的 Token 消耗明细
```

所有子命令都支持 `--json` / `-j` 以 JSON 格式输出：

```bash
glm_usage st --json
glm_usage token -d 7 -j
```

指定其他配置文件：

```bash
glm_usage st /path/to/config.json
```

## 示例输出

### 配额用量

```
$ glm_usage st
  项目                           已用
  ─────────────────────────────────────────────────
  Token (5小时窗口)              ██░░░░░░░░░░░░░░░░░░ 13%
    06-04 05:26 ~ 06-04 10:26
  Token (周额度)                 ██████░░░░░░░░░░░░░░ 32%
    05-30 18:35 ~ 06-06 18:35
  MCP (月) 224/4000              █░░░░░░░░░░░░░░░░░░░ 5%
    search-prime                 134
    web-reader                   90
    zread                        0
```

### Token 消耗明细

```
$ glm_usage token -d 7
  Token 消耗明细（过去 7 天）

  模型          Token 消耗   占比
  ─────────────────────────────────
  GLM-5.1       259.7M     98.6%
  GLM-5-Turbo   583        0.0%
  GLM-4.7       198.3K     0.1%
  GLM-4.6V      10.4K      0.0%
  GLM-4.5       13.5M      5.1%
  GLM-4.5-Air   3.8M       1.5%
  ─────────────────────────────────
  合计          263.5M
```

### JSON 输出

```bash
$ glm_usage st -j
[
  {
    "percentage": 13,
    "nextResetTime": 1780539971291,
    "window": "5h",
    "start": "2026-06-04 05:26",
    "end": "2026-06-04 10:26"
  },
  ...
]
```

## GLM Coding Plan 限额规则

### 计量单位

单位是 **Prompts（请求次数）**，不是 Tokens。每个 prompt 内部触发 15-20 次模型推理，但配额按 prompt 计。

### 各套餐基础额度

| 套餐 | 5 小时滑动窗口 | 每周 | 每月 |
|------|-------------|------|------|
| Lite | ~80 | ~400 | ~1,600 |
| Pro | ~400 | ~2,000 | ~8,000 |
| Max | ~1,600 | ~8,000 | ~32,000 |

### 动态消耗倍率

| 模型 | 高峰期 (UTC+8 14:00–18:00) | 非高峰期 |
|------|---------------------------|---------|
| 常规模型（GLM-4.7 等） | 1× | 1× |
| 高级模型（GLM-5.1 / GLM-5 / GLM-5-Turbo） | 3× | 2× |

> **限时福利**：至 2026 年 6 月底，非高峰期调用高级模型按 **1×** 扣除。

### 周期机制

- **5h 滑动窗口**：每个 prompt 在精确 5 小时后单独恢复额度。窗口更新为离散式（至少 5-10 分钟变化一次），非实时滑动。
- **周额度**：固定周期点统一重置。
- **月度 MCP**：固定周期点重置。

## Z.ai API 参考

所有 API 时间均为 **UTC+8**（北京时间），认证使用 `Authorization: <ANTHROPIC_AUTH_TOKEN>`（无 Bearer 前缀）。

### 配额查询

```
GET /api/monitor/usage/quota/limit
```

返回各窗口的 `percentage`、`nextResetTime`、套餐 `level`。

### 模型用量

```
GET /api/monitor/usage/model-usage?startTime=...&endTime=...
```

返回逐小时的 `modelCallCount`（即 prompt 数）和各模型的 token 消耗。时间格式 `yyyy-MM-dd HH:mm:ss`（UTC+8），粒度为整小时。

> **关键发现**：`modelCallCount` 是 prompt 数（用户查询次数），不是模型内部调用次数。实测周窗口偏差 -4.5%，5h 窗口（需边界扣减）偏差 -6.1%。

## 项目结构

```
glm_usage/
  __init__.py    CLI 入口（argparse）
  config.py      Token / 配置文件读取
  client.py      Z.ai API 调用
  display.py     终端显示工具函数
  commands.py    子命令实现
```

## 开发

```bash
# 安装（可编辑模式）
uv tool install -e .

# 运行测试
glm_usage st
glm_usage token -d 1

# 代码规范：单文件不超过 180 行，需要拆分和抽象
# 时区规范：所有时间统一使用 UTC+8，禁止 timezone.utc
```

## License

MIT
