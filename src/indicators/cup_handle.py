    # cup_handle.py
import math
import pandas as pd
import numpy as np

def detect_cup_and_handle(
    df: pd.DataFrame,
    lookback=200,                 # bars to look back for the pattern
    smooth=5,                     # smoothing window (rolling mean) to reduce noise
    rim_tolerance=0.03,           # right rim must be within 3% of left rim
    min_cup_depth=0.08,           # cup depth at least 8% from rim to trough
    max_cup_depth=0.5,            # avoid “too deep” cups (>50%)
    min_cup_len=25,               # min bars from left rim to right rim
    max_cup_len=180,              # max bars for the cup
    handle_max_drop=0.15,         # handle pullback <= 15% from right rim
    handle_min_len=3,             # at least 3 bars
    handle_max_len=30,            # at most 30 bars
    breakout_vol_mult=1.4,        # breakout volume >= 1.4x 20-day avg
    vol_avg_window=20
):
    """
    Returns a dict with details if a valid pattern ends near the last bar, else None.

    df must have columns: ['Open','High','Low','Close','Volume']; DateTime index preferred.
    """
    if df is None or len(df) < max(lookback, min_cup_len + handle_min_len + 5):
        return None

    work = df.tail(lookback).copy()
    # Smooth price to reduce local noise; use Close for structure recognition
    price = work['Close'].rolling(smooth, min_periods=1).mean()
    vol = work['Volume']

    n = len(work)
    idx = price.index

    # 1) Find a LEFT RIM (local maximum) in the first third of the window
    first_third = range(3, max(4, n // 3))
    left_rim_i = max(first_third, key=lambda i: price.iloc[i], default=None)
    if left_rim_i is None:
        return None

    left_rim_price = price.iloc[left_rim_i]

    # 2) Find a TROUGH (local minimum) after the left rim
    if left_rim_i + 3 >= n - 3:
        return None
    trough_i = left_rim_i + 1 + np.argmin(price.iloc[left_rim_i + 1 : n - 1].values)
    trough_price = price.iloc[trough_i]

    # Basic cup depth checks
    cup_depth = (left_rim_price - trough_price) / left_rim_price
    if cup_depth < min_cup_depth or cup_depth > max_cup_depth:
        return None

    # 3) Find a RIGHT RIM (local maximum) after the trough, before last bars (leave room for handle)
    search_end = n - max(handle_min_len + 3, 5)
    if trough_i + 3 >= search_end:
        return None

    right_rim_i = trough_i + 1 + np.argmax(price.iloc[trough_i + 1 : search_end].values)
    right_rim_price = price.iloc[right_rim_i]

    # Rims should be close within tolerance (rounded U, not lopsided)
    if abs(right_rim_price - left_rim_price) / left_rim_price > rim_tolerance:
        return None

    # Cup length check
    cup_len = right_rim_i - left_rim_i
    if cup_len < min_cup_len or cup_len > max_cup_len:
        return None

    # 4) Handle: small pullback after right rim
    # Define handle window between right rim and last bar - 1
    handle_start = right_rim_i + 1
    handle_end = n - 1
    if handle_end - handle_start + 1 < handle_min_len:
        return None

    handle_slice = price.iloc[handle_start : handle_end + 1]
    if len(handle_slice) < handle_min_len:
        return None

    # Max drawdown during handle (from right rim)
    handle_min = handle_slice.min()
    handle_drawdown = (right_rim_price - handle_min) / right_rim_price
    if handle_drawdown < 0 or handle_drawdown > handle_max_drop:
        return None

    # Optional: ensure gentle downward/sideways drift in handle (not a crash)
    # Fit a small regression slope over handle; small negative or flat is ok
    x = np.arange(len(handle_slice))
    y = handle_slice.values
    if len(x) >= 2:
        slope = np.polyfit(x, y, 1)[0]
        # too steep down could be a failure handle (heuristic)
        if slope < -0.002 * right_rim_price:
            return None

    handle_len = len(handle_slice)
    if handle_len > handle_max_len:
        return None

    # 5) Breakout: last close > max of both rims; and volume expansion
    last_close = work['Close'].iloc[-1]
    last_vol = vol.iloc[-1]
    rim_level = max(df['Close'].iloc[work.index[left_rim_i]], df['Close'].iloc[work.index[right_rim_i]])
    breakout = last_close > rim_level * (1.000 + 0.001)  # tiny buffer

    vol_ok = True
    if breakout:
        vol_avg = vol.iloc[-(vol_avg_window + 1):-1].mean() if len(vol) > vol_avg_window else vol.mean()
        vol_ok = (last_vol >= breakout_vol_mult * vol_avg) if not math.isnan(vol_avg) and vol_avg > 0 else True

    if not (breakout and vol_ok):
        return None

    return {
        "left_rim_date": str(idx[left_rim_i]),
        "right_rim_date": str(idx[right_rim_i]),
        "trough_date": str(idx[trough_i]),
        "cup_depth_pct": round(100 * cup_depth, 2),
        "cup_len_bars": int(cup_len),
        "handle_len_bars": int(handle_len),
        "handle_drawdown_pct": round(100 * handle_drawdown, 2),
        "rim_level": float(rim_level),
        "last_close": float(last_close),
        "breakout_vol": int(last_vol),
        "avg_vol": int(vol.iloc[-(vol_avg_window + 1):-1].mean()) if len(vol) > vol_avg_window else int(vol.mean()),
        "confirmed": True
    }