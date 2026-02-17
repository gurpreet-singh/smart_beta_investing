"""
MOMCASH Analytics Engine
========================
Generates comprehensive analytics and dashboard data for the MOMCASH strategy.

Outputs:
  - Summary KPIs (CAGR, XIRR, Max DD, MAR, Sharpe, Ulcer)
  - NAV comparison charts (MOMCASH vs Pure Momentum vs Static 75/25)
  - Allocation tier timeline
  - Signal strength charts
  - Drawdown comparison
  - Calendar year returns
  - Regime transition analysis
"""

import pandas as pd
import numpy as np
from pathlib import Path
import json
import sys

sys.path.insert(0, str(Path(__file__).parent))
from nifty500cash_strategy import MOMCASHStrategy, calculate_xirr


class MOMCASHAnalytics:
    """Generate dashboard-ready analytics for MOMCASH strategy"""

    def __init__(self, portfolio_file, monthly_sip=10000):
        """Initialize with portfolio CSV from strategy run"""
        self.portfolio_df = pd.read_csv(portfolio_file)
        self.portfolio_df['Date'] = pd.to_datetime(self.portfolio_df['Date'])
        self.monthly_sip = monthly_sip
        self.df = self.portfolio_df.copy()

    # ====================================================================
    # SUMMARY KPIs
    # ====================================================================

    def calculate_summary_kpis(self):
        """Calculate performance KPIs for all three strategies"""
        df = self.df.copy()
        kpis = {}

        strategies = {
            'momcash': {
                'nav_col': 'Portfolio_NAV',
                'dd_col': 'Portfolio_Drawdown',
                'name': 'MOMCASH (Dynamic Mom/Cash)',
            },
            'pure_momentum': {
                'nav_col': 'Momentum_NAV',
                'dd_col': 'Momentum_Drawdown',
                'name': 'Pure Momentum (100%)',
            },
            'static_7525': {
                'nav_col': 'Static_7525_NAV',
                'dd_col': 'Static_Drawdown',
                'name': 'Static 75/25',
            },
        }

        for key, config in strategies.items():
            nav = df[config['nav_col']].dropna()
            if len(nav) < 2:
                continue

            # CAGR
            start_val = nav.iloc[0]
            end_val = nav.iloc[-1]
            years = len(nav) / 12
            cagr = ((end_val / start_val) ** (1 / years) - 1) * 100

            # Max Drawdown
            dd = df[config['dd_col']].dropna()
            max_dd = dd.min() * 100

            # Monthly returns
            monthly_returns = nav.pct_change().dropna()

            # Sharpe Ratio (annualized, 5% risk-free)
            excess = monthly_returns - (0.05 / 12)
            sharpe = (excess.mean() / excess.std()) * np.sqrt(12) if excess.std() > 0 else 0

            # MAR Ratio
            mar = cagr / abs(max_dd) if max_dd != 0 else 0

            # Ulcer Index
            dd_vals = dd.values * 100
            neg_dd = dd_vals[dd_vals < 0]
            ulcer = np.sqrt(np.mean(neg_dd ** 2)) if len(neg_dd) > 0 else 0

            # Volatility (annualized)
            vol = monthly_returns.std() * np.sqrt(12) * 100

            # Best / Worst months
            best_month = monthly_returns.max() * 100
            worst_month = monthly_returns.min() * 100

            # % positive months
            positive_months = (monthly_returns > 0).sum() / len(monthly_returns) * 100

            # SIP XIRR
            sip_data = df[['Date', config['nav_col']]].dropna().reset_index(drop=True)
            sip_data['Units'] = self.monthly_sip / sip_data[config['nav_col']]
            sip_data['Cum_Units'] = sip_data['Units'].cumsum()
            sip_data['Total_Invested'] = self.monthly_sip * (sip_data.index + 1)
            sip_data['Portfolio_Value'] = sip_data['Cum_Units'] * sip_data[config['nav_col']]

            cash_flows = [(row['Date'], -self.monthly_sip) for _, row in sip_data.iterrows()]
            cash_flows.append((sip_data['Date'].iloc[-1], sip_data['Portfolio_Value'].iloc[-1]))
            xirr = calculate_xirr(cash_flows)

            kpis[key] = {
                'name': config['name'],
                'cagr': round(cagr, 2),
                'xirr': round(xirr, 2),
                'max_drawdown': round(max_dd, 2),
                'sharpe': round(sharpe, 2),
                'mar': round(mar, 2),
                'ulcer_index': round(ulcer, 2),
                'volatility': round(vol, 2),
                'best_month': round(best_month, 2),
                'worst_month': round(worst_month, 2),
                'positive_months_pct': round(positive_months, 1),
                'total_invested': round(float(sip_data['Total_Invested'].iloc[-1]), 0),
                'final_value': round(float(sip_data['Portfolio_Value'].iloc[-1]), 0),
                'start_nav': round(float(start_val), 2),
                'end_nav': round(float(end_val), 2),
                'num_months': len(nav),
                'years': round(years, 1),
            }

        return kpis

    # ====================================================================
    # NAV COMPARISON CHART DATA
    # ====================================================================

    def generate_nav_chart(self):
        """Generate NAV comparison timeseries for charting"""
        df = self.df.copy()

        chart_data = {
            'dates': df['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'momcash_nav': df['Portfolio_NAV'].replace({np.nan: None}).tolist(),
            'momentum_nav': df['Momentum_NAV'].replace({np.nan: None}).tolist(),
            'static_7525_nav': df['Static_7525_NAV'].replace({np.nan: None}).tolist(),
        }

        return chart_data

    # ====================================================================
    # ALLOCATION TIMELINE CHART
    # ====================================================================

    def generate_allocation_chart(self):
        """Generate allocation timeline with risk score"""
        df = self.df.copy()

        chart_data = {
            'dates': df['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'w_mom': df['w_mom'].replace({np.nan: None}).tolist(),
            'w_cash': df['w_cash'].replace({np.nan: None}).tolist(),
            'risk_score': df['risk_score'].replace({np.nan: None}).tolist() if 'risk_score' in df.columns else [],
            'allocation_tier': df['allocation_tier'].replace({np.nan: None}).tolist(),
        }

        # Add score components if available
        score_cols = ['score_extension', 'score_3m_heat', 'score_dist_ma',
                      'score_zscore', 'score_volatility', 'score_deceleration',
                      'score_bubble_24m', 'score_dd_danger']
        for col in score_cols:
            if col in df.columns:
                chart_data[col] = df[col].replace({np.nan: None}).tolist()

        return chart_data

    # ====================================================================
    # SIGNAL STRENGTH CHART
    # ====================================================================

    def generate_signal_chart(self):
        """Generate signal strength indicators over time"""
        df = self.df.copy()

        chart_data = {
            'dates': df['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'return_6m': (df['return_6m'] * 100).replace({np.nan: None}).tolist(),
            'return_3m': (df['return_3m'] * 100).replace({np.nan: None}).tolist(),
            'momentum_zscore': df['momentum_zscore'].replace({np.nan: None}).tolist(),
            'dist_from_ma': (df['dist_from_ma'] * 100).replace({np.nan: None}).tolist(),
            'drawdown': (df['drawdown'] * 100).replace({np.nan: None}).tolist(),
            'volatility_3m': (df['volatility_3m'] * 100).replace({np.nan: None}).tolist(),
        }

        return chart_data

    # ====================================================================
    # DRAWDOWN COMPARISON CHART
    # ====================================================================

    def generate_drawdown_chart(self):
        """Generate drawdown comparison timeseries"""
        df = self.df.copy()

        chart_data = {
            'dates': df['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'momcash_dd': (df['Portfolio_Drawdown'] * 100).replace({np.nan: None}).tolist(),
            'momentum_dd': (df['Momentum_Drawdown'] * 100).replace({np.nan: None}).tolist(),
            'static_7525_dd': (df['Static_Drawdown'] * 100).replace({np.nan: None}).tolist(),
        }

        return chart_data

    # ====================================================================
    # CALENDAR YEAR RETURNS
    # ====================================================================

    def generate_calendar_returns(self):
        """Generate calendar year returns comparison"""
        df = self.df.copy()

        # Compute annual returns for each strategy
        df['Year'] = df['Date'].dt.year

        yearly_data = []
        for year in sorted(df['Year'].unique()):
            year_df = df[df['Year'] == year]
            if len(year_df) < 2:
                continue

            # Portfolio NAV returns for the year
            momcash_ret = (year_df['Portfolio_NAV'].iloc[-1] / year_df['Portfolio_NAV'].iloc[0] - 1) * 100
            mom_ret = (year_df['Momentum_NAV'].iloc[-1] / year_df['Momentum_NAV'].iloc[0] - 1) * 100
            static_ret = (year_df['Static_7525_NAV'].iloc[-1] / year_df['Static_7525_NAV'].iloc[0] - 1) * 100

            # Allocation stats for the year
            avg_mom_alloc = year_df['w_mom'].mean() * 100
            avg_cash_alloc = year_df['w_cash'].mean() * 100

            yearly_data.append({
                'year': int(year),
                'momcash_return': round(momcash_ret, 2),
                'momentum_return': round(mom_ret, 2),
                'static_7525_return': round(static_ret, 2),
                'avg_momentum_allocation': round(avg_mom_alloc, 1),
                'avg_cash_allocation': round(avg_cash_alloc, 1),
                'outperformance': round(momcash_ret - mom_ret, 2),
            })

        return yearly_data

    # ====================================================================
    # ALLOCATION DISTRIBUTION HISTOGRAM
    # ====================================================================

    def generate_allocation_distribution(self):
        """Generate allocation distribution based on risk score zones"""
        df = self.df.copy()

        zone_defs = {
            'fully_invested': {'label': '🟢 Fully Invested (score 0-10)', 'desc': '100% Momentum'},
            'low_risk':       {'label': '🟡 Low Risk (score 10-30)', 'desc': '~90% Momentum'},
            'elevated_risk':  {'label': '🟠 Elevated Risk (score 30-60)', 'desc': '~75% Momentum'},
            'high_risk':      {'label': '🔴 High Risk (score 60-100)', 'desc': '~50% Momentum'},
        }

        tier_dist = df['allocation_tier'].value_counts().to_dict()

        distribution = {}
        for tier, count in tier_dist.items():
            info = zone_defs.get(tier, {'label': tier, 'desc': tier})
            avg_mom = df[df['allocation_tier'] == tier]['w_mom'].mean() * 100 if count > 0 else 75
            distribution[tier] = {
                'count': int(count),
                'pct': round(count / len(df) * 100, 1),
                'momentum_pct': round(avg_mom, 1),
                'cash_pct': round(100 - avg_mom, 1),
                'label': info['label'],
            }

        return distribution

    # ====================================================================
    # REGIME TRANSITION ANALYSIS
    # ====================================================================

    def generate_regime_transitions(self):
        """Analyze zone transitions — when did risk level change?"""
        df = self.df.copy()

        transitions = []
        prev_tier = None

        for _, row in df.iterrows():
            curr_tier = row.get('allocation_tier', 'fully_invested')
            if curr_tier != prev_tier and prev_tier is not None:
                transitions.append({
                    'date': row['Date'].strftime('%Y-%m-%d'),
                    'from_tier': prev_tier,
                    'to_tier': curr_tier,
                    'risk_score': round(float(row.get('risk_score', 0)), 1),
                    'w_mom': round(float(row.get('w_mom', 1.0)), 2),
                    'momentum_nav': round(float(row['Close_mom']), 2) if not pd.isna(row.get('Close_mom')) else None,
                })
            prev_tier = curr_tier

        return transitions

    # ====================================================================
    # ROLLING METRICS
    # ====================================================================

    def generate_rolling_metrics(self):
        """Generate rolling 12M and 36M return comparisons"""
        df = self.df.copy()

        # Rolling 12M returns
        df['rolling_12m_momcash'] = df['Portfolio_NAV'].pct_change(12) * 100
        df['rolling_12m_momentum'] = df['Momentum_NAV'].pct_change(12) * 100
        df['rolling_12m_static'] = df['Static_7525_NAV'].pct_change(12) * 100

        # Rolling 36M returns (annualized)
        df['rolling_36m_momcash'] = ((df['Portfolio_NAV'] / df['Portfolio_NAV'].shift(36)) ** (1/3) - 1) * 100
        df['rolling_36m_momentum'] = ((df['Momentum_NAV'] / df['Momentum_NAV'].shift(36)) ** (1/3) - 1) * 100
        df['rolling_36m_static'] = ((df['Static_7525_NAV'] / df['Static_7525_NAV'].shift(36)) ** (1/3) - 1) * 100

        chart_data = {
            'dates': df['Date'].dt.strftime('%Y-%m-%d').tolist(),
            'rolling_12m': {
                'momcash': df['rolling_12m_momcash'].replace({np.nan: None}).tolist(),
                'momentum': df['rolling_12m_momentum'].replace({np.nan: None}).tolist(),
                'static': df['rolling_12m_static'].replace({np.nan: None}).tolist(),
            },
            'rolling_36m': {
                'momcash': df['rolling_36m_momcash'].replace({np.nan: None}).tolist(),
                'momentum': df['rolling_36m_momentum'].replace({np.nan: None}).tolist(),
                'static': df['rolling_36m_static'].replace({np.nan: None}).tolist(),
            },
        }

        return chart_data

    # ====================================================================
    # EXPORT ALL TO DASHBOARD JSON
    # ====================================================================

    def export_dashboard_data(self, output_file):
        """Export complete dashboard data as JSON"""
        print("\n" + "=" * 80)
        print("GENERATING MOMCASH DASHBOARD DATA")
        print("=" * 80)

        # Gather all analytics
        print("   📊 Calculating KPIs...")
        kpis = self.calculate_summary_kpis()

        print("   📈 Generating NAV chart...")
        nav_chart = self.generate_nav_chart()

        print("   🎯 Generating allocation chart...")
        alloc_chart = self.generate_allocation_chart()

        print("   📡 Generating signal chart...")
        signal_chart = self.generate_signal_chart()

        print("   📉 Generating drawdown chart...")
        dd_chart = self.generate_drawdown_chart()

        print("   📅 Generating calendar returns...")
        cal_returns = self.generate_calendar_returns()

        print("   📊 Generating allocation distribution...")
        alloc_dist = self.generate_allocation_distribution()

        print("   🔄 Generating regime transitions...")
        transitions = self.generate_regime_transitions()

        print("   📏 Generating rolling metrics...")
        rolling = self.generate_rolling_metrics()

        # Assemble dashboard data
        dashboard_data = {
            'strategy_name': 'MOMCASH v2 — Continuous Risk Score Architecture',
            'strategy_description': (
                'Systematic risk management on Nifty 500 Momentum 50 exposure. '
                'Base 100% momentum allocation with continuous risk scoring. '
                'Each signal independently adds cash as risk accumulates — '
                'cash builds BEFORE crashes, not at them. '
                'Uses 6 independent risk signals + 2 reload signals.'
            ),
            'kpis': kpis,
            'charts': {
                'nav_comparison': nav_chart,
                'allocation_timeline': alloc_chart,
                'signals': signal_chart,
                'drawdown_comparison': dd_chart,
                'rolling_metrics': rolling,
            },
            'calendar_returns': cal_returns,
            'allocation_distribution': alloc_dist,
            'regime_transitions': transitions,
        }

        # Clean NaN values
        def clean_nan(obj):
            if isinstance(obj, dict):
                return {k: clean_nan(v) for k, v in obj.items()}
            elif isinstance(obj, list):
                return [clean_nan(item) for item in obj]
            elif isinstance(obj, float) and (np.isnan(obj) or np.isinf(obj)):
                return None
            elif isinstance(obj, (np.integer,)):
                return int(obj)
            elif isinstance(obj, (np.floating,)):
                return float(obj) if not np.isnan(obj) else None
            return obj

        dashboard_data = clean_nan(dashboard_data)

        # Write JSON
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        with open(output_path, 'w') as f:
            json.dump(dashboard_data, f, indent=2)

        print(f"\n✅ Dashboard data exported to: {output_path}")
        print(f"   File size: {output_path.stat().st_size / 1024:.1f} KB")

        return dashboard_data


def main():
    """Generate MOMCASH analytics from existing portfolio data"""
    # Paths
    base_dir = Path(__file__).parent.parent
    portfolio_file = base_dir / "output" / "monthly" / "nifty500cash_momcash_portfolio.csv"

    if not portfolio_file.exists():
        print("⚠️  Portfolio file not found. Running strategy first...")
        from nifty500cash_strategy import main as run_strategy
        run_strategy()

    # Generate analytics
    analytics = MOMCASHAnalytics(portfolio_file, monthly_sip=10000)

    # Export dashboard data
    output_file = base_dir / "output" / "nifty500cash_dashboard.json"
    analytics.export_dashboard_data(output_file)

    print("\n" + "=" * 80)
    print("✅ MOMCASH ANALYTICS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()
