"""
Compare single 6M vs multi-horizon composite relative momentum
Both Nifty 200 and Nifty 500
"""
import pandas as pd
import numpy as np
from pathlib import Path
from scipy.optimize import newton
import warnings
warnings.filterwarnings('ignore')

def calculate_xirr(cash_flows, guess=0.1):
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

def run_strategy(mom_file, val_file, signal_type='6M', sip=10000):
    mom_df = pd.read_csv(mom_file)
    mom_df['Date'] = pd.to_datetime(mom_df['Date'])
    mom_df = mom_df.rename(columns={'Close': 'Close_mom'})
    
    val_df = pd.read_csv(val_file)
    val_df['Date'] = pd.to_datetime(val_df['Date'])
    val_df = val_df.rename(columns={'Close': 'Close_val'})
    
    df = pd.merge(mom_df[['Date', 'Close_mom']], val_df[['Date', 'Close_val']], on='Date', how='inner')
    df['Return_mom'] = df['Close_mom'].pct_change()
    df['Return_val'] = df['Close_val'].pct_change()
    
    # Compute signals
    df['RelMom_3M'] = df['Close_mom'].pct_change(3) - df['Close_val'].pct_change(3)
    df['RelMom_6M'] = df['Close_mom'].pct_change(6) - df['Close_val'].pct_change(6)
    df['RelMom_9M'] = df['Close_mom'].pct_change(9) - df['Close_val'].pct_change(9)
    
    # Composite: 50% 6M + 25% 9M + 25% 3M
    df['RelMom_Composite'] = (
        0.50 * df['RelMom_6M'] +
        0.25 * df['RelMom_9M'] +
        0.25 * df['RelMom_3M']
    )
    
    if signal_type == '6M':
        signal_col = 'RelMom_6M'
    elif signal_type == 'composite':
        signal_col = 'RelMom_Composite'
    
    df['regime'] = np.where(df[signal_col] > 0, 'momentum', 'value')
    df['regime'] = df['regime'].shift(1).fillna('value')
    
    df['w_mom'] = np.where(df['regime'] == 'momentum', 1.0, 0.0)
    df['w_val'] = 1.0 - df['w_mom']
    df['Portfolio_Return'] = df['w_mom'] * df['Return_mom'] + df['w_val'] * df['Return_val']
    df['Portfolio_NAV'] = 1000 * (1 + df['Portfolio_Return']).cumprod()
    df.loc[0, 'Portfolio_NAV'] = 1000
    
    # SIP
    sip_data = df[['Date', 'Portfolio_NAV']].rename(columns={'Portfolio_NAV': 'NAV'}).dropna()
    sip_data['Units'] = sip / sip_data['NAV']
    sip_data['Cum_Units'] = sip_data['Units'].cumsum()
    sip_data['Invested'] = sip * (np.arange(len(sip_data)) + 1)
    sip_data['Value'] = sip_data['Cum_Units'] * sip_data['NAV']
    sip_data['Peak'] = sip_data['Value'].cummax()
    sip_data['DD'] = (sip_data['Value'] - sip_data['Peak']) / sip_data['Peak'] * 100
    
    final = sip_data['Value'].iloc[-1]
    invested = sip_data['Invested'].iloc[-1]
    max_dd = sip_data['DD'].min()
    
    cfs = [(r['Date'], -sip) for _, r in sip_data.iterrows()]
    cfs.append((sip_data['Date'].iloc[-1], final))
    xirr = calculate_xirr(cfs)
    
    years = len(sip_data) / 12
    cagr = ((sip_data['NAV'].iloc[-1] / sip_data['NAV'].iloc[0]) ** (1/years) - 1) * 100
    switches = (df['regime'] != df['regime'].shift(1)).sum() - 1
    
    # 2025 return
    df_2025 = df[df['Date'].dt.year == 2025]
    ret_2025 = (1 + df_2025['Portfolio_Return']).prod() - 1 if len(df_2025) > 0 else 0
    
    return {
        'cagr': cagr, 'xirr': xirr, 'max_dd': max_dd,
        'switches': switches, 'final': final,
        'ret_2025': ret_2025 * 100
    }

def main():
    base = Path(__file__).parent.parent
    
    configs = [
        {
            'name': 'NIFTY 200',
            'mom': base / 'nifty200' / 'output' / 'monthly' / 'nifty200_momentum_30_monthly.csv',
            'val': base / 'nifty200' / 'output' / 'monthly' / 'nifty200_value_30_monthly.csv',
        },
        {
            'name': 'NIFTY 500',
            'mom': base / 'nifty500' / 'output' / 'monthly' / 'nifty500_momentum_50_monthly.csv',
            'val': base / 'nifty500' / 'output' / 'monthly' / 'nifty500_value_50_monthly.csv',
        },
    ]
    
    for cfg in configs:
        print(f"\n{'='*80}")
        print(f"  {cfg['name']} — MONTHLY ROTATION (100/0)")
        print(f"{'='*80}")
        
        r6 = run_strategy(cfg['mom'], cfg['val'], '6M')
        rc = run_strategy(cfg['mom'], cfg['val'], 'composite')
        
        print(f"\n{'Metric':<20s}  {'Single 6M':>14s}  {'Composite':>14s}  {'Delta':>10s}")
        print("-" * 62)
        rows = [
            ('Index CAGR', f"{r6['cagr']:.2f}%", f"{rc['cagr']:.2f}%", f"{rc['cagr']-r6['cagr']:+.2f}%"),
            ('SIP XIRR', f"{r6['xirr']:.2f}%", f"{rc['xirr']:.2f}%", f"{rc['xirr']-r6['xirr']:+.2f}%"),
            ('Max Drawdown', f"{r6['max_dd']:.2f}%", f"{rc['max_dd']:.2f}%", f"{rc['max_dd']-r6['max_dd']:+.2f}%"),
            ('Switches', f"{r6['switches']:.0f}", f"{rc['switches']:.0f}", f"{rc['switches']-r6['switches']:+.0f}"),
            ('2025 Return', f"{r6['ret_2025']:.2f}%", f"{rc['ret_2025']:.2f}%", f"{rc['ret_2025']-r6['ret_2025']:+.2f}%"),
            ('Final Value', f"₹{r6['final']:,.0f}", f"₹{rc['final']:,.0f}", ""),
        ]
        for label, v1, v2, delta in rows:
            print(f"{label:<20s}  {v1:>14s}  {v2:>14s}  {delta:>10s}")

if __name__ == "__main__":
    main()
