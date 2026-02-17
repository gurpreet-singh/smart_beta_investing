"""
Deep audit: Where is alpha being made/lost?
Nifty 500 strategy vs pure momentum, pure value, 50/50 blend
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

base = Path(__file__).parent.parent

for universe, mom_file, val_file in [
    ('NIFTY 200',
     base / 'nifty200' / 'output' / 'monthly' / 'nifty200_momentum_30_monthly.csv',
     base / 'nifty200' / 'output' / 'monthly' / 'nifty200_value_30_monthly.csv'),
    ('NIFTY 500',
     base / 'nifty500' / 'output' / 'monthly' / 'nifty500_momentum_50_monthly.csv',
     base / 'nifty500' / 'output' / 'monthly' / 'nifty500_value_50_monthly.csv'),
]:
    mom_df = pd.read_csv(mom_file)
    mom_df['Date'] = pd.to_datetime(mom_df['Date'])
    mom_df = mom_df.rename(columns={'Close': 'Close_mom'})
    
    val_df = pd.read_csv(val_file)
    val_df['Date'] = pd.to_datetime(val_df['Date'])
    val_df = val_df.rename(columns={'Close': 'Close_val'})
    
    df = pd.merge(mom_df[['Date', 'Close_mom']], val_df[['Date', 'Close_val']], on='Date', how='inner')
    df['Return_mom'] = df['Close_mom'].pct_change()
    df['Return_val'] = df['Close_val'].pct_change()
    df['Return_5050'] = 0.5 * df['Return_mom'] + 0.5 * df['Return_val']
    
    # Strategy
    df['RelMom_6M'] = df['Close_mom'].pct_change(6) - df['Close_val'].pct_change(6)
    df['regime'] = np.where(df['RelMom_6M'] > 0, 'momentum', 'value')
    df['regime'] = df['regime'].shift(1).fillna('value')
    df['w_mom'] = np.where(df['regime'] == 'momentum', 1.0, 0.0)
    df['Return_strat'] = df['w_mom'] * df['Return_mom'] + (1 - df['w_mom']) * df['Return_val']
    
    # NAV series
    df['NAV_mom'] = 1000 * (1 + df['Return_mom']).cumprod()
    df['NAV_val'] = 1000 * (1 + df['Return_val']).cumprod()
    df['NAV_5050'] = 1000 * (1 + df['Return_5050']).cumprod()
    df['NAV_strat'] = 1000 * (1 + df['Return_strat']).cumprod()
    for col in ['NAV_mom', 'NAV_val', 'NAV_5050', 'NAV_strat']:
        df.loc[0, col] = 1000
    
    years = len(df) / 12
    
    print(f"\n{'='*90}")
    print(f"  {universe} — FULL PERIOD CAGR COMPARISON ({df['Date'].iloc[0].strftime('%Y-%m')} to {df['Date'].iloc[-1].strftime('%Y-%m')})")
    print(f"{'='*90}")
    
    cagrs = {}
    for name, col in [('Pure Momentum', 'NAV_mom'), ('Pure Value', 'NAV_val'), 
                       ('50/50 Static', 'NAV_5050'), ('Strategy (6M)', 'NAV_strat')]:
        cagr = ((df[col].iloc[-1] / 1000) ** (1/years) - 1) * 100
        cagrs[name] = cagr
        print(f"  {name:<20s}: {cagr:>7.2f}%  (Final NAV: ₹{df[col].iloc[-1]:>10,.0f})")
    
    print(f"\n  Strategy alpha vs 50/50:     {cagrs['Strategy (6M)'] - cagrs['50/50 Static']:+.2f}%")
    print(f"  Strategy alpha vs best:      {cagrs['Strategy (6M)'] - max(cagrs['Pure Momentum'], cagrs['Pure Value']):+.2f}%")
    
    # Year-by-year comparison
    df['Year'] = df['Date'].dt.year
    print(f"\n{'Year':>6s} {'Mom':>8s} {'Val':>8s} {'50/50':>8s} {'Strat':>8s} {'Alpha':>8s} {'Regime':>20s}")
    print("-" * 65)
    
    for year in sorted(df['Year'].unique()):
        yr = df[df['Year'] == year]
        ret_m = (1 + yr['Return_mom']).prod() - 1
        ret_v = (1 + yr['Return_val']).prod() - 1
        ret_50 = (1 + yr['Return_5050']).prod() - 1
        ret_s = (1 + yr['Return_strat']).prod() - 1
        alpha = ret_s - ret_50
        
        # What regime was dominant this year?
        mom_months = (yr['regime'] == 'momentum').sum()
        val_months = (yr['regime'] == 'value').sum()
        regime_str = f"M:{mom_months} V:{val_months}"
        
        # Color-code alpha
        alpha_str = f"{alpha*100:+.1f}%"
        better = max(ret_m, ret_v)
        winner = "MOM" if ret_m > ret_v else "VAL"
        was_right = (winner == "MOM" and mom_months > val_months) or (winner == "VAL" and val_months > mom_months)
        mark = "✅" if was_right else "❌"
        
        print(f"{year:>6d} {ret_m*100:>7.1f}% {ret_v*100:>7.1f}% {ret_50*100:>7.1f}% {ret_s*100:>7.1f}% {alpha_str:>8s} {regime_str:>10s}  {mark} {winner} won")
    
    # Accuracy
    correct = 0
    total_years = 0
    for year in sorted(df['Year'].unique()):
        yr = df[df['Year'] == year]
        ret_m = (1 + yr['Return_mom']).prod() - 1
        ret_v = (1 + yr['Return_val']).prod() - 1
        mom_months = (yr['regime'] == 'momentum').sum()
        val_months = (yr['regime'] == 'value').sum()
        winner = "MOM" if ret_m > ret_v else "VAL"
        was_right = (winner == "MOM" and mom_months > val_months) or (winner == "VAL" and val_months > mom_months)
        if was_right:
            correct += 1
        total_years += 1
    
    print(f"\n  Regime accuracy: {correct}/{total_years} years ({correct/total_years*100:.0f}%)")
    
    # SIP XIRR for all 4
    print(f"\n  SIP XIRR Comparison (₹10,000/month):")
    for name, ret_col in [('Pure Momentum', 'Return_mom'), ('Pure Value', 'Return_val'),
                           ('50/50 Static', 'Return_5050'), ('Strategy (6M)', 'Return_strat')]:
        nav = 1000 * (1 + df[ret_col]).cumprod()
        nav.iloc[0] = 1000
        sip = 10000
        units = sip / nav
        cum_units = units.cumsum()
        value = cum_units * nav
        
        cfs = [(d, -sip) for d in df['Date']]
        cfs.append((df['Date'].iloc[-1], value.iloc[-1]))
        xirr = calculate_xirr(cfs)
        print(f"    {name:<20s}: {xirr:>7.2f}%")
