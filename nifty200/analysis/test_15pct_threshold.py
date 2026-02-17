"""
Test Simple Momentum Strategy with 15% gain threshold

Compare:
- Original: 20% gain / 20% loss
- New: 15% gain / 20% loss (more aggressive momentum entry)
"""

import pandas as pd
import numpy as np
from pathlib import Path

def run_strategy(gain_threshold=20, loss_threshold=-20, strategy_name="Simple Momentum"):
    """Run Simple Momentum Strategy with custom thresholds"""
    
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
    
    # Calculate 3-month momentum return
    df['Mom_3M_Return'] = df['Close_mom'].pct_change(3) * 100
    
    # Initialize regime
    df['regime'] = 'momentum'
    
    # Apply rules
    for i in range(1, len(df)):
        mom_3m = df.loc[i, 'Mom_3M_Return']
        prev_regime = df.loc[i-1, 'regime']
        
        if pd.isna(mom_3m):
            df.loc[i, 'regime'] = prev_regime
            continue
        
        # Rule 1: Momentum gains threshold% in 3 months → 100% Momentum
        if mom_3m >= gain_threshold:
            df.loc[i, 'regime'] = 'momentum'
        
        # Rule 2: Momentum loses 20% in 3 months → 100% Value
        elif mom_3m <= loss_threshold:
            df.loc[i, 'regime'] = 'value'
        
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
    
    # Regime distribution
    regime_counts = df['regime'].value_counts()
    
    return {
        'strategy_name': strategy_name,
        'gain_threshold': gain_threshold,
        'loss_threshold': loss_threshold,
        'cagr': cagr * 100,
        'total_return': total_return,
        'max_dd': max_dd,
        'mar_ratio': mar_ratio,
        'switches': switches,
        'avg_switch_freq': len(df) / switches if switches > 0 else 0,
        'momentum_months': regime_counts.get('momentum', 0),
        'value_months': regime_counts.get('value', 0),
        'pct_momentum': regime_counts.get('momentum', 0) / len(df) * 100,
        'end_nav': end_nav
    }

if __name__ == "__main__":
    print("\n" + "="*80)
    print("TESTING MOMENTUM GAIN THRESHOLD SENSITIVITY")
    print("="*80)
    
    # Test different gain thresholds
    results = []
    
    # Original: 20% gain / 20% loss
    print("\n📊 Testing: 20% gain / 20% loss (Original)")
    r1 = run_strategy(gain_threshold=20, loss_threshold=-20, strategy_name="20/20 (Original)")
    results.append(r1)
    
    # New: 15% gain / 20% loss
    print("📊 Testing: 15% gain / 20% loss (More Aggressive)")
    r2 = run_strategy(gain_threshold=15, loss_threshold=-20, strategy_name="15/20 (Aggressive)")
    results.append(r2)
    
    # Even more aggressive: 10% gain / 20% loss
    print("📊 Testing: 10% gain / 20% loss (Very Aggressive)")
    r3 = run_strategy(gain_threshold=10, loss_threshold=-20, strategy_name="10/20 (Very Aggressive)")
    results.append(r3)
    
    # Conservative: 25% gain / 20% loss
    print("📊 Testing: 25% gain / 20% loss (Conservative)")
    r4 = run_strategy(gain_threshold=25, loss_threshold=-20, strategy_name="25/20 (Conservative)")
    results.append(r4)
    
    # Create comparison table
    print("\n" + "="*80)
    print("THRESHOLD SENSITIVITY ANALYSIS - NIFTY 200")
    print("="*80)
    
    print(f"\n{'Strategy':<25} {'CAGR':<8} {'Switches':<10} {'MAR':<8} {'Momentum%':<12} {'Total Ret%':<12}")
    print("-" * 80)
    
    for r in results:
        print(f"{r['strategy_name']:<25} "
              f"{r['cagr']:>6.2f}%  "
              f"{r['switches']:>3d} ({r['avg_switch_freq']:>4.1f}m)  "
              f"{r['mar_ratio']:>6.2f}  "
              f"{r['pct_momentum']:>6.1f}%      "
              f"{r['total_return']:>8.1f}%")
    
    # Find best by CAGR
    best = max(results, key=lambda x: x['cagr'])
    
    print("\n" + "="*80)
    print("🏆 BEST STRATEGY BY CAGR")
    print("="*80)
    print(f"\nStrategy: {best['strategy_name']}")
    print(f"  CAGR:              {best['cagr']:.2f}%")
    print(f"  Total Return:      {best['total_return']:.2f}%")
    print(f"  Switches:          {best['switches']} (every {best['avg_switch_freq']:.1f} months)")
    print(f"  MAR Ratio:         {best['mar_ratio']:.2f}")
    print(f"  Max Drawdown:      {best['max_dd']:.2f}%")
    print(f"  Time in Momentum:  {best['pct_momentum']:.1f}%")
    
    # Analysis
    print("\n" + "="*80)
    print("📊 KEY INSIGHTS")
    print("="*80)
    
    original = results[0]
    aggressive = results[1]
    
    cagr_diff = aggressive['cagr'] - original['cagr']
    switch_diff = aggressive['switches'] - original['switches']
    
    print(f"\n15% vs 20% Gain Threshold:")
    print(f"  CAGR Change:       {cagr_diff:+.2f}% ({'+better' if cagr_diff > 0 else 'worse'})")
    print(f"  Switch Change:     {switch_diff:+d} switches ({'+more' if switch_diff > 0 else 'fewer'})")
    print(f"  MAR Change:        {aggressive['mar_ratio'] - original['mar_ratio']:+.2f}")
    
    if cagr_diff > 0:
        print(f"\n✅ 15% threshold IMPROVES returns by {cagr_diff:.2f}%")
    else:
        print(f"\n❌ 15% threshold REDUCES returns by {abs(cagr_diff):.2f}%")
    
    if switch_diff > 0:
        print(f"⚠️  But increases switches by {switch_diff} ({switch_diff/original['switches']*100:.1f}% more)")
    else:
        print(f"✅ And reduces switches by {abs(switch_diff)} ({abs(switch_diff)/original['switches']*100:.1f}% fewer)")
    
    print("\n" + "="*80)
