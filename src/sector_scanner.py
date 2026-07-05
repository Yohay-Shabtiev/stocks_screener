"""Sector performance scanner vs SPX (SPY).

All returns use bar data from yfinance:
  1W  -> weekly bars   (interval="1wk")
  1M  -> 1 monthly bar back
  3M  -> 3 monthly bars back
  6M  -> 6 monthly bars back
  YTD -> last close of previous year vs today

Bar data is cached to historical_data/sector_weekly_bars.csv and
sector_monthly_bars.csv and reused on later runs. Use --refresh-prices
to force a re-download.

Usage:
    python sector_scanner.py
    python sector_scanner.py --periods 1W 1M 3M
    python sector_scanner.py --refresh-prices
"""

from __future__ import annotations

import argparse
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import pandas as pd
import yfinance as yf

_ET = ZoneInfo("America/New_York")

SECTOR_ETFS: dict[str, str] = {
    "XLK":  "Technology",
    "XLF":  "Financials",
    "XLE":  "Energy",
    "XLV":  "Health Care",
    "XLI":  "Industrials",
    "XLY":  "Consumer Discretionary",
    "XLP":  "Consumer Staples",
    "XLU":  "Utilities",
    "XLRE": "Real Estate",
    "XLB":  "Materials",
    "XLC":  "Communication Services",
}

BENCHMARK = "SPY"

PERIODS = ["1W", "1M", "3M", "6M", "YTD"]

WEEKLY_CSV  = Path("historical_data") / "sector_weekly_bars.csv"
MONTHLY_CSV = Path("historical_data") / "sector_monthly_bars.csv"


def _closes(raw: pd.DataFrame) -> pd.DataFrame:
    df = raw["Close"] if isinstance(raw.columns, pd.MultiIndex) else raw
    return df.dropna(how="all")


def _load_or_download(
    csv_path: Path,
    download_fn,
    tickers: list[str],
    *,
    force: bool,
    label: str,
) -> pd.DataFrame:
    if not force and csv_path.exists():
        df = pd.read_csv(csv_path, index_col=0, parse_dates=True)
        if set(tickers).issubset(df.columns):
            print(f"Loaded {label} from {csv_path.name}.")
            return df
    print(f"Downloading {label}...")
    df = download_fn(tickers)
    csv_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(csv_path)
    return df


def download_weekly_closes(tickers: list[str], *, force: bool = False) -> pd.DataFrame:
    return _load_or_download(
        WEEKLY_CSV,
        lambda t: _closes(yf.download(t, period="3mo", interval="1wk", auto_adjust=True, progress=False)),
        tickers,
        force=force,
        label="weekly bars",
    )


def download_monthly_closes(tickers: list[str], *, force: bool = False) -> pd.DataFrame:
    return _load_or_download(
        MONTHLY_CSV,
        lambda t: _closes(yf.download(t, period="2y", interval="1mo", auto_adjust=True, progress=False)),
        tickers,
        force=force,
        label="monthly bars",
    )


def weekly_returns_from_closes(c: pd.DataFrame) -> dict[str, float]:
    """Current week return (since last Friday's close)."""
    if len(c) < 2:
        return {}
    return (c.iloc[-1] / c.iloc[-2] - 1).dropna().to_dict()


def monthly_returns_from_closes(c: pd.DataFrame) -> dict[str, dict[str, float | None]]:
    """Compute 1M/3M/6M/YTD returns from monthly close DataFrame."""
    current_year = datetime.now(_ET).year
    result: dict[str, dict[str, float | None]] = {}
    for ticker in c.columns:
        s = c[ticker].dropna()
        if s.empty:
            result[str(ticker)] = {}
            continue
        latest = float(s.iloc[-1])
        prev_yr = s[s.index.year < current_year]
        result[str(ticker)] = {
            "1M":  float(latest / s.iloc[-2]  - 1) if len(s) >= 2 else None,
            "3M":  float(latest / s.iloc[-4]  - 1) if len(s) >= 4 else None,
            "6M":  float(latest / s.iloc[-7]  - 1) if len(s) >= 7 else None,
            "YTD": float(latest / prev_yr.iloc[-1] - 1) if not prev_yr.empty else None,
        }
    return result


# Convenience wrappers (download + compute in one call)
def fetch_weekly_returns(tickers: list[str], *, force: bool = False) -> dict[str, float]:
    return weekly_returns_from_closes(download_weekly_closes(tickers, force=force))


def fetch_monthly_returns(tickers: list[str], *, force: bool = False) -> dict[str, dict[str, float | None]]:
    return monthly_returns_from_closes(download_monthly_closes(tickers, force=force))


def scan(periods: list[str] | None = None, *, force: bool = False) -> pd.DataFrame:
    if periods is None:
        periods = PERIODS

    tickers = [BENCHMARK] + list(SECTOR_ETFS.keys())

    week_rets    = fetch_weekly_returns(tickers, force=force) if "1W" in periods else {}
    monthly_data = fetch_monthly_returns(tickers, force=force)

    rows = []
    for etf, name in SECTOR_ETFS.items():
        row: dict = {"Ticker": etf, "Sector": name}
        for p in periods:
            if p == "1W":
                sector_ret = week_rets.get(etf)
                spx_ret    = week_rets.get(BENCHMARK)
            else:
                sector_ret = monthly_data.get(etf, {}).get(p)
                spx_ret    = monthly_data.get(BENCHMARK, {}).get(p)
            if sector_ret is None or spx_ret is None:
                row[p] = None
                row[f"{p}_vs_SPX"] = None
            else:
                row[p] = sector_ret
                row[f"{p}_vs_SPX"] = sector_ret - spx_ret
        rows.append(row)

    return pd.DataFrame(rows).set_index("Ticker")


def _fmt(val: float | None) -> str:
    if val is None:
        return "  n/a  "
    sign = "+" if val >= 0 else ""
    return f"{sign}{val * 100:.2f}%"


def _beat(val: float | None) -> str:
    return ">" if (val is not None and val > 0) else " "


def print_table(df: pd.DataFrame, periods: list[str]) -> None:
    print(f"\n{'Sector Relative Performance vs SPY':^80}")
    print("=" * 80)

    header = f"{'Ticker':<6}  {'Sector':<28}"
    for p in periods:
        header += f"  {p:>8}  {'vs SPX':>8}"
    print(header)
    print("-" * 80)

    last_p = periods[-1]
    vs_col = f"{last_p}_vs_SPX"
    if vs_col in df.columns:
        df = df.sort_values(vs_col, ascending=False)

    for ticker, row in df.iterrows():
        line = f"{ticker:<6}  {row['Sector']:<28}"
        for p in periods:
            ret = row.get(p)
            vs  = row.get(f"{p}_vs_SPX")
            line += f"  {_fmt(ret):>8}  {_beat(vs)}{_fmt(vs):>8}"
        print(line)

    print("-" * 80)
    print("  '>' = outperforming SPY for that period\n")

    # SPY return = any ETF's return minus its vs_SPX spread
    print("Benchmark (SPY):")
    ref = df.iloc[0]
    spy_line = f"  {'SPY':<6}  {'S&P 500':<28}"
    for p in periods:
        etf_ret = ref.get(p)
        vs_spx  = ref.get(f"{p}_vs_SPX")
        spy_ret = (etf_ret - vs_spx) if (etf_ret is not None and vs_spx is not None) else None
        spy_line += f"  {_fmt(spy_ret):>8}  {'':>9}"
    print(spy_line)
    print()


def main() -> None:
    parser = argparse.ArgumentParser(description="Sector scanner vs SPX")
    parser.add_argument(
        "--periods", nargs="+",
        choices=PERIODS,
        default=PERIODS,
    )
    parser.add_argument(
        "--refresh-prices", action="store_true",
        help="Re-download bar data (ignore saved CSVs)",
    )
    args = parser.parse_args()

    print("Fetching data...")
    df = scan(args.periods, force=args.refresh_prices)
    print_table(df, args.periods)


if __name__ == "__main__":
    main()
