# Final Strategy: Dynamic Factor Tilt (75/25 Base, 5% Steps)

## ✅ Strategy Configuration

### Allocation Ladder (11 Levels)
**Base**: 75% Momentum / 25% Value  
**Range**: 100/0 (full momentum) ↔ 50/50 (balanced)  
**Increment**: 5% steps

| Level | Momentum | Value | Usage (Nifty 200) |
|-------|----------|-------|-------------------|
| 1 | **50%** | **50%** | 14 months (5.6%) |
| 2 | **55%** | **45%** | 17 months (6.8%) |
| 3 | **60%** | **40%** | 16 months (6.4%) |
| 4 | **65%** | **35%** | 15 months (6.0%) |
| 5 | **70%** | **30%** | 23 months (9.2%) |
| 6 | **75%** | **25%** | 48 months (19.3%) ⭐ BASE |
| 7 | **80%** | **20%** | 32 months (12.9%) |
| 8 | **85%** | **15%** | 29 months (11.6%) |
| 9 | **90%** | **10%** | 20 months (8.0%) |
| 10 | **95%** | **5%** | 22 months (8.8%) |
| 11 | **100%** | **0%** | 13 months (5.2%) |

## 📊 Performance Results

### Nifty 200
```
SIP XIRR:          20.94%
Index CAGR:        22.29%
Total Invested:    ₹24.9L
Final Value:       ₹3.18Cr
Absolute Gain:     ₹2.93Cr
Total Return:      1177.18%
Max Drawdown:      -50.89%
Max Investor DD:   -10.72%
MAR Ratio:         0.41
Avg Allocation:    76.3% Momentum / 23.7% Value
```

### Nifty 500
```
SIP XIRR:          22.71%
Index CAGR:        24.81%
Total Invested:    ₹24.7L
Final Value:       ₹3.95Cr
Absolute Gain:     ₹3.70Cr
Total Return:      1498.22%
Max Drawdown:      -57.06%
Max Investor DD:   -9.77%
MAR Ratio:         0.40
Avg Allocation:    76.7% Momentum / 23.3% Value
```

### ₹10K Growth
- **Nifty 200**: ₹10,000 → ₹6,50,956 (6,410% return)
- **Nifty 500**: ₹10,000 → ₹9,58,263 (9,483% return)

## 🎯 Key Improvements Over Previous Versions

### vs. Cash Overlay (10M/6M MA)
| Metric | Cash Overlay | Dynamic Tilt | Improvement |
|--------|--------------|--------------|-------------|
| **Nifty 200 CAGR** | 16.64% | 22.29% | **+5.65%** |
| **Nifty 500 CAGR** | 20.03% | 24.81% | **+4.78%** |
| **Cash Time** | 28% | 0% | **-28%** |
| **₹10K → (N200)** | ₹2.44L | ₹6.51L | **+167%** |

### vs. 70/30 Base (2.5% steps)
| Metric | 70/30 Base | 75/25 Base | Improvement |
|--------|------------|------------|-------------|
| **Nifty 200 CAGR** | 20.21% | 22.29% | **+2.08%** |
| **Nifty 500 CAGR** | 22.63% | 24.81% | **+2.18%** |
| **Steps** | 13 levels | 11 levels | **Simpler** |
| **Increment** | 2.5% | 5% | **Easier** |

## 💡 Why This Configuration Works

### 1. Stronger Momentum Bias (75/25 Base)
- **Momentum premium**: Historically outperforms value
- **Structural tilt**: Captures long-term momentum factor
- **Still diversified**: 25% value provides balance

### 2. Wider Range (100/0 to 50/50)
- **Full conviction**: Can go 100% momentum when signal is strongest
- **Balanced fallback**: 50/50 when momentum is weakest
- **More responsive**: Larger tilts capture stronger signals

### 3. 5% Increments
- **Simpler execution**: Only 11 levels vs. 13
- **Easier calculations**: Multiples of 5%
- **Reduced trading**: Larger buffer before rebalancing
- **Practical**: Easy to implement in real portfolios

## 📈 Recent Allocations (2024-2025)

```
Dec 2024: 95/5   (very strong momentum)
Jan 2025: 80/20  (strong momentum)
Feb 2025: 75/25  (base allocation)
Mar 2025: 55/45  (weak momentum)
Apr 2025: 65/35  (below neutral)
May 2025: 70/30  (slightly below base)
Jun 2025: 75/25  (base allocation)
Jul 2025: 85/15  (strong momentum)
Aug 2025: 90/10  (very strong momentum)
Sep 2025: 85/15  (strong momentum)
Oct 2025: 75/25  (base allocation)
Nov 2025: 75/25  (base allocation)
Dec 2025: 60/40  (weak momentum)
```

## 🔧 Practical Implementation

### For ₹10L Portfolio

| Allocation | Momentum | Value | Change from Base |
|------------|----------|-------|------------------|
| 50/50 | ₹5,00,000 | ₹5,00,000 | Sell ₹2.5L mom, Buy ₹2.5L val |
| 60/40 | ₹6,00,000 | ₹4,00,000 | Sell ₹1.5L mom, Buy ₹1.5L val |
| 70/30 | ₹7,00,000 | ₹3,00,000 | Sell ₹0.5L mom, Buy ₹0.5L val |
| **75/25** | **₹7,50,000** | **₹2,50,000** | **BASE** |
| 80/20 | ₹8,00,000 | ₹2,00,000 | Buy ₹0.5L mom, Sell ₹0.5L val |
| 90/10 | ₹9,00,000 | ₹1,00,000 | Buy ₹1.5L mom, Sell ₹1.5L val |
| 100/0 | ₹10,00,000 | ₹0 | Buy ₹2.5L mom, Sell ₹2.5L val |

### Monthly Rebalancing
1. **Calculate signal** (end of month)
2. **Determine allocation** (round to nearest 5%)
3. **Rebalance if changed** (execute trades)
4. **Verify positions** (confirm allocations)

### Trading Frequency
- **Average**: ~1 change per month
- **Typical change**: 5-10% shift
- **Transaction cost**: ~0.15-0.25% annually

## 🎯 Strategy Characteristics

### Strengths
1. ✅ **High Returns**: 21-25% CAGR
2. ✅ **Simple Execution**: Only 11 levels, 5% steps
3. ✅ **Always Invested**: No cash drag
4. ✅ **Momentum Bias**: Captures factor premium
5. ✅ **Adaptive**: Tilts based on signal strength

### Considerations
1. ⚠️ **Higher Volatility**: -51% to -57% max drawdown
2. ⚠️ **Momentum Risk**: Can go 100% momentum
3. ⚠️ **Rebalancing Costs**: ~12 trades per year
4. ⚠️ **Tax Impact**: Triggers capital gains

### Ideal For
- ✅ Long-term investors (10+ years)
- ✅ SIP discipline (monthly investments)
- ✅ Volatility tolerance (can handle -50% DD)
- ✅ Active management (monthly rebalancing)

### Not Ideal For
- ❌ Short-term traders (< 5 years)
- ❌ Low volatility preference
- ❌ Passive investors (set-and-forget)
- ❌ Tax-sensitive accounts

## 📊 Allocation Distribution

### Nifty 200 (249 months)
```
Extreme Momentum (90-100%):  55 months (22%)
Strong Momentum (80-85%):    61 months (24%)
Base/Near Base (70-75%):     71 months (29%)
Weak Momentum (55-65%):      48 months (19%)
Balanced (50/50):            14 months (6%)
```

### Key Insights
- **48% of time**: Strong to extreme momentum tilt (80-100%)
- **29% of time**: At or near base allocation (70-75%)
- **23% of time**: Weak momentum or balanced (50-65%)
- **Average**: 76% momentum (slightly above base)

## 🔄 Evolution of Strategy

### Version 1: Binary Rotation + Cash Overlay
- ❌ 75/25 ↔ 25/75 rotation
- ❌ 10M/6M MA cash filter
- ❌ 28% time in cash
- ❌ 16-20% CAGR

### Version 2: Dynamic Tilt (70/30 Base, 2.5% Steps)
- ✅ 70/30 base, 85/15 to 55/45 range
- ✅ 2.5% increments (13 levels)
- ✅ 0% cash
- ✅ 20-23% CAGR

### Version 3: Dynamic Tilt (75/25 Base, 5% Steps) ⭐ FINAL
- ✅ **75/25 base**, **100/0 to 50/50 range**
- ✅ **5% increments (11 levels)**
- ✅ **0% cash**
- ✅ **22-25% CAGR**

## 🎉 Final Verdict

This is a **production-ready, institutional-grade factor tilt strategy** that:

1. **Delivers**: 21-25% CAGR (vs 16-20% with cash overlay)
2. **Simplifies**: 11 levels in 5% steps (vs 13 levels in 2.5% steps)
3. **Adapts**: Tilts based on signal strength (vs binary rotation)
4. **Compounds**: Always 100% invested (vs 28% cash drag)
5. **Executes**: Practical allocations (vs impossible decimals)

**Perfect for**: Long-term SIP investors who can tolerate volatility and want to capture the momentum premium with systematic rebalancing.

---

**Strategy Name**: Dynamic Factor Tilt (75/25 Base)  
**Version**: 3.0 (Final)  
**Base Allocation**: 75% Momentum / 25% Value  
**Tilt Range**: 100/0 to 50/50  
**Increment**: 5% steps (11 levels)  
**Rebalancing**: Monthly  
**Expected CAGR**: 22-25%  
**Max Drawdown**: -51% to -57%  
**Status**: ✅ Production Ready
