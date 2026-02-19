"""
Nifty 200 Momentum 30 - Dynamic SIP Strategy with Drawdown-Based Multipliers

This script backtests a SIP strategy where investment amounts increase based on 
how far the index is from its all-time high:
- Normal SIP (1x): Index within 10% of ATH or at new high
- 2x SIP: Index 10-20% below ATH
- 4x SIP: Index 20-30% below ATH
- 6x SIP: Index 30%+ below ATH

The script includes optimization capabilities to find the best multiplier combinations.
"""

import pandas as pd
import numpy as np
from datetime import datetime
from scipy.optimize import differential_evolution
import itertools
import warnings
warnings.filterwarnings('ignore')


def load_nifty200_momentum_data():
    """Load Nifty 200 Momentum 30 monthly data"""
    file_path = '/Users/personatech/smart_beta_investing/nifty200/output/monthly/nifty200_momentum_30_monthly.csv'
    df = pd.read_csv(file_path)
    df['Date'] = pd.to_datetime(df['Date'])
    df = df.sort_values('Date').reset_index(drop=True)
    return df


def calculate_xirr(cashflows, dates, guess=0.1):
    """
    Calculate XIRR (Extended Internal Rate of Return) for irregular cashflows
    
    Args:
        cashflows: List of cashflow amounts (negative for investments, positive for final value)
        dates: List of dates corresponding to cashflows
        guess: Initial guess for the rate
    
    Returns:
        XIRR as a percentage
    """
    if len(cashflows) != len(dates):
        raise ValueError("Cashflows and dates must have the same length")
    
    # Convert dates to days from first date
    dates = pd.to_datetime(dates)
    start_date = dates[0]
    days = [(d - start_date).days for d in dates]
    
    def xirr_formula(rate):
        """NPV formula for XIRR calculation"""
        return sum([cf / (1 + rate) ** (day / 365.0) for cf, day in zip(cashflows, days)])
    
    try:
        from scipy.optimize import newton
        result = newton(xirr_formula, guess)
        return result * 100  # Convert to percentage
    except:
        # If Newton's method fails, try a simple search
        for rate in np.linspace(-0.99, 3, 1000):
            if abs(xirr_formula(rate)) < 1:
                return rate * 100
        return 0


def simulate_sip(df, base_sip_amount=10000, multipliers=[1, 2, 4, 6], 
                 thresholds=[0, 10, 20, 30], verbose=True):
    """
    Simulate SIP with dynamic multipliers based on drawdown from ATH
    
    Args:
        df: DataFrame with Date and Close columns
        base_sip_amount: Base monthly SIP amount
        multipliers: List of multipliers [normal, 10-20%, 20-30%, 30%+]
        thresholds: Drawdown thresholds in % [0, 10, 20, 30]
        verbose: Print detailed results
    
    Returns:
        Dictionary with performance metrics
    """
    df = df.copy()
    
    # Calculate all-time high (ATH) at each point
    df['ATH'] = df['Close'].expanding().max()
    
    # Calculate drawdown from ATH in percentage
    df['Drawdown_Pct'] = ((df['ATH'] - df['Close']) / df['ATH']) * 100
    
    # Determine SIP multiplier based on drawdown
    def get_multiplier(dd_pct):
        if dd_pct >= thresholds[3]:  # 30%+ below ATH
            return multipliers[3]
        elif dd_pct >= thresholds[2]:  # 20-30% below ATH
            return multipliers[2]
        elif dd_pct >= thresholds[1]:  # 10-20% below ATH
            return multipliers[1]
        else:  # Within 10% of ATH or at new high
            return multipliers[0]
    
    df['Multiplier'] = df['Drawdown_Pct'].apply(get_multiplier)
    df['SIP_Amount'] = base_sip_amount * df['Multiplier']
    
    # Calculate units purchased each month
    df['Units_Purchased'] = df['SIP_Amount'] / df['Close']
    df['Cumulative_Units'] = df['Units_Purchased'].cumsum()
    
    # Calculate portfolio value
    df['Cumulative_Investment'] = df['SIP_Amount'].cumsum()
    df['Portfolio_Value'] = df['Cumulative_Units'] * df['Close']
    
    # Calculate returns
    df['Absolute_Return'] = df['Portfolio_Value'] - df['Cumulative_Investment']
    df['Return_Pct'] = (df['Absolute_Return'] / df['Cumulative_Investment']) * 100
    
    # Prepare cashflows for XIRR calculation
    cashflows = (-df['SIP_Amount'].values).tolist()
    cashflows.append(df['Portfolio_Value'].iloc[-1])  # Final portfolio value
    
    dates = df['Date'].tolist()
    dates.append(df['Date'].iloc[-1])  # Use last date for final value
    
    # Calculate XIRR
    xirr = calculate_xirr(cashflows, dates)
    
    # Calculate CAGR
    years = (df['Date'].iloc[-1] - df['Date'].iloc[0]).days / 365.25
    total_return_multiple = df['Portfolio_Value'].iloc[-1] / df['Cumulative_Investment'].iloc[-1]
    cagr = (total_return_multiple ** (1 / years) - 1) * 100
    
    # Calculate maximum drawdown of portfolio value
    df['Portfolio_Peak'] = df['Portfolio_Value'].expanding().max()
    df['Portfolio_Drawdown'] = ((df['Portfolio_Peak'] - df['Portfolio_Value']) / df['Portfolio_Peak']) * 100
    max_portfolio_dd = df['Portfolio_Drawdown'].max()
    
    # Count multiplier usage
    multiplier_counts = df['Multiplier'].value_counts().sort_index()
    
    results = {
        'xirr': xirr,
        'cagr': cagr,
        'total_invested': df['Cumulative_Investment'].iloc[-1],
        'final_value': df['Portfolio_Value'].iloc[-1],
        'absolute_return': df['Absolute_Return'].iloc[-1],
        'return_pct': df['Return_Pct'].iloc[-1],
        'max_portfolio_drawdown': max_portfolio_dd,
        'total_months': len(df),
        'multiplier_usage': multiplier_counts.to_dict(),
        'avg_sip': df['SIP_Amount'].mean(),
        'max_sip': df['SIP_Amount'].max(),
        'total_units': df['Cumulative_Units'].iloc[-1],
        'avg_cost': df['Cumulative_Investment'].iloc[-1] / df['Cumulative_Units'].iloc[-1],
        'final_nav': df['Close'].iloc[-1],
        'df': df
    }
    
    if verbose:
        print("=" * 80)
        print(f"DYNAMIC SIP STRATEGY BACKTEST RESULTS")
        print(f"Period: {df['Date'].iloc[0].strftime('%Y-%m-%d')} to {df['Date'].iloc[-1].strftime('%Y-%m-%d')}")
        print(f"Duration: {years:.2f} years ({len(df)} months)")
        print("=" * 80)
        print(f"\nSTRATEGY PARAMETERS:")
        print(f"  Base SIP Amount: ₹{base_sip_amount:,.0f}")
        print(f"  Multipliers: {multipliers}")
        print(f"  Thresholds: {thresholds}%")
        print(f"\nMULTIPLIER USAGE:")
        for mult, count in sorted(multiplier_counts.items()):
            pct = (count / len(df)) * 100
            print(f"  {mult}x SIP: {count} months ({pct:.1f}%)")
        print(f"\nINVESTMENT SUMMARY:")
        print(f"  Total Invested: ₹{results['total_invested']:,.0f}")
        print(f"  Average SIP: ₹{results['avg_sip']:,.0f}")
        print(f"  Maximum SIP: ₹{results['max_sip']:,.0f}")
        print(f"\nPORTFOLIO METRICS:")
        print(f"  Final Value: ₹{results['final_value']:,.0f}")
        print(f"  Absolute Return: ₹{results['absolute_return']:,.0f}")
        print(f"  Return %: {results['return_pct']:.2f}%")
        print(f"  Total Units: {results['total_units']:,.2f}")
        print(f"  Average Cost: ₹{results['avg_cost']:,.2f}")
        print(f"  Final NAV: ₹{results['final_nav']:,.2f}")
        print(f"\nPERFORMANCE METRICS:")
        print(f"  XIRR: {results['xirr']:.2f}%")
        print(f"  CAGR: {results['cagr']:.2f}%")
        print(f"  Max Portfolio Drawdown: {results['max_portfolio_drawdown']:.2f}%")
        print("=" * 80)
    
    return results


def simulate_regular_sip(df, sip_amount=10000, verbose=True):
    """
    Simulate regular SIP with fixed amount
    
    Args:
        df: DataFrame with Date and Close columns
        sip_amount: Fixed monthly SIP amount
        verbose: Print detailed results
    
    Returns:
        Dictionary with performance metrics
    """
    return simulate_sip(df, base_sip_amount=sip_amount, multipliers=[1, 1, 1, 1], 
                       thresholds=[0, 10, 20, 30], verbose=verbose)


def compare_strategies(df, base_sip=10000, dynamic_multipliers=[1, 2, 4, 6], 
                       dynamic_thresholds=[0, 10, 20, 30]):
    """
    Compare dynamic SIP strategy with regular SIP
    
    Args:
        df: DataFrame with Date and Close columns
        base_sip: Base SIP amount
        dynamic_multipliers: Multipliers for dynamic strategy
        dynamic_thresholds: Thresholds for dynamic strategy
    
    Returns:
        Comparison DataFrame
    """
    print("\n" + "=" * 80)
    print("REGULAR SIP (BASELINE)")
    print("=" * 80)
    regular_results = simulate_regular_sip(df, sip_amount=base_sip, verbose=True)
    
    print("\n" + "=" * 80)
    print("DYNAMIC SIP (DRAWDOWN-BASED MULTIPLIERS)")
    print("=" * 80)
    dynamic_results = simulate_sip(df, base_sip_amount=base_sip, 
                                   multipliers=dynamic_multipliers,
                                   thresholds=dynamic_thresholds, verbose=True)
    
    # Create comparison
    comparison = pd.DataFrame({
        'Metric': ['XIRR (%)', 'CAGR (%)', 'Total Invested (₹)', 'Final Value (₹)', 
                   'Absolute Return (₹)', 'Return %', 'Max Portfolio DD (%)', 
                   'Avg SIP (₹)', 'Max SIP (₹)'],
        'Regular SIP': [
            regular_results['xirr'],
            regular_results['cagr'],
            regular_results['total_invested'],
            regular_results['final_value'],
            regular_results['absolute_return'],
            regular_results['return_pct'],
            regular_results['max_portfolio_drawdown'],
            regular_results['avg_sip'],
            regular_results['max_sip']
        ],
        'Dynamic SIP': [
            dynamic_results['xirr'],
            dynamic_results['cagr'],
            dynamic_results['total_invested'],
            dynamic_results['final_value'],
            dynamic_results['absolute_return'],
            dynamic_results['return_pct'],
            dynamic_results['max_portfolio_drawdown'],
            dynamic_results['avg_sip'],
            dynamic_results['max_sip']
        ]
    })
    
    comparison['Difference'] = comparison['Dynamic SIP'] - comparison['Regular SIP']
    comparison['Improvement %'] = (comparison['Difference'] / comparison['Regular SIP'].abs()) * 100
    
    print("\n" + "=" * 80)
    print("STRATEGY COMPARISON")
    print("=" * 80)
    print(comparison.to_string(index=False))
    print("\n" + "=" * 80)
    print(f"XIRR Improvement: {dynamic_results['xirr'] - regular_results['xirr']:.2f} percentage points")
    print(f"CAGR Improvement: {dynamic_results['cagr'] - regular_results['cagr']:.2f} percentage points")
    print(f"Additional Investment Required: ₹{dynamic_results['total_invested'] - regular_results['total_invested']:,.0f}")
    print(f"Additional Wealth Created: ₹{dynamic_results['final_value'] - regular_results['final_value']:,.0f}")
    print("=" * 80)
    
    return comparison, regular_results, dynamic_results


def optimize_multipliers_grid_search(df, base_sip=10000, 
                                     multiplier_ranges=[[1], [1.5, 2, 2.5, 3], 
                                                       [3, 4, 5, 6], [5, 6, 7, 8, 10]],
                                     thresholds=[0, 10, 20, 30]):
    """
    Grid search to find optimal multipliers
    
    Args:
        df: DataFrame with Date and Close columns
        base_sip: Base SIP amount
        multiplier_ranges: List of possible values for each multiplier
        thresholds: Fixed thresholds
    
    Returns:
        Best parameters and results
    """
    print("\n" + "=" * 80)
    print("GRID SEARCH OPTIMIZATION")
    print("=" * 80)
    print(f"Testing {np.prod([len(r) for r in multiplier_ranges])} combinations...")
    
    best_xirr = -np.inf
    best_params = None
    best_results = None
    all_results = []
    
    # Generate all combinations
    for combo in itertools.product(*multiplier_ranges):
        multipliers = list(combo)
        
        # Skip invalid combinations (multipliers should be increasing)
        if not all(multipliers[i] <= multipliers[i+1] for i in range(len(multipliers)-1)):
            continue
        
        try:
            results = simulate_sip(df, base_sip_amount=base_sip, 
                                  multipliers=multipliers,
                                  thresholds=thresholds, verbose=False)
            
            all_results.append({
                'multipliers': multipliers,
                'xirr': results['xirr'],
                'cagr': results['cagr'],
                'max_dd': results['max_portfolio_drawdown'],
                'total_invested': results['total_invested'],
                'final_value': results['final_value']
            })
            
            if results['xirr'] > best_xirr:
                best_xirr = results['xirr']
                best_params = multipliers
                best_results = results
        except:
            continue
    
    # Sort results by XIRR
    all_results_df = pd.DataFrame(all_results)
    all_results_df = all_results_df.sort_values('xirr', ascending=False).reset_index(drop=True)
    
    print(f"\nTested {len(all_results)} valid combinations")
    print(f"\nTOP 10 STRATEGIES BY XIRR:")
    print("-" * 80)
    for idx, row in all_results_df.head(10).iterrows():
        print(f"{idx+1}. Multipliers: {row['multipliers']} | XIRR: {row['xirr']:.2f}% | "
              f"CAGR: {row['cagr']:.2f}% | Max DD: {row['max_dd']:.2f}%")
    
    print("\n" + "=" * 80)
    print("BEST STRATEGY (HIGHEST XIRR)")
    print("=" * 80)
    print(f"Optimal Multipliers: {best_params}")
    print(f"XIRR: {best_xirr:.2f}%")
    
    return best_params, best_results, all_results_df


def optimize_thresholds_grid_search(df, base_sip=10000, multipliers=[1, 2, 4, 6],
                                    threshold_ranges=[[0], [5, 10, 15], 
                                                     [15, 20, 25], [25, 30, 35, 40]]):
    """
    Grid search to find optimal thresholds
    
    Args:
        df: DataFrame with Date and Close columns
        base_sip: Base SIP amount
        multipliers: Fixed multipliers
        threshold_ranges: List of possible values for each threshold
    
    Returns:
        Best parameters and results
    """
    print("\n" + "=" * 80)
    print("THRESHOLD OPTIMIZATION")
    print("=" * 80)
    print(f"Testing {np.prod([len(r) for r in threshold_ranges])} combinations...")
    
    best_xirr = -np.inf
    best_params = None
    best_results = None
    all_results = []
    
    # Generate all combinations
    for combo in itertools.product(*threshold_ranges):
        thresholds = list(combo)
        
        # Skip invalid combinations (thresholds should be increasing)
        if not all(thresholds[i] < thresholds[i+1] for i in range(len(thresholds)-1)):
            continue
        
        try:
            results = simulate_sip(df, base_sip_amount=base_sip, 
                                  multipliers=multipliers,
                                  thresholds=thresholds, verbose=False)
            
            all_results.append({
                'thresholds': thresholds,
                'xirr': results['xirr'],
                'cagr': results['cagr'],
                'max_dd': results['max_portfolio_drawdown'],
                'total_invested': results['total_invested'],
                'final_value': results['final_value']
            })
            
            if results['xirr'] > best_xirr:
                best_xirr = results['xirr']
                best_params = thresholds
                best_results = results
        except:
            continue
    
    # Sort results by XIRR
    all_results_df = pd.DataFrame(all_results)
    all_results_df = all_results_df.sort_values('xirr', ascending=False).reset_index(drop=True)
    
    print(f"\nTested {len(all_results)} valid combinations")
    print(f"\nTOP 10 THRESHOLD CONFIGURATIONS BY XIRR:")
    print("-" * 80)
    for idx, row in all_results_df.head(10).iterrows():
        print(f"{idx+1}. Thresholds: {row['thresholds']}% | XIRR: {row['xirr']:.2f}% | "
              f"CAGR: {row['cagr']:.2f}% | Max DD: {row['max_dd']:.2f}%")
    
    print("\n" + "=" * 80)
    print("BEST THRESHOLD CONFIGURATION (HIGHEST XIRR)")
    print("=" * 80)
    print(f"Optimal Thresholds: {best_params}%")
    print(f"XIRR: {best_xirr:.2f}%")
    
    return best_params, best_results, all_results_df


def full_optimization(df, base_sip=10000):
    """
    Comprehensive optimization of both multipliers and thresholds
    
    Args:
        df: DataFrame with Date and Close columns
        base_sip: Base SIP amount
    
    Returns:
        Best parameters and results
    """
    print("\n" + "=" * 80)
    print("COMPREHENSIVE OPTIMIZATION (MULTIPLIERS + THRESHOLDS)")
    print("=" * 80)
    
    # Define search space
    multiplier_options = [
        [1],  # Normal (fixed)
        [1.5, 2, 2.5, 3],  # 10-20% drawdown
        [3, 4, 5, 6],  # 20-30% drawdown
        [5, 6, 7, 8, 10]  # 30%+ drawdown
    ]
    
    threshold_options = [
        [0],  # Normal (fixed)
        [5, 8, 10, 12, 15],  # First threshold
        [15, 18, 20, 22, 25],  # Second threshold
        [25, 28, 30, 35, 40]  # Third threshold
    ]
    
    best_xirr = -np.inf
    best_multipliers = None
    best_thresholds = None
    best_results = None
    all_results = []
    
    total_combos = (np.prod([len(r) for r in multiplier_options]) * 
                   np.prod([len(r) for r in threshold_options]))
    print(f"Testing up to {total_combos} combinations...")
    
    tested = 0
    for mult_combo in itertools.product(*multiplier_options):
        multipliers = list(mult_combo)
        
        # Skip invalid multiplier combinations
        if not all(multipliers[i] <= multipliers[i+1] for i in range(len(multipliers)-1)):
            continue
        
        for thresh_combo in itertools.product(*threshold_options):
            thresholds = list(thresh_combo)
            
            # Skip invalid threshold combinations
            if not all(thresholds[i] < thresholds[i+1] for i in range(len(thresholds)-1)):
                continue
            
            try:
                results = simulate_sip(df, base_sip_amount=base_sip, 
                                      multipliers=multipliers,
                                      thresholds=thresholds, verbose=False)
                
                tested += 1
                
                all_results.append({
                    'multipliers': multipliers,
                    'thresholds': thresholds,
                    'xirr': results['xirr'],
                    'cagr': results['cagr'],
                    'max_dd': results['max_portfolio_drawdown'],
                    'total_invested': results['total_invested'],
                    'final_value': results['final_value'],
                    'avg_sip': results['avg_sip']
                })
                
                if results['xirr'] > best_xirr:
                    best_xirr = results['xirr']
                    best_multipliers = multipliers
                    best_thresholds = thresholds
                    best_results = results
            except:
                continue
    
    # Sort results by XIRR
    all_results_df = pd.DataFrame(all_results)
    all_results_df = all_results_df.sort_values('xirr', ascending=False).reset_index(drop=True)
    
    print(f"\nTested {tested} valid combinations")
    print(f"\nTOP 15 STRATEGIES BY XIRR:")
    print("-" * 100)
    for idx, row in all_results_df.head(15).iterrows():
        print(f"{idx+1}. Mult: {row['multipliers']} | Thresh: {row['thresholds']}% | "
              f"XIRR: {row['xirr']:.2f}% | CAGR: {row['cagr']:.2f}% | "
              f"MaxDD: {row['max_dd']:.2f}% | AvgSIP: ₹{row['avg_sip']:,.0f}")
    
    print("\n" + "=" * 80)
    print("OPTIMAL STRATEGY (HIGHEST XIRR)")
    print("=" * 80)
    print(f"Optimal Multipliers: {best_multipliers}")
    print(f"Optimal Thresholds: {best_thresholds}%")
    print(f"XIRR: {best_xirr:.2f}%")
    
    return best_multipliers, best_thresholds, best_results, all_results_df


def main():
    """Main execution function"""
    print("\n" + "=" * 80)
    print("NIFTY 200 MOMENTUM 30 - DYNAMIC SIP ANALYSIS")
    print("=" * 80)
    
    # Load data
    df = load_nifty200_momentum_data()
    print(f"\nLoaded data: {len(df)} months from {df['Date'].iloc[0].strftime('%Y-%m-%d')} "
          f"to {df['Date'].iloc[-1].strftime('%Y-%m-%d')}")
    
    # Base SIP amount
    base_sip = 10000
    
    # 1. Compare original strategy with regular SIP
    print("\n" + "=" * 80)
    print("PART 1: BASELINE COMPARISON")
    print("=" * 80)
    comparison, regular_results, dynamic_results = compare_strategies(
        df, base_sip=base_sip, 
        dynamic_multipliers=[1, 2, 4, 6],
        dynamic_thresholds=[0, 10, 20, 30]
    )
    
    # 2. Optimize multipliers
    print("\n" + "=" * 80)
    print("PART 2: MULTIPLIER OPTIMIZATION")
    print("=" * 80)
    best_multipliers, best_mult_results, mult_results_df = optimize_multipliers_grid_search(
        df, base_sip=base_sip
    )
    
    # 3. Optimize thresholds
    print("\n" + "=" * 80)
    print("PART 3: THRESHOLD OPTIMIZATION")
    print("=" * 80)
    best_thresholds, best_thresh_results, thresh_results_df = optimize_thresholds_grid_search(
        df, base_sip=base_sip
    )
    
    # 4. Full optimization
    print("\n" + "=" * 80)
    print("PART 4: COMPREHENSIVE OPTIMIZATION")
    print("=" * 80)
    opt_multipliers, opt_thresholds, opt_results, all_opt_results = full_optimization(
        df, base_sip=base_sip
    )
    
    # 5. Final comparison with optimized strategy
    print("\n" + "=" * 80)
    print("PART 5: FINAL OPTIMIZED STRATEGY")
    print("=" * 80)
    final_comparison, _, optimized_results = compare_strategies(
        df, base_sip=base_sip,
        dynamic_multipliers=opt_multipliers,
        dynamic_thresholds=opt_thresholds
    )
    
    # Summary
    print("\n" + "=" * 80)
    print("FINAL SUMMARY")
    print("=" * 80)
    print(f"\nRegular SIP XIRR: {regular_results['xirr']:.2f}%")
    print(f"Original Dynamic SIP XIRR: {dynamic_results['xirr']:.2f}% "
          f"(+{dynamic_results['xirr'] - regular_results['xirr']:.2f}pp)")
    print(f"Optimized Dynamic SIP XIRR: {optimized_results['xirr']:.2f}% "
          f"(+{optimized_results['xirr'] - regular_results['xirr']:.2f}pp)")
    print(f"\nOptimal Parameters:")
    print(f"  Multipliers: {opt_multipliers}")
    print(f"  Thresholds: {opt_thresholds}%")
    print(f"\nImprovement over Regular SIP:")
    print(f"  XIRR: +{optimized_results['xirr'] - regular_results['xirr']:.2f} percentage points")
    print(f"  Additional Wealth: ₹{optimized_results['final_value'] - regular_results['final_value']:,.0f}")
    print(f"  Additional Investment: ₹{optimized_results['total_invested'] - regular_results['total_invested']:,.0f}")
    print("=" * 80)
    
    return {
        'regular': regular_results,
        'original_dynamic': dynamic_results,
        'optimized': optimized_results,
        'optimal_multipliers': opt_multipliers,
        'optimal_thresholds': opt_thresholds,
        'all_optimization_results': all_opt_results
    }


if __name__ == "__main__":
    results = main()
