"""
Quarterly Alpha Rotation Strategy (100/0)
Dynamic allocation between Momentum 30 and Value 30 based on quarterly relative momentum

Strategy: Institutional-style factor rotation
- 6M relative momentum signal (raw, no MA smoothing)
- Decisions only at quarter boundaries (calendar is the smoother)
- 100/0 hard allocation (momentum or value, no neutral)
- 1-month execution delay (no lookahead bias)
- No hysteresis, no cooldown — quarterly frequency does the filtering
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


class PortfolioStrategy:
    def __init__(self, data_folder, monthly_sip=10000):
        self.data_folder = Path(data_folder)
        self.monthly_sip = monthly_sip
        self.output_folder = self.data_folder.parent / "output" / "monthly"
        
    def load_monthly_data(self):
        """Load pre-generated monthly data for both indices"""
        print("\n" + "="*80)
        print("QUARTERLY ALPHA ROTATION STRATEGY (100/0)")
        print("="*80)
        print("\n📂 Loading monthly index data...")
        
        # Load momentum data
        mom_file = self.output_folder / "nifty200_momentum_30_monthly.csv"
        mom_df = pd.read_csv(mom_file)
        mom_df['Date'] = pd.to_datetime(mom_df['Date'])
        mom_df = mom_df.rename(columns={'Close': 'Close_mom'})
        
        # Load value data
        val_file = self.output_folder / "nifty200_value_30_monthly.csv"
        val_df = pd.read_csv(val_file)
        val_df['Date'] = pd.to_datetime(val_df['Date'])
        val_df = val_df.rename(columns={'Close': 'Close_val'})
        
        # Merge on date
        merged = pd.merge(mom_df[['Date', 'Close_mom']], 
                         val_df[['Date', 'Close_val']], 
                         on='Date', how='inner')
        
        print(f"✅ Loaded {len(merged)} months of data")
        print(f"   Date range: {merged['Date'].min().strftime('%Y-%m')} to {merged['Date'].max().strftime('%Y-%m')}")
        
        return merged
    
    def calculate_returns(self, df):
        """Calculate monthly returns for both indices"""
        df['Return_mom'] = df['Close_mom'].pct_change()
        df['Return_val'] = df['Close_val'].pct_change()
        
        # Calculate ratio for reference
        df['Ratio'] = df['Close_mom'] / df['Close_val']
        
        return df

    def calculate_portfolio_returns(self, df):
        """Calculate portfolio returns based on dynamic weights"""
        df['Portfolio_Return'] = (
            df['w_mom'] * df['Return_mom'] + 
            df['w_val'] * df['Return_val']
        )
        
        # Build portfolio NAV (starting at 1000 to match indices)
        df['Portfolio_NAV'] = 1000 * (1 + df['Portfolio_Return']).cumprod()
        
        # Handle first row (NaN return)
        df.loc[0, 'Portfolio_NAV'] = 1000
        
        return df
    
    def run_sip_on_portfolio(self, df, strategy_name):
        """Run SIP analysis on the constructed portfolio NAV"""
        print(f"\n🎯 Running SIP analysis for: {strategy_name}")
        
        # Prepare data for SIP calculation
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
        
        # Calculate investor drawdown (on invested capital)
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
        
        # MAR (XIRR / abs(MaxDD))
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
        """Run Quarterly Alpha Rotation strategy
        
        Institutional-style factor rotation:
        - 6M relative momentum signal (no MA, no hysteresis)
        - Decisions only at quarter boundaries
        - 100/0 hard allocation (momentum or value)
        - 1-month execution delay (no lookahead)
        - Calendar acts as the smoother
        """
        print("\n" + "="*80)
        print("BACKTESTING: QUARTERLY ALPHA ROTATION (100/0)")
        print("="*80)
        
        # Load data
        df = self.load_monthly_data()
        df = self.calculate_returns(df)
        
        # STEP 1 — Quarterly decision grid
        df['Quarter'] = df['Date'].dt.to_period('Q')
        
        # STEP 2 — 6M relative momentum signal (raw, no MA smoothing)
        df['RelMom_6M'] = (
            df['Close_mom'].pct_change(6) -
            df['Close_val'].pct_change(6)
        )
        
        # STEP 3 — Sample ONLY quarter ends
        quarterly = df.groupby('Quarter').last()
        
        # STEP 4 — 100/0 regime selection (no neutral, hard switch)
        quarterly['regime'] = np.where(
            quarterly['RelMom_6M'] > 0,
            'momentum',
            'value'
        )
        
        # STEP 5 — Forward fill regime to monthly rows
        df = df.merge(
            quarterly[['regime']],
            left_on='Quarter',
            right_index=True,
            how='left'
        )
        df['regime'] = df['regime'].ffill()
        
        # STEP 6 — Execute next month (no lookahead)
        df['regime'] = df['regime'].shift(1).fillna('value')
        
        # STEP 7 — Set weights based on regime
        df['w_mom'] = np.where(df['regime'] == 'momentum', 1.0, 0.0)
        df['w_val'] = 1.0 - df['w_mom']
        
        # STEP 8 — Portfolio returns
        df = self.calculate_portfolio_returns(df)
        
        # Print regime summary
        regime_counts = df['regime'].value_counts()
        total = len(df)
        print(f"\n📊 Regime Distribution:")
        for regime, count in regime_counts.items():
            print(f"   {regime:>10s}: {count:3d} months ({count/total*100:.1f}%)")
        
        # Count regime switches
        switches = (df['regime'] != df['regime'].shift(1)).sum() - 1
        print(f"   Switches:  {switches}")
        
        print("\n✅ Strategy calculations complete")
        
        # Run SIP analysis
        results, sip_data = self.run_sip_on_portfolio(df, 'Quarterly Alpha Rotation 100/0')
        
        # Save portfolio data (keep filename for dashboard compatibility)
        output_file = self.output_folder / "portfolio_ratio_trend_75_25.csv"
        df.to_csv(output_file, index=False)
        print(f"\n✅ Saved portfolio to: {output_file}")
        
        return results, df, sip_data
    
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
        print("="*80)

def main():
    """
    Main execution function - Quarterly Alpha Rotation strategy
    """
    # Initialize strategy
    data_folder = Path(__file__).parent.parent / "data"
    strategy = PortfolioStrategy(data_folder, monthly_sip=10000)
    
    # Run the strategy
    results, portfolio_df, sip_df = strategy.run_strategy()
    
    # Display results
    strategy.display_results(results)
    
    print("\n" + "="*80)
    print("✅ STRATEGY COMPLETE")
    print("="*80)
    print("\n")

if __name__ == "__main__":
    main()
