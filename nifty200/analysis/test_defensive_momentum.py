"""
Test Defensive Momentum Strategy

New rule: When in momentum regime, if value's 3M return > momentum's 3M return,
use 50/50 allocation instead of 100/0 until momentum regains leadership.

Compare:
1. Binary 100/0 (Current)
2. Defensive 100/0 with 50/50 fallback (New)
"""

import pandas as pd
import numpy as np
from pathlib import Path

def run_binary_strategy():
    """Current strategy: Pure binary 100/0"""
    
    # Load data
    data_folder = Path(__file__).parent.parent / "output" / "monthly"
    mom_file = data_folder / "nifty200_momentum_30_monthly.csv"
    val_file = data_folder / "nifty200_value_30_monthly.csv"
    
    mom_df = pd.read_csv(mom_file, parse_dates=['Date'])
    val_df = pd.read_csv(val_file, parse_dates=['Date'])
    
    df = mom_df[['Date', 'Close']].merge(
        val_df[['Date', 'Close']],
        on='Date',
        suffixes=('_mom', '_val')
    )
    
    # Calculate returns
    df['Return_mom'] = df['Close_mom'].pct_change()
    df['Return_val'] = df['Close_val'].pct_change()
    df['Mom_3M_Return'] = df['Close_mom'].pct_change(3) * 100
    
    # Binary regime
    df['regime'] = 'momentum'
    for i in range(1, len(df)):
        mom_3m = df.loc[i, 'Mom_3M_Return']
        prev_regime = df.loc[i-1, 'regime']
        
        if pd.isna(mom_3m):
            df.loc[i, 'regime'] = prev_regime
            continue
        
        if mom_3m >= 20:
            df.loc[i, 'regime'] = 'momentum'
        elif mom_3m <= -15:
            df.loc[i, 'regime'] = 'value'
        else:
            df.loc[i, 'regime'] = prev_regime
    
    # Binary allocation
    df['w_mom'] = np.where(df['regime'] == 'momentum', 1.0, 0.0)
    df['w_val'] = 1.0 - df['w_mom']
    
    # Shift weights
    df['w_mom'] = df['w_mom'].shift(1).fillna(1.0)
    df['w_val'] = df['w_val'].shift(1).fillna(0.0)
    
    # Calculate returns
    df['Portfolio_Return'] = df['w_mom'] * df['Return_mom'] + df['w_val'] * df['Return_val']
    df['Portfolio_NAV'] = 100 * (1 + df['Portfolio_Return']).cumprod()
    
    return df

def run_defensive_strategy():
    """New strategy: 50/50 when value outperforms in momentum regime"""
    
    # Load data
    data_folder = Path(__file__).parent.parent / "output" / "monthly"
    mom_file = data_folder / "nifty200_momentum_30_monthly.csv"
    val_file = data_folder / "nifty200_value_30_monthly.csv"
    
    mom_df = pd.read_csv(mom_file, parse_dates=['Date'])
    val_df = pd.read_csv(val_file, parse_dates=['Date'])
    
    df = mom_df[['Date', 'Close']].merge(
        val_df[['Date', 'Close']],
        on='Date',
        suffixes=('_mom', '_val')
    )
    
    # Calculate returns
    df['Return_mom'] = df['Close_mom'].pct_change()
    df['Return_val'] = df['Close_val'].pct_change()
    df['Mom_3M_Return'] = df['Close_mom'].pct_change(3) * 100
    df['Val_3M_Return'] = df['Close_val'].pct_change(3) * 100
    
    # Regime detection (same as binary)
    df['regime'] = 'momentum'
    for i in range(1, len(df)):
        mom_3m = df.loc[i, 'Mom_3M_Return']
        prev_regime = df.loc[i-1, 'regime']
        
        if pd.isna(mom_3m):
            df.loc[i, 'regime'] = prev_regime
            continue
        
        if mom_3m >= 20:
            df.loc[i, 'regime'] = 'momentum'
        elif mom_3m <= -15:
            df.loc[i, 'regime'] = 'value'
        else:
            df.loc[i, 'regime'] = prev_regime
    
    # DEFENSIVE ALLOCATION: Check if value is outperforming
    df['allocation_mode'] = 'normal'
    
    for i in range(len(df)):
        regime = df.loc[i, 'regime']
        mom_3m = df.loc[i, 'Mom_3M_Return']
        val_3m = df.loc[i, 'Val_3M_Return']
        
        # If in momentum regime but value is outperforming → defensive 50/50
        if regime == 'momentum' and not pd.isna(mom_3m) and not pd.isna(val_3m):
            if val_3m > mom_3m:
                df.loc[i, 'allocation_mode'] = 'defensive'
    
    # Set allocations based on regime and mode
    df['w_mom'] = 0.0
    df['w_val'] = 0.0
    
    for i in range(len(df)):
        regime = df.loc[i, 'regime']
        mode = df.loc[i, 'allocation_mode']
        
        if regime == 'momentum':
            if mode == 'defensive':
                df.loc[i, 'w_mom'] = 0.5  # Defensive 50/50
                df.loc[i, 'w_val'] = 0.5
            else:
                df.loc[i, 'w_mom'] = 1.0  # Normal 100/0
                df.loc[i, 'w_val'] = 0.0
        else:  # value regime
            df.loc[i, 'w_mom'] = 0.0
            df.loc[i, 'w_val'] = 1.0
    
    # Shift weights (no lookahead)
    df['w_mom'] = df['w_mom'].shift(1).fillna(1.0)
    df['w_val'] = df['w_val'].shift(1).fillna(0.0)
    
    # Calculate returns
    df['Portfolio_Return'] = df['w_mom'] * df['Return_mom'] + df['w_val'] * df['Return_val']
    df['Portfolio_NAV'] = 100 * (1 + df['Portfolio_Return']).cumprod()
    
    return df

def calculate_metrics(df, strategy_name):
    """Calculate performance metrics"""
    valid_nav = df['Portfolio_NAV'].dropna()
    start_nav = valid_nav.iloc[0]
    end_nav = valid_nav.iloc[-1]
    years = len(df) / 12
    cagr = (end_nav / start_nav) ** (1 / years) - 1
    
    # Max Drawdown
    running_max = valid_nav.expanding().max()
    drawdown = (valid_nav - running_max) / running_max * 100
    max_dd = drawdown.min()
    
    # Total Return
    total_return = (end_nav / start_nav - 1) * 100
    
    # MAR Ratio
    mar_ratio = (cagr * 100) / abs(max_dd) if max_dd != 0 else 0
    
    # Switches
    switches = (df['regime'] != df['regime'].shift(1)).sum() - 1
    
    # Regime distribution
    regime_counts = df['regime'].value_counts()
    
    # Defensive mode usage (if applicable)
    defensive_months = 0
    if 'allocation_mode' in df.columns:
        defensive_months = (df['allocation_mode'] == 'defensive').sum()
    
    return {
        'strategy_name': strategy_name,
        'cagr': cagr * 100,
        'total_return': total_return,
        'max_dd': max_dd,
        'mar_ratio': mar_ratio,
        'switches': switches,
        'pct_momentum': regime_counts.get('momentum', 0) / len(df) * 100,
        'defensive_months': defensive_months,
        'end_nav': end_nav
    }

if __name__ == "__main__":
    print("\n" + "="*80)
    print("DEFENSIVE MOMENTUM STRATEGY TEST")
    print("="*80)
    
    print("\n📊 Running Binary 100/0 Strategy (Current)...")
    df_binary = run_binary_strategy()
    metrics_binary = calculate_metrics(df_binary, "Binary 100/0 (Current)")
    
    print("📊 Running Defensive 50/50 Strategy (New)...")
    df_defensive = run_defensive_strategy()
    metrics_defensive = calculate_metrics(df_defensive, "Defensive 50/50 (New)")
    
    # Comparison
    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON")
    print("="*80)
    
    print(f"\n{'Metric':<25} {'Binary 100/0':<15} {'Defensive 50/50':<15} {'Difference':<15}")
    print("-" * 75)
    print(f"{'CAGR':<25} {metrics_binary['cagr']:>6.2f}%        {metrics_defensive['cagr']:>6.2f}%        {metrics_defensive['cagr']-metrics_binary['cagr']:>+6.2f}%")
    print(f"{'Total Return':<25} {metrics_binary['total_return']:>6.0f}%        {metrics_defensive['total_return']:>6.0f}%        {metrics_defensive['total_return']-metrics_binary['total_return']:>+6.0f}%")
    print(f"{'Max Drawdown':<25} {metrics_binary['max_dd']:>6.2f}%       {metrics_defensive['max_dd']:>6.2f}%       {metrics_defensive['max_dd']-metrics_binary['max_dd']:>+6.2f}%")
    print(f"{'MAR Ratio':<25} {metrics_binary['mar_ratio']:>6.2f}         {metrics_defensive['mar_ratio']:>6.2f}         {metrics_defensive['mar_ratio']-metrics_binary['mar_ratio']:>+6.2f}")
    print(f"{'Switches':<25} {metrics_binary['switches']:>6.0f}          {metrics_defensive['switches']:>6.0f}          {metrics_defensive['switches']-metrics_binary['switches']:>+6.0f}")
    print(f"{'Time in Momentum':<25} {metrics_binary['pct_momentum']:>6.1f}%        {metrics_defensive['pct_momentum']:>6.1f}%        {metrics_defensive['pct_momentum']-metrics_binary['pct_momentum']:>+6.1f}%")
    print(f"{'Defensive Months':<25} {metrics_binary['defensive_months']:>6.0f}          {metrics_defensive['defensive_months']:>6.0f}          -")
    
    # Analysis
    print("\n" + "="*80)
    print("📊 DEFENSIVE MODE ANALYSIS")
    print("="*80)
    
    defensive_periods = df_defensive[df_defensive['allocation_mode'] == 'defensive'].copy()
    print(f"\nDefensive 50/50 used: {len(defensive_periods)} months ({len(defensive_periods)/len(df_defensive)*100:.1f}%)")
    
    if len(defensive_periods) > 0:
        print(f"\nFirst 10 Defensive Periods:")
        print("-" * 80)
        for idx, row in defensive_periods.head(10).iterrows():
            print(f"  {row['Date'].strftime('%Y-%m-%d')}: "
                  f"Mom 3M: {row['Mom_3M_Return']:>6.2f}%, "
                  f"Val 3M: {row['Val_3M_Return']:>6.2f}%, "
                  f"Allocation: 50/50")
    
    # Recommendation
    print("\n" + "="*80)
    print("🏆 RECOMMENDATION")
    print("="*80)
    
    cagr_diff = metrics_defensive['cagr'] - metrics_binary['cagr']
    mar_diff = metrics_defensive['mar_ratio'] - metrics_binary['mar_ratio']
    
    if cagr_diff > 0 and mar_diff > 0:
        print(f"\n✅ DEFENSIVE STRATEGY WINS!")
        print(f"   CAGR Improvement: {cagr_diff:+.2f}%")
        print(f"   MAR Improvement: {mar_diff:+.2f}")
        print(f"   Uses defensive 50/50 in {metrics_defensive['defensive_months']} months")
    elif cagr_diff > 0:
        print(f"\n⚖️  MIXED RESULTS")
        print(f"   CAGR Improvement: {cagr_diff:+.2f}%")
        print(f"   MAR Change: {mar_diff:+.2f}")
    else:
        print(f"\n❌ BINARY STRATEGY BETTER")
        print(f"   CAGR Difference: {cagr_diff:+.2f}%")
        print(f"   MAR Difference: {mar_diff:+.2f}")
        print(f"   Defensive mode adds complexity without benefit")
    
    print("\n" + "="*80)
