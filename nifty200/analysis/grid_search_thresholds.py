"""
Grid Search for Optimal Momentum Strategy Thresholds

Test all combinations of:
- Gain thresholds: 5%, 10%, 15%, 20%, 25%, 30%
- Loss thresholds: -5%, -10%, -15%, -20%, -25%, -30%
- Time periods: 1-month, 3-month
"""

import pandas as pd
import numpy as np
from pathlib import Path
import itertools

def run_strategy(gain_threshold, loss_threshold, period_months=3):
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
    
    # Apply rules
    for i in range(1, len(df)):
        mom_ret = df.loc[i, 'Mom_Return']
        prev_regime = df.loc[i-1, 'regime']
        
        if pd.isna(mom_ret):
            df.loc[i, 'regime'] = prev_regime
            continue
        
        # Rule 1: Momentum gains threshold% → 100% Momentum
        if mom_ret >= gain_threshold:
            df.loc[i, 'regime'] = 'momentum'
        
        # Rule 2: Momentum loses threshold% → 100% Value
        elif mom_ret <= loss_threshold:
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
    if len(valid_nav) == 0:
        return None
    
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
        'gain_threshold': gain_threshold,
        'loss_threshold': loss_threshold,
        'period_months': period_months,
        'cagr': cagr * 100,
        'total_return': total_return,
        'max_dd': max_dd,
        'mar_ratio': mar_ratio,
        'switches': switches,
        'avg_switch_freq': len(df) / switches if switches > 0 else 999,
        'pct_momentum': regime_counts.get('momentum', 0) / len(df) * 100,
        'end_nav': end_nav
    }

if __name__ == "__main__":
    print("\n" + "="*80)
    print("COMPREHENSIVE THRESHOLD GRID SEARCH")
    print("="*80)
    
    # Define parameter grid
    gain_thresholds = [5, 10, 15, 20, 25, 30]
    loss_thresholds = [-5, -10, -15, -20, -25, -30]
    periods = [1, 3]  # 1-month and 3-month
    
    print(f"\nTesting {len(gain_thresholds)} gain thresholds × {len(loss_thresholds)} loss thresholds × {len(periods)} periods")
    print(f"Total combinations: {len(gain_thresholds) * len(loss_thresholds) * len(periods)}")
    
    # Run grid search
    results = []
    total = len(gain_thresholds) * len(loss_thresholds) * len(periods)
    count = 0
    
    for period in periods:
        for gain in gain_thresholds:
            for loss in loss_thresholds:
                count += 1
                if count % 10 == 0:
                    print(f"  Progress: {count}/{total} ({count/total*100:.0f}%)", end='\r')
                
                result = run_strategy(gain, loss, period)
                if result:
                    results.append(result)
    
    print(f"\n  Completed: {len(results)} valid strategies tested")
    
    # Convert to DataFrame for analysis
    df_results = pd.DataFrame(results)
    
    # Find top strategies by different metrics
    print("\n" + "="*80)
    print("TOP 10 STRATEGIES BY CAGR")
    print("="*80)
    
    top_cagr = df_results.nlargest(10, 'cagr')
    
    print(f"\n{'Rank':<5} {'Period':<7} {'Gain%':<7} {'Loss%':<7} {'CAGR':<8} {'Switches':<10} {'MAR':<7} {'Mom%':<7}")
    print("-" * 80)
    
    for idx, (i, row) in enumerate(top_cagr.iterrows(), 1):
        print(f"{idx:<5} "
              f"{row['period_months']}M      "
              f"+{row['gain_threshold']:<5.0f}  "
              f"{row['loss_threshold']:<6.0f}  "
              f"{row['cagr']:>6.2f}%  "
              f"{row['switches']:>3.0f} ({row['avg_switch_freq']:>4.1f}m)  "
              f"{row['mar_ratio']:>5.2f}  "
              f"{row['pct_momentum']:>5.1f}%")
    
    # Find top by MAR ratio (risk-adjusted)
    print("\n" + "="*80)
    print("TOP 10 STRATEGIES BY MAR RATIO (Risk-Adjusted)")
    print("="*80)
    
    top_mar = df_results.nlargest(10, 'mar_ratio')
    
    print(f"\n{'Rank':<5} {'Period':<7} {'Gain%':<7} {'Loss%':<7} {'CAGR':<8} {'Switches':<10} {'MAR':<7} {'Mom%':<7}")
    print("-" * 80)
    
    for idx, (i, row) in enumerate(top_mar.iterrows(), 1):
        print(f"{idx:<5} "
              f"{row['period_months']}M      "
              f"+{row['gain_threshold']:<5.0f}  "
              f"{row['loss_threshold']:<6.0f}  "
              f"{row['cagr']:>6.2f}%  "
              f"{row['switches']:>3.0f} ({row['avg_switch_freq']:>4.1f}m)  "
              f"{row['mar_ratio']:>5.2f}  "
              f"{row['pct_momentum']:>5.1f}%")
    
    # Find strategies with fewest switches
    print("\n" + "="*80)
    print("TOP 10 STRATEGIES BY FEWEST SWITCHES (Simplicity)")
    print("="*80)
    
    top_simple = df_results.nsmallest(10, 'switches').nlargest(10, 'cagr')
    
    print(f"\n{'Rank':<5} {'Period':<7} {'Gain%':<7} {'Loss%':<7} {'CAGR':<8} {'Switches':<10} {'MAR':<7} {'Mom%':<7}")
    print("-" * 80)
    
    for idx, (i, row) in enumerate(top_simple.iterrows(), 1):
        print(f"{idx:<5} "
              f"{row['period_months']}M      "
              f"+{row['gain_threshold']:<5.0f}  "
              f"{row['loss_threshold']:<6.0f}  "
              f"{row['cagr']:>6.2f}%  "
              f"{row['switches']:>3.0f} ({row['avg_switch_freq']:>4.1f}m)  "
              f"{row['mar_ratio']:>5.2f}  "
              f"{row['pct_momentum']:>5.1f}%")
    
    # Best overall (balance of CAGR, MAR, and simplicity)
    print("\n" + "="*80)
    print("🏆 RECOMMENDED STRATEGY (Best Balance)")
    print("="*80)
    
    # Score: 50% CAGR, 30% MAR, 20% Simplicity (inverse of switches)
    df_results['cagr_score'] = (df_results['cagr'] - df_results['cagr'].min()) / (df_results['cagr'].max() - df_results['cagr'].min())
    df_results['mar_score'] = (df_results['mar_ratio'] - df_results['mar_ratio'].min()) / (df_results['mar_ratio'].max() - df_results['mar_ratio'].min())
    df_results['simple_score'] = 1 - (df_results['switches'] - df_results['switches'].min()) / (df_results['switches'].max() - df_results['switches'].min())
    
    df_results['total_score'] = (
        0.5 * df_results['cagr_score'] +
        0.3 * df_results['mar_score'] +
        0.2 * df_results['simple_score']
    )
    
    best = df_results.nlargest(1, 'total_score').iloc[0]
    
    print(f"\nPeriod:           {best['period_months']}-month")
    print(f"Gain Threshold:   +{best['gain_threshold']:.0f}%")
    print(f"Loss Threshold:   {best['loss_threshold']:.0f}%")
    print(f"\nPerformance:")
    print(f"  CAGR:           {best['cagr']:.2f}%")
    print(f"  Total Return:   {best['total_return']:.2f}%")
    print(f"  Max Drawdown:   {best['max_dd']:.2f}%")
    print(f"  MAR Ratio:      {best['mar_ratio']:.2f}")
    print(f"\nTrading:")
    print(f"  Switches:       {best['switches']:.0f} (every {best['avg_switch_freq']:.1f} months)")
    print(f"  Time in Mom:    {best['pct_momentum']:.1f}%")
    
    # Compare with original 20/20 strategy
    original = df_results[(df_results['gain_threshold'] == 20) & 
                          (df_results['loss_threshold'] == -20) & 
                          (df_results['period_months'] == 3)].iloc[0]
    
    print("\n" + "="*80)
    print("📊 COMPARISON WITH ORIGINAL (20% / -20% / 3M)")
    print("="*80)
    
    print(f"\n{'Metric':<20} {'Original':<15} {'Best':<15} {'Improvement':<15}")
    print("-" * 65)
    print(f"{'CAGR':<20} {original['cagr']:>6.2f}%        {best['cagr']:>6.2f}%        {best['cagr']-original['cagr']:>+6.2f}%")
    print(f"{'MAR Ratio':<20} {original['mar_ratio']:>6.2f}         {best['mar_ratio']:>6.2f}         {best['mar_ratio']-original['mar_ratio']:>+6.2f}")
    print(f"{'Switches':<20} {original['switches']:>6.0f}          {best['switches']:>6.0f}          {best['switches']-original['switches']:>+6.0f}")
    print(f"{'Max Drawdown':<20} {original['max_dd']:>6.2f}%       {best['max_dd']:>6.2f}%       {best['max_dd']-original['max_dd']:>+6.2f}%")
    
    if best['cagr'] > original['cagr']:
        improvement = best['cagr'] - original['cagr']
        print(f"\n✅ Best strategy IMPROVES CAGR by {improvement:.2f}%!")
    else:
        print(f"\n✅ Original strategy remains optimal!")
    
    # Save results to CSV
    output_file = Path(__file__).parent.parent / "output" / "monthly" / "threshold_grid_search_results.csv"
    df_results.to_csv(output_file, index=False)
    print(f"\n💾 Full results saved to: {output_file}")
    
    print("\n" + "="*80)
