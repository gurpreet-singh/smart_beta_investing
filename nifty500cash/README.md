# MOMCASH v2 — Continuous Risk Score Architecture

## Core Concept

**This is NOT factor rotation. This is systematic risk modulation.**

The MOMCASH strategy manages a single exposure — Nifty 500 Momentum 50 — and uses cash as a systematic risk management tool. Instead of binary tier switching, cash builds GRADUALLY as risk signals accumulate:

1. **Build cash BEFORE crashes** — each signal independently adds cash
2. **Hold cash DURING crashes** — drawdown danger prevents premature redeployment
3. **Return to fully invested naturally** — persistence decay gradually restores full momentum

## Architecture

### Base Allocation
```
Momentum: 100%  (fully invested by default)
Cash:       0%  (no permanent cash drag)
```

### Continuous Risk Score (0–100)

Instead of discrete tiers with AND logic (too slow), each signal independently contributes points to a risk score. Cash allocation = `risk_score × 50%`.

| Signal                         | Max Points | Logic                                        |
|--------------------------------|-----------|----------------------------------------------|
| 6M Return Percentile           | 30        | Linear: 50th→0, 100th→30                    |
| 3M Return (short-term heat)    | 20        | Step: >8%→5, >12%→10, >18%→20               |
| Distance from 10M MA           | 20        | Linear: 5%→0, 25%+→20                       |
| Momentum Z-score               | 15        | Linear: 0.5→0, 2.0+→15                      |
| Volatility spike               | 10        | Binary: vol > 1.5× median → 10              |
| Momentum decelerating + extended| 5        | Binary: decel AND 6M > 15% → 5              |
| Drawdown danger                | 25        | Step: >-30%→25, >-20%→15                     |
| **TOTAL POSSIBLE**             | **125**   | Clamped to 100                               |

### Risk Score Persistence

The key innovation: **risk score decays slowly** (max -20 pts/month).

When signals fade (e.g., at the start of a crash when returns turn negative), the effective risk score doesn't snap to 0 — it decays gradually. This keeps you protected through the critical early crash months.

```
             ┌─── Raw score drops as crash starts (returns go negative)
             │    BUT effective score holds high due to persistence
             ▼
Risk Score: 95 → 75 → 55 → 35 → 15 → 0  (5 months to fully decay)
Cash:       50% → 40% → 30% → 20% → 10% → 0%
```

### How It Behaves

| Market Phase        | Risk Score | Momentum | Cash   | Why                           |
|--------------------|-----------|----------|--------|-------------------------------|
| Normal market       | 0–10      | 100%     | 0%     | No signals → fully invested   |
| Early bull run      | 10–25     | 90–95%   | 5–10%  | Some extension signals fire   |
| Late bull (extended)| 50–80     | 60–75%   | 25–40% | Multiple signals accumulating |
| Peak overextension  | 80–100    | 50–60%   | 40–50% | Near-maximum protection       |
| Early crash         | 60–80     | 60–70%   | 30–40% | Persistence holds protection  |
| Deep crash          | 25–50     | 75–90%   | 10–25% | DD danger signal + persistence|
| Recovery            | 0–10      | 100%     | 0%     | All signals fade, fully back  |

## Performance (2005–2025)

| Metric              | MOMCASH v2           | Pure Momentum (100%)  | Static 75/25         |
|---------------------|---------------------|-----------------------|---------------------|
| Index CAGR          | ~18.0%              | 21.2%                 | 17.6%               |
| SIP XIRR            | ~15.1%              | 18.8%                 | 15.7%               |
| Max Drawdown (SIP)  | ~-45%               | -60%                  | -44%                |
| MAR Ratio           | 0.33                | 0.31                  | 0.35                |
| Sharpe Ratio        | 0.67                | 0.71                  | 0.71                |
| Ulcer Index         | 14.0                | 18.9                  | 13.3                |
| Avg Cash            | ~15%                | 0%                    | 25%                 |

### Key Tradeoff
- Gave up ~3.2% CAGR vs Pure Momentum
- Saved ~14.5% max drawdown
- Each 1% CAGR sacrifice bought 4.5% drawdown reduction
- MAR ratio improved (0.31 → 0.33)
- Ulcer Index improved (18.9 → 14.0)

## Signal Logic

All signals are **lagged by 1 month** (signal_t → allocation_t+1). No lookahead bias.

### Risk Signals (cash building)
- **Momentum Extension**: 6M return percentile vs rolling 36M history
- **Short-term Heat**: 3M return stepped thresholds (8%, 12%, 18%)
- **Distance from MA**: How far above 10-month moving average
- **Z-score**: Statistical extremeness of current momentum
- **Volatility Spike**: 3M vol > 1.5× rolling 36M median
- **Deceleration**: Momentum slowing while still extended (6M > 15%)
- **Drawdown Danger**: In deep drawdown (-20%+), hold cash don't deploy

### No Explicit Reload
The system returns to fully invested naturally through persistence decay. No explicit "reload" signal is needed — when risk signals fade and drawdown recovers, the score decays to 0 and you're fully invested again.

## File Structure

```
nifty500cash/
├── README.md                              ← This file
├── analysis/
│   ├── nifty500cash_strategy.py           ← Core MOMCASH v2 strategy engine
│   └── nifty500cash_analytics.py          ← Analytics & dashboard JSON generator
└── output/
    ├── monthly/
    │   └── nifty500cash_momcash_portfolio.csv  ← Strategy output data
    └── nifty500cash_dashboard.json            ← Dashboard JSON
```

## Usage

### Run Strategy
```bash
cd smart_beta_investing
python3 nifty500cash/analysis/nifty500cash_strategy.py
```

### Generate Dashboard Data
```bash
python3 nifty500cash/analysis/nifty500cash_analytics.py
```

## Why This Works

The old binary tier approach failed because:
1. **AND logic = too late**: Required ALL conditions to align before de-risking
2. **Binary switching = too sudden**: Jumped from base → overheated in one step
3. **No persistence**: Risk score snapped to 0 when crash started (signals reversed)

The v2 approach fixes all three:
1. **Independent signals**: Each signal adds cash on its own (OR logic)
2. **Gradual building**: Cash accumulates progressively as bull extends
3. **Persistence**: Risk score decays slowly — protection lasts through early crash

This is **systematic risk management**, not crash prediction.
