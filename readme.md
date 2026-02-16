# Nifty 200 Smart Beta SIP Analysis

Complete SIP (Systematic Investment Plan) analysis for Nifty 200 Smart Beta indices.

## 📁 Project Structure

```
smart_beta_investing/
├── analysis/                      # Analysis scripts
│   ├── nifty200betareturns.py    # Main SIP analysis engine
│   └── generate_dashboard_data.py # Dashboard data generator
├── dashboard/                     # Web dashboard files
│   ├── dashboard.html            # Dashboard UI
│   ├── dashboard.css             # Styles
│   ├── dashboard.js              # Dashboard logic
│   └── serve_dashboard.py        # Local web server
├── data/                          # Source data (CSV files)
│   ├── nifty200mom30/           # Momentum 30 index data
│   └── nifty200val30/           # Value 30 index data
└── output/                        # Generated outputs
    ├── monthly/                  # Monthly consolidated CSVs
    │   ├── nifty200_momentum_30_monthly.csv
    │   └── nifty200_value_30_monthly.csv
    └── dashboard_data.json       # Dashboard data
```

## 🚀 Quick Start

### 1. Run SIP Analysis

```bash
python3 analysis/nifty200betareturns.py
```

This will:
- Analyze all indices
- Calculate SIP XIRR, Index CAGR, returns, and drawdowns
- Generate monthly CSV files in `output/monthly/`
- Display detailed results in console

### 2. Generate Dashboard Data

```bash
python3 analysis/generate_dashboard_data.py
```

This will:
- Run the analysis
- Export results to `output/dashboard_data.json`

### 3. View Dashboard

```bash
python3 dashboard/serve_dashboard.py
```

Then open: **http://localhost:8000/dashboard/dashboard.html**

## 📊 Features

### Indices Analyzed
- **NIFTY200 MOMENTUM 30**: High momentum stocks
- **NIFTY200 VALUE 30**: Value-focused stocks

### Metrics Calculated
- **SIP XIRR**: Annualized return accounting for phased investments
- **Index CAGR**: Compound Annual Growth Rate (2005-2025)
- **Total Returns**: Overall percentage gains
- **Maximum Drawdown**: Peak-to-trough decline
- **Portfolio Value**: Current investment worth

### Analysis Period
- **Start**: April 2005
- **End**: December 2025
- **Duration**: ~20.7 years
- **Monthly SIP**: ₹10,000 per index

## 🎯 Key Findings

The analysis shows:
- **Momentum 30** delivers superior returns (CAGR: 18.55%) but with higher volatility
- **Value 30** offers more stable growth (CAGR: 14.41%) with lower drawdowns
- SIP XIRR is typically 1-2% lower than Index CAGR (due to phased investment)

## 📝 Notes

- All calculations use **end-of-month close prices** for realistic SIP simulation
- XIRR properly accounts for cashflow timing (correct for SIP analysis)
- Index CAGR assumes lump sum on Day 1 (for comparison only)
- Portfolio drawdown not shown (meaningless for SIP with regular inflows)

## 🛠️ Requirements

```bash
pip install pandas numpy pyxirr
```

## 📄 License

For educational and personal use.
