"""
Compare 1-Month vs 3-Month Strategies

Compare:
1. 3M 20%/-15% (Best from grid search)
2. 1M 10%/-10% (User suggested - more reactive)
"""

import pandas as pd
import numpy as np
from pathlib import Path

def run_strategy(gain_threshold, loss_threshold, period_months, strategy_name):
    """Run Simple Momentum Strategy with custom thresholds and period"""
    
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
    
    # Calculate momentum return over specified period
    df['Mom_Return'] = df['Close_mom'].pct_change(period_months) * 100
    
    # Initialize regime
    df['regime'] = 'momentum'
    df['switch_reason'] = ''
    
    # Apply rules and track switches
    for i in range(1, len(df)):
        mom_ret = df.loc[i, 'Mom_Return']
        prev_regime = df.loc[i-1, 'regime']
        
        if pd.isna(mom_ret):
            df.loc[i, 'regime'] = prev_regime
            continue
        
        # Rule 1: Momentum gains threshold% → 100% Momentum
        if mom_ret >= gain_threshold:
            df.loc[i, 'regime'] = 'momentum'
            if prev_regime != 'momentum':
                df.loc[i, 'switch_reason'] = f'Gain: {mom_ret:.1f}% >= {gain_threshold}%'
        
        # Rule 2: Momentum loses threshold% → 100% Value
        elif mom_ret <= loss_threshold:
            df.loc[i, 'regime'] = 'value'
            if prev_regime != 'value':
                df.loc[i, 'switch_reason'] = f'Loss: {mom_ret:.1f}% <= {loss_threshold}%'
        
        # Rule 3: Otherwise → Stay in current regime
        else:
            df.loc[i, 'regime'] = prev_regime
    
    # Binary allocation
    df['w_mom'] = np.where(df['regime'] == 'momentum', 1.0, 0.0)
    df['w_val'] = 1.0 - df['w_mom']
    
    # Shift weights (no lookahead bias)
    df['w_mom'] = df['w_mom'].shift(1).fillna(1.0)
    df['w_val'] = df['w_val'].shift(1).fillna(0.0)
    
    # Calculate portfolio returns
    df['Portfolio_Return'] = df['w_mom'] * df['Return_mom'] + df['w_val'] * df['Return_val']
    df['Portfolio_NAV'] = 100 * (1 + df['Portfolio_Return']).cumprod()
    
    # Calculate metrics
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
    
    # Count switches
    switches = (df['regime'] != df['regime'].shift(1)).sum() - 1
    switch_details = df[df['switch_reason'] != ''][['Date', 'regime', 'switch_reason', 'Mom_Return']].copy()
    
    # Regime distribution
    regime_counts = df['regime'].value_counts()
    
    return {
        'strategy_name': strategy_name,
        'cagr': cagr * 100,
        'total_return': total_return,
        'max_dd': max_dd,
        'mar_ratio': mar_ratio,
        'switches': switches,
        'avg_switch_freq': len(df) / switches if switches > 0 else 999,
        'pct_momentum': regime_counts.get('momentum', 0) / len(df) * 100,
        'end_nav': end_nav
    }, df, switch_details

if __name__ == "__main__":
    print("\n" + "="*80)
    print("STRATEGY COMPARISON: 3-MONTH vs 1-MONTH")
    print("="*80)
    
    # Strategy 1: 3M 20%/-15% (Best from grid search)
    print("\n📊 Running: 3-Month 20%/-15% (Grid Search Winner)")
    r1, df1, switches1 = run_strategy(
        gain_threshold=20,
        loss_threshold=-15,
        period_months=3,
        strategy_name="3M 20%/-15% (Winner)"
    )
    
    # Strategy 2: 1M 10%/-10% (User suggested)
    print("📊 Running: 1-Month 10%/-10% (Reactive)")
    r2, df2, switches2 = run_strategy(
        gain_threshold=10,
        loss_threshold=-10,
        period_months=1,
        strategy_name="1M 10%/-10% (Reactive)"
    )
    
    # Strategy 3: Original 3M 20%/-20%
    print("📊 Running: 3-Month 20%/-20% (Original)")
    r3, df3, switches3 = run_strategy(
        gain_threshold=20,
        loss_threshold=-20,
        period_months=3,
        strategy_name="3M 20%/-20% (Original)"
    )
    
    # Comparison Table
    print("\n" + "="*80)
    print("PERFORMANCE COMPARISON")
    print("="*80)
    
    results = [r1, r2, r3]
    
    print(f"\n{'Strategy':<25} {'CAGR':<10} {'Switches':<12} {'MAR':<8} {'Mom%':<8} {'Max DD':<10}")
    print("-" * 80)
    
    for r in results:
        print(f"{r['strategy_name']:<25} "
              f"{r['cagr']:>6.2f}%   "
              f"{r['switches']:>3.0f} ({r['avg_switch_freq']:>4.1f}m)  "
              f"{r['mar_ratio']:>6.2f}  "
              f"{r['pct_momentum']:>6.1f}%  "
              f"{r['max_dd']:>7.2f}%")
    
    # Detailed comparison
    print("\n" + "="*80)
    print("DETAILED METRICS")
    print("="*80)
    
    print(f"\n{'Metric':<25} {'3M 20/-15':<15} {'1M 10/-10':<15} {'3M 20/-20':<15}")
    print("-" * 70)
    print(f"{'CAGR':<25} {r1['cagr']:>6.2f}%        {r2['cagr']:>6.2f}%        {r3['cagr']:>6.2f}%")
    print(f"{'Total Return':<25} {r1['total_return']:>6.0f}%        {r2['total_return']:>6.0f}%        {r3['total_return']:>6.0f}%")
    print(f"{'Max Drawdown':<25} {r1['max_dd']:>6.2f}%       {r2['max_dd']:>6.2f}%       {r3['max_dd']:>6.2f}%")
    print(f"{'MAR Ratio':<25} {r1['mar_ratio']:>6.2f}         {r2['mar_ratio']:>6.2f}         {r3['mar_ratio']:>6.2f}")
    print(f"{'Switches':<25} {r1['switches']:>6.0f}          {r2['switches']:>6.0f}          {r3['switches']:>6.0f}")
    print(f"{'Avg Switch Freq':<25} {r1['avg_switch_freq']:>6.1f}m        {r2['avg_switch_freq']:>6.1f}m        {r3['avg_switch_freq']:>6.1f}m")
    print(f"{'Time in Momentum':<25} {r1['pct_momentum']:>6.1f}%        {r2['pct_momentum']:>6.1f}%        {r3['pct_momentum']:>6.1f}%")
    
    # Find best
    best = max(results, key=lambda x: x['cagr'])
    
    print("\n" + "="*80)
    print("🏆 WINNER BY CAGR")
    print("="*80)
    print(f"\nStrategy: {best['strategy_name']}")
    print(f"  CAGR:              {best['cagr']:.2f}%")
    print(f"  Total Return:      {best['total_return']:.2f}%")
    print(f"  Max Drawdown:      {best['max_dd']:.2f}%")
    print(f"  MAR Ratio:         {best['mar_ratio']:.2f}")
    print(f"  Switches:          {best['switches']:.0f} (every {best['avg_switch_freq']:.1f} months)")
    print(f"  Time in Momentum:  {best['pct_momentum']:.1f}%")
    
    # Switch analysis
    print("\n" + "="*80)
    print("SWITCH ANALYSIS: 1M 10%/-10% vs 3M 20%/-15%")
    print("="*80)
    
    print(f"\n1-Month 10%/-10% Strategy:")
    print(f"  Total Switches: {len(switches2)}")
    print("\n  Switch Details:")
    for idx, row in switches2.head(10).iterrows():
        print(f"    {row['Date'].strftime('%Y-%m-%d')}: {row['switch_reason']} → {row['regime']}")
    if len(switches2) > 10:
        print(f"    ... and {len(switches2) - 10} more switches")
    
    print(f"\n3-Month 20%/-15% Strategy:")
    print(f"  Total Switches: {len(switches1)}")
    print("\n  Switch Details:")
    for idx, row in switches1.iterrows():
        print(f"    {row['Date'].strftime('%Y-%m-%d')}: {row['switch_reason']} → {row['regime']}")
    
    # Recommendation
    print("\n" + "="*80)
    print("📊 RECOMMENDATION")
    print("="*80)
    
    cagr_diff_1m = r2['cagr'] - r1['cagr']
    switch_diff_1m = r2['switches'] - r1['switches']
    
    print(f"\n1M 10%/-10% vs 3M 20%/-15%:")
    print(f"  CAGR Difference:     {cagr_diff_1m:+.2f}%")
    print(f"  Switch Difference:   {switch_diff_1m:+.0f} switches")
    print(f"  MAR Difference:      {r2['mar_ratio'] - r1['mar_ratio']:+.2f}")
    
    if r1['cagr'] > r2['cagr']:
        print(f"\n✅ RECOMMENDED: 3M 20%/-15%")
        print(f"   Reason: {r1['cagr'] - r2['cagr']:.2f}% higher CAGR with {r1['switches'] - r2['switches']:.0f} fewer switches")
    else:
        print(f"\n✅ RECOMMENDED: 1M 10%/-10%")
        print(f"   Reason: {r2['cagr'] - r1['cagr']:.2f}% higher CAGR")
    
    print("\n" + "="*80)
