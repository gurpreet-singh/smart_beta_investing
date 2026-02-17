# Practical Implementation Guide - Dynamic Factor Tilt

## Allocation Ladder (2.5% Increments)

### Available Allocations
The strategy uses **13 discrete allocation levels** in 2.5% steps:

| Level | Momentum | Value | Signal Strength | Frequency (Nifty 200) |
|-------|----------|-------|-----------------|----------------------|
| 1 | 55.0% | 45.0% | Weakest | 12 months (4.8%) |
| 2 | 57.5% | 42.5% | Very Weak | 15 months (6.0%) |
| 3 | 60.0% | 40.0% | Weak | 13 months (5.2%) |
| 4 | 62.5% | 37.5% | Below Neutral | 15 months (6.0%) |
| 5 | 65.0% | 35.0% | Slightly Below | 15 months (6.0%) |
| 6 | 67.5% | 32.5% | Near Neutral | 15 months (6.0%) |
| **7** | **70.0%** | **30.0%** | **Neutral (Base)** | **46 months (18.5%)** |
| 8 | 72.5% | 27.5% | Slightly Above | 25 months (10.0%) |
| 9 | 75.0% | 25.0% | Above Neutral | 29 months (11.6%) |
| 10 | 77.5% | 22.5% | Strong | 17 months (6.8%) |
| 11 | 80.0% | 20.0% | Very Strong | 16 months (6.4%) |
| 12 | 82.5% | 17.5% | Extremely Strong | 20 months (8.0%) |
| 13 | 85.0% | 15.0% | Strongest | 11 months (4.4%) |

## Real-World Execution

### Monthly Rebalancing Process

**Step 1: Calculate Signal (End of Month)**
```
Composite Signal = 0.7 × (6M Mom Outperformance) + 0.3 × (3M Mom Outperformance)
Signal Percentile = Rank within last 36 months
```

**Step 2: Map to Allocation**
```
Raw Allocation = 55% + (30% × Signal Percentile)
Rounded Allocation = Round to nearest 2.5%
```

**Step 3: Rebalance Portfolio**
```
If current ≠ target:
    Sell difference from overweight factor
    Buy difference in underweight factor
```

### Example Execution (December 2024)

**Calculation:**
- 6M Momentum Outperformance: +15.2%
- 3M Momentum Outperformance: +8.7%
- Composite Signal: (0.7 × 15.2%) + (0.3 × 8.7%) = 13.25%
- 36M Percentile: 92nd percentile
- Raw Allocation: 55% + (30% × 0.92) = 82.6%
- **Rounded: 82.5% Momentum / 17.5% Value**

**Rebalancing:**
- Current: 72.5% Momentum / 27.5% Value
- Target: 82.5% Momentum / 17.5% Value
- **Action: Sell 10% Value, Buy 10% Momentum**

## Practical Advantages

### 1. Simple Execution
- ✅ Only 13 possible allocations
- ✅ Changes in 2.5% increments
- ✅ Easy to calculate position sizes
- ✅ Minimal transaction costs

### 2. Reduced Trading
**Rounding creates natural buffer:**
- Small signal changes don't trigger rebalancing
- Only trade when crossing 2.5% threshold
- Reduces whipsaws and costs

**Example:**
```
Month 1: Signal → 71.3% → Rounded to 70.0%
Month 2: Signal → 72.1% → Rounded to 72.5% → TRADE
Month 3: Signal → 71.8% → Rounded to 72.5% → NO TRADE
```

### 3. Portfolio Construction

**For ₹10L Portfolio:**

| Allocation | Momentum Amount | Value Amount |
|------------|----------------|--------------|
| 55/45 | ₹5,50,000 | ₹4,50,000 |
| 60/40 | ₹6,00,000 | ₹4,00,000 |
| 65/35 | ₹6,50,000 | ₹3,50,000 |
| **70/30** | **₹7,00,000** | **₹3,00,000** |
| 75/25 | ₹7,50,000 | ₹2,50,000 |
| 80/20 | ₹8,00,000 | ₹2,00,000 |
| 85/15 | ₹8,50,000 | ₹1,50,000 |

## Performance Impact of Rounding

### Before Rounding (Continuous)
- Nifty 200 CAGR: 20.26%
- Nifty 500 CAGR: 22.59%

### After Rounding (2.5% Steps)
- Nifty 200 CAGR: 20.21% (-0.05%)
- Nifty 500 CAGR: 22.63% (+0.04%)

**Impact: Negligible!**
- Performance difference < 0.1%
- Massively easier to implement
- Lower transaction costs offset any theoretical loss

## Allocation Distribution

### Nifty 200 (249 months)
```
Extreme Tilts (55-62.5%, 82.5-85%):  73 months (29%)
Moderate Tilts (65-67.5%, 75-80%):   92 months (37%)
Near Base (70-72.5%):                84 months (34%)
```

### Most Common Allocations
1. **70/30** - 46 months (base allocation)
2. **75/25** - 29 months (moderate momentum tilt)
3. **72.5/27.5** - 25 months (slight momentum tilt)
4. **82.5/17.5** - 20 months (strong momentum tilt)

## Implementation Checklist

### Monthly Process
- [ ] **Day 1-5**: Calculate month-end signals
- [ ] **Day 6-10**: Determine target allocation
- [ ] **Day 11-15**: Execute rebalancing trades
- [ ] **Day 16-20**: Verify positions
- [ ] **Day 21-30**: Monitor until next month

### Tools Needed
1. **Data Source**: NSE indices (Momentum 30, Value 30)
2. **Calculation**: Excel/Python for signal computation
3. **Execution**: Broker platform for trades
4. **Tracking**: Portfolio tracker for verification

### Automation Potential
```python
# Pseudo-code for automation
def calculate_allocation(mom_6m, val_6m, mom_3m, val_3m):
    signal = 0.7 * (mom_6m - val_6m) + 0.3 * (mom_3m - val_3m)
    percentile = get_percentile(signal, lookback=36)
    raw_weight = 0.55 + 0.30 * percentile
    rounded_weight = round(raw_weight / 0.025) * 0.025
    return rounded_weight, 1 - rounded_weight
```

## Transaction Cost Analysis

### Typical Rebalancing
- **Average Change**: 5-7.5% per rebalance
- **Frequency**: ~12 times per year
- **Cost per Trade**: 0.1-0.2% (brokerage + impact)
- **Annual Cost**: ~0.15-0.25% of portfolio

### Cost Mitigation
1. **Use Index Funds**: Lower impact cost
2. **Limit Orders**: Reduce slippage
3. **Batch Trades**: Combine with SIP
4. **Tax Efficiency**: Long-term holdings where possible

## Tax Considerations

### India Tax Treatment
- **Equity Funds**: LTCG 12.5% (>1 year), STCG 20%
- **Rebalancing**: Triggers capital gains
- **Strategy**: Hold positions >1 year when possible

### Tax-Efficient Approach
1. **SIP Continues**: New money always invested
2. **Rebalance Minimally**: Only when crossing thresholds
3. **Harvest Losses**: Offset gains when available
4. **Long-Term Focus**: Minimize short-term trades

## Comparison: Continuous vs. Rounded

### Continuous Allocation (Impractical)
```
Month 1: 62.35916469% / 37.64083531%
Month 2: 60.80090977% / 39.19909023%
Month 3: 66.85304373% / 33.14695627%
```
❌ Impossible to execute precisely
❌ Excessive trading
❌ High transaction costs

### Rounded Allocation (Practical)
```
Month 1: 62.5% / 37.5%
Month 2: 60.0% / 40.0%
Month 3: 67.5% / 32.5%
```
✅ Easy to execute
✅ Reduced trading
✅ Lower costs

## Summary

The **2.5% rounding** provides:

1. ✅ **Practical Implementation**: Clean, simple allocations
2. ✅ **Minimal Performance Impact**: < 0.1% difference
3. ✅ **Lower Costs**: Fewer trades, less slippage
4. ✅ **Easier Tracking**: Simple position sizes
5. ✅ **Better Compliance**: Clear, auditable rules

**Recommendation**: Always use rounded allocations in live trading. The theoretical precision of continuous weights is meaningless when transaction costs and execution challenges are considered.

---

**Implementation Status**: ✅ Active
**Rounding Increment**: 2.5%
**Allocation Range**: 55-85% (13 levels)
**Performance Impact**: Negligible
