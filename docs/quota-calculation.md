# 额度计算方式

## 核心概念

- **1 prompt = 1 user query**（一次用户提问）
- 每个 prompt 内部触发 15-20 次模型推理，但配额按 prompt 计
- `modelCallCount` 就是 prompt 数，不是模型调用次数
- API 只返回 `percentage`，需结合套餐基础额度反推具体数量
- **所有时间为 UTC+8**

## 5h 滑动窗口

### 窗口范围

从 `/api/monitor/usage/quota/limit` 获取 `nextResetTime`，窗口为：

```
start = nextResetTime - 5h
end   = nextResetTime
```

### 计算 prompts

1. 用 `/api/monitor/usage/model-usage` 查询 `start ~ end` 的逐小时数据
2. 汇总 `modelCallCount` 得到原始 prompts
3. **边界扣减**: 第一个小时可能包含窗口开始前（`start` 整点之前）的数据，需按时间比例扣除：

```python
first_hour_excess = (start.minute) / 60  # 窗口开始的整点之前占比
first_hour_prompts = modelCallCount[0] * (1 - first_hour_excess)
other_prompts = sum(modelCallCount[1:])
total_prompts = first_hour_prompts + other_prompts
```

4. 应用动态倍率（如需精确计算，需按每小时每模型分别计算）

### 验证结果

```
窗口: 05:26 ~ 10:26 (UTC+8)
原始: 264 prompts (05:00 时=193, 06:00 时=71)
线性扣减: 264 - 193 × 26/60 ≈ 180
API: 12% × 1600 = 192
偏差: -6.1% ✅
```

## 周窗口

### 窗口范围

```
start = nextResetTime(unit=6) - 7 days
end   = nextResetTime(unit=6)
```

### 计算 prompts

直接汇总 `modelCallCount` 即可，无需边界扣减（周窗口足够长，边界影响 <0.3%）：

```python
total_prompts = sum(modelCallCount for hours in window)
```

### 验证结果

```
modelCallCount: 2,369
API: 31% × 8000 = 2,480
偏差: -4.5% ✅
```

## 反推公式（无 model-usage 时）

```python
used_prompts = tier_limit * percentage / 100
remaining_prompts = tier_limit * (100 - percentage) / 100
```

适用于 5h 和周窗口，精度取决于套餐额度是否匹配。

## 动态倍率计算（需逐小时逐模型）

```python
ADVANCED = {'GLM-5.1', 'GLM-5', 'GLM-5-Turbo'}
PEAK_UTC8_HOURS = range(14, 18)  # UTC+8 14:00-18:00

for each hour:
    is_peak = hour_utc8 in PEAK_UTC8_HOURS
    hour_total_tokens = sum(model_tokens for all models)
    for each model:
        est_prompts = hour_prompts * (model_tokens / hour_total_tokens)
        is_advanced = model in ADVANCED
        if is_advanced:
            multiplier = 3 if is_peak else 1  # 福利期非高峰1×
        else:
            multiplier = 1
        consumed += est_prompts * multiplier
```

注意：按 token 占比分配 prompt 数会引入 ~12% 偏差（高级模型单次 prompt 消耗更多 token）。

## 各套餐基础额度

| 套餐 | 5h 滑动窗口 | 每周 | 每月 |
|------|-----------|------|------|
| Lite | 80 | 400 | 1,600 |
| Pro | 400 | 2,000 | 8,000 |
| Max | 1,600 | 8,000 | 32,000 |

## 动态倍率

- **高峰期**: UTC+8 14:00–18:00
- **高级模型**: GLM-5.1、GLM-5、GLM-5-Turbo
- 高峰 3×，非高峰 2×（福利期至 2026-06 底非高峰 1×）

## 周期机制

- **5h 滑动窗口**: 每个 prompt 在精确 5h 后单独恢复额度；nextResetTime = 最早活跃 prompt 的过期时间
  - 窗口更新是**离散的**，非实时滑动，至少 5-10 分钟才变化一次（保守估计 ≥30 分钟）
  - nextResetTime 和 percentage 不会秒级变化，短时间内多次查询结果相同
- **周额度**: 固定周期点统一重置（从 nextResetTime 获取）
