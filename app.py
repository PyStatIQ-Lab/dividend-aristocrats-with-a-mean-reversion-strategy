import streamlit as st
import pandas as pd
import yfinance as yf
import numpy as np
import talib

# Function to get stock data from yfinance
def get_stock_data(symbol):
    stock = yf.Ticker(symbol)
    data = stock.history(period="1y")  # Get 1 year of historical data
    return data

# Function to calculate RSI using yfinance data
def calculate_rsi(data, period=14):
    rsi = talib.RSI(data['Close'], timeperiod=period)
    return rsi

# Function to calculate Bollinger Bands using yfinance data
def calculate_bollinger_bands(data, period=20, nbdevup=2, nbdevdn=2):
    upperband, middleband, lowerband = talib.BBANDS(data['Close'], timeperiod=period, nbdevup=nbdevup, nbdevdn=nbdevdn, matype=0)
    return upperband, middleband, lowerband

# Function to analyze stocks
def analyze_stocks(df, risk_tolerance, time_horizon):
    selected_stocks = []
    
    for symbol in df['Symbol']:
        try:
            # Get the stock data
            data = get_stock_data(symbol)

            # Technical indicators
            rsi = calculate_rsi(data)
            upperband, middleband, lowerband = calculate_bollinger_bands(data)

            # Check if stock meets the fundamental and technical criteria
            # Fundamental criteria
            dividend_yield = yf.Ticker(symbol).info.get('dividendYield', 0)
            payout_ratio = yf.Ticker(symbol).info.get('payoutRatio', 0)
            
            if dividend_yield > 0.03 and payout_ratio < 0.60:
                # Technical criteria
                if rsi[-1] < 30 and data['Close'][-1] < lowerband[-1]:
                    if time_horizon == 'Short-term' and rsi[-1] > 50:
                        selected_stocks.append(symbol)
                    elif time_horizon == 'Long-term':
                        selected_stocks.append(symbol)
        except Exception as e:
            # Handle cases where the data for the stock is unavailable
            continue

    return selected_stocks

# Streamlit app
def main():
    st.title('Dividend Aristocrats + Mean Reversion Strategy')

    # File upload
    uploaded_file = st.file_uploader("Upload stocklist.xlsx", type=["xlsx"])

    if uploaded_file is not None:
        # Read the file
        xls = pd.ExcelFile(uploaded_file)

        # Display available sheet names
        sheet_names = xls.sheet_names
        selected_sheet = st.selectbox('Select a sheet', sheet_names)

        # Load the selected sheet into a DataFrame
        df = pd.read_excel(xls, sheet_name=selected_sheet)

        # Ensure 'Symbol' column exists
        if 'Symbol' not in df.columns:
            st.error("No 'Symbol' column found in the selected sheet!")
            return

        # Risk Tolerance
        risk_tolerance = st.selectbox('Risk Tolerance', ['Low', 'Medium', 'High'])
        time_horizon = st.selectbox('Time Horizon', ['Short-term', 'Long-term'])

        # Analyze the stocks based on user input
        if st.button('Analyze Stocks'):
            selected_stocks = analyze_stocks(df, risk_tolerance, time_horizon)

            if selected_stocks:
                st.write(f"Stocks that meet the criteria: {', '.join(selected_stocks)}")
            else:
                st.write("No stocks meet the criteria.")

if __name__ == "__main__":
    main()
