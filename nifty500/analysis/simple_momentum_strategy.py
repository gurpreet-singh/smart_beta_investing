"""
Simple Momentum Strategy for Nifty 500

Strategy:
- If Momentum gains 20% in 3 months → 100% Momentum
- If Momentum loses 20% in 3 months → 100% Value
- Otherwise → Stay in current regime
"""

import pandas as pd
import numpy as np
from pathlib import Path

class SimpleMomentumStrategy500:
    def __init__(self):
        self.data_folder = Path(__file__).parent.parent / "output" / "monthly"
        self.output_folder = self.data_folder
        
    def load_monthly_data(self):
        """Load monthly momentum and value data"""
        print("\n📂 Loading Nifty 500 monthly index data...")
        
        mom_file = self.data_folder / "nifty500_momentum_50_monthly.csv"
        val_file = self.data_folder / "nifty500_value_50_monthly.csv"
        
        mom_df = pd.read_csv(mom_file, parse_dates=['Date'])
        val_df = pd.read_csv(val_file, parse_dates=['Date'])
        
        # Merge
        df = mom_df[['Date', 'Close']].merge(
            val_df[['Date', 'Close']],
            on='Date',
            suffixes=('_mom', '_val')
        )
        
        print(f"✅ Loaded {len(df)} months of data")
        print(f"   Date range: {df['Date'].min().strftime('%Y-%m')} to {df['Date'].max().strftime('%Y-%m')}")
        
        return df
    
    def calculate_returns(self, df):
        """Calculate monthly returns"""
        df['Return_mom'] = df['Close_mom'].pct_change()
        df['Return_val'] = df['Close_val'].pct_change()
        return df
    
    def calculate_portfolio_returns(self, df):
        """Calculate portfolio NAV and metrics"""
        df['Portfolio_NAV'] = 100 * (1 + df['Portfolio_Return']).cumprod()
        return df
    
    def run_sip_analysis(self, df, strategy_name):
        """Run SIP analysis"""
        print(f"\n🎯 Running SIP analysis for: {strategy_name}")
        
        # Monthly SIP of ₹10,000
        monthly_sip = 10000
        
        sip_data = []
        total_units = 0
        total_invested = 0
        
        for idx, row in df.iterrows():
            nav = row['Portfolio_NAV']
            
            # Skip if NAV is NaN
            if pd.isna(nav):
                continue
            
            # Invest monthly SIP
            units_bought = monthly_sip / nav
            total_units += units_bought
            total_invested += monthly_sip
            
            current_value = total_units * nav
            
            sip_data.append({
                'Date': row['Date'],
                'NAV': nav,
                'Units_Bought': units_bought,
                'Total_Units': total_units,
                'Invested': total_invested,
                'Current_Value': current_value,
                'Gain': current_value - total_invested
            })
        
        sip_df = pd.DataFrame(sip_data)
        
        # Calculate XIRR (approximate using CAGR)
        start_date = sip_df['Date'].iloc[0]
        end_date = sip_df['Date'].iloc[-1]
        years = (end_date - start_date).days / 365.25
        
        final_value = sip_df['Current_Value'].iloc[-1]
        total_invested = sip_df['Invested'].iloc[-1]
        
        # Approximate XIRR using simple CAGR formula
        xirr = (final_value / total_invested) ** (1 / years) - 1
        
        # Calculate index CAGR
        valid_nav = df['Portfolio_NAV'].dropna()
        start_nav = valid_nav.iloc[0]
        end_nav = valid_nav.iloc[-1]
        index_cagr = (end_nav / start_nav) ** (1 / years) - 1
        
        # Max drawdown
        running_max = valid_nav.expanding().max()
        drawdown = (valid_nav - running_max) / running_max * 100
        max_dd = drawdown.min()
        
        # Investor max drawdown (on SIP portfolio)
        sip_running_max = sip_df['Current_Value'].expanding().max()
        sip_drawdown = (sip_df['Current_Value'] - sip_running_max) / sip_running_max * 100
        investor_max_dd = sip_drawdown.min()
        
        results = {
            'strategy_name': strategy_name,
            'sip_xirr': xirr * 100,
            'index_cagr': index_cagr * 100,
            'total_invested': total_invested,
            'final_value': final_value,
            'absolute_gain': final_value - total_invested,
            'total_return': (final_value / total_invested - 1) * 100,
            'max_drawdown': max_dd,
            'investor_max_dd': investor_max_dd,
            'mar_ratio': (index_cagr * 100) / abs(max_dd) if max_dd != 0 else 0
        }
        
        return results, sip_df
    
    def run_strategy(self):
        """Run Simple Momentum Strategy for Nifty 500"""
        print("\n" + "="*80)
        print("BACKTESTING: SIMPLE MOMENTUM STRATEGY - NIFTY 500")
        print("="*80)
        
        # Load data
        df = self.load_monthly_data()
        df = self.calculate_returns(df)
        
        # Calculate 3-month momentum return
        df['Mom_3M_Return'] = df['Close_mom'].pct_change(3) * 100  # In percentage
        
        # Initialize regime
        df['regime'] = 'momentum'  # Start with momentum
        
        # Apply simple rules
        for i in range(1, len(df)):
            mom_3m = df.loc[i, 'Mom_3M_Return']
            prev_regime = df.loc[i-1, 'regime']
            
            # Skip if NaN
            if pd.isna(mom_3m):
                df.loc[i, 'regime'] = prev_regime
                continue
            
            # Rule 1: Momentum gains 20%+ in 3 months → 100% Momentum
            if mom_3m >= 20:
                df.loc[i, 'regime'] = 'momentum'
            
            # Rule 2: Momentum loses 20%+ in 3 months → 100% Value
            elif mom_3m <= -20:
                df.loc[i, 'regime'] = 'value'
            
            # Rule 3: Otherwise → Stay in current regime
            else:
                df.loc[i, 'regime'] = prev_regime
        
        # Binary allocation based on regime
        df['w_mom'] = np.where(df['regime'] == 'momentum', 1.0, 0.0)
        df['w_val'] = 1.0 - df['w_mom']
        
        # Shift weights to avoid lookahead bias
        df['w_mom'] = df['w_mom'].shift(1)
        df['w_val'] = df['w_val'].shift(1)
        
        # Fill first month with momentum (default)
        df['w_mom'] = df['w_mom'].fillna(1.0)
        df['w_val'] = df['w_val'].fillna(0.0)
        
        # Calculate portfolio returns
        df['Portfolio_Return'] = df['w_mom'] * df['Return_mom'] + df['w_val'] * df['Return_val']
        
        # Calculate NAV
        df = self.calculate_portfolio_returns(df)
        
        # Calculate metrics
        start_nav = 100
        end_nav = df['Portfolio_NAV'].iloc[-1]
        years = len(df) / 12
        cagr = (end_nav / start_nav) ** (1 / years) - 1
        
        # Max Drawdown
        running_max = df['Portfolio_NAV'].expanding().max()
        drawdown = (df['Portfolio_NAV'] - running_max) / running_max * 100
        max_dd = drawdown.min()
        
        # Total Return
        total_return = (end_nav / start_nav - 1) * 100
        
        # MAR Ratio
        mar_ratio = (cagr * 100) / abs(max_dd) if max_dd != 0 else 0
        
        # Count switches
        switches = (df['regime'] != df['regime'].shift(1)).sum() - 1
        
        # Regime distribution
        regime_counts = df['regime'].value_counts()
        
        # Print results
        print("\n" + "="*80)
        print("STRATEGY RESULTS - NIFTY 500")
        print("="*80)
        
        print(f"\n📊 Performance Metrics:")
        print(f"   CAGR:              {cagr * 100:.2f}%")
        print(f"   Total Return:      {total_return:.2f}%")
        print(f"   Max Drawdown:      {max_dd:.2f}%")
        print(f"   MAR Ratio:         {mar_ratio:.2f}")
        print(f"   Final NAV:         ₹{end_nav:,.2f}")
        
        print(f"\n📊 Regime Distribution:")
        for regime, count in regime_counts.items():
            pct = count / len(df) * 100
            print(f"   {regime.capitalize():<10}: {count:3d} months ({pct:.1f}%)")
        
        print(f"\n📊 Switching Behavior:")
        print(f"   Total Switches:    {switches}")
        print(f"   Avg Switch Freq:   Every {len(df)/switches:.1f} months")
        
        print(f"\n📊 Allocation Stats:")
        print(f"   Avg Momentum:      {df['w_mom'].mean() * 100:.1f}%")
        print(f"   Avg Value:         {df['w_val'].mean() * 100:.1f}%")
        
        # Run SIP analysis
        sip_results, sip_df = self.run_sip_analysis(df, 'Simple Momentum - Nifty 500')
        
        # Print SIP results
        print("\n" + "="*80)
        print("SIP ANALYSIS RESULTS")
        print("="*80)
        print(f"\n   SIP XIRR:          {sip_results['sip_xirr']:.2f}%")
        print(f"   Index CAGR:        {sip_results['index_cagr']:.2f}%")
        print(f"   Total Invested:    ₹{sip_results['total_invested']:,.0f}")
        print(f"   Final Value:       ₹{sip_results['final_value']:,.0f}")
        print(f"   Absolute Gain:     ₹{sip_results['absolute_gain']:,.0f}")
        print(f"   Total Return:      {sip_results['total_return']:.2f}%")
        print(f"   Max Drawdown:      {sip_results['max_drawdown']:.2f}%")
        print(f"   Investor Max DD:   {sip_results['investor_max_dd']:.2f}%")
        
        # Save results
        output_file = self.output_folder / "nifty500_simple_momentum.csv"
        df.to_csv(output_file, index=False)
        print(f"\n✅ Saved portfolio to: {output_file}")
        
        return sip_results, df

if __name__ == "__main__":
    strategy = SimpleMomentumStrategy500()
    results, df = strategy.run_strategy()
    
    print("\n" + "="*80)
    print("✅ STRATEGY COMPLETE")
    print("="*80)
