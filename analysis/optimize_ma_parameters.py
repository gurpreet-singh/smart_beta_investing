"""
Test different MA parameters for portfolio regime filter
Goal: Find optimal balance between drawdown protection and rally capture
"""
import pandas as pd
import numpy as np
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).parent.parent / 'nifty200' / 'analysis'))
from nifty200_portfolio_strategy import PortfolioStrategy

def test_ma_parameters(exit_ma, entry_ma, universe='nifty200'):
    """Test a specific MA parameter combination"""
    
    if universe == 'nifty200':
        data_file = Path(__file__).parent.parent / 'nifty200' / 'output' / 'monthly' / 'portfolio_ratio_trend_75_25.csv'
    else:
        data_file = Path(__file__).parent.parent / 'nifty500' / 'output' / 'monthly' / 'nifty500_portfolio_ratio_trend_75_25.csv'
    
    # Load data
    df = pd.read_csv(data_file)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)
    
    # Reconstruct RAW weights from regime (before cash filter)
    df['w_mom_raw'] = df['regime'].apply(lambda x: 0.75 if x == 'momentum' else 0.25)
    df['w_val_raw'] = df['regime'].apply(lambda x: 0.25 if x == 'momentum' else 0.75)
    
    # Calculate raw returns (before cash filter)
    df['Portfolio_Return_Raw'] = df['w_mom_raw'] * df['Return_mom'] + df['w_val_raw'] * df['Return_val']
    df['Portfolio_NAV_Raw'] = 1000 * (1 + df['Portfolio_Return_Raw']).cumprod()
    df.loc[0, 'Portfolio_NAV_Raw'] = 1000
    
    # Apply MA filter with custom parameters
    df['Port_MA_Exit'] = df['Portfolio_NAV_Raw'].rolling(exit_ma).mean()
    df['Port_MA_Entry'] = df['Portfolio_NAV_Raw'].rolling(entry_ma).mean()
    
    # State machine
    risk_on = []
    current_state = True
    
    for i in range(len(df)):
        nav = df['Portfolio_NAV_Raw'].iloc[i]
        ma_exit = df['Port_MA_Exit'].iloc[i]
        ma_entry = df['Port_MA_Entry'].iloc[i]
        
        if pd.isna(ma_exit) or pd.isna(ma_entry):
            current_state = True
        elif current_state:
            if nav < ma_exit:
                current_state = False
        else:
            if nav > ma_entry:
                current_state = True
        
        risk_on.append(current_state)
    
    df['risk_on'] = risk_on
    df['risk_on'] = df['risk_on'].shift(1).fillna(True)  # Prevent lookahead
    
    # Apply cash filter to RAW weights
    df['w_mom_final'] = df['w_mom_raw'] * df['risk_on']
    df['w_val_final'] = df['w_val_raw'] * df['risk_on']
    df['Portfolio_Return'] = df['w_mom_final'] * df['Return_mom'] + df['w_val_final'] * df['Return_val']
    df['Portfolio_NAV'] = 1000 * (1 + df['Portfolio_Return']).cumprod()
    df.loc[0, 'Portfolio_NAV'] = 1000
    
    # Calculate metrics
    years = len(df) / 12
    cagr = ((df['Portfolio_NAV'].iloc[-1] / 1000) ** (1/years) - 1) * 100
    
    # Max drawdown
    running_max = df['Portfolio_NAV'].cummax()
    drawdown = (df['Portfolio_NAV'] - running_max) / running_max * 100
    max_dd = drawdown.min()
    
    # Cash months
    cash_months = (~df['risk_on']).sum()
    cash_pct = cash_months / len(df) * 100
    
    # 2012 performance (the problematic year)
    df_2012 = df[df['Date'].dt.year == 2012]
    ret_2012 = ((1 + df_2012['Portfolio_Return']).prod() - 1) * 100 if len(df_2012) > 0 else 0
    
    return {
        'exit_ma': exit_ma,
        'entry_ma': entry_ma,
        'cagr': cagr,
        'max_dd': max_dd,
        'mar_ratio': cagr / abs(max_dd) if max_dd != 0 else 0,
        'cash_months': cash_months,
        'cash_pct': cash_pct,
        'ret_2012': ret_2012
    }

def main():
    print("="*80)
    print("  MA PARAMETER OPTIMIZATION")
    print("="*80)
    
    # Test different combinations
    # Format: (exit_ma, entry_ma)
    params_to_test = [
        (10, 10),  # Symmetric (baseline)
        (10, 6),   # Current asymmetric
        (10, 4),   # More responsive entry
        (8, 6),    # Faster exit, moderate entry
        (8, 4),    # Both faster
        (12, 6),   # Slower exit, moderate entry
        (12, 8),   # Both slower
        (6, 4),    # Very responsive
    ]
    
    results_200 = []
    results_500 = []
    
    print("\n🔍 Testing Nifty 200...")
    for exit_ma, entry_ma in params_to_test:
        result = test_ma_parameters(exit_ma, entry_ma, 'nifty200')
        results_200.append(result)
        print(f"  {exit_ma}/{entry_ma}: CAGR={result['cagr']:.2f}% | DD={result['max_dd']:.2f}% | MAR={result['mar_ratio']:.2f} | 2012={result['ret_2012']:.1f}%")
    
    print("\n🔍 Testing Nifty 500...")
    for exit_ma, entry_ma in params_to_test:
        result = test_ma_parameters(exit_ma, entry_ma, 'nifty500')
        results_500.append(result)
        print(f"  {exit_ma}/{entry_ma}: CAGR={result['cagr']:.2f}% | DD={result['max_dd']:.2f}% | MAR={result['mar_ratio']:.2f} | 2012={result['ret_2012']:.1f}%")
    
    # Create comparison table
    print("\n" + "="*80)
    print("  NIFTY 200 RESULTS")
    print("="*80)
    print(f"{'Exit/Entry':<12} {'CAGR':<8} {'Max DD':<10} {'MAR':<8} {'Cash%':<8} {'2012':<8}")
    print("-"*80)
    for r in results_200:
        print(f"{r['exit_ma']}/{r['entry_ma']:<10} {r['cagr']:>6.2f}%  {r['max_dd']:>8.2f}%  {r['mar_ratio']:>6.2f}  {r['cash_pct']:>6.1f}%  {r['ret_2012']:>6.1f}%")
    
    print("\n" + "="*80)
    print("  NIFTY 500 RESULTS")
    print("="*80)
    print(f"{'Exit/Entry':<12} {'CAGR':<8} {'Max DD':<10} {'MAR':<8} {'Cash%':<8} {'2012':<8}")
    print("-"*80)
    for r in results_500:
        print(f"{r['exit_ma']}/{r['entry_ma']:<10} {r['cagr']:>6.2f}%  {r['max_dd']:>8.2f}%  {r['mar_ratio']:>6.2f}  {r['cash_pct']:>6.1f}%  {r['ret_2012']:>6.1f}%")
    
    # Find best by MAR ratio
    best_200 = max(results_200, key=lambda x: x['mar_ratio'])
    best_500 = max(results_500, key=lambda x: x['mar_ratio'])
    
    print("\n" + "="*80)
    print("  OPTIMAL PARAMETERS (by MAR Ratio)")
    print("="*80)
    print(f"Nifty 200: {best_200['exit_ma']}/{best_200['entry_ma']} → MAR={best_200['mar_ratio']:.2f} | CAGR={best_200['cagr']:.2f}% | DD={best_200['max_dd']:.2f}%")
    print(f"Nifty 500: {best_500['exit_ma']}/{best_500['entry_ma']} → MAR={best_500['mar_ratio']:.2f} | CAGR={best_500['cagr']:.2f}% | DD={best_500['max_dd']:.2f}%")
    print("="*80)

if __name__ == "__main__":
    main()
