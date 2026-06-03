# API 接口发现

## 已确认的端点

### 1. 配额查询 `/api/monitor/usage/quota/limit`

- **认证**: `Authorization: <ANTHROPIC_AUTH_TOKEN>`（无 Bearer 前缀）
- **方法**: GET
- **返回**: `percentage`（百分比），不含具体 prompt 数量
- **时间**: nextResetTime 为 UTC+8 epoch ms

```json
{
  "limits": [
    {"type": "TOKENS_LIMIT", "unit": 3, "percentage": 12, "nextResetTime": 1780539971291},
    {"type": "TOKENS_LIMIT", "unit": 6, "percentage": 32, "nextResetTime": 1780742112996},
    {"type": "TIME_LIMIT", "unit": 5, "percentage": 5, "usage": 4000, "currentValue": 224, ...}
  ],
  "level": "max"
}
```

| 字段 | 含义 |
|------|------|
| `unit=3` | 5 小时滑动窗口 |
| `unit=6` | 周额度（固定周期重置） |
| `unit=5` | MCP 月度工具额度 |
| `level` | 套餐等级 (lite/pro/max) |
| `nextResetTime` | 窗口结束/重置时间（epoch ms，UTC+8） |

### 2. 模型用量 `/api/monitor/usage/model-usage`

- **认证**: 同上
- **方法**: GET
- **参数**: `startTime` / `endTime`（格式 `yyyy-MM-dd HH:mm:ss`，**UTC+8**）
- **粒度**: 按整小时
- **时间**: 返回的 x_time 为 UTC+8

| 字段 | 说明 |
|------|------|
| `x_time` | 逐小时时间轴（UTC+8） |
| `modelCallCount` | 逐小时总 prompt 数（不区分模型） |
| `modelDataList[].tokensUsage` | 逐模型逐小时 token 数（非 prompt 数） |

**限制**: 无逐模型逐小时的 prompt 数，只有逐模型逐小时的 token 消耗。API 只返回整小时粒度，无法精确到分钟。

### 3. 工具用量 `/api/monitor/usage/tool-usage`

- 同模型用量的参数格式
- 返回 `search-prime` / `web-reader` / `zread` 的调用次数

## 关键发现

### API 时间为 UTC+8

所有 API 的入参和返回时间均为 UTC+8（北京时间），不是 UTC。之前用 UTC 查询导致窗口错位。

### modelCallCount = prompt 数

官方说明："One prompt refers to one query. Each prompt is estimated to invoke the model 15–20 times."

实测验证：

| 假设 | 周窗口偏差 | 结论 |
|------|-----------|------|
| `modelCallCount / 15~20 = prompt 数` | -93%~-95% | ❌ |
| `modelCallCount = prompt 数` | -4.5% | ✅ |

**结论**: `modelCallCount` 就是 prompt 数（用户查询次数），不是模型内部调用次数。

## 验证结论

### 周窗口 ✅ 精确匹配

| 指标 | 数值 |
|------|------|
| modelCallCount | 2,369 |
| API percentage | 31% |
| Max 反推（8000×31%） | 2,480 |
| 偏差 | -4.5% ✅ |

### 5h 滑动窗口 ✅ 近似匹配（需边界扣减）

| 指标 | 数值 |
|------|------|
| 查询窗口 | 05:26 ~ 10:26 (UTC+8) |
| 原始 modelCallCount | 264（05:00 时=193, 06:00 时=71） |
| 线性扣减后（05:00~05:25 不在窗口内） | ~180 |
| API percentage | 12% |
| Max 反推（1600×12%） | 192 |
| 偏差 | -6.1% ✅ |

**偏差原因**: API 只返回整小时数据，无法精确切到 05:26。05:00 这个小时里有 26 分钟（05:00~05:25）不属于窗口，线性扣减是近似。

**窗口更新频率**: 5h 窗口并非实时滑动，nextResetTime 和 percentage 至少 5-10 分钟才变化一次（实测 12 秒内 3 次查询结果完全相同）。

### 其他限制

- **ZAI_API_KEY 无效**: 只有 `ANTHROPIC_AUTH_TOKEN`（Coding Plan Token）能调用监控接口
- **国内站需 Cookie**: open.bigmodel.cn 的监控接口不支持 API Key 认证，需浏览器 Cookie
