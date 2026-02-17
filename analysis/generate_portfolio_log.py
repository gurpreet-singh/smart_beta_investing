"""
Generate monthly portfolio holdings log
Shows month-by-month breakdown of momentum, value, cash holdings and total portfolio value
Starting capital: ₹10,000
"""
import pandas as pd
import numpy as np
from pathlib import Path

def generate_portfolio_log(portfolio_csv, output_file, strategy_name):
    """Generate monthly holdings log from portfolio CSV"""
    
    df = pd.read_csv(portfolio_csv)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Starting capital
    initial_capital = 10000
    
    # Initialize portfolio
    portfolio_value = initial_capital
    holdings = []
    
    for i, row in df.iterrows():
        # Get weights (already final weights with cash filter applied)
        w_mom = row['w_mom']
        w_val = row['w_val']
        w_cash = row.get('w_cash', 0.0)
        
        # Calculate holdings at start of month
        mom_holding = portfolio_value * w_mom
        val_holding = portfolio_value * w_val
        cash_holding = portfolio_value * w_cash
        
        # Get returns for the month
        ret_mom = row['Return_mom']
        ret_val = row['Return_val']
        # Cash earns 0%
        
        # Calculate new holdings after returns
        mom_holding_end = mom_holding * (1 + ret_mom) if not np.isnan(ret_mom) else mom_holding
        val_holding_end = val_holding * (1 + ret_val) if not np.isnan(ret_val) else val_holding
        cash_holding_end = cash_holding  # Cash doesn't change
        
        # New portfolio value
        portfolio_value_end = mom_holding_end + val_holding_end + cash_holding_end
        
        # Record
        holdings.append({
            'Year': row['Date'].year,
            'Month': row['Date'].strftime('%b'),
            'Date': row['Date'].strftime('%Y-%m-%d'),
            'Momentum_Holding': mom_holding_end,
            'Value_Holding': val_holding_end,
            'Cash_Holding': cash_holding_end,
            'Total_Portfolio': portfolio_value_end,
            'Momentum_Weight': w_mom * 100,
            'Value_Weight': w_val * 100,
            'Cash_Weight': w_cash * 100,
            'Regime': row['regime'],
            'Risk_On': row.get('risk_on', True)
        })
        
        # Update for next iteration
        portfolio_value = portfolio_value_end
    
    # Create DataFrame
    log_df = pd.DataFrame(holdings)
    
    # Save to CSV
    log_df.to_csv(output_file, index=False)
    
    print(f"\n{'='*80}")
    print(f"  {strategy_name} — PORTFOLIO HOLDINGS LOG")
    print(f"{'='*80}")
    print(f"\n✅ Generated monthly portfolio log: {output_file}")
    print(f"   Starting Capital: ₹{initial_capital:,.0f}")
    print(f"   Final Portfolio:  ₹{log_df['Total_Portfolio'].iloc[-1]:,.0f}")
    print(f"   Total Return:     {(log_df['Total_Portfolio'].iloc[-1]/initial_capital - 1)*100:.2f}%")
    print(f"   Months:           {len(log_df)}")
    
    # Summary stats
    avg_cash = log_df['Cash_Weight'].mean()
    avg_mom = log_df['Momentum_Weight'].mean()
    avg_val = log_df['Value_Weight'].mean()
    
    print(f"\n📊 Average Allocation:")
    print(f"   Momentum: {avg_mom:.1f}%")
    print(f"   Value:    {avg_val:.1f}%")
    print(f"   Cash:     {avg_cash:.1f}%")
    
    return log_df

def main():
    base = Path(__file__).parent.parent
    
    # Nifty 200
    nifty200_csv = base / 'nifty200' / 'output' / 'monthly' / 'portfolio_ratio_trend_75_25.csv'
    nifty200_log = base / 'nifty200' / 'output' / 'nifty200_portfolio_holdings_log.csv'
    
    generate_portfolio_log(nifty200_csv, nifty200_log, 'NIFTY 200')
    
    # Nifty 500
    nifty500_csv = base / 'nifty500' / 'output' / 'monthly' / 'nifty500_portfolio_ratio_trend_75_25.csv'
    nifty500_log = base / 'nifty500' / 'output' / 'nifty500_portfolio_holdings_log.csv'
    
    generate_portfolio_log(nifty500_csv, nifty500_log, 'NIFTY 500')
    
    print(f"\n{'='*80}")
    print("✅ ALL PORTFOLIO LOGS GENERATED")
    print(f"{'='*80}\n")

if __name__ == "__main__":
    main()
