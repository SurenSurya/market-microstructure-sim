import streamlit as st
import yfinance as yf
import pandas as pd
import pandas_ta as ta

# --- Page Setup ---
st.set_page_config(page_title="Market Strategy Simulator", layout="wide")
st.title("📊 Market Microstructure Strategy Simulator")

# --- Sidebar Inputs ---
st.sidebar.header("🔧 Strategy Configuration")

ticker = st.sidebar.text_input("Ticker", value="RELIANCE.NS")
start = st.sidebar.date_input("Start Date", value=pd.to_datetime("2022-01-01"))
end = st.sidebar.date_input("End Date", value=pd.to_datetime("2023-01-01"))
initial_capital = st.sidebar.number_input("Initial Capital (₹)", value=100000)
transaction_cost = st.sidebar.number_input("Transaction Cost (%)", value=0.1)
compounding = st.sidebar.checkbox("Enable Compounding", value=True)

indicator = st.sidebar.selectbox("Indicator", ["RSI", "SMA", "EMA", "MACD", "Bollinger Bands"])
param = st.sidebar.slider("Indicator Parameter", min_value=5, max_value=50, value=14)
timeframe = st.sidebar.selectbox("Timeframe", ["Daily", "Weekly", "Monthly"])
tf_map = {"Daily": "1D", "Weekly": "1W", "Monthly": "1M"}

# --- Fetch Real-Time Data ---
df = yf.download(ticker, start=start, end=end, progress=False)

# --- Flatten MultiIndex columns if needed ---
if isinstance(df.columns, pd.MultiIndex):
    df.columns = ['_'.join(col).strip() for col in df.columns]
else:
    df.columns = [str(col) for col in df.columns]

# --- Remove ticker suffix if present ---
suffix = f"_{ticker}"
df.columns = [col.replace(suffix, "") if isinstance(col, str) and col.endswith(suffix) else col for col in df.columns]

# --- Validate Data ---
required_cols = ["Open", "High", "Low", "Close", "Volume"]
missing_cols = [col for col in required_cols if col not in df.columns]

if df.empty:
    st.error("❌ No data returned. Check the ticker or date range.")
    st.stop()
elif missing_cols:
    st.error(f"❌ Missing columns: {missing_cols}. Data may be malformed or incomplete.")
    st.dataframe(df.head())
    st.stop()

# --- Resample Data ---
if timeframe != "Daily":
    df = df.resample(tf_map[timeframe]).agg({
        "Open": "first", "High": "max", "Low": "min", "Close": "last", "Volume": "sum"
    }).dropna()

# --- Apply Indicator ---
if indicator == "RSI":
    df.ta.rsi(length=param, append=True)
    signal_col = f"RSI_{param}"
elif indicator == "SMA":
    df.ta.sma(length=param, append=True)
    signal_col = f"SMA_{param}"
elif indicator == "EMA":
    df.ta.ema(length=param, append=True)
    signal_col = f"EMA_{param}"
elif indicator == "MACD":
    df.ta.macd(append=True)
    signal_col = "MACD_12_26_9"
elif indicator == "Bollinger Bands":
    df.ta.bbands(length=param, append=True)
    signal_col = f"BBL_{param}_2.0"

df.dropna(subset=[signal_col], inplace=True)

# --- Strategy Simulation ---
def simulate(df, capital, cost_pct, compound):
    position = 0
    trades = []
    equity_curve = []

    for i, row in df.iterrows():
        if "Close" not in row:
            st.error(f"❌ 'Close' column missing at {i}. Available columns: {list(row.index)}")
            st.stop()

        signal = row.get(signal_col, None)
        price = row["Close"]

        if pd.notna(signal) and signal < 30 and position == 0:
            qty = capital // price
            cost = qty * price * (cost_pct / 100)
            capital -= qty * price + cost
            position = qty
            trades.append((i, "BUY", price, qty))

        elif pd.notna(signal) and signal > 70 and position > 0:
            proceeds = position * price
            cost = proceeds * (cost_pct / 100)
            capital += proceeds - cost
            trades.append((i, "SELL", price, position))
            position = 0

        current_value = capital + (position * price if position > 0 else 0)
        equity_curve.append((i, current_value))

        if compound and position == 0:
            capital = current_value

    equity_df = pd.DataFrame(equity_curve, columns=["Date", "Equity"]).set_index("Date")
    return trades, capital, equity_df

# --- Run Simulation ---
trades, final_value, equity_df = simulate(df, initial_capital, transaction_cost, compounding)

# --- Display Results ---
st.subheader("📋 Trade Log")
trade_df = pd.DataFrame(trades, columns=["Date", "Type", "Price", "Quantity"])
st.dataframe(trade_df)

st.subheader("💰 Final Portfolio Value")
st.metric(label="Portfolio Value", value=f"₹{final_value:,.2f}")

st.subheader("📈 Equity Curve")
st.line_chart(equity_df)

# --- Export Buttons ---
st.subheader("📤 Export Results")
st.download_button("Download Trade Log", trade_df.to_csv(index=False), file_name="trade_log.csv")
st.download_button("Download Equity Curve", equity_df.to_csv(), file_name="equity_curve.csv")

# --- Strategy Notes ---
st.subheader("🧠 Strategy Notes")
notes = st.text_area("Add notes about this strategy for your portfolio or recruiter")
