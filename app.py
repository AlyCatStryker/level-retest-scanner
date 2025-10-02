import math
import numpy as np
import pandas as pd
import yfinance as yf
import streamlit as st

# ----------------------------
# Helpers
# ----------------------------
def fetch_data(ticker: str, period: str, interval: str) -> pd.DataFrame:
    df = yf.download(tickers=ticker, period=period, interval=interval, auto_adjust=True, progress=False)
    if not isinstance(df.index, pd.DatetimeIndex):
        df.index = pd.to_datetime(df.index)
    df = df.rename(columns=str.title)  # ensure 'Open','High','Low','Close','Volume'
    df = df.dropna()
    return df

def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    high = df["High"]
    low = df["Low"]
    close = df["Close"]
    prev_close = close.shift(1)
    tr = pd.concat([(high - low).abs(),
                    (high - prev_close).abs(),
                    (low - prev_close).abs()], axis=1).max(axis=1)
    return tr.rolling(n, min_periods=1).mean()

def find_breakout_retests(
    df: pd.DataFrame,
    level: float,
    tolerance_pct: float = 0.001,
    max_retest_window: int = 20,
    takeoff_window: int = 20,
    takeoff_pct: float = 0.005,
    use_atr: bool = True,
    atr_mult: float = 1.0,
) -> pd.DataFrame:
    '''
    Detect pattern: price breaks above `level`, pulls back to retest it,
    then accelerates higher (takeoff).

    Returns a DataFrame of events with timestamps and returns.
    '''
    a = atr(df, 14)
    close = df["Close"]
    low = df["Low"]
    high = df["High"]

    results = []
    for i in range(1, len(df)):
        # Breakout: cross from below to above
        if close.iloc[i-1] < level <= close.iloc[i]:
            breakout_idx = i

            # Look for retest in the next `max_retest_window` bars
            retest_idx = None
            tol_up = level * (1 + tolerance_pct)
            tol_dn = level * (1 - tolerance_pct)
            end_rt = min(len(df)-1, breakout_idx + max_retest_window)
            for j in range(breakout_idx+1, end_rt+1):
                # Retest occurs if price trades back to the level zone
                if low.iloc[j] <= tol_up and high.iloc[j] >= tol_dn:
                    # Require close back above level to confirm hold
                    if close.iloc[j] >= level:
                        retest_idx = j
                        break

            if retest_idx is None:
                continue

            # Look for takeoff after retest
            takeoff_idx = None
            end_to = min(len(df)-1, retest_idx + takeoff_window)

            for k in range(retest_idx+1, end_to+1):
                threshold = level * (1 + takeoff_pct)
                if use_atr:
                    threshold = max(threshold, level + atr_mult * a.iloc[k])
                if close.iloc[k] >= threshold:
                    takeoff_idx = k
                    break

            if takeoff_idx is None:
                continue

            ret = (close.iloc[takeoff_idx] / level) - 1.0
            results.append({
                "breakout_time": df.index[breakout_idx],
                "retest_time": df.index[retest_idx],
                "takeoff_time": df.index[takeoff_idx],
                "level": level,
                "close_at_takeoff": float(close.iloc[takeoff_idx]),
                "return_from_level_pct": float(ret * 100.0),
                "bars_to_retest": int(retest_idx - breakout_idx),
                "bars_to_takeoff": int(takeoff_idx - retest_idx),
                "atr_at_takeoff": float(a.iloc[takeoff_idx]),
            })

    return pd.DataFrame(results)

def invert_series(series: pd.Series, method: str = "mirror"):
    '''
    Invert a price series so downtrends appear as uptrends.
    Methods:
      - 'negate': simply multiply by -1
      - 'mirror': reflect around the median so values remain positive
    '''
    if method == "negate":
        return -series
    med = series.median()
    return med + (med - series)

# ----------------------------
# UI
# ----------------------------
st.set_page_config(page_title="Level Retest Scanner", layout="wide")
st.title("📈 Level Retest Scanner + Inverted Chart")

with st.sidebar:
    st.subheader("Data")
    ticker = st.text_input("Ticker (examples: BTC-USD, ^IXIC, NQ=F)", value="BTC-USD")
    period = st.selectbox("Period", ["7d","1mo","3mo","6mo","1y","2y","5y","max"], index=4)
    interval = st.selectbox("Interval", ["5m","15m","30m","60m","1d"], index=3)
    st.caption("Note: very small intervals may be limited by data providers.")

    st.subheader("Strategy")
    level = st.number_input("Key Level (your line in the sand)", value=60000.0, step=100.0, format="%.4f")
    tolerance_pct = st.slider("Retest tolerance (%)", min_value=0.01, max_value=0.50, value=0.10, step=0.01) / 100.0
    max_retest_window = st.number_input("Max bars to find retest", value=20, min_value=1, step=1)
    takeoff_window = st.number_input("Max bars to confirm takeoff", value=20, min_value=1, step=1)
    takeoff_pct = st.slider("Min takeoff (% above level)", min_value=0.10, max_value=3.0, value=0.50, step=0.10) / 100.0
    use_atr = st.checkbox("Also require ATR-based thrust", value=True)
    atr_mult = st.slider("ATR multiplier", min_value=0.5, max_value=3.0, value=1.0, step=0.1)

    st.subheader("Chart")
    invert = st.checkbox("Invert chart (make drops look like rallies)", value=False)
    invert_method = st.selectbox("Invert method", ["mirror","negate"], index=0, help="Mirror keeps values positive; negate multiplies by -1.")

    run_btn = st.button("Run Scan")

# Load
df = fetch_data(ticker, period, interval)

left, right = st.columns([2,1], gap="large")

with left:
    st.subheader(f"Price Chart — {ticker}")
    chart_df = df.copy()
    if invert:
        chart_df["Close"] = invert_series(chart_df["Close"], method=invert_method)
        st.caption("Inverted view enabled. You're seeing declines as rises (for psychology).")

    # Use Streamlit native chart for speed
    st.line_chart(chart_df["Close"], height=360)

    # Draw level line as a small table indicator (Streamlit doesn't natively overlay horizontal lines)
    st.markdown(f"**Level:** `{level}`  •  **Tolerance:** ±{tolerance_pct*100:.2f}%  •  **Takeoff ≥** {takeoff_pct*100:.2f}%  {'• ATR filter ON' if use_atr else ''}")

with right:
    st.subheader("ATR (for context)")
    a = atr(df, 14)
    st.line_chart(a.rename("ATR"), height=180)

if run_btn:
    results = find_breakout_retests(
        df, level, tolerance_pct, max_retest_window, takeoff_window, takeoff_pct, use_atr, atr_mult
    )

    st.subheader("🔎 Pattern Matches")
    if results.empty:
        st.info("No breakout → retest → takeoff sequences found with the current settings.")
    else:
        # Show top rows
        st.dataframe(results, use_container_width=True)
        # Allow download
        csv = results.to_csv(index=False).encode("utf-8")
        st.download_button("Download results as CSV", data=csv, file_name="retest_signals.csv", mime="text/csv")

st.markdown("---")
st.caption("Tip: For NQ futures try `NQ=F`; for NASDAQ Composite use `^IXIC`; for Bitcoin use `BTC-USD`.")