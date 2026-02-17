"""
Factor Outperformance Analysis
Identifies periods when Momentum or Value significantly outperformed each other
and analyzes the market conditions (6M, 1Y, 3Y returns) that preceded these periods.

Goal: Develop predictive rules for when to expect Value vs Momentum outperformance
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
from datetime import datetime, timedelta
import warnings
warnings.filterwarnings('ignore')

# Set plotting style
plt.style.use('seaborn-v0_8-darkgrid')
sns.set_palette("husl")


class FactorOutperformanceAnalyzer:
    """Analyzes periods of significant factor outperformance"""
    
    def __init__(self, data_folder):
        self.data_folder = Path(data_folder)
        self.output_folder = self.data_folder.parent / "output"
        self.df = None
        
    def load_data(self):
        """Load monthly momentum and value data"""
        print("\n" + "="*100)
        print("FACTOR OUTPERFORMANCE ANALYSIS")
        print("="*100)
        print("\n📂 Loading monthly data...")
        
        # Load momentum
        mom_file = self.output_folder / "monthly" / "nifty200_momentum_30_monthly.csv"
        mom_df = pd.read_csv(mom_file, parse_dates=['Date'])
        mom_df = mom_df.rename(columns={'Close': 'Mom_Close'})
        
        # Load value
        val_file = self.output_folder / "monthly" / "nifty200_value_30_monthly.csv"
        val_df = pd.read_csv(val_file, parse_dates=['Date'])
        val_df = val_df.rename(columns={'Close': 'Val_Close'})
        
        # Merge
        self.df = pd.merge(mom_df[['Date', 'Mom_Close']], 
                          val_df[['Date', 'Val_Close']], 
                          on='Date', how='inner')
        
        print(f"✅ Loaded {len(self.df)} months of data")
        print(f"   Date range: {self.df['Date'].min().strftime('%Y-%m')} to {self.df['Date'].max().strftime('%Y-%m')}")
        
        return self.df
    
    def calculate_returns(self):
        """Calculate various return periods"""
        print("\n📊 Calculating returns...")
        
        df = self.df.copy()
        
        # Monthly returns
        df['Mom_Ret_1M'] = df['Mom_Close'].pct_change() * 100
        df['Val_Ret_1M'] = df['Val_Close'].pct_change() * 100
        
        # Relative performance (momentum - value)
        df['Rel_Perf_1M'] = df['Mom_Ret_1M'] - df['Val_Ret_1M']
        
        # Rolling returns for different periods
        for months in [3, 6, 12, 24, 36]:
            df[f'Mom_Ret_{months}M'] = df['Mom_Close'].pct_change(months) * 100
            df[f'Val_Ret_{months}M'] = df['Val_Close'].pct_change(months) * 100
            df[f'Rel_Perf_{months}M'] = df[f'Mom_Ret_{months}M'] - df[f'Val_Ret_{months}M']
        
        # Cumulative relative performance
        df['Cum_Rel_Perf'] = df['Rel_Perf_1M'].cumsum()
        
        # Ratio
        df['Mom_Val_Ratio'] = df['Mom_Close'] / df['Val_Close']
        
        self.df = df
        print("✅ Returns calculated")
        
        return df
    
    def identify_outperformance_periods(self, threshold_months=6, threshold_pct=10):
        """
        Identify periods of significant outperformance.
        
        Args:
            threshold_months: Minimum duration of outperformance (default 6 months)
            threshold_pct: Minimum cumulative outperformance % (default 10%)
        
        Returns:
            DataFrames with momentum and value outperformance periods
        """
        print("\n" + "="*100)
        print(f"IDENTIFYING OUTPERFORMANCE PERIODS (>{threshold_pct}% over {threshold_months}+ months)")
        print("="*100)
        
        df = self.df.copy()
        
        # Calculate rolling outperformance
        df['Rolling_Rel_Perf_6M'] = df['Rel_Perf_1M'].rolling(threshold_months).sum()
        
        # Identify strong momentum periods (Mom >> Val)
        df['Strong_Mom'] = df['Rolling_Rel_Perf_6M'] > threshold_pct
        
        # Identify strong value periods (Val >> Mom)
        df['Strong_Val'] = df['Rolling_Rel_Perf_6M'] < -threshold_pct
        
        # Find regime changes (start of outperformance)
        df['Mom_Start'] = (df['Strong_Mom']) & (~df['Strong_Mom'].shift(1).fillna(False))
        df['Val_Start'] = (df['Strong_Val']) & (~df['Strong_Val'].shift(1).fillna(False))
        
        # Get periods
        mom_periods = df[df['Mom_Start']].copy()
        val_periods = df[df['Val_Start']].copy()
        
        print(f"\n📊 Found {len(mom_periods)} periods where Momentum strongly outperformed")
        print(f"📊 Found {len(val_periods)} periods where Value strongly outperformed")
        
        return mom_periods, val_periods
    
    def analyze_preconditions(self, periods_df, factor_name):
        """
        Analyze market conditions that preceded outperformance periods.
        
        Args:
            periods_df: DataFrame with outperformance start dates
            factor_name: 'Momentum' or 'Value'
        
        Returns:
            DataFrame with preconditions analysis
        """
        print("\n" + "="*100)
        print(f"ANALYZING PRECONDITIONS FOR {factor_name.upper()} OUTPERFORMANCE")
        print("="*100)
        
        if len(periods_df) == 0:
            print(f"⚠️  No {factor_name} outperformance periods found")
            return pd.DataFrame()
        
        results = []
        
        for idx, row in periods_df.iterrows():
            date = row['Date']
            
            # Get the row index
            row_idx = self.df[self.df['Date'] == date].index[0]
            
            # Get preconditions (6M, 1Y, 3Y returns BEFORE the outperformance started)
            if row_idx >= 36:  # Need at least 36 months of history
                precond = {
                    'Start_Date': date,
                    'Start_Date_Str': date.strftime('%Y-%m'),
                    
                    # Returns at the START of outperformance
                    'Mom_Ret_6M_Prior': self.df.loc[row_idx, 'Mom_Ret_6M'],
                    'Val_Ret_6M_Prior': self.df.loc[row_idx, 'Val_Ret_6M'],
                    'Rel_Perf_6M_Prior': self.df.loc[row_idx, 'Rel_Perf_6M'],
                    
                    'Mom_Ret_1Y_Prior': self.df.loc[row_idx, 'Mom_Ret_12M'],
                    'Val_Ret_1Y_Prior': self.df.loc[row_idx, 'Val_Ret_12M'],
                    'Rel_Perf_1Y_Prior': self.df.loc[row_idx, 'Rel_Perf_12M'],
                    
                    'Mom_Ret_3Y_Prior': self.df.loc[row_idx, 'Mom_Ret_36M'],
                    'Val_Ret_3Y_Prior': self.df.loc[row_idx, 'Val_Ret_36M'],
                    'Rel_Perf_3Y_Prior': self.df.loc[row_idx, 'Rel_Perf_36M'],
                    
                    # Ratio at start
                    'Mom_Val_Ratio': self.df.loc[row_idx, 'Mom_Val_Ratio'],
                    
                    # Subsequent performance (6M AFTER outperformance started)
                    'Mom_Ret_6M_After': self.df.loc[min(row_idx + 6, len(self.df)-1), 'Mom_Ret_6M'] if row_idx + 6 < len(self.df) else np.nan,
                    'Val_Ret_6M_After': self.df.loc[min(row_idx + 6, len(self.df)-1), 'Val_Ret_6M'] if row_idx + 6 < len(self.df) else np.nan,
                    'Rel_Perf_6M_After': self.df.loc[min(row_idx + 6, len(self.df)-1), 'Rel_Perf_6M'] if row_idx + 6 < len(self.df) else np.nan,
                }
                
                results.append(precond)
        
        results_df = pd.DataFrame(results)
        
        if len(results_df) > 0:
            print(f"\n✅ Analyzed {len(results_df)} {factor_name} outperformance periods")
            print(f"\nPeriods identified:")
            for _, row in results_df.iterrows():
                print(f"   • {row['Start_Date_Str']}")
        
        return results_df
    
    def display_preconditions_summary(self, mom_precond, val_precond):
        """Display summary statistics of preconditions"""
        print("\n" + "="*100)
        print("PRECONDITIONS SUMMARY")
        print("="*100)
        
        if len(mom_precond) > 0:
            print(f"\n🟢 MOMENTUM OUTPERFORMANCE PRECONDITIONS (n={len(mom_precond)})")
            print("-" * 100)
            print(f"\n{'Metric':<30} {'Mean':<12} {'Median':<12} {'Min':<12} {'Max':<12}")
            print("-" * 100)
            
            metrics = [
                ('6M Prior Mom Return', 'Mom_Ret_6M_Prior'),
                ('6M Prior Val Return', 'Val_Ret_6M_Prior'),
                ('6M Prior Rel Perf', 'Rel_Perf_6M_Prior'),
                ('1Y Prior Mom Return', 'Mom_Ret_1Y_Prior'),
                ('1Y Prior Val Return', 'Val_Ret_1Y_Prior'),
                ('1Y Prior Rel Perf', 'Rel_Perf_1Y_Prior'),
                ('3Y Prior Mom Return', 'Mom_Ret_3Y_Prior'),
                ('3Y Prior Val Return', 'Val_Ret_3Y_Prior'),
                ('3Y Prior Rel Perf', 'Rel_Perf_3Y_Prior'),
            ]
            
            for label, col in metrics:
                mean_val = mom_precond[col].mean()
                median_val = mom_precond[col].median()
                min_val = mom_precond[col].min()
                max_val = mom_precond[col].max()
                print(f"{label:<30} {mean_val:>11.2f}% {median_val:>11.2f}% {min_val:>11.2f}% {max_val:>11.2f}%")
        
        if len(val_precond) > 0:
            print(f"\n🔴 VALUE OUTPERFORMANCE PRECONDITIONS (n={len(val_precond)})")
            print("-" * 100)
            print(f"\n{'Metric':<30} {'Mean':<12} {'Median':<12} {'Min':<12} {'Max':<12}")
            print("-" * 100)
            
            for label, col in metrics:
                mean_val = val_precond[col].mean()
                median_val = val_precond[col].median()
                min_val = val_precond[col].min()
                max_val = val_precond[col].max()
                print(f"{label:<30} {mean_val:>11.2f}% {median_val:>11.2f}% {min_val:>11.2f}% {max_val:>11.2f}%")
    
    def derive_switching_rules(self, mom_precond, val_precond):
        """Derive actionable switching rules from the analysis"""
        print("\n" + "="*100)
        print("DERIVED SWITCHING RULES")
        print("="*100)
        
        if len(mom_precond) == 0 or len(val_precond) == 0:
            print("\n⚠️  Insufficient data to derive rules")
            return
        
        print("\n📋 RULE SET FOR FACTOR ROTATION")
        print("-" * 100)
        
        # Analyze momentum outperformance triggers
        print("\n🟢 MOMENTUM OUTPERFORMANCE TYPICALLY STARTS WHEN:")
        print()
        
        # 6M relative performance
        mom_6m_rel_mean = mom_precond['Rel_Perf_6M_Prior'].mean()
        mom_6m_rel_median = mom_precond['Rel_Perf_6M_Prior'].median()
        
        print(f"   1. 6-Month Relative Performance:")
        print(f"      • Mean: {mom_6m_rel_mean:+.2f}%")
        print(f"      • Median: {mom_6m_rel_median:+.2f}%")
        if mom_6m_rel_median < 0:
            print(f"      → Momentum tends to outperform AFTER underperforming")
        else:
            print(f"      → Momentum tends to outperform AFTER already leading")
        
        # 1Y relative performance
        mom_1y_rel_mean = mom_precond['Rel_Perf_1Y_Prior'].mean()
        mom_1y_rel_median = mom_precond['Rel_Perf_1Y_Prior'].median()
        
        print(f"\n   2. 1-Year Relative Performance:")
        print(f"      • Mean: {mom_1y_rel_mean:+.2f}%")
        print(f"      • Median: {mom_1y_rel_median:+.2f}%")
        
        # 3Y relative performance
        mom_3y_rel_mean = mom_precond['Rel_Perf_3Y_Prior'].mean()
        mom_3y_rel_median = mom_precond['Rel_Perf_3Y_Prior'].median()
        
        print(f"\n   3. 3-Year Relative Performance:")
        print(f"      • Mean: {mom_3y_rel_mean:+.2f}%")
        print(f"      • Median: {mom_3y_rel_median:+.2f}%")
        
        # Analyze value outperformance triggers
        print("\n\n🔴 VALUE OUTPERFORMANCE TYPICALLY STARTS WHEN:")
        print()
        
        # 6M relative performance
        val_6m_rel_mean = val_precond['Rel_Perf_6M_Prior'].mean()
        val_6m_rel_median = val_precond['Rel_Perf_6M_Prior'].median()
        
        print(f"   1. 6-Month Relative Performance:")
        print(f"      • Mean: {val_6m_rel_mean:+.2f}%")
        print(f"      • Median: {val_6m_rel_median:+.2f}%")
        if val_6m_rel_median > 0:
            print(f"      → Value tends to outperform AFTER momentum has been leading")
        else:
            print(f"      → Value tends to outperform AFTER already leading")
        
        # 1Y relative performance
        val_1y_rel_mean = val_precond['Rel_Perf_1Y_Prior'].mean()
        val_1y_rel_median = val_precond['Rel_Perf_1Y_Prior'].median()
        
        print(f"\n   2. 1-Year Relative Performance:")
        print(f"      • Mean: {val_1y_rel_mean:+.2f}%")
        print(f"      • Median: {val_1y_rel_median:+.2f}%")
        
        # 3Y relative performance
        val_3y_rel_mean = val_precond['Rel_Perf_3Y_Prior'].mean()
        val_3y_rel_median = val_precond['Rel_Perf_3Y_Prior'].median()
        
        print(f"\n   3. 3-Year Relative Performance:")
        print(f"      • Mean: {val_3y_rel_mean:+.2f}%")
        print(f"      • Median: {val_3y_rel_median:+.2f}%")
        
        # Derive specific thresholds
        print("\n\n" + "="*100)
        print("ACTIONABLE TRADING RULES")
        print("="*100)
        
        print("\n✅ RULE 1: Switch to VALUE when:")
        val_6m_threshold = val_precond['Rel_Perf_6M_Prior'].quantile(0.25)
        val_1y_threshold = val_precond['Rel_Perf_1Y_Prior'].quantile(0.25)
        
        print(f"   • 6M Relative Performance > {val_6m_threshold:.1f}% (Momentum has been leading)")
        print(f"   • AND 1Y Relative Performance > {val_1y_threshold:.1f}%")
        print(f"   → This signals momentum exhaustion, value likely to catch up")
        
        print("\n✅ RULE 2: Stay in MOMENTUM when:")
        mom_6m_threshold = mom_precond['Rel_Perf_6M_Prior'].quantile(0.75)
        mom_1y_threshold = mom_precond['Rel_Perf_1Y_Prior'].quantile(0.75)
        
        print(f"   • 6M Relative Performance < {mom_6m_threshold:.1f}%")
        print(f"   • OR 1Y Relative Performance < {mom_1y_threshold:.1f}%")
        print(f"   → Momentum continues to dominate")
        
        # Mean reversion analysis
        print("\n\n" + "="*100)
        print("MEAN REVERSION ANALYSIS")
        print("="*100)
        
        print("\n📊 Key Insight:")
        if val_6m_rel_median > 0:
            print("   • Value outperformance tends to follow periods of MOMENTUM strength")
            print("   • This suggests MEAN REVERSION behavior")
            print("   • Strategy: Tilt to Value after extended Momentum runs")
        else:
            print("   • Value outperformance tends to follow periods of VALUE strength")
            print("   • This suggests MOMENTUM CONTINUATION behavior")
            print("   • Strategy: Stay with the trend")
        
        # Return the rules as a dictionary
        rules = {
            'switch_to_value': {
                '6m_rel_perf_threshold': val_6m_threshold,
                '1y_rel_perf_threshold': val_1y_threshold,
                'description': 'Switch to Value when Momentum has been leading'
            },
            'stay_momentum': {
                '6m_rel_perf_threshold': mom_6m_threshold,
                '1y_rel_perf_threshold': mom_1y_threshold,
                'description': 'Stay in Momentum when it continues to dominate'
            }
        }
        
        return rules
    
    def create_visualizations(self, mom_precond, val_precond):
        """Create visualizations of outperformance periods"""
        print("\n📊 Creating visualizations...")
        
        fig = plt.figure(figsize=(18, 12))
        gs = fig.add_gridspec(4, 2, hspace=0.3, wspace=0.3)
        
        # 1. Relative performance over time with markers
        ax1 = fig.add_subplot(gs[0, :])
        ax1.plot(self.df['Date'], self.df['Rel_Perf_6M'], linewidth=1.5, alpha=0.8, label='6M Relative Performance')
        ax1.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        ax1.axhline(y=10, color='green', linestyle=':', linewidth=1, alpha=0.5, label='Mom outperformance threshold')
        ax1.axhline(y=-10, color='red', linestyle=':', linewidth=1, alpha=0.5, label='Val outperformance threshold')
        
        # Mark momentum outperformance starts
        if len(mom_precond) > 0:
            ax1.scatter(mom_precond['Start_Date'], [10]*len(mom_precond), 
                       color='green', s=100, marker='^', zorder=5, label='Mom outperformance starts')
        
        # Mark value outperformance starts
        if len(val_precond) > 0:
            ax1.scatter(val_precond['Start_Date'], [-10]*len(val_precond), 
                       color='red', s=100, marker='v', zorder=5, label='Val outperformance starts')
        
        ax1.set_title('6-Month Relative Performance (Momentum - Value) with Outperformance Periods', 
                     fontsize=14, fontweight='bold')
        ax1.set_xlabel('Date', fontsize=12)
        ax1.set_ylabel('Relative Performance (%)', fontsize=12)
        ax1.legend(loc='best', fontsize=9)
        ax1.grid(True, alpha=0.3)
        
        # 2. Preconditions distribution - 6M
        ax2 = fig.add_subplot(gs[1, 0])
        if len(mom_precond) > 0:
            ax2.hist(mom_precond['Rel_Perf_6M_Prior'], bins=10, alpha=0.6, color='green', 
                    label=f'Mom (n={len(mom_precond)})', edgecolor='black')
        if len(val_precond) > 0:
            ax2.hist(val_precond['Rel_Perf_6M_Prior'], bins=10, alpha=0.6, color='red', 
                    label=f'Val (n={len(val_precond)})', edgecolor='black')
        ax2.axvline(x=0, color='black', linestyle='--', linewidth=1)
        ax2.set_title('6M Prior Relative Performance Distribution', fontsize=12, fontweight='bold')
        ax2.set_xlabel('6M Relative Performance (%)', fontsize=10)
        ax2.set_ylabel('Frequency', fontsize=10)
        ax2.legend()
        ax2.grid(True, alpha=0.3)
        
        # 3. Preconditions distribution - 1Y
        ax3 = fig.add_subplot(gs[1, 1])
        if len(mom_precond) > 0:
            ax3.hist(mom_precond['Rel_Perf_1Y_Prior'], bins=10, alpha=0.6, color='green', 
                    label=f'Mom (n={len(mom_precond)})', edgecolor='black')
        if len(val_precond) > 0:
            ax3.hist(val_precond['Rel_Perf_1Y_Prior'], bins=10, alpha=0.6, color='red', 
                    label=f'Val (n={len(val_precond)})', edgecolor='black')
        ax3.axvline(x=0, color='black', linestyle='--', linewidth=1)
        ax3.set_title('1Y Prior Relative Performance Distribution', fontsize=12, fontweight='bold')
        ax3.set_xlabel('1Y Relative Performance (%)', fontsize=10)
        ax3.set_ylabel('Frequency', fontsize=10)
        ax3.legend()
        ax3.grid(True, alpha=0.3)
        
        # 4. Preconditions distribution - 3Y
        ax4 = fig.add_subplot(gs[2, 0])
        if len(mom_precond) > 0:
            ax4.hist(mom_precond['Rel_Perf_3Y_Prior'], bins=10, alpha=0.6, color='green', 
                    label=f'Mom (n={len(mom_precond)})', edgecolor='black')
        if len(val_precond) > 0:
            ax4.hist(val_precond['Rel_Perf_3Y_Prior'], bins=10, alpha=0.6, color='red', 
                    label=f'Val (n={len(val_precond)})', edgecolor='black')
        ax4.axvline(x=0, color='black', linestyle='--', linewidth=1)
        ax4.set_title('3Y Prior Relative Performance Distribution', fontsize=12, fontweight='bold')
        ax4.set_xlabel('3Y Relative Performance (%)', fontsize=10)
        ax4.set_ylabel('Frequency', fontsize=10)
        ax4.legend()
        ax4.grid(True, alpha=0.3)
        
        # 5. Box plots comparison
        ax5 = fig.add_subplot(gs[2, 1])
        
        data_to_plot = []
        labels = []
        
        if len(mom_precond) > 0:
            data_to_plot.extend([mom_precond['Rel_Perf_6M_Prior'], 
                                mom_precond['Rel_Perf_1Y_Prior'],
                                mom_precond['Rel_Perf_3Y_Prior']])
            labels.extend(['Mom\n6M', 'Mom\n1Y', 'Mom\n3Y'])
        
        if len(val_precond) > 0:
            data_to_plot.extend([val_precond['Rel_Perf_6M_Prior'], 
                                val_precond['Rel_Perf_1Y_Prior'],
                                val_precond['Rel_Perf_3Y_Prior']])
            labels.extend(['Val\n6M', 'Val\n1Y', 'Val\n3Y'])
        
        bp = ax5.boxplot(data_to_plot, labels=labels, patch_artist=True)
        
        # Color the boxes
        colors = ['green', 'green', 'green', 'red', 'red', 'red']
        for patch, color in zip(bp['boxes'], colors[:len(bp['boxes'])]):
            patch.set_facecolor(color)
            patch.set_alpha(0.6)
        
        ax5.axhline(y=0, color='black', linestyle='--', linewidth=1)
        ax5.set_title('Prior Relative Performance Box Plots', fontsize=12, fontweight='bold')
        ax5.set_ylabel('Relative Performance (%)', fontsize=10)
        ax5.grid(True, alpha=0.3, axis='y')
        
        # 6. Cumulative relative performance
        ax6 = fig.add_subplot(gs[3, :])
        ax6.plot(self.df['Date'], self.df['Cum_Rel_Perf'], linewidth=1.5, alpha=0.8)
        ax6.axhline(y=0, color='black', linestyle='--', linewidth=1, alpha=0.5)
        
        # Mark outperformance starts
        if len(mom_precond) > 0:
            for _, row in mom_precond.iterrows():
                idx = self.df[self.df['Date'] == row['Start_Date']].index[0]
                ax6.axvline(x=row['Start_Date'], color='green', linestyle=':', alpha=0.3)
        
        if len(val_precond) > 0:
            for _, row in val_precond.iterrows():
                idx = self.df[self.df['Date'] == row['Start_Date']].index[0]
                ax6.axvline(x=row['Start_Date'], color='red', linestyle=':', alpha=0.3)
        
        ax6.set_title('Cumulative Relative Performance (Momentum - Value)', fontsize=14, fontweight='bold')
        ax6.set_xlabel('Date', fontsize=12)
        ax6.set_ylabel('Cumulative Relative Performance (%)', fontsize=12)
        ax6.grid(True, alpha=0.3)
        
        plt.suptitle('Factor Outperformance Analysis', fontsize=16, fontweight='bold', y=0.995)
        
        # Save
        output_file = self.output_folder / "factor_outperformance_analysis.png"
        plt.savefig(output_file, dpi=300, bbox_inches='tight')
        print(f"✅ Saved visualization: {output_file}")
        plt.close()
    
    def run_analysis(self):
        """Run complete outperformance analysis"""
        # Load and prepare data
        self.load_data()
        self.calculate_returns()
        
        # Identify outperformance periods
        mom_periods, val_periods = self.identify_outperformance_periods(
            threshold_months=6, 
            threshold_pct=10
        )
        
        # Analyze preconditions
        mom_precond = self.analyze_preconditions(mom_periods, 'Momentum')
        val_precond = self.analyze_preconditions(val_periods, 'Value')
        
        # Display summary
        self.display_preconditions_summary(mom_precond, val_precond)
        
        # Derive rules
        rules = self.derive_switching_rules(mom_precond, val_precond)
        
        # Create visualizations
        self.create_visualizations(mom_precond, val_precond)
        
        # Save detailed results
        if len(mom_precond) > 0:
            mom_file = self.output_folder / "monthly" / "momentum_outperformance_periods.csv"
            mom_precond.to_csv(mom_file, index=False)
            print(f"\n✅ Saved momentum periods: {mom_file}")
        
        if len(val_precond) > 0:
            val_file = self.output_folder / "monthly" / "value_outperformance_periods.csv"
            val_precond.to_csv(val_file, index=False)
            print(f"✅ Saved value periods: {val_file}")
        
        print("\n" + "="*100)
        print("✅ ANALYSIS COMPLETE")
        print("="*100)
        print()
        
        return mom_precond, val_precond, rules


def main():
    """Main execution"""
    data_folder = Path(__file__).parent.parent / "data"
    analyzer = FactorOutperformanceAnalyzer(data_folder)
    
    mom_precond, val_precond, rules = analyzer.run_analysis()


if __name__ == "__main__":
    main()
