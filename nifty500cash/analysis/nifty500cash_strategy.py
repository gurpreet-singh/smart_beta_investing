"""
MOMCASH Strategy v2 — Continuous Risk Score Architecture
=========================================================

Core Insight:
  The old binary tier approach (wait for ALL conditions → switch) fails because
  by the time ALL signals align, the crash is already underway.

  The new approach: EACH risk signal independently adds cash.
  Cash builds GRADUALLY as the bull extends.
  By the time the crash hits, you already have 30-50% cash.

Architecture:
  Base: 100% Momentum / 0% Cash (fully invested by default)
  
  Risk Score (0–100): Each signal independently contributes points.
    - No AND logic. Each signal works alone.
    - More signals firing = more cash = more protection.
    - Cash builds progressively as risk accumulates.
  
  Cash allocation = risk_score × MAX_CASH_PCT / 100
  Max cash = 50% (at risk_score = 100)
  
  Reload (negative score): After crashes, risk score goes negative → 100% momentum.
  
  Signal_t → allocation_t+1 (always lagged by 1 month)

Risk Score Components:
  ┌──────────────────────────────────┬────────────┬─────────────────────────────────┐
  │ Signal                           │ Max Points │ Logic                           │
  ├──────────────────────────────────┼────────────┼─────────────────────────────────┤
  │ 6M Return Percentile (extension) │ 30         │ Linear: 50th→0, 100th→30       │
  │ 3M Return (short-term heat)      │ 20         │ Step: >8%→5, >12%→10, >18%→20  │
  │ Distance from 10M MA             │ 20         │ Linear: 5%→0, 25%+→20          │
  │ Momentum Z-score                 │ 15         │ Linear: 0.5→0, 2.0+→15         │
  │ Volatility spike                 │ 10         │ Binary: vol > 1.5× median → 10 │
  │ Momentum decelerating + extended │  5         │ Binary: decel AND 6M > 15% → 5 │
  ├──────────────────────────────────┼────────────┼─────────────────────────────────┤
  │ TOTAL POSSIBLE                   │ 100        │                                 │
  └──────────────────────────────────┴────────────┴─────────────────────────────────┘
  
  Reload (negative) signals:
  │ Major drawdown + 3M positive     │ -30        │ DD > -15% AND 3M > 0            │
  │ Below MA but trend intact        │ -10        │ Below MA but 6M > 0             │

Why this works:
  - In NORMAL markets: risk score ~5-15 → cash 2-7% → basically fully invested
  - In LATE BULL: risk score ~40-60 → cash 20-30% → gradually building cash  
  - At PEAK OVEREXTENSION: risk score ~80-100 → cash 40-50% → heavy protection
  - POST CRASH: negative reload → 100% momentum → mean reversion capture
  
  The cash builds BEFORE the crash, not AT the crash.
"""

import pandas as pd
import numpy as np
from pathlib import Path
import warnings
warnings.filterwarnings('ignore')


def calculate_xirr(cash_flows, guess=0.1):
    """Calculate XIRR (Extended Internal Rate of Return) using Newton-Raphson method"""
    from scipy.optimize import newton

    cash_flows = sorted(cash_flows, key=lambda x: x[0])
    start_date = cash_flows[0][0]

    amounts = []
    days = []
    for date, amount in cash_flows:
        days.append((date - start_date).days)
        amounts.append(amount)

    def xnpv(rate):
        return sum([amount / (1 + rate) ** (day / 365.0) for amount, day in zip(amounts, days)])

    def xnpv_deriv(rate):
        return sum([-amount * day / 365.0 / (1 + rate) ** (day / 365.0 + 1) for amount, day in zip(amounts, days)])

    try:
        rate = newton(xnpv, guess, fprime=xnpv_deriv, maxiter=100)
        return rate * 100
    except:
        return 0.0


# ============================================================================
# CONFIGURATION
# ============================================================================

# Base: fully invested
BASE_MOMENTUM = 1.00
BASE_CASH = 0.00

# Maximum cash when risk score = 100
MAX_CASH_PCT = 0.70  # 70% max cash — allows aggressive protection in crashes

# Cash return assumption (liquid fund / debt fund)
CASH_ANNUAL_RETURN = 0.05  # 5% annualized
CASH_MONTHLY_RETURN = (1 + CASH_ANNUAL_RETURN) ** (1/12) - 1


class MOMCASHStrategy:
    """
    MOMCASH v2: Continuous Risk Score Architecture
    
    Each risk signal independently contributes to a risk score (0–100).
    Risk score maps linearly to cash allocation (0% → MAX_CASH_PCT).
    Cash builds gradually as the bull extends — protection is in place
    BEFORE the crash, not triggered BY the crash.
    """

    def __init__(self, data_folder, monthly_sip=10000, cash_return='simulated'):
        self.data_folder = Path(data_folder)
        self.monthly_sip = monthly_sip
        self.cash_return = cash_return
        self.output_folder = self.data_folder.parent / "nifty500cash" / "output" / "monthly"
        self.output_folder.mkdir(parents=True, exist_ok=True)

    # ========================================================================
    # DATA LOADING
    # ========================================================================

    def load_monthly_data(self):
        """Load pre-generated monthly momentum index data"""
        print("\n" + "=" * 80)
        print("MOMCASH v2 — Continuous Risk Score Architecture")
        print("=" * 80)
        print("\n📂 Loading monthly momentum index data...")

        mom_file = self.data_folder.parent / "nifty500" / "output" / "monthly" / "nifty500_momentum_50_monthly.csv"
        mom_df = pd.read_csv(mom_file)
        mom_df['Date'] = pd.to_datetime(mom_df['Date'])
        mom_df = mom_df.rename(columns={'Close': 'Close_mom'})

        print(f"✅ Loaded {len(mom_df)} months of momentum data")
        print(f"   Date range: {mom_df['Date'].min().strftime('%Y-%m')} to {mom_df['Date'].max().strftime('%Y-%m')}")

        return mom_df

    # ========================================================================
    # SIGNAL COMPUTATION
    # ========================================================================

    def compute_signals(self, df):
        """Compute all momentum state variables"""
        print("\n📊 Computing momentum signals...")

        # === TREND STRENGTH ===
        df['return_6m'] = df['Close_mom'].pct_change(6)
        df['return_9m'] = df['Close_mom'].pct_change(9)
        df['return_3m'] = df['Close_mom'].pct_change(3)
        df['return_1m'] = df['Close_mom'].pct_change(1)

        # 10-month moving average (≈ 200-day MA)
        df['ma_10m'] = df['Close_mom'].rolling(window=10, min_periods=5).mean()
        df['ma_slope'] = df['ma_10m'].pct_change(3)

        # Momentum Z-score (rolling 36-month window)
        df['return_6m_mean'] = df['return_6m'].rolling(window=36, min_periods=12).mean()
        df['return_6m_std'] = df['return_6m'].rolling(window=36, min_periods=12).std()
        df['momentum_zscore'] = (df['return_6m'] - df['return_6m_mean']) / df['return_6m_std']

        # === OVEREXTENSION SIGNALS ===
        df['dist_from_ma'] = (df['Close_mom'] - df['ma_10m']) / df['ma_10m']

        # Momentum deceleration: current 3M vs previous 3M (lagged by 3M)
        df['return_3m_prev'] = df['return_3m'].shift(3)
        df['momentum_decelerating'] = df['return_3m'] < df['return_3m_prev']

        # Rolling percentile of 6M return (36M window)
        df['return_6m_percentile'] = df['return_6m'].rolling(window=36, min_periods=12).apply(
            lambda x: (x.rank(pct=True).iloc[-1]) if len(x) > 0 else 0.5
        )

        # === DRAWDOWN / RELOAD SIGNALS ===
        df['rolling_peak'] = df['Close_mom'].cummax()
        df['drawdown'] = (df['Close_mom'] - df['rolling_peak']) / df['rolling_peak']
        df['below_ma'] = df['Close_mom'] < df['ma_10m']

        # 3M realized volatility (annualized)
        df['volatility_3m'] = df['return_1m'].rolling(window=3, min_periods=2).std() * np.sqrt(12)
        df['vol_median_36m'] = df['volatility_3m'].rolling(window=36, min_periods=12).median()
        df['vol_spike'] = df['volatility_3m'] > (df['vol_median_36m'] * 1.5)

        # 24-month cumulative return (multi-year bubble detection)
        df['return_24m'] = df['Close_mom'].pct_change(24)

        print("   ✅ All momentum signals computed")
        return df

    # ========================================================================
    # CONTINUOUS RISK SCORE ENGINE (the core innovation)
    # ========================================================================

    def calculate_risk_score(self, df):
        """
        Calculate continuous risk score for each month.
        
        KEY DESIGN PRINCIPLES:
        1. Each signal independently contributes points (no AND logic)
        2. Risk score has PERSISTENCE — decays slowly (max -15 pts/month)
           This prevents snapping from 95→0 when crash starts
        3. Reload only fires after drawdown materially recovers
        4. Below-MA during elevated risk → HOLD cash, don't reload
        """
        print("\n🔧 Computing continuous risk scores with persistence...")

         # Initialize score components for transparency
        df['score_extension'] = 0.0      # 6M bubble (max 25) — RARE
        df['score_3m_heat'] = 0.0        # 3M extreme heat (max 20) — RARE
        df['score_dist_ma'] = 0.0        # Far above MA (max 20) — RARE
        df['score_zscore'] = 0.0         # Z-score extreme (max 15) — RARE
        df['score_volatility'] = 0.0     # Vol spike (max 10)
        df['score_deceleration'] = 0.0   # Deceleration (max 5)
        df['score_dd_danger'] = 0.0      # Drawdown danger / crash onset (max 80) — KEY
        df['score_bubble_24m'] = 0.0     # Multi-year bubble (max 25) — RARE

        # === RISK SCORE PERSISTENCE PARAMETERS ===
        MAX_DECAY_PER_MONTH = 25.0   # Fast decay when slope is positive (redeploy quickly)

        # We'll compute raw score first, then apply persistence
        raw_scores = np.zeros(len(df))

        for i in range(len(df)):
            row = df.iloc[i]

            if pd.isna(row['return_6m']):
                continue

            ret_3m = row['return_3m'] if not pd.isna(row['return_3m']) else 0
            ret_6m = row['return_6m'] if not pd.isna(row['return_6m']) else 0
            dd = row['drawdown'] if not pd.isna(row['drawdown']) else 0
            dist = row['dist_from_ma'] if not pd.isna(row['dist_from_ma']) else 0

            # ============================================================
            # BUBBLE SIGNALS — fire RARELY, only at genuine extremes
            # Goal: Hold cash only during 2007-type bubble tops
            # ============================================================

            # 1. MOMENTUM EXTENSION — only above 85th percentile (max 25 pts)
            pctile = row.get('return_6m_percentile', 0.5)
            if not pd.isna(pctile) and pctile > 0.85:
                score_ext = ((pctile - 0.85) / 0.15) * 25.0
            else:
                score_ext = 0.0
            df.iat[i, df.columns.get_loc('score_extension')] = score_ext

            # 2. SHORT-TERM EXTREME HEAT — only above 25% (max 20 pts)
            if ret_3m > 0.35:
                score_3m = 20.0
            elif ret_3m > 0.25:
                score_3m = 10.0
            else:
                score_3m = 0.0
            df.iat[i, df.columns.get_loc('score_3m_heat')] = score_3m

            # 3. DISTANCE FROM MA — only above 25% (max 20 pts)
            if dist > 0.25:
                score_dist = min(((dist - 0.25) / 0.25) * 20.0, 20.0)
            else:
                score_dist = 0.0
            df.iat[i, df.columns.get_loc('score_dist_ma')] = score_dist

            # 4. Z-SCORE — only above 1.5 (max 15 pts)
            zscore = row['momentum_zscore'] if not pd.isna(row['momentum_zscore']) else 0
            if zscore > 1.5:
                score_z = min(((zscore - 1.5) / 1.0) * 15.0, 15.0)
            else:
                score_z = 0.0
            df.iat[i, df.columns.get_loc('score_zscore')] = score_z

            # 5. VOLATILITY SPIKE (max 10 pts) — keep as-is, it's useful
            if row.get('vol_spike', False) and not pd.isna(row.get('vol_spike')):
                score_vol = 10.0
            else:
                score_vol = 0.0
            df.iat[i, df.columns.get_loc('score_volatility')] = score_vol

            # 6. DECELERATION while extended (max 5 pts)
            decel = row.get('momentum_decelerating', False)
            if decel and ret_6m > 0.30:
                score_decel = 5.0
            else:
                score_decel = 0.0
            df.iat[i, df.columns.get_loc('score_deceleration')] = score_decel

            # 6b. MULTI-YEAR BUBBLE (max 25 pts)
            # "The bigger the run over 2-3 years, the bigger the crash."
            # Only fires at extreme multi-year outperformance.
            ret_24m = row['return_24m'] if not pd.isna(row.get('return_24m', float('nan'))) else 0
            if ret_24m > 1.50:
                score_bubble = 25.0   # 150%+ in 2 years = severe bubble
            elif ret_24m > 1.00:
                score_bubble = 15.0   # 100%+ in 2 years = bubble territory
            else:
                score_bubble = 0.0
            df.iat[i, df.columns.get_loc('score_bubble_24m')] = score_bubble

            # ============================================================
            # 7. CRASH-ONSET / DRAWDOWN DANGER (max 80 pts) — KEY SIGNAL
            # Must be STRONG enough to push raw score above frozen effective
            # score. During crashes, bubble signals fade to 0 — dd_danger is
            # the ONLY signal that fires. It must single-handedly drive the
            # score high enough for 50-70% cash.
            # ============================================================
            prev_dd = df.iloc[i-1]['drawdown'] if i > 0 and not pd.isna(df.iloc[i-1].get('drawdown', float('nan'))) else 0
            dd_deepening = dd < prev_dd - 0.01  # DD getting worse by >1%
            
            if dd < -0.25 and ret_3m < -0.10:
                score_dd = 80.0    # Severe crash: max protection
            elif dd < -0.20 and ret_3m < -0.10:
                score_dd = 65.0    # Active crash: deep DD + falling fast
            elif dd < -0.15 and dd_deepening:
                score_dd = 50.0    # Crash accelerating
            elif dd < -0.10 and dd_deepening and dist < 0:
                score_dd = 35.0    # Crash starting: below MA + deepening
            else:
                score_dd = 0.0
            df.iat[i, df.columns.get_loc('score_dd_danger')] = score_dd

            # Raw instantaneous score
            raw_scores[i] = (score_ext + score_3m + score_dist + score_z +
                             score_vol + score_decel + score_bubble + score_dd)


        # ============================================================
        # APPLY RISK SCORE PERSISTENCE — CONDITION-BASED
        # Risk rising → follow immediately (build cash fast)
        # Momentum still falling (3M < 0) → FREEZE score (hold cash)
        # Momentum turned positive → decay at 25/month (redeploy fast)
        # This holds cash through the ENTIRE crash, deploys on recovery.
        # ============================================================
        df['risk_score_raw'] = np.clip(raw_scores, 0, 100)

        effective_scores = np.zeros(len(df))
        for i in range(len(df)):
            raw = df.iloc[i]['risk_score_raw']
            if i == 0:
                effective_scores[i] = raw
            else:
                prev_effective = effective_scores[i - 1]
                if raw >= prev_effective:
                    # Risk rising → follow immediately (build cash fast)
                    effective_scores[i] = raw
                else:
                    # Risk falling → only deploy cash when downward slope halts
                    ret_3m = df.iloc[i]['return_3m'] if not pd.isna(df.iloc[i].get('return_3m', float('nan'))) else 0
                    dd = df.iloc[i]['drawdown'] if not pd.isna(df.iloc[i].get('drawdown', float('nan'))) else 0
                    
                    if ret_3m < 0:
                        # MOMENTUM STILL FALLING → FREEZE score completely
                        # Don't deploy ANY cash while the slope is downward
                        decay = 0.0
                    elif dd < -0.15:
                        # Slope turned positive, recovering from crash
                        # → deploy moderately fast to capture recovery
                        decay = 20.0
                    else:
                        # Slope positive AND near highs → full speed deployment
                        decay = MAX_DECAY_PER_MONTH
                    
                    effective_scores[i] = max(raw, prev_effective - decay)
                # Ensure still in valid range
                effective_scores[i] = np.clip(effective_scores[i], 0, 100)

        df['risk_score'] = effective_scores

        # ============================================================
        # MAP RISK SCORE → CASH ALLOCATION (CONVEX / POWER CURVE)
        # Linear mapping gives too much cash at low scores.
        # Convex: cash = (score/100)^2 × MAX_CASH_PCT
        #   Score 10 → 0.7% cash (negligible)
        #   Score 30 → 6.3% cash (minimal drag)
        #   Score 50 → 17.5% cash (moderate)
        #   Score 70 → 34.3% cash (defensive)
        #   Score 90 → 56.7% cash (crash mode)
        # This keeps cash near 0 in bull markets, ramps hard in crashes.
        # ============================================================
        df['w_cash'] = ((df['risk_score'] / 100.0) ** 2) * MAX_CASH_PCT
        df['w_mom'] = 1.0 - df['w_cash']

        # ============================================================
        # 🚨 CRITICAL: LAG BY 1 MONTH (no lookahead bias)
        # ============================================================
        df['w_mom'] = df['w_mom'].shift(1)
        df['w_cash'] = df['w_cash'].shift(1)
        df['risk_score'] = df['risk_score'].shift(1)

        # Fill first month with base (fully invested)
        df['w_mom'] = df['w_mom'].fillna(BASE_MOMENTUM)
        df['w_cash'] = df['w_cash'].fillna(BASE_CASH)
        df['risk_score'] = df['risk_score'].fillna(0)

        # Round to 5% for practical implementation
        df['w_mom'] = (df['w_mom'] * 100 / 5.0).round() * 5.0 / 100
        df['w_cash'] = 1.0 - df['w_mom']
        df['w_mom'] = df['w_mom'].clip(0.5, 1.0).round(4)
        df['w_cash'] = df['w_cash'].clip(0.0, 0.5).round(4)

        # Create descriptive allocation tier labels for reporting
        df['allocation_tier'] = pd.cut(
            df['risk_score'],
            bins=[-0.01, 10, 30, 60, 100],
            labels=['fully_invested', 'low_risk', 'elevated_risk', 'high_risk']
        ).astype(str)

        # ============================================================
        # PRINT SUMMARY
        # ============================================================
        print(f"\n📊 Risk Score Distribution (with persistence):")
        print(f"   Mean risk score:    {df['risk_score'].mean():.1f} / 100")
        print(f"   Median risk score:  {df['risk_score'].median():.1f} / 100")
        print(f"   Max risk score:     {df['risk_score'].max():.1f} / 100")
        print(f"   Min risk score:     {df['risk_score'].min():.1f} / 100")

        tier_counts = df['allocation_tier'].value_counts()
        print(f"\n📊 Allocation Zones:")
        zone_defs = {
            'fully_invested': '100% Mom (score 0-10)',
            'low_risk':       '~90% Mom (score 10-30)',
            'elevated_risk':  '~75% Mom (score 30-60)',
            'high_risk':      '~50% Mom (score 60-100)',
        }
        for tier in ['fully_invested', 'low_risk', 'elevated_risk', 'high_risk']:
            count = tier_counts.get(tier, 0)
            desc = zone_defs.get(tier, '')
            print(f"   {desc:30s}: {count:3d} months ({count/len(df)*100:.1f}%)")

        # Signal contribution analysis
        score_cols = ['score_extension', 'score_3m_heat', 'score_dist_ma',
                      'score_zscore', 'score_volatility', 'score_deceleration',
                      'score_bubble_24m', 'score_dd_danger']
        valid = df[df['return_6m'].notna()]
        print(f"\n📊 Average Signal Contributions (when active):")
        for col in score_cols:
            active = valid[valid[col] != 0]
            if len(active) > 0:
                name = col.replace('score_', '').replace('_', ' ').title()
                print(f"   {name:25s}: avg {active[col].mean():+.1f} pts, "
                      f"active {len(active):3d}/{len(valid)} months ({len(active)/len(valid)*100:.0f}%)")

        print(f"\n   📈 Average Momentum Allocation: {df['w_mom'].mean()*100:.1f}%")
        print(f"   💵 Average Cash Allocation:     {df['w_cash'].mean()*100:.1f}%")

        return df

    # ========================================================================
    # PORTFOLIO CALCULATION
    # ========================================================================

    def calculate_portfolio_returns(self, df):
        """Calculate portfolio returns"""
        print("\n💰 Calculating portfolio returns...")

        df['Return_mom'] = df['Close_mom'].pct_change()

        if self.cash_return == 'simulated':
            df['Return_cash'] = CASH_MONTHLY_RETURN
            print(f"   💵 Cash return: {CASH_ANNUAL_RETURN*100:.1f}% annualized ({CASH_MONTHLY_RETURN*100:.4f}% monthly)")
        else:
            df['Return_cash'] = 0.0
            print(f"   💵 Cash return: 0%")

        # Portfolio return
        df['Portfolio_Return'] = (
            df['w_mom'] * df['Return_mom'] +
            df['w_cash'] * df['Return_cash']
        )

        # NAVs
        df['Portfolio_NAV'] = 1000 * (1 + df['Portfolio_Return']).cumprod()
        df.loc[0, 'Portfolio_NAV'] = 1000

        df['Momentum_NAV'] = 1000 * (1 + df['Return_mom']).cumprod()
        df.loc[0, 'Momentum_NAV'] = 1000

        df['Static_7525_Return'] = 0.75 * df['Return_mom'] + 0.25 * df['Return_cash']
        df['Static_7525_NAV'] = 1000 * (1 + df['Static_7525_Return']).cumprod()
        df.loc[0, 'Static_7525_NAV'] = 1000

        # Drawdowns
        df['Portfolio_Peak'] = df['Portfolio_NAV'].cummax()
        df['Portfolio_Drawdown'] = (df['Portfolio_NAV'] - df['Portfolio_Peak']) / df['Portfolio_Peak']

        df['Momentum_Peak'] = df['Momentum_NAV'].cummax()
        df['Momentum_Drawdown'] = (df['Momentum_NAV'] - df['Momentum_Peak']) / df['Momentum_Peak']

        df['Static_Peak'] = df['Static_7525_NAV'].cummax()
        df['Static_Drawdown'] = (df['Static_7525_NAV'] - df['Static_Peak']) / df['Static_Peak']

        print("   ✅ Portfolio NAV computed")
        return df

    # ========================================================================
    # SIP ANALYSIS
    # ========================================================================

    def run_sip_on_portfolio(self, df, strategy_name, nav_col='Portfolio_NAV'):
        """Run SIP analysis on any NAV series"""
        print(f"\n🎯 Running SIP analysis for: {strategy_name}")

        sip_data = df[['Date', nav_col]].copy()
        sip_data = sip_data.rename(columns={nav_col: 'NAV'})
        sip_data = sip_data.dropna()
        sip_data = sip_data.reset_index(drop=True)

        sip_data['Units_Bought'] = self.monthly_sip / sip_data['NAV']
        sip_data['Cumulative_Units'] = sip_data['Units_Bought'].cumsum()
        sip_data['Total_Invested'] = self.monthly_sip * (sip_data.index + 1)
        sip_data['Portfolio_Value'] = sip_data['Cumulative_Units'] * sip_data['NAV']

        sip_data['Peak_Portfolio_Value'] = sip_data['Portfolio_Value'].cummax()
        sip_data['Drawdown_Pct'] = (
            (sip_data['Portfolio_Value'] - sip_data['Peak_Portfolio_Value']) /
            sip_data['Peak_Portfolio_Value'] * 100
        )
        sip_data['Investor_Drawdown_Pct'] = (
            (sip_data['Portfolio_Value'] - sip_data['Total_Invested']) /
            sip_data['Total_Invested'] * 100
        )

        total_invested = sip_data['Total_Invested'].iloc[-1]
        final_value = sip_data['Portfolio_Value'].iloc[-1]
        absolute_gain = final_value - total_invested
        total_return_pct = (absolute_gain / total_invested) * 100
        max_drawdown = sip_data['Drawdown_Pct'].min()
        max_investor_dd = sip_data['Investor_Drawdown_Pct'].min()

        cash_flows = []
        for idx, row in sip_data.iterrows():
            cash_flows.append((row['Date'], -self.monthly_sip))
        cash_flows.append((sip_data['Date'].iloc[-1], final_value))
        sip_xirr = calculate_xirr(cash_flows)

        start_nav = sip_data['NAV'].iloc[0]
        end_nav = sip_data['NAV'].iloc[-1]
        years = len(sip_data) / 12
        index_cagr = ((end_nav / start_nav) ** (1 / years) - 1) * 100

        mar_ratio = sip_xirr / abs(max_drawdown) if max_drawdown != 0 else 0

        returns_series = df[nav_col].pct_change().dropna()
        excess_returns = returns_series - (0.05 / 12)
        sharpe = (excess_returns.mean() / excess_returns.std()) * np.sqrt(12) if excess_returns.std() > 0 else 0

        dd_pct = sip_data['Drawdown_Pct'].values
        ulcer_index = np.sqrt(np.mean(dd_pct[dd_pct < 0] ** 2)) if (dd_pct < 0).any() else 0

        results = {
            'strategy_name': strategy_name,
            'sip_xirr': sip_xirr,
            'index_cagr': index_cagr,
            'total_return_pct': total_return_pct,
            'total_invested': total_invested,
            'final_value': final_value,
            'absolute_gain': absolute_gain,
            'max_drawdown': max_drawdown,
            'max_investor_drawdown': max_investor_dd,
            'mar_ratio': mar_ratio,
            'sharpe_ratio': sharpe,
            'ulcer_index': ulcer_index,
            'num_months': len(sip_data),
            'start_nav': start_nav,
            'end_nav': end_nav,
            'years': years,
        }

        return results, sip_data

    # ========================================================================
    # MAIN EXECUTION
    # ========================================================================

    def run_strategy(self):
        """Run the complete MOMCASH v2 strategy pipeline"""

        df = self.load_monthly_data()
        df = self.compute_signals(df)
        df = self.calculate_risk_score(df)
        df = self.calculate_portfolio_returns(df)

        print("\n" + "=" * 80)
        print("STRATEGY COMPARISON")
        print("=" * 80)

        comparisons = {}

        momcash_results, momcash_sip = self.run_sip_on_portfolio(
            df, 'MOMCASH v2 (Risk Score)', 'Portfolio_NAV')
        comparisons['momcash'] = momcash_results

        pure_mom_results, _ = self.run_sip_on_portfolio(
            df, 'Pure Momentum (100%)', 'Momentum_NAV')
        comparisons['pure_momentum'] = pure_mom_results

        static_results, _ = self.run_sip_on_portfolio(
            df, 'Static 75/25 (Mom/Cash)', 'Static_7525_NAV')
        comparisons['static_7525'] = static_results

        output_file = self.output_folder / "nifty500cash_momcash_portfolio.csv"
        df.to_csv(output_file, index=False)
        print(f"\n✅ Saved portfolio to: {output_file}")

        return comparisons, df, momcash_sip

    # ========================================================================
    # RESULTS DISPLAY
    # ========================================================================

    def display_results(self, comparisons):
        """Display comparative performance results"""
        print("\n" + "=" * 100)
        print("MOMCASH v2 — CONTINUOUS RISK SCORE — PERFORMANCE COMPARISON")
        print("=" * 100)

        print(f"\n{'Metric':<30s}", end="")
        for key, r in comparisons.items():
            print(f"  {r['strategy_name']:<28s}", end="")
        print()
        print("-" * 120)

        metrics = [
            ('Index CAGR', 'index_cagr', '{:.2f}%'),
            ('SIP XIRR', 'sip_xirr', '{:.2f}%'),
            ('Total Return', 'total_return_pct', '{:.1f}%'),
            ('Total Invested', 'total_invested', '₹{:,.0f}'),
            ('Final Value', 'final_value', '₹{:,.0f}'),
            ('Absolute Gain', 'absolute_gain', '₹{:,.0f}'),
            ('Max Drawdown', 'max_drawdown', '{:.2f}%'),
            ('Max Investor DD', 'max_investor_drawdown', '{:.2f}%'),
            ('MAR Ratio', 'mar_ratio', '{:.2f}'),
            ('Sharpe Ratio', 'sharpe_ratio', '{:.2f}'),
            ('Ulcer Index', 'ulcer_index', '{:.2f}'),
        ]

        for label, key, fmt in metrics:
            print(f"  {label:<28s}", end="")
            for comp_key, r in comparisons.items():
                val = r.get(key, 0)
                formatted = fmt.format(val)
                print(f"  {formatted:<28s}", end="")
            print()

        print("=" * 120)

        momcash = comparisons['momcash']
        pure_mom = comparisons['pure_momentum']

        print("\n📊 KEY INSIGHTS:")
        print(f"   CAGR Difference:      {momcash['index_cagr'] - pure_mom['index_cagr']:+.2f}% vs Pure Momentum")
        print(f"   Drawdown Improvement: {momcash['max_drawdown'] - pure_mom['max_drawdown']:+.2f}% (less negative = better)")
        print(f"   MAR Improvement:      {momcash['mar_ratio'] - pure_mom['mar_ratio']:+.2f}")
        print(f"   Sharpe Improvement:   {momcash['sharpe_ratio'] - pure_mom['sharpe_ratio']:+.2f}")

        if momcash['index_cagr'] < pure_mom['index_cagr']:
            cagr_cost = pure_mom['index_cagr'] - momcash['index_cagr']
            dd_saved = pure_mom['max_drawdown'] - momcash['max_drawdown']
            print(f"\n   💡 TRADEOFF ANALYSIS:")
            print(f"      Gave up {cagr_cost:.2f}% CAGR")
            print(f"      Saved {abs(dd_saved):.2f}% max drawdown")
            print(f"      Each 1% CAGR bought {abs(dd_saved)/cagr_cost:.1f}% drawdown reduction")
            print(f"      MAR improved: {pure_mom['mar_ratio']:.2f} → {momcash['mar_ratio']:.2f}")
            print(f"      Ulcer improved: {pure_mom['ulcer_index']:.2f} → {momcash['ulcer_index']:.2f}")


def main():
    """Main execution function"""
    data_folder = Path(__file__).parent.parent.parent / "data"
    strategy = MOMCASHStrategy(data_folder, monthly_sip=10000, cash_return='simulated')

    comparisons, portfolio_df, sip_df = strategy.run_strategy()
    strategy.display_results(comparisons)

    print("\n" + "=" * 80)
    print("✅ MOMCASH v2 STRATEGY COMPLETE")
    print("=" * 80)
    print("\n")


if __name__ == "__main__":
    main()
