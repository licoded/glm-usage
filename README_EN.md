# GLM Usage

English | [中文](README.md)

A CLI tool for querying [GLM Coding Plan](https://docs.z.ai) usage statistics. View quota consumption, token usage breakdown, and JSON output.

> **GLM Coding Plan** is a coding subscription by [Z.ai](https://z.ai) (Zhipu AI International) that provides GLM models for use in Claude Code, Cline, and other coding tools.

## Installation

```bash
# Requires uv or pip
uv tool install git+https://github.com/licoded/glm-usage.git

# Or install from source
git clone https://github.com/licoded/glm-usage.git
cd glm_usage
uv tool install -e .
```

## Configuration

The tool looks for `ANTHROPIC_AUTH_TOKEN` in this order:

1. Environment variable `ANTHROPIC_AUTH_TOKEN`
2. `env.ANTHROPIC_AUTH_TOKEN` in `~/.claude/settings.json`

If you've already set up Claude Code with Z.ai, no extra configuration is needed.

## Usage

```
glm_usage status        View quota usage (5h / weekly / monthly MCP)
glm_usage st            Same as above (shorthand)
glm_usage token -d 7    View token usage breakdown for the past 7 days
glm_usage token -h 5    View token usage breakdown for the past 5 hours
```

All subcommands support `--json` / `-j` for JSON output:

```bash
glm_usage st --json
glm_usage token -d 7 -j
```

Specify a custom config file:

```bash
glm_usage st /path/to/config.json
```

## Example Output

### Quota Usage

```
$ glm_usage st
  Item                            Used
  ─────────────────────────────────────────────────
  Token (5h Window)               ██░░░░░░░░░░░░░░░░░░ 13%
    06-04 05:26 ~ 06-04 10:26
  Token (Weekly)                  ██████░░░░░░░░░░░░░░ 32%
    05-30 18:35 ~ 06-06 18:35
  MCP (Monthly) 224/4000          █░░░░░░░░░░░░░░░░░░░ 5%
    search-prime                  134
    web-reader                    90
    zread                         0
```

### Token Usage Breakdown

```
$ glm_usage token -d 7
  Token Usage Breakdown (Past 7 Days)

  Model         Token Usage   Share
  ─────────────────────────────────
  GLM-5.1       259.7M       98.6%
  GLM-5-Turbo   583           0.0%
  GLM-4.7       198.3K        0.1%
  GLM-4.6V      10.4K         0.0%
  GLM-4.5       13.5M         5.1%
  GLM-4.5-Air   3.8M          1.5%
  ─────────────────────────────────
  Total         263.5M
```

### JSON Output

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

## GLM Coding Plan Quota Rules

### Unit of Measurement

The unit is **Prompts (request count)**, not Tokens. Each prompt internally triggers 15–20 model inferences, but quota is counted per prompt.

### Plan Limits

| Plan | 5h Sliding Window | Weekly | Monthly |
|------|-------------------|--------|---------|
| Lite | ~80 | ~400 | ~1,600 |
| Pro | ~400 | ~2,000 | ~8,000 |
| Max | ~1,600 | ~8,000 | ~32,000 |

### Dynamic Consumption Multiplier

| Model | Peak (UTC+8 14:00–18:00) | Off-Peak |
|-------|-------------------------|----------|
| Standard (GLM-4.7, etc.) | 1× | 1× |
| Advanced (GLM-5.1 / GLM-5 / GLM-5-Turbo) | 3× | 2× |

> **Limited-time offer**: Through the end of June 2026, advanced models consume only **1×** quota during off-peak hours.

### Cycle Mechanism

- **5h Sliding Window**: Each prompt recovers its quota exactly 5 hours after consumption. Window updates are discrete (changes every 5–10+ minutes), not real-time.
- **Weekly**: Resets at a fixed cycle point.
- **Monthly MCP**: Resets at a fixed cycle point.

## Z.ai API Reference

All API times are in **UTC+8** (Beijing Time). Authentication: `Authorization: <ANTHROPIC_AUTH_TOKEN>` (no Bearer prefix).

### Quota Query

```
GET /api/monitor/usage/quota/limit
```

Returns `percentage`, `nextResetTime`, and plan `level` for each window.

### Model Usage

```
GET /api/monitor/usage/model-usage?startTime=...&endTime=...
```

Returns hourly `modelCallCount` (prompt count) and per-model token consumption. Time format: `yyyy-MM-dd HH:mm:ss` (UTC+8), granularity: whole hours.

> **Key Finding**: `modelCallCount` is the prompt count (user queries), not internal model invocations. Verified: weekly window deviation -4.5%, 5h window (with boundary deduction) deviation -6.1%.

## Project Structure

```
glm_usage/
  __init__.py    CLI entry point (argparse)
  config.py      Token / config file reader
  client.py      Z.ai API client
  display.py     Terminal display utilities
  commands.py    Subcommand implementations
```

## Development

```bash
# Install (editable mode)
uv tool install -e .

# Test
glm_usage st
glm_usage token -d 1

# Code style: max 180 lines per file, split and abstract as needed
# Timezone: always use UTC+8, never timezone.utc
```

## License

MIT
