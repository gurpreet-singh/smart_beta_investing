"""
Portfolio Analytics Engine
Calculates comprehensive performance, risk, allocation, regime, and attribution metrics
for the dual-factor rotation strategy
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import plotly.graph_objects as go
from plotly.subplots import make_subplots

class PortfolioAnalytics:
    def __init__(self, portfolio_file, monthly_sip=10000):
        """Initialize with portfolio strategy CSV file"""
        self.portfolio_df = pd.read_csv(portfolio_file)
        self.portfolio_df['Date'] = pd.to_datetime(self.portfolio_df['Date'])
        self.monthly_sip = monthly_sip
        self.master_df = None
        
    def build_master_dataframe(self):
        """Build comprehensive master dataframe with all metrics"""
        print("\n" + "="*80)
        print("BUILDING MASTER ANALYTICS DATAFRAME")
        print("="*80)
        
        df = self.portfolio_df.copy()
        
        # ① PERFORMANCE METRICS
        print("\n📊 Calculating performance metrics...")
        
        # Rolling returns (3Y, 5Y)
        df['Rolling_3Y_CAGR'] = ((df['Portfolio_NAV'] / df['Portfolio_NAV'].shift(36)) ** (1/3) - 1) * 100
        df['Rolling_5Y_CAGR'] = ((df['Portfolio_NAV'] / df['Portfolio_NAV'].shift(60)) ** (1/5) - 1) * 100
        
        # Calendar year grouping
        df['Year'] = df['Date'].dt.year
        df['Month'] = df['Date'].dt.month
        
        # ② RISK METRICS
        print("📉 Calculating risk metrics...")
        
        # NAV drawdown
        df['Running_Max_NAV'] = df['Portfolio_NAV'].cummax()
        df['NAV_Drawdown_Pct'] = ((df['Portfolio_NAV'] - df['Running_Max_NAV']) / df['Running_Max_NAV']) * 100
        
        # Individual Index Drawdowns (for underwater chart comparison)
        df['Running_Max_Mom'] = df['Close_mom'].cummax()
        df['Mom_Drawdown_Pct'] = ((df['Close_mom'] - df['Running_Max_Mom']) / df['Running_Max_Mom']) * 100
        
        df['Running_Max_Val'] = df['Close_val'].cummax()
        df['Val_Drawdown_Pct'] = ((df['Close_val'] - df['Running_Max_Val']) / df['Running_Max_Val']) * 100
        
        # Underwater periods (boolean)
        df['Underwater'] = df['Portfolio_NAV'] < df['Running_Max_NAV']
        
        # Calculate SIP metrics for investor drawdown
        df['Units_Bought'] = self.monthly_sip / df['Portfolio_NAV']
        df['Cumulative_Units'] = df['Units_Bought'].cumsum()
        df['Total_Invested'] = self.monthly_sip * (df.index + 1)
        df['Portfolio_Value'] = df['Cumulative_Units'] * df['Portfolio_NAV']
        df['Peak_Portfolio_Value'] = df['Portfolio_Value'].cummax()
        df['Investor_Drawdown_Pct'] = ((df['Portfolio_Value'] - df['Peak_Portfolio_Value']) / df['Peak_Portfolio_Value']) * 100
        
        # Volatility (annualized)
        df['Volatility_Ann'] = df['Portfolio_Return'].rolling(12).std() * np.sqrt(12) * 100
        
        # Ulcer Index (rolling 12M)
        df['Ulcer_Index'] = np.sqrt(df['NAV_Drawdown_Pct'].rolling(12).apply(lambda x: (x**2).mean()))
        
        # ③ ALLOCATION METRICS
        print("🎯 Calculating allocation metrics...")
        
        # Regime classification
        df['Regime'] = df['w_mom'].apply(lambda x: 'Momentum' if x > 0.5 else 'Value')
        
        # Turnover (monthly weight change)
        df['Turnover'] = df['w_mom'].diff().abs()
        
        # ④ ATTRIBUTION METRICS
        print("🔍 Calculating attribution...")
        
        # Factor contributions
        df['Mom_Contribution'] = df['w_mom'] * df['Return_mom']
        df['Val_Contribution'] = df['w_val'] * df['Return_val']
        
        # Cumulative contributions
        df['Cumulative_Mom_Contrib'] = (1 + df['Mom_Contribution']).cumprod() - 1
        df['Cumulative_Val_Contrib'] = (1 + df['Val_Contribution']).cumprod() - 1
        
        # Compute static 50/50 for comparison
        df['Static_Return'] = 0.5 * df['Return_mom'] + 0.5 * df['Return_val']
        df['Static_NAV'] = 1000 * (1 + df['Static_Return']).cumprod()
        df.loc[0, 'Static_NAV'] = 1000
        
        # Excess return over static
        df['Excess_Return'] = df['Portfolio_Return'] - df['Static_Return']
        df['Alpha_NAV'] = df['Portfolio_NAV'] - df['Static_NAV']
        
        self.master_df = df
        print(f"✅ Master dataframe built: {len(df)} rows, {len(df.columns)} columns")
        
        return df
    
    def calculate_summary_kpis(self):
        """Calculate top-level KPI summary cards"""
        df = self.master_df
        
        # Performance KPIs
        start_nav = df['Portfolio_NAV'].iloc[0]
        end_nav = df['Portfolio_NAV'].iloc[-1]
        years = len(df) / 12
        cagr = ((end_nav / start_nav) ** (1 / years) - 1) * 100
        
        total_invested = df['Total_Invested'].iloc[-1]
        final_value = df['Portfolio_Value'].iloc[-1]
        
        # Calculate XIRR (simplified)
        from nifty500_portfolio_strategy import calculate_xirr
        cash_flows = [(row['Date'], -self.monthly_sip) for _, row in df.iterrows()]
        cash_flows.append((df['Date'].iloc[-1], final_value))
        sip_xirr = calculate_xirr(cash_flows)
        
        # Risk KPIs
        max_dd = df['NAV_Drawdown_Pct'].min()
        max_investor_dd = df['Investor_Drawdown_Pct'].min()
        mar_ratio = sip_xirr / abs(max_dd) if max_dd != 0 else 0
        avg_volatility = df['Volatility_Ann'].mean()
        
        # Allocation KPIs
        pct_time_momentum = (df['Regime'] == 'Momentum').sum() / len(df) * 100
        avg_turnover = df['Turnover'].sum() / years
        
        # Regime durations
        regime_changes = (df['Regime'] != df['Regime'].shift()).cumsum()
        regime_durations = df.groupby(regime_changes).size()
        avg_regime_duration = regime_durations.mean()
        
        kpis = {
            'sip_xirr': round(sip_xirr, 2),
            'cagr': round(cagr, 2),
            'max_drawdown': round(max_dd, 2),
            'max_investor_dd': round(max_investor_dd, 2),
            'mar_ratio': round(mar_ratio, 2),
            'volatility': round(avg_volatility, 2),
            'pct_time_momentum': round(pct_time_momentum, 1),
            'avg_regime_duration': round(avg_regime_duration, 1),
            'total_invested': int(total_invested),
            'final_value': int(final_value),
            'total_return_pct': round(((final_value - total_invested) / total_invested) * 100, 2),
            'annual_turnover': round(avg_turnover * 100, 1)
        }
        
        return kpis
    
    def generate_calendar_returns(self):
        """Generate calendar year returns comparison data (strategy vs individual indices)"""
        df = self.master_df
        
        # Strategy returns by year
        strategy_returns = df.groupby('Year')['Portfolio_Return'].apply(
            lambda x: ((1 + x).prod() - 1) * 100
        ).reset_index()
        strategy_returns.columns = ['Year', 'Return']
        
        # Momentum index returns by year
        mom_returns = df.groupby('Year')['Return_mom'].apply(
            lambda x: ((1 + x).prod() - 1) * 100
        ).reset_index()
        mom_returns.columns = ['Year', 'Mom_Return']
        
        # Value index returns by year
        val_returns = df.groupby('Year')['Return_val'].apply(
            lambda x: ((1 + x).prod() - 1) * 100
        ).reset_index()
        val_returns.columns = ['Year', 'Val_Return']
        
        # Merge all
        merged = strategy_returns.merge(mom_returns, on='Year').merge(val_returns, on='Year')
        
        return merged.to_dict('records')
    
    def generate_allocation_histogram(self):
        """Generate allocation distribution data"""
        df = self.master_df
        
        # Bin allocation
        bins = [0, 0.3, 0.5, 0.7, 1.0]
        labels = ['Value Heavy (0-30%)', 'Balanced (30-50%)', 'Slight Momentum (50-70%)', 'Momentum Heavy (70-100%)']
        df['Allocation_Bucket'] = pd.cut(df['w_mom'], bins=bins, labels=labels, include_lowest=True)
        
        distribution = df['Allocation_Bucket'].value_counts().to_dict()
        
        return {k: int(v) for k, v in distribution.items()}
    
    def generate_regime_analysis(self):
        """Generate regime transition and duration analysis"""
        df = self.master_df
        
        # Regime durations
        regime_changes = (df['Regime'] != df['Regime'].shift()).cumsum()
        regime_info = df.groupby(regime_changes).agg({
            'Regime': 'first',
            'Date': ['first', 'count']
        }).reset_index(drop=True)
        
        regime_info.columns = ['Regime', 'Start_Date', 'Duration']
        
        # Convert dates to strings for JSON serialization
        regime_info['Start_Date'] = regime_info['Start_Date'].dt.strftime('%Y-%m-%d')
        
        # Transition matrix
        transitions = pd.crosstab(
            df['Regime'].shift(), 
            df['Regime'], 
            normalize='index'
        ).round(3)
        
        return {
            'durations': regime_info.to_dict('records'),
            'transition_matrix': transitions.to_dict()
        }
    
    def generate_charts_data(self):
        """Generate all chart data for dashboard"""
        df = self.master_df
        
        charts = {}
        
        # Chart 1: Portfolio NAV (log scale)
        charts['nav_series'] = {
            'dates': df['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'nav': df['Portfolio_NAV'].tolist()
        }
        
        # Chart 2: SIP Portfolio Value
        charts['sip_value_series'] = {
            'dates': df['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'invested': df['Total_Invested'].tolist(),
            'value': df['Portfolio_Value'].tolist()
        }
        
        # Chart 3: Underwater Drawdowns (Strategy + Individual Indices)
        charts['drawdown_series'] = {
            'dates': df['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'strategy_dd': df['NAV_Drawdown_Pct'].tolist(),
            'momentum_dd': df['Mom_Drawdown_Pct'].tolist(),
            'value_dd': df['Val_Drawdown_Pct'].tolist()
        }
        
        # Chart 4: Allocation Stack (round to integers to avoid floating point errors)
        charts['allocation_series'] = {
            'dates': df['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'momentum': (df['w_mom'] * 100).round(0).tolist(),
            'value': (df['w_val'] * 100).round(0).tolist(),
            'regime': df['Regime'].tolist()
        }
        
        # Chart 5: Rolling Returns (replace NaN with None for JSON serialization)
        charts['rolling_returns'] = {
            'dates': df['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'rolling_3y': df['Rolling_3Y_CAGR'].replace({np.nan: None}).tolist(),
            'rolling_5y': df['Rolling_5Y_CAGR'].replace({np.nan: None}).tolist()
        }
        
        # Chart 6: Factor Attribution
        charts['attribution'] = {
            'dates': df['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'mom_contrib': (df['Cumulative_Mom_Contrib'] * 100).tolist(),
            'val_contrib': (df['Cumulative_Val_Contrib'] * 100).tolist()
        }
        
        # Chart 7: Alpha vs Static
        charts['alpha'] = {
            'dates': df['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'strategy_nav': df['Portfolio_NAV'].tolist(),
            'static_nav': df['Static_NAV'].tolist(),
            'alpha': df['Alpha_NAV'].tolist()
        }
        
        # Chart 8: Monthly Return Distribution
        valid_returns = df['Portfolio_Return'].dropna() * 100
        returns_hist = np.histogram(valid_returns, bins=30)
        charts['return_distribution'] = {
            'counts': returns_hist[0].tolist(),
            'bins': returns_hist[1].tolist()
        }
        
        return charts
    
    def export_dashboard_data(self, output_file):
        """Export complete dashboard data as JSON"""
        print("\n" + "="*80)
        print("EXPORTING PORTFOLIO DASHBOARD DATA")
        print("="*80)
        
        if self.master_df is None:
            self.build_master_dataframe()
        
        # Load portfolio holdings log if available
        holdings_log = None
        # Construct correct path: nifty500_portfolio_dashboard.json -> nifty500_portfolio_holdings_log.csv
        output_path = Path(output_file)
        holdings_file = output_path.parent / f"{output_path.stem.split('_')[0]}_portfolio_holdings_log.csv"
        if holdings_file.exists():
            holdings_df = pd.read_csv(holdings_file)
            holdings_log = holdings_df.to_dict('records')
            print(f"\n📊 Loaded portfolio holdings log: {len(holdings_log)} months")
        
        dashboard_data = {
            'kpis': self.calculate_summary_kpis(),
            'calendar_returns': self.generate_calendar_returns(),
            'allocation_distribution': self.generate_allocation_histogram(),
            'regime_analysis': self.generate_regime_analysis(),
            'charts': self.generate_charts_data()
        }
        
        # Add holdings log if available
        if holdings_log:
            dashboard_data['portfolio_holdings'] = holdings_log
        
        # Save to file
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        
        # Helper function to convert NaN to None recursively
        def convert_nan(obj):
            if isinstance(obj, dict):
                return {k: convert_nan(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [convert_nan(v) for v in obj]
            elif isinstance(obj, float) and np.isnan(obj):
                return None
            else:
                return obj
        
        # Convert NaN to None for valid JSON
        dashboard_data_clean = convert_nan(dashboard_data)
        
        with open(output_path, 'w') as f:
            json.dump(dashboard_data_clean, f, indent=2)
        
        print(f"\n✅ Exported dashboard data to: {output_path}")
        print(f"   - {len(dashboard_data['kpis'])} KPIs")
        print(f"   - {len(dashboard_data['calendar_returns'])} years of returns")
        print(f"   - {len(dashboard_data['charts'])} chart datasets")
        
        return dashboard_data

def main():
    """Generate portfolio dashboard data for best strategy"""
    print("\n" + "="*80)
    print("PORTFOLIO DASHBOARD DATA GENERATOR")
    print("="*80)
    
    # Input: Best strategy portfolio file
    portfolio_file = Path(__file__).parent.parent / "output" / "monthly" / "nifty500_simple_momentum.csv"
    
    if not portfolio_file.exists():
        print(f"\n❌ Portfolio file not found: {portfolio_file}")
        print("   Run portfoliostrategy.py first!")
        return
    
    # Output: Dashboard JSON
    output_file = Path(__file__).parent.parent / "output" / "nifty500_portfolio_dashboard.json"
    
    # Generate analytics
    analytics = PortfolioAnalytics(portfolio_file, monthly_sip=10000)
    analytics.build_master_dataframe()
    dashboard_data = analytics.export_dashboard_data(output_file)
    
    print("\n" + "="*80)
    print("✅ PORTFOLIO DASHBOARD DATA READY")
    print("="*80)
    print(f"\nLoad this in your dashboard: {output_file}\n")

if __name__ == "__main__":
    main()
