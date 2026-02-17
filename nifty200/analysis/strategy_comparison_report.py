"""
Strategy Comparison Report: Regime-Based Switching vs Quarterly Alpha Rotation
Generated: 2026-02-17

This report compares two momentum-value allocation strategies:
1. Regime-Based Switching (NEW): Uses weekly Mom/Val ratio signals
2. Quarterly Alpha Rotation (EXISTING): Uses quarterly relative momentum signals
"""

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path

# Set style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")

def create_comparison_report():
    """Generate comprehensive comparison between strategies"""
    
    print("=" * 100)
    print(" " * 25 + "STRATEGY COMPARISON REPORT")
    print("=" * 100)
    print()
    
    # Define results
    strategies = {
        'Pure Momentum (100/0)': {
            'cagr': 18.47,
            'description': 'Buy and hold Nifty 200 Momentum 30',
            'allocation': '100% Momentum, 0% Value',
            'switches': 0,
            'time_in_regime': {'momentum': 100.0, 'value': 0.0}
        },
        'Pure Value (0/100)': {
            'cagr': 14.35,
            'description': 'Buy and hold Nifty 200 Value 30',
            'allocation': '0% Momentum, 100% Value',
            'switches': 0,
            'time_in_regime': {'momentum': 0.0, 'value': 100.0}
        },
        'Quarterly Alpha Rotation': {
            'cagr': 18.12,
            'sip_xirr': 17.00,
            'max_dd': -50.27,
            'mar_ratio': 0.34,
            'total_return': 663.43,
            'description': 'Dynamic tilt based on quarterly relative momentum',
            'allocation': 'Base 75/25, Range 100/0 to 50/50',
            'avg_allocation': {'momentum': 76.3, 'value': 23.7},
            'switches': 22,
            'time_in_regime': {'momentum': 50.6, 'value': 49.4}
        },
        'Regime-Based Switching': {
            'cagr': 17.97,
            'sip_xirr': 16.53,
            'max_dd': -51.46,
            'mar_ratio': 0.32,
            'total_return': 618.90,
            'description': 'Switches based on weekly Mom/Val ratio and 8W momentum',
            'allocation': '75/25 (momentum regime) or 50/50 (value regime)',
            'avg_allocation': {'momentum': 71.9, 'value': 28.1},
            'switches': 32,
            'time_in_regime': {'momentum': 87.6, 'value': 12.4}
        }
    }
    
    # Print detailed comparison
    print("\n" + "=" * 100)
    print("1. PERFORMANCE METRICS COMPARISON")
    print("=" * 100)
    print()
    
    print(f"{'Strategy':<30} {'CAGR':<10} {'SIP XIRR':<12} {'Max DD':<10} {'MAR':<8} {'Total Ret':<12}")
    print("-" * 100)
    
    for name, metrics in strategies.items():
        cagr = f"{metrics['cagr']:.2f}%" if 'cagr' in metrics else "N/A"
        xirr = f"{metrics['sip_xirr']:.2f}%" if 'sip_xirr' in metrics else "N/A"
        dd = f"{metrics['max_dd']:.2f}%" if 'max_dd' in metrics else "N/A"
        mar = f"{metrics['mar_ratio']:.2f}" if 'mar_ratio' in metrics else "N/A"
        ret = f"{metrics['total_return']:.2f}%" if 'total_return' in metrics else "N/A"
        
        print(f"{name:<30} {cagr:<10} {xirr:<12} {dd:<10} {mar:<8} {ret:<12}")
    
    print()
    print("=" * 100)
    print("2. ALLOCATION & REGIME ANALYSIS")
    print("=" * 100)
    print()
    
    for name, metrics in strategies.items():
        print(f"\n{name}:")
        print(f"  Description: {metrics['description']}")
        print(f"  Allocation:  {metrics['allocation']}")
        
        if 'avg_allocation' in metrics:
            print(f"  Avg Allocation: {metrics['avg_allocation']['momentum']:.1f}% Momentum / {metrics['avg_allocation']['value']:.1f}% Value")
        
        print(f"  Time in Regime: {metrics['time_in_regime']['momentum']:.1f}% Momentum / {metrics['time_in_regime']['value']:.1f}% Value")
        print(f"  Number of Switches: {metrics['switches']}")
    
    print()
    print("=" * 100)
    print("3. KEY INSIGHTS")
    print("=" * 100)
    print()
    
    print("📊 CAGR Rankings:")
    print("   1. Pure Momentum:           18.47% ⭐ (Best)")
    print("   2. Quarterly Alpha:         18.12% (-0.35% vs Momentum)")
    print("   3. Regime Switching:        17.97% (-0.50% vs Momentum)")
    print("   4. Pure Value:              14.35%")
    print()
    
    print("🔄 Switching Behavior:")
    print("   • Regime Switching:  32 switches over 249 months (1 switch every 7.8 months)")
    print("   • Quarterly Alpha:   22 switches over 249 months (1 switch every 11.3 months)")
    print("   • Regime Switching is MORE ACTIVE (45% more switches)")
    print()
    
    print("⏱️  Time Spent in Each Regime:")
    print("   Regime Switching:")
    print("      - Momentum regime (75/25): 87.6% of time (218 months)")
    print("      - Value regime (50/50):    12.4% of time (31 months)")
    print()
    print("   Quarterly Alpha:")
    print("      - Momentum regime: 50.6% of time (126 months)")
    print("      - Value regime:    49.4% of time (123 months)")
    print()
    print("   → Regime Switching stays in momentum-dominant allocation much longer")
    print()
    
    print("💡 INTERPRETATION:")
    print("-" * 100)
    print()
    print("1. REGIME SWITCHING CHARACTERISTICS:")
    print("   ✓ More conservative: Only switches when BOTH conditions met")
    print("   ✓ Momentum-biased: Spends 87.6% in momentum-dominant allocation")
    print("   ✓ Defensive: Switches to balanced (50/50) only during clear value regimes")
    print("   ✗ Slightly lower CAGR: -0.50% vs pure momentum, -0.15% vs quarterly alpha")
    print()
    
    print("2. QUARTERLY ALPHA CHARACTERISTICS:")
    print("   ✓ More balanced: Spends equal time in momentum and value regimes")
    print("   ✓ Dynamic tilt: Gradual allocation changes (not binary)")
    print("   ✓ Better CAGR: 18.12% (closer to pure momentum)")
    print("   ✓ Fewer switches: 22 vs 32 (less trading)")
    print()
    
    print("3. WHEN TO USE EACH STRATEGY:")
    print()
    print("   Use REGIME SWITCHING if you:")
    print("   • Believe momentum is the dominant factor long-term")
    print("   • Want to reduce exposure only during clear value regimes")
    print("   • Prefer a defensive, momentum-biased approach")
    print("   • Can tolerate more frequent switches (monthly rebalancing)")
    print()
    print("   Use QUARTERLY ALPHA if you:")
    print("   • Want more balanced exposure to both factors")
    print("   • Prefer smoother, gradual allocation changes")
    print("   • Want fewer switches (quarterly rebalancing)")
    print("   • Seek slightly higher CAGR with similar risk")
    print()
    
    print("=" * 100)
    print("4. RECOMMENDATION")
    print("=" * 100)
    print()
    print("Based on the analysis:")
    print()
    print("🏆 WINNER: Quarterly Alpha Rotation")
    print()
    print("Reasons:")
    print("  1. Higher CAGR (18.12% vs 17.97%)")
    print("  2. Better SIP XIRR (17.00% vs 16.53%)")
    print("  3. Fewer switches (22 vs 32) → lower transaction costs")
    print("  4. Better MAR ratio (0.34 vs 0.32)")
    print("  5. More balanced regime exposure (50/50 vs 88/12)")
    print()
    print("However, Regime Switching has merit if:")
    print("  • You have strong conviction in momentum factor dominance")
    print("  • You want a more defensive, momentum-biased portfolio")
    print("  • You can execute weekly signal calculations and monthly rebalancing")
    print()
    
    print("=" * 100)
    print("5. CORRELATION ANALYSIS INSIGHTS")
    print("=" * 100)
    print()
    print("From the correlation analysis (momvalcorrelation.py):")
    print()
    print("  • Momentum-Value correlation: +0.78 (HIGH positive correlation)")
    print("  • This explains why switching doesn't add much value")
    print("  • Both factors move together, so diversification benefit is limited")
    print("  • Value provides +0.62% weekly benefit only 12.5% of the time")
    print()
    print("  Key finding: In Indian markets, Mom and Val are NOT negatively correlated")
    print("  → Traditional US-style factor rotation doesn't work as well")
    print("  → Momentum-biased allocation is more appropriate")
    print()
    
    print("=" * 100)
    print()


if __name__ == "__main__":
    create_comparison_report()
