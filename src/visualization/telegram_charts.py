"""
SBRS 2.0 — Telegram Visual Reports

Generates PNG chart images for weekly/daily Telegram summaries.
Designed with dark theme and market-specific color coding.

Usage:
    py -m src.visualization.telegram_charts          # Generate & send weekly report
    py -m src.visualization.telegram_charts --test   # Generate PNGs only (no send)
"""

import sqlite3
import sys
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path

try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    raise ImportError("Install plotly: py -m pip install plotly kaleido")

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
DB_PATH = PROJECT_ROOT / 'data' / 'zeros_requiem.db'
CHART_DIR = PROJECT_ROOT / 'logs' / 'charts'
CHART_DIR.mkdir(parents=True, exist_ok=True)

MARKET_COLORS = {
    'GC=F': '#FFD700', '^GDAXI': '#00FF88', '^IXIC': '#00D4FF',
    'GBPUSD=X': '#7B2FF7', 'BTC-USD': '#F7931A', 'ETH-USD': '#627EEA',
}
MARKET_NAMES = {
    'GC=F': 'Gold', '^GDAXI': 'DAX', '^IXIC': 'NASDAQ',
    'GBPUSD=X': 'GBP/USD', 'BTC-USD': 'BTC', 'ETH-USD': 'ETH',
}

BG = '#0E1117'
CARD = '#1E2130'
WIN = '#00FF88'
LOSS = '#FF4B4B'
TEXT = '#FAFAFA'
GRID = '#2A2A3E'
SUBTLE = '#6A6A8A'


def _load_trades(days: int = 7) -> pd.DataFrame:
    """Load trades from the last N days."""
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(str(DB_PATH))
    cutoff = (datetime.utcnow() - timedelta(days=days)).isoformat()
    df = pd.read_sql_query(
        f"SELECT * FROM trades WHERE exit_time > '{cutoff}' ORDER BY exit_time", conn
    )
    conn.close()
    if not df.empty:
        df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True, errors='coerce')
        df['entry_time'] = pd.to_datetime(df['entry_time'], utc=True, errors='coerce')
        df['is_win'] = df['pnl'] > 0
        df['market'] = df['symbol'].map(MARKET_NAMES).fillna(df['symbol'])
    return df


def _load_all_trades() -> pd.DataFrame:
    """Load all trades."""
    if not DB_PATH.exists():
        return pd.DataFrame()
    conn = sqlite3.connect(str(DB_PATH))
    df = pd.read_sql_query("SELECT * FROM trades ORDER BY exit_time", conn)
    conn.close()
    if not df.empty:
        df['exit_time'] = pd.to_datetime(df['exit_time'], utc=True, errors='coerce')
        df['entry_time'] = pd.to_datetime(df['entry_time'], utc=True, errors='coerce')
        df['is_win'] = df['pnl'] > 0
        df['market'] = df['symbol'].map(MARKET_NAMES).fillna(df['symbol'])
    return df


def generate_weekly_report(days: int = 7) -> Path:
    """
    Generate the weekly performance report image.
    Returns path to the saved PNG.
    """
    week_df = _load_trades(days)
    all_df = _load_all_trades()

    fig = make_subplots(
        rows=3, cols=2,
        row_heights=[0.4, 0.3, 0.3],
        subplot_titles=[
            'Portfolio Equity Curve (All Time)',
            'This Week — Trade Results',
            'PnL by Market (This Week)',
            'Win/Loss Ratio (This Week)',
            'R-Multiple Distribution (All Time)',
            'Weekly Summary',
        ],
        specs=[
            [{'type': 'scatter'}, {'type': 'scatter'}],
            [{'type': 'bar'}, {'type': 'pie'}],
            [{'type': 'histogram'}, {'type': 'table'}],
        ],
        vertical_spacing=0.12,
        horizontal_spacing=0.1,
    )

    # ── Panel 1: All-time equity curve ─────────────────────
    if not all_df.empty:
        for symbol in all_df['symbol'].unique():
            sym = all_df[all_df['symbol'] == symbol].sort_values('exit_time').dropna(subset=['exit_time'])
            if sym.empty:
                continue
            color = MARKET_COLORS.get(symbol, '#888888')
            name = MARKET_NAMES.get(symbol, symbol)
            cum = sym['pnl'].cumsum()
            fig.add_trace(go.Scatter(
                x=sym['exit_time'], y=cum, name=name,
                line=dict(color=color, width=2), mode='lines',
            ), row=1, col=1)

    # ── Panel 2: This week's trades as lollipop chart ──────
    if not week_df.empty:
        for _, trade in week_df.iterrows():
            color = WIN if trade['pnl'] > 0 else LOSS
            market = trade.get('market', '?')
            fig.add_trace(go.Scatter(
                x=[trade['exit_time']], y=[trade['pnl']],
                mode='markers+text', showlegend=False,
                marker=dict(color=color, size=12, symbol='diamond',
                            line=dict(color='white', width=1)),
                text=[f"{market}"], textposition='top center',
                textfont=dict(size=9, color=color),
            ), row=1, col=2)
        fig.add_hline(y=0, line=dict(color=SUBTLE, width=1, dash='dash'), row=1, col=2)

    # ── Panel 3: PnL by market bar chart ───────────────────
    if not week_df.empty:
        market_pnl = week_df.groupby('symbol')['pnl'].sum().reset_index()
        market_pnl['name'] = market_pnl['symbol'].map(MARKET_NAMES)
        market_pnl['color'] = market_pnl['pnl'].apply(lambda x: WIN if x > 0 else LOSS)
        fig.add_trace(go.Bar(
            x=market_pnl['name'], y=market_pnl['pnl'],
            marker=dict(color=market_pnl['color'].tolist(),
                        line=dict(color='white', width=0.5)),
            text=market_pnl['pnl'].apply(lambda x: f'${x:+,.0f}'),
            textposition='outside', textfont=dict(size=10),
            showlegend=False,
        ), row=2, col=1)

    # ── Panel 4: Win/Loss pie chart ────────────────────────
    if not week_df.empty:
        wins = len(week_df[week_df['is_win']])
        losses = len(week_df) - wins
        fig.add_trace(go.Pie(
            labels=['Wins', 'Losses'], values=[wins, losses],
            marker=dict(colors=[WIN, LOSS]),
            hole=0.5, textinfo='value+percent',
            textfont=dict(size=12),
            showlegend=False,
        ), row=2, col=2)

    # ── Panel 5: R-multiple distribution ───────────────────
    if not all_df.empty and 'r_multiple' in all_df.columns:
        valid_r = all_df['r_multiple'].dropna()
        if len(valid_r) > 0:
            colors = [WIN if r > 0 else LOSS for r in valid_r]
            fig.add_trace(go.Histogram(
                x=valid_r, nbinsx=25,
                marker=dict(color=WIN, line=dict(color=GRID, width=0.5)),
                showlegend=False,
            ), row=3, col=1)

    # ── Panel 6: Summary table ─────────────────────────────
    total_pnl = week_df['pnl'].sum() if not week_df.empty else 0
    total_trades = len(week_df)
    wr = (len(week_df[week_df['is_win']]) / total_trades * 100) if total_trades > 0 else 0
    all_pnl = all_df['pnl'].sum() if not all_df.empty else 0
    all_trades = len(all_df)

    fig.add_trace(go.Table(
        header=dict(
            values=['Metric', 'This Week', 'All Time'],
            fill_color=CARD, font=dict(color=TEXT, size=11),
            line=dict(color=GRID),
        ),
        cells=dict(
            values=[
                ['Trades', 'PnL', 'Win Rate', 'Best Trade', 'Worst Trade'],
                [
                    str(total_trades),
                    f'${total_pnl:+,.2f}',
                    f'{wr:.0f}%',
                    f'${week_df["pnl"].max():+,.2f}' if not week_df.empty else '—',
                    f'${week_df["pnl"].min():+,.2f}' if not week_df.empty else '—',
                ],
                [
                    str(all_trades),
                    f'${all_pnl:+,.2f}',
                    f'{len(all_df[all_df["is_win"]]) / all_trades * 100:.0f}%' if all_trades > 0 else '—',
                    f'${all_df["pnl"].max():+,.2f}' if not all_df.empty else '—',
                    f'${all_df["pnl"].min():+,.2f}' if not all_df.empty else '—',
                ],
            ],
            fill_color=BG, font=dict(color=TEXT, size=10),
            line=dict(color=GRID),
        ),
    ), row=3, col=2)

    # ── Layout ─────────────────────────────────────────────
    now = datetime.utcnow()
    week_start = (now - timedelta(days=days)).strftime('%b %d')
    week_end = now.strftime('%b %d, %Y')

    fig.update_layout(
        title=dict(
            text=f"SBRS 2.0 — Weekly Report ({week_start} – {week_end})",
            font=dict(size=22, color='#FFD700', family='Inter'),
            x=0.5,
        ),
        paper_bgcolor=BG,
        plot_bgcolor=BG,
        font=dict(color=TEXT, family='Inter, sans-serif'),
        height=1000,
        width=1200,
        showlegend=True,
        legend=dict(bgcolor='rgba(0,0,0,0)', font=dict(size=10)),
    )

    for ax_name in ['xaxis', 'xaxis2', 'xaxis3', 'xaxis5']:
        fig.update_layout(**{ax_name: dict(gridcolor=GRID, showgrid=True)})
    for ax_name in ['yaxis', 'yaxis2', 'yaxis3', 'yaxis5']:
        fig.update_layout(**{ax_name: dict(gridcolor=GRID, showgrid=True)})

    output_path = CHART_DIR / f"weekly_report_{now.strftime('%Y%m%d')}.png"
    fig.write_image(str(output_path), scale=2)
    print(f"  Weekly report saved to {output_path}")
    return output_path


def send_weekly_telegram(image_path: Path) -> bool:
    """Send the weekly report image via Telegram."""
    import os
    try:
        from dotenv import load_dotenv
        load_dotenv(PROJECT_ROOT / '.env')
    except ImportError:
        pass

    token = os.getenv('TELEGRAM_BOT_TOKEN', '')
    chat_id = os.getenv('TELEGRAM_CHAT_ID', '')

    if not token or not chat_id:
        print("  Telegram not configured, skipping send")
        return False

    import requests
    url = f"https://api.telegram.org/bot{token}/sendPhoto"

    week_df = _load_trades(7)
    total_pnl = week_df['pnl'].sum() if not week_df.empty else 0
    total_trades = len(week_df)
    emoji = "📈" if total_pnl >= 0 else "📉"

    caption = (
        f"{emoji} <b>SBRS 2.0 Weekly Report</b>\n"
        f"Trades: {total_trades} | PnL: ${total_pnl:+,.2f}\n"
        f"<i>See attached chart for full breakdown</i>"
    )

    try:
        with open(image_path, 'rb') as photo:
            resp = requests.post(url, data={
                'chat_id': chat_id,
                'caption': caption,
                'parse_mode': 'HTML',
            }, files={'photo': photo}, timeout=30)
        return resp.status_code == 200
    except Exception as e:
        print(f"  Error sending Telegram photo: {e}")
        return False


def main():
    print("SBRS 2.0 — Weekly Report Generator")
    print("=" * 50)

    test_mode = '--test' in sys.argv

    print("  Generating weekly report chart...")
    path = generate_weekly_report(days=7)

    if test_mode:
        print(f"  Test mode — chart saved to {path}")
        print("  Open the PNG to preview the report.")
    else:
        print("  Sending to Telegram...")
        success = send_weekly_telegram(path)
        if success:
            print("  Weekly report sent to Telegram!")
        else:
            print("  Failed to send to Telegram (check token/chat_id)")


if __name__ == '__main__':
    main()
