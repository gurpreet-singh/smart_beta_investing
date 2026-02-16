"""
Nifty 200 Beta Returns Analysis
Analyzes SIP returns for Nifty200 Momentum 30, Alpha 30, and Value 30 indices
SIP starts from April 2005 and continues through December 2025
"""

import pandas as pd
import numpy as np
from pathlib import Path
from datetime import datetime
import glob
from pyxirr import xirr

class SIPAnalyzer:
    def __init__(self, data_folder, monthly_sip=10000):
        self.data_folder = Path(data_folder)
        self.monthly_sip = monthly_sip
        self.indices = {
            'nifty200mom30': 'NIFTY200 MOMENTUM 30',
            'nifty200val30': 'NIFTY200 VALUE 30'
        }
        
    def read_and_consolidate_index_data(self, index_folder):
        """Read all CSV files for an index and combine them"""
        folder_path = self.data_folder / index_folder
        csv_files = sorted(glob.glob(str(folder_path / "*.csv")))
        
        all_data = []
        for file in csv_files:
            df = pd.read_csv(file)
            all_data.append(df)
        
        # Combine all years
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Convert Date column to datetime
        combined_df['Date'] = pd.to_datetime(combined_df['Date'], format='%d %b %Y')
        
        # Sort by date (oldest first)
        combined_df = combined_df.sort_values('Date')
        
        # Convert Close to float
        combined_df['Close'] = combined_df['Close'].astype(float)
        
        return combined_df
    
    def get_monthly_closes(self, df):
        """Extract the last trading day close for each month (month-end)
        
        This uses the actual close price on the last trading day of each month,
        which matches realistic SIP investment behavior where you invest at month-end.
        """
        # Group by year-month and get the last trading day's data
        df['YearMonth'] = df['Date'].dt.to_period('M')
        
        # Get the last row (last trading day) for each month
        monthly_data = df.groupby('YearMonth').last().reset_index()
        
        return monthly_data[['Date', 'Close', 'YearMonth']]
    
    def save_monthly_data(self, monthly_data, index_name):
        """Save monthly consolidated data to CSV"""
        output_dir = self.data_folder.parent / "output" / "monthly"
        output_dir.mkdir(parents=True, exist_ok=True)
        output_file = output_dir / f"{index_name.lower().replace(' ', '_')}_monthly.csv"
        monthly_data.to_csv(output_file, index=False)
        print(f"Saved monthly data to: {output_file}")
        return output_file
    
    def calculate_sip_returns(self, monthly_closes):
        """Calculate SIP returns for the entire period"""
        sip_data = monthly_closes.copy()
        
        if len(sip_data) == 0:
            return None
        
        # Reset index to ensure proper sequential counting
        sip_data = sip_data.reset_index(drop=True)
        
        # Calculate units purchased each month (at month-end NAV)
        sip_data['Units_Purchased'] = self.monthly_sip / sip_data['Close']
        sip_data['Cumulative_Units'] = sip_data['Units_Purchased'].cumsum()
        sip_data['Total_Invested'] = self.monthly_sip * (sip_data.index + 1)
        sip_data['Portfolio_Value'] = sip_data['Cumulative_Units'] * sip_data['Close']
        
        # Calculate returns
        sip_data['Returns'] = ((sip_data['Portfolio_Value'] - sip_data['Total_Invested']) / 
                               sip_data['Total_Invested'] * 100)
        
        return sip_data
    
    def calculate_xirr(self, sip_data):
        """Calculate XIRR (Extended Internal Rate of Return) for SIP
        
        This is the CORRECT way to measure SIP returns because it accounts
        for the timing of each cashflow. Unlike CAGR which assumes lump sum
        investment, XIRR properly handles periodic investments.
        """
        if sip_data is None or len(sip_data) == 0:
            return 0
        
        cashflows = []
        
        # Monthly SIP outflows (negative cashflows)
        # pyxirr expects tuples in format: (date, amount)
        for _, row in sip_data.iterrows():
            date_obj = row['Date'].to_pydatetime().date()
            cashflows.append((date_obj, float(-self.monthly_sip)))
        
        # Final portfolio value (positive inflow)
        final_value = float(sip_data['Portfolio_Value'].iloc[-1])
        final_date = sip_data['Date'].iloc[-1].to_pydatetime().date()
        cashflows.append((final_date, final_value))
        
        try:
            # XIRR returns annualized return as decimal, convert to percentage
            result = xirr(cashflows)
            return result * 100 if result is not None else 0
        except Exception as e:
            # If XIRR calculation fails, return 0
            print(f"XIRR calculation failed: {e}")
            import traceback
            traceback.print_exc()
            return 0
    
    def calculate_max_drawdown(self, sip_data):
        """Calculate maximum drawdown - ONLY Index NAV drawdown
        
        Portfolio drawdown is NOT calculated because it's meaningless for SIP:
        - New money enters every month, naturally trending portfolio value upward
        - Drawdown becomes mathematically distorted
        - Only Index NAV drawdown shows true market risk
        """
        if sip_data is None or len(sip_data) == 0:
            return 0
        
        # Index NAV drawdown - shows index decline from peak
        nav_values = sip_data['Close'].values
        running_max_nav = np.maximum.accumulate(nav_values)
        nav_drawdown = ((nav_values - running_max_nav) / running_max_nav) * 100
        max_nav_dd = nav_drawdown.min()
        
        return max_nav_dd
    
    def calculate_invested_capital_drawdown(self, sip_data):
        """Calculate maximum drawdown on invested capital (Investor Drawdown)
        
        This is THE MOST IMPORTANT metric for SIP investors.
        It shows: "At my worst moment, how much of my contributed money was I down?"
        
        Unlike Index NAV drawdown (which can be -60% in crashes), Investor Drawdown
        is much lower because you're continuously buying at lower prices during crashes.
        
        This explains why SIP investors can psychologically survive market crashes
        that would wipe out lump-sum investors.
        
        Calculation:
        - Equity Multiple = Portfolio_Value / Total_Invested
        - Treat this as a "personal NAV" and compute drawdown on it
        
        Example:
            Month 1: Invested 100k, Value 120k → Equity = 1.20
            Month 2: Invested 110k, Value 90k  → Equity = 0.82 (down 18% from invested)
        """
        if sip_data is None or len(sip_data) == 0:
            return 0
        
        # Calculate equity curve (multiple of invested capital)
        equity_curve = sip_data['Portfolio_Value'] / sip_data['Total_Invested']
        
        # Find running maximum
        running_max = np.maximum.accumulate(equity_curve)
        
        # Calculate drawdown on equity curve
        drawdown = ((equity_curve - running_max) / running_max) * 100
        
        # Find maximum drawdown (most negative value)
        max_investor_dd = drawdown.min()
        
        return max_investor_dd

    
    def analyze_index(self, index_folder, index_name):
        """Complete analysis for one index"""
        print(f"\n{'='*80}")
        print(f"Analyzing: {index_name}")
        print(f"{'='*80}")
        
        # Read data
        df = self.read_and_consolidate_index_data(index_folder)
        
        # Get monthly closes
        monthly_closes = self.get_monthly_closes(df)
        
        # Save monthly data
        monthly_file = self.save_monthly_data(monthly_closes, index_name)
        
        print(f"\nTotal daily data points: {len(df)}")
        print(f"Monthly data points: {len(monthly_closes)}")
        print(f"Date range: {df['Date'].min().strftime('%Y-%m-%d')} to {df['Date'].max().strftime('%Y-%m-%d')}")
        print(f"Investment period: {monthly_closes['Date'].iloc[0].strftime('%Y-%m-%d')} to {monthly_closes['Date'].iloc[-1].strftime('%Y-%m-%d')}")
        
        # Calculate SIP returns
        sip_data = self.calculate_sip_returns(monthly_closes)
        
        if sip_data is None or len(sip_data) == 0:
            print("\nNo data available!")
            return None
        
        # Calculate metrics
        total_invested = sip_data['Total_Invested'].iloc[-1]
        final_value = sip_data['Portfolio_Value'].iloc[-1]
        absolute_return = final_value - total_invested
        return_pct = (absolute_return / total_invested) * 100
        
        xirr_return = self.calculate_xirr(sip_data)
        max_nav_dd = self.calculate_max_drawdown(sip_data)
        max_investor_dd = self.calculate_invested_capital_drawdown(sip_data)
        
        # Get start and end NAV
        start_nav = sip_data['Close'].iloc[0]
        end_nav = sip_data['Close'].iloc[-1]
        nav_return = ((end_nav - start_nav) / start_nav) * 100
        
        # Calculate Index CAGR (not SIP XIRR)
        start_date = sip_data['Date'].iloc[0]
        end_date = sip_data['Date'].iloc[-1]
        years = (end_date - start_date).days / 365.25
        index_cagr = (pow(end_nav / start_nav, 1/years) - 1) * 100 if years > 0 else 0
        
        # Display results
        print(f"\n{'─'*80}")
        print(f"SIP ANALYSIS - COMPLETE PERIOD")
        print(f"{'─'*80}")
        print(f"Monthly SIP Amount:           ₹{self.monthly_sip:,.2f}")
        print(f"Number of SIPs:               {len(sip_data)}")
        print(f"Total Amount Invested:        ₹{total_invested:,.2f}")
        print(f"Final Portfolio Value:        ₹{final_value:,.2f}")
        print(f"Absolute Gain/Loss:           ₹{absolute_return:,.2f}")
        print(f"Return Percentage:            {return_pct:.2f}%")
        print(f"SIP XIRR (Annualized):        {xirr_return:.2f}%")
        print(f"\nRisk Metrics:")
        print(f"  Max Index Drawdown:         {max_nav_dd:.2f}%")
        print(f"  Max Investor Drawdown:      {max_investor_dd:.2f}% ⭐ (on invested capital)")
        print(f"\nIndex Performance:")
        print(f"  Starting NAV:               {start_nav:,.2f}")
        print(f"  Ending NAV:                 {end_nav:,.2f}")
        print(f"  Index Return:               {nav_return:.2f}%")
        print(f"  Index CAGR:                 {index_cagr:.2f}%")
        
        # Show first 10 and last 10 months
        print(f"\n{'─'*80}")
        print(f"FIRST 10 MONTHS")
        print(f"{'─'*80}")
        print(f"{'Date':<12} {'NAV':<12} {'Units':<12} {'Total Units':<15} {'Invested':<15} {'Value':<15} {'Return %':<10}")
        print(f"{'─'*80}")
        
        for idx, row in sip_data.head(10).iterrows():
            print(f"{row['Date'].strftime('%Y-%m-%d'):<12} "
                  f"{row['Close']:>11,.2f} "
                  f"{row['Units_Purchased']:>11,.4f} "
                  f"{row['Cumulative_Units']:>14,.4f} "
                  f"₹{row['Total_Invested']:>13,.0f} "
                  f"₹{row['Portfolio_Value']:>13,.0f} "
                  f"{row['Returns']:>9.2f}%")
        
        print(f"\n{'─'*80}")
        print(f"LAST 10 MONTHS")
        print(f"{'─'*80}")
        print(f"{'Date':<12} {'NAV':<12} {'Units':<12} {'Total Units':<15} {'Invested':<15} {'Value':<15} {'Return %':<10}")
        print(f"{'─'*80}")
        
        for idx, row in sip_data.tail(10).iterrows():
            print(f"{row['Date'].strftime('%Y-%m-%d'):<12} "
                  f"{row['Close']:>11,.2f} "
                  f"{row['Units_Purchased']:>11,.4f} "
                  f"{row['Cumulative_Units']:>14,.4f} "
                  f"₹{row['Total_Invested']:>13,.0f} "
                  f"₹{row['Portfolio_Value']:>13,.0f} "
                  f"{row['Returns']:>9.2f}%")
        
        return {
            'index_name': index_name,
            'total_invested': total_invested,
            'final_value': final_value,
            'absolute_return': absolute_return,
            'return_pct': return_pct,
            'xirr': xirr_return,
            'max_nav_dd': max_nav_dd,
            'max_investor_dd': max_investor_dd,
            'num_sips': len(sip_data),
            'start_nav': start_nav,
            'end_nav': end_nav,
            'nav_return': nav_return,
            'index_cagr': index_cagr
        }
    
    def run_analysis(self):
        """Run analysis for both indices"""
        print("\n" + "="*80)
        print(" "*20 + "NIFTY 200 SMART BETA SIP ANALYSIS")
        print("="*80)
        print(f"\nMonthly SIP per Index: ₹{self.monthly_sip:,.2f}")
        print(f"Total Monthly Investment: ₹{self.monthly_sip * 2:,.2f}")
        print(f"Investment Strategy: SIP at end of each month")
        
        results = {}
        
        for folder, name in self.indices.items():
            result = self.analyze_index(folder, name)
            if result:
                results[folder] = result
        
        # Summary comparison
        if len(results) > 0:
            print(f"\n{'='*80}")
            print(f"COMPARATIVE SUMMARY - BOTH INDICES")
            print(f"{'='*80}")
            print(f"\n{'Index':<30} {'Invested':<18} {'Final Value':<18} {'Gain':<18} {'Return %':<12} {'XIRR':<10}")
            print(f"{'─'*80}")
            
            total_invested_all = 0
            total_value_all = 0
            
            for folder, result in results.items():
                print(f"{result['index_name']:<30} "
                      f"₹{result['total_invested']:>16,.0f} "
                      f"₹{result['final_value']:>16,.0f} "
                      f"₹{result['absolute_return']:>16,.0f} "
                      f"{result['return_pct']:>11.2f}% "
                      f"{result['xirr']:>9.2f}%")
                
                total_invested_all += result['total_invested']
                total_value_all += result['final_value']
            
            total_gain = total_value_all - total_invested_all
            total_return_pct = (total_gain / total_invested_all) * 100
            
            print(f"{'─'*80}")
            print(f"{'TOTAL PORTFOLIO':<30} "
                  f"₹{total_invested_all:>16,.0f} "
                  f"₹{total_value_all:>16,.0f} "
                  f"₹{total_gain:>16,.0f} "
                  f"{total_return_pct:>11.2f}%")
            
            print(f"\n{'='*80}")
            print(f"KEY INSIGHTS")
            print(f"{'='*80}")
            
            # Find best performer
            best_return = max(results.items(), key=lambda x: x[1]['return_pct'])
            best_xirr = max(results.items(), key=lambda x: x[1]['xirr'])
            best_nav_return = max(results.items(), key=lambda x: x[1]['nav_return'])
            least_drawdown = max(results.items(), key=lambda x: x[1]['max_nav_dd'])  # Less negative is better
            
            print(f"\n✓ Best SIP Returns:     {best_return[1]['index_name']}")
            print(f"  - Total Return: {best_return[1]['return_pct']:.2f}%")
            print(f"  - XIRR: {best_return[1]['xirr']:.2f}%")
            print(f"  - Invested: ₹{best_return[1]['total_invested']:,.0f}")
            print(f"  - Current Value: ₹{best_return[1]['final_value']:,.0f}")
            print(f"  - Absolute Gain: ₹{best_return[1]['absolute_return']:,.0f}")
            
            print(f"\n✓ Best Index NAV Return: {best_nav_return[1]['index_name']}")
            print(f"  - NAV Return: {best_nav_return[1]['nav_return']:.2f}%")
            print(f"  - Start NAV: {best_nav_return[1]['start_nav']:,.2f}")
            print(f"  - End NAV: {best_nav_return[1]['end_nav']:,.2f}")
            
            print(f"\n✓ Lowest Drawdown:      {least_drawdown[1]['index_name']}")
            print(f"  - Max Index DD: {least_drawdown[1]['max_nav_dd']:.2f}%")
            
            print(f"\n{'─'*80}")
            print(f"TOTAL PORTFOLIO SUMMARY")
            print(f"{'─'*80}")
            print(f"✓ Total Amount Invested:        ₹{total_invested_all:,.2f}")
            print(f"✓ Current Portfolio Value:      ₹{total_value_all:,.2f}")
            print(f"✓ Total Absolute Gain:          ₹{total_gain:,.2f}")
            print(f"✓ Overall Return:               {total_return_pct:.2f}%")
            
            # Calculate average monthly investment and duration
            avg_num_sips = sum(r['num_sips'] for r in results.values()) / len(results)
            years = avg_num_sips / 12
            
            print(f"\n✓ Investment Duration:          {years:.1f} years ({int(avg_num_sips)} months)")
            print(f"✓ Monthly Investment:           ₹{self.monthly_sip * 2:,.0f}")
            
        print(f"\n{'='*80}\n")


def main():
    # Initialize analyzer
    data_folder = Path(__file__).parent.parent / "data"
    analyzer = SIPAnalyzer(data_folder, monthly_sip=10000)
    
    # Run analysis
    analyzer.run_analysis()


if __name__ == "__main__":
    main()
