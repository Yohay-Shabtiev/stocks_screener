import pandas as pd
import lists

def add_change(df):
    df['Change'] = [(df.iloc[i]['Close'] - df.iloc[i]['Open']) for i in range(df.shape[0])]

def add_SMAs(tickers, indicator_data_path):
    for ticker in tickers:
        try:
            existing = pd.read_csv(
                f"{indicator_data_path}/{ticker}.csv",
                index_col=0,
                parse_dates=True,
            )
        except FileNotFoundError:
            print(f"Could not read '{ticker}.csv' from {indicator_data_path}")
            continue

        if "Close" not in existing.columns:
            print(f"'Close' column missing for {ticker}, skipping SMA")
            continue

        close = existing["Close"]

        for period in lists.sma_periods:
            sma_column = f"SMA_{period}"
            full_sma = close.rolling(window=period).mean()

            if sma_column in existing.columns:
                # fill only previously empty rows
                mask = existing[sma_column].isna()
                existing.loc[mask, sma_column] = full_sma[mask]
            else:
                # first time creating this SMA column
                existing[sma_column] = full_sma

        existing = existing.round(4)
        existing.to_csv(f"{indicator_data_path}/{ticker}.csv")


def add_EMAs(tickers, indicator_data_path):
    for ticker in tickers:
        try:
            existing = pd.read_csv(
                f"{indicator_data_path}/{ticker}.csv",
                index_col=0,
                parse_dates=True,
            )
        except FileNotFoundError:
            print(f"Could not read '{ticker}.csv' from {indicator_data_path}")
            continue

        if "Close" not in existing.columns:
            print(f"'Close' column missing for {ticker}, skipping EMA")
            continue

        close = existing["Close"]

        for period in lists.ema_periods:
            ema_column = f"EMA_{period}"
            full_ema = close.ewm(span=period, adjust=False).mean()

            if ema_column in existing.columns:
                mask = existing[ema_column].isna()
                existing.loc[mask, ema_column] = full_ema[mask]
            else:
                existing[ema_column] = full_ema

        existing = existing.round(4)
        existing.to_csv(f"{indicator_data_path}/{ticker}.csv")


def add_bollinger_bands(tickers, indicator_data_path, window=21):
    for ticker in tickers:
        try:
            existing = pd.read_csv(
                f"{indicator_data_path}/{ticker}.csv",
                index_col=0,
                parse_dates=True,
            )
        except FileNotFoundError:
            print(f"Could not read '{ticker}.csv' from {indicator_data_path}")
            continue

        if "Close" not in existing.columns:
            print(f"'Close' column missing for {ticker}, skipping BB")
            continue

        close = existing["Close"]

        # make sure SMA_21 exists (incrementally)
        sma_col = "SMA_21"
        full_sma21 = close.rolling(window=window).mean()

        if sma_col in existing.columns:
            mask_sma = existing[sma_col].isna()
            existing.loc[mask_sma, sma_col] = full_sma21[mask_sma]
        else:
            existing[sma_col] = full_sma21

        # full rolling std
        std_full = close.rolling(window).std()

        # Upper / Lower / BandWidth – fill only NaNs if already exist
        upper_col = "UpperBand"
        lower_col = "LowerBand"
        bw_col = "BandWidth"

        full_upper = existing[sma_col] + 2 * std_full
        full_lower = existing[sma_col] - 2 * std_full
        full_bw = (full_upper - full_lower) / existing[sma_col]

        for col_name, full_series in [
            (upper_col, full_upper),
            (lower_col, full_lower),
            (bw_col, full_bw),
        ]:
            if col_name in existing.columns:
                mask = existing[col_name].isna()
                existing.loc[mask, col_name] = full_series[mask]
            else:
                existing[col_name] = full_series

        # we don't keep StdDev column anymore
        existing = existing.round(4)
        existing.to_csv(f"{indicator_data_path}/{ticker}.csv")


def add_atr(tickers, indicator_data_path, period=14):
    for ticker in tickers:
        try:
            existing = pd.read_csv(
                f"{indicator_data_path}/{ticker}.csv",
                index_col=0,
                parse_dates=True,
            )
        except FileNotFoundError:
            print(f"Could not read '{ticker}.csv' from {indicator_data_path}")
            continue

        if existing.empty:
            print(f"No data for ATR for '{ticker}'")
            continue

        if not {"High", "Low", "Close"}.issubset(existing.columns):
            print(f"Missing High/Low/Close for '{ticker}', skipping ATR")
            continue

        high = existing["High"]
        low = existing["Low"]
        close = existing["Close"]

        # True Range for all rows
        tr = [
            max(
                high.iloc[i] - low.iloc[i],
                abs(high.iloc[i] - close.iloc[i - 1]),
                abs(low.iloc[i] - close.iloc[i - 1]),
            )
            for i in range(1, len(close))
        ]
        tr.insert(0, high.iloc[0] - low.iloc[0])
        tr_series = pd.Series(tr, index=existing.index)

        full_atr = tr_series.rolling(window=period, min_periods=1).mean()

        if "ATR" in existing.columns:
            mask = existing["ATR"].isna()
            existing.loc[mask, "ATR"] = full_atr[mask]
        else:
            existing["ATR"] = full_atr

        existing = existing.round(4)
        existing.to_csv(f"{indicator_data_path}/{ticker}.csv")


# def add_EMAs(df, ema_periods):
    
#     for period in ema_periods:
#         ema_column = f"EMA_{period}"
#         df[ema_column] = df['Close'].ewm(span=period, adjust=False).mean()

# def add_bollinger_bands(df, window=21):
    
#     df['StdDev'] = df['Close'].rolling(window).std()
#     df['UpperBand'] = df['SMA_21'] + (df['StdDev'] * 2)
#     df['LowerBand'] = df['SMA_21'] - (df['StdDev'] * 2)
#     df['BandWidth'] = (df['UpperBand'] - df['LowerBand']) / df['SMA_21']

#     df = df.drop(columns=['StdDev'])

# def add_atr(df, period=14):
#     high = df['High']
#     low = df['Low']
#     close = df['Close']

#     tr = [max(high.iloc[i] - low.iloc[i],
#               abs(high.iloc[i] - close.iloc[i - 1]),
#               abs(low.iloc[i] - close.iloc[i - 1])) for i in range(1, len(close))]

#     tr.insert(0, high.iloc[0] - low.iloc[0])

#     tr_series = pd.Series(tr, index=df.index)

#     atr = tr_series.rolling(window=period, min_periods=1).mean()
    
#     df['ATR'] = atr
