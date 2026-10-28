"""Bloomberg-inspired local dashboard for daily strategy research.

Run with:
    streamlit run app.py
"""

from __future__ import annotations

from datetime import date, timedelta

import pandas as pd
import streamlit as st

from strategy_layer.ui.backtest_service import BacktestService, STRATEGIES


st.set_page_config(
    page_title="BTSM Terminal",
    page_icon="▣",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp { background: #070b10; color: #d7e0e8; }
    [data-testid="stSidebar"] { background: #0c131b; border-right: 1px solid #263746; }
    h1, h2, h3 { color: #f2a900; letter-spacing: .03em; }
    .terminal-card { background:#0d151e; border:1px solid #2a4050; padding:14px; }
    .signal-long { color:#20d486; font-weight:700; }
    .signal-short { color:#ff6b6b; font-weight:700; }
    .signal-flat { color:#9aa8b5; font-weight:700; }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def run_backtest(
    ticker: str,
    strategy_key: str,
    start_date: str,
    end_date: str,
    initial_capital: float,
    transaction_cost_bps: float,
    params: tuple,
):
    parameter_map = dict(params)
    return BacktestService().run(
        ticker, strategy_key, start_date, end_date, initial_capital,
        transaction_cost_bps, parameter_map,
    )


def main() -> None:
    st.title("BTSM TERMINAL")
    st.caption("POINT-IN-TIME RESEARCH  |  DAILY MARKET DATA  |  PAPER TRADING WORKBENCH")

    with st.sidebar:
        st.header("RUN CONFIG")
        ticker = st.text_input("Ticker", "AAPL").strip().upper()
        strategy_keys = {item.label: item.key for item in STRATEGIES}
        strategy_label = st.selectbox("Strategy", list(strategy_keys))
        strategy_key = strategy_keys[strategy_label]
        pair_ticker = ""
        if strategy_key == "stat_arb":
            pair_ticker = st.text_input("Pair ticker", "MSFT").strip().upper()
        start = st.date_input("Start", date.today() - timedelta(days=365 * 3))
        end = st.date_input("End", date.today())
        capital = st.number_input("Initial capital", min_value=100.0, value=100_000.0, step=10_000.0)
        costs = st.number_input("Transaction costs (bps)", min_value=0.0, value=5.0, step=0.5)
        window = st.number_input("Band lookback", min_value=2, value=20, step=1)
        deviations = st.number_input("Band deviations", min_value=0.1, value=2.0, step=0.1)
        run = st.button("RUN BACKTEST", type="primary", use_container_width=True)

    selected = next(item for item in STRATEGIES if item.key == strategy_key)
    st.info(selected.description)
    if not run:
        st.markdown("### Workspace ready")
        st.write("Konfiguriere links einen Ticker und starte einen Daily-Backtest.")
        return
    if start >= end:
        st.error("Startdatum muss vor dem Enddatum liegen.")
        return

    params = {"window": int(window), "num_std": float(deviations)} if strategy_key == "noise_band" else {}
    if strategy_key == "stat_arb":
        params = {"other_ticker": pair_ticker, "lookback": 60, "entry_z": 2.0}
    try:
        result = run_backtest(
            ticker, strategy_key, start.isoformat(), end.isoformat(), capital, costs,
            tuple(sorted(params.items())),
        )
    except (RuntimeError, ValueError) as exc:
        st.error(str(exc))
        return

    returns = result.result.returns
    annualized = (1 + returns).prod() ** (252 / max(len(returns), 1)) - 1
    volatility = returns.std() * (252 ** 0.5)
    drawdown = (result.result.equity / result.result.equity.cummax() - 1).min()
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("TOTAL RETURN", f"{result.result.total_return:.2%}")
    c2.metric("ANNUALIZED", f"{annualized:.2%}")
    c3.metric("VOLATILITY", f"{volatility:.2%}")
    c4.metric("MAX DRAWDOWN", f"{drawdown:.2%}")

    left, right = st.columns([2, 1])
    with left:
        st.subheader("EQUITY / PRICE")
        chart = pd.DataFrame({
            "Equity": result.result.equity,
            "Close": result.prices["Close"] / result.prices["Close"].iloc[0] * capital,
        })
        st.line_chart(chart)
    with right:
        st.subheader("CURRENT SIGNAL")
        latest = result.signals.iloc[-1]
        position = latest["position"]
        css = "signal-long" if position > 0 else "signal-short" if position < 0 else "signal-flat"
        st.markdown(f'<p class="{css}">{latest["signal_reason"]}</p>', unsafe_allow_html=True)
        st.metric("Position", f"{position:.2f}")
        st.metric("Last close", f"{latest['close']:.2f}")

    st.subheader("SIGNAL BREAKDOWN")
    st.dataframe(
        result.signals.tail(100).sort_index(ascending=False),
        use_container_width=True,
        height=420,
    )
    st.caption("Signals are shifted by one daily bar in the engine to prevent same-bar look-ahead.")


if __name__ == "__main__":
    main()
