import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf

# Load stock list from the Excel file
@st.cache_data
def load_stocklist():
    file_path = "stocklist.xlsx"
    xls = pd.ExcelFile(file_path)
    sheets = xls.sheet_names  # Get sheet names
    return {sheet: pd.read_excel(xls, sheet_name=sheet)['Symbol'].dropna().tolist() for sheet in sheets}

# Fetch stock data from yfinance and calculate technical indicators
def get_stock_data(symbol):
    try:
        stock = yf.Ticker(symbol)
        info = stock.info
        earnings = stock.calendar
        
        # Fundamental Factors
        dividend_yield = info.get('dividendYield', np.nan)  # Dividend Yield
        payout_ratio = info.get('payoutRatio', np.nan)  # Dividend Payout Ratio
        market_cap = info.get('marketCap', np.nan)  # Market Capitalization
        
        # Fetch historical price data (1 year for dividend yield + technical indicators)
        hist = stock.history(period="1y")
        
        if not hist.empty:
            # Calculate Bollinger Bands
            hist['BB_upper'], hist['BB_middle'], hist['BB_lower'] = (
                hist['Close'].rolling(window=20).mean() + 2 * hist['Close'].rolling(window=20).std(),
                hist['Close'].rolling(window=20).mean(),
                hist['Close'].rolling(window=20).mean() - 2 * hist['Close'].rolling(window=20).std()
            )

            # Calculate RSI (14-period)
            delta = hist['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            hist['RSI'] = 100 - (100 / (1 + rs))
            
            # Technical Signals
            rsi_oversold = 1 if hist['RSI'].iloc[-1] < 30 else 0
            price_below_bollinger = 1 if hist['Close'].iloc[-1] < hist['BB_lower'].iloc[-1] else 0
        else:
            rsi_oversold = price_below_bollinger = np.nan

        return {
            "Symbol": symbol,
            "Dividend Yield": dividend_yield if pd.notna(dividend_yield) else 0,
            "Payout Ratio": payout_ratio if pd.notna(payout_ratio) else 0,
            "Market Cap": market_cap if pd.notna(market_cap) else 0,
            "RSI < 30": rsi_oversold,
            "Price < Lower Bollinger Band": price_below_bollinger,
        }
    except Exception as e:
        return None

# Rank stocks based on Dividend Yield + Mean Reversion Strategy
def calculate_stock_scores(df, risk_tolerance, min_market_cap):
    df = df.dropna().reset_index(drop=True)
    
    # Apply Market Cap filter
    df = df[df['Market Cap'] >= min_market_cap]
    
    # Assigning Scores
    df["Dividend Score"] = df["Dividend Yield"].rank(ascending=False)
    df["Technical Score"] = df["RSI < 30"] + df["Price < Lower Bollinger Band"]
    
    # Calculate Combined Score
    df["Combined Score"] = (df["Dividend Score"] * 0.6) + (df["Technical Score"] * 0.4)
    
    # Sort based on Combined Score
    df = df.sort_values(by="Combined Score", ascending=False)
    
    return df

# Streamlit UI
st.title("📊 Dividend Aristocrats + Mean Reversion Strategy")

# Load stocklist
stocklist = load_stocklist()
sheet_selection = st.selectbox("Select Stock List", options=list(stocklist.keys()))

# User Inputs
risk_tolerance = st.radio("Select Risk Tolerance", ["Conservative", "Balanced", "Aggressive"], index=1)
min_market_cap = st.slider("Minimum Market Cap (in Billion)", min_value=1, max_value=2000, value=100, step=1)
time_horizon = st.radio("Select Time Horizon", ["Hold until RSI > 50", "Hold 1 Year"], index=0)

# Fetch data for selected stocks
symbols = stocklist[sheet_selection]
st.write(f"Fetching data for {len(symbols)} stocks...")

stock_data = [get_stock_data(symbol) for symbol in symbols]
stock_df = pd.DataFrame([s for s in stock_data if s])

# Check if data exists
if not stock_df.empty:
    filtered_df = calculate_stock_scores(stock_df, risk_tolerance, min_market_cap)
    
    # Display top stock picks with Combined Score
    st.subheader("🏆 Dividend Aristocrats + Mean Reversion Picks")
    st.dataframe(filtered_df[["Symbol", "Dividend Yield", "Payout Ratio", "RSI < 30", "Price < Lower Bollinger Band", "Combined Score"]].head(10))
    
    # Entry & Exit Strategy
    st.subheader("📈 Entry/Exit Points")
    filtered_df["Entry Point"] = "Buy now (oversold)"
    filtered_df["Exit Point"] = "Sell when RSI > 50" if time_horizon == "Hold until RSI > 50" else "Hold 1 year"
    st.dataframe(filtered_df[["Symbol", "Entry Point", "Exit Point"]].head(10))

else:
    st.warning("No stock data found. Try selecting another sheet or check stock symbols.")
