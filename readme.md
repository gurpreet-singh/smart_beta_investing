# Smart Beta Investment Strategy

A systematic investment strategy that dynamically allocates between Momentum and Value factors from NSE Smart Beta indices.

## 🎯 Overview

This project implements a **Quarterly Alpha Rotation Strategy** with dynamic factor tilting:

- **Base Allocation**: 75% Momentum / 25% Value
- **Tilt Range**: 100/0 (full momentum) to 50/50 (balanced)
- **Rebalancing**: Monthly
- **Performance**: 21-25% CAGR across Nifty 200 and Nifty 500 universes

## 📊 Quick Stats

| Universe | SIP XIRR | Index CAGR | Max Drawdown | Status |
|----------|----------|------------|--------------|--------|
| **Nifty 200** | 20.94% | 22.29% | -50.89% | ✅ Live |
| **Nifty 500** | 22.71% | 24.81% | -57.06% | ✅ Live |

## 📚 Documentation

**👉 [Read Complete Strategy Documentation](STRATEGY.md)** - Comprehensive guide covering:
- Strategy logic and implementation details
- Performance metrics and backtesting results
- Practical implementation guide
- Risk considerations
- Usage instructions

## 🚀 Quick Start

### Nifty 200
```bash
# Generate monthly data
python3 nifty200/analysis/nifty200_generate_dashboard_data.py

# Run strategy backtest
python3 nifty200/analysis/nifty200_portfolio_strategy.py

# Generate dashboard data
python3 nifty200/analysis/nifty200_portfolio_analytics.py

# View dashboard
python3 dashboard/serve_dashboard.py
# Open: http://localhost:8000/nifty200/dashboard/nifty200_dashboard.html
```

### Nifty 500
```bash
# Generate monthly data
python3 nifty500/analysis/nifty500_generate_dashboard_data.py

# Run strategy backtest
python3 nifty500/analysis/nifty500_portfolio_strategy.py

# Generate dashboard data
python3 nifty500/analysis/nifty500_portfolio_analytics.py

# View dashboard
python3 dashboard/serve_dashboard.py
# Open: http://localhost:8000/nifty500/dashboard/nifty500_dashboard.html
```

## 📁 Project Structure

```
smart_beta_investing/
├── STRATEGY.md                    # 📖 Complete strategy documentation
├── README.md                      # This file
│
├── data/                          # Raw index data
│   ├── nifty200mom30/            # Nifty 200 Momentum 30
│   ├── nifty200val30/            # Nifty 200 Value 30
│   ├── nifty500mom50/            # Nifty 500 Momentum 50
│   └── nifty500val50/            # Nifty 500 Value 50
│
├── nifty200/                      # Nifty 200 implementation
│   ├── analysis/                  # Strategy scripts
│   ├── output/monthly/           # Generated data
│   └── dashboard/                # Interactive dashboard
│
├── nifty500/                      # Nifty 500 implementation
│   ├── analysis/                  # Strategy scripts
│   ├── output/monthly/           # Generated data
│   └── dashboard/                # Interactive dashboard
│
└── dashboard/                     # Dashboard server
    └── serve_dashboard.py
```

## 🎯 Strategy Highlights

### Dynamic Factor Tilt
- **Adaptive allocation** based on composite momentum signal (70% 6M + 30% 3M)
- **11 allocation levels** in 5% increments (50/50 to 100/0)
- **No lookahead bias** - signals from month t applied to month t+1
- **Always invested** - 0% cash allocation

### Performance
- **21-25% CAGR** across both universes
- **₹10K → ₹6.5L-₹9.6L** over 20 years (lumpsum)
- **₹10K/month SIP → ₹3.2Cr-₹4Cr** over 20 years
- **MAR Ratio**: 0.40-0.41

## 🗂️ Data Sources

All data from **NSE India** (April 2005 - Present):
- Nifty 200 Momentum 30
- Nifty 200 Value 30
- Nifty 500 Momentum 50
- Nifty 500 Value 50

## 📝 License

Personal investment research project.

---

**Last Updated**: February 17, 2026  
**Version**: 3.0 (Production Ready)  
**Status**: ✅ Both Nifty 200 and Nifty 500 strategies live
