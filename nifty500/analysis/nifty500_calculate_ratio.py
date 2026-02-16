"""
Weekly Momentum/Value Ratio Calculator
Calculates the weekly ratio of Momentum 50 / Value 50 from 2005 to 2025
and generates an interactive Plotly chart for the dashboard
"""

import pandas as pd
import numpy as np
from pathlib import Path
import plotly.graph_objects as go
import json

class RatioAnalyzer:
    def __init__(self, data_folder):
        self.data_folder = Path(data_folder)
        self.output_folder = self.data_folder.parent / "nifty500" / "output" / "weekly"
        self.output_folder.mkdir(parents=True, exist_ok=True)
        
    def read_and_consolidate_index_data(self, index_folder):
        """Read all CSV files for an index and combine them"""
        import glob
        
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
        
        # Sort by date
        combined_df = combined_df.sort_values('Date')
        
        # Convert Close to float
        combined_df['Close'] = combined_df['Close'].astype(float)
        
        return combined_df
    
    def get_weekly_closes(self, df):
        """Extract weekly close prices (last trading day of each week)
        
        Uses period groupby instead of resample to match TradingView's
        OHLC aggregation behavior more closely.
        """
        # Convert to period and group by week
        df['Week'] = df['Date'].dt.to_period('W')
        
        # Group by week and take last value (mimics OHLC close)
        weekly = df.groupby('Week').last().reset_index(drop=True)
        
        return weekly[['Date', 'Close']]
    
    def calculate_momentum_value_ratio(self):
        """Calculate weekly Momentum/Value ratio"""
        print("\n" + "="*80)
        print("CALCULATING MOMENTUM/VALUE RATIO - WEEKLY DATA")
        print("="*80)
        
        # Read momentum data
        print("\nReading Momentum 50 data...")
        momentum_df = self.read_and_consolidate_index_data('nifty500mom50')
        momentum_weekly = self.get_weekly_closes(momentum_df)
        momentum_weekly.columns = ['Date', 'Momentum_Close']
        
        # Read value data
        print("Reading Value 50 data...")
        value_df = self.read_and_consolidate_index_data('nifty500val50')
        value_weekly = self.get_weekly_closes(value_df)
        value_weekly.columns = ['Date', 'Value_Close']
        
        # Merge on date
        print("Calculating ratio...")
        ratio_df = pd.merge(momentum_weekly, value_weekly, on='Date', how='inner')
        
        # Calculate ratio directly (both indices start at 1000, so no normalization needed)
        ratio_df['Momentum_Value_Ratio'] = ratio_df['Momentum_Close'] / ratio_df['Value_Close']
        
        # Calculate 30-week moving average
        ratio_df['MA_30_Week'] = ratio_df['Momentum_Value_Ratio'].rolling(window=30, min_periods=1).mean()
        
        print(f"\nTotal weekly data points: {len(ratio_df)}")
        print(f"Date range: {ratio_df['Date'].min().strftime('%Y-%m-%d')} to {ratio_df['Date'].max().strftime('%Y-%m-%d')}")
        print(f"Ratio range: {ratio_df['Momentum_Value_Ratio'].min():.4f} to {ratio_df['Momentum_Value_Ratio'].max():.4f}")
        print(f"✅ Added 30-week moving average")
        
        # Save to CSV
        output_file = self.output_folder / "momentum_value_ratio_weekly.csv"
        ratio_df.to_csv(output_file, index=False)
        print(f"✅ Saved weekly ratio data to: {output_file}")
        
        return ratio_df
    
    def create_interactive_chart(self, ratio_df):
        """Create interactive Plotly chart"""
        print("\nGenerating interactive Plotly chart...")
        print(f"📊 Data points to plot: {len(ratio_df)}")
        print(f"   Date range: {ratio_df['Date'].iloc[0]} to {ratio_df['Date'].iloc[-1]}")
        print(f"   Ratio range: {ratio_df['Momentum_Value_Ratio'].min():.4f} to {ratio_df['Momentum_Value_Ratio'].max():.4f}")
        
        # Create the figure
        fig = go.Figure()
        
        # Convert to lists explicitly to avoid serialization issues
        dates_list = ratio_df['Date'].tolist()
        ratio_list = ratio_df['Momentum_Value_Ratio'].tolist()
        ma_30_list = ratio_df['MA_30_Week'].tolist()
        
        print(f"✅ Converted to lists - Dates: {len(dates_list)}, Ratios: {len(ratio_list)}, MA: {len(ma_30_list)}")
        
        # Add the ratio line
        fig.add_trace(go.Scatter(
            x=dates_list,
            y=ratio_list,
            mode='lines',
            name='Momentum/Value Ratio',
            line=dict(color='#8b5cf6', width=2),
            hovertemplate='<b>Date:</b> %{x|%d %b %Y}<br>' +
                          '<b>Ratio:</b> %{y:.4f}<br>' +
                          '<extra></extra>'
        ))
        
        # Add 30-week moving average line
        fig.add_trace(go.Scatter(
            x=dates_list,
            y=ma_30_list,
            mode='lines',
            name='30-Week MA',
            line=dict(color='#f59e0b', width=3, dash='solid'),
            hovertemplate='<b>Date:</b> %{x|%d %b %Y}<br>' +
                          '<b>30W MA:</b> %{y:.4f}<br>' +
                          '<extra></extra>'
        ))
        
        # Add a horizontal line at 1.0 (equal performance)
        fig.add_hline(
            y=1.0,
            line_dash="dash",
            line_color="rgba(255, 255, 255, 0.3)",
            annotation_text="Equal Performance",
            annotation_position="right"
        )
        
        # Calculate mean for reference
        mean_ratio = ratio_df['Momentum_Value_Ratio'].mean()
        fig.add_hline(
            y=mean_ratio,
            line_dash="dot",
            line_color="rgba(16, 185, 129, 0.5)",
            annotation_text=f"Mean: {mean_ratio:.4f}",
            annotation_position="left"
        )
        
        # Update layout for dark theme
        fig.update_layout(
            title={
                'text': 'Momentum/Value Ratio (Weekly)',
                'font': {'size': 24, 'color': '#f1f5f9', 'family': 'Inter'}
            },
            xaxis=dict(
                title='Date',
                showgrid=True,
                gridcolor='rgba(255, 255, 255, 0.1)',
                color='#94a3b8',
                tickfont=dict(size=12)
            ),
            yaxis=dict(
                title='Ratio (Momentum / Value)',
                showgrid=True,
                gridcolor='rgba(255, 255, 255, 0.1)',
                color='#94a3b8',
                tickfont=dict(size=12)
            ),
            plot_bgcolor='#1e293b',
            paper_bgcolor='#0f172a',
            font=dict(family='Inter', color='#f1f5f9'),
            hovermode='x unified',
            hoverlabel=dict(
                bgcolor='#334155',
                font_size=14,
                font_family='Inter'
            ),
            height=500,
            margin=dict(l=60, r=60, t=80, b=60)
        )
        
        # Linear scale for ratio (removed log scale per user request)
        
        
        # Save as JSON for web rendering
        chart_json = fig.to_json()
        json_file = self.output_folder / "ratio_chart.json"
        with open(json_file, 'w') as f:
            f.write(chart_json)
        
        print(f"✅ Saved chart JSON to: {json_file}")
        
        # Also save as standalone HTML for testing
        html_file = self.output_folder / "ratio_chart.html"
        fig.write_html(html_file)
        print(f"✅ Saved standalone HTML chart to: {html_file}")
        
        return fig

def main():
    # Initialize analyzer
    data_folder = Path(__file__).parent.parent.parent / "data"
    analyzer = RatioAnalyzer(data_folder)
    
    # Calculate ratio
    ratio_df = analyzer.calculate_momentum_value_ratio()
    
    # Create chart
    analyzer.create_interactive_chart(ratio_df)
    
    print("\n" + "="*80)
    print("✅ RATIO ANALYSIS COMPLETE")
    print("="*80 + "\n")

if __name__ == "__main__":
    main()
