"""Scan for stocks that outperform the ETF of their GICS sector.

All returns use bar data from yfinance — no daily data downloaded:
  1W  -> weekly bars   (current week vs last Friday's close)
  1M  -> 1 monthly bar back
  3M  -> 3 monthly bars back
  6M  -> 6 monthly bars back
  YTD -> since last year-end close

Categorisation (3M beat is the gate):
  DCA     -> beats ETF on 3M + both 1W and 1M  (consistent momentum)
  Delayed -> beats ETF on 3M + exactly one of 1W / 1M  (lagging, hunting ground)
  skip    -> no 3M beat, or beats 3M but lags both 1W and 1M

Sector mapping is fetched from yfinance once and cached to disk.
Delete historical_data/sector_mapping.json to force a refresh.

Usage:
    python stock_vs_sector.py
    python stock_vs_sector.py --periods 1W 1M 3M 6M
    python stock_vs_sector.py --refresh-cache
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import yfinance as yf
import pandas as pd

import lists
from sector_scanner import (
    SECTOR_ETFS, PERIODS,
    download_weekly_closes, download_monthly_closes,
    weekly_returns_from_closes, monthly_returns_from_closes,
)

GICS_TO_ETF: dict[str, str] = {
    "Technology":             "XLK",
    "Financial Services":     "XLF",
    "Energy":                 "XLE",
    "Healthcare":             "XLV",
    "Industrials":            "XLI",
    "Consumer Cyclical":      "XLY",
    "Consumer Defensive":     "XLP",
    "Utilities":              "XLU",
    "Real Estate":            "XLRE",
    "Basic Materials":        "XLB",
    "Communication Services": "XLC",
}

SECTOR_CACHE = Path("historical_data") / "sector_mapping.json"
WEEKLY_CSV   = Path("historical_data") / "weekly_bars.csv"
MONTHLY_CSV  = Path("historical_data") / "monthly_bars.csv"

FILTER_PERIODS = ("1W", "1M", "3M")


def get_bar_data(
    symbols: list[str],
    *,
    force: bool = False,
) -> tuple[dict[str, float], dict[str, dict[str, float | None]]]:
    """Load weekly/monthly bar closes from CSV if available, otherwise download and save."""

    def _load_or_fetch(csv_path: Path, download_fn, label: str) -> pd.DataFrame:
        if not force and csv_path.exists():
            df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
            if set(symbols).issubset(df.columns):
                print(f"Loaded {label} from {csv_path.name}.")
                return df
        print(f"Downloading {label}...")
        df = download_fn(symbols)
        csv_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_csv(csv_path)
        return df

    weekly_closes  = _load_or_fetch(WEEKLY_CSV,  download_weekly_closes,  "weekly bars")
    monthly_closes = _load_or_fetch(MONTHLY_CSV, download_monthly_closes, "monthly bars")

    return (
        weekly_returns_from_closes(weekly_closes),
        monthly_returns_from_closes(monthly_closes),
    )


def load_sector_mapping(
    tickers: list[str],
    *,
    refresh: bool = False,
    cache_path: Path = SECTOR_CACHE,
) -> dict[str, str]:
    cache: dict[str, str | None] = {}
    if not refresh and cache_path.exists():
        cache = json.loads(cache_path.read_text())

    missing = [t for t in tickers if t not in cache]
    if missing:
        print(f"Fetching sector info for {len(missing)} ticker(s) - this runs once then caches...")
        for t in missing:
            try:
                sector = yf.Ticker(t).info.get("sector")
                cache[t] = GICS_TO_ETF.get(sector)
            except Exception:
                cache[t] = None

        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(json.dumps(cache, indent=2))

    return {t: etf for t, etf in cache.items() if etf}


def _categorize(beats_1w: bool | None, beats_1m: bool | None, beats_3m: bool | None) -> str | None:
    if not beats_3m:
        return None
    short_beats = sum([bool(beats_1w), bool(beats_1m)])
    if short_beats == 2:
        return "DCA"
    if short_beats == 1:
        return "Delayed"
    return None


def scan(
    tickers: list[str],
    display_periods: list[str],
    sector_map: dict[str, str],
    week_rets: dict[str, float],
    monthly_data: dict[str, dict[str, float | None]],
) -> pd.DataFrame:
    all_periods = list(dict.fromkeys(
        p for p in PERIODS if p in set(display_periods) | set(FILTER_PERIODS)
    ))

    rows = []
    for ticker in tickers:
        etf = sector_map.get(ticker)
        if not etf:
            continue

        row: dict = {
            "Ticker": ticker,
            "Sector ETF": etf,
            "Sector": next((v for k, v in SECTOR_ETFS.items() if k == etf), etf),
        }

        for p in all_periods:
            if p == "1W":
                stock_ret = week_rets.get(ticker)
                etf_ret   = week_rets.get(etf)
            else:
                stock_ret = monthly_data.get(ticker, {}).get(p)
                etf_ret   = monthly_data.get(etf, {}).get(p)

            spread = None if (stock_ret is None or etf_ret is None) else stock_ret - etf_ret
            row[p]             = stock_ret
            row[f"{p}_etf"]    = etf_ret
            row[f"{p}_spread"] = spread
            row[f"{p}_beats"]  = spread is not None and spread > 0

        row["category"] = _categorize(
            row.get("1W_beats"), row.get("1M_beats"), row.get("3M_beats")
        )
        rows.append(row)

    return pd.DataFrame(rows).set_index("Ticker")


def _fmt(val: float | None) -> str:
    if val is None:
        return "  n/a  "
    sign = "+" if val >= 0 else ""
    return f"{sign}{val * 100:.2f}%"


def _beat(spread: float | None) -> str:
    return ">" if (spread is not None and spread > 0) else " "


def _print_group(group: pd.DataFrame, label: str, sort_col: str, display_periods: list[str]) -> None:
    if group.empty:
        return
    group = group.sort_values(sort_col, ascending=False)
    print(f"\n  [{label}]")
    print(f"  {'Ticker':<8}  " + "  ".join(f"{p:>10}  {'vs ETF':>8}" for p in display_periods))
    print("  " + "-" * (12 + 22 * len(display_periods)))
    for ticker, row in group.iterrows():
        parts = [
            f"{_fmt(row.get(p)):>10}  {_beat(row.get(f'{p}_spread'))}{_fmt(row.get(f'{p}_spread')):>8}"
            for p in display_periods
        ]
        print(f"  {ticker:<8}  " + "  ".join(parts))


def print_results(df: pd.DataFrame, display_periods: list[str]) -> None:
    sort_col = f"{'3M' if '3M' in display_periods else display_periods[-1]}_spread"

    for etf, group in sorted(df.groupby("Sector ETF"), key=lambda x: x[0]):
        sector_name = group["Sector"].iloc[0]
        dca     = group[group["category"] == "DCA"]
        delayed = group[group["category"] == "Delayed"]

        if dca.empty and delayed.empty:
            continue

        ref = group.iloc[0]
        etf_line = "  ".join(f"{p}: {_fmt(ref.get(f'{p}_etf'))}" for p in display_periods)
        print("\n" + "=" * 76)
        print(f"  {etf}  {sector_name:<28}  ETF -> {etf_line}")

        _print_group(dca,     "DCA - consistent outperformers",  sort_col, display_periods)
        _print_group(delayed, "Delayed - lagging but 3M strong", sort_col, display_periods)

    print("\n" + "=" * 76)
    print("  [DCA] beats ETF on 1W+1M+3M  |  [Delayed] beats 3M, lags on one of 1W/1M")
    print("  '>' = beating the sector ETF for that period\n")


def main() -> None:
    parser = argparse.ArgumentParser(description="Stocks vs sector ETF scanner")
    parser.add_argument(
        "--periods", nargs="+",
        choices=PERIODS,
        default=["1W", "1M", "3M"],
    )
    parser.add_argument(
        "--refresh-cache", action="store_true",
        help="Re-fetch sector assignments from yfinance",
    )
    parser.add_argument(
        "--refresh-prices", action="store_true",
        help="Re-download bar data (ignore saved CSVs)",
    )
    args = parser.parse_args()

    display_periods = list(dict.fromkeys(
        p for p in PERIODS if p in set(args.periods) | set(FILTER_PERIODS)
    ))

    sector_map  = load_sector_mapping(lists.all_tickers, refresh=args.refresh_cache)
    all_symbols = sorted(set(sector_map.keys()) | set(sector_map.values()))

    week_rets, monthly_data = get_bar_data(all_symbols, force=args.refresh_prices)

    df = scan(lists.all_tickers, display_periods, sector_map, week_rets, monthly_data)
    print_results(df, display_periods)


if __name__ == "__main__":
    main()
