import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import argrelextrema
import mplfinance as mpf

def show_graph(tickers):
    for ticker in tickers:
        # === Load data ===
        df = pd.read_csv(f"historical_data/{ticker}(1d-SOURCE).csv", parse_dates=['Date'], index_col='Date')
        # === Detect local extrema ===
        order = 5
        local_max_idx = argrelextrema(df['Close'].values, np.greater_equal, order=order)[0]
        local_min_idx = argrelextrema(df['Close'].values, np.less_equal, order=order)[0]

        df['max'] = np.nan
        df['min'] = np.nan
        df.loc[df.index[local_max_idx], 'max'] = df['Close'].iloc[local_max_idx]
        df.loc[df.index[local_min_idx], 'min'] = df['Close'].iloc[local_min_idx]

        # === Resistance/Support ===
        most_significant_max = df['max'].dropna().max()
        most_significant_min = df['min'].dropna().min()

        # === Flip levels (±1%) ===
        max_vals = df['max'].dropna().values
        min_vals = df['min'].dropna().values
        raw_flip_levels = []

        for max_p in max_vals:
            for min_p in min_vals:
                avg_p = (max_p + min_p) / 2
                if abs(max_p - min_p) / avg_p <= 0.01:
                    raw_flip_levels.append(avg_p)

        # === Group into 5% clusters ===
        raw_flip_levels = sorted([round(lvl, 2) for lvl in raw_flip_levels])
        grouped_levels = []
        visited = set()

        for i, lvl in enumerate(raw_flip_levels):
            if i in visited:
                continue
            cluster = [lvl]
            visited.add(i)
            for j in range(i+1, len(raw_flip_levels)):
                if j in visited:
                    continue
                if abs(raw_flip_levels[j] - lvl) / lvl <= 0.05:
                    cluster.append(raw_flip_levels[j])
                    visited.add(j)
            grouped_levels.append(round(np.mean(cluster), 2))

        # === Build horizontal lines for support/resistance/flip ===
        hlines = {
            'hlines': [most_significant_max, most_significant_min] + grouped_levels,
            'colors': ['orange', 'green'] + ['gray'] * len(grouped_levels),
            'linestyle': ['--', '--'] + [':'] * len(grouped_levels),
            'linewidths': [2, 2] + [1.5] * len(grouped_levels),
            'alpha': 0.7
        }

        # === Plot ===
        mpf.plot(
            df,
            type='candle',
            volume=True,
            title=f"{ticker}",
            style='yahoo',
            addplot=[],
            hlines=hlines,
            figscale=1.4,
            figratio=(10,6),
            tight_layout=True
        )