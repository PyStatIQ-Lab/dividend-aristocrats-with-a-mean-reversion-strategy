import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import talib

# Function to calculate RSI and Bollinger Bands
def calculate_indicators(stock_data):
    stock_data['RSI'] = talib.RSI(stock_data['Close'], timeperiod=14)
    upperband, middleband, lowerband = talib.BBANDS(stock_data['Close'], timeperiod=20, nbdevup=2, nbdevdn=2, matype=0)
    stock_data['Lower_BB'] = lowerband
    return stock_data

# Function to fetch stock data and perform analysis
def analyze_stocks(stock_list, min_market_cap, time_horizon):
    selected_stocks = []

    for symbol in stock_list:
        # Fetch stock data
        stock = yf.Ticker(symbol)
        stock_info = stock.info
        
        # Fundamental filters
        if 'dividendYield' in stock_info and stock_info['dividendYield'] > 0.03:  # Dividend Yield > 3%
            if 'payoutRatio' in stock_info and stock_info['payoutRatio'] < 60:  # Payout Ratio < 60%
                
                # Get historical stock data for technical analysis
                hist_data = stock.history(period="1y")
                hist_data = calculate_indicators(hist_data)
                
                # Technical filters (RSI < 30 and price < lower Bollinger Band)
                if hist_data['RSI'].iloc[-1] < 30 and hist_data['Close'].iloc[-1] < hist_data['Lower_BB'].iloc[-1]:
                    if stock_info['marketCap'] >= min_market_cap:
                        selected_stocks.append(symbol)
    
    return selected_stocks

# Streamlit UI
st.title("Dividend Aristocrats + Mean Reversion Strategy")

# Upload stocklist.xlsx
uploaded_file = st.file_uploader("Choose a stock list (Excel file)", type="xlsx")

if uploaded_file is not None:
    # Load the excel file
    excel_data = pd.ExcelFile(uploaded_file)
    
    # List available sheet names
    sheet_names = excel_data.sheet_names
    selected_sheet = st.selectbox("Select a Sheet to Analyze", sheet_names)
    
    # Read data from selected sheet
    stock_data = pd.read_excel(uploaded_file, sheet_name=selected_sheet)
    
    # Get the list of stock symbols
    stock_symbols = stock_data['Symbol'].dropna().tolist()
    
    # User input for Risk Tolerance
    min_market_cap = st.number_input("Minimum Market Cap (in billions)", min_value=1.0, value=10.0) * 1e9
    
    # User input for Time Horizon (Short-term or Long-term)
    time_horizon = st.selectbox("Time Horizon", ["Short-term (Hold until RSI > 50)", "Long-term (Hold for 1 year)"])
    
    # Analyze stocks based on user input
    if st.button("Analyze Stocks"):
        with st.spinner("Analyzing..."):
            result_stocks = analyze_stocks(stock_symbols, min_market_cap, time_horizon)
        
        if result_stocks:
            st.write(f"Found {len(result_stocks)} stocks that meet the criteria:")
            st.write(result_stocks)
        else:
            st.write("No stocks meet the criteria based on the given filters.")

else:
    st.write("Please upload a stock list to get started.")
