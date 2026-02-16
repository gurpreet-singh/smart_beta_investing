"""
Generate Dashboard Data
Runs the SIP analysis and exports results to JSON for the dashboard
Includes weekly index data with moving averages for charting
"""

import json
import sys
import pandas as pd
import numpy as np
from pathlib import Path

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent))

from nifty500_sip_returns import SIPAnalyzer

def get_weekly_closes(df):
    """Extract weekly close prices (last trading day of each week)"""
    # Convert to period and group by week
    df['Week'] = df['Date'].dt.to_period('W')
    
    # Group by week and take last value (mimics OHLC close)
    weekly = df.groupby('Week').last().reset_index(drop=True)
    
    return weekly[['Date', 'Close']]

def read_and_consolidate_index_data(data_folder, index_folder):
    """Read all CSV files for an index and combine them"""
    import glob
    
    folder_path = data_folder / index_folder
    csv_files = sorted(glob.glob(str(folder_path / "*.csv")))
    
    all_data = []
    for file in csv_files:
        df = pd.read_csv(file)
        all_data.append(df)
    
    # Combine all years
    combined_df = pd.concat(all_data, ignore_index=True)
    
    # Convert Date column to datetime
    combined_df['Date'] = pd.to_datetime(combined_df['Date'], format='%d %b %Y')
    
    # Sort by date
    combined_df = combined_df.sort_values('Date')
    
    # Convert Close to float
    combined_df['Close'] = combined_df['Close'].astype(float)
    
    return combined_df

def load_weekly_data_with_ma(data_folder, ma_period=30):
    """Load weekly data for Momentum and Value indices with moving averages
    Uses the same method as ratio calculation
    """
    
    print("\n📊 Loading weekly index data with 30-week moving averages...")
    
    # Read momentum data
    print("   Processing Momentum 30...")
    momentum_df = read_and_consolidate_index_data(data_folder, 'nifty500mom50')
    momentum_weekly = get_weekly_closes(momentum_df)
    momentum_weekly['MA_30'] = momentum_weekly['Close'].rolling(window=ma_period, min_periods=1).mean()
    
    # Read value data
    print("   Processing Value 30...")
    value_df = read_and_consolidate_index_data(data_folder, 'nifty500val50')
    value_weekly = get_weekly_closes(value_df)
    value_weekly['MA_30'] = value_weekly['Close'].rolling(window=ma_period, min_periods=1).mean()
    
    # Load existing ratio data from weekly folder
    print("   Loading existing ratio data...")
    ratio_file = data_folder.parent / "nifty500" / "output" / "weekly" / "momentum_value_ratio_weekly.csv"
    ratio_df = pd.read_csv(ratio_file)
    ratio_df['Date'] = pd.to_datetime(ratio_df['Date'])
    
    print(f"   ✅ Momentum: {len(momentum_weekly)} weeks")
    print(f"   ✅ Value: {len(value_weekly)} weeks")
    print(f"   ✅ Ratio: {len(ratio_df)} weeks")
    
    return {
        'momentum': {
            'dates': momentum_weekly['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'close': momentum_weekly['Close'].tolist(),
            'ma_30': momentum_weekly['MA_30'].replace({np.nan: None}).tolist()
        },
        'value': {
            'dates': value_weekly['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'close': value_weekly['Close'].tolist(),
            'ma_30': value_weekly['MA_30'].replace({np.nan: None}).tolist()
        },
        'ratio': {
            'dates': ratio_df['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'ratio': ratio_df['Momentum_Value_Ratio'].tolist(),
            'ma_30': ratio_df['MA_30_Week'].replace({np.nan: None}).tolist()
        }
    }

def main():
    # Initialize analyzer
    data_folder = Path(__file__).parent.parent.parent / "data"
    analyzer = SIPAnalyzer(data_folder, monthly_sip=10000)
    
    # Manually run analysis for each index
    results = {}
    
    for folder, name in analyzer.indices.items():
        print(f"\nProcessing {name}...")
        result = analyzer.analyze_index(folder, name)
        if result:
            results[folder] = result
    
    if results:
        # Prepare dashboard data
        dashboard_data = {
            'indices': [],
            'portfolio': {
                'total_invested': 0,
                'total_value': 0,
                'total_gain': 0,
                'overall_return': 0
            }
        }
        
        total_invested_all = 0
        total_value_all = 0
        
        for folder, result in results.items():
            dashboard_data['indices'].append({
                'name': result['index_name'],
                'sip_xirr': round(float(result['xirr']), 2),
                'index_cagr': round(float(result['index_cagr']), 2),
                'total_return': round(float(result['return_pct']), 2),
                'total_invested': round(float(result['total_invested']), 2),
                'final_value': round(float(result['final_value']), 2),
                'absolute_gain': round(float(result['absolute_return']), 2),
                'max_drawdown': round(float(result['max_nav_dd']), 2),
                'max_investor_drawdown': round(float(result['max_investor_dd']), 2),
                'start_nav': round(float(result['start_nav']), 2),
                'end_nav': round(float(result['end_nav']), 2),
                'num_sips': int(result['num_sips'])
            })
            
            total_invested_all += result['total_invested']
            total_value_all += result['final_value']
        
        total_gain = total_value_all - total_invested_all
        total_return_pct = (total_gain / total_invested_all) * 100
        
        dashboard_data['portfolio']['total_invested'] = round(float(total_invested_all), 2)
        dashboard_data['portfolio']['total_value'] = round(float(total_value_all), 2)
        dashboard_data['portfolio']['total_gain'] = round(float(total_gain), 2)
        dashboard_data['portfolio']['overall_return'] = round(float(total_return_pct), 2)
        
        # Add weekly chart data
        try:
            weekly_data = load_weekly_data_with_ma(data_folder, ma_period=30)
            dashboard_data['weekly_charts'] = weekly_data
            print("   ✅ Weekly chart data added to dashboard JSON")
        except Exception as e:
            print(f"   ⚠️ Warning: Could not load weekly data: {e}")
            import traceback
            traceback.print_exc()
            dashboard_data['weekly_charts'] = None
        
        # Export to JSON
        output_dir = Path(__file__).parent.parent / "output"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / "dashboard_data.json"
        with open(output_file, 'w') as f:
            json.dump(dashboard_data, f, indent=2)
        
        print(f"\n{'='*80}")
        print(f"✅ Dashboard data exported to: {output_file}")
        print(f"{'='*80}\n")
        return dashboard_data
    
    return None

if __name__ == "__main__":
    main()
