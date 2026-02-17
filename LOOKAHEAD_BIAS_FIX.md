# Lookahead Bias Fix - Impact Analysis

## The Problem

### What Was Wrong
The portfolio regime filter was making **same-bar decisions**, a classic lookahead bias:

```python
# WRONG - Same bar decision
for i in range(len(df)):
    nav = df['Portfolio_NAV_Raw'].iloc[i]  # Month t NAV
    ma_exit = df['Port_MA_Exit'].iloc[i]   # Month t MA
    
    if nav < ma_exit:
        current_state = False  # Affects month t allocation ❌

df['risk_on'] = risk_on
df['w_mom_final'] = df['w_mom'] * df['risk_on']  # Applied to month t
```

**Timeline of the bug:**
1. Month t closes → Portfolio_NAV_Raw[t] is calculated
2. Compare NAV[t] to MA[t] → Generate risk_on[t]
3. Apply risk_on[t] to month t's allocation → **IMPOSSIBLE IN LIVE TRADING**

You can't know month-end NAV before deciding whether you were invested that month!

### The Fix

```python
# CORRECT - Next-bar execution
df['risk_on'] = risk_on

# ⚠️ CRITICAL: Shift signal forward to prevent lookahead bias
# Signal at month t affects allocation at month t+1
df['risk_on'] = df['risk_on'].shift(1).fillna(True)

df['w_mom_final'] = df['w_mom'] * df['risk_on']  # Now affects month t+1 ✅
```

**Corrected timeline:**
1. Month t closes → Portfolio_NAV_Raw[t] is calculated
2. Compare NAV[t] to MA[t] → Generate risk_on[t]
3. Apply risk_on[t] to **month t+1's** allocation → **REALISTIC**

## Performance Impact

### Before Fix (With Lookahead Bias)

| Metric | Nifty 200 | Nifty 500 |
|--------|-----------|-----------|
| **CAGR** | **31.39%** | **34.23%** |
| **SIP XIRR** | **30.04%** | **32.11%** |
| **Max DD** | **-19.29%** | **-21.91%** |
| **MAR Ratio** | **1.56** | **1.47** |
| Final Value (₹10K) | ₹2,886,696 | ₹4,284,262 |

### After Fix (Lookahead-Free)

| Metric | Nifty 200 | Nifty 500 |
|--------|-----------|-----------|
| **CAGR** | **16.64%** | **20.03%** |
| **SIP XIRR** | **16.24%** | **16.96%** |
| **Max DD** | **-29.95%** | **-35.50%** |
| **MAR Ratio** | **0.54** | **0.48** |
| Final Value (₹10K) | ₹243,693 | ₹428,232 |

### Impact Summary

| Metric | Nifty 200 Impact | Nifty 500 Impact |
|--------|------------------|------------------|
| **CAGR** | **-14.75%** | **-14.20%** |
| **SIP XIRR** | **-13.80%** | **-15.15%** |
| **Max DD** | **-10.66%** worse | **-13.59%** worse |
| **MAR Ratio** | **-1.02** | **-0.99** |
| **Final Value** | **-91.6%** | **-90.0%** |

## Key Insights

### 1. Massive Overstatement
The lookahead bias inflated returns by **~14-15% CAGR** - nearly doubling the strategy's performance!

### 2. Drawdown Understatement
Max drawdown was understated by **~11-14%**, making the strategy appear much safer than it actually is.

### 3. MAR Ratio Collapse
The risk-adjusted return (MAR ratio) collapsed from **1.5** to **0.5** - a **67% reduction**.

### 4. Realistic Performance
After the fix, the strategy shows:
- **Nifty 200**: 16.24% XIRR with -29.95% max DD
- **Nifty 500**: 16.96% XIRR with -35.50% max DD

These are still respectable returns, but far more realistic and achievable in live trading.

## Why This Matters

### In Backtesting
- **Inflated confidence**: You think you have a 30% CAGR strategy
- **Underestimated risk**: You think max DD is only -20%
- **False sense of security**: MAR ratio of 1.5 looks excellent

### In Live Trading
- **Reality check**: Actual returns are ~16-17% CAGR
- **Higher drawdowns**: Expect -30% to -35% drawdowns
- **Lower risk-adjusted returns**: MAR ratio ~0.5

### The Danger
If you sized positions based on the inflated backtest:
- You'd be taking **2-3x more risk** than you thought
- Drawdowns would be **50% larger** than expected
- You might abandon the strategy during normal drawdowns

## Technical Details

### What Changed
**File**: `nifty200/analysis/nifty200_portfolio_strategy.py` (line 277-280)
**File**: `nifty500/analysis/nifty500_portfolio_strategy.py` (line 277-280)

```python
# Added after calculating risk_on signal
df['risk_on'] = df['risk_on'].shift(1).fillna(True)
```

### Why `.shift(1)`?
- Moves each value forward by 1 row
- Signal at index i now affects index i+1
- First month gets `fillna(True)` since there's no prior signal

### Why `.fillna(True)`?
- First month has no prior signal to shift from
- Default to risk-on for the first month
- Conservative assumption: start invested

## Verification

### Check the Fix
Look at any month's data in the portfolio CSV:

**Before fix:**
```
Date: 2008-10-31
NAV: 950 (below MA)
risk_on: False (same month) ❌
Return: 0% (cash applied immediately)
```

**After fix:**
```
Date: 2008-10-31
NAV: 950 (below MA)
risk_on: True (still using prior month's signal) ✅
Return: -15% (took the hit this month)

Date: 2008-11-30
risk_on: False (now using Oct's signal) ✅
Return: 0% (cash applied next month)
```

## Conclusion

This fix demonstrates why **rigorous lookahead bias checking** is critical:

1. ✅ **Always shift signals forward** when using end-of-period data
2. ✅ **Question suspiciously good results** - they often hide bugs
3. ✅ **Test signal timing** - ensure decisions use only past data
4. ✅ **Document assumptions** - make lookahead prevention explicit

The corrected strategy still provides:
- **Solid absolute returns** (16-20% CAGR)
- **Factor diversification** (momentum + value)
- **Drawdown protection** (cash overlay reduces worst losses)
- **Realistic expectations** for live trading

But now we know the **true performance** we can expect.

## Files Modified

1. `/Users/personatech/smart_beta_investing/nifty200/analysis/nifty200_portfolio_strategy.py`
2. `/Users/personatech/smart_beta_investing/nifty500/analysis/nifty500_portfolio_strategy.py`

Both files now include the critical `.shift(1)` fix with explanatory comments.
