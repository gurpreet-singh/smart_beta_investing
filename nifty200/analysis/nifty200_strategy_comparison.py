"""
Nifty 200 Strategy Comparison
Compare existing strategy (free switching) vs 2-month cooldown with 50/50 transition

The 2-month cooldown rule with 50/50 transition:
- After a switch happens in Jan, the next full switch can only happen in March.
- During the cooldown month (Feb), if the signal wants to switch:
  → Instead of blocking entirely, allocate 50/50 (equal weight)
  → This softens the transition instead of hard-locking
- If the signal agrees with the current allocation during cooldown, keep 75/25.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Import from the existing strategy module
import sys
sys.path.insert(0, str(Path(__file__).parent))
from nifty200_portfolio_strategy import PortfolioStrategy, calculate_xirr


def apply_cooldown_with_5050(df):
    """Apply 2-month cooldown with 50/50 allocation during cooldown disagreements.
    
    Logic:
    - When a full switch occurs, start a 2-month cooldown (next switch in 2 months).
    - During cooldown, if raw signal disagrees with current regime:
        → Use 50/50 allocation (instead of hard-locking to old allocation)
    - During cooldown, if raw signal agrees with current regime:
        → Keep the normal 75/25 allocation
    - After cooldown expires, a full switch is allowed again.
    
    Returns:
        DataFrame with 'w_mom_cooldown' and 'w_val_cooldown' columns
    """
    df = df.copy()
    
    signals = df['Signal_Binary'].values.copy()
    n = len(signals)
    
    w_mom = np.zeros(n)
    w_val = np.zeros(n)
    allocation_type = [''] * n  # Track: 'normal' or '50/50'
    
    # Start with first signal's allocation
    current_regime_signal = signals[0]
    if current_regime_signal == 1:
        w_mom[0] = 0.75
    else:
        w_mom[0] = 0.25
    w_val[0] = 1 - w_mom[0]
    allocation_type[0] = 'normal'
    
    months_since_switch = 999  # Allow first switch freely
    
    for i in range(1, n):
        months_since_switch += 1
        raw_signal = signals[i]
        
        if raw_signal != current_regime_signal:
            # Signal wants to switch
            if months_since_switch >= 2:
                # Cooldown expired → allow full switch
                current_regime_signal = raw_signal
                months_since_switch = 0
                # Normal 75/25 allocation
                if current_regime_signal == 1:
                    w_mom[i] = 0.75
                else:
                    w_mom[i] = 0.25
                allocation_type[i] = 'normal'
            else:
                # Still in cooldown → go 50/50
                w_mom[i] = 0.50
                allocation_type[i] = '50/50'
        else:
            # Signal agrees with current regime → normal allocation
            if current_regime_signal == 1:
                w_mom[i] = 0.75
            else:
                w_mom[i] = 0.25
            allocation_type[i] = 'normal'
        
        w_val[i] = 1 - w_mom[i]
    
    df['w_mom_cooldown'] = w_mom
    df['w_val_cooldown'] = w_val
    df['Allocation_Type'] = allocation_type
    
    return df


def run_comparison():
    """Run both strategies and compare results."""
    
    print("\n" + "=" * 100)
    print(" " * 10 + "NIFTY 200 STRATEGY COMPARISON")
    print(" " * 10 + "EXISTING vs 2-MONTH COOLDOWN WITH 50/50 TRANSITION")
    print("=" * 100)
    
    # --- Use the existing PortfolioStrategy class to load data & compute signals ---
    data_folder = Path(__file__).parent.parent / "data"
    strategy = PortfolioStrategy(data_folder, monthly_sip=10000)
    
    # Load and prepare data (same for both strategies)
    df = strategy.load_monthly_data()
    df = strategy.calculate_returns(df)
    df = strategy.signal_ratio_trend(df, ma_length=6)
    
    # ========================================================================
    # STRATEGY 1: EXISTING (Free Switching)
    # ========================================================================
    df_existing = df.copy()
    df_existing = strategy.apply_allocation(df_existing)
    df_existing = strategy.calculate_portfolio_returns(df_existing)
    
    results_existing, sip_existing = strategy.run_sip_on_portfolio(
        df_existing, 'Existing (Free Switching)'
    )
    
    # Count switches for existing
    existing_switches = (df_existing['Signal_Binary'].diff().abs() > 0).sum()
    
    # ========================================================================
    # STRATEGY 2: 2-MONTH COOLDOWN WITH 50/50 TRANSITION  
    # ========================================================================
    df_cooldown = df.copy()
    df_cooldown = apply_cooldown_with_5050(df_cooldown)
    
    # Use the cooldown weights for portfolio
    df_cooldown['w_mom'] = df_cooldown['w_mom_cooldown']
    df_cooldown['w_val'] = df_cooldown['w_val_cooldown']
    
    # Calculate portfolio returns
    df_cooldown['Portfolio_Return'] = (
        df_cooldown['w_mom'] * df_cooldown['Return_mom'] +
        df_cooldown['w_val'] * df_cooldown['Return_val']
    )
    df_cooldown['Portfolio_NAV'] = 1000 * (1 + df_cooldown['Portfolio_Return']).cumprod()
    df_cooldown.loc[0, 'Portfolio_NAV'] = 1000
    
    results_cooldown, sip_cooldown = strategy.run_sip_on_portfolio(
        df_cooldown, '3-Month Cooldown + 50/50'
    )
    
    # Count actual regime changes (full switches only, not 50/50 transitions)
    # A "full switch" is when allocation goes from 75/25 to 25/75 or vice versa
    full_switches = 0
    prev_regime = None
    for i, row in df_cooldown.iterrows():
        if row['Allocation_Type'] == 'normal':
            regime = 'mom' if row['w_mom'] == 0.75 else 'val'
            if prev_regime is not None and regime != prev_regime:
                full_switches += 1
            prev_regime = regime
    
    # Count total months at 50/50
    months_5050 = (df_cooldown['Allocation_Type'] == '50/50').sum()
    
    # ========================================================================
    # DISPLAY COMPARISON
    # ========================================================================
    
    print("\n" + "=" * 100)
    print(" " * 25 + "📊 STRATEGY COMPARISON RESULTS")
    print("=" * 100)
    
    # --- Switch / Allocation Analysis ---
    print("\n" + "─" * 100)
    print("🔄 SWITCH & ALLOCATION ANALYSIS")
    print("─" * 100)
    print(f"   Existing Strategy Switches:         {existing_switches}")
    print(f"   Cooldown Strategy Full Switches:     {full_switches}")
    print(f"   Months at 50/50 Allocation:          {months_5050}")
    print(f"   Full Switches Avoided:               {existing_switches - full_switches}")
    print(f"   Reduction in Full Switches:          {((existing_switches - full_switches) / existing_switches * 100):.1f}%")
    
    # --- Show months where 50/50 was applied ---
    months_5050_df = df_cooldown[df_cooldown['Allocation_Type'] == '50/50'][
        ['Date', 'Signal_Binary', 'w_mom_cooldown', 'Ratio', 'Ratio_MA']
    ]
    
    if len(months_5050_df) > 0:
        print(f"\n   Months with 50/50 allocation (cooldown active, signal disagreed) — {len(months_5050_df)} months:")
        print(f"   {'Date':<14} {'Raw Signal':<14} {'Allocation':<18} {'Ratio':<12} {'Ratio MA':<12}")
        print(f"   {'─' * 68}")
        for _, row in months_5050_df.iterrows():
            raw_regime = 'Momentum' if row['Signal_Binary'] == 1 else 'Value'
            print(f"   {row['Date'].strftime('%Y-%m'):<14} {raw_regime:<14} {'50/50':<18} {row['Ratio']:.4f}      {row['Ratio_MA']:.4f}")
    
    # --- Performance Comparison ---
    print("\n" + "─" * 100)
    print("📈 PERFORMANCE COMPARISON")
    print("─" * 100)
    
    header = f"   {'Metric':<35} {'Existing':<25} {'Cooldown + 50/50':<25} {'Difference':<15}"
    print(header)
    print(f"   {'─' * 95}")
    
    # CAGR
    cagr_diff = results_cooldown['index_cagr'] - results_existing['index_cagr']
    print(f"   {'CAGR (Index)':<35} {results_existing['index_cagr']:>10.2f}%{'':<14} {results_cooldown['index_cagr']:>10.2f}%{'':<14} {cagr_diff:>+.2f}%")
    
    # SIP XIRR
    xirr_diff = results_cooldown['sip_xirr'] - results_existing['sip_xirr']
    print(f"   {'XIRR (SIP Returns)':<35} {results_existing['sip_xirr']:>10.2f}%{'':<14} {results_cooldown['sip_xirr']:>10.2f}%{'':<14} {xirr_diff:>+.2f}%")
    
    print(f"   {'─' * 95}")
    
    # Additional metrics
    print(f"   {'Total Invested':<35} ₹{results_existing['total_invested']:>12,.0f}{'':<12} ₹{results_cooldown['total_invested']:>12,.0f}")
    print(f"   {'Final Portfolio Value':<35} ₹{results_existing['final_value']:>12,.0f}{'':<12} ₹{results_cooldown['final_value']:>12,.0f}")
    
    gain_diff = results_cooldown['absolute_gain'] - results_existing['absolute_gain']
    print(f"   {'Absolute Gain':<35} ₹{results_existing['absolute_gain']:>12,.0f}{'':<12} ₹{results_cooldown['absolute_gain']:>12,.0f}{'':<12} ₹{gain_diff:>+,.0f}")
    
    print(f"   {'Total Return %':<35} {results_existing['total_return_pct']:>10.2f}%{'':<14} {results_cooldown['total_return_pct']:>10.2f}%")
    
    print(f"   {'Max Drawdown':<35} {results_existing['max_drawdown']:>10.2f}%{'':<14} {results_cooldown['max_drawdown']:>10.2f}%")
    print(f"   {'Max Investor Drawdown':<35} {results_existing['max_investor_drawdown']:>10.2f}%{'':<14} {results_cooldown['max_investor_drawdown']:>10.2f}%")
    print(f"   {'MAR Ratio':<35} {results_existing['mar_ratio']:>10.2f}{'':<15} {results_cooldown['mar_ratio']:>10.2f}")
    
    print(f"   {'Start NAV':<35} {results_existing['start_nav']:>10.2f}{'':<15} {results_cooldown['start_nav']:>10.2f}")
    print(f"   {'End NAV':<35} {results_existing['end_nav']:>10.2f}{'':<15} {results_cooldown['end_nav']:>10.2f}")
    
    # --- Summary ---
    print("\n" + "=" * 100)
    print(" " * 30 + "📋 SUMMARY")
    print("=" * 100)
    
    if cagr_diff > 0:
        print(f"\n   ✅ Cooldown + 50/50 has HIGHER CAGR by {cagr_diff:+.2f}%")
    else:
        print(f"\n   ❌ Cooldown + 50/50 has LOWER CAGR by {cagr_diff:+.2f}%")
    
    if xirr_diff > 0:
        print(f"   ✅ Cooldown + 50/50 has HIGHER SIP XIRR by {xirr_diff:+.2f}%")
    else:
        print(f"   ❌ Cooldown + 50/50 has LOWER SIP XIRR by {xirr_diff:+.2f}%")
    
    dd_diff = results_cooldown['max_drawdown'] - results_existing['max_drawdown']
    if dd_diff > 0:  # Less negative = better
        print(f"   ✅ Cooldown + 50/50 has LOWER Max Drawdown (better risk) by {dd_diff:+.2f}%")
    else:
        print(f"   ❌ Cooldown + 50/50 has HIGHER Max Drawdown (worse risk) by {dd_diff:+.2f}%")
    
    print(f"\n   💡 Full switches reduced from {existing_switches} → {full_switches} ({((existing_switches - full_switches) / existing_switches * 100):.0f}% fewer)")
    print(f"   💡 {months_5050} months used 50/50 allocation during cooldown periods")
    
    print("\n" + "=" * 100 + "\n")
    
    return results_existing, results_cooldown


if __name__ == "__main__":
    run_comparison()
