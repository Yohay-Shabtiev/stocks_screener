# THIS FILE CONTAINS ALL THE FUNCTIONS USE TO DOWNLOAD DATA 
import yfinance as yf
from datetime import datetime, timedelta
import os
import pandas as pd

def download_stock_data(
    ticker: str,
    interval: str,
    period: str | None = None,
    start: str | None = None,
    end: str | None = None,
):    
    try:
        df = yf.download(ticker, period=period, interval=interval)
        # , threads=False, auto_adjust=True)
        df.columns = [col[0] for col in df.columns]
        if df.empty:
            print(f"⚠️ No data found for {ticker}. Check the ticker symbol.")
            return None
        print(f"{ticker}    ✅")
        return df

    except Exception as e:
        print(f"❌ Error downloading data: {e}")
        return None


def download_specific_day_data(ticker):
    
    today = datetime.today()
    tommorow = today + timedelta(1)

    a = today.strftime("%Y-%m-%d")
    b = tommorow.strftime("%Y-%m-%d")

    try:
        df = yf.download(ticker, start=a, end=b, interval="1d")
        df.columns = [col[0] for col in df.columns]
        if df.empty:
            print(f"⚠️ No data found for {ticker}.")
            return None
        
        print(f"✅ Data for {ticker}")
        df.to_csv(f"today/{ticker}(1d-SOURCE).csv")
        return df

    except Exception as e:
        print(f"❌ Error downloading data: {e}")
        return None


def merge_yesterday_today(ticker):
    # Directories (relative to the script's location)
    yesterday_dir = "./yesterday"
    today_dir = "./today"

    # Filename
    filename = f"{ticker}(1d-SOURCE).csv"

    # Full paths to the files
    yesterday_file = os.path.join(yesterday_dir, filename)
    today_file = os.path.join(today_dir, filename)

    # Read the CSV files
    try:
        df_yesterday = pd.read_csv(yesterday_file, index_col=0)
        df_today_last = pd.read_csv(today_file, index_col=0).tail(1)  # Get the last row

        # Append the last line from today to yesterday
        updated_df = pd.concat([df_yesterday, df_today_last])

        # Save the updated data back to yesterday's file
        updated_df.to_csv(yesterday_file)
    
    except FileNotFoundError as e:
        print(f"Error: {e}")