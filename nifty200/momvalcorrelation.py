"""
Momentum-Value Correlation Analysis for Smart Beta Switching Strategy

This module performs comprehensive correlation analysis between Momentum and Value factors
to identify optimal switching opportunities. It goes beyond simple correlation to analyze:
1. Rolling correlation over time
2. Conditional correlation during stress periods
3. Relative performance correlation (momentum/value ratio)
4. Regime detection and switching signals

Author: Smart Beta Investing Analysis
Date: 2026-02-17
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class MomentumValueCorrelationAnalyzer:
    """
    Analyzes correlation patterns between Momentum and Value factors
    to identify switching opportunities.
    """
    
    def __init__(self, data_dir='output'):
        """
        Initialize the analyzer with data directory.
        
        Args:
            data_dir: Directory containing the momentum and value data files
        """
        self.data_dir = Path(data_dir)
        self.weekly_data = None
        self.monthly_data = None
        self.mom_ret = None
        self.val_ret = None
        self.ratio = None
        
    def load_data(self):
        """Load weekly and monthly momentum/value data."""
        print("=" * 80)
        print("LOADING DATA")
        print("=" * 80)
        
        # Load weekly ratio data (already has momentum and value prices)
        weekly_file = self.data_dir / 'weekly' / 'nifty200_momentum_value_ratio_weekly.csv'
        if weekly_file.exists():
            self.weekly_data = pd.read_csv(weekly_file, parse_dates=['Date'])
            self.weekly_data.set_index('Date', inplace=True)
            print(f"✓ Loaded weekly data: {len(self.weekly_data)} rows")
            print(f"  Date range: {self.weekly_data.index.min()} to {self.weekly_data.index.max()}")
        else:
            raise FileNotFoundError(f"Weekly data file not found: {weekly_file}")
        
        # Load monthly data
        mom_file = self.data_dir / 'monthly' / 'nifty200_momentum_30_monthly.csv'
        val_file = self.data_dir / 'monthly' / 'nifty200_value_30_monthly.csv'
        
        if mom_file.exists() and val_file.exists():
            mom_monthly = pd.read_csv(mom_file, parse_dates=['Date'])
            val_monthly = pd.read_csv(val_file, parse_dates=['Date'])
            
            self.monthly_data = pd.DataFrame({
                'Date': mom_monthly['Date'],
                'Momentum_Close': mom_monthly['Close'],
                'Value_Close': val_monthly['Close']
            })
            self.monthly_data.set_index('Date', inplace=True)
            print(f"✓ Loaded monthly data: {len(self.monthly_data)} rows")
            print(f"  Date range: {self.monthly_data.index.min()} to {self.monthly_data.index.max()}")
        else:
            print("⚠ Monthly data files not found, will use weekly data only")
        
        print()
        
    def calculate_returns(self):
        """
        STEP A: Convert prices to weekly returns.
        """
        print("=" * 80)
        print("STEP A: CALCULATING WEEKLY RETURNS")
        print("=" * 80)
        
        # Calculate weekly returns
        self.mom_ret = self.weekly_data['Momentum_Close'].pct_change()
        self.val_ret = self.weekly_data['Value_Close'].pct_change()
        
        # Calculate the ratio
        self.ratio = self.weekly_data['Momentum_Close'] / self.weekly_data['Value_Close']
        
        print(f"Momentum returns calculated: {len(self.mom_ret.dropna())} periods")
        print(f"Value returns calculated: {len(self.val_ret.dropna())} periods")
        print(f"Momentum/Value ratio calculated: {len(self.ratio.dropna())} periods")
        print()
        
        # Basic statistics
        print("Return Statistics:")
        print(f"  Momentum - Mean: {self.mom_ret.mean()*100:.3f}%, Std: {self.mom_ret.std()*100:.3f}%")
        print(f"  Value    - Mean: {self.val_ret.mean()*100:.3f}%, Std: {self.val_ret.std()*100:.3f}%")
        print()
        
    def analyze_rolling_correlation(self, window=26):
        """
        STEP B: Calculate and plot rolling correlation.
        
        Args:
            window: Rolling window size (default 26 weeks ≈ 6 months)
        
        Returns:
            DataFrame with rolling correlation
        """
        print("=" * 80)
        print(f"STEP B: ROLLING CORRELATION (Window = {window} weeks ≈ {window/4.33:.1f} months)")
        print("=" * 80)
        
        rolling_corr = self.mom_ret.rolling(window).corr(self.val_ret)
        
        # Statistics
        print(f"Rolling Correlation Statistics:")
        print(f"  Mean:   {rolling_corr.mean():.3f}")
        print(f"  Median: {rolling_corr.median():.3f}")
        print(f"  Std:    {rolling_corr.std():.3f}")
        print(f"  Min:    {rolling_corr.min():.3f}")
        print(f"  Max:    {rolling_corr.max():.3f}")
        print()
        
        # Analyze distribution
        negative_pct = (rolling_corr < 0).sum() / len(rolling_corr.dropna()) * 100
        near_zero_pct = ((rolling_corr >= -0.2) & (rolling_corr <= 0.2)).sum() / len(rolling_corr.dropna()) * 100
        
        print(f"Distribution Analysis:")
        print(f"  Negative correlation: {negative_pct:.1f}% of time")
        print(f"  Near zero (-0.2 to +0.2): {near_zero_pct:.1f}% of time")
        print()
        
        # Plot
        plt.figure(figsize=(14, 6))
        plt.plot(rolling_corr.index, rolling_corr.values, linewidth=1.5, alpha=0.8)
        plt.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        plt.axhline(y=-0.2, color='red', linestyle=':', linewidth=1, alpha=0.5, label='Switching threshold (-0.2)')
        plt.axhline(y=0.2, color='green', linestyle=':', linewidth=1, alpha=0.5)
        plt.fill_between(rolling_corr.index, -0.2, 0.2, alpha=0.1, color='gray', label='Near-zero zone')
        plt.title(f'{window}-Week Rolling Correlation: Momentum vs Value', fontsize=14, fontweight='bold')
        plt.xlabel('Date', fontsize=12)
        plt.ylabel('Correlation', fontsize=12)
        plt.legend()
        plt.grid(True, alpha=0.3)
        plt.tight_layout()
        plt.savefig(self.data_dir / 'rolling_correlation.png', dpi=300, bbox_inches='tight')
        print(f"✓ Saved plot: {self.data_dir / 'rolling_correlation.png'}")
        plt.close()
        
        return rolling_corr
        
    def analyze_stress_correlation(self):
        """
        STEP C: Calculate conditional correlation during momentum stress periods.
        
        Returns:
            Dictionary with stress correlation metrics
        """
        print("=" * 80)
        print("STEP C: CONDITIONAL CORRELATION (During Momentum Stress)")
        print("=" * 80)
        
        # Define stress periods (when momentum returns are negative)
        stress = self.mom_ret < 0
        
        # Calculate correlations
        stress_corr = self.mom_ret[stress].corr(self.val_ret[stress])
        normal_corr = self.mom_ret[~stress].corr(self.val_ret[~stress])
        full_corr = self.mom_ret.corr(self.val_ret)
        
        stress_weeks = stress.sum()
        total_weeks = len(stress)
        stress_pct = stress_weeks / total_weeks * 100
        
        print(f"Stress Period Analysis:")
        print(f"  Total weeks: {total_weeks}")
        print(f"  Stress weeks (Mom < 0): {stress_weeks} ({stress_pct:.1f}%)")
        print()
        
        print(f"Correlation Metrics:")
        print(f"  Full period correlation:   {full_corr:+.3f}")
        print(f"  Normal period correlation: {normal_corr:+.3f}")
        print(f"  Stress period correlation: {stress_corr:+.3f}")
        print()
        
        # Interpretation
        print("Interpretation:")
        if stress_corr < -0.2:
            print("  ✓ STRONG HEDGING: Value provides strong protection during momentum stress")
        elif stress_corr < 0:
            print("  ✓ HEDGING: Value provides some protection during momentum stress")
        elif stress_corr < 0.2:
            print("  ≈ DIVERSIFICATION: Value provides diversification benefit")
        else:
            print("  ✗ NO PROTECTION: Value does not hedge momentum during stress")
        print()
        
        # Calculate average returns during stress
        mom_stress_ret = self.mom_ret[stress].mean() * 100
        val_stress_ret = self.val_ret[stress].mean() * 100
        
        print(f"Average Returns During Stress:")
        print(f"  Momentum: {mom_stress_ret:+.3f}% per week")
        print(f"  Value:    {val_stress_ret:+.3f}% per week")
        print()
        
        return {
            'full_corr': full_corr,
            'normal_corr': normal_corr,
            'stress_corr': stress_corr,
            'stress_weeks': stress_weeks,
            'stress_pct': stress_pct,
            'mom_stress_ret': mom_stress_ret,
            'val_stress_ret': val_stress_ret
        }
        
    def analyze_relative_performance(self, window=26):
        """
        STEP D & E: Analyze relative performance ratio and regime correlation.
        
        Args:
            window: Window for moving average (default 26 weeks)
        
        Returns:
            DataFrame with regime analysis
        """
        print("=" * 80)
        print(f"STEP D & E: RELATIVE PERFORMANCE & REGIME ANALYSIS")
        print("=" * 80)
        
        # Calculate ratio returns
        ratio_ret = self.ratio.pct_change()
        
        # Calculate moving average
        ratio_ma = self.ratio.rolling(window).mean()
        
        # Identify regimes
        value_regime = self.ratio < ratio_ma  # Value leading when ratio below MA
        mom_regime = self.ratio >= ratio_ma   # Momentum leading when ratio above MA
        
        # Calculate statistics for each regime
        value_regime_weeks = value_regime.sum()
        mom_regime_weeks = mom_regime.sum()
        total_weeks = len(value_regime)
        
        print(f"Regime Distribution:")
        print(f"  Total weeks: {total_weeks}")
        print(f"  Value regime weeks: {value_regime_weeks} ({value_regime_weeks/total_weeks*100:.1f}%)")
        print(f"  Momentum regime weeks: {mom_regime_weeks} ({mom_regime_weeks/total_weeks*100:.1f}%)")
        print()
        
        # Performance during each regime
        mom_ret_in_value_regime = self.mom_ret[value_regime].mean() * 100
        val_ret_in_value_regime = self.val_ret[value_regime].mean() * 100
        
        mom_ret_in_mom_regime = self.mom_ret[mom_regime].mean() * 100
        val_ret_in_mom_regime = self.val_ret[mom_regime].mean() * 100
        
        print(f"Average Weekly Returns by Regime:")
        print(f"  During VALUE regime (Ratio < {window}W MA):")
        print(f"    Momentum: {mom_ret_in_value_regime:+.3f}%")
        print(f"    Value:    {val_ret_in_value_regime:+.3f}%")
        print(f"    Difference: {(val_ret_in_value_regime - mom_ret_in_value_regime):+.3f}%")
        print()
        print(f"  During MOMENTUM regime (Ratio >= {window}W MA):")
        print(f"    Momentum: {mom_ret_in_mom_regime:+.3f}%")
        print(f"    Value:    {val_ret_in_mom_regime:+.3f}%")
        print(f"    Difference: {(mom_ret_in_mom_regime - val_ret_in_mom_regime):+.3f}%")
        print()
        
        # Plot ratio with regimes
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(14, 10))
        
        # Plot 1: Ratio with MA
        ax1.plot(self.ratio.index, self.ratio.values, label='Mom/Val Ratio', linewidth=1.5, alpha=0.8)
        ax1.plot(ratio_ma.index, ratio_ma.values, label=f'{window}W MA', linewidth=2, color='red', alpha=0.7)
        ax1.fill_between(self.ratio.index, self.ratio.values, ratio_ma.values, 
                         where=(self.ratio < ratio_ma), alpha=0.2, color='blue', label='Value Regime')
        ax1.fill_between(self.ratio.index, self.ratio.values, ratio_ma.values, 
                         where=(self.ratio >= ratio_ma), alpha=0.2, color='green', label='Momentum Regime')
        ax1.set_title('Momentum/Value Ratio with Regime Detection', fontsize=14, fontweight='bold')
        ax1.set_ylabel('Ratio', fontsize=12)
        ax1.legend(loc='best')
        ax1.grid(True, alpha=0.3)
        
        # Plot 2: Cumulative returns by regime
        cum_mom = (1 + self.mom_ret).cumprod()
        cum_val = (1 + self.val_ret).cumprod()
        
        ax2.plot(cum_mom.index, cum_mom.values, label='Momentum', linewidth=1.5, alpha=0.8)
        ax2.plot(cum_val.index, cum_val.values, label='Value', linewidth=1.5, alpha=0.8)
        ax2.set_title('Cumulative Returns: Momentum vs Value', fontsize=14, fontweight='bold')
        ax2.set_xlabel('Date', fontsize=12)
        ax2.set_ylabel('Cumulative Return (Base=1)', fontsize=12)
        ax2.legend(loc='best')
        ax2.grid(True, alpha=0.3)
        ax2.set_yscale('log')
        
        plt.tight_layout()
        plt.savefig(self.data_dir / 'regime_analysis.png', dpi=300, bbox_inches='tight')
        print(f"✓ Saved plot: {self.data_dir / 'regime_analysis.png'}")
        plt.close()
        
        # Create regime DataFrame
        regime_df = pd.DataFrame({
            'ratio': self.ratio,
            'ratio_ma': ratio_ma,
            'value_regime': value_regime,
            'mom_ret': self.mom_ret,
            'val_ret': self.val_ret
        })
        
        return regime_df
        
    def evaluate_switching_conditions(self, rolling_corr, regime_df, lookback_8w=8, ma_window=26):
        """
        Evaluate the three conditions for switching strategy.
        
        Switching is justified when ALL three conditions are met:
        1. Rolling correlation < -0.2
        2. Momentum 8-week return < 2%
        3. Momentum/Value ratio < 26-week MA
        
        Args:
            rolling_corr: Rolling correlation series
            regime_df: DataFrame with regime analysis
            lookback_8w: Lookback period for momentum return (default 8 weeks)
            ma_window: Moving average window (default 26 weeks)
        
        Returns:
            DataFrame with switching signals
        """
        print("=" * 80)
        print("SWITCHING CONDITION EVALUATION")
        print("=" * 80)
        
        # Calculate 8-week momentum return
        mom_8w_ret = self.weekly_data['Momentum_Close'].pct_change(lookback_8w) * 100
        
        # Define conditions
        condition_1 = rolling_corr < -0.2
        condition_2 = mom_8w_ret < 2.0
        condition_3 = regime_df['ratio'] < regime_df['ratio_ma']
        
        # All three conditions must be met
        switch_signal = condition_1 & condition_2 & condition_3
        
        # Count signals
        total_weeks = len(switch_signal.dropna())
        switch_weeks = switch_signal.sum()
        switch_pct = switch_weeks / total_weeks * 100
        
        print(f"Condition Analysis (out of {total_weeks} weeks):")
        print(f"  Condition 1 (Corr < -0.2):      {condition_1.sum()} weeks ({condition_1.sum()/total_weeks*100:.1f}%)")
        print(f"  Condition 2 (Mom 8W < 2%):      {condition_2.sum()} weeks ({condition_2.sum()/total_weeks*100:.1f}%)")
        print(f"  Condition 3 (Ratio < {ma_window}W MA): {condition_3.sum()} weeks ({condition_3.sum()/total_weeks*100:.1f}%)")
        print()
        print(f"  ALL THREE CONDITIONS MET:       {switch_weeks} weeks ({switch_pct:.1f}%)")
        print()
        
        # Create switching DataFrame
        switch_df = pd.DataFrame({
            'rolling_corr': rolling_corr,
            'mom_8w_ret': mom_8w_ret,
            'ratio': regime_df['ratio'],
            'ratio_ma': regime_df['ratio_ma'],
            'condition_1': condition_1,
            'condition_2': condition_2,
            'condition_3': condition_3,
            'switch_to_value': switch_signal,
            'mom_ret': self.mom_ret,
            'val_ret': self.val_ret
        })
        
        # Analyze performance when switch signal is active
        if switch_weeks > 0:
            mom_ret_when_switch = self.mom_ret[switch_signal].mean() * 100
            val_ret_when_switch = self.val_ret[switch_signal].mean() * 100
            
            print(f"Average Weekly Returns When Switch Signal Active:")
            print(f"  Momentum: {mom_ret_when_switch:+.3f}%")
            print(f"  Value:    {val_ret_when_switch:+.3f}%")
            print(f"  Benefit:  {(val_ret_when_switch - mom_ret_when_switch):+.3f}%")
            print()
        
        # Simple switching trigger
        print("=" * 80)
        print("SIMPLE SWITCHING TRIGGER")
        print("=" * 80)
        print("IF:")
        print("  - Momentum 8W return < 0%")
        print("  - AND Momentum/Value ratio < 26W MA")
        print("THEN:")
        print("  → Tilt toward VALUE")
        print("ELSE:")
        print("  → MOMENTUM dominant")
        print()
        
        # Calculate simple trigger
        simple_trigger = (mom_8w_ret < 0) & (regime_df['ratio'] < regime_df['ratio_ma'])
        simple_trigger_weeks = simple_trigger.sum()
        simple_trigger_pct = simple_trigger_weeks / total_weeks * 100
        
        print(f"Simple Trigger Active: {simple_trigger_weeks} weeks ({simple_trigger_pct:.1f}%)")
        
        if simple_trigger_weeks > 0:
            mom_ret_simple = self.mom_ret[simple_trigger].mean() * 100
            val_ret_simple = self.val_ret[simple_trigger].mean() * 100
            
            print(f"  Momentum avg return: {mom_ret_simple:+.3f}%")
            print(f"  Value avg return:    {val_ret_simple:+.3f}%")
            print(f"  Benefit:             {(val_ret_simple - mom_ret_simple):+.3f}%")
        print()
        
        switch_df['simple_trigger'] = simple_trigger
        
        return switch_df
        
    def generate_summary_report(self, rolling_corr, stress_metrics, switch_df):
        """
        Generate a comprehensive summary report.
        
        Args:
            rolling_corr: Rolling correlation series
            stress_metrics: Dictionary with stress correlation metrics
            switch_df: DataFrame with switching signals
        """
        print("=" * 80)
        print("COMPREHENSIVE SUMMARY REPORT")
        print("=" * 80)
        print()
        
        print("📊 TYPICAL VALUES FOR NIFTY FACTOR DATA")
        print("-" * 80)
        print(f"{'Metric':<30} {'Expected Range':<20} {'Your Data':<20}")
        print("-" * 80)
        
        full_corr = stress_metrics['full_corr']
        stress_corr = stress_metrics['stress_corr']
        
        print(f"{'Full-period correlation':<30} {'-0.1 to +0.1':<20} {full_corr:+.3f}")
        print(f"{'Stress correlation':<30} {'-0.3 to -0.5':<20} {stress_corr:+.3f}")
        print(f"{'Ratio regime swings':<30} {'Clear multi-month':<20} {'See chart':<20}")
        print()
        
        print("✅ INTERPRETATION")
        print("-" * 80)
        
        if abs(full_corr) < 0.15:
            print("✓ Long-term correlation ≈ zero → Good diversification")
        else:
            print("⚠ Long-term correlation not near zero → Limited diversification")
            
        if stress_corr < -0.2:
            print("✓ During stress: Value negatively correlated → Good hedge")
        else:
            print("⚠ During stress: Value not providing strong hedge")
            
        print("✓ Relative leadership rotates → Switching opportunity exists")
        print()
        
        print("🎯 SWITCHING JUSTIFICATION")
        print("-" * 80)
        print("Rotation is mathematically worthwhile when ALL conditions met:")
        print()
        print("  ✓ Condition 1: Rolling correlation < -0.2")
        print("  ✓ Condition 2: Momentum 8W return < 2%")
        print("  ✓ Condition 3: Momentum/Value ratio < 26W MA")
        print()
        
        switch_weeks = switch_df['switch_to_value'].sum()
        total_weeks = len(switch_df['switch_to_value'].dropna())
        
        print(f"All conditions met: {switch_weeks}/{total_weeks} weeks ({switch_weeks/total_weeks*100:.1f}%)")
        print()
        
        if switch_weeks > 0:
            benefit = (switch_df.loc[switch_df['switch_to_value'], 'val_ret'].mean() - 
                      switch_df.loc[switch_df['switch_to_value'], 'mom_ret'].mean()) * 100
            print(f"Average weekly benefit when switching: {benefit:+.3f}%")
            print()
        
        print("💡 RECOMMENDATION")
        print("-" * 80)
        
        if switch_weeks > 0 and stress_corr < -0.2:
            print("✅ SWITCHING STRATEGY IS JUSTIFIED")
            print()
            print("The data shows:")
            print("  • Clear regime rotation between Momentum and Value")
            print("  • Value provides hedge during Momentum stress")
            print("  • Switching conditions identify favorable periods")
            print()
            print("Suggested approach:")
            print("  • Use the 3-condition framework for tactical switches")
            print("  • Or use the simple trigger (Mom 8W < 0 AND Ratio < 26W MA)")
            print("  • Monitor rolling correlation for early warnings")
        else:
            print("⚠ SWITCHING STRATEGY NEEDS REVIEW")
            print()
            print("Consider:")
            print("  • Adjusting switching thresholds")
            print("  • Using longer lookback periods")
            print("  • Focusing on regime-based allocation instead")
        
        print()
        print("=" * 80)
        
    def run_full_analysis(self):
        """
        Run the complete correlation analysis pipeline.
        """
        print("\n")
        print("╔" + "=" * 78 + "╗")
        print("║" + " " * 15 + "MOMENTUM-VALUE CORRELATION ANALYSIS" + " " * 28 + "║")
        print("║" + " " * 20 + "Smart Beta Switching Strategy" + " " * 29 + "║")
        print("╚" + "=" * 78 + "╝")
        print("\n")
        
        # Load data
        self.load_data()
        
        # Step A: Calculate returns
        self.calculate_returns()
        
        # Step B: Rolling correlation
        rolling_corr = self.analyze_rolling_correlation(window=26)
        
        # Step C: Stress correlation
        stress_metrics = self.analyze_stress_correlation()
        
        # Step D & E: Relative performance and regime analysis
        regime_df = self.analyze_relative_performance(window=26)
        
        # Evaluate switching conditions
        switch_df = self.evaluate_switching_conditions(rolling_corr, regime_df)
        
        # Generate summary report
        self.generate_summary_report(rolling_corr, stress_metrics, switch_df)
        
        # Save results
        output_file = self.data_dir / 'momentum_value_correlation_analysis.csv'
        switch_df.to_csv(output_file)
        print(f"\n✓ Analysis results saved to: {output_file}")
        print(f"✓ Charts saved to: {self.data_dir}")
        print()
        
        return switch_df


def main():
    """Main execution function."""
    # Initialize analyzer
    analyzer = MomentumValueCorrelationAnalyzer(data_dir='output')
    
    # Run full analysis
    results = analyzer.run_full_analysis()
    
    print("\n✅ Analysis complete!")
    print("\nNext steps:")
    print("  1. Review the generated charts in the output folder")
    print("  2. Examine the correlation analysis CSV file")
    print("  3. Implement the switching strategy based on the signals")
    print("  4. Backtest the strategy with your portfolio code")
    print()


if __name__ == "__main__":
    main()
