"""Debug 2025 returns for Nifty 200 strategy"""
import pandas as pd
import numpy as np
from pathlib import Path

base = Path(__file__).parent.parent

# Load the generated portfolio CSV
portfolio_file = base / 'nifty200' / 'output' / 'monthly' / 'portfolio_ratio_trend_75_25.csv'
df = pd.read_csv(portfolio_file)
df['Date'] = pd.to_datetime(df['Date'])

# Filter 2025
df_2025 = df[df['Date'].dt.year == 2025].copy()

print("=" * 100)
print("2025 MONTH-BY-MONTH BREAKDOWN — NIFTY 200")
print("=" * 100)
print(f"\n{'Date':<12s} {'regime':<12s} {'w_mom':>6s} {'w_val':>6s} {'Ret_mom':>9s} {'Ret_val':>9s} {'Port_Ret':>9s} {'RelMom_6M':>10s}")
print("-" * 80)

for _, row in df_2025.iterrows():
    ret_m = f"{row['Return_mom']*100:.2f}%" if not np.isnan(row['Return_mom']) else "NaN"
    ret_v = f"{row['Return_val']*100:.2f}%" if not np.isnan(row['Return_val']) else "NaN"
    port_r = f"{row['Portfolio_Return']*100:.2f}%" if not np.isnan(row['Portfolio_Return']) else "NaN"
    rm = f"{row['RelMom_6M']:.4f}" if 'RelMom_6M' in row.index and not np.isnan(row['RelMom_6M']) else "NaN"
    print(f"{row['Date'].strftime('%Y-%m-%d'):<12s} {row['regime']:<12s} {row['w_mom']:>6.1f} {row['w_val']:>6.1f} {ret_m:>9s} {ret_v:>9s} {port_r:>9s} {rm:>10s}")

# Annual returns
mom_2025 = (1 + df_2025['Return_mom']).prod() - 1
val_2025 = (1 + df_2025['Return_val']).prod() - 1
port_2025 = (1 + df_2025['Portfolio_Return']).prod() - 1

print(f"\n2025 Annual Returns:")
print(f"  Momentum: {mom_2025*100:.2f}%")
print(f"  Value:    {val_2025*100:.2f}%")
print(f"  Strategy: {port_2025*100:.2f}%")

# Also show late 2024 to see the signal leading into 2025
print(f"\n\nLATE 2024 (context for signal shifts):")
df_late2024 = df[(df['Date'].dt.year == 2024) & (df['Date'].dt.month >= 9)]
print(f"\n{'Date':<12s} {'regime':<12s} {'w_mom':>6s} {'w_val':>6s} {'Ret_mom':>9s} {'Ret_val':>9s} {'Port_Ret':>9s} {'RelMom_6M':>10s}")
print("-" * 80)
for _, row in df_late2024.iterrows():
    ret_m = f"{row['Return_mom']*100:.2f}%" if not np.isnan(row['Return_mom']) else "NaN"
    ret_v = f"{row['Return_val']*100:.2f}%" if not np.isnan(row['Return_val']) else "NaN"
    port_r = f"{row['Portfolio_Return']*100:.2f}%" if not np.isnan(row['Portfolio_Return']) else "NaN"
    rm = f"{row['RelMom_6M']:.4f}" if 'RelMom_6M' in row.index and not np.isnan(row['RelMom_6M']) else "NaN"
    print(f"{row['Date'].strftime('%Y-%m-%d'):<12s} {row['regime']:<12s} {row['w_mom']:>6.1f} {row['w_val']:>6.1f} {ret_m:>9s} {ret_v:>9s} {port_r:>9s} {rm:>10s}")

# Check: what would pure value have given for the same months the strategy was in value?
print(f"\n\nWHAT-IF ANALYSIS:")
print("If strategy were 100% value all of 2025:")
val_full = (1 + df_2025['Return_val']).prod() - 1
print(f"  Return: {val_full*100:.2f}%")
print("If strategy were 100% momentum all of 2025:")
mom_full = (1 + df_2025['Return_mom']).prod() - 1
print(f"  Return: {mom_full*100:.2f}%")

# Check months where strategy was in momentum during 2025
mom_months = df_2025[df_2025['regime'] == 'momentum']
val_months = df_2025[df_2025['regime'] == 'value']
print(f"\nMonths in momentum: {len(mom_months)}")
print(f"Months in value:    {len(val_months)}")
if len(mom_months) > 0:
    print(f"Return during momentum months (mom factor): {(1+mom_months['Return_mom']).prod()-1:.4f}")
    print(f"Return during momentum months (val factor): {(1+mom_months['Return_val']).prod()-1:.4f}")
