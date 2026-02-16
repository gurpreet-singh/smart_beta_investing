"""
Generate Dashboard Data
Runs the SIP analysis and exports results to JSON for the dashboard
"""

import json
import sys
from pathlib import Path

# Add parent directory to path to import the module
sys.path.insert(0, str(Path(__file__).parent))

from nifty200betareturns import SIPAnalyzer

def main():
    # Initialize analyzer
    data_folder = Path(__file__).parent.parent / "data"
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
