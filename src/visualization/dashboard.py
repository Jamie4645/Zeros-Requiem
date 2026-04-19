"""
SBRS 2.0 — Sovereign Performance Dashboard

A Streamlit-powered interactive dashboard for monitoring live paper trading
across Gold, DAX, NASDAQ, and GBP/USD.

Run: py -m streamlit run src/visualization/dashboard.py
"""

import json
import sqlite3
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
from datetime import datetime, timedelta
from pathlib import Path

try:
    import streamlit as st
except ImportError:
    raise ImportError("Install streamlit: py -m pip install streamlit plotly")

# ── Configuration ─────────────────────────────────────────────

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'zeros_requiem.db'
STATE_DIR = PROJECT_ROOT / 'state'

MARKET_COLORS = {
    'GC=F': '#FFD700',       # Gold
    'XAU_USD': '#FFD700',
    '^GDAXI': '#00FF88',    # DAX - emerald
    'DE30_EUR': '#00FF88',
    '^IXIC': '#00D4FF',     # NASDAQ - electric blue
    'NAS100_USD': '#00D4FF',
    'GBPUSD=X': '#7B2FF7',  # GBP/USD - purple
    'GBP_USD': '#7B2FF7',
    'BTC-USD': '#F7931A',   # Bitcoin - orange
    'ETH-USD': '#627EEA',   # Ethereum - eth blue
}

MARKET_NAMES = {
    'GC=F': 'Gold', '^GDAXI': 'DAX', '^IXIC': 'NASDAQ',
    'GBPUSD=X': 'GBP/USD', 'BTC-USD': 'BTC', 'ETH-USD': 'ETH',
}

BG_COLOR = '#0E1117'
CARD_BG = '#1E2130'
TEXT_COLOR = '#FAFAFA'
WIN_COLOR = '#00FF88'
LOSS_COLOR = '#FF4B4B'
NEUTRAL_COLOR = '#4A4A6A'

PLOTLY_LAYOUT = dict(
    paper_bgcolor='rgba(0,0,0,0)',
    plot_bgcolor='rgba(0,0,0,0)',
    font=dict(color=TEXT_COLOR, family='Inter, sans-serif'),
    margin=dict(l=40, r=20, t=40, b=30),
    legend=dict(bgcolor='rgba(0,0,0,0)'),
)


# ── Data Loading ──────────────────────────────────────────────

@st.cache_data(ttl=60)
def load_trades() -> pd.DataFrame:
    """Load all trades from SQLite."""
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql_query("SELECT * FROM trades ORDER BY entry_time", conn)
    conn.close()
    if not df.empty:
        df['entry_time'] = pd.to_datetime(df['entry_time'], utc=True, errors='coerce')
        df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True, errors='coerce')
        df['is_win'] = df['pnl'] > 0
        df['market'] = df['symbol'].map(MARKET_NAMES).fillna(df['symbol'])
        df['color'] = df['symbol'].map(MARKET_COLORS).fillna('#888888')
    return df


def load_all_states() -> dict:
    """Load all per-symbol state files."""
    states = {}
    if not STATE_DIR.exists():
        return states

    for f in STATE_DIR.glob('sbrs_state*.json'):
        try:
            with open(f) as fh:
                data = json.load(fh)
            key = data.get('symbol', f.stem)
            states[key] = data
        except Exception:
            continue
    return states


# ── Charts ────────────────────────────────────────────────────

def equity_curve_chart(df: pd.DataFrame) -> go.Figure:
    """Combined equity curve with per-market area fills."""
    fig = go.Figure()

    if df.empty:
        fig.add_annotation(text="No trades yet — waiting for live data",
                           xref="paper", yref="paper", x=0.5, y=0.5,
                           showarrow=False, font=dict(size=18, color=NEUTRAL_COLOR))
        fig.update_layout(**PLOTLY_LAYOUT, height=400, title="Portfolio Equity Curve")
        return fig

    for symbol in df['symbol'].unique():
        sym_df = df[df['symbol'] == symbol].sort_values('exit_time')
        if sym_df.empty:
            continue
        cum_pnl = sym_df['pnl'].cumsum()
        name = MARKET_NAMES.get(symbol, symbol)
        color = MARKET_COLORS.get(symbol, '#888888')
        r, g, b = int(color[1:3], 16), int(color[3:5], 16), int(color[5:7], 16)
        fig.add_trace(go.Scatter(
            x=sym_df['exit_time'], y=cum_pnl,
            name=name, mode='lines+markers',
            line=dict(color=color, width=2),
            marker=dict(size=4),
            fill='tozeroy',
            fillcolor=f'rgba({r},{g},{b},0.1)',
        ))

    fig.update_layout(
        **PLOTLY_LAYOUT, height=420,
        title=dict(text="Equity Curve by Market", font=dict(size=18)),
        xaxis=dict(gridcolor='#2A2A3E', showgrid=True),
        yaxis=dict(gridcolor='#2A2A3E', showgrid=True, title="Cumulative PnL ($)"),
        hovermode='x unified',
    )
    return fig


def trade_scatter_chart(df: pd.DataFrame) -> go.Figure:
    """Trade map — scatter plot with color/shape encoding."""
    fig = go.Figure()

    if df.empty:
        fig.add_annotation(text="No trades yet", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(size=18, color=NEUTRAL_COLOR))
        fig.update_layout(**PLOTLY_LAYOUT, height=400, title="Trade Map")
        return fig

    for symbol in df['symbol'].unique():
        sym_df = df[df['symbol'] == symbol]
        name = MARKET_NAMES.get(symbol, symbol)
        color = MARKET_COLORS.get(symbol, '#888888')

        wins = sym_df[sym_df['is_win']]
        losses = sym_df[~sym_df['is_win']]

        if not wins.empty:
            fig.add_trace(go.Scatter(
                x=wins['exit_time'], y=wins['r_multiple'],
                mode='markers', name=f'{name} Win',
                marker=dict(
                    color=WIN_COLOR, size=wins['pnl'].abs().clip(upper=200) / 10 + 6,
                    symbol='triangle-up' if wins['direction'].iloc[0] == 'long' else 'triangle-down',
                    line=dict(color=color, width=1.5),
                    opacity=0.85,
                ),
                hovertemplate=f'<b>{name}</b><br>R: %{{y:.2f}}<br>PnL: $%{{customdata:.2f}}<extra></extra>',
                customdata=wins['pnl'],
            ))

        if not losses.empty:
            fig.add_trace(go.Scatter(
                x=losses['exit_time'], y=losses['r_multiple'],
                mode='markers', name=f'{name} Loss',
                marker=dict(
                    color=LOSS_COLOR, size=losses['pnl'].abs().clip(upper=200) / 10 + 6,
                    symbol='x',
                    line=dict(color=color, width=1.5),
                    opacity=0.7,
                ),
                hovertemplate=f'<b>{name}</b><br>R: %{{y:.2f}}<br>PnL: $%{{customdata:.2f}}<extra></extra>',
                customdata=losses['pnl'],
            ))

    fig.add_hline(y=0, line=dict(color=NEUTRAL_COLOR, width=1, dash='dash'))

    fig.update_layout(
        **PLOTLY_LAYOUT, height=420,
        title=dict(text="Trade Map — Every Trade, Color-Coded", font=dict(size=18)),
        xaxis=dict(gridcolor='#2A2A3E', showgrid=True),
        yaxis=dict(gridcolor='#2A2A3E', showgrid=True, title="R-Multiple"),
        hovermode='closest',
    )
    return fig


def weekly_heatmap(df: pd.DataFrame) -> go.Figure:
    """Weekly PnL heatmap — rows=markets, columns=weeks."""
    fig = go.Figure()

    if df.empty or 'exit_time' not in df.columns:
        fig.add_annotation(text="No trades yet", xref="paper", yref="paper",
                           x=0.5, y=0.5, showarrow=False,
                           font=dict(size=18, color=NEUTRAL_COLOR))
        fig.update_layout(**PLOTLY_LAYOUT, height=250, title="Weekly PnL Heatmap")
        return fig

    valid = df.dropna(subset=['exit_time']).copy()
    if valid.empty:
        fig.update_layout(**PLOTLY_LAYOUT, height=250, title="Weekly PnL Heatmap")
        return fig

    valid['week'] = valid['exit_time'].dt.isocalendar().week.astype(str) + '-' + valid['exit_time'].dt.year.astype(str)
    valid['week_start'] = valid['exit_time'].dt.to_period('W').apply(lambda x: x.start_time)

    pivot = valid.pivot_table(values='pnl', index='market', columns='week_start', aggfunc='sum', fill_value=0)

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=[d.strftime('%b %d') for d in pivot.columns],
        y=pivot.index.tolist(),
        colorscale=[[0, LOSS_COLOR], [0.5, '#1E2130'], [1, WIN_COLOR]],
        zmid=0,
        text=[[f'${v:+.0f}' for v in row] for row in pivot.values],
        texttemplate='%{text}',
        textfont=dict(size=11),
        hovertemplate='%{y}<br>Week of %{x}<br>PnL: $%{z:,.2f}<extra></extra>',
    ))

    fig.update_layout(
        **PLOTLY_LAYOUT, height=280,
        title=dict(text="Weekly PnL Heatmap", font=dict(size=18)),
        xaxis=dict(title="Week", tickangle=-45),
    )
    return fig


def radar_chart(df: pd.DataFrame) -> go.Figure:
    """Performance radar — compare markets on key metrics."""
    fig = go.Figure()

    if df.empty:
        fig.update_layout(**PLOTLY_LAYOUT, height=400, title="Market Radar")
        return fig

    categories = ['Win Rate', 'Profit Factor', 'Avg R', 'Max Streak', 'Trade Count']

    for symbol in df['symbol'].unique():
        sym = df[df['symbol'] == symbol]
        if len(sym) < 3:
            continue

        name = MARKET_NAMES.get(symbol, symbol)
        color = MARKET_COLORS.get(symbol, '#888888')

        wr = len(sym[sym['is_win']]) / len(sym) * 100 if len(sym) > 0 else 0
        gross_win = sym[sym['pnl'] > 0]['pnl'].sum()
        gross_loss = abs(sym[sym['pnl'] <= 0]['pnl'].sum())
        pf = gross_win / gross_loss if gross_loss > 0 else 0
        avg_r = sym['r_multiple'].mean() if len(sym) > 0 else 0

        streak = 0
        max_win_streak = 0
        for w in sym['is_win']:
            if w:
                streak += 1
                max_win_streak = max(max_win_streak, streak)
            else:
                streak = 0

        values = [
            min(wr / 60 * 100, 100),
            min(pf / 3 * 100, 100),
            min((avg_r + 1) / 2 * 100, 100),
            min(max_win_streak / 8 * 100, 100),
            min(len(sym) / 50 * 100, 100),
        ]

        fig.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            name=name,
            line=dict(color=color, width=2),
            fill='toself',
            fillcolor=f'rgba({int(color[1:3],16)},{int(color[3:5],16)},{int(color[5:7],16)},0.12)',
        ))

    fig.update_layout(
        **PLOTLY_LAYOUT, height=420,
        title=dict(text="Market Performance Radar", font=dict(size=18)),
        polar=dict(
            bgcolor='rgba(0,0,0,0)',
            radialaxis=dict(visible=True, range=[0, 100], gridcolor='#2A2A3E'),
            angularaxis=dict(gridcolor='#2A2A3E'),
        ),
    )
    return fig


def exit_reason_chart(df: pd.DataFrame) -> go.Figure:
    """Donut chart of exit reasons."""
    if df.empty:
        fig = go.Figure()
        fig.update_layout(**PLOTLY_LAYOUT, height=300, title="Exit Reasons")
        return fig

    reason_map = {
        'tp': 'Take Profit', 'sl': 'Stop Loss', 'ma_cross': 'MA Cross',
        'timeout': 'Timeout', 'trailing_sl': 'Trailing SL',
        'broker_closed': 'Broker', 'sl_be': 'BE Stop',
    }
    reasons = df['exit_reason'].map(lambda x: reason_map.get(x, x)).value_counts()

    colors = ['#00FF88', '#FF4B4B', '#FFD700', '#00D4FF', '#7B2FF7', '#FF8C00', '#888888']

    fig = go.Figure(data=[go.Pie(
        labels=reasons.index, values=reasons.values,
        hole=0.55, marker=dict(colors=colors[:len(reasons)]),
        textinfo='label+percent', textfont=dict(size=11),
        hovertemplate='%{label}: %{value} trades (%{percent})<extra></extra>',
    )])

    fig.update_layout(**PLOTLY_LAYOUT, height=340,
                       title=dict(text="Exit Reasons", font=dict(size=18)))
    return fig


def pnl_distribution_chart(df: pd.DataFrame) -> go.Figure:
    """R-multiple distribution histogram."""
    fig = go.Figure()

    if df.empty:
        fig.update_layout(**PLOTLY_LAYOUT, height=300, title="R-Multiple Distribution")
        return fig

    fig.add_trace(go.Histogram(
        x=df['r_multiple'], nbinsx=30,
        marker=dict(
            color=[WIN_COLOR if r > 0 else LOSS_COLOR for r in df['r_multiple']],
            line=dict(color='#2A2A3E', width=0.5),
        ),
        hovertemplate='R: %{x:.2f}<br>Count: %{y}<extra></extra>',
    ))

    fig.add_vline(x=0, line=dict(color='white', width=1, dash='dash'))

    fig.update_layout(
        **PLOTLY_LAYOUT, height=340,
        title=dict(text="R-Multiple Distribution", font=dict(size=18)),
        xaxis=dict(title="R-Multiple", gridcolor='#2A2A3E'),
        yaxis=dict(title="Frequency", gridcolor='#2A2A3E'),
        bargap=0.05,
    )
    return fig


# ── Streamlit App ─────────────────────────────────────────────

def main():
    st.set_page_config(
        page_title="Zero's Requiem — SBRS 2.0",
        page_icon="⚔️",
        layout="wide",
        initial_sidebar_state="collapsed",
    )

    st.markdown("""
    <style>
        .stApp { background-color: #0E1117; }
        .metric-card {
            background: linear-gradient(135deg, #1E2130 0%, #252840 100%);
            border-radius: 12px; padding: 20px; margin: 5px 0;
            border: 1px solid #2A2A3E;
        }
        .metric-value { font-size: 28px; font-weight: 700; color: #FAFAFA; }
        .metric-label { font-size: 13px; color: #8888AA; margin-top: 4px; }
        .win { color: #00FF88; }
        .loss { color: #FF4B4B; }
        .gold-text { color: #FFD700; }
        .header-title {
            font-size: 36px; font-weight: 800;
            background: linear-gradient(90deg, #FFD700, #FF8C00);
            -webkit-background-clip: text; -webkit-text-fill-color: transparent;
            margin-bottom: 0;
        }
        .header-sub { color: #8888AA; font-size: 14px; margin-top: -10px; }
        div[data-testid="stMetric"] { background: #1E2130; border-radius: 10px; padding: 15px; border: 1px solid #2A2A3E; }
        div[data-testid="stMetric"] label { color: #8888AA !important; }
        div[data-testid="stMetric"] div[data-testid="stMetricValue"] { color: #FAFAFA !important; }
    </style>
    """, unsafe_allow_html=True)

    # Header
    st.markdown('<p class="header-title">Zero\'s Requiem</p>', unsafe_allow_html=True)
    st.markdown('<p class="header-sub">SBRS 2.0 — Sovereign Performance Dashboard</p>', unsafe_allow_html=True)

    # Load data
    df = load_trades()
    states = load_all_states()

    # ── Top Metrics Row ────────────────────────────────────
    col1, col2, col3, col4, col5, col6 = st.columns(6)

    total_pnl = df['pnl'].sum() if not df.empty else 0
    total_trades = len(df)
    wr = (len(df[df['is_win']]) / len(df) * 100) if not df.empty and len(df) > 0 else 0
    gross_w = df[df['pnl'] > 0]['pnl'].sum() if not df.empty else 0
    gross_l = abs(df[df['pnl'] <= 0]['pnl'].sum()) if not df.empty else 0
    pf = gross_w / gross_l if gross_l > 0 else 0
    capital = sum(s.get('current_capital', 0) for s in states.values()) / max(len(states), 1)
    open_positions = sum(len(s.get('open_trades', [])) for s in states.values())

    pnl_delta = round(total_pnl, 2)
    col1.metric("Total PnL", f"${total_pnl:+,.2f}", delta=pnl_delta)
    col2.metric("Trades", f"{total_trades}")
    col3.metric("Win Rate", f"{wr:.1f}%")
    col4.metric("Profit Factor", f"{pf:.2f}")
    col5.metric("Capital", f"${capital:,.0f}")
    col6.metric("Open Positions", f"{open_positions}")

    st.divider()

    # ── Market Status Cards ────────────────────────────────
    st.subheader("Market Status")
    market_cols = st.columns(4)
    symbols_config = [
        ('GC=F', 'Gold', '#FFD700'),
        ('^GDAXI', 'DAX', '#00FF88'),
        ('^IXIC', 'NASDAQ', '#00D4FF'),
        ('GBPUSD=X', 'GBP/USD', '#7B2FF7'),
    ]

    for i, (sym, name, color) in enumerate(symbols_config):
        with market_cols[i]:
            sym_trades = df[df['symbol'] == sym] if not df.empty else pd.DataFrame()
            sym_pnl = sym_trades['pnl'].sum() if not sym_trades.empty else 0
            sym_count = len(sym_trades)
            sym_wr = (len(sym_trades[sym_trades['is_win']]) / len(sym_trades) * 100) if sym_count > 0 else 0

            state = states.get(sym, {})
            sym_open = len(state.get('open_trades', []))
            sym_pending = len(state.get('pending_setups', []))

            pnl_color = "win" if sym_pnl >= 0 else "loss"
            st.markdown(f"""
            <div class="metric-card">
                <div style="color:{color}; font-size:20px; font-weight:700;">{name}</div>
                <div class="metric-value {pnl_color}">${sym_pnl:+,.2f}</div>
                <div class="metric-label">
                    {sym_count} trades | {sym_wr:.0f}% WR | {sym_open} open | {sym_pending} pending
                </div>
            </div>
            """, unsafe_allow_html=True)

    st.divider()

    # ── Main Charts ────────────────────────────────────────
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Equity", "🎯 Trade Map", "📊 Analysis", "🔥 Heatmap"])

    with tab1:
        st.plotly_chart(equity_curve_chart(df), width="stretch")

    with tab2:
        st.plotly_chart(trade_scatter_chart(df), width="stretch")

    with tab3:
        c1, c2 = st.columns(2)
        with c1:
            st.plotly_chart(radar_chart(df), width="stretch")
        with c2:
            st.plotly_chart(exit_reason_chart(df), width="stretch")
        st.plotly_chart(pnl_distribution_chart(df), width="stretch")

    with tab4:
        st.plotly_chart(weekly_heatmap(df), width="stretch")

    # ── Recent Trades Table ────────────────────────────────
    st.divider()
    st.subheader("Recent Trades")

    if not df.empty:
        recent = df.sort_values('exit_time', ascending=False).head(20).copy()
        recent['PnL'] = recent['pnl'].apply(lambda x: f'${x:+,.2f}')
        recent['R'] = recent['r_multiple'].apply(lambda x: f'{x:+.2f}R')
        recent['Dir'] = recent['direction'].str.upper()
        recent['Market'] = recent['market']
        recent['Entry'] = recent['entry_time'].dt.strftime('%Y-%m-%d %H:%M')
        recent['Exit'] = recent['exit_time'].dt.strftime('%Y-%m-%d %H:%M')
        recent['Reason'] = recent['exit_reason']

        display_cols = ['Market', 'Dir', 'Entry', 'Exit', 'PnL', 'R', 'Reason']
        st.dataframe(
            recent[display_cols].reset_index(drop=True),
            width="stretch",
            hide_index=True,
        )
    else:
        st.info("No trades recorded yet. The dashboard will populate as the runner executes trades.")

    # Footer
    st.markdown("---")
    st.markdown(
        '<p style="color:#4A4A6A; text-align:center; font-size:12px;">'
        'Zero\'s Requiem — SBRS 2.0 Sovereign Performance Dashboard | '
        'Auto-refreshes every 60 seconds</p>',
        unsafe_allow_html=True
    )


if __name__ == '__main__':
    main()
