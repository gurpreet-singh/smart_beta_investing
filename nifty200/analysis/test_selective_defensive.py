"""
Alternative: Defensive strategy only when momentum is WEAK

Instead of checking if value > momentum in 3M returns,
only go defensive when:
1. In momentum regime
2. Momentum 3M return is NEGATIVE (weak momentum)
3. Value 3M return is POSITIVE (strong value)

This is more selective and only protects during momentum weakness.
"""

import pandas as pd
import numpy as np
from pathlib import Path

def run_selective_defensive_strategy():
    """Defensive 50/50 only when momentum is weak (negative) and value is strong (positive)"""
    
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
    
    # Regime detection
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
    
    # SELECTIVE DEFENSIVE: Only when momentum is weak AND value is strong
    df['allocation_mode'] = 'normal'
    
    for i in range(len(df)):
        regime = df.loc[i, 'regime']
        mom_3m = df.loc[i, 'Mom_3M_Return']
        val_3m = df.loc[i, 'Val_3M_Return']
        
        # Defensive only if: momentum regime + momentum negative + value positive
        if regime == 'momentum' and not pd.isna(mom_3m) and not pd.isna(val_3m):
            if mom_3m < 0 and val_3m > 0:
                df.loc[i, 'allocation_mode'] = 'defensive'
    
    # Set allocations
    df['w_mom'] = 0.0
    df['w_val'] = 0.0
    
    for i in range(len(df)):
        regime = df.loc[i, 'regime']
        mode = df.loc[i, 'allocation_mode']
        
        if regime == 'momentum':
            if mode == 'defensive':
                df.loc[i, 'w_mom'] = 0.5
                df.loc[i, 'w_val'] = 0.5
            else:
                df.loc[i, 'w_mom'] = 1.0
                df.loc[i, 'w_val'] = 0.0
        else:
            df.loc[i, 'w_mom'] = 0.0
            df.loc[i, 'w_val'] = 1.0
    
    # Shift weights
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
    
    running_max = valid_nav.expanding().max()
    drawdown = (valid_nav - running_max) / running_max * 100
    max_dd = drawdown.min()
    
    total_return = (end_nav / start_nav - 1) * 100
    mar_ratio = (cagr * 100) / abs(max_dd) if max_dd != 0 else 0
    switches = (df['regime'] != df['regime'].shift(1)).sum() - 1
    regime_counts = df['regime'].value_counts()
    
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
    print("SELECTIVE DEFENSIVE MOMENTUM STRATEGY")
    print("="*80)
    print("\nDefensive 50/50 ONLY when:")
    print("  - In momentum regime")
    print("  - Momentum 3M return < 0% (weak)")
    print("  - Value 3M return > 0% (strong)")
    
    # Load binary for comparison
    from test_defensive_momentum import run_binary_strategy
    
    print("\n📊 Running Binary 100/0 Strategy...")
    df_binary = run_binary_strategy()
    metrics_binary = calculate_metrics(df_binary, "Binary 100/0")
    
    print("📊 Running Selective Defensive Strategy...")
    df_selective = run_selective_defensive_strategy()
    metrics_selective = calculate_metrics(df_selective, "Selective Defensive")
    
    # Comparison
    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON")
    print("="*80)
    
    print(f"\n{'Metric':<25} {'Binary 100/0':<15} {'Selective Def':<15} {'Difference':<15}")
    print("-" * 75)
    print(f"{'CAGR':<25} {metrics_binary['cagr']:>6.2f}%        {metrics_selective['cagr']:>6.2f}%        {metrics_selective['cagr']-metrics_binary['cagr']:>+6.2f}%")
    print(f"{'Total Return':<25} {metrics_binary['total_return']:>6.0f}%        {metrics_selective['total_return']:>6.0f}%        {metrics_selective['total_return']-metrics_binary['total_return']:>+6.0f}%")
    print(f"{'Max Drawdown':<25} {metrics_binary['max_dd']:>6.2f}%       {metrics_selective['max_dd']:>6.2f}%       {metrics_selective['max_dd']-metrics_binary['max_dd']:>+6.2f}%")
    print(f"{'MAR Ratio':<25} {metrics_binary['mar_ratio']:>6.2f}         {metrics_selective['mar_ratio']:>6.2f}         {metrics_selective['mar_ratio']-metrics_binary['mar_ratio']:>+6.2f}")
    print(f"{'Defensive Months':<25} {metrics_binary['defensive_months']:>6.0f}          {metrics_selective['defensive_months']:>6.0f}          -")
    
    # Analysis
    print("\n" + "="*80)
    print("📊 SELECTIVE DEFENSIVE ANALYSIS")
    print("="*80)
    
    defensive_periods = df_selective[df_selective['allocation_mode'] == 'defensive'].copy()
    print(f"\nSelective Defensive used: {len(defensive_periods)} months ({len(defensive_periods)/len(df_selective)*100:.1f}%)")
    
    if len(defensive_periods) > 0:
        print(f"\nAll Selective Defensive Periods:")
        print("-" * 80)
        for idx, row in defensive_periods.iterrows():
            print(f"  {row['Date'].strftime('%Y-%m-%d')}: "
                  f"Mom 3M: {row['Mom_3M_Return']:>6.2f}%, "
                  f"Val 3M: {row['Val_3M_Return']:>6.2f}%, "
                  f"Allocation: 50/50")
    
    # Recommendation
    print("\n" + "="*80)
    print("🏆 RECOMMENDATION")
    print("="*80)
    
    cagr_diff = metrics_selective['cagr'] - metrics_binary['cagr']
    
    if cagr_diff > 0:
        print(f"\n✅ SELECTIVE DEFENSIVE WINS!")
        print(f"   CAGR Improvement: {cagr_diff:+.2f}%")
        print(f"   Only uses defensive mode {metrics_selective['defensive_months']} times")
    else:
        print(f"\n❌ BINARY STRATEGY STILL BETTER")
        print(f"   CAGR Difference: {cagr_diff:+.2f}%")
        print(f"\n💡 CONCLUSION:")
        print(f"   The binary 100/0 strategy is optimal.")
        print(f"   Adding defensive 50/50 allocation reduces returns.")
        print(f"   Momentum's strength is in full commitment - not hedging.")
    
    print("\n" + "="*80)
