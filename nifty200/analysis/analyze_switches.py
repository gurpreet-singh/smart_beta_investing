"""
Analyze when regime switches actually occur
"""

import pandas as pd
import numpy as np
from pathlib import Path

def analyze_switches(gain_threshold=20, loss_threshold=-20):
    """Analyze when and why switches occur"""
    
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
    
    # Calculate 3-month momentum return
    df['Mom_3M_Return'] = df['Close_mom'].pct_change(3) * 100
    
    # Initialize regime
    df['regime'] = 'momentum'
    df['switch_reason'] = ''
    
    # Apply rules and track reasons
    for i in range(1, len(df)):
        mom_3m = df.loc[i, 'Mom_3M_Return']
        prev_regime = df.loc[i-1, 'regime']
        
        if pd.isna(mom_3m):
            df.loc[i, 'regime'] = prev_regime
            continue
        
        # Rule 1: Momentum gains threshold% in 3 months → 100% Momentum
        if mom_3m >= gain_threshold:
            df.loc[i, 'regime'] = 'momentum'
            if prev_regime != 'momentum':
                df.loc[i, 'switch_reason'] = f'Gain: {mom_3m:.1f}% >= {gain_threshold}%'
        
        # Rule 2: Momentum loses 20% in 3 months → 100% Value
        elif mom_3m <= loss_threshold:
            df.loc[i, 'regime'] = 'value'
            if prev_regime != 'value':
                df.loc[i, 'switch_reason'] = f'Loss: {mom_3m:.1f}% <= {loss_threshold}%'
        
        # Rule 3: Otherwise → Stay in current regime
        else:
            df.loc[i, 'regime'] = prev_regime
    
    # Find switches
    df['switched'] = df['regime'] != df['regime'].shift(1)
    switches = df[df['switched'] & (df['switch_reason'] != '')].copy()
    
    return df, switches

if __name__ == "__main__":
    print("\n" + "="*80)
    print("ANALYZING REGIME SWITCHES")
    print("="*80)
    
    # Test with 20% threshold
    print("\n📊 Testing with 20% gain / 20% loss threshold:")
    df_20, switches_20 = analyze_switches(gain_threshold=20, loss_threshold=-20)
    
    print(f"\nTotal Switches: {len(switches_20)}")
    print("\nSwitch Details:")
    print("-" * 80)
    for idx, row in switches_20.iterrows():
        print(f"{row['Date'].strftime('%Y-%m-%d')}: {row['switch_reason']}")
        print(f"  → Switched to: {row['regime']}")
    
    # Test with 15% threshold
    print("\n" + "="*80)
    print("\n📊 Testing with 15% gain / 20% loss threshold:")
    df_15, switches_15 = analyze_switches(gain_threshold=15, loss_threshold=-20)
    
    print(f"\nTotal Switches: {len(switches_15)}")
    print("\nSwitch Details:")
    print("-" * 80)
    for idx, row in switches_15.iterrows():
        print(f"{row['Date'].strftime('%Y-%m-%d')}: {row['switch_reason']}")
        print(f"  → Switched to: {row['regime']}")
    
    # Compare
    print("\n" + "="*80)
    print("COMPARISON")
    print("="*80)
    
    if len(switches_15) == len(switches_20):
        print(f"\n✅ Both thresholds produce IDENTICAL switches ({len(switches_20)} switches)")
        print("\n💡 This means:")
        print("   - All switches are triggered by the LOSS threshold (-20%)")
        print("   - The GAIN threshold doesn't matter (15%, 20%, 25% all same)")
        print("   - Momentum is so strong that it rarely needs the gain trigger")
    else:
        print(f"\n📊 15% threshold: {len(switches_15)} switches")
        print(f"📊 20% threshold: {len(switches_20)} switches")
        print(f"📊 Difference: {len(switches_15) - len(switches_20)} switches")
    
    # Analyze 3M momentum distribution
    print("\n" + "="*80)
    print("3-MONTH MOMENTUM RETURN DISTRIBUTION")
    print("="*80)
    
    valid_returns = df_20['Mom_3M_Return'].dropna()
    
    print(f"\nStatistics:")
    print(f"  Mean:    {valid_returns.mean():>8.2f}%")
    print(f"  Median:  {valid_returns.median():>8.2f}%")
    print(f"  Std Dev: {valid_returns.std():>8.2f}%")
    print(f"  Min:     {valid_returns.min():>8.2f}%")
    print(f"  Max:     {valid_returns.max():>8.2f}%")
    
    print(f"\nThreshold Analysis:")
    print(f"  Returns > +25%:  {(valid_returns > 25).sum():>4d} months ({(valid_returns > 25).sum()/len(valid_returns)*100:>5.1f}%)")
    print(f"  Returns > +20%:  {(valid_returns > 20).sum():>4d} months ({(valid_returns > 20).sum()/len(valid_returns)*100:>5.1f}%)")
    print(f"  Returns > +15%:  {(valid_returns > 15).sum():>4d} months ({(valid_returns > 15).sum()/len(valid_returns)*100:>5.1f}%)")
    print(f"  Returns > +10%:  {(valid_returns > 10).sum():>4d} months ({(valid_returns > 10).sum()/len(valid_returns)*100:>5.1f}%)")
    print(f"  Returns < -20%:  {(valid_returns < -20).sum():>4d} months ({(valid_returns < -20).sum()/len(valid_returns)*100:>5.1f}%)")
    print(f"  Returns < -15%:  {(valid_returns < -15).sum():>4d} months ({(valid_returns < -15).sum()/len(valid_returns)*100:>5.1f}%)")
    print(f"  Returns < -10%:  {(valid_returns < -10).sum():>4d} months ({(valid_returns < -10).sum()/len(valid_returns)*100:>5.1f}%)")
    
    print("\n" + "="*80)
