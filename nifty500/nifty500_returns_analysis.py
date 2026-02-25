#!/usr/bin/env python3
from __future__ import annotations
"""
Nifty 500 Returns Analysis
===========================
Calculates rolling CAGR for every month from 2005 to present:
  - 1 Year CAGR
  - 3 Year CAGR
  - 5 Year CAGR
  - 10 Year CAGR

Applies the same analysis to:
  - Nifty 500 Momentum 50 Index
  - Nifty 500 Value 50 Index

Output: nifty500/output/nifty500_returns_analysis.json
"""

import pandas as pd
import numpy as np
import json
import os
from pathlib import Path

# ─────────────────────────────────────────────
# PATHS
# ─────────────────────────────────────────────
BASE_DIR     = Path(__file__).parent
MOMENTUM_CSV = BASE_DIR / "output" / "monthly" / "nifty500_momentum_50_monthly.csv"
VALUE_CSV    = BASE_DIR / "output" / "monthly" / "nifty500_value_50_monthly.csv"
OUTPUT_DIR   = BASE_DIR / "output"
OUTPUT_FILE  = OUTPUT_DIR / "nifty500_returns_analysis.json"
OUTPUT_CSV_DIR = OUTPUT_DIR / "returns_analysis"

OUTPUT_CSV_DIR.mkdir(parents=True, exist_ok=True)


# ─────────────────────────────────────────────
# CAGR CALCULATION HELPER
# ─────────────────────────────────────────────
def compute_cagr(start_value: float, end_value: float, years: float) -> float | None:
    """Returns annualised CAGR as a percentage, or None if data is insufficient."""
    if start_value <= 0 or years <= 0:
        return None
    cagr = ((end_value / start_value) ** (1.0 / years) - 1) * 100
    return round(cagr, 4)


# ─────────────────────────────────────────────
# LOAD AND PREPROCESS
# ─────────────────────────────────────────────
def load_monthly_data(csv_path: Path) -> pd.DataFrame:
    df = pd.read_csv(csv_path, parse_dates=["Date"])
    df = df.dropna(subset=["Close"])
    df = df.sort_values("Date").reset_index(drop=True)
    df["YearMonth"] = df["Date"].dt.to_period("M")
    return df


# ─────────────────────────────────────────────
# ROLLING CAGR ENGINE
# ─────────────────────────────────────────────
PERIODS = {
    "1Y":  1,
    "3Y":  3,
    "5Y":  5,
    "10Y": 10,
}


def compute_rolling_cagrs(df: pd.DataFrame) -> pd.DataFrame:
    """
    For each row (end month), look back N years and compute CAGR.
    Returns a DataFrame with columns: Date, Close, CAGR_1Y, CAGR_3Y, CAGR_5Y, CAGR_10Y.
    """
    results = []

    for i, row in df.iterrows():
        end_date  = row["Date"]
        end_value = row["Close"]
        record = {
            "Date":  end_date.strftime("%Y-%m"),
            "Close": end_value,
        }

        for label, years in PERIODS.items():
            target_date = end_date - pd.DateOffset(years=years)
            past_rows   = df[df["Date"] <= target_date]
            if len(past_rows) == 0:
                record[f"CAGR_{label}"] = None
            else:
                past_row     = past_rows.iloc[-1]
                start_value  = past_row["Close"]
                actual_years = (end_date - past_row["Date"]).days / 365.25
                record[f"CAGR_{label}"] = compute_cagr(start_value, end_value, actual_years)

        results.append(record)

    return pd.DataFrame(results)


# ─────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────
def main():
    print("=" * 60)
    print("  Nifty 500 Returns Analysis")
    print("=" * 60)

    # Momentum
    print("\n📊 Loading Nifty 500 Momentum 50 data …")
    mom_df = load_monthly_data(MOMENTUM_CSV)
    print(f"   Rows: {len(mom_df)}  |  Range: {mom_df['Date'].min().date()} → {mom_df['Date'].max().date()}")

    mom_cagr = compute_rolling_cagrs(mom_df)
    print(f"   1Y CAGR rows : {mom_cagr['CAGR_1Y'].notna().sum()}")
    print(f"   3Y CAGR rows : {mom_cagr['CAGR_3Y'].notna().sum()}")
    print(f"   5Y CAGR rows : {mom_cagr['CAGR_5Y'].notna().sum()}")
    print(f"   10Y CAGR rows: {mom_cagr['CAGR_10Y'].notna().sum()}")

    # Value
    print("\n📊 Loading Nifty 500 Value 50 data …")
    val_df = load_monthly_data(VALUE_CSV)
    print(f"   Rows: {len(val_df)}  |  Range: {val_df['Date'].min().date()} → {val_df['Date'].max().date()}")

    val_cagr = compute_rolling_cagrs(val_df)
    print(f"   1Y CAGR rows : {val_cagr['CAGR_1Y'].notna().sum()}")
    print(f"   3Y CAGR rows : {val_cagr['CAGR_3Y'].notna().sum()}")
    print(f"   5Y CAGR rows : {val_cagr['CAGR_5Y'].notna().sum()}")
    print(f"   10Y CAGR rows: {val_cagr['CAGR_10Y'].notna().sum()}")

    # ── Save CSVs ──────────────────────────────
    mom_csv_out = OUTPUT_CSV_DIR / "momentum_cagr_monthly.csv"
    val_csv_out = OUTPUT_CSV_DIR / "value_cagr_monthly.csv"
    mom_cagr.to_csv(mom_csv_out, index=False)
    val_cagr.to_csv(val_csv_out, index=False)
    print(f"\n✅ CSVs saved:")
    print(f"   {mom_csv_out}")
    print(f"   {val_csv_out}")

    # ── Build JSON for dashboard ───────────────
    def df_to_chart_series(cagr_df: pd.DataFrame) -> dict:
        series = {}
        for label in PERIODS.keys():
            col  = f"CAGR_{label}"
            mask = cagr_df[col].notna()
            series[label] = {
                "dates":  cagr_df.loc[mask, "Date"].tolist(),
                "values": cagr_df.loc[mask, col].tolist(),
            }
        return series

    output = {
        "metadata": {
            "generated_at":   pd.Timestamp.now().strftime("%Y-%m-%d %H:%M:%S"),
            "momentum_start": mom_df["Date"].min().strftime("%Y-%m"),
            "momentum_end":   mom_df["Date"].max().strftime("%Y-%m"),
            "value_start":    val_df["Date"].min().strftime("%Y-%m"),
            "value_end":      val_df["Date"].max().strftime("%Y-%m"),
        },
        "momentum": df_to_chart_series(mom_cagr),
        "value":    df_to_chart_series(val_cagr),
    }

    with open(OUTPUT_FILE, "w") as f:
        json.dump(output, f, indent=2)

    size_kb = OUTPUT_FILE.stat().st_size / 1024
    print(f"\n✅ JSON saved: {OUTPUT_FILE}  ({size_kb:.1f} KB)")

    print("\n" + "=" * 60)
    print("  Summary statistics:")
    print("=" * 60)
    for label in PERIODS.keys():
        mom_vals = mom_cagr[f"CAGR_{label}"].dropna()
        val_vals = val_cagr[f"CAGR_{label}"].dropna()
        if len(mom_vals) > 0 and len(val_vals) > 0:
            print(f"\n  {label} CAGR:")
            print(f"    Momentum → Min: {mom_vals.min():.1f}%  Max: {mom_vals.max():.1f}%  Avg: {mom_vals.mean():.1f}%")
            print(f"    Value    → Min: {val_vals.min():.1f}%  Max: {val_vals.max():.1f}%  Avg: {val_vals.mean():.1f}%")

    print("\n🚀 Dashboard JSON ready. Refresh the browser to see the charts!")


if __name__ == "__main__":
    main()
