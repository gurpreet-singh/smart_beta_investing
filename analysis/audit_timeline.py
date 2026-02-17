"""
Audit the timeline of regime assignments to verify correctness
"""
import pandas as pd
import numpy as np
from pathlib import Path

base = Path(__file__).parent.parent

# Load nifty200 data
mom_file = base / 'nifty200' / 'output' / 'monthly' / 'nifty200_momentum_30_monthly.csv'
val_file = base / 'nifty200' / 'output' / 'monthly' / 'nifty200_value_30_monthly.csv'

mom_df = pd.read_csv(mom_file)
mom_df['Date'] = pd.to_datetime(mom_df['Date'])
mom_df = mom_df.rename(columns={'Close': 'Close_mom'})

val_df = pd.read_csv(val_file)
val_df['Date'] = pd.to_datetime(val_df['Date'])
val_df = val_df.rename(columns={'Close': 'Close_val'})

df = pd.merge(mom_df[['Date', 'Close_mom']], val_df[['Date', 'Close_val']], on='Date', how='inner')
df['Return_mom'] = df['Close_mom'].pct_change()
df['Return_val'] = df['Close_val'].pct_change()
df['Quarter'] = df['Date'].dt.to_period('Q')

df['RelMom_6M'] = df['Close_mom'].pct_change(6) - df['Close_val'].pct_change(6)

quarterly = df.groupby('Quarter').last()
quarterly['regime'] = np.where(quarterly['RelMom_6M'] > 0, 'momentum', 'value')

# === CURRENT METHOD: shift(1) at quarterly level ===
quarterly['regime_exec'] = quarterly['regime'].shift(1)

print("=" * 80)
print("QUARTERLY TABLE (current method: shift(1) at quarterly level)")
print("=" * 80)
print(f"\n{'Quarter':<12s} {'Last Date':<12s} {'RelMom_6M':>10s} {'regime':>12s} {'regime_exec':>12s}")
print("-" * 60)
for q in quarterly.index[:12]:
    row = quarterly.loc[q]
    rm = f"{row['RelMom_6M']:.4f}" if not np.isnan(row['RelMom_6M']) else "NaN"
    re = row['regime_exec'] if pd.notna(row['regime_exec']) else "NaN"
    print(f"{str(q):<12s} {row['Date'].strftime('%Y-%m-%d'):<12s} {rm:>10s} {row['regime']:>12s} {re:>12s}")

# Now merge to monthly
df_current = df.copy()
df_current = df_current.merge(quarterly[['regime_exec']], left_on='Quarter', right_index=True, how='left')
df_current['regime'] = df_current['regime_exec'].ffill().fillna('value')

print("\n\nMONTHLY TIMELINE (current: quarterly shift(1))")
print(f"\n{'Date':<12s} {'Quarter':<10s} {'RelMom_6M':>10s} {'regime':>12s} {'Return_mom':>11s} {'Return_val':>11s}")
print("-" * 70)
for i in range(min(24, len(df_current))):
    row = df_current.iloc[i]
    rm = f"{row['RelMom_6M']:.4f}" if not np.isnan(row['RelMom_6M']) else "NaN"
    ret_m = f"{row['Return_mom']:.4f}" if not np.isnan(row['Return_mom']) else "NaN"
    ret_v = f"{row['Return_val']:.4f}" if not np.isnan(row['Return_val']) else "NaN"
    print(f"{row['Date'].strftime('%Y-%m-%d'):<12s} {str(row['Quarter']):<10s} {rm:>10s} {row['regime']:>12s} {ret_m:>11s} {ret_v:>11s}")

# === CORRECT METHOD: What it SHOULD be ===
# The decision at quarter-end Q should apply starting FIRST MONTH of Q+1
# That means: shift by 1 quarter, then merge
# But that's exactly what shift(1) at quarterly level does when merged by Quarter
# The issue is: does the FIRST month of Q+1 get the right regime?

print("\n\n" + "=" * 80)
print("VERIFICATION: Does April get Q1's decision?")
print("=" * 80)

# Find a transition to verify
for i in range(6, len(df_current)-1):
    row = df_current.iloc[i]
    prev = df_current.iloc[i-1]
    if str(row['Quarter']) != str(prev['Quarter']):
        print(f"\nQuarter boundary: {prev['Date'].strftime('%Y-%m-%d')} ({prev['Quarter']}) -> {row['Date'].strftime('%Y-%m-%d')} ({row['Quarter']})")
        print(f"  Previous month regime: {prev['regime']}")
        print(f"  This month regime:     {row['regime']}")
        # What was the quarterly decision for the previous quarter?
        prev_q = prev['Quarter']
        if prev_q in quarterly.index:
            q_row = quarterly.loc[prev_q]
            print(f"  Previous quarter ({prev_q}) decision: {q_row['regime']} -> regime_exec: {q_row['regime_exec'] if pd.notna(q_row['regime_exec']) else 'NaN'}")
        curr_q = row['Quarter']
        if curr_q in quarterly.index:
            q_row = quarterly.loc[curr_q]
            print(f"  Current quarter ({curr_q}) regime_exec: {q_row['regime_exec'] if pd.notna(q_row['regime_exec']) else 'NaN'}")
        if i > 12:
            break

# === ALTERNATIVE: The proper way ===
# Decision at end of Q(t) should apply to all of Q(t+1)
# quarterly['regime_exec'] = quarterly['regime'].shift(1) does this correctly
# because when we merge by Quarter, Q(t+1) rows get regime_exec = regime from Q(t)

# But what about within-Q(t+1)? All 3 months get the SAME regime_exec.
# That IS correct — the decision holds for the entire next quarter.

print("\n\n" + "=" * 80)
print("BENCHMARK COMPARISON: Strategy vs Pure Momentum vs Pure Value")
print("=" * 80)

# Calculate pure buy-and-hold returns
years = len(df) / 12
mom_cagr = ((df['Close_mom'].iloc[-1] / df['Close_mom'].iloc[0]) ** (1/years) - 1) * 100
val_cagr = ((df['Close_val'].iloc[-1] / df['Close_val'].iloc[0]) ** (1/years) - 1) * 100
equal_cagr = 0.5 * mom_cagr + 0.5 * val_cagr  # approximate

df_current['w_mom'] = np.where(df_current['regime'] == 'momentum', 1.0, 0.0)
df_current['w_val'] = 1.0 - df_current['w_mom']
df_current['Portfolio_Return'] = df_current['w_mom'] * df_current['Return_mom'] + df_current['w_val'] * df_current['Return_val']
df_current['Portfolio_NAV'] = 1000 * (1 + df_current['Portfolio_Return']).cumprod()
df_current.loc[0, 'Portfolio_NAV'] = 1000

strat_cagr = ((df_current['Portfolio_NAV'].iloc[-1] / 1000) ** (1/years) - 1) * 100

print(f"\n  Pure Momentum CAGR:  {mom_cagr:.2f}%")
print(f"  Pure Value CAGR:     {val_cagr:.2f}%")
print(f"  50/50 Static CAGR:   ~{equal_cagr:.2f}% (approx)")
print(f"  Strategy CAGR:       {strat_cagr:.2f}%")
print(f"  Alpha vs 50/50:      {strat_cagr - equal_cagr:+.2f}%")
print(f"  Alpha vs best:       {strat_cagr - max(mom_cagr, val_cagr):+.2f}%")
