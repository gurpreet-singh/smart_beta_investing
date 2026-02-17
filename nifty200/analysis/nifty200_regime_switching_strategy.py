"""
Regime-Based Switching Strategy
Dynamic allocation between Momentum 30 and Value 30 based on regime detection

Strategy: Data-driven regime rotation
- Uses Mom/Val ratio vs 26-week MA for regime detection
- 8-week momentum return filter to avoid whipsaws
- Switches between momentum-dominant and balanced allocations
- Weekly signal calculation, monthly execution
- Tracks regime time, switches, and performance

Based on correlation analysis showing:
- High positive correlation (0.78) between Mom and Val
- Clear regime rotation with 0.62% weekly benefit during switches
- Value outperforms when ratio < 26W MA and momentum weak
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def calculate_xirr(cash_flows, guess=0.1):
    """Calculate XIRR (Extended Internal Rate of Return) using Newton-Raphson method
    
    Args:
        cash_flows: List of tuples (date, amount) where amount is negative for investments
    """
    from datetime import datetime
    from scipy.optimize import newton
    
    # Sort by date
    cash_flows = sorted(cash_flows, key=lambda x: x[0])
    
    # Start date
    start_date = cash_flows[0][0]
    
    # Convert to days from start
    amounts = []
    days = []
    for date, amount in cash_flows:
        days.append((date - start_date).days)
        amounts.append(amount)
    
    # XIRR function (NPV at rate r)
    def xnpv(rate):
        return sum([amount / (1 + rate) ** (day / 365.0) for amount, day in zip(amounts, days)])
    
    # Derivative for Newton-Raphson
    def xnpv_deriv(rate):
        return sum([-amount * day / 365.0 / (1 + rate) ** (day / 365.0 + 1) for amount, day in zip(amounts, days)])
    
    try:
        rate = newton(xnpv, guess, fprime=xnpv_deriv, maxiter=100)
        return rate * 100  # Convert to percentage
    except:
        return 0.0


class RegimeSwitchingStrategy:
    def __init__(self, data_folder, monthly_sip=10000):
        self.data_folder = Path(data_folder)
        self.monthly_sip = monthly_sip
        self.output_folder = self.data_folder.parent / "output"
        
    def load_weekly_data(self):
        """Load weekly momentum/value ratio data"""
        print("\n" + "="*80)
        print("REGIME-BASED SWITCHING STRATEGY")
        print("="*80)
        print("\n📂 Loading weekly ratio data...")
        
        # Load weekly ratio data
        ratio_file = self.output_folder / "weekly" / "nifty200_momentum_value_ratio_weekly.csv"
        weekly_df = pd.read_csv(ratio_file, parse_dates=['Date'])
        
        print(f"✅ Loaded {len(weekly_df)} weeks of data")
        print(f"   Date range: {weekly_df['Date'].min().strftime('%Y-%m-%d')} to {weekly_df['Date'].max().strftime('%Y-%m-%d')}")
        
        return weekly_df
    
    def load_monthly_data(self):
        """Load monthly momentum and value data"""
        print("\n📂 Loading monthly index data...")
        
        # Load momentum data
        mom_file = self.output_folder / "monthly" / "nifty200_momentum_30_monthly.csv"
        mom_df = pd.read_csv(mom_file, parse_dates=['Date'])
        mom_df = mom_df.rename(columns={'Close': 'Close_mom'})
        
        # Load value data
        val_file = self.output_folder / "monthly" / "nifty200_value_30_monthly.csv"
        val_df = pd.read_csv(val_file, parse_dates=['Date'])
        val_df = val_df.rename(columns={'Close': 'Close_val'})
        
        # Merge on date
        monthly_df = pd.merge(mom_df[['Date', 'Close_mom']], 
                             val_df[['Date', 'Close_val']], 
                             on='Date', how='inner')
        
        print(f"✅ Loaded {len(monthly_df)} months of data")
        print(f"   Date range: {monthly_df['Date'].min().strftime('%Y-%m')} to {monthly_df['Date'].max().strftime('%Y-%m')}")
        
        return monthly_df
    
    def calculate_regime_signals(self, weekly_df, ma_window=26, lookback_8w=8):
        """
        Calculate regime switching signals based on:
        1. Mom/Val ratio vs 26-week MA
        2. 8-week momentum return
        
        Args:
            weekly_df: Weekly data with momentum and value prices
            ma_window: Moving average window (default 26 weeks)
            lookback_8w: Lookback for momentum return (default 8 weeks)
        
        Returns:
            DataFrame with regime signals
        """
        print("\n" + "="*80)
        print("CALCULATING REGIME SIGNALS")
        print("="*80)
        
        df = weekly_df.copy()
        
        # Calculate ratio and its MA
        df['Ratio'] = df['Momentum_Close'] / df['Value_Close']
        df['Ratio_MA'] = df['Ratio'].rolling(ma_window).mean()
        
        # Calculate 8-week momentum return
        df['Mom_8W_Return'] = df['Momentum_Close'].pct_change(lookback_8w) * 100
        
        # Define regime conditions
        # Switch to VALUE when:
        # 1. Momentum 8W return < 0% (momentum is weak)
        # 2. Ratio < 26W MA (value regime is active)
        df['condition_1'] = df['Mom_8W_Return'] < 0
        df['condition_2'] = df['Ratio'] < df['Ratio_MA']
        
        # Regime signal
        df['switch_to_value'] = df['condition_1'] & df['condition_2']
        df['regime'] = np.where(df['switch_to_value'], 'value', 'momentum')
        
        print(f"\n📊 Regime Signal Statistics:")
        print(f"   Total weeks analyzed: {len(df.dropna())}")
        print(f"   Condition 1 (Mom 8W < 0%): {df['condition_1'].sum()} weeks")
        print(f"   Condition 2 (Ratio < MA): {df['condition_2'].sum()} weeks")
        print(f"   Both conditions met: {df['switch_to_value'].sum()} weeks")
        
        return df
    
    def apply_monthly_allocation(self, weekly_df, monthly_df):
        """
        Apply regime-based allocation to monthly returns.
        
        Allocation strategy:
        - Momentum regime: 75% Momentum / 25% Value (momentum-dominant)
        - Value regime: 50% Momentum / 50% Value (balanced)
        
        Args:
            weekly_df: Weekly data with regime signals
            monthly_df: Monthly price data
        
        Returns:
            DataFrame with monthly allocations and returns
        """
        print("\n" + "="*80)
        print("APPLYING MONTHLY ALLOCATION")
        print("="*80)
        
        # Calculate monthly returns
        monthly_df['Return_mom'] = monthly_df['Close_mom'].pct_change()
        monthly_df['Return_val'] = monthly_df['Close_val'].pct_change()
        monthly_df['Ratio'] = monthly_df['Close_mom'] / monthly_df['Close_val']
        
        # For each month, use the regime signal from the last week of the PREVIOUS month
        # This ensures no lookahead bias
        
        # Get end-of-month dates from monthly data
        monthly_df['YearMonth'] = monthly_df['Date'].dt.to_period('M')
        
        # Get regime signal from weekly data at end of each month
        weekly_df['YearMonth'] = weekly_df['Date'].dt.to_period('M')
        
        # Get last week's regime for each month
        monthly_regime = weekly_df.groupby('YearMonth').last()[['regime', 'switch_to_value']].reset_index()
        
        # Merge regime to monthly data
        monthly_df = monthly_df.merge(monthly_regime, on='YearMonth', how='left')
        
        # Shift regime by 1 month to avoid lookahead bias
        # End-of-month regime determines NEXT month's allocation
        monthly_df['regime'] = monthly_df['regime'].shift(1)
        monthly_df['switch_to_value'] = monthly_df['switch_to_value'].shift(1)
        
        # Fill first month with momentum regime (default)
        monthly_df['regime'] = monthly_df['regime'].fillna('momentum')
        monthly_df['switch_to_value'] = monthly_df['switch_to_value'].fillna(False)
        
        # Define allocations based on regime
        # Momentum regime: 75/25 (momentum-dominant)
        # Value regime: 50/50 (balanced)
        monthly_df['w_mom'] = np.where(
            monthly_df['regime'] == 'momentum',
            0.75,  # Momentum-dominant
            0.50   # Balanced
        )
        monthly_df['w_val'] = 1.0 - monthly_df['w_mom']
        
        # Calculate portfolio returns
        monthly_df['Portfolio_Return'] = (
            monthly_df['w_mom'] * monthly_df['Return_mom'] + 
            monthly_df['w_val'] * monthly_df['Return_val']
        )
        
        # Build portfolio NAV (starting at 1000)
        monthly_df['Portfolio_NAV'] = 1000 * (1 + monthly_df['Portfolio_Return']).cumprod()
        monthly_df.loc[0, 'Portfolio_NAV'] = 1000
        
        # Calculate regime statistics
        regime_counts = monthly_df['regime'].value_counts()
        total_months = len(monthly_df)
        
        print(f"\n📊 Regime Distribution (Monthly):")
        for regime, count in regime_counts.items():
            print(f"   {regime.capitalize():\u003e10s}: {count:3d} months ({count/total_months*100:.1f}%)")
        
        # Count switches
        switches = (monthly_df['regime'] != monthly_df['regime'].shift(1)).sum() - 1
        print(f"   Switches:  {switches} times")
        
        # Average allocation
        print(f"\n📊 Average Allocation:")
        print(f"   Momentum: {monthly_df['w_mom'].mean()*100:.1f}%")
        print(f"   Value:    {monthly_df['w_val'].mean()*100:.1f}%")
        
        # Time in each allocation
        alloc_75_25 = (monthly_df['w_mom'] == 0.75).sum()
        alloc_50_50 = (monthly_df['w_mom'] == 0.50).sum()
        
        print(f"\n📊 Time in Each Allocation:")
        print(f"   75/25 (Momentum-dominant): {alloc_75_25} months ({alloc_75_25/total_months*100:.1f}%)")
        print(f"   50/50 (Balanced):          {alloc_50_50} months ({alloc_50_50/total_months*100:.1f}%)")
        
        return monthly_df, switches
    
    def run_sip_analysis(self, df, strategy_name):
        """Run SIP analysis on the portfolio"""
        print(f"\n🎯 Running SIP analysis for: {strategy_name}")
        
        # Prepare data
        sip_data = df[['Date', 'Portfolio_NAV']].copy()
        sip_data = sip_data.rename(columns={'Portfolio_NAV': 'NAV'})
        sip_data = sip_data.dropna()
        
        # Calculate SIP metrics
        sip_data['Units_Bought'] = self.monthly_sip / sip_data['NAV']
        sip_data['Cumulative_Units'] = sip_data['Units_Bought'].cumsum()
        sip_data['Total_Invested'] = self.monthly_sip * (sip_data.index + 1)
        sip_data['Portfolio_Value'] = sip_data['Cumulative_Units'] * sip_data['NAV']
        
        # Calculate drawdowns
        sip_data['Peak_Portfolio_Value'] = sip_data['Portfolio_Value'].cummax()
        sip_data['Drawdown_Pct'] = (
            (sip_data['Portfolio_Value'] - sip_data['Peak_Portfolio_Value']) / 
            sip_data['Peak_Portfolio_Value'] * 100
        )
        
        # Calculate investor drawdown
        sip_data['Investor_Drawdown_Pct'] = (
            (sip_data['Portfolio_Value'] - sip_data['Total_Invested']) / 
            sip_data['Total_Invested'] * 100
        )
        
        # Final metrics
        total_invested = sip_data['Total_Invested'].iloc[-1]
        final_value = sip_data['Portfolio_Value'].iloc[-1]
        absolute_gain = final_value - total_invested
        total_return_pct = (absolute_gain / total_invested) * 100
        max_drawdown = sip_data['Drawdown_Pct'].min()
        max_investor_dd = sip_data['Investor_Drawdown_Pct'].min()
        
        # Calculate XIRR
        cash_flows = []
        for idx, row in sip_data.iterrows():
            cash_flows.append((row['Date'], -self.monthly_sip))
        cash_flows.append((sip_data['Date'].iloc[-1], final_value))
        
        sip_xirr = calculate_xirr(cash_flows)
        
        # Index CAGR
        start_nav = sip_data['NAV'].iloc[0]
        end_nav = sip_data['NAV'].iloc[-1]
        years = len(sip_data) / 12
        index_cagr = ((end_nav / start_nav) ** (1 / years) - 1) * 100
        
        # MAR ratio
        mar_ratio = sip_xirr / abs(max_drawdown) if max_drawdown != 0 else 0
        
        results = {
            'strategy_name': strategy_name,
            'sip_xirr': sip_xirr,
            'index_cagr': index_cagr,
            'total_return_pct': total_return_pct,
            'total_invested': total_invested,
            'final_value': final_value,
            'absolute_gain': absolute_gain,
            'max_drawdown': max_drawdown,
            'max_investor_drawdown': max_investor_dd,
            'mar_ratio': mar_ratio,
            'num_months': len(sip_data),
            'start_nav': start_nav,
            'end_nav': end_nav
        }
        
        return results, sip_data
    
    def run_strategy(self):
        """Run the complete regime-based switching strategy"""
        # Load data
        weekly_df = self.load_weekly_data()
        monthly_df = self.load_monthly_data()
        
        # Calculate regime signals on weekly data
        weekly_df = self.calculate_regime_signals(weekly_df, ma_window=26, lookback_8w=8)
        
        # Apply monthly allocation based on regime
        monthly_df, num_switches = self.apply_monthly_allocation(weekly_df, monthly_df)
        
        # Run SIP analysis
        results, sip_data = self.run_sip_analysis(monthly_df, 'Regime-Based Switching (75/25 → 50/50)')
        
        # Add switch count to results
        results['num_switches'] = num_switches
        
        # Save portfolio data
        output_file = self.output_folder / "monthly" / "portfolio_regime_switching.csv"
        monthly_df.to_csv(output_file, index=False)
        print(f"\n✅ Saved portfolio to: {output_file}")
        
        return results, monthly_df, sip_data, weekly_df
    
    def display_results(self, results):
        """Display strategy performance results"""
        print("\n" + "="*80)
        print("STRATEGY PERFORMANCE RESULTS")
        print("="*80)
        
        print(f"\n🏆 {results['strategy_name']}")
        print("-" * 80)
        print(f"   SIP XIRR:          {results['sip_xirr']:.2f}%")
        print(f"   Index CAGR:        {results['index_cagr']:.2f}%")
        print(f"   Total Invested:    ₹{results['total_invested']:,.0f}")
        print(f"   Final Value:       ₹{results['final_value']:,.0f}")
        print(f"   Absolute Gain:     ₹{results['absolute_gain']:,.0f}")
        print(f"   Total Return:      {results['total_return_pct']:.2f}%")
        print(f"   Max Drawdown:      {results['max_drawdown']:.2f}%")
        print(f"   Max Investor DD:   {results['max_investor_drawdown']:.2f}%")
        print(f"   MAR Ratio:         {results['mar_ratio']:.2f}")
        print(f"   Number of Switches: {results['num_switches']}")
        print("="*80)
    
    def compare_with_baseline(self, results):
        """Compare regime switching with pure momentum baseline"""
        print("\n" + "="*80)
        print("COMPARISON WITH BASELINE STRATEGIES")
        print("="*80)
        
        # Load pure momentum data for comparison
        mom_file = self.output_folder / "monthly" / "nifty200_momentum_30_monthly.csv"
        mom_df = pd.read_csv(mom_file, parse_dates=['Date'])
        
        # Calculate pure momentum CAGR
        start_price = mom_df['Close'].iloc[0]
        end_price = mom_df['Close'].iloc[-1]
        years = len(mom_df) / 12
        mom_cagr = ((end_price / start_price) ** (1 / years) - 1) * 100
        
        # Load pure value data
        val_file = self.output_folder / "monthly" / "nifty200_value_30_monthly.csv"
        val_df = pd.read_csv(val_file, parse_dates=['Date'])
        
        # Calculate pure value CAGR
        start_price_val = val_df['Close'].iloc[0]
        end_price_val = val_df['Close'].iloc[-1]
        val_cagr = ((end_price_val / start_price_val) ** (1 / years) - 1) * 100
        
        print(f"\n📊 CAGR Comparison:")
        print(f"   Pure Momentum (100/0):        {mom_cagr:.2f}%")
        print(f"   Pure Value (0/100):           {val_cagr:.2f}%")
        print(f"   Regime Switching (75/25→50/50): {results['index_cagr']:.2f}%")
        print()
        print(f"   Outperformance vs Momentum:   {results['index_cagr'] - mom_cagr:+.2f}%")
        print(f"   Outperformance vs Value:      {results['index_cagr'] - val_cagr:+.2f}%")
        
        return {
            'mom_cagr': mom_cagr,
            'val_cagr': val_cagr,
            'regime_cagr': results['index_cagr']
        }


def main():
    """Main execution function"""
    # Initialize strategy
    data_folder = Path(__file__).parent.parent / "data"
    strategy = RegimeSwitchingStrategy(data_folder, monthly_sip=10000)
    
    # Run the strategy
    results, portfolio_df, sip_df, weekly_df = strategy.run_strategy()
    
    # Display results
    strategy.display_results(results)
    
    # Compare with baseline
    comparison = strategy.compare_with_baseline(results)
    
    print("\n" + "="*80)
    print("✅ REGIME-BASED SWITCHING STRATEGY COMPLETE")
    print("="*80)
    print("\n")


if __name__ == "__main__":
    main()
