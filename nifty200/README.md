# Nifty 200 Smart Beta Analysis

This folder contains all analysis, data, and dashboard files specifically for **Nifty 200** based Smart Beta indices (Momentum 30 and Value 30).

## 📁 Folder Structure

```
nifty200/
├── analysis/                           # Analysis scripts
│   ├── nifty200_sip_returns.py        # SIP returns calculation for individual indices
│   ├── nifty200_calculate_ratio.py    # Momentum/Value ratio analysis (weekly)
│   ├── nifty200_portfolio_strategy.py # Portfolio strategy (Ratio Trend 75/25)
│   ├── nifty200_portfolio_analytics.py # Portfolio analytics & dashboard data export
│   └── nifty200_generate_dashboard_data.py # Individual indices dashboard data
│
├── output/                             # Generated output files
│   ├── monthly/                        # Monthly aggregated data
│   │   ├── nifty200_momentum_30_monthly.csv
│   │   ├── nifty200_value_30_monthly.csv
│   │   ├── nifty200_portfolio_ratio_trend_75_25.csv
│   │   └── nifty200_dashboard_data.json
│   ├── weekly/                         # Weekly analysis data
│   │   ├── nifty200_momentum_value_ratio_weekly.csv
│   │   ├── nifty200_ratio_chart.json
│   │   └── nifty200_ratio_chart.html
│   ├── nifty200_dashboard_data.json   # Individual indices dashboard data
│   └── nifty200_portfolio_dashboard.json # Portfolio strategy dashboard data
│
├── dashboard/                          # Dashboard files
│   ├── nifty200_dashboard.html        # Main dashboard HTML
│   ├── nifty200_dashboard.js          # Dashboard JavaScript
│   └── nifty200_dashboard.css         # Dashboard styles
│
└── NIFTY200_STRATEGY_DOCUMENTATION.md # Strategy documentation

```

## 🎯 Strategy

**Ratio Trend 75/25**
- Compares Momentum/Value ratio to its 6-month moving average
- Binary allocation: 75/25 or 25/75
- Monthly rebalancing
- ~3 trades/year

## 📊 Performance Metrics (April 2005 - December 2025)

- **SIP XIRR**: 26.30%
- **Strategy CAGR**: 27.44%
- **Total Return**: 2,486.46%
- **Max Drawdown**: -56.52%
- **MAR Ratio**: 0.47
- **Volatility**: 24.1%

## 🚀 How to Run

### 1. Generate Individual Indices Data
```bash
cd /Users/personatech/smart_beta_investing
python3 nifty200/analysis/nifty200_sip_returns.py
python3 nifty200/analysis/nifty200_calculate_ratio.py
python3 nifty200/analysis/nifty200_generate_dashboard_data.py
```

### 2. Generate Portfolio Strategy Data
```bash
python3 nifty200/analysis/nifty200_portfolio_strategy.py
python3 nifty200/analysis/nifty200_portfolio_analytics.py
```

### 3. View Dashboard
Open `nifty200/dashboard/nifty200_dashboard.html` in a browser
Or serve via HTTP server from project root

## 📝 Notes

- All analysis uses data from `../data/nifty200mom30` and `../data/nifty200val30`
- Output files are self-contained within this folder
- Dashboard references files relative to this folder structure

## 🔄 Next Steps for Nifty 500

The parent folder structure is ready for Nifty 500 analysis:
- Create similar `nifty500/` folder
- Adapt analysis scripts for Nifty 500 data sources
- Keep analyses completely separate
