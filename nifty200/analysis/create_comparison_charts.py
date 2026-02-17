"""
Visual Comparison of Strategies
Creates charts comparing regime-based switching vs quarterly alpha rotation
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import numpy as np

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def create_comparison_charts():
    """Create visual comparison charts"""
    
    output_dir = Path(__file__).parent.parent / "output" / "monthly"
    
    # Load portfolio data
    regime_df = pd.read_csv(output_dir / "portfolio_regime_switching.csv", parse_dates=['Date'])
    quarterly_df = pd.read_csv(output_dir / "portfolio_ratio_trend_75_25.csv", parse_dates=['Date'])
    
    # Load pure momentum and value
    mom_df = pd.read_csv(output_dir / "nifty200_momentum_30_monthly.csv", parse_dates=['Date'])
    val_df = pd.read_csv(output_dir / "nifty200_value_30_monthly.csv", parse_dates=['Date'])
    
    # Create figure with subplots
    fig = plt.figure(figsize=(16, 12))
    gs = fig.add_gridspec(3, 2, hspace=0.3, wspace=0.3)
    
    # 1. NAV Comparison
    ax1 = fig.add_subplot(gs[0, :])
    ax1.plot(mom_df['Date'], mom_df['Close'], label='Pure Momentum', linewidth=2, alpha=0.7)
    ax1.plot(val_df['Date'], val_df['Close'], label='Pure Value', linewidth=2, alpha=0.7)
    ax1.plot(quarterly_df['Date'], quarterly_df['Portfolio_NAV'], label='Quarterly Alpha', linewidth=2, alpha=0.9)
    ax1.plot(regime_df['Date'], regime_df['Portfolio_NAV'], label='Regime Switching', linewidth=2, alpha=0.9, linestyle='--')
    ax1.set_title('Portfolio NAV Comparison (2005-2025)', fontsize=14, fontweight='bold')
    ax1.set_xlabel('Date', fontsize=12)
    ax1.set_ylabel('NAV (Base = 1000)', fontsize=12)
    ax1.legend(loc='upper left', fontsize=10)
    ax1.grid(True, alpha=0.3)
    ax1.set_yscale('log')
    
    # 2. Allocation Over Time - Regime Switching
    ax2 = fig.add_subplot(gs[1, 0])
    ax2.fill_between(regime_df['Date'], 0, regime_df['w_mom']*100, 
                     alpha=0.6, label='Momentum', color='green')
    ax2.fill_between(regime_df['Date'], regime_df['w_mom']*100, 100, 
                     alpha=0.6, label='Value', color='orange')
    ax2.set_title('Regime Switching: Allocation Over Time', fontsize=12, fontweight='bold')
    ax2.set_xlabel('Date', fontsize=10)
    ax2.set_ylabel('Allocation (%)', fontsize=10)
    ax2.legend(loc='upper right', fontsize=9)
    ax2.grid(True, alpha=0.3)
    ax2.set_ylim(0, 100)
    
    # 3. Allocation Over Time - Quarterly Alpha
    ax3 = fig.add_subplot(gs[1, 1])
    ax3.fill_between(quarterly_df['Date'], 0, quarterly_df['w_mom']*100, 
                     alpha=0.6, label='Momentum', color='green')
    ax3.fill_between(quarterly_df['Date'], quarterly_df['w_mom']*100, 100, 
                     alpha=0.6, label='Value', color='orange')
    ax3.set_title('Quarterly Alpha: Allocation Over Time', fontsize=12, fontweight='bold')
    ax3.set_xlabel('Date', fontsize=10)
    ax3.set_ylabel('Allocation (%)', fontsize=10)
    ax3.legend(loc='upper right', fontsize=9)
    ax3.grid(True, alpha=0.3)
    ax3.set_ylim(0, 100)
    
    # 4. Performance Metrics Bar Chart
    ax4 = fig.add_subplot(gs[2, 0])
    strategies = ['Pure\nMomentum', 'Pure\nValue', 'Quarterly\nAlpha', 'Regime\nSwitching']
    cagr_values = [18.47, 14.35, 18.12, 17.97]
    colors = ['#2ecc71', '#e74c3c', '#3498db', '#9b59b6']
    bars = ax4.bar(strategies, cagr_values, color=colors, alpha=0.7, edgecolor='black')
    ax4.set_title('CAGR Comparison', fontsize=12, fontweight='bold')
    ax4.set_ylabel('CAGR (%)', fontsize=10)
    ax4.grid(True, alpha=0.3, axis='y')
    
    # Add value labels on bars
    for bar, val in zip(bars, cagr_values):
        height = bar.get_height()
        ax4.text(bar.get_x() + bar.get_width()/2., height,
                f'{val:.2f}%', ha='center', va='bottom', fontsize=9, fontweight='bold')
    
    # 5. Switching Activity
    ax5 = fig.add_subplot(gs[2, 1])
    strategies_switch = ['Quarterly\nAlpha', 'Regime\nSwitching']
    switches = [22, 32]
    colors_switch = ['#3498db', '#9b59b6']
    bars2 = ax5.bar(strategies_switch, switches, color=colors_switch, alpha=0.7, edgecolor='black')
    ax5.set_title('Number of Switches (249 months)', fontsize=12, fontweight='bold')
    ax5.set_ylabel('Number of Switches', fontsize=10)
    ax5.grid(True, alpha=0.3, axis='y')
    
    # Add value labels
    for bar, val in zip(bars2, switches):
        height = bar.get_height()
        ax5.text(bar.get_x() + bar.get_width()/2., height,
                f'{val}', ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    plt.suptitle('Strategy Comparison: Regime Switching vs Quarterly Alpha Rotation', 
                 fontsize=16, fontweight='bold', y=0.995)
    
    # Save figure
    output_file = output_dir.parent / "strategy_comparison_charts.png"
    plt.savefig(output_file, dpi=300, bbox_inches='tight')
    print(f"✅ Saved comparison charts to: {output_file}")
    plt.close()
    
    # Create regime distribution pie charts
    fig2, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))
    
    # Regime Switching distribution
    regime_counts = regime_df['regime'].value_counts()
    colors1 = ['#2ecc71', '#e74c3c']
    ax1.pie(regime_counts.values, labels=[f'{k.capitalize()}\n({v} months)' for k, v in regime_counts.items()], 
            autopct='%1.1f%%', colors=colors1, startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'})
    ax1.set_title('Regime Switching: Time in Each Regime', fontsize=13, fontweight='bold')
    
    # Quarterly Alpha distribution
    quarterly_counts = quarterly_df['regime'].value_counts()
    ax2.pie(quarterly_counts.values, labels=[f'{k.capitalize()}\n({v} months)' for k, v in quarterly_counts.items()], 
            autopct='%1.1f%%', colors=colors1, startangle=90, textprops={'fontsize': 11, 'fontweight': 'bold'})
    ax2.set_title('Quarterly Alpha: Time in Each Regime', fontsize=13, fontweight='bold')
    
    plt.suptitle('Regime Distribution Comparison', fontsize=15, fontweight='bold')
    
    # Save figure
    output_file2 = output_dir.parent / "regime_distribution_charts.png"
    plt.savefig(output_file2, dpi=300, bbox_inches='tight')
    print(f"✅ Saved regime distribution charts to: {output_file2}")
    plt.close()
    
    # Create detailed metrics table
    print("\n" + "="*80)
    print("DETAILED METRICS COMPARISON")
    print("="*80)
    
    metrics_data = {
        'Metric': [
            'CAGR (%)',
            'SIP XIRR (%)',
            'Max Drawdown (%)',
            'MAR Ratio',
            'Avg Mom Allocation (%)',
            'Avg Val Allocation (%)',
            'Time in Mom Regime (%)',
            'Time in Val Regime (%)',
            'Number of Switches',
            'Avg Switch Frequency (months)'
        ],
        'Quarterly Alpha': [
            18.12,
            17.00,
            -50.27,
            0.34,
            76.3,
            23.7,
            50.6,
            49.4,
            22,
            11.3
        ],
        'Regime Switching': [
            17.97,
            16.53,
            -51.46,
            0.32,
            71.9,
            28.1,
            87.6,
            12.4,
            32,
            7.8
        ],
        'Difference': [
            -0.15,
            -0.47,
            -1.19,
            -0.02,
            -4.4,
            +4.4,
            +37.0,
            -37.0,
            +10,
            -3.5
        ]
    }
    
    df_metrics = pd.DataFrame(metrics_data)
    print("\n" + df_metrics.to_string(index=False))
    print()


if __name__ == "__main__":
    create_comparison_charts()
