# Level Retest Scanner + Inverted Chart

A Streamlit app that helps you visualize and *scan for your favorite pattern*:

> **Breakout above a key level → Pullback (retest) to that level → Aggressive takeoff.**

It also includes an **invert chart** toggle so that deep selloffs display like strong rallies — a psychological trick to help you see the *inverse* setups more clearly.

---

## ✨ Features
- Works with tickers like **BTC-USD**, **^IXIC** (NASDAQ Composite), **NQ=F** (NASDAQ futures)
- Choose **period** and **interval** (e.g., 60m, 1d)
- Input your **key level**
- Tune **tolerance**, **retest window**, **takeoff window**
- Optional **ATR thrust** filter
- **Invert chart** (mirror or negate) to view downtrends as uptrends
- Export **CSV** of detected signals

---

## 🧰 Tech Stack
- Python, Streamlit
- yfinance, pandas, numpy

---

## 🛠️ Quickstart

```bash
# 1) Create and enter a project folder
mkdir level-retest-scanner && cd level-retest-scanner

# 2) Create a virtual env (macOS)
python3 -m venv .venv
source .venv/bin/activate

# 3) Install dependencies
pip install -r requirements.txt

# 4) Run
streamlit run app.py
```

Open the local URL Streamlit prints (usually http://localhost:8501).

---

## 🧪 How the Scanner Works
1. **Breakout**: The close crosses up through your **level**.
2. **Retest**: Within `max_retest_window` bars, the price trades back to the level zone (± tolerance) and **closes back above** the level.
3. **Takeoff**: Within `takeoff_window` bars after the retest, the close exceeds either:
   - `level * (1 + takeoff_pct)`, or
   - `level + ATR * atr_mult` (if ATR filter is enabled).

Results include timestamps and return from the level at the takeoff bar.

---

## 📦 Requirements
See `requirements.txt`.

---

## 📌 Notes
- Intraday data availability varies per symbol/provider; if 5m isn't working, try 15m/60m or daily.
- Invert modes:
  - **mirror**: reflects around the median (keeps prices positive)
  - **negate**: multiplies by -1 (can go negative)

---

## 🖼️ Screenshots
Add a screenshot of the app here after you run it locally.

---

## 🧑‍💻 Author
Built by Alex Wilson (ASU Data Science) — portfolio-ready demo showcasing finance, data, and UI.