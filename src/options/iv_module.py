from __future__ import annotations
import yfinance as yf
import pandas as pd
import numpy as np
from datetime import date, datetime, timedelta
from pathlib import Path
import lists  # your existing lists module

# --------------------------------------------------------------------
# Paths
# --------------------------------------------------------------------
# Adjust this if your structure is different.
# We assume:
# BASE_DIR /
#   options/
#   historical_data/
#   <your_package>/
#     <this_file>.py


# --------------------------------------------------------------------
# Core IV function
# --------------------------------------------------------------------
def calc_ticker_30d_iv(
    ticker: str,
    obs_date,                     # pd.Timestamp, datetime, or date
    ohlcv_df: pd.DataFrame,
    days_forward: int = 30,
    options_root: str | Path = "historical_data/options_chain",
):
    """
    Compute a 30d IV for `ticker` as of `obs_date`, using locally saved
    option-chain CSVs under: historical_data/options_chain/{ticker}/

    File naming convention (example, obs_date=2025-12-05, ticker=AAPL):
        2025-12-05AAPL_2026-01-02_calls.csv
        2025-12-05AAPL_2026-01-02_puts.csv
    """

    # Normalize obs_date to a date
    if isinstance(obs_date, pd.Timestamp):
        obs_date = obs_date.date()
    elif isinstance(obs_date, datetime):
        obs_date = obs_date.date()

    obs_str = obs_date.strftime("%Y-%m-%d")

    # Directory with this ticker's option chains
    ticker_dir = Path(options_root) / ticker

    # All CALL files for this observation date
    call_files = list(ticker_dir.glob(f"{obs_str}{ticker}_*_calls.csv"))
    if not call_files:
        raise FileNotFoundError(f"No call files for {ticker} on {obs_str} in {ticker_dir}")

    # Parse expiration dates out of filenames
    expirations = []
    for f in call_files:
        name = f.name  # e.g. 2025-12-05AAPL_2026-01-02_calls.csv
        prefix = f"{obs_str}{ticker}_"
        suffix = "_calls.csv"
        exp_str = name[len(prefix) : -len(suffix)]
        exp_date = datetime.strptime(exp_str, "%Y-%m-%d").date()
        expirations.append((exp_date, f))

    # Choose expiration closest to obs_date + days_forward
    target_exp_date = obs_date + timedelta(days=days_forward)
    exp_date, call_file = min(expirations, key=lambda x: abs(x[0] - target_exp_date))
    exp_str = exp_date.strftime("%Y-%m-%d")

    # Matching PUT file
    put_file = ticker_dir / f"{obs_str}{ticker}_{exp_str}_puts.csv"
    if not put_file.exists():
        raise FileNotFoundError(f"Put file not found: {put_file}")

    calls = pd.read_csv(call_file)
    puts = pd.read_csv(put_file)

    if calls.empty or puts.empty:
        raise ValueError(f"Empty calls/puts for {ticker} on {obs_str}, exp {exp_str}")

    # Spot price from OHLCV on obs_date
    try:
        spot = float(ohlcv_df.loc[pd.Timestamp(obs_date), "Close"])
    except KeyError:
        raise KeyError(f"No OHLCV Close for {ticker} on {obs_str}")

    # Find ATM strike (closest to spot)
    calls = calls.copy()
    calls["dist"] = (calls["strike"] - spot).abs()
    atm_row = calls.sort_values("dist").iloc[0]
    atm_strike = float(atm_row["strike"])

    # Call & put rows at that strike
    atm_call = calls.loc[calls["strike"] == atm_strike].iloc[0]
    atm_put = puts.loc[puts["strike"] == atm_strike].iloc[0]

    iv_call = float(atm_call["impliedVolatility"])
    iv_put = float(atm_put["impliedVolatility"])
    iv_30d = (iv_call + iv_put) / 2.0

    return {
        "ticker": ticker,
        "obs_date": obs_str,
        "spot": spot,
        "expiration": exp_str,
        "atm_strike": atm_strike,
        "iv_call": iv_call,
        "iv_put": iv_put,
        "iv_30d": iv_30d,
    }


# --------------------------------------------------------------------
# Save snapshot IV for a list of tickers
# --------------------------------------------------------------------
def save_30d_iv_for_tickers(tickers, output_path) -> pd.DataFrame:
    """
    For each ticker in `tickers`, compute 30d ATM IV (using ticker_30d_iv_today)
    and save the results to a CSV.
    """
    results = []

    for t in tickers:
        try:
            info = calc_ticker_30d_iv(t)
            results.append(info)
        except Exception as e:
            print(f"Error for {t}: {e}")

    if not results:
        raise ValueError("No results to save – all tickers failed?")

    df = pd.DataFrame(results)
    df = df[
        [
            "ticker",
            "spot",
            "expiration",
            "atm_strike",
            "iv_call",
            "iv_put",
            "iv_30d",
        ]
    ]
    df.to_csv(output_path, index=False)
    return df


# --------------------------------------------------------------------
# This function function downloads the option chain for all expiration
# --------------------------------------------------------------------
def save_all_option_chains(tickers: list, options_dir: Path) -> None:
    """
    Save calls & puts chains for ALL expirations of a ticker into `options_dir`.

    Files:
        {ticker}_{expiration}_calls.csv
        {ticker}_{expiration}_puts.csv
    """

    for ticker in tickers:
        ticker_dir = options_dir / f"{ticker}"
        ticker_dir.mkdir(parents=True, exist_ok=True)

        tk = yf.Ticker(ticker)
        
        # Get last trading day from recent daily history
        hist = tk.history(period="7d", interval="1d")
        if hist.empty:
            raise ValueError(f"No price history for {ticker}, cannot determine last trading day")
        # last_trading_day = date(2025,12,15).strftime("%Y-%m-%d")
        last_trading_day = hist.index[-1].date().strftime("%Y-%m-%d")
        

        if not tk.options:
            raise ValueError(f"No options for {ticker}")

        for exp_str in tk.options:
            chain = tk.option_chain(exp_str)
            calls = chain.calls
            puts = chain.puts

            calls_path = ticker_dir / f"{last_trading_day}{ticker}_{exp_str}_calls.csv"
            puts_path = ticker_dir / f"{last_trading_day}{ticker}_{exp_str}_puts.csv"

            calls.to_csv(calls_path, index=False)
            puts.to_csv(puts_path, index=False)

        print(f"Saved option chains for {ticker} to {ticker_dir}")


# --------------------------------------------------------------------
# Add 30d IV to existing indicator CSV
# --------------------------------------------------------------------

from pathlib import Path
import pandas as pd

def _pick_expiration_file(
    *,
    options_chain_dir: Path,
    ticker: str,
    obs_date: pd.Timestamp,
    days_forward: int,
    side: str,  # "calls" or "puts"
) -> Path | None:
    """
    Looks under: options_chain_dir / {ticker}/
    for files like: 2025-12-11AAPL_2026-05-15_calls.csv
    """
    ticker = ticker.upper()
    chain_dir = Path(options_chain_dir) / ticker  # <-- FIX

    obs_str = obs_date.strftime("%Y-%m-%d")
    pattern = f"{obs_str}{ticker}_????-??-??_{side}.csv"

    files = list(chain_dir.glob(pattern))
    if not files:
        return None

    target = (obs_date + pd.Timedelta(days=days_forward)).normalize()

    def exp_date_from_name(p: Path) -> pd.Timestamp:
        exp_str = p.name.split(f"{ticker}_", 1)[1].split(f"_{side}.csv", 1)[0]
        return pd.to_datetime(exp_str)

    return min(files, key=lambda p: abs(exp_date_from_name(p) - target))

def add_iv_to_indicator_csv(
    ticker: str,
    indicator_csv_path: str | Path,
    options_chain_dir: str | Path,
    days_forward: int = 30,
) -> None:
    indicator_csv_path = Path(indicator_csv_path)
    options_chain_dir = Path(options_chain_dir)

    df = pd.read_csv(
        indicator_csv_path,
        index_col="Date",
        parse_dates=["Date"],
    ).sort_index()

    if "iv_30d" not in df.columns:
        df["iv_30d"] = pd.NA

    # Fill ONLY rows where iv_30d is missing (your Dec 12 case)
    missing_dates = df.index[df["iv_30d"].isna()].sort_values()
    if len(missing_dates) == 0:
        return

    for dt in missing_dates:
        calls_path = _pick_expiration_file(
            options_chain_dir=options_chain_dir,
            ticker=ticker,
            obs_date=dt,
            days_forward=days_forward,
            side="calls",
        )
        puts_path = _pick_expiration_file(
            options_chain_dir=options_chain_dir,
            ticker=ticker,
            obs_date=dt,
            days_forward=days_forward,
            side="puts",
        )

        # If you only save calls (no puts files), we can still proceed with calls only.
        if calls_path is None and puts_path is None:
            print(f"[{ticker}] {dt.date()} missing iv_30d, but no chain files found. Skipping.")
            continue

        try:
            calls_df = pd.read_csv(calls_path) if calls_path else None
            puts_df = pd.read_csv(puts_path) if puts_path else None

            # ---- PLUG YOUR CALC HERE ----
            # Replace this with your implementation that computes iv_30d
            # from the option chain data you saved on disk.
            #
            # Example expected return: float iv_30d
            iv_30d = calc_ticker_30d_iv(
                ticker=ticker,
                obs_date=dt,
                calls_df=calls_df,
                puts_df=puts_df,
                days_forward=days_forward,
            )
            # -----------------------------

            df.loc[dt, "iv_30d"] = round(float(iv_30d), 4)
            src = calls_path.name if calls_path else puts_path.name
            print(f"[{ticker}] {dt.date()} → iv_30d={df.loc[dt,'iv_30d']:.4f} (from {src})")

        except Exception as e:
            print(f"[{ticker}] Skipping {dt.date()} – {e}")
            continue

    df.sort_index().to_csv(indicator_csv_path)


# --------------------------------------------------------------------
# Run for all IV_tickers (if executed as a script)
# --------------------------------------------------------------------
def calculate_iv_30d(tickers: list, indicator_csv_path: str):
    for t in tickers:
        # data_file = ohlcv_csv_path / f"{t}.csv"
        options_chain_path = Path("historical_data") / "options_chain"
        indicator_file = indicator_csv_path / f"{t}.csv"
        add_iv_to_indicator_csv(t, indicator_file, options_chain_path)


def detect_gaps(ticker: str, df: pd.DataFrame) -> pd.DataFrame:
    
    # Make sure data is sorted by date
    df = df.sort_index()

    # Yesterday's close, aligned with today's row
    y_high = df["High"].shift(1)
    y_close = df["Close"].shift(1)

    # ---- Definitions ----
    # Def 1 - "fake positive gap":
    # today.Open > yesterday.Close
    # today.Low <= yesterday.Close
    # today.Open > today.Close
    fake_gap = (
        (df["Open"] > y_high) &
        (df["Low"] <= y_close) &
        (df["Open"] > df["Close"])
    )

    # Def 2 - "real positive gap":
    # today.Open > yesterday.Close
    # today.Open < today.Close
    real_gap = (
        (df["Open"] > y_high) &
        (df["Open"] < df["Close"])
    )

    # Keep only days with any kind of gap
    any_gap = fake_gap | real_gap
    gap_dates = df.index[any_gap]

    # Build a small result DataFrame: Date + gap_type
    gap_type = []
    for date in gap_dates:
        if fake_gap.loc[date]:
            gap_type.append("fake")
        elif real_gap.loc[date]:
            gap_type.append("real")
        else:
            gap_type.append(None)  # should not happen

    result = pd.DataFrame(
        {"gap_type": gap_type},
        index=gap_dates
    )
    result.index.name = "Date"

    fake_count = 0
    real_count = 0
    with open(f"{ticker}", "w") as f:
        for date, g_type in zip(gap_dates, gap_type, strict=True):
            if g_type == "fake":
                fake_count+=1
            else:
                real_count+=1
            f.writelines(f"{date}: {g_type}\n")
        
        f.writelines(f"fake({fake_count})   real({real_count})\n")

    return result


def mark_big_moves_vs_vix(spx_df: pd.DataFrame,
                          vix_df: pd.DataFrame,
                          output_path: str) -> pd.DataFrame:
    """
    Compare daily SPX moves to 'expected' daily volatility from VIX
    and mark days where |return| > expected_sigma as green/red.

    spx_df: DataFrame with column 'Close', indexed by Date (daily).
    vix_df: DataFrame with column 'Close', indexed by Date (daily).
    output_path: CSV path to write (e.g. 'spx_vs_vix_moves.csv').

    Returns:
        DataFrame of all 'bigger-than-expected' days plus summary rows.
    """

    # 1) Make sure both are sorted and aligned on dates
    spx = spx_df[['Close']].rename(columns={'Close': 'SPX_Close'}).sort_index()
    vix = vix_df[['Close']].rename(columns={'Close': 'VIX_Close'}).sort_index()

    # Inner join – only dates where we have both SPX and VIX
    df = spx.join(vix, how='inner')

    # 2) Daily SPX and VIX returns
    df['spx_return_pct'] = df['SPX_Close'].pct_change()
    df['vix_return_pct'] = df['VIX_Close'].pct_change()

    # 3) Expected daily sigma from VIX (Black–Scholes style)
    # sigma_daily = (VIX/100) / sqrt(252)
    df['expected_daily_sigma'] = (df['VIX_Close'] / 100.0) / np.sqrt(252.0)

    # 4) Flag days where |SPX return| > expected sigma
    df['bigger_than_expected'] = df['spx_return_pct'].abs() > df['expected_daily_sigma']

    # Drop first day (NaN returns)
    df = df.dropna(subset=['spx_return_pct', 'expected_daily_sigma', 'vix_return_pct'])

    # Keep only days with bigger-than-expected move
    big_moves = df[df['bigger_than_expected']].copy()

    # 5) Colors: SPX & VIX
    def classify_color(r):
        if r > 0:
            return 'green'
        elif r < 0:
            return 'red'
        else:
            return 'neutral'

    big_moves['spx_color'] = big_moves['spx_return_pct'].apply(classify_color)
    big_moves['vix_color'] = big_moves['vix_return_pct'].apply(classify_color)

    # 6) Prepare result for CSV (date-only index)
    result = big_moves[['spx_return_pct',
                        'spx_color']].copy()

    # Make index pure date (no time) as string YYYY-MM-DD
    result.index = result.index.strftime('%Y-%m-%d')
    result.index.name = 'Date'

    # 7) Summary counts
    total_green = (result['spx_color'] == 'green').sum()
    total_red   = (result['spx_color'] == 'red').sum()
    green_with_vix_red = (
        (big_moves['spx_color'] == 'green') &
        (big_moves['vix_color'] == 'red')
    ).sum()
    red_with_vix_green = (
        (big_moves['spx_color'] == 'red') &
        (big_moves['vix_color'] == 'green')
    ).sum()

    # Summary rows as index labels
    summary_index_green = f"TOTAL_GREEN ({total_green}) VIX was red in ({green_with_vix_red}) of them"
    summary_index_red   = f"TOTAL_RED ({total_red} )VIX was green in ({red_with_vix_green}) of them"

    summary = pd.DataFrame(
        [
            {
                'Date': summary_index_green,
                'spx_return_pct': '',
                'expected_daily_sigma': '',
                'spx_color': '',
                'vix_return_pct': '',
                'vix_color': ''
            },
            {
                'Date': summary_index_red,
                'spx_color': ''
            }
        ]
    ).set_index('Date')

    final = pd.concat([result, summary], axis=0)

    # 8) Write to CSV
    final.to_csv(output_path)

    return final


def process_tickers_for_gaps_and_iv(tickers, data_dir, output_dir):
    data_dir = Path(data_dir)
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    for ticker in tickers:
        csv_path = data_dir / f"{ticker}.csv"
        if not csv_path.exists():
            print(f"{ticker}: file not found, skipping")
            continue

        # read OHLCV (+ maybe iv_30d)
        df = pd.read_csv(csv_path, parse_dates=["Date"])
        df = df.set_index("Date").sort_index()

        # 1) detect gaps
        detect_gaps(ticker, df)

        # 2) only run mark_big_moves_vs_vix if iv_30d exists
        if "iv_30d" in df.columns and df["iv_30d"].notna().any():
            # build a VIX-like df from iv_30d (iv is in decimals, VIX is %)
            vix_like = pd.DataFrame(index=df.index)
            vix_like["Close"] = df["iv_30d"] * 100.0

            out_file = output_dir / f"{ticker}_moves_vs_iv.csv"
            mark_big_moves_vs_vix(df, vix_like, str(out_file))
        else:
            print(f"{ticker}: no iv_30d column, skipping mark_big_moves_vs_vix")
