"""Minimal entrypoint script for downloading OHLCV data from Yahoo Finance.

This script is meant to be scheduled (for example via AWS EventBridge / Lambda / ECS task)
and its *only* responsibility is:
- read a list of tickers from lists.py
- download/refresh historical OHLCV data via indicators.data_fetch.download_stock_data
- store/append the data into historical_data/raw_data/<TICKER>.csv

"""

from pathlib import Path
from typing import Iterable

import pandas as pd

import lists
from indicators.indicators import add_SMAs, add_EMAs, add_bollinger_bands, add_atr
from indicators.analysis import crossing_upper_BB
from indicators.data_fetch import download_stock_data
from options import iv_module 



OPTIONS_CHAIN_DIR = Path("historical_data") / "options_chain"
RAW_DATA_DIR = Path("historical_data") / "raw_data"
HISTORICAL_INDICATOR_DIR = Path("historical_data") / "indicator_data"


def ensure_dir(path: Path) -> None:
    """Create the raw data directory if it does not exist."""
    path.mkdir(parents=True, exist_ok=True)


def update_single_ticker(ticker: str, period: str = "5y", interval: str = "1d") -> None:
    """
    Download data for a single ticker and merge it into its CSV under RAW_DATA_DIR.

    - If the CSV does not exist, it will be created.
    - If it exists, new data will be appended and duplicate dates removed (keeping the last).
    """
    ensure_dir(RAW_DATA_DIR)

    csv_path = RAW_DATA_DIR / f"{ticker}.csv"

    try:
        existing = pd.read_csv(csv_path, index_col=0, parse_dates=True)
    except FileNotFoundError:
        existing = pd.DataFrame()

    if existing.empty:
        # First time: grab full history
        new_data = download_stock_data(
            ticker=ticker,
            period=period,
            interval=interval
        )
    else:
        # Incremental update: from last saved date until today
        last_date = existing.index.max()  # Timestamp
        start_str = last_date.strftime("%Y-%m-%d")

        new_data = download_stock_data(
            ticker=ticker,
            start=start_str,    # <-- youג€™ll need download_stock_data to accept this
            interval=interval
        )

    if new_data is None or new_data.empty:
        print(f"{ticker}: no new data downloaded.")
        return

    if existing.empty:
        combined = new_data
    else:
        combined = pd.concat([existing, new_data])
        combined = combined[~combined.index.duplicated(keep="last")]

    combined = combined.round(3)
    combined.to_csv(csv_path)
    print(f"{ticker}: data saved to {csv_path}")


def download_ohlcv_data(tickers: Iterable[str], period: str = "1y", interval: str = "1d") -> None:
    """Loop over a list of tickers and update each one."""
    for ticker in tickers:
        try:
            update_single_ticker(ticker, period=period, interval=interval)
        except Exception as exc:  # noqa: BLE001
            print(f"ג ן¸ Failed to update {ticker}: {exc}")


def is_down_then_up_last_n(tickers: list, col: str, n: int) -> list[str]:
    """
    Return tickers where the last n values of col go down then up (V-shape).
    """
    if n < 3:
        return []

    matched = []
    for ticker in tickers:
        df = pd.read_csv(f"{HISTORICAL_INDICATOR_DIR}/{ticker}.csv", index_col=0, parse_dates=True)
        s = df[col].dropna().iloc[-n:]
        idx_min = s.idxmin()
        pos_min = s.index.get_loc(idx_min)

        if pos_min == 0 or pos_min == len(s) - 1:
            continue

        left = s.iloc[:pos_min + 1]
        right = s.iloc[pos_min:]
        if left.is_monotonic_decreasing and right.is_monotonic_increasing:
            matched.append(ticker)

    return matched


def add_ohlcv_to_indicator_csv(
    tickers: list,
    indicator_csv_path: str | Path,
    ohlcv_csv_path: str | Path,
) -> None:
    """
    Ensure the indicator CSV contains OHLCV columns for all available dates.

    - Reads indicator CSV (indexed by Date)
    - Reads OHLCV CSV (indexed by Date)
    - Unions the date index
    - Copies OHLCV columns (Open, High, Low, Close, etc.) into the indicator DF
    - Saves back to indicator_csv_path
    """
    indicator_csv_path = Path(indicator_csv_path)
    ohlcv_csv_path = Path(ohlcv_csv_path)

    for ticker in tickers:

        # 1) Load indicator and OHLCV
        try:
            df = pd.read_csv(
            indicator_csv_path / f"{ticker}.csv",
            index_col="Date",
            parse_dates=["Date"],
        ).sort_index()
        except FileNotFoundError:
            df = pd.DataFrame()

        ohlcv_df = pd.read_csv(
            ohlcv_csv_path / f"{ticker}.csv",
            index_col="Date",
            parse_dates=["Date"],
        ).sort_index()

        # 2) Align indexes: union of all dates
        combined_index = df.index.union(ohlcv_df.index)
        combined_index.name = "Date"
        df = df.reindex(combined_index)

        # 3) Copy OHLCV columns from ohlcv_df (aligned by index automatically)
        for col in ohlcv_df.columns:
            df[col] = ohlcv_df[col]

        # 4) Save back
        out_path = indicator_csv_path / f"{ticker}.csv"
        df.sort_index().to_csv(out_path)

        print(f"[{ticker}] Synced OHLCV into {indicator_csv_path}")


def main() -> None:
    
    # 1) Dowload raw ohlcv data
    # download_ohlcv_data(lists.all_tickers, period="5y", interval="1d")
    # add_ohlcv_to_indicator_csv(lists.all_tickers, HISTORICAL_INDICATOR_DIR, RAW_DATA_DIR)
    # 2) Download chain option data
    ensure_dir(OPTIONS_CHAIN_DIR)
    # iv_module.save_all_option_chains(lists.IV_tickers, OPTIONS_CHAIN_DIR)

    # 3) Add iv_30d
    ensure_dir(HISTORICAL_INDICATOR_DIR)
    # iv_module.calculate_iv_30d(lists.all_tickers, HISTORICAL_INDICATOR_DIR)
    # add_SMAs(lists.all_tickers, HISTORICAL_INDICATOR_DIR)
    # add_EMAs(lists.all_tickers, HISTORICAL_INDICATOR_DIR)
    # add_bollinger_bands(lists.all_tickers, HISTORICAL_INDICATOR_DIR)
    # add_atr(lists.all_tickers, HISTORICAL_INDICATOR_DIR)

    # listen for the record

    # crossing_upper_BB(lists.all_tickers)
    screen_tickers_sma_momentum(lists.all_tickers, HISTORICAL_INDICATOR_DIR)

    # for ticker in lists.all_tickers:
    #     df = pd.read_csv(f"{HISTORICAL_INDICATOR_DIR}/{ticker}.csv", index_col=0, parse_dates=True)
    #     # sma = df["SMA_21"].iloc[-10:-5]   # last 5 days
    #     sma = df["SMA_21"].iloc[-5:]   # last 5 days
    #     close_col = df["Close"].iloc[-21:]

    #     total_close_above_min = 0
    #     found = False
    #     # internal points of the 5-day window: indices 1, 2, 3 (0-based)
    #     for i in range(1, len(sma) - 1):
    #         if sma.iloc[i] < sma.iloc[i - 1] and sma.iloc[i] < sma.iloc[i + 1]:
    #             found = True
    #             min_point = sma.iloc[i]
    #             total_close_above_min = (close_col > min_point).sum()
    #             break

    #     if not found:
    #         continue

    #     if total_close_above_min >= 13 and \
    #         abs(df['Close'].iloc[-1] - df['SMA_21'].iloc[-1]) < 1.2 * df['ATR'].iloc[-1]:
    #             print(ticker)

    # for ticker in lists.all_tickers:
    #     df = pd.read_csv(f"{HISTORICAL_INDICATOR_DIR}/{ticker}.csv", index_col=0, parse_dates=True)
    #     left_edge = df["SMA_21"].iloc[-21]
    #     right_edge = df["SMA_21"].iloc[-1]
    #     min_val = df["SMA_21"].iloc[-21:].min()
    #     last21_close = df["Close"].iloc[-21:]
    #     if min_val > df["SMA_89"].iloc[-1]:
    #         if left_edge > min_val and right_edge > min_val:
    #             total_close_above_min = (last21_close > min_val).sum()
    #             if total_close_above_min >= 11:
    #                 print(ticker)

    # for ticker in lists.all_tickers:
    #     df = pd.read_csv(f"{HISTORICAL_INDICATOR_DIR}/{ticker}.csv", index_col=0, parse_dates=True)
    #     min_val = df["Close"].iloc[-55:].min()
    #     max_val = df["Close"].iloc[-55:].max()

    #     diff = max_val - min_val
    #     foibo38 = min_val + diff * 0.382
    #     foibo50 = min_val + diff * 0.5

    #     if foibo38 < df["Close"].iloc[-1] < foibo50:
    #         if df["Close"].iloc[-1] < df["SMA_21"].iloc[-1]:
    #             print(ticker)

    # for ticker in lists.all_tickers:
    #     df = pd.read_csv(f"{HISTORICAL_INDICATOR_DIR}/{ticker}.csv", index_col=0, parse_dates=True)
    #     last_day = df.iloc[-1]
    #     if last_day['Close'] == df['Close'].iloc[-55:].max() and \
    #        last_day['SMA_55'] != df['SMA_55'].iloc[-55:].max():
    #         print(ticker)
    

def passes_sma_momentum_filter(
    df: pd.DataFrame,
    *,
    sma_col: str = "SMA_21",
    close_col: str = "Close",
    atr_col: str = "ATR",
    sma_days: int = 7,
    diff_days: int = 3,
    atr_mult: float = 2.0,
) -> bool:
    req = {sma_col, close_col, atr_col}
    if not req.issubset(df.columns):
        return False

    df = df.sort_index()
    df = df[~df.index.duplicated(keep="last")]

    if len(df) < max(sma_days, diff_days):
        return False

    sma_tail = df[sma_col].tail(sma_days)
    if sma_tail.isna().any():
        return False
    if not (sma_tail.diff().iloc[1:] > 0).all():
        return False

    diff_tail = (df[close_col] - df[sma_col]).tail(diff_days)
    if diff_tail.isna().any():
        return False
    if not (diff_tail > 0).all():
        return False
    if not (diff_tail.diff().iloc[1:] > 0).all():
        return False

    last_close = df[close_col].iloc[-1]
    last_sma   = df[sma_col].iloc[-1]
    last_atr   = df[atr_col].iloc[-1]
    if pd.isna(last_atr):
        return False

    return abs(last_close - last_sma) <= 3 * last_atr
    # return True


def screen_tickers_sma_momentum(
    tickers: list[str],
    indicator_dir: str | Path,
    *,
    sma_days: int = 7,
    diff_days: int = 3,
    atr_mult: float = 2.0,
) -> list[str]:
    indicator_dir = Path(indicator_dir)
    passed: list[str] = []

    for ticker in tickers:
        path = indicator_dir / f"{ticker}.csv"
        try:
            df = pd.read_csv(path, index_col=0, parse_dates=True)
        except FileNotFoundError:
            continue

        if passes_sma_momentum_filter(
            df,
            sma_days=sma_days,
            diff_days=diff_days,
            atr_mult=atr_mult,
        ):
            passed.append(ticker)

    for t in passed:
        print(t)

if __name__ == "__main__":

    main()
