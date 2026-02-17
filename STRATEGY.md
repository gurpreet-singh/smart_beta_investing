# Smart Beta Investment Strategy - Complete Documentation

## 📋 Table of Contents
1. [Strategy Overview](#strategy-overview)
2. [Current Implementation](#current-implementation)
3. [Performance Metrics](#performance-metrics)
4. [Technical Details](#technical-details)
5. [Practical Implementation](#practical-implementation)
6. [Risk Considerations](#risk-considerations)
7. [Project Structure](#project-structure)
8. [Usage Instructions](#usage-instructions)

---

## Strategy Overview

### What is This Strategy?

This is a **Quarterly Alpha Rotation Strategy** that dynamically allocates between two NSE Smart Beta indices:
- **Nifty 200 Momentum 30** (momentum factor)
- **Nifty 200 Value 30** (value factor)

The strategy uses a **dynamic factor tilt** approach with a momentum-biased base allocation that adjusts based on relative factor strength.

### Key Characteristics

- **Base Allocation**: 75% Momentum / 25% Value
- **Tilt Range**: 100/0 (full momentum) to 50/50 (balanced)
- **Rebalancing**: Monthly
- **Signal**: Composite momentum (70% 6M + 30% 3M relative momentum)
- **Execution**: 1-month delay to avoid lookahead bias
- **Allocation Steps**: 5% increments (11 levels)

---

## Current Implementation

### Strategy Logic

#### 1. Signal Calculation
```
RelMom_6M = Mom_Index.pct_change(6) - Val_Index.pct_change(6)
RelMom_3M = Mom_Index.pct_change(3) - Val_Index.pct_change(3)
Composite_Signal = 0.7 × RelMom_6M + 0.3 × RelMom_3M
```

#### 2. Signal Normalization
- Calculate rolling 36-month percentile of signal strength
- Use percentile to determine allocation tilt
- Round to nearest 5% for practical implementation

#### 3. Allocation Mapping

| Signal Percentile | Momentum | Value | Description |
|-------------------|----------|-------|-------------|
| 0th (weakest) | 50% | 50% | Balanced |
| 25th | 62.5% | 37.5% | Below base |
| 50th (neutral) | 75% | 25% | **Base allocation** |
| 75th | 87.5% | 12.5% | Above base |
| 100th (strongest) | 100% | 0% | Full momentum |

**Practical Levels (5% steps):**
- 50/50, 55/45, 60/40, 65/35, 70/30
- **75/25** (base)
- 80/20, 85/15, 90/10, 95/5, 100/0

#### 4. Execution Timing
- Signal calculated at end of month `t`
- Allocation applied to month `t+1` returns
- **No lookahead bias** - prevents performance overstatement

---

## Performance Metrics

### Nifty 200 Universe (2005-2025)

```
📊 PERFORMANCE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SIP XIRR:                    20.94%
Index CAGR:                  22.29%
Total Invested:              ₹24,90,000
Final Value:                 ₹3,18,00,000
Absolute Gain:               ₹2,93,10,000
Total Return:                1,177.18%
Max Drawdown (NAV):          -50.89%
Max Investor Drawdown:       -10.72%
MAR Ratio (XIRR/MaxDD):      0.41

Period:                      April 2005 - December 2025 (249 months)
Monthly SIP:                 ₹10,000
Average Allocation:          76.3% Momentum / 23.7% Value
```

### Nifty 500 Universe (2005-2025)

```
📊 PERFORMANCE SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

SIP XIRR:                    22.71%
Index CAGR:                  24.81%
Total Invested:              ₹24,70,000
Final Value:                 ₹3,95,00,000
Absolute Gain:               ₹3,70,30,000
Total Return:                1,498.22%
Max Drawdown (NAV):          -57.06%
Max Investor Drawdown:       -9.77%
MAR Ratio (XIRR/MaxDD):      0.40

Period:                      April 2005 - December 2025 (247 months)
Monthly SIP:                 ₹10,000
Average Allocation:          76.7% Momentum / 23.3% Value
```

### Lumpsum Growth (₹10,000 invested in April 2005)

- **Nifty 200**: ₹10,000 → ₹6,50,956 (6,410% return, 22.29% CAGR)
- **Nifty 500**: ₹10,000 → ₹9,58,263 (9,483% return, 24.81% CAGR)

---

## Technical Details

### Why This Configuration Works

#### 1. Stronger Momentum Bias (75/25 Base)
- **Momentum premium**: Historically outperforms value in Indian markets
- **Structural tilt**: Captures long-term momentum factor
- **Still diversified**: 25% value provides balance and downside protection

#### 2. Wider Tilt Range (100/0 to 50/50)
- **Full conviction**: Can go 100% momentum when signal is strongest
- **Balanced fallback**: 50/50 when momentum is weakest
- **More responsive**: Larger tilts capture stronger signals

#### 3. 5% Increments (11 Levels)
- **Simpler execution**: Only 11 levels vs. 13 with 2.5% steps
- **Easier calculations**: Multiples of 5%
- **Reduced trading**: Larger buffer before rebalancing
- **Practical**: Easy to implement in real portfolios

#### 4. Composite Signal (70% 6M + 30% 3M)
- **Primary trend**: 6-month captures medium-term momentum
- **Confirmation**: 3-month adds recent strength
- **Balanced**: Not too slow, not too reactive

#### 5. No Lookahead Bias
- **Critical fix**: Signals from month `t` applied to month `t+1`
- **Realistic**: Mimics actual implementation constraints
- **Conservative**: Prevents performance overstatement

### Allocation Distribution (Nifty 200, 249 months)

```
Allocation Level    Months    Percentage
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
100/0 (Full Mom)      13        5.2%
95/5                  22        8.8%
90/10                 20        8.0%
85/15                 29       11.6%
80/20                 32       12.9%
75/25 (BASE)          48       19.3%  ⭐
70/30                 23        9.2%
65/35                 15        6.0%
60/40                 16        6.4%
55/45                 17        6.8%
50/50 (Balanced)      14        5.6%

Summary:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Extreme Momentum (90-100%):    55 months (22%)
Strong Momentum (80-85%):      61 months (24%)
Base/Near Base (70-75%):       71 months (29%)
Weak Momentum (55-65%):        48 months (19%)
Balanced (50/50):              14 months (6%)
```

### Evolution of Strategy

#### Version 1: Binary Rotation + Cash Overlay ❌
- 75/25 ↔ 25/75 rotation
- 10M/6M MA cash filter
- 28% time in cash
- 16-20% CAGR
- **Problem**: Cash drag reduced returns

#### Version 2: Dynamic Tilt (70/30 Base, 2.5% Steps) ✅
- 70/30 base, 85/15 to 55/45 range
- 2.5% increments (13 levels)
- 0% cash
- 20-23% CAGR
- **Problem**: Too many levels, less momentum bias

#### Version 3: Dynamic Tilt (75/25 Base, 5% Steps) ⭐ **CURRENT**
- **75/25 base**, **100/0 to 50/50 range**
- **5% increments (11 levels)**
- **0% cash**
- **22-25% CAGR**
- **Status**: ✅ Production Ready

---

## Practical Implementation

### For ₹10,00,000 Portfolio

| Allocation | Momentum | Value | Change from Base (75/25) |
|------------|----------|-------|--------------------------|
| 50/50 | ₹5,00,000 | ₹5,00,000 | Sell ₹2.5L mom, Buy ₹2.5L val |
| 55/45 | ₹5,50,000 | ₹4,50,000 | Sell ₹2.0L mom, Buy ₹2.0L val |
| 60/40 | ₹6,00,000 | ₹4,00,000 | Sell ₹1.5L mom, Buy ₹1.5L val |
| 65/35 | ₹6,50,000 | ₹3,50,000 | Sell ₹1.0L mom, Buy ₹1.0L val |
| 70/30 | ₹7,00,000 | ₹3,00,000 | Sell ₹0.5L mom, Buy ₹0.5L val |
| **75/25** | **₹7,50,000** | **₹2,50,000** | **BASE - No change** |
| 80/20 | ₹8,00,000 | ₹2,00,000 | Buy ₹0.5L mom, Sell ₹0.5L val |
| 85/15 | ₹8,50,000 | ₹1,50,000 | Buy ₹1.0L mom, Sell ₹1.0L val |
| 90/10 | ₹9,00,000 | ₹1,00,000 | Buy ₹1.5L mom, Sell ₹1.5L val |
| 95/5 | ₹9,50,000 | ₹50,000 | Buy ₹2.0L mom, Sell ₹2.0L val |
| 100/0 | ₹10,00,000 | ₹0 | Buy ₹2.5L mom, Sell ₹2.5L val |

### Monthly Rebalancing Process

1. **Last day of month**: Calculate composite signal
2. **Determine allocation**: Map signal percentile to allocation (round to 5%)
3. **Compare with current**: Check if allocation changed
4. **Execute if changed**: Rebalance to new allocation
5. **Record**: Log allocation for tracking

### Trading Frequency & Costs

- **Average changes**: ~12 per year (once per month on average)
- **Typical change**: 5-10% shift
- **Transaction cost**: ~0.15-0.25% annually (assuming 0.02% per trade)
- **Tax impact**: LTCG on equity (>1 year holding)

### Example Recent Allocations (2024-2025)

```
Month           Allocation    Signal Strength    Action
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Dec 2024        95/5         Very Strong        Buy momentum
Jan 2025        80/20        Strong             Sell some momentum
Feb 2025        75/25        Neutral            Return to base
Mar 2025        55/45        Weak               Shift to value
Apr 2025        65/35        Below Neutral      Partial recovery
May 2025        70/30        Slightly Weak      Near base
Jun 2025        75/25        Neutral            At base
Jul 2025        85/15        Strong             Buy momentum
Aug 2025        90/10        Very Strong        More momentum
Sep 2025        85/15        Strong             Slight reduction
Oct 2025        75/25        Neutral            Return to base
Nov 2025        75/25        Neutral            Hold base
Dec 2025        60/40        Weak               Shift to value
```

---

## Risk Considerations

### Strengths ✅

1. **High Returns**: 21-25% CAGR across both universes
2. **Simple Execution**: Only 11 levels, 5% steps
3. **Always Invested**: No cash drag (0% cash allocation)
4. **Momentum Bias**: Captures factor premium
5. **Adaptive**: Tilts based on signal strength
6. **Diversified**: Always holds both factors
7. **Systematic**: Rules-based, no discretion

### Risks & Considerations ⚠️

1. **Higher Volatility**: -51% to -57% max drawdown
2. **Momentum Risk**: Can go 100% momentum in extreme conditions
3. **Rebalancing Costs**: ~12 trades per year
4. **Tax Impact**: Triggers capital gains on rebalancing
5. **Factor Risk**: Both factors can underperform simultaneously
6. **Tracking Error**: May diverge from benchmark indices

### Ideal For ✅

- Long-term investors (10+ years horizon)
- SIP discipline (monthly investments)
- Volatility tolerance (can handle -50% drawdowns)
- Active management (monthly rebalancing)
- Tax-efficient accounts (or long-term holdings)

### Not Ideal For ❌

- Short-term traders (<5 years)
- Low volatility preference
- Passive investors (set-and-forget)
- Tax-sensitive accounts (frequent trading)
- Risk-averse investors

---

## Project Structure

```
smart_beta_investing/
├── STRATEGY.md                        # This file - Complete strategy documentation
├── README.md                          # Project overview (to be kept)
│
├── data/                              # Raw index data
│   ├── nifty200mom30/                # Nifty 200 Momentum 30 historical CSVs
│   ├── nifty200val30/                # Nifty 200 Value 30 historical CSVs
│   ├── nifty500mom50/                # Nifty 500 Momentum 50 historical CSVs
│   └── nifty500val50/                # Nifty 500 Value 50 historical CSVs
│
├── nifty200/                          # Nifty 200 Analysis
│   ├── analysis/
│   │   ├── nifty200_portfolio_strategy.py          # Main strategy implementation
│   │   ├── nifty200_portfolio_analytics.py         # Dashboard data generation
│   │   └── nifty200_generate_dashboard_data.py     # Monthly data consolidation
│   ├── output/
│   │   └── monthly/
│   │       ├── nifty200_momentum_30_monthly.csv
│   │       ├── nifty200_value_30_monthly.csv
│   │       └── portfolio_ratio_trend_75_25.csv
│   ├── dashboard/
│   │   ├── nifty200_dashboard.html
│   │   ├── nifty200_dashboard.js
│   │   └── nifty200_dashboard.css
│   └── README.md                      # Nifty 200 specific docs
│
├── nifty500/                          # Nifty 500 Analysis
│   ├── analysis/
│   │   ├── nifty500_portfolio_strategy.py
│   │   ├── nifty500_portfolio_analytics.py
│   │   └── nifty500_generate_dashboard_data.py
│   ├── output/
│   │   └── monthly/
│   ├── dashboard/
│   └── README.md
│
└── dashboard/                         # Combined dashboard server
    └── serve_dashboard.py             # Local HTTP server
```

---

## Usage Instructions

### 1. Generate Monthly Data

**For Nifty 200:**
```bash
cd /Users/personatech/smart_beta_investing
python3 nifty200/analysis/nifty200_generate_dashboard_data.py
```

This consolidates daily/weekly data into monthly close prices.

### 2. Run Strategy Backtest

**For Nifty 200:**
```bash
python3 nifty200/analysis/nifty200_portfolio_strategy.py
```

**For Nifty 500:**
```bash
python3 nifty500/analysis/nifty500_portfolio_strategy.py
```

This will:
- Load monthly index data
- Calculate composite momentum signal
- Apply dynamic tilt allocations
- Run SIP analysis
- Save results to `output/monthly/portfolio_ratio_trend_75_25.csv`

### 3. Generate Dashboard Data

**For Nifty 200:**
```bash
python3 nifty200/analysis/nifty200_portfolio_analytics.py
```

**For Nifty 500:**
```bash
python3 nifty500/analysis/nifty500_portfolio_analytics.py
```

This generates comprehensive analytics and chart data.

### 4. View Dashboard

```bash
python3 dashboard/serve_dashboard.py
```

Then open in browser:
- **Nifty 200**: http://localhost:8000/nifty200/dashboard/nifty200_dashboard.html
- **Nifty 500**: http://localhost:8000/nifty500/dashboard/nifty500_dashboard.html

### Dashboard Features

#### Individual Indices Tab
- Performance comparison (Momentum vs Value)
- SIP investment analysis
- NAV charts (log scale)
- Drawdown analysis

#### Portfolio Strategy Tab
- Performance cards (XIRR, CAGR, MAR Ratio)
- Portfolio NAV chart (log scale)
- SIP portfolio value vs invested amount
- Drawdown analysis (NAV & investor)
- Dynamic allocation heatmap (year × month)
- Rolling returns (3Y & 5Y CAGR)
- Factor attribution (cumulative contributions)
- Alpha vs static 50/50 benchmark

---

## Maintenance & Monitoring

### Monthly Tasks
1. Download latest index data from NSE
2. Run data generation script
3. Run strategy backtest
4. Check allocation signal
5. Rebalance if allocation changed
6. Log trades and allocations

### Quarterly Tasks
1. Review dashboard performance
2. Verify allocation distribution
3. Check drawdown levels
4. Compare with benchmarks
5. Review transaction costs

### Annual Tasks
1. Verify index constituents haven't changed
2. Review overall strategy performance
3. Tax planning for capital gains
4. Rebalance to target allocation if drifted

---

## Data Sources

- **Nifty 200 Momentum 30**: NSE historical data (April 2005 - Present)
- **Nifty 200 Value 30**: NSE historical data (April 2005 - Present)
- **Nifty 500 Momentum 50**: NSE historical data (April 2005 - Present)
- **Nifty 500 Value 50**: NSE historical data (April 2005 - Present)

All data downloaded from NSE India official website.

---

## Final Verdict

This is a **production-ready, institutional-grade factor tilt strategy** that:

1. ✅ **Delivers**: 21-25% CAGR (vs 16-20% with cash overlay)
2. ✅ **Simplifies**: 11 levels in 5% steps (vs 13 levels in 2.5% steps)
3. ✅ **Adapts**: Tilts based on signal strength (vs binary rotation)
4. ✅ **Compounds**: Always 100% invested (vs 28% cash drag)
5. ✅ **Executes**: Practical allocations (vs impossible decimals)

**Perfect for**: Long-term SIP investors who can tolerate volatility and want to capture the momentum premium with systematic rebalancing.

---

**Strategy Name**: Quarterly Alpha Rotation (Dynamic Factor Tilt)  
**Version**: 3.0 (Final)  
**Base Allocation**: 75% Momentum / 25% Value  
**Tilt Range**: 100/0 to 50/50  
**Increment**: 5% steps (11 levels)  
**Rebalancing**: Monthly  
**Expected CAGR**: 22-25%  
**Max Drawdown**: -51% to -57%  
**Status**: ✅ Production Ready  
**Last Updated**: February 17, 2026
