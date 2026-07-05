================================================================

This project is for educational and informational purposes only. It does not constitute financial, investment, or trading advice. Nothing it outputs is a recommendation to buy or sell any security. Data is sourced from Yahoo Finance via `yfinance` and may be delayed, incomplete, or inaccurate. Use at your own risk — the author accepts no liability for any losses resulting from use of this software.

================================================================


# Stock Screener

A Python-based technical analysis screener that scans a watchlist of ~250 S&P 500 / Nasdaq stocks for tradeable setups using price action, momentum, and volatility indicators.

## What it does

- Downloads and incrementally updates daily OHLCV data from Yahoo Finance
- Computes technical indicators: SMAs (21/55/89/144/200), EMAs (5/8), Bollinger Bands, ATR, and implied volatility (IV-30d)
- Runs a library of pattern-detection screens across the full watchlist
- Writes matching tickers to output files for review

## Screens implemented

| Screen | Logic |
|---|---|
| SMA momentum | SMA trending up N days, price above and widening from SMA, within ATR range |
| Bollinger Band squeeze | BBW in bottom 35th percentile, expanding, price above SMA_21 |
| Crossed upper BB | High > UpperBand on last candle |
| ATR start-of-increase | ATR in 25th–40th percentile of trailing year |
| Cup & handle | Pattern detection over configurable lookback |
| Doji + Marubozu | Candlestick pattern combinations |
| Golden cross | Price > SMA_21, low BBW, SMA_55 approaching SMA_200, increasing EMAs |
| 52-week high proximity | Within 3% of 52w high, shrinking BBW, aligned SMAs |
| Volume surge | Short-window volume significantly above long-window baseline |
| Low-volatility pullback | Price dipped on declining volume then closed green |

## Project structure

```
src/
  main.py                # Entry point — data pipeline + active screen
  lists.py               # Ticker watchlists (all_tickers, IV_tickers, etc.)
  sector_scanner.py       # Sector ETF performance vs SPX
  stock_vs_sector.py      # Stocks that outperform their sector ETF
  compare_weeks.py        # Diff two weekly scan output files

  indicators/
    data_fetch.py        # Yahoo Finance download via yfinance
    indicators.py        # SMA, EMA, Bollinger Bands, ATR calculation
    analysis.py          # All screen/filter functions (writes to outputs/)
    analysis_utils.py    # Candlestick helpers (doji, marubozu detection)
    cup_handle.py        # Cup-and-handle pattern logic

  options/
    iv_module.py         # Options chain download + IV-30d calculation

requirements.txt         # Python dependencies
dockerfile               # Container setup for scheduled runs (e.g. AWS ECS)

historical_data/         # Local data cache (excluded from version control)
  raw_data/              # Per-ticker OHLCV CSVs
  indicator_data/        # Per-ticker CSVs with indicators added
  options_chain/         # Raw options chain snapshots

outputs/                 # Screen results and scan reports
```

## Setup

```bash
pip install -r requirements.txt
python src/main.py
```

Run all scripts from the project root so relative paths (`historical_data/`, `outputs/`) resolve correctly.

Data is cached locally under `historical_data/`. On the first run it downloads 5 years of history; subsequent runs fetch only the delta since the last saved date.

## Dependencies

- `yfinance` — market data
- `pandas` — data processing
- `numpy` — numerical helpers
