"""
Dual-Factor Rotation Strategy - RATIO TREND (OPTIMAL)
Dynamic allocation between Momentum 30 and Value 30 based on ratio trend
Always invested, no cash - optimal risk-adjusted returns

Strategy: Ratio Trend 75/25 with 2-Month Cooldown + 50/50 Transition
- Compares Momentum/Value ratio to its 6-month moving average
- If ratio > MA: 75% Momentum, 25% Value
- If ratio < MA: 25% Momentum, 75% Value
- After a switch, next full switch only after 2 months
- During cooldown, if signal disagrees: 50/50 allocation
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
        print("DUAL-FACTOR ROTATION STRATEGY - RATIO TREND")
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
        
        # Calculate ratio for signals
        df['Ratio'] = df['Close_mom'] / df['Close_val']
        
        return df
    
    def signal_ratio_trend(self, df, ma_length=6):
        """Ratio Trend Signal (OPTIMAL)
        
        Favors Momentum when ratio is above its moving average
        Natural whipsaw protection from MA smoothing
        """
        df['Ratio_MA'] = df['Ratio'].rolling(ma_length).mean()
        df['Signal_Ratio'] = df['Ratio'] - df['Ratio_MA']
        
        # Binary signal: 1 = favor Momentum, 0 = favor Value
        df['Signal_Binary'] = (df['Ratio'] > df['Ratio_MA']).astype(int)
        
        return df
    
    def apply_allocation(self, df):
        """Apply 75/25 allocation with 2-month cooldown and 50/50 transition.
        
        After a full switch, the next full switch can only occur 2 months later.
        During the cooldown month, if the signal disagrees with the current regime,
        the allocation goes to 50/50 instead of hard-locking to the old allocation.
        If the signal agrees during cooldown, normal 75/25 is maintained.
        """
        signals = df['Signal_Binary'].values.copy()
        n = len(signals)
        
        w_mom = np.zeros(n)
        w_val = np.zeros(n)
        
        # Start with first signal's allocation
        current_regime_signal = signals[0]
        w_mom[0] = 0.75 if current_regime_signal == 1 else 0.25
        w_val[0] = 1 - w_mom[0]
        
        months_since_switch = 999  # Allow first switch freely
        
        for i in range(1, n):
            months_since_switch += 1
            raw_signal = signals[i]
            
            if raw_signal != current_regime_signal:
                # Signal wants to switch
                if months_since_switch >= 2:
                    # Cooldown expired → allow full switch
                    current_regime_signal = raw_signal
                    months_since_switch = 0
                    w_mom[i] = 0.75 if current_regime_signal == 1 else 0.25
                else:
                    # Still in cooldown → go 50/50
                    w_mom[i] = 0.50
            else:
                # Signal agrees with current regime → normal allocation
                w_mom[i] = 0.75 if current_regime_signal == 1 else 0.25
            
            w_val[i] = 1 - w_mom[i]
        
        df['w_mom'] = w_mom
        df['w_val'] = w_val
        
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
        """Run the Ratio Trend 75/25 strategy"""
        print("\n" + "="*80)
        print("BACKTESTING: RATIO TREND 75/25 STRATEGY")
        print("="*80)
        
        # Load data
        df = self.load_monthly_data()
        df = self.calculate_returns(df)
        
        # Calculate signal
        df = self.signal_ratio_trend(df, ma_length=6)
        
        # Apply allocation
        df = self.apply_allocation(df)
        df = self.calculate_portfolio_returns(df)
        
        print("\n✅ Strategy calculations complete")
        
        # Run SIP analysis
        results, sip_data = self.run_sip_on_portfolio(df, 'Ratio Trend 75/25')
        
        # Save portfolio data
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
    Main execution function - Ratio Trend strategy analysis
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
