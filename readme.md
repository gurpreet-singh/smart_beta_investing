# Smart Beta Portfolio Investment Strategy

A systematic investment strategy combining Momentum and Value factors from NSE Smart Beta indices with dynamic allocation based on factor ratio trends.

## 🎯 Project Overview

This project implements and analyzes smart beta investment strategies across different market universes:

- **Nifty 200 Universe**: Momentum 30 & Value 30 indices
- **Nifty 500 Universe**: Momentum 50 & Value 50 indices (upcoming)

## 📁 Project Structure

```
smart_beta_investing/
├── data/                          # Raw index data (daily/weekly)
│   ├── nifty200mom30/            # Nifty 200 Momentum 30 CSVs
│   ├── nifty200val30/            # Nifty 200 Value 30 CSVs
│   ├── nifty500mom50/            # Nifty 500 Momentum 50 CSVs (future)
│   └── nifty500val50/            # Nifty 500 Value 50 CSVs (future)
│
├── nifty200/                      # ✅ Nifty 200 Analysis (Complete)
│   ├── analysis/                  # Analysis scripts
│   ├── output/                    # Generated data & results
│   ├── dashboard/                 # Interactive dashboard
│   ├── README.md                  # Nifty 200 documentation
│   └── NIFTY200_STRATEGY_DOCUMENTATION.md
│
├── nifty500/                      # 🚧 Nifty 500 Analysis (Upcoming)
│   ├── analysis/                  # (To be created)
│   ├── output/                    # (To be created)
│   └── dashboard/                 # (To be created)
│
├── analysis/                      # Legacy analysis files (reference)
├── output/                        # Legacy output files (reference)
├── dashboard/                     # Legacy dashboard (reference)
└── README.md                      # This file
```

## 🚀 Quick Start

### Nifty 200 Analysis

See [`nifty200/README.md`](nifty200/README.md) for complete instructions.

**Quick run:**
```bash
# Generate data
python3 nifty200/analysis/nifty200_generate_dashboard_data.py
python3 nifty200/analysis/nifty200_portfolio_strategy.py
python3 nifty200/analysis/nifty200_portfolio_analytics.py

# View dashboard
open nifty200/dashboard/nifty200_dashboard.html
```

## 📊 Strategies Implemented

### Ratio Trend 75/25 (Nifty 200)
- **Signal**: Momentum/Value ratio vs 6-month MA
- **Allocation**: Binary 75/25 or 25/75
- **Rebalancing**: Monthly
- **Performance**: 26.30% SIP XIRR, 27.44% CAGR

## 📈 Performance Summary

| Metric | Nifty 200 | Nifty 500 |
|--------|-----------|-----------|
| SIP XIRR | 26.30% | Coming soon |
| Strategy CAGR | 27.44% | Coming soon |
| Max Drawdown | -56.52% | Coming soon |
| MAR Ratio | 0.47 | Coming soon |

## 🗂️ Data Sources

- **Nifty 200 Momentum 30**: NSE historical data (April 2005 - December 2025)
- **Nifty 200 Value 30**: NSE historical data (April 2005 - December 2025)
- **Nifty 500 Momentum 50**: (Upcoming)
- **Nifty 500 Value 50**: (Upcoming)

## 📚 Documentation

- [Nifty 200 Strategy Documentation](nifty200/NIFTY200_STRATEGY_DOCUMENTATION.md)
- [Nifty 200 README](nifty200/README.md)

## 🔄 Migration Notes

**Previous structure** (before Feb 2026):
- All analysis scripts were in root `analysis/` folder
- All outputs were in root `output/` folder
- Dashboard was in root `dashboard/` folder

**Current structure**:
- Each index universe (Nifty 200, Nifty 500) has its own folder
- All files are prefixed with the index name (e.g., `nifty200_*.py`)
- Completely separate analysis pipelines
- Legacy files remain in root folders for reference

## 🎯 Next Steps

1. ✅ Nifty 200 analysis complete
2. 🚧 Set up Nifty 500 analysis structure
3. 🚧 Implement Nifty 500 strategy variations
4. 🚧 Compare Nifty 200 vs Nifty 500 performance

## 📝 License

This is a personal investment research project.

---

**Last Updated**: February 2026  
**Status**: Nifty 200 analysis complete, Nifty 500 in progress
