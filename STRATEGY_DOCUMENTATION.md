# Ratio Trend 75/25 Strategy - Final Configuration

## Overview
This project now implements a **single, optimized portfolio rotation strategy**: the **Ratio Trend 75/25**.

After testing multiple signal approaches and allocation schemes, this strategy emerged as the clear winner with the best risk-adjusted returns.

## Strategy Details

### Signal Calculation
The strategy uses a **trend-following approach on the Momentum/Value ratio**:

1. **Calculate Ratio** = Momentum Index / Value Index
2. **Calculate 6-Month Moving Average** of the ratio
3. **Generate Signal**:
   - If Ratio > MA → Allocate 75% Momentum, 25% Value
   - If Ratio < MA → Allocate 25% Momentum, 75% Value

### Key Characteristics
- **Rebalancing**: Monthly
- **Allocation**: Binary (75/25 or 25/75)
- **Trend Following**: Uses 6-month MA for natural whipsaw protection
- **Balance**: Spends ~52% time in Momentum, ~48% time in Value

## Performance Metrics

| Metric | Value |
|--------|-------|
| **SIP XIRR** | 26.30% |
| **Index CAGR** | 27.44% |
| **Total Return** | 2,486.46% |
| **Max Drawdown** | -48.17% |
| **Max Investor Drawdown** | -2.51% |
| **MAR Ratio** | 0.55 |
| **Annual Turnover** | ~3 rebalances/year |

### Investment Performance
- **Total Invested (20 years)**: ₹24,90,000
- **Final Value**: ₹6,44,02,942
- **Absolute Gain**: ₹6,19,12,942

## Files Structure

### Core Strategy Files
```
analysis/
├── portfoliostrategy.py          # Main strategy implementation
├── portfolio_analytics.py         # Dashboard data generation
└── nifty200betareturns.py        # Base SIP analysis

output/
└── monthly/
    └── portfolio_ratio_trend_75_25.csv  # Strategy output

output/
└── portfolio_dashboard.json      # Dashboard data
```

### Dashboard Files
```
dashboard/
├── dashboard.html                # Main HTML
├── dashboard.js                  # JavaScript logic
├── dashboard.css                 # Styling
└── serve_dashboard.py            # Local server
```

## How to Use

### 1. Generate Strategy Data
```bash
python3 analysis/portfoliostrategy.py
```

This will:
- Load monthly index data
- Calculate the ratio trend signal  
- Apply 75/25 allocations
- Run SIP analysis
- Save results to `output/monthly/portfolio_ratio_trend_75_25.csv`

### 2. Generate Dashboard Data
```bash
python3 analysis/portfolio_analytics.py
```

This will:
- Load the portfolio strategy CSV
- Calculate comprehensive analytics
- Generate charts data
- Export to `output/portfolio_dashboard.json`

### 3. View Dashboard
```bash
python3 dashboard/serve_dashboard.py
```

Then open: http://localhost:8000/dashboard/dashboard.html

## Dashboard Features

### Individual Indices Tab
- Performance comparison of Momentum 30 vs Value 30
- SIP investment analysis
- NAV charts

### Portfolio Strategy Tab
Shows the **Ratio Trend 75/25** strategy with:

#### Performance Cards
- SIP XIRR, Strategy CAGR, MAR Ratio
- Total returns, investment  amounts
- Max drawdowns (NAV and investor)

#### Charts
1. **Portfolio NAV** (log scale)
2. **SIP Portfolio Value** vs Invested Amount
3. **Drawdown Analysis** (NAV & Investor)
4. **Dynamic Allocation Table** (Year x Month)
   - Shows 75/25 or 25/75 allocations
   - Yellow highlighting for allocation changes
   - Two-line format: mom-XX / val-XX
5. **Rolling Returns** (3Y & 5Y CAGR)
6. **Factor Attribution** (Cumulative contributions)
7. **Alpha vs Static 50/50**

## Why This Strategy Wins

### 1. Natural Whipsaw Protection
- The 6-month MA filters out monthly noise
- Only switches when sustained trend change occurs
- Avoids costly whipsaws from false signals

### 2. Optimal Transaction Frequency
- ~3 rebalances per year is:
  - Low enough to minimize costs
  - High enough to capture regime changes

### 3. Best Risk-Adjusted Returns  
- Highest MAR ratio (0.55) among all tested strategies
- Lowest investor drawdown (-2.51%)
- Strong absolute returns (26.30% XIRR)

### 4. Balanced Factor Exposure
- Nearly equal time in both factors
- Preserves diversification benefits
- Captures both factor premiums

### 5. Simplicity
- Single, clear signal (ratio vs MA)
- Binary allocation (no complex calculations)
- Easy to understand and implement

## Code Simplifications Done

### Removed Strategies
- ❌ Pure Momentum/Value (100/0)
- ❌ Relative Momentum Signal
- ❌ Ensemble Signal (RelMom + Ratio AND logic)
- ❌ Z-score Mean Reversion
- ❌ 3-State Anti-Whipsaw variants
- ❌ 70/30 and 60/40 allocation schemes
- ❌ Static 50/50

### Kept Clean
- ✅ Single Ratio Trend signal
- ✅ Single 75/25 allocation scheme
- ✅ Simplified code with clear purpose
- ✅ Comprehensive analytics and dashboard

## Next Steps

To implement this strategy in production:

1. **Paper Trade**: Monitor signals for 3-6 months
2. **Automate**: Set up monthly rebalancing alerts
3. **Execute**: Follow signals with actual investments
4. **Monitor**: Use dashboard to track performance
5. **Review**: Quarterly check on allocation efficiency

## Maintenance

The strategy requires:
- **Monthly**: Check signal and rebalance if needed (~3 times/year)
- **Quarterly**: Review dashboard performance
- **Annually**: Verify index constituents haven't changed

## Contact & Support

For questions or issues:
- Review code in `analysis/portfoliostrategy.py`
- Check dashboard data in `output/portfolio_dashboard.json`
- Verify allocation table in dashboard

---

**Last Updated**: February 16, 2026
**Strategy Version**: 1.0 (Final - Ratio Trend Only)
**Performance Period**: April 2005 - December 2025
