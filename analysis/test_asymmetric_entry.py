"""
Test asymmetric entry/exit for portfolio regime filter
Exit: 10M MA (conservative)
Entry: 6M MA (aggressive)
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

def run_strategy(mom_file, val_file, exit_ma=10, entry_ma=10, sip=10000):
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
    
    # Signals
    df['RelMom_6M'] = df['Close_mom'].pct_change(6) - df['Close_val'].pct_change(6)
    df['RelMom_3M'] = df['Close_mom'].pct_change(3) - df['Close_val'].pct_change(3)
    df['RelMom_Signal'] = 0.7 * df['RelMom_6M'] + 0.3 * df['RelMom_3M']
    
    # Quarterly decision
    quarterly = df.groupby('Quarter').last()
    quarterly['regime'] = np.where(quarterly['RelMom_Signal'] > 0, 'momentum', 'value')
    quarterly['regime_exec'] = quarterly['regime'].shift(1)
    
    df = df.merge(quarterly[['regime_exec']], left_on='Quarter', right_index=True, how='left')
    df['regime'] = df['regime_exec'].ffill().fillna('value')
    
    # 75/25 allocation
    df['w_mom'] = np.where(df['regime'] == 'momentum', 0.75, 0.25)
    df['w_val'] = 1.0 - df['w_mom']
    
    # Raw portfolio (before cash filter)
    df['Portfolio_Return_Raw'] = df['w_mom'] * df['Return_mom'] + df['w_val'] * df['Return_val']
    df['Portfolio_NAV_Raw'] = 1000 * (1 + df['Portfolio_Return_Raw']).cumprod()
    df.loc[0, 'Portfolio_NAV_Raw'] = 1000
    
    # Asymmetric cash filter with state machine
    df['Port_MA_Exit'] = df['Portfolio_NAV_Raw'].rolling(exit_ma).mean()
    df['Port_MA_Entry'] = df['Portfolio_NAV_Raw'].rolling(entry_ma).mean()
    
    # State machine for asymmetric entry/exit
    risk_on = []
    current_state = True  # Start risk-on
    
    for i in range(len(df)):
        nav = df['Portfolio_NAV_Raw'].iloc[i]
        ma_exit = df['Port_MA_Exit'].iloc[i]
        ma_entry = df['Port_MA_Entry'].iloc[i]
        
        if pd.isna(ma_exit) or pd.isna(ma_entry):
            current_state = True
        elif current_state:  # Currently risk-on
            if nav < ma_exit:  # Exit on slow MA
                current_state = False
        else:  # Currently in cash
            if nav > ma_entry:  # Re-enter on fast MA
                current_state = True
        
        risk_on.append(current_state)
    
    df['risk_on'] = risk_on
    
    # Apply cash filter
    df['w_mom_final'] = df['w_mom'] * df['risk_on']
    df['w_val_final'] = df['w_val'] * df['risk_on']
    df['w_cash'] = 1.0 - (df['w_mom_final'] + df['w_val_final'])
    
    df['Portfolio_Return'] = (
        df['w_mom_final'] * df['Return_mom'] + 
        df['w_val_final'] * df['Return_val']
    )
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
    
    # Max portfolio DD
    df['Peak_NAV'] = df['Portfolio_NAV'].cummax()
    df['DD_NAV'] = (df['Portfolio_NAV'] - df['Peak_NAV']) / df['Peak_NAV'] * 100
    max_port_dd = df['DD_NAV'].min()
    
    cash_months = (~df['risk_on']).sum()
    regime_switches = (df['risk_on'] != df['risk_on'].shift(1)).sum() - 1
    
    return {
        'cagr': cagr, 'xirr': xirr, 'max_dd': max_dd,
        'max_port_dd': max_port_dd, 'cash_months': cash_months,
        'regime_switches': regime_switches, 'final': final
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
    
    # Test different entry/exit combinations
    tests = [
        (10, 10, 'Symmetric 10/10'),
        (10, 6, 'Asymmetric 10/6 (Recommended)'),
        (10, 5, 'Asymmetric 10/5'),
        (10, 3, 'Asymmetric 10/3'),
    ]
    
    for cfg in configs:
        print(f"\n{'='*90}")
        print(f"  {cfg['name']} — ASYMMETRIC ENTRY/EXIT TEST")
        print(f"{'='*90}")
        print(f"\n{'Config':<30s}  {'CAGR':>8s}  {'XIRR':>8s}  {'Port DD':>8s}  {'Cash':>6s}  {'Switches':>9s}")
        print("-" * 90)
        
        for exit_ma, entry_ma, label in tests:
            r = run_strategy(cfg['mom'], cfg['val'], exit_ma, entry_ma)
            print(f"{label:<30s}  {r['cagr']:>7.2f}%  {r['xirr']:>7.2f}%  {r['max_port_dd']:>7.2f}%  {r['cash_months']:>6.0f}  {r['regime_switches']:>9.0f}")

if __name__ == "__main__":
    main()
