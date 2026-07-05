"""Refresh raw OHLCV data and recompute indicators (SMA/EMA/Bollinger/ATR) for all tickers.

Wraps the same steps as main.py's commented-out pipeline:
1. download_ohlcv_data  -> incrementally update historical_data/raw_data/<TICKER>.csv
2. add_ohlcv_to_indicator_csv -> merge OHLCV into historical_data/indicator_data/<TICKER>.csv
3. add_SMAs / add_EMAs / add_bollinger_bands / add_atr -> fill in new indicator rows

Runs sequentially (one yfinance call per ticker), so expect a few hours for the
full ~341-ticker universe if Yahoo Finance is throttling requests.

Usage:
    python src/refresh_data.py
"""

import os
os.environ.setdefault("PYTHONIOENCODING", "utf-8")
import sys
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

import lists
import main as m
from indicators.indicators import add_SMAs, add_EMAs, add_bollinger_bands, add_atr


def main() -> None:
    m.ensure_dir(m.RAW_DATA_DIR)

    print("=== downloading/updating raw OHLCV ===")
    m.download_ohlcv_data(lists.all_tickers, period="5y", interval="1d")

    print("=== merging OHLCV into indicator csvs ===")
    m.add_ohlcv_to_indicator_csv(lists.all_tickers, m.HISTORICAL_INDICATOR_DIR, m.RAW_DATA_DIR)

    print("=== recomputing SMA/EMA/BB/ATR ===")
    add_SMAs(lists.all_tickers, m.HISTORICAL_INDICATOR_DIR)
    add_EMAs(lists.all_tickers, m.HISTORICAL_INDICATOR_DIR)
    add_bollinger_bands(lists.all_tickers, m.HISTORICAL_INDICATOR_DIR)
    add_atr(lists.all_tickers, m.HISTORICAL_INDICATOR_DIR)

    print("DONE")


if __name__ == "__main__":
    main()
