"""
Test multiple composite weightings to find optimal balance
Quarterly 75/25 allocation
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

def run_quarterly_strategy(mom_file, val_file, w6m=1.0, w3m=0.0, sip=10000):
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
    
    # Compute signals
    df['RelMom_6M'] = df['Close_mom'].pct_change(6) - df['Close_val'].pct_change(6)
    df['RelMom_3M'] = df['Close_mom'].pct_change(3) - df['Close_val'].pct_change(3)
    
    # Composite with custom weights
    df['RelMom_Signal'] = w6m * df['RelMom_6M'] + w3m * df['RelMom_3M']
    
    # Quarterly decision
    quarterly = df.groupby('Quarter').last()
    quarterly['regime'] = np.where(quarterly['RelMom_Signal'] > 0, 'momentum', 'value')
    quarterly['regime_exec'] = quarterly['regime'].shift(1)
    
    df = df.merge(quarterly[['regime_exec']], left_on='Quarter', right_index=True, how='left')
    df['regime'] = df['regime_exec'].ffill().fillna('value')
    
    # 75/25 allocation
    df['w_mom'] = np.where(df['regime'] == 'momentum', 0.75, 0.25)
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
    max_dd = sip_data['DD'].min()
    
    cfs = [(r['Date'], -sip) for _, r in sip_data.iterrows()]
    cfs.append((sip_data['Date'].iloc[-1], final))
    xirr = calculate_xirr(cfs)
    
    years = len(sip_data) / 12
    cagr = ((sip_data['NAV'].iloc[-1] / sip_data['NAV'].iloc[0]) ** (1/years) - 1) * 100
    switches = (df['regime'] != df['regime'].shift(1)).sum() - 1
    
    return {'cagr': cagr, 'xirr': xirr, 'max_dd': max_dd, 'switches': switches}

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
    
    # Test different weightings
    weightings = [
        (1.00, 0.00, '100% 6M'),
        (0.80, 0.20, '80/20'),
        (0.70, 0.30, '70/30'),
        (0.60, 0.40, '60/40'),
        (0.50, 0.50, '50/50'),
    ]
    
    for cfg in configs:
        print(f"\n{'='*85}")
        print(f"  {cfg['name']} — QUARTERLY ROTATION (75/25) — COMPOSITE WEIGHTING TEST")
        print(f"{'='*85}")
        print(f"\n{'Weighting':<12s}  {'CAGR':>8s}  {'XIRR':>8s}  {'Max DD':>8s}  {'Switches':>9s}  {'vs 100% 6M':>12s}")
        print("-" * 85)
        
        baseline = None
        for w6, w3, label in weightings:
            r = run_quarterly_strategy(cfg['mom'], cfg['val'], w6, w3)
            if baseline is None:
                baseline = r
            
            delta_xirr = r['xirr'] - baseline['xirr']
            delta_str = f"{delta_xirr:+.2f}%" if w6 < 1.0 else "baseline"
            
            print(f"{label:<12s}  {r['cagr']:>7.2f}%  {r['xirr']:>7.2f}%  {r['max_dd']:>7.2f}%  {r['switches']:>9.0f}  {delta_str:>12s}")

if __name__ == "__main__":
    main()
