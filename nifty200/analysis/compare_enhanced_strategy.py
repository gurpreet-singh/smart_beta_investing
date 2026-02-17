"""
Compare Enhanced Trend-Following Strategy with Previous Strategies
Shows the impact of hysteresis and confirmed reversals
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set plotting style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

# Paths
output_folder = Path(__file__).parent.parent / "output" / "monthly"

print("\n" + "="*100)
print("STRATEGY COMPARISON: ENHANCED TREND-FOLLOWING vs PREVIOUS STRATEGIES")
print("="*100)

# Load all strategy results
print("\n📂 Loading strategy data...")

# Enhanced Trend-Following (NEW)
enhanced_file = output_folder / "portfolio_ratio_trend_75_25.csv"
enhanced_df = pd.read_csv(enhanced_file, parse_dates=['Date'])

# Regime Switching (from previous analysis)
regime_file = output_folder / "portfolio_regime_switching.csv"
if regime_file.exists():
    regime_df = pd.read_csv(regime_file, parse_dates=['Date'])
    has_regime = True
else:
    has_regime = False
    print("⚠️  Regime switching data not found")

# Baselines
mom_file = output_folder / "nifty200_momentum_30_monthly.csv"
val_file = output_folder / "nifty200_value_30_monthly.csv"

mom_df = pd.read_csv(mom_file, parse_dates=['Date'])
val_df = pd.read_csv(val_file, parse_dates=['Date'])

print("✅ Data loaded")

# Calculate performance metrics
def calculate_metrics(df, return_col='Portfolio_Return'):
    """Calculate performance metrics"""
    # Check if return column exists, if not calculate from Close
    if return_col not in df.columns:
        if 'Close' in df.columns:
            returns = df['Close'].pct_change()
            returns = returns.fillna(0)
        else:
            raise ValueError(f"Neither '{return_col}' nor 'Close' column found in dataframe")
    else:
        returns = df[return_col]
        # Check if returns are in percentage form (values > 1) or decimal form (values < 1)
        # If max absolute value is < 1, assume decimal form
        if returns.abs().max() < 1:
            # Already in decimal form, no conversion needed
            pass
        else:
            # In percentage form, convert to decimal
            returns = returns / 100
    
    # CAGR
    start_nav = 100
    end_nav = start_nav * (1 + returns).prod()
    years = len(df) / 12
    cagr = (end_nav / start_nav) ** (1 / years) - 1
    
    # Max Drawdown
    nav = start_nav * (1 + returns).cumprod()
    running_max = nav.expanding().max()
    drawdown = (nav - running_max) / running_max * 100
    max_dd = drawdown.min()
    
    # Total Return
    total_return = (end_nav / start_nav - 1) * 100
    
    # MAR Ratio
    mar_ratio = (cagr * 100) / abs(max_dd) if max_dd != 0 else 0
    
    return {
        'CAGR': cagr * 100,
        'Total_Return': total_return,
        'Max_DD': max_dd,
        'MAR_Ratio': mar_ratio,
        'End_NAV': end_nav
    }

# Calculate metrics for all strategies
print("\n📊 Calculating performance metrics...")

enhanced_metrics = calculate_metrics(enhanced_df)

if has_regime:
    regime_metrics = calculate_metrics(regime_df)

mom_metrics = calculate_metrics(mom_df)
val_metrics = calculate_metrics(val_df)

# Count switches
enhanced_switches = (enhanced_df['regime'] != enhanced_df['regime'].shift(1)).sum() - 1

if has_regime:
    regime_switches = (regime_df['regime'] != regime_df['regime'].shift(1)).sum() - 1

# Regime distribution
enhanced_regime_dist = enhanced_df['regime'].value_counts()
if has_regime:
    regime_regime_dist = regime_df['regime'].value_counts()

# Print comparison
print("\n" + "="*100)
print("PERFORMANCE COMPARISON")
print("="*100)

print(f"\n{'Metric':<25} {'Enhanced TF':<15} {'Regime Switch':<15} {'Pure Mom':<15} {'Pure Val':<15}")
print("-" * 100)

print(f"{'CAGR':<25} {enhanced_metrics['CAGR']:>14.2f}% ", end="")
if has_regime:
    print(f"{regime_metrics['CAGR']:>14.2f}% ", end="")
else:
    print(f"{'N/A':>15} ", end="")
print(f"{mom_metrics['CAGR']:>14.2f}% {val_metrics['CAGR']:>14.2f}%")

print(f"{'Total Return':<25} {enhanced_metrics['Total_Return']:>14.2f}% ", end="")
if has_regime:
    print(f"{regime_metrics['Total_Return']:>14.2f}% ", end="")
else:
    print(f"{'N/A':>15} ", end="")
print(f"{mom_metrics['Total_Return']:>14.2f}% {val_metrics['Total_Return']:>14.2f}%")

print(f"{'Max Drawdown':<25} {enhanced_metrics['Max_DD']:>14.2f}% ", end="")
if has_regime:
    print(f"{regime_metrics['Max_DD']:>14.2f}% ", end="")
else:
    print(f"{'N/A':>15} ", end="")
print(f"{mom_metrics['Max_DD']:>14.2f}% {val_metrics['Max_DD']:>14.2f}%")

print(f"{'MAR Ratio':<25} {enhanced_metrics['MAR_Ratio']:>14.2f}  ", end="")
if has_regime:
    print(f"{regime_metrics['MAR_Ratio']:>14.2f}  ", end="")
else:
    print(f"{'N/A':>15} ", end="")
print(f"{mom_metrics['MAR_Ratio']:>14.2f}  {val_metrics['MAR_Ratio']:>14.2f}")

print(f"{'Number of Switches':<25} {enhanced_switches:>14}  ", end="")
if has_regime:
    print(f"{regime_switches:>14}  ", end="")
else:
    print(f"{'N/A':>15} ", end="")
print(f"{'N/A':>15} {'N/A':>15}")

print("\n" + "="*100)
print("REGIME DISTRIBUTION")
print("="*100)

print(f"\n{'Regime':<20} {'Enhanced TF':<20} {'Regime Switch':<20}")
print("-" * 60)

for regime in ['momentum', 'value']:
    enhanced_count = enhanced_regime_dist.get(regime, 0)
    enhanced_pct = enhanced_count / len(enhanced_df) * 100
    
    print(f"{regime.capitalize():<20} {enhanced_count:>3} ({enhanced_pct:>5.1f}%)       ", end="")
    
    if has_regime:
        regime_count = regime_regime_dist.get(regime, 0)
        regime_pct = regime_count / len(regime_df) * 100
        print(f"{regime_count:>3} ({regime_pct:>5.1f}%)")
    else:
        print("N/A")

# Average allocations
print("\n" + "="*100)
print("AVERAGE ALLOCATIONS")
print("="*100)

print(f"\n{'Strategy':<30} {'Avg Momentum':<15} {'Avg Value':<15}")
print("-" * 60)

enhanced_avg_mom = enhanced_df['w_mom'].mean() * 100
enhanced_avg_val = enhanced_df['w_val'].mean() * 100

print(f"{'Enhanced Trend-Following':<30} {enhanced_avg_mom:>14.1f}% {enhanced_avg_val:>14.1f}%")

if has_regime:
    regime_avg_mom = regime_df['w_mom'].mean() * 100
    regime_avg_val = regime_df['w_val'].mean() * 100
    print(f"{'Regime Switching':<30} {regime_avg_mom:>14.1f}% {regime_avg_val:>14.1f}%")

# Key insights
print("\n" + "="*100)
print("KEY INSIGHTS")
print("="*100)

print("\n✅ Enhanced Trend-Following Strategy:")
print(f"   • CAGR: {enhanced_metrics['CAGR']:.2f}%")
print(f"   • Switches: {enhanced_switches} (every {len(enhanced_df)/enhanced_switches:.1f} months)")
print(f"   • Avg Momentum allocation: {enhanced_avg_mom:.1f}%")
print(f"   • Regime distribution: {enhanced_regime_dist.get('momentum', 0)} momentum / {enhanced_regime_dist.get('value', 0)} value")

if has_regime:
    print(f"\n📊 Comparison with Regime Switching:")
    cagr_diff = enhanced_metrics['CAGR'] - regime_metrics['CAGR']
    switch_diff = enhanced_switches - regime_switches
    
    print(f"   • CAGR difference: {cagr_diff:+.2f}%")
    print(f"   • Switch difference: {switch_diff:+d} ({switch_diff/regime_switches*100:+.1f}%)")
    
    if cagr_diff > 0:
        print(f"   ✅ Enhanced TF outperforms by {cagr_diff:.2f}%")
    else:
        print(f"   ⚠️  Enhanced TF underperforms by {abs(cagr_diff):.2f}%")
    
    if switch_diff < 0:
        print(f"   ✅ Enhanced TF has {abs(switch_diff)} fewer switches")
    else:
        print(f"   ⚠️  Enhanced TF has {switch_diff} more switches")

print("\n📈 Comparison with Pure Factors:")
print(f"   • Momentum CAGR: {mom_metrics['CAGR']:.2f}%")
print(f"   • Value CAGR: {val_metrics['CAGR']:.2f}%")
print(f"   • Enhanced TF vs Momentum: {enhanced_metrics['CAGR'] - mom_metrics['CAGR']:+.2f}%")
print(f"   • Enhanced TF vs Value: {enhanced_metrics['CAGR'] - val_metrics['CAGR']:+.2f}%")

# Create visualization
print("\n📊 Creating comparison charts...")

fig = plt.figure(figsize=(18, 10))
gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)

# 1. NAV comparison
ax1 = fig.add_subplot(gs[0, :])

enhanced_nav = 100 * (1 + enhanced_df['Portfolio_Return']).cumprod()
mom_returns = mom_df['Close'].pct_change().fillna(0)
val_returns = val_df['Close'].pct_change().fillna(0)
mom_nav = 100 * (1 + mom_returns).cumprod()
val_nav = 100 * (1 + val_returns).cumprod()

ax1.plot(enhanced_df['Date'], enhanced_nav, linewidth=2, label=f'Enhanced TF ({enhanced_metrics["CAGR"]:.2f}%)', color='blue')
if has_regime:
    regime_nav = 100 * (1 + regime_df['Portfolio_Return']).cumprod()
    ax1.plot(regime_df['Date'], regime_nav, linewidth=2, label=f'Regime Switch ({regime_metrics["CAGR"]:.2f}%)', color='orange', alpha=0.7)
ax1.plot(mom_df['Date'], mom_nav, linewidth=1.5, label=f'Pure Momentum ({mom_metrics["CAGR"]:.2f}%)', color='green', alpha=0.6, linestyle='--')
ax1.plot(val_df['Date'], val_nav, linewidth=1.5, label=f'Pure Value ({val_metrics["CAGR"]:.2f}%)', color='red', alpha=0.6, linestyle='--')

ax1.set_title('NAV Comparison (₹100 Initial Investment)', fontsize=14, fontweight='bold')
ax1.set_xlabel('Date', fontsize=12)
ax1.set_ylabel('NAV (₹)', fontsize=12)
ax1.legend(loc='best', fontsize=10)
ax1.grid(True, alpha=0.3)
ax1.set_yscale('log')

# 2. Allocation over time
ax2 = fig.add_subplot(gs[1, 0])
ax2.fill_between(enhanced_df['Date'], 0, enhanced_df['w_mom'] * 100, alpha=0.6, color='green', label='Momentum')
ax2.fill_between(enhanced_df['Date'], enhanced_df['w_mom'] * 100, 100, alpha=0.6, color='red', label='Value')
ax2.set_title('Enhanced TF: Allocation Over Time', fontsize=12, fontweight='bold')
ax2.set_xlabel('Date', fontsize=10)
ax2.set_ylabel('Allocation (%)', fontsize=10)
ax2.legend(loc='best')
ax2.grid(True, alpha=0.3)
ax2.set_ylim(0, 100)

# 3. Regime distribution
ax3 = fig.add_subplot(gs[1, 1])
regime_data = [enhanced_regime_dist.get('momentum', 0), enhanced_regime_dist.get('value', 0)]
colors = ['green', 'red']
labels = [f'Momentum\n({enhanced_regime_dist.get("momentum", 0)} months)', 
          f'Value\n({enhanced_regime_dist.get("value", 0)} months)']
ax3.pie(regime_data, labels=labels, colors=colors, autopct='%1.1f%%', startangle=90)
ax3.set_title('Enhanced TF: Regime Distribution', fontsize=12, fontweight='bold')

# 4. Performance metrics bar chart
ax4 = fig.add_subplot(gs[2, 0])
metrics = ['CAGR', 'MAR Ratio']
enhanced_vals = [enhanced_metrics['CAGR'], enhanced_metrics['MAR_Ratio']]

if has_regime:
    regime_vals = [regime_metrics['CAGR'], regime_metrics['MAR_Ratio']]
    x = np.arange(len(metrics))
    width = 0.35
    ax4.bar(x - width/2, enhanced_vals, width, label='Enhanced TF', color='blue', alpha=0.7)
    ax4.bar(x + width/2, regime_vals, width, label='Regime Switch', color='orange', alpha=0.7)
    ax4.set_xticks(x)
else:
    ax4.bar(metrics, enhanced_vals, color='blue', alpha=0.7)

ax4.set_xticklabels(metrics)
ax4.set_title('Performance Metrics Comparison', fontsize=12, fontweight='bold')
ax4.set_ylabel('Value', fontsize=10)
ax4.legend()
ax4.grid(True, alpha=0.3, axis='y')

# 5. Number of switches
ax5 = fig.add_subplot(gs[2, 1])
strategies = ['Enhanced TF']
switches_data = [enhanced_switches]

if has_regime:
    strategies.append('Regime Switch')
    switches_data.append(regime_switches)

colors_bar = ['blue', 'orange'][:len(strategies)]
bars = ax5.bar(strategies, switches_data, color=colors_bar, alpha=0.7)

# Add value labels on bars
for bar in bars:
    height = bar.get_height()
    ax5.text(bar.get_x() + bar.get_width()/2., height,
            f'{int(height)}',
            ha='center', va='bottom', fontsize=11, fontweight='bold')

ax5.set_title('Number of Regime Switches', fontsize=12, fontweight='bold')
ax5.set_ylabel('Switches', fontsize=10)
ax5.grid(True, alpha=0.3, axis='y')

plt.suptitle('Enhanced Trend-Following Strategy Comparison', fontsize=16, fontweight='bold', y=0.995)

# Save
output_file = output_folder.parent / "enhanced_trend_following_comparison.png"
plt.savefig(output_file, dpi=300, bbox_inches='tight')
print(f"✅ Saved comparison chart: {output_file}")
plt.close()

print("\n" + "="*100)
print("✅ COMPARISON COMPLETE")
print("="*100)
print()
