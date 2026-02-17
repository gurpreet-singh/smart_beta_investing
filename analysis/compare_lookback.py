"""
Compare 3M vs 6M relative momentum lookback for Quarterly Alpha Rotation
Both Nifty 200 and Nifty 500
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')

def calculate_xirr(cash_flows, guess=0.1):
    from scipy.optimize import newton
    cash_flows = sorted(cash_flows, key=lambda x: x[0])
    start_date = cash_flows[0][0]
    amounts = [cf[1] for cf in cash_flows]
    days = [(cf[0] - start_date).days for cf in cash_flows]
    
    def xnpv(rate):
        return sum([a / (1 + rate) ** (d / 365.0) for a, d in zip(amounts, days)])
    def xnpv_deriv(rate):
        return sum([-a * d / 365.0 / (1 + rate) ** (d / 365.0 + 1) for a, d in zip(amounts, days)])
    
    try:
        return newton(xnpv, guess, fprime=xnpv_deriv, maxiter=100) * 100
    except:
        return 0.0

def run_quarterly_rotation(mom_file, val_file, lookback_months, sip=10000):
    """Run quarterly alpha rotation with specified lookback"""
    mom_df = pd.read_csv(mom_file)
    mom_df['Date'] = pd.to_datetime(mom_df['Date'])
    mom_df = mom_df.rename(columns={'Close': 'Close_mom'})
    
    val_df = pd.read_csv(val_file)
    val_df['Date'] = pd.to_datetime(val_df['Date'])
    val_df = val_df.rename(columns={'Close': 'Close_val'})
    
    df = pd.merge(mom_df[['Date', 'Close_mom']], val_df[['Date', 'Close_val']], on='Date', how='inner')
    
    df['Return_mom'] = df['Close_mom'].pct_change()
    df['Return_val'] = df['Close_val'].pct_change()
    df['Quarter'] = df['Date'].dt.to_period('Q')
    
    # Relative momentum with specified lookback
    df['RelMom'] = df['Close_mom'].pct_change(lookback_months) - df['Close_val'].pct_change(lookback_months)
    
    # Quarter-end decisions
    quarterly = df.groupby('Quarter').last()
    quarterly['regime'] = np.where(quarterly['RelMom'] > 0, 'momentum', 'value')
    
    # Merge back and forward fill
    df = df.merge(quarterly[['regime']], left_on='Quarter', right_index=True, how='left')
    df['regime'] = df['regime'].ffill()
    
    # 1-month execution delay (no lookahead)
    df['regime'] = df['regime'].shift(1).fillna('value')
    
    # Portfolio returns
    df['w_mom'] = np.where(df['regime'] == 'momentum', 1.0, 0.0)
    df['w_val'] = 1.0 - df['w_mom']
    df['Portfolio_Return'] = df['w_mom'] * df['Return_mom'] + df['w_val'] * df['Return_val']
    df['Portfolio_NAV'] = 1000 * (1 + df['Portfolio_Return']).cumprod()
    df.loc[0, 'Portfolio_NAV'] = 1000
    
    # SIP + metrics
    sip_data = df[['Date', 'Portfolio_NAV']].rename(columns={'Portfolio_NAV': 'NAV'}).dropna()
    sip_data['Units_Bought'] = sip / sip_data['NAV']
    sip_data['Cumulative_Units'] = sip_data['Units_Bought'].cumsum()
    sip_data['Total_Invested'] = sip * (sip_data.index + 1)
    sip_data['Portfolio_Value'] = sip_data['Cumulative_Units'] * sip_data['NAV']
    sip_data['Peak'] = sip_data['Portfolio_Value'].cummax()
    sip_data['DD'] = (sip_data['Portfolio_Value'] - sip_data['Peak']) / sip_data['Peak'] * 100
    sip_data['Inv_DD'] = (sip_data['Portfolio_Value'] - sip_data['Total_Invested']) / sip_data['Total_Invested'] * 100
    
    final_value = sip_data['Portfolio_Value'].iloc[-1]
    total_invested = sip_data['Total_Invested'].iloc[-1]
    max_dd = sip_data['DD'].min()
    max_inv_dd = sip_data['Inv_DD'].min()
    
    cash_flows = [(r['Date'], -sip) for _, r in sip_data.iterrows()]
    cash_flows.append((sip_data['Date'].iloc[-1], final_value))
    sip_xirr = calculate_xirr(cash_flows)
    
    years = len(sip_data) / 12
    start_nav = sip_data['NAV'].iloc[0]
    end_nav = sip_data['NAV'].iloc[-1]
    index_cagr = ((end_nav / start_nav) ** (1 / years) - 1) * 100
    
    switches = (df['regime'] != df['regime'].shift(1)).sum() - 1
    mom_pct = (df['regime'] == 'momentum').mean() * 100
    
    return {
        'cagr': index_cagr,
        'xirr': sip_xirr,
        'max_dd': max_dd,
        'max_inv_dd': max_inv_dd,
        'mar': sip_xirr / abs(max_dd) if max_dd != 0 else 0,
        'switches': switches,
        'mom_pct': mom_pct,
        'total_return': (final_value - total_invested) / total_invested * 100,
        'final_value': final_value,
    }

def main():
    base = Path(__file__).parent.parent
    
    configs = [
        {
            'name': 'NIFTY 200',
            'mom_file': base / 'nifty200' / 'output' / 'monthly' / 'nifty200_momentum_30_monthly.csv',
            'val_file': base / 'nifty200' / 'output' / 'monthly' / 'nifty200_value_30_monthly.csv',
        },
        {
            'name': 'NIFTY 500',
            'mom_file': base / 'nifty500' / 'output' / 'monthly' / 'nifty500_momentum_50_monthly.csv',
            'val_file': base / 'nifty500' / 'output' / 'monthly' / 'nifty500_value_50_monthly.csv',
        },
    ]
    
    lookbacks = [3, 6]
    
    for config in configs:
        print(f"\n{'='*80}")
        print(f"  {config['name']} — QUARTERLY ALPHA ROTATION (100/0)")
        print(f"{'='*80}")
        print(f"\n{'Metric':<22s}  {'3M Lookback':>14s}  {'6M Lookback':>14s}  {'Delta':>10s}")
        print("-" * 65)
        
        results = {}
        for lb in lookbacks:
            results[lb] = run_quarterly_rotation(config['mom_file'], config['val_file'], lb)
        
        r3 = results[3]
        r6 = results[6]
        
        rows = [
            ('Index CAGR', f"{r3['cagr']:.2f}%", f"{r6['cagr']:.2f}%", f"{r3['cagr']-r6['cagr']:+.2f}%"),
            ('SIP XIRR', f"{r3['xirr']:.2f}%", f"{r6['xirr']:.2f}%", f"{r3['xirr']-r6['xirr']:+.2f}%"),
            ('Max Drawdown', f"{r3['max_dd']:.2f}%", f"{r6['max_dd']:.2f}%", f"{r3['max_dd']-r6['max_dd']:+.2f}%"),
            ('Max Investor DD', f"{r3['max_inv_dd']:.2f}%", f"{r6['max_inv_dd']:.2f}%", f"{r3['max_inv_dd']-r6['max_inv_dd']:+.2f}%"),
            ('MAR Ratio', f"{r3['mar']:.3f}", f"{r6['mar']:.3f}", f"{r3['mar']-r6['mar']:+.3f}"),
            ('Regime Switches', f"{r3['switches']:.0f}", f"{r6['switches']:.0f}", f"{r3['switches']-r6['switches']:+.0f}"),
            ('Momentum %', f"{r3['mom_pct']:.1f}%", f"{r6['mom_pct']:.1f}%", f"{r3['mom_pct']-r6['mom_pct']:+.1f}%"),
            ('Total Return', f"{r3['total_return']:.0f}%", f"{r6['total_return']:.0f}%", ""),
            ('Final Value', f"₹{r3['final_value']:,.0f}", f"₹{r6['final_value']:,.0f}", ""),
        ]
        
        for label, v3, v6, delta in rows:
            print(f"{label:<22s}  {v3:>14s}  {v6:>14s}  {delta:>10s}")

if __name__ == "__main__":
    main()
